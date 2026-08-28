from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
        self, points: list[str], horizon_seconds: int, interval_seconds: int
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

    def advance(self, controls: dict[str, float]) -> dict[str, Any]:
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
