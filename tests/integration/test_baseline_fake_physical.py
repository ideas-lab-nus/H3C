from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from h3c.experiments.profiles import load_profile
from h3c_baselines.configuration import BaselineRunPlan
from h3c_baselines.mpc.identification import execute_identification, verify_identification_run
from h3c_baselines.outputs.reporting import generate_report
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
        "conditioning_advance_count": 672,
        "evaluation_advance_count": 4,
        "stop_count": 1,
        "test_id_changes": 0,
    }
    assert (run_dir / "completion.json").is_file()
    assert not (run_dir / "agent_calls.jsonl").exists()
    assert not (run_dir / "observations.jsonl").exists()
    physical = FakeBaselinePhysical.instances[0]
    assert (physical.initialize_count, physical.advance_count, physical.stop_count) == (1, 676, 1)
    assert not (tmp_path / "lock" / ".execution.lock").exists()
    report = generate_report(run_dir, output_root=tmp_path / "report")
    report_dir = Path(report["report_dir"])
    assert (report_dir / "report.md").is_file()
    assert (report_dir / "results.csv").is_file()
    assert (report_dir / "SZ_Air_basic-rbc_timeseries.png").is_file()


def test_legacy_internal_warmup_has_no_explicit_prefix_advances(
    tmp_path: Path, monkeypatch: Any
) -> None:
    FakeBaselinePhysical.instances.clear()
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    result = execute_baseline_plans(
        [
            BaselineRunPlan(
                "SZ_Air",
                "basic-rbc",
                evaluation_hours=1,
                conditioning_mode="legacy_internal_warmup",
            )
        ],
        suite="legacy-replay-test",
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


def test_drl_policy_comfort_is_logged_and_reaches_next_observation(
    tmp_path: Path, monkeypatch: Any
) -> None:
    FakeBaselinePhysical.instances.clear()
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    monkeypatch.setattr("h3c_baselines.runtime.runner._source_commit", lambda: "a" * 40)
    result = execute_baseline_plans(
        [
            BaselineRunPlan(
                "MZ_Air",
                "h-drl",
                evaluation_hours=1,
                conditioning_mode="legacy_internal_warmup",
            )
        ],
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


def test_mpc_identification_is_reproducible_and_evaluation_disjoint(tmp_path: Path) -> None:
    FakeBaselinePhysical.instances.clear()
    result = execute_identification(
        "SZ_Air",
        7,
        endpoint="http://fake-boptest",
        output_root=tmp_path / "identification",
        lock_root=tmp_path / "lock",
        physical_factory=FakeBaselinePhysical,
    )
    run_dir = Path(result["run_dir"])
    verification = verify_identification_run(run_dir)
    assert verification["execution_integrity"] is True
    assert verification["checks"]["model_reproducible"] is True
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["lifecycle"] == {
        "initialize_count": 1,
        "advance_count": 672,
        "stop_count": 1,
    }
    rows = (run_dir / "identification_data.csv").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 674  # header + 672 controlled samples + terminal target state
    assert not (tmp_path / "lock" / ".execution.lock").exists()


def test_mpc_identification_data_tampering_fails_closed(tmp_path: Path) -> None:
    FakeBaselinePhysical.instances.clear()
    result = execute_identification(
        "SZ_Air",
        7,
        endpoint="http://fake-boptest",
        output_root=tmp_path / "identification",
        lock_root=tmp_path / "lock",
        physical_factory=FakeBaselinePhysical,
    )
    run_dir = Path(result["run_dir"])
    source = run_dir / "identification_data.csv"
    original = source.read_text(encoding="utf-8")
    tampered = original.replace("100.0", "101.0", 1)
    assert tampered != original
    source.write_text(tampered, encoding="utf-8")
    verification = verify_identification_run(run_dir)
    assert verification["execution_integrity"] is False
    assert verification["classification"] == "RUN-INVALID"
    assert "identification_data_identity" in verification["errors"]
