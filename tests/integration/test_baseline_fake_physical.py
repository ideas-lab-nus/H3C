from __future__ import annotations

import csv
import json
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from h3c.experiments.profiles import load_profile
from h3c.runtime.comfort import step_reward
from h3c.runtime.occupancy import documented_occupancy_active
from h3c.runtime.protocol import physical_evidence_identity
from h3c_baselines.configuration import BaselineRunPlan
from h3c_baselines.outputs.reporting import generate_report
from h3c_baselines.outputs.verification import verify_baseline_run
from h3c_baselines.runtime.runner import execute_baseline_plans


class FakeBaselinePhysical:
    instances: list[FakeBaselinePhysical] = []

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.test_id: str | None = None
        self.time = 0
        self.initialize_count = 0
        self.advance_count = 0
        self.stop_count = 0
        self.profile = load_profile("SZ_Air")
        self.instances.append(self)

    def _state(self) -> dict[str, Any]:
        value: dict[str, Any] = {"time": self.time}
        for zone in self.profile["zones"].values():
            value[zone["temperature_sensor"]] = 297.15
        for point in self.profile["global_inputs"]["power_meters"]:
            value[point] = 100.0
        return value

    def initialize(
        self, testcase: str, start_time_seconds: int, warmup_period_seconds: int
    ) -> dict[str, Any]:
        assert testcase == self.profile["testcase"]
        assert warmup_period_seconds == 7 * 86400
        self.initialize_count += 1
        self.test_id = "fake-baseline-test"
        self.time = start_time_seconds
        return self._state()

    def forecast(
        self, points: Sequence[str], horizon_seconds: int, interval_seconds: int
    ) -> dict[str, list[float | None]]:
        assert interval_seconds == 900
        length = horizon_seconds // interval_seconds + 1
        result: dict[str, list[float | None]] = {}
        for point in points:
            if point == self.profile["global_inputs"]["outdoor_temperature"]:
                result[point] = [293.15] * length
            elif point == self.profile["global_inputs"]["solar_irradiance"]:
                result[point] = [100.0] * length
            elif point == self.profile["global_inputs"]["electricity_price"]:
                result[point] = [0.1] * length
            else:
                result[point] = [1.0] * length
        return result

    def advance(self, controls: Mapping[str, float]) -> dict[str, Any]:
        assert controls
        self.advance_count += 1
        self.time += 900
        return self._state()

    def get_kpis(self) -> dict[str, Any]:
        assert self.test_id is not None
        return {"cost_tot": 1.0, "ener_tot": 2.0}

    def stop(self) -> None:
        assert self.test_id is not None
        self.stop_count += 1
        self.test_id = None


