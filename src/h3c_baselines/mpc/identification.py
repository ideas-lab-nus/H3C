"""Fresh, evaluation-disjoint enhanced-RBC trajectories for ARX identification."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import subprocess
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from h3c.experiments.profiles import load_profile, repository_root
from h3c.runtime.clients import BoptestHttpClient
from h3c.runtime.comfort import ComfortModel
from h3c.runtime.execution_lock import physical_execution_lock
from h3c.runtime.occupancy import effective_count
from h3c.runtime.protocol import (
    PhysicalClient,
    control_input,
    forecast_points,
    require_time,
    resolve_forecast_missing_occupancy,
    site_power,
    zone_temperature_c,
)
from h3c_baselines.configuration import load_formal_suite
from h3c_baselines.controllers.enhanced_rbc import EnhancedRbcController
from h3c_baselines.mpc.vector_arx import (
    ArxLayout,
    FittedArxModel,
    build_dataset,
    fit_vector_arx,
)
from h3c_baselines.outputs.integrity import secret_occurrences

PhysicalFactory = Callable[[str], PhysicalClient]
IDENTIFICATION_COLUMNS = ("time_seconds", "sample_role", "outputs", "controls", "disturbance")


def _write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as file:
        file.write(
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )


def _replace_json(path: Path, value: Any) -> None:
    pending = path.with_name(f".{path.name}.pending")
    with pending.open("x", encoding="utf-8", newline="\n") as file:
        file.write(
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )
        file.flush()
        os.fsync(file.fileno())
    pending.replace(path)


def _source_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository_root(), text=True
    ).strip()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _disturbance(
    profile: Mapping[str, Any],
    forecast: Mapping[str, list[float]],
    zones: tuple[str, ...],
    step: int,
    time_seconds: int,
) -> tuple[NDArray[np.float64], dict[str, float]]:
    occupancy = {
        zone: effective_count(
            profile["occupancy"],
            time_seconds,
            float(forecast[profile["zones"][zone]["occupancy_forecast"]][step]),
        )
        for zone in zones
    }
    fraction = (time_seconds % 86400) / 86400.0
    vector = np.asarray(
        [
            float(forecast[profile["global_inputs"]["outdoor_temperature"]][step]) - 273.15,
            float(forecast[profile["global_inputs"]["solar_irradiance"]][step]),
            *[occupancy[zone] for zone in zones],
            math.sin(2.0 * math.pi * fraction),
            math.cos(2.0 * math.pi * fraction),
        ],
        dtype=np.float64,
    )
    return vector, occupancy


def _native_kpis(client: PhysicalClient) -> dict[str, Any]:
    method = getattr(client, "get_kpis", None)
    if not callable(method):
        raise ValueError("physical client does not implement native KPI retrieval")
    value = method()
    if not isinstance(value, dict):
        raise ValueError("native BOPTEST KPI response is invalid")
    return value


def _load_identification_data(
    path: Path,
) -> tuple[NDArray[np.int64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != IDENTIFICATION_COLUMNS:
            raise ValueError("identification data header is invalid")
        rows = list(reader)
    times = np.asarray([int(row["time_seconds"]) for row in rows], dtype=np.int64)
    outputs = np.asarray([json.loads(row["outputs"]) for row in rows], dtype=np.float64)
    controls = np.asarray([json.loads(row["controls"]) for row in rows], dtype=np.float64)
    disturbances = np.asarray([json.loads(row["disturbance"]) for row in rows], dtype=np.float64)
    if not rows or rows[-1]["sample_role"] != "terminal_target_state":
        raise ValueError("identification data lacks its terminal target state")
    if any(row["sample_role"] != "controlled_step" for row in rows[:-1]):
        raise ValueError("identification sample roles are invalid")
    return times, outputs, controls, disturbances


def verify_identification_run(run_dir: Path, *, require_completion: bool = True) -> dict[str, Any]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    resolved = json.loads((run_dir / "resolved_config.json").read_text(encoding="utf-8"))
    fit_report = json.loads((run_dir / "fit_report.json").read_text(encoding="utf-8"))
    model = FittedArxModel.load(run_dir / "model_coefficients.npz")
    times, outputs, controls, disturbances = _load_identification_data(
        run_dir / "identification_data.csv"
    )
    case = str(manifest["case"])
    days = int(manifest["identification_days"])
    profile = load_profile(case)
    zones = tuple(profile["zones"])
    evaluation_start = int(profile["evaluation_start_day"]) * 86400
    suite = load_formal_suite()
    layout = ArxLayout(
        zones,
        (
            "outdoor_temperature_c",
            "solar_irradiance_w_m2",
            *[f"effective_occupancy_{zone}" for zone in zones],
            "time_sine",
            "time_cosine",
        ),
    )
    features, targets, target_times = build_dataset(layout, times, outputs, controls, disturbances)
    rebuilt, rebuilt_report = fit_vector_arx(
        layout,
        features,
        targets,
        validation_rows=int(suite["mpc"]["validation_days"]) * 96,
        alpha_candidates=tuple(float(value) for value in suite["mpc"]["ridge_alpha_candidates"]),
    )
    expected_steps = days * 96
    checks: dict[str, bool] = {
        "resolved_identity": resolved.get("case") == case
        and resolved.get("identification_days") == days,
        "registered_duration": int(suite["mpc_identification_days"][case]) == days,
        "source_commit_present": isinstance(manifest.get("source_commit"), str)
        and len(manifest["source_commit"]) == 40,
        "initialize_once": manifest["lifecycle"]["initialize_count"] == 1,
        "advance_count": manifest["lifecycle"]["advance_count"] == expected_steps,
        "stop_once": manifest["lifecycle"]["stop_count"] == 1,
        "test_id_present": isinstance(manifest.get("test_id"), str),
        "sample_count": len(times) == expected_steps + 1,
        "timeline_start": int(times[0]) == evaluation_start - expected_steps * 900,
        "timeline_ends_at_evaluation_boundary": int(times[-1]) == evaluation_start
        and int(target_times.max()) == evaluation_start,
        "model_reproducible": model.identity == rebuilt.identity == fit_report["model_identity"],
        "identification_data_identity": manifest.get("identification_data_sha256")
        == _file_sha256(run_dir / "identification_data.csv"),
        "fit_report_reproducible": fit_report == rebuilt_report,
        "finite_coefficients": bool(np.all(np.isfinite(model.coefficients))),
        "native_kpis_present": (run_dir / "native_boptest_kpis.json").is_file(),
        "secret_scan_complete": manifest.get("secret_scan_status") == "completed",
        "secret_absent": manifest.get("secret_exposure_count") == 0,
    }
    errors = sorted(name for name, passed in checks.items() if not passed)
    verified = not errors
    classification = "IDENTIFICATION-COMPLETE" if verified else "RUN-INVALID"
    if require_completion:
        completion = json.loads((run_dir / "completion.json").read_text(encoding="utf-8"))
        checks["completion_identity"] = (
            completion.get("classification") == classification
            and completion.get("model_identity") == model.identity
        )
        if not checks["completion_identity"]:
            errors.append("completion_identity")
            verified = False
            classification = "RUN-INVALID"
    return {
        "schema": "h3c_mpc_identification_verification",
        "schema_version": 1,
        "checks": checks,
        "errors": sorted(set(errors)),
        "execution_integrity": verified,
        "completion_eligible": verified,
        "classification": classification,
        "model_identity": model.identity,
    }


def execute_identification(
    case: str,
    days: int,
    *,
    endpoint: str,
    output_root: Path,
    lock_root: Path,
    physical_factory: PhysicalFactory | None = None,
) -> dict[str, Any]:
    profile = load_profile(case)
    expected_days = int(load_formal_suite()["mpc_identification_days"][case])
    if days != expected_days:
        raise ValueError("identification duration differs from the frozen suite")
    zones = tuple(profile["zones"])
    evaluation_start = int(profile["evaluation_start_day"]) * 86400
    start = evaluation_start - days * 86400
    steps = days * 96
    source_commit = _source_commit()
    run_identity = hashlib.sha256(
        json.dumps(
            {"case": case, "days": days, "source_commit": source_commit}, sort_keys=True
        ).encode()
    ).hexdigest()
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "-" + run_identity[:12]
    run_dir = (output_root.resolve() / case / run_id).resolve()
    if not run_dir.is_relative_to(output_root.resolve()) or run_dir.exists():
        raise ValueError("fresh identification directory is invalid")
    run_dir.mkdir(parents=True)
    resolved = {
        "schema": "h3c_mpc_identification_plan",
        "schema_version": 1,
        "case": case,
        "identification_days": days,
        "controller": "enhanced-rbc",
        "start_time_seconds": start,
        "evaluation_boundary_seconds": evaluation_start,
        "case_profile": profile,
    }
    manifest: dict[str, Any] = {
        "schema": "h3c_mpc_identification_manifest",
        "schema_version": 1,
        "case": case,
        "source_commit": source_commit,
        "run_identity": run_identity,
        "identification_days": days,
        "evaluation_start_seconds": evaluation_start,
        "secret_scan_status": "pending",
        "secret_exposure_count": None,
        "lifecycle": {"initialize_count": 0, "advance_count": 0, "stop_count": 0},
    }
    _write_json(run_dir / "resolved_config.json", resolved)
    _write_json(run_dir / "manifest.json", manifest)
    client = (physical_factory or BoptestHttpClient)(endpoint)
    controller = EnhancedRbcController(zones, repository_root() / profile["program"])
    started = time.perf_counter()
    model: FittedArxModel | None = None
    with physical_execution_lock(lock_root):
        try:
            state = client.initialize(
                profile["testcase"], start, int(profile["protocol"]["server_warmup_days"]) * 86400
            )
            manifest["lifecycle"]["initialize_count"] = 1
            require_time(state, start)
            test_id = client.test_id
            if not isinstance(test_id, str) or not test_id:
                raise ValueError("identification initialize did not return a test id")
            manifest["test_id"] = test_id
            points = forecast_points(profile)
            source_forecast = client.forecast(points, (steps + 96) * 900, 900)
            forecast, resolution_events = resolve_forecast_missing_occupancy(
                profile,
                source_forecast,
                points,
                steps + 97,
                forecast_phase="mpc_identification",
                start_time_seconds=start,
                step_seconds=900,
            )
            manifest["occupancy_missing_value_resolution_count"] = len(resolution_events)
            comfort = ComfortModel(profile["comfort"])
            last_setpoints = dict.fromkeys(zones, 25.0)
            last_pmv = dict.fromkeys(zones, 0.0)
            last_occupancy = dict.fromkeys(zones, 0.0)
            times: list[int] = []
            outputs: list[list[float]] = []
            controls: list[list[float]] = []
            disturbances: list[list[float]] = []
            for step in range(steps):
                action_time = start + step * 900
                require_time(state, action_time)
                disturbance, occupancy = _disturbance(profile, forecast, zones, step, action_time)
                future_occupancy = {
                    zone: [
                        effective_count(
                            profile["occupancy"],
                            action_time + offset * 900,
                            float(
                                forecast[profile["zones"][zone]["occupancy_forecast"]][
                                    step + offset
                                ]
                            ),
                        )
                        for offset in range(1, 5)
                    ]
                    for zone in zones
                }
                setpoints, _ = controller.decide(
                    occupancy=occupancy,
                    future_occupancy=future_occupancy,
                    last_setpoints_c=last_setpoints,
                    last_pmv=last_pmv,
                    last_occupancy=last_occupancy,
                )
                times.append(action_time)
                outputs.append(
                    [
                        *[zone_temperature_c(profile, state, zone) for zone in zones],
                        site_power(profile, state),
                    ]
                )
                controls.append([setpoints[zone] for zone in zones])
                disturbances.append(disturbance.tolist())
                next_state = client.advance(control_input(profile, setpoints))
                manifest["lifecycle"]["advance_count"] += 1
                require_time(next_state, action_time + 900)
                if client.test_id != test_id:
                    raise ValueError("test id changed during MPC identification")
                daily = forecast[profile["global_inputs"]["outdoor_temperature"]][
                    step : step + 97 : 4
                ]
                comfort.update_clothing(
                    action_time, sum(float(value) - 273.15 for value in daily) / len(daily)
                )
                last_pmv = {
                    zone: comfort.pmv(zone_temperature_c(profile, next_state, zone))
                    for zone in zones
                }
                state = next_state
                last_setpoints = setpoints
                last_occupancy = occupancy
            terminal_disturbance, _ = _disturbance(
                profile, forecast, zones, steps, evaluation_start
            )
            times.append(evaluation_start)
            outputs.append(
                [
                    *[zone_temperature_c(profile, state, zone) for zone in zones],
                    site_power(profile, state),
                ]
            )
            controls.append(controls[-1])
            disturbances.append(terminal_disturbance.tolist())
            layout = ArxLayout(
                zones,
                (
                    "outdoor_temperature_c",
                    "solar_irradiance_w_m2",
                    *[f"effective_occupancy_{zone}" for zone in zones],
                    "time_sine",
                    "time_cosine",
                ),
            )
            time_array = np.asarray(times, dtype=np.int64)
            output_array = np.asarray(outputs, dtype=np.float64)
            control_array = np.asarray(controls, dtype=np.float64)
            disturbance_array = np.asarray(disturbances, dtype=np.float64)
            features, targets, _ = build_dataset(
                layout, time_array, output_array, control_array, disturbance_array
            )
            suite = load_formal_suite()
            model, fit_report = fit_vector_arx(
                layout,
                features,
                targets,
                validation_rows=int(suite["mpc"]["validation_days"]) * 96,
                alpha_candidates=tuple(
                    float(value) for value in suite["mpc"]["ridge_alpha_candidates"]
                ),
            )
            with (run_dir / "identification_data.csv").open(
                "x", encoding="utf-8", newline=""
            ) as file:
                writer = csv.DictWriter(file, fieldnames=IDENTIFICATION_COLUMNS)
                writer.writeheader()
                for index, time_seconds in enumerate(times):
                    writer.writerow(
                        {
                            "time_seconds": time_seconds,
                            "sample_role": (
                                "terminal_target_state"
                                if index == len(times) - 1
                                else "controlled_step"
                            ),
                            "outputs": json.dumps(outputs[index], separators=(",", ":")),
                            "controls": json.dumps(controls[index], separators=(",", ":")),
                            "disturbance": json.dumps(disturbances[index], separators=(",", ":")),
                        }
                    )
            manifest["identification_data_sha256"] = _file_sha256(
                run_dir / "identification_data.csv"
            )
            model.save(run_dir / "model_coefficients.npz")
            _write_json(run_dir / "fit_report.json", fit_report)
            _write_json(run_dir / "native_boptest_kpis.json", _native_kpis(client))
        finally:
            if client.test_id is not None:
                client.stop()
                manifest["lifecycle"]["stop_count"] += 1
            manifest["secret_exposure_count"] = secret_occurrences(run_dir)
            manifest["secret_scan_status"] = "completed"
            _replace_json(run_dir / "manifest.json", manifest)
    if model is None:
        raise AssertionError("MPC identification exited without a fitted model")
    verification = verify_identification_run(run_dir, require_completion=False)
    _write_json(run_dir / "verification.json", verification)
    if verification["completion_eligible"] is not True:
        raise ValueError(f"MPC identification verification failed: {verification['errors']}")
    completion = {
        "schema": "h3c_mpc_identification_completion",
        "schema_version": 1,
        "classification": "IDENTIFICATION-COMPLETE",
        "model_identity": model.identity,
        "elapsed_seconds": time.perf_counter() - started,
    }
    pending = run_dir / ".completion.pending"
    pending.write_text(json.dumps(completion, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(pending, run_dir / "completion.json")
    final = verify_identification_run(run_dir)
    if final["execution_integrity"] is not True:
        raise ValueError(f"MPC identification completion is invalid: {final['errors']}")
    return {"run_dir": str(run_dir), "model_identity": model.identity, "status": "complete"}
