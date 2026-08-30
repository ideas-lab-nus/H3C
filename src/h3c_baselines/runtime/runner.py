"""Fresh conditioned BOPTEST runner shared by independent baseline controllers."""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from h3c.experiments.profiles import repository_root
from h3c.experiments.settings import load_runtime_contract
from h3c.runtime.clients import BoptestHttpClient
from h3c.runtime.comfort import ComfortModel, step_reward
from h3c.runtime.execution_lock import physical_execution_lock
from h3c.runtime.occupancy import effective_count
from h3c.runtime.protocol import (
    PhysicalClient,
    build_forecast_evidence,
    control_input,
    forecast_points,
    initialize_evaluation_boundary,
    require_time,
    resolve_forecast_missing_occupancy,
    site_power,
    zone_temperature_c,
)
from h3c.runtime.source_identity import committed_source_identity
from h3c_baselines.configuration import (
    BaselineRunPlan,
    formal_evaluation_plans,
    load_hierarchical_mpc_config,
    mpc_formal_evaluation_plans,
)
from h3c_baselines.controllers.basic_rbc import basic_rbc_setpoints
from h3c_baselines.controllers.drl import FrozenDrlController
from h3c_baselines.controllers.enhanced_rbc import EnhancedRbcController
from h3c_baselines.models import model_entry, verify_checkpoint
from h3c_baselines.mpc.optimizer import HierarchicalMpcController
from h3c_baselines.mpc.training import verify_frozen_mpc_model
from h3c_baselines.mpc.vector_arx import FittedArxModel
from h3c_baselines.outputs.artifacts import BaselineArtifacts
from h3c_baselines.outputs.integrity import secret_occurrences
from h3c_baselines.outputs.metrics import compute_baseline_metrics
from h3c_baselines.outputs.verification import verify_baseline_run
from h3c_baselines.policies.observation_contracts import PolicyObservationBuilder

PhysicalFactory = Callable[[str], PhysicalClient]


def _source_commit() -> str:
    return committed_source_identity()