class FakeMZAirPhysical(FakeBaselinePhysical):
    def __init__(self, endpoint: str) -> None:
        super().__init__(endpoint)
        self.profile = load_profile("MZ_Air")

    def forecast(
        self, points: Sequence[str], horizon_seconds: int, interval_seconds: int
    ) -> dict[str, list[float | None]]:
        values = super().forecast(points, horizon_seconds, interval_seconds)
        outdoor = self.profile["global_inputs"]["outdoor_temperature"]
        values[outdoor] = [
            273.65 + index * 0.2 for index in range(horizon_seconds // interval_seconds + 1)
        ]
        return values


class FakeHydroPhysical(FakeBaselinePhysical):
    def __init__(self, endpoint: str) -> None:
        super().__init__(endpoint)
        self.profile = load_profile("MZ_Hydro")

    def forecast(
        self, points: Sequence[str], horizon_seconds: int, interval_seconds: int
    ) -> dict[str, list[float | None]]:
        values = super().forecast(points, horizon_seconds, interval_seconds)
        length = horizon_seconds // interval_seconds + 1
        missing_index = next(
            index
            for index in range(1, length)
            if documented_occupancy_active(
                self.profile["occupancy"], self.time + index * interval_seconds
            )
        )
        occupancy_points = {
            mapping["occupancy_forecast"] for mapping in self.profile["zones"].values()
        }
        for point in occupancy_points:
            values[point][missing_index] = None
        return values


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_basic_rbc_fake_lifecycle_and_artifact_contract(tmp_path: Path, monkeypatch: Any) -> None:
    FakeBaselinePhysical.instances.clear()
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    result = execute_baseline_plans(
        [BaselineRunPlan("SZ_Air", "basic-rbc", evaluation_hours=1)],
        suite="test",
        output_root=tmp_path / "runs",
        lock_root=tmp_path / "lock",
        physical_factory=FakeBaselinePhysical,
    )
    assert result["completed_runs"][0]["classification"] == "BASELINE-PASS"
    run_dir = Path(result["completed_runs"][0]["run_dir"])
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["lifecycle"] == {
        "initialize_count": 1,
        "conditioning_advance_count": 0,
        "evaluation_advance_count": 4,
        "stop_count": 1,
        "test_id_changes": 0,
    }
    assert (run_dir / "completion.json").is_file()
    assert not (run_dir / "agent_calls.jsonl").exists()
    assert not (run_dir / "observations.jsonl").exists()
    physical = FakeBaselinePhysical.instances[0]
    assert (physical.initialize_count, physical.advance_count, physical.stop_count) == (1, 4, 1)
    assert not (tmp_path / "lock" / ".execution.lock").exists()
    report = generate_report(run_dir, output_root=tmp_path / "report")
    report_dir = Path(report["report_dir"])
    assert (report_dir / "report.md").is_file()
    assert (report_dir / "results.csv").is_file()
    assert (report_dir / "SZ_Air_basic-rbc_timeseries.png").is_file()
    report_payload = json.loads((report_dir / "report.json").read_text(encoding="utf-8"))
    summary = report_payload["runs"][0]
    assert summary["source_commit"] == manifest["source_commit"]
    assert summary["run_identity"] == manifest["run_identity"]
    assert summary["model_sha256"] is None
    assert summary["native_cost_tot"] == 1.0
    report_markdown = (report_dir / "report.md").read_text(encoding="utf-8")
    assert "Native BOPTEST KPIs" in report_markdown

    timing_path = run_dir / "timing.jsonl"
    timing_rows = [
        json.loads(line) for line in timing_path.read_text(encoding="utf-8").splitlines()
    ]
    initialized = next(row for row in timing_rows if row.get("event") == "initialized")
    initialized["warmup_period_seconds"] = 6 * 86400
    timing_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in timing_rows) + "\n",
        encoding="utf-8",
    )
    assert verify_baseline_run(run_dir)["checks"]["lifecycle_timeline"] is False


def test_evaluation_start_internal_warmup_has_no_explicit_prefix_advances(
    tmp_path: Path, monkeypatch: Any
) -> None:
    FakeBaselinePhysical.instances.clear()
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    result = execute_baseline_plans(
        [BaselineRunPlan("SZ_Air", "basic-rbc", evaluation_hours=1)],
        suite="evaluation-start-test",
        output_root=tmp_path / "runs",
        lock_root=tmp_path / "lock",
        physical_factory=FakeBaselinePhysical,
    )
    run_dir = Path(result["completed_runs"][0]["run_dir"])
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["lifecycle"] == {
        "initialize_count": 1,
        "conditioning_advance_count": 0,
        "evaluation_advance_count": 4,
        "stop_count": 1,
        "test_id_changes": 0,
    }
    assert (run_dir / "physical_conditioning.jsonl").read_text(encoding="utf-8") == ""
    physical = FakeBaselinePhysical.instances[0]
    assert (physical.initialize_count, physical.advance_count, physical.stop_count) == (1, 4, 1)


@pytest.mark.parametrize("controller", ["enhanced-rbc", "c-drl"])
def test_program_and_centralized_policy_contracts_verify_on_production_path(
    controller: str, tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    result = execute_baseline_plans(
        [BaselineRunPlan("SZ_Air", controller, evaluation_hours=1)],
        suite="controller-contract-test",
        output_root=tmp_path / "runs",
        lock_root=tmp_path / "lock",
        physical_factory=FakeBaselinePhysical,
    )
    run_dir = Path(result["completed_runs"][0]["run_dir"])
    verification = verify_baseline_run(run_dir)
    assert verification["execution_integrity"] is True
    assert (
        verification["checks"][
            "controller_contract" if controller == "enhanced-rbc" else "policy_contract"
        ]
        is True
    )


def test_baseline_verifier_recomputes_identity_boundary_and_trajectory(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    result = execute_baseline_plans(
        [BaselineRunPlan("SZ_Air", "basic-rbc", evaluation_hours=1)],
        suite="tamper-test",
        output_root=tmp_path / "runs",
        lock_root=tmp_path / "lock",
        physical_factory=FakeBaselinePhysical,
    )
    source = Path(result["completed_runs"][0]["run_dir"])
    assert verify_baseline_run(source)["execution_integrity"] is True

    cases: list[tuple[str, str]] = []

    resolved_copy = tmp_path / "resolved-tamper"
    shutil.copytree(source, resolved_copy)
    resolved = _json(resolved_copy / "resolved_config.json")
    resolved["case_profile"]["evaluation_start_day"] += 1
    _write_json(resolved_copy / "resolved_config.json", resolved)
    cases.append(("resolved_plan_identity", str(resolved_copy)))

    manifest_copy = tmp_path / "manifest-tamper"
    shutil.copytree(source, manifest_copy)
    manifest = _json(manifest_copy / "manifest.json")
    manifest["source_commit"] = "b" * 40
    _write_json(manifest_copy / "manifest.json", manifest)
    cases.append(("manifest_identity", str(manifest_copy)))

    boundary_copy = tmp_path / "boundary-tamper"
    shutil.copytree(source, boundary_copy)
    timing = _jsonl(boundary_copy / "timing.jsonl")
    boundary_row = next(row for row in timing if row.get("phase") == "evaluation_boundary")
    boundary_row["boundary"]["physical_state"]["time"] += 900
    new_identity = physical_evidence_identity(boundary_row["boundary"])
    boundary_row["evaluation_boundary_identity"] = new_identity
    _write_jsonl(boundary_copy / "timing.jsonl", timing)
    manifest = _json(boundary_copy / "manifest.json")
    manifest["evaluation_boundary_identity"] = new_identity
    _write_json(boundary_copy / "manifest.json", manifest)
    cases.append(("evaluation_boundary_identity", str(boundary_copy)))

    test_id_copy = tmp_path / "test-id-tamper"
    shutil.copytree(source, test_id_copy)
    actions = _jsonl(test_id_copy / "actions.jsonl")
    actions[0]["test_id"] = "different-test-id"
    _write_jsonl(test_id_copy / "actions.jsonl", actions)
    cases.append(("test_id_continuity", str(test_id_copy)))

    trajectory_copy = tmp_path / "trajectory-tamper"
    shutil.copytree(source, trajectory_copy)
    actions = _jsonl(trajectory_copy / "actions.jsonl")
    actions[0]["final_setpoint_c"] += 0.5
    _write_jsonl(trajectory_copy / "actions.jsonl", actions)
    cases.append(("trajectory_recomputed", str(trajectory_copy)))

    completion_copy = tmp_path / "completion-tamper"
    shutil.copytree(source, completion_copy)
    completion = _json(completion_copy / "completion.json")
    completion["run_identity"] = "c" * 64
    _write_json(completion_copy / "completion.json", completion)
    cases.append(("completion_identity", str(completion_copy)))

    for expected_check, directory in cases:
        verification = verify_baseline_run(Path(directory))
        assert verification["execution_integrity"] is False
        assert verification["checks"][expected_check] is False


def test_hydro_missing_occupancy_resolution_is_recomputed(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    result = execute_baseline_plans(
        [BaselineRunPlan("MZ_Hydro", "basic-rbc", evaluation_hours=1)],
        suite="hydro-resolution-test",
        output_root=tmp_path / "runs",
        lock_root=tmp_path / "lock",
        physical_factory=FakeHydroPhysical,
    )
    run_dir = Path(result["completed_runs"][0]["run_dir"])
    verification = verify_baseline_run(run_dir)
    assert verification["execution_integrity"] is True
    manifest = _json(run_dir / "manifest.json")
    assert manifest["occupancy_forecast_missing_value_resolution_count"] == 2

    tampered = tmp_path / "hydro-resolution-tamper"
    shutil.copytree(run_dir, tampered)
    rows = _jsonl(tampered / "timing.jsonl")
    event = next(
        row for row in rows if row.get("phase") == "occupancy_forecast_missing_value_resolution"
    )
    event["resolution_rule"] = "documented_nonoccupancy_zero"
    _write_jsonl(tampered / "timing.jsonl", rows)
    failed = verify_baseline_run(tampered)
    assert failed["execution_integrity"] is False
    assert failed["checks"]["occupancy_resolution_evidence"] is False

    deleted = tmp_path / "hydro-resolution-delete-tamper"
    shutil.copytree(run_dir, deleted)
    rows = _jsonl(deleted / "timing.jsonl")
    rows = [
        row for row in rows if row.get("phase") != "occupancy_forecast_missing_value_resolution"
    ]
    _write_jsonl(deleted / "timing.jsonl", rows)
    manifest = _json(deleted / "manifest.json")
    manifest["occupancy_forecast_missing_value_resolution_count"] = 0
    _write_json(deleted / "manifest.json", manifest)
    failed = verify_baseline_run(deleted)
    assert failed["execution_integrity"] is False
    assert failed["checks"]["occupancy_resolution_evidence"] is False


def test_drl_policy_comfort_is_logged_and_reaches_next_observation(
    tmp_path: Path, monkeypatch: Any
) -> None:
    FakeBaselinePhysical.instances.clear()
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    monkeypatch.setattr("h3c_baselines.runtime.runner._source_commit", lambda: "a" * 40)
    result = execute_baseline_plans(
        [BaselineRunPlan("MZ_Air", "h-drl", evaluation_hours=1)],
        suite="policy-comfort-test",
        output_root=tmp_path / "runs",
        lock_root=tmp_path / "lock",
        physical_factory=FakeMZAirPhysical,
    )
    run_dir = Path(result["completed_runs"][0]["run_dir"])
    diagnostics = [
        json.loads(line)
        for line in (run_dir / "controller_diagnostics.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    observations = [
        json.loads(line)
        for line in (run_dir / "observations.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    actions = [
        json.loads(line)
        for line in (run_dir / "actions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert all(row["outcome"]["effective_occupancy"] == 0.0 for row in actions[:5])
    occupancy_feature_indices = [
        index
        for index, name in enumerate(observations[0]["columns"])
        if name.startswith("occupancy_")
    ]
    assert occupancy_feature_indices
    assert all(observations[0]["raw"][index] == 1.0 for index in occupancy_feature_indices)
    assert all("policy_input_clothing_insulation" in row for row in diagnostics)
    first_policy_pmv = diagnostics[0]["policy_input_pmv"]
    second_observation = observations[1]
    pmv_indices = [
        index for index, name in enumerate(second_observation["columns"]) if name.startswith("pmv_")
    ]
    policy_order = ["cor", "nor", "sou", "eas", "wes"]
    assert [second_observation["raw"][index] for index in pmv_indices] == pytest.approx(
        [first_policy_pmv[zone] for zone in policy_order]
    )
    public_pmv = {row["zone"]: row["outcome"]["pmv"] for row in actions[:5]}
    assert any(public_pmv[zone] != first_policy_pmv[zone] for zone in policy_order)

    incomplete = tmp_path / "incomplete-policy-evidence"
    shutil.copytree(run_dir, incomplete)
    observation_rows = _jsonl(incomplete / "observations.jsonl")
    inference_rows = _jsonl(incomplete / "policy_inference.jsonl")
    _write_jsonl(
        incomplete / "observations.jsonl",
        [{"step": row["step"]} for row in observation_rows],
    )
    _write_jsonl(
        incomplete / "policy_inference.jsonl",
        [{"step": row["step"]} for row in inference_rows],
    )
    verification = verify_baseline_run(incomplete)
    assert verification["execution_integrity"] is False
    assert verification["checks"]["policy_contract"] is False

    action_mapping = tmp_path / "policy-action-mapping-tamper"
    shutil.copytree(run_dir, action_mapping)
    inference_rows = _jsonl(action_mapping / "policy_inference.jsonl")
    inference_rows[0]["raw_action"][0] = 0.0
    _write_jsonl(action_mapping / "policy_inference.jsonl", inference_rows)
    verification = verify_baseline_run(action_mapping)
    assert verification["execution_integrity"] is False
    assert verification["checks"]["policy_contract"] is False

    column_order = tmp_path / "policy-column-order-tamper"
    shutil.copytree(run_dir, column_order)
    observation_rows = _jsonl(column_order / "observations.jsonl")
    observation_rows[0]["columns"][0], observation_rows[0]["columns"][1] = (
        observation_rows[0]["columns"][1],
        observation_rows[0]["columns"][0],
    )
    _write_jsonl(column_order / "observations.jsonl", observation_rows)
    verification = verify_baseline_run(column_order)
    assert verification["checks"]["policy_contract"] is False

    normalization = tmp_path / "policy-normalization-tamper"
    shutil.copytree(run_dir, normalization)
    observation_rows = _jsonl(normalization / "observations.jsonl")
    observation_rows[0]["normalized"][0] += 0.01
    _write_jsonl(normalization / "observations.jsonl", observation_rows)
    verification = verify_baseline_run(normalization)
    assert verification["checks"]["policy_contract"] is False

    local_projection = tmp_path / "policy-local-projection-tamper"
    shutil.copytree(run_dir, local_projection)
    observation_rows = _jsonl(local_projection / "observations.jsonl")
    observation_rows[0]["local_normalized"]["cor"][0] += 0.01
    _write_jsonl(local_projection / "observations.jsonl", observation_rows)
    verification = verify_baseline_run(local_projection)
    assert verification["checks"]["policy_contract"] is False

    public_occupancy = tmp_path / "public-occupancy-tamper"
    shutil.copytree(run_dir, public_occupancy)
    action_rows = _jsonl(public_occupancy / "actions.jsonl")
    for row in action_rows[:5]:
        row["outcome"]["effective_occupancy"] = 1.0
    _write_jsonl(public_occupancy / "actions.jsonl", action_rows)
    performance_path = public_occupancy / "performance.csv"
    with performance_path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = list(reader.fieldnames or ())
        performance_rows = list(reader)
    first = performance_rows[0]
    occupancy_values = [1.0] * 5
    first["zone_occupancy"] = json.dumps(occupancy_values, separators=(",", ":"))
    first["step_reward"] = str(
        step_reward(
            cost=float(first["step_cost"]),
            pmv=json.loads(first["zone_pmv"]),
            occupancy=occupancy_values,
            setpoints_c=json.loads(first["zone_setpoints_c"]),
            previous_setpoints_c=[25.0] * 5,
            objective=load_profile("MZ_Air")["objective"],
        )
    )
    with performance_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(performance_rows)
    verification = verify_baseline_run(public_occupancy)
    assert verification["checks"]["trajectory_recomputed"] is False


def test_drl_dependency_preflight_fails_before_artifacts_or_physical_initialize(
    tmp_path: Path, monkeypatch: Any
) -> None:
    physical_factory_calls = 0

    def fail_controller(case: str, controller: str) -> None:
        assert (case, controller) == ("SZ_Air", "c-drl")
        raise RuntimeError("optional baseline dependency is unavailable")

    def physical_factory(endpoint: str) -> FakeBaselinePhysical:
        nonlocal physical_factory_calls
        physical_factory_calls += 1
        return FakeBaselinePhysical(endpoint)

    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    monkeypatch.setattr("h3c_baselines.runtime.runner.FrozenDrlController", fail_controller)
    with pytest.raises(RuntimeError, match="optional baseline dependency is unavailable"):
        execute_baseline_plans(
            [BaselineRunPlan("SZ_Air", "c-drl", evaluation_hours=1)],
            suite="test",
            output_root=tmp_path / "runs",
            lock_root=tmp_path / "lock",
            physical_factory=physical_factory,
        )
    assert physical_factory_calls == 0
    assert not (tmp_path / "runs").exists()
    assert not (tmp_path / "lock" / ".execution.lock").exists()