def _canonical(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _identity(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _future_occupancy(
    profile: Mapping[str, Any],
    forecast: Mapping[str, Sequence[float]],
    zones: tuple[str, ...],
    *,
    step: int,
    action_time: int,
) -> dict[str, list[float]]:
    return {
        zone: [
            effective_count(
                profile["occupancy"],
                action_time + offset * 900,
                float(forecast[profile["zones"][zone]["occupancy_forecast"]][step + offset]),
            )
            for offset in range(1, 5)
        ]
        for zone in zones
    }


def _legacy_policy_daily_outdoor_mean_c(
    profile: Mapping[str, Any],
    forecast: Mapping[str, Sequence[float]],
    *,
    step: int,
) -> float:
    """Return the original DRL policy's 96 consecutive 15-minute samples."""
    outdoor_point = str(profile["global_inputs"]["outdoor_temperature"])
    values = forecast[outdoor_point][step : step + 96]
    if len(values) != 96:
        raise ValueError("policy comfort forecast lacks 96 consecutive samples")
    return sum(float(value) - 273.15 for value in values) / 96.0


def _legacy_policy_pmv(
    comfort: ComfortModel,
    profile: Mapping[str, Any],
    forecast: Mapping[str, Sequence[float]],
    temperatures_c: Mapping[str, float],
    *,
    step: int,
    action_time: int,
) -> dict[str, float]:
    comfort.update_clothing(
        action_time,
        _legacy_policy_daily_outdoor_mean_c(profile, forecast, step=step),
    )
    return {zone: comfort.pmv(value) for zone, value in temperatures_c.items()}


def _mpc_disturbances(
    profile: Mapping[str, Any],
    forecast: Mapping[str, Sequence[float]],
    zones: tuple[str, ...],
    *,
    step: int,
    action_time: int,
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    list[int],
    list[float],
]:
    disturbances: list[list[float]] = []
    occupancy_rows: list[list[float]] = []
    prices: list[float] = []
    action_times: list[int] = []
    daily_means: list[float] = []
    outdoor_point = profile["global_inputs"]["outdoor_temperature"]
    for horizon in range(4):
        time_seconds = action_time + horizon * 900
        fraction = (time_seconds % 86400) / 86400.0
        occupancy = [
            effective_count(
                profile["occupancy"],
                time_seconds,
                float(forecast[profile["zones"][zone]["occupancy_forecast"]][step + horizon]),
            )
            for zone in zones
        ]
        disturbances.append(
            [
                float(forecast[outdoor_point][step + horizon]) - 273.15,
                float(forecast[profile["global_inputs"]["solar_irradiance"]][step + horizon]),
                *occupancy,
                math.sin(2.0 * math.pi * fraction),
                math.cos(2.0 * math.pi * fraction),
            ]
        )
        occupancy_rows.append(occupancy)
        prices.append(
            float(forecast[profile["global_inputs"]["electricity_price"]][step + horizon])
        )
        action_times.append(time_seconds)
        daily = forecast[outdoor_point][step + horizon : step + horizon + 97 : 4]
        daily_means.append(sum(float(value) - 273.15 for value in daily) / len(daily))
    return (
        np.asarray(disturbances, dtype=np.float64),
        np.asarray(prices, dtype=np.float64),
        np.asarray(occupancy_rows, dtype=np.float64),
        action_times,
        daily_means,
    )


def _native_kpis(physical: PhysicalClient) -> dict[str, Any]:
    method = getattr(physical, "get_kpis", None)
    if not callable(method):
        raise ValueError("physical client does not implement native KPI retrieval")
    value = method()
    if not isinstance(value, dict):
        raise ValueError("native BOPTEST KPI response is invalid")
    return value


def _execute_one(
    plan: BaselineRunPlan,
    *,
    suite: str,
    endpoint: str,
    output_root: Path,
    physical_factory: PhysicalFactory,
) -> dict[str, Any]:
    resolved = plan.resolved()
    profile = resolved["case_profile"]

    # Load every frozen-policy dependency and checkpoint before creating artifacts or
    # touching BOPTEST. A missing optional baseline dependency is an environment
    # preflight failure, not a reason to spend a fresh physical conditioning prefix.
    drl: FrozenDrlController | None = None
    observation_builder: PolicyObservationBuilder | None = None
    drl_identity: dict[str, Any] | None = None
    if plan.controller in {"c-drl", "h-drl"}:
        entry = model_entry(plan.case, plan.controller)
        drl_identity = verify_checkpoint(entry)
        drl = FrozenDrlController(plan.case, plan.controller)
        observation_builder = PolicyObservationBuilder(profile, entry)

    mpc_model: FittedArxModel | None = None
    mpc_identity: dict[str, Any] | None = None
    if plan.controller == "hierarchical-mpc":
        mpc_identity = verify_frozen_mpc_model(plan.case)
        if mpc_identity["valid"] is not True:
            raise ValueError("frozen hierarchical MPC model verification failed")
        mpc_model = FittedArxModel.load(
            repository_root() / "models" / "mpc" / plan.case / "model_coefficients.npz"
        )

    source_commit = _source_commit()
    execution_identity = {
        "plan_identity": resolved["plan_identity"],
        "source_commit": source_commit,
        "physical_endpoint_identity": _identity(endpoint.rstrip("/")),
        "mpc_model_identity": None if mpc_model is None else mpc_model.identity,
    }
    run_identity = _identity(execution_identity)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "-" + run_identity[:12]
    artifacts = BaselineArtifacts(output_root, suite, plan.case, run_id, plan.controller)
    manifest: dict[str, Any] = {
        "manifest_schema": "h3c_baseline_manifest",
        "schema_version": 1,
        "run_identity": run_identity,
        "source_commit": source_commit,
        "case": plan.case,
        "controller": plan.controller,
        "conditioning_prefix_identity": None,
        "evaluation_boundary_identity": None,
        "mpc_model_identity": execution_identity["mpc_model_identity"],
        "secret_scan_status": "pending",
        "secret_exposure_count": None,
        "occupancy_forecast_missing_value_resolution_count": 0,
        "lifecycle": {
            "initialize_count": 0,
            "conditioning_advance_count": 0,
            "evaluation_advance_count": 0,
            "stop_count": 0,
            "test_id_changes": 0,
        },
    }
    resolved["execution_identity"] = execution_identity
    artifacts.create(resolved, manifest)
    if drl_identity is not None:
        artifacts.write_new_json("model_identity.json", drl_identity)
    if mpc_identity is not None:
        artifacts.write_new_json("mpc_model_identity.json", mpc_identity)
    physical = physical_factory(endpoint)
    initialized = False
    stop_attempted = False
    frozen_test_id: str | None = None
    evaluation_start = int(profile["evaluation_start_day"]) * 86400
    evaluation_end = evaluation_start + plan.evaluation_hours * 3600
    last_physical_time = evaluation_start
    started = time.perf_counter()
    try:
        boundary = initialize_evaluation_boundary(
            physical,
            profile,
            artifacts,
            on_initialized=lambda _test_id: manifest["lifecycle"].update({"initialize_count": 1}),
        )
        initialized = True
        frozen_test_id = boundary.test_id
        manifest["conditioning_prefix_identity"] = boundary.conditioning_prefix_identity
        manifest["evaluation_boundary_identity"] = boundary.evaluation_boundary_identity
        manifest["lifecycle"]["conditioning_advance_count"] = 0
        zones = tuple(profile["zones"])
        steps = plan.evaluation_hours * 4
        artifacts.append_jsonl(
            "timing.jsonl",
            {
                "phase": "physical_lifecycle",
                "event": "evaluation_started",
                "time_seconds": evaluation_start,
                "test_id": boundary.test_id,
            },
        )
        points = forecast_points(profile)
        source_forecast = physical.forecast(points, (steps + 96) * 900, 900)
        forecast, resolution_events = resolve_forecast_missing_occupancy(
            profile,
            source_forecast,
            points,
            steps + 97,
            forecast_phase="evaluation",
            start_time_seconds=evaluation_start,
            step_seconds=900,
        )
        artifacts.write_new_json(
            "forecast_inputs.json",
            build_forecast_evidence(
                points,
                source_forecast,
                forecast,
                start_time_seconds=evaluation_start,
                step_seconds=900,
            ),
        )
        for event in resolution_events:
            artifacts.append_jsonl("timing.jsonl", event)
        manifest["occupancy_forecast_missing_value_resolution_count"] = len(resolution_events)
        state = boundary.state
        last_setpoints = dict(boundary.last_setpoint_c)
        last_pmv = dict(boundary.last_pmv)
        last_occupancy = dict(boundary.last_occupancy)
        enhanced = (
            EnhancedRbcController(zones, repository_root() / profile["program"])
            if plan.controller in {"enhanced-rbc", "hierarchical-mpc"}
            else None
        )
        policy_comfort = ComfortModel(profile["comfort"]) if drl is not None else None
        if observation_builder is not None:
            observation_builder.reset(state)
        mpc: HierarchicalMpcController | None = None
        output_history: NDArray[np.float64] | None = None
        control_history: NDArray[np.float64] | None = None
        if plan.controller == "hierarchical-mpc":
            assert mpc_model is not None
            if (
                mpc_model.identity != manifest["mpc_model_identity"]
                or mpc_model.layout.zones != zones
            ):
                raise ValueError("MPC model identity or zone layout is invalid")
            mpc = HierarchicalMpcController(
                mpc_model,
                profile["objective"],
                load_hierarchical_mpc_config()["excitation"],
            )
            boundary_output = np.asarray(
                [
                    *[zone_temperature_c(profile, state, zone) for zone in zones],
                    site_power(profile, state),
                ],
                dtype=np.float64,
            )
            output_history = np.vstack([boundary_output] * 4)
            control_history = np.vstack(
                [[float(profile["protocol"]["initial_setpoint_c"])] * len(zones)] * 4
            )

        for step in range(steps):
            action_time = evaluation_start + step * 900
            require_time(state, action_time)
            current_occupancy = {
                zone: effective_count(
                    profile["occupancy"],
                    action_time,
                    float(forecast[profile["zones"][zone]["occupancy_forecast"]][step]),
                )
                for zone in zones
            }
            future = _future_occupancy(profile, forecast, zones, step=step, action_time=action_time)
            enhanced_setpoints: dict[str, float] | None = None
            enhanced_diagnostics: dict[str, Any] | None = None
            if enhanced is not None:
                enhanced_setpoints, enhanced_diagnostics = enhanced.decide(
                    occupancy=current_occupancy,
                    future_occupancy=future,
                    last_setpoints_c=last_setpoints,
                    last_pmv=last_pmv,
                    last_occupancy=last_occupancy,
                )
            diagnostics: dict[str, Any]
            if plan.controller == "basic-rbc":
                setpoints = basic_rbc_setpoints(zones, current_occupancy)
                diagnostics = {"status": "scheduled", "method_degraded": False}
            elif plan.controller == "enhanced-rbc":
                assert enhanced_setpoints is not None and enhanced_diagnostics is not None
                setpoints = enhanced_setpoints
                diagnostics = {
                    "status": "canonical_program",
                    "method_degraded": False,
                    "zones": enhanced_diagnostics,
                }
            elif plan.controller in {"c-drl", "h-drl"}:
                assert drl is not None and observation_builder is not None
                packet = observation_builder.build(
                    forecast, step=step, action_time_seconds=action_time, step_seconds=900
                )
                setpoints, policy_diagnostics = drl.decide(packet, current_occupancy)
                diagnostics = {
                    "status": "policy_inference",
                    "method_degraded": False,
                    **policy_diagnostics,
                }
                artifacts.append_jsonl(
                    "observations.jsonl",
                    {
                        "step": step,
                        "time_seconds": action_time,
                        "columns": list(packet.columns),
                        "raw": packet.raw.tolist(),
                        "normalized": packet.normalized.tolist(),
                        "local_normalized": {
                            zone: value.tolist() for zone, value in packet.local_normalized.items()
                        },
                    },
                )
                artifacts.append_jsonl(
                    "policy_inference.jsonl", {"step": step, **policy_diagnostics}
                )
            else:
                assert (
                    mpc is not None and output_history is not None and control_history is not None
                )
                assert enhanced_setpoints is not None
                disturbances, prices, occupancy_horizon, times, daily_means = _mpc_disturbances(
                    profile, forecast, zones, step=step, action_time=action_time
                )
                decision = mpc.decide(
                    step=step,
                    output_history=output_history,
                    control_history=control_history,
                    disturbances=disturbances,
                    prices=prices,
                    occupancy=occupancy_horizon,
                    terminal_occupancy={zone: future[zone][3] for zone in zones},
                    action_times=times,
                    daily_outdoor_means_c=daily_means,
                    comfort=boundary.comfort,
                    previous_setpoints_c=last_setpoints,
                    enhanced_rbc_warm_start=enhanced_setpoints,
                )
                setpoints = decision.setpoints_c
                diagnostics = decision.diagnostics
                artifacts.append_jsonl("solver_trace.jsonl", {"step": step, **diagnostics})
                artifacts.append_jsonl(
                    "predictions.jsonl",
                    {
                        "step": step,
                        "predicted_outputs": diagnostics.get("predicted_outputs"),
                        "negative_power_prediction_count": diagnostics.get(
                            "negative_power_prediction_count", 0
                        ),
                    },
                )
            next_state = physical.advance(control_input(profile, setpoints))
            manifest["lifecycle"]["evaluation_advance_count"] += 1
            require_time(next_state, action_time + 900)
            last_physical_time = action_time + 900
            if physical.test_id != boundary.test_id:
                manifest["lifecycle"]["test_id_changes"] += 1
                raise ValueError("test id changed during baseline evaluation")
            outdoor = forecast[profile["global_inputs"]["outdoor_temperature"]][
                step : step + 97 : 4
            ]
            boundary.comfort.update_clothing(
                action_time, sum(float(value) - 273.15 for value in outdoor) / len(outdoor)
            )
            temperatures = {zone: zone_temperature_c(profile, next_state, zone) for zone in zones}
            pmv = {zone: boundary.comfort.pmv(temperatures[zone]) for zone in zones}
            policy_pmv = pmv
            if policy_comfort is not None:
                policy_pmv = _legacy_policy_pmv(
                    policy_comfort,
                    profile,
                    forecast,
                    temperatures,
                    step=step,
                    action_time=action_time,
                )
                diagnostics["policy_input_clothing_insulation"] = policy_comfort.clothing_insulation
                diagnostics["policy_input_pmv"] = policy_pmv
            power = site_power(profile, next_state)
            price = float(forecast[profile["global_inputs"]["electricity_price"]][step])
            cost = power * 0.25 / 1000.0 * price
            reward = step_reward(
                cost=cost,
                pmv=[pmv[zone] for zone in zones],
                occupancy=[current_occupancy[zone] for zone in zones],
                setpoints_c=[setpoints[zone] for zone in zones],
                previous_setpoints_c=[last_setpoints[zone] for zone in zones],
                objective=profile["objective"],
            )
            for zone in zones:
                artifacts.append_jsonl(
                    "actions.jsonl",
                    {
                        "step": step,
                        "zone": zone,
                        "test_id": boundary.test_id,
                        "action_time_seconds": action_time,
                        "outcome_time_seconds": action_time + 900,
                        "final_setpoint_c": setpoints[zone],
                        "outcome": {
                            "zone_temperature_c": temperatures[zone],
                            "pmv": pmv[zone],
                            "effective_occupancy": current_occupancy[zone],
                            "power_w": power,
                            "electricity_price": price,
                            "cost": cost,
                        },
                    },
                )
            artifacts.append_jsonl("controller_diagnostics.jsonl", {"step": step, **diagnostics})
            artifacts.append_performance(
                (
                    action_time,
                    step,
                    power,
                    cost,
                    reward,
                    _canonical([temperatures[zone] for zone in zones]),
                    _canonical([setpoints[zone] for zone in zones]),
                    _canonical([pmv[zone] for zone in zones]),
                    _canonical([current_occupancy[zone] for zone in zones]),
                )
            )
            if observation_builder is not None:
                observation_builder.update(next_state, setpoints, policy_pmv, power)
            if output_history is not None and control_history is not None:
                output_history = np.vstack(
                    ([*[temperatures[zone] for zone in zones], power], output_history[:-1])
                )
                control_history = np.vstack(
                    ([*[setpoints[zone] for zone in zones]], control_history[:-1])
                )
            state = next_state
            last_setpoints = setpoints
            last_pmv = pmv
            last_occupancy = current_occupancy
        artifacts.append_jsonl(
            "timing.jsonl",
            {
                "phase": "physical_lifecycle",
                "event": "evaluation_completed",
                "time_seconds": evaluation_end,
                "test_id": boundary.test_id,
            },
        )
        artifacts.write_new_json("native_boptest_kpis.json", _native_kpis(physical))
    finally:
        if initialized or physical.test_id is not None:
            stop_attempted = True
            physical.stop()
            manifest["lifecycle"]["stop_count"] += 1
            artifacts.append_jsonl(
                "timing.jsonl",
                {
                    "phase": "physical_lifecycle",
                    "event": "stopped",
                    "time_seconds": last_physical_time,
                    "test_id": frozen_test_id or physical.test_id,
                },
            )
        if artifacts.run_dir.is_dir() and not (artifacts.run_dir / "completion.json").exists():
            manifest["secret_exposure_count"] = secret_occurrences(artifacts.run_dir)
            manifest["secret_scan_status"] = "completed"
            artifacts.replace_json("manifest.json", manifest)
    if not stop_attempted:
        raise AssertionError("baseline execution exited without stopping the physical test")
    metrics = compute_baseline_metrics(artifacts.run_dir)
    artifacts.write_new_json("metrics.json", metrics)
    verification = verify_baseline_run(artifacts.run_dir, require_completion=False)
    artifacts.write_new_json("verification.json", verification)
    if verification["completion_eligible"] is not True:
        raise ValueError(f"baseline verification failed: {verification['errors']}")
    completion = {
        "completion_schema": "h3c_baseline_completion",
        "schema_version": 1,
        "classification": verification["classification"],
        "run_identity": run_identity,
        "elapsed_seconds": time.perf_counter() - started,
    }
    artifacts.publish_completion(completion)
    final = verify_baseline_run(artifacts.run_dir)
    if final["execution_integrity"] is not True:
        raise ValueError(f"baseline completion verification failed: {final['errors']}")
    return {
        "case": plan.case,
        "controller": plan.controller,
        "classification": final["classification"],
        "run_dir": str(artifacts.run_dir),
    }


def execute_baseline_plans(
    plans: Sequence[BaselineRunPlan],
    *,
    suite: str,
    output_root: Path | None = None,
    physical_factory: PhysicalFactory | None = None,
    lock_root: Path | None = None,
) -> dict[str, Any]:
    if not plans:
        raise ValueError("baseline execution requires at least one plan")
    runtime = load_runtime_contract()
    endpoint_name = runtime["physical_service"]["endpoint_environment_variable"]
    endpoint = os.environ.get(endpoint_name, "").rstrip("/")
    if not endpoint:
        raise ValueError(f"{endpoint_name} is required for baseline execution")
    root = (output_root or repository_root() / "outputs" / "baselines" / "runs").resolve()
    resolved_lock_root = (lock_root or repository_root() / "outputs" / "runs").resolve()
    results: list[dict[str, Any]] = []
    with physical_execution_lock(resolved_lock_root):
        for plan in plans:
            results.append(
                _execute_one(
                    plan,
                    suite=suite,
                    endpoint=endpoint,
                    output_root=root,
                    physical_factory=physical_factory or BoptestHttpClient,
                )
            )
    return {"execution": "strictly_serial", "completed_runs": results}


def execute_formal_suite() -> dict[str, Any]:
    return execute_baseline_plans(formal_evaluation_plans(), suite="formal")


def execute_mpc_formal_suite() -> dict[str, Any]:
    return execute_baseline_plans(mpc_formal_evaluation_plans(), suite="mpc-formal")
