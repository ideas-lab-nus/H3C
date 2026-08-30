from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from h3c.experiments.profiles import load_profile
from h3c.runtime.execution_lock import physical_execution_lock
from h3c_baselines.configuration import BaselineRunPlan
from h3c_baselines.runtime import runner


class ConcurrentFakePhysical:
    instances: list[ConcurrentFakePhysical] = []
    instance_lock = threading.Lock()
    first_advance_barrier: threading.Barrier | None = None
    fail_case: str | None = None
    stop_fail_case: str | None = None
    finish_order: list[str] = []

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.test_id: str | None = None
        self.case: str | None = None
        self.profile: dict[str, Any] | None = None
        self.time = 0
        self.initialize_count = 0
        self.advance_count = 0
        self.stop_count = 0
        self.lifecycle_sink: Callable[[Mapping[str, Any]], None] | None = None
        with self.instance_lock:
            self.instances.append(self)

    @classmethod
    def reset(cls) -> None:
        cls.instances = []
        cls.first_advance_barrier = None
        cls.fail_case = None
        cls.stop_fail_case = None
        cls.finish_order = []

    def set_lifecycle_sink(self, sink: Callable[[Mapping[str, Any]], None]) -> None:
        self.lifecycle_sink = sink

    def _emit(self, event: str, status: str | None = None) -> None:
        if self.lifecycle_sink is None:
            return
        row: dict[str, Any] = {
            "phase": "physical_dispatch",
            "event": event,
            "dispatch_mode": "auto",
            "test_id": self.test_id,
            "testcase": None if self.profile is None else self.profile["testcase"],
        }
        if status is not None:
            row["status"] = status
        self.lifecycle_sink(row)

    def _state(self) -> dict[str, Any]:
        assert self.profile is not None
        state: dict[str, Any] = {"time": self.time}
        for zone in self.profile["zones"].values():
            state[zone["temperature_sensor"]] = 297.15
        for point in self.profile["global_inputs"]["power_meters"]:
            state[point] = 100.0
        return state

    def initialize(
        self,
        testcase: str,
        start_time_seconds: int,
        warmup_period_seconds: int,
    ) -> dict[str, Any]:
        profiles = {case: load_profile(case) for case in ("SZ_Air", "MZ_Hydro", "MZ_Air")}
        self.case = next(
            case for case, profile in profiles.items() if profile["testcase"] == testcase
        )
        self.profile = profiles[self.case]
        assert warmup_period_seconds == 7 * 86400
        self.test_id = f"test-{self.case}"
        self.time = start_time_seconds
        self.initialize_count += 1
        self._emit("selected")
        self._emit("status_changed", "Queued")
        self._emit("status_changed", "Running")
        self._emit("configured", "Running")
        self._emit("initialized", "Running")
        return self._state()

    def forecast(
        self,
        points: Sequence[str],
        horizon_seconds: int,
        interval_seconds: int,
    ) -> dict[str, list[float | None]]:
        assert self.profile is not None
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
        assert controls and self.case is not None
        self.advance_count += 1
        if self.advance_count == 1 and self.first_advance_barrier is not None:
            self.first_advance_barrier.wait(timeout=5)
        if self.case == self.fail_case:
            raise RuntimeError(f"advance failed for {self.case}")
        self.time += 900
        return self._state()

    def get_kpis(self) -> dict[str, Any]:
        assert self.case is not None
        delay = {"SZ_Air": 0.06, "MZ_Hydro": 0.03, "MZ_Air": 0.0}[self.case]
        time.sleep(delay)
        return {"cost_tot": 1.0, "ener_tot": 2.0}

    def stop(self) -> None:
        assert self.case is not None and self.test_id is not None
        self.stop_count += 1
        with self.instance_lock:
            self.finish_order.append(self.case)
        if self.case == self.stop_fail_case:
            raise RuntimeError(f"stop failed for {self.case}")
        self._emit("stopped")
        self.test_id = None


def _plans() -> list[BaselineRunPlan]:
    return [
        BaselineRunPlan(case, "basic-rbc", evaluation_hours=1)
        for case in ("SZ_Air", "MZ_Hydro", "MZ_Air")
    ]


def test_concurrent_runner_overlaps_arms_and_reconstructs_registered_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ConcurrentFakePhysical.reset()
    ConcurrentFakePhysical.first_advance_barrier = threading.Barrier(3)
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    source_threads: list[str] = []

    def source_commit() -> str:
        source_threads.append(threading.current_thread().name)
        return "a" * 40

    monkeypatch.setattr(runner, "_source_commit", source_commit)
    lock_roots: list[Path] = []
    original_lock = physical_execution_lock

    @contextmanager
    def tracked_lock(root: Path) -> Iterator[Path]:
        lock_roots.append(root.resolve())
        with original_lock(root) as path:
            yield path

    monkeypatch.setattr("h3c_baselines.runtime.runner.physical_execution_lock", tracked_lock)
    result = runner.execute_baseline_plans_concurrently(
        _plans(),
        suite="concurrent-test",
        output_root=tmp_path / "runs",
        lock_root=tmp_path / "locks",
        physical_factory=ConcurrentFakePhysical,
    )

    assert result["execution"] == "dynamic_concurrent"
    assert result["dispatch_mode"] == "auto"
    assert result["source_commit"] == "a" * 40
    assert source_threads == [threading.main_thread().name]
    assert [row["case"] for row in result["completed_runs"]] == [
        "SZ_Air",
        "MZ_Hydro",
        "MZ_Air",
    ]
    assert ConcurrentFakePhysical.finish_order == ["MZ_Air", "MZ_Hydro", "SZ_Air"]
    run_dirs = [Path(row["run_dir"]).resolve() for row in result["completed_runs"]]
    assert set(run_dirs).issubset(set(lock_roots))
    assert len([path for path in lock_roots if "concurrent-suites" in path.parts]) == 1
    assert not list(tmp_path.rglob(".execution.lock"))
    for run_dir in run_dirs:
        timing = [
            json.loads(line)
            for line in (run_dir / "timing.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        dispatch = [row for row in timing if row.get("phase") == "physical_dispatch"]
        assert [row["event"] for row in dispatch[:5]] == [
            "selected",
            "status_changed",
            "status_changed",
            "configured",
            "initialized",
        ]
        assert [row["status"] for row in dispatch if row["event"] == "status_changed"] == [
            "Queued",
            "Running",
        ]
        assert all(row["dispatch_mode"] == "auto" for row in dispatch)


def test_concurrent_runner_awaits_all_arms_and_preserves_primary_and_stop_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ConcurrentFakePhysical.reset()
    ConcurrentFakePhysical.first_advance_barrier = threading.Barrier(3)
    ConcurrentFakePhysical.fail_case = "MZ_Hydro"
    ConcurrentFakePhysical.stop_fail_case = "MZ_Hydro"
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")

    with pytest.raises(runner.ConcurrentBaselineExecutionError) as raised:
        runner.execute_baseline_plans_concurrently(
            _plans(),
            suite="concurrent-failure-test",
            output_root=tmp_path / "runs",
            lock_root=tmp_path / "locks",
            physical_factory=ConcurrentFakePhysical,
        )

    summary = raised.value.summary
    assert [row["case"] for row in summary["runs"]] == ["SZ_Air", "MZ_Hydro", "MZ_Air"]
    assert [row["case"] for row in summary["completed_runs"]] == ["SZ_Air", "MZ_Air"]
    assert [row["case"] for row in summary["failed_runs"]] == ["MZ_Hydro"]
    assert summary["failed_runs"][0]["failure_evidence_present"] is True
    failed_run = Path(summary["failed_runs"][0]["run_dir"])
    failure = json.loads((failed_run / "failure.json").read_text(encoding="utf-8"))
    failure_details = json.loads((failed_run / "failure_details.json").read_text(encoding="utf-8"))
    assert failure["schema_version"] == 2
    assert failure["failure_details_identity"] == runner._identity(failure_details)
    assert failure_details["primary_failure"] == {
        "type": "RuntimeError",
        "message": "advance failed for MZ_Hydro",
    }
    assert failure_details["stop_failure"] == {
        "type": "RuntimeError",
        "message": "stop failed for MZ_Hydro",
    }
    assert not (failed_run / "completion.json").exists()
    assert not (failed_run / ".failure.pending").exists()
    assert set(ConcurrentFakePhysical.finish_order) == {"SZ_Air", "MZ_Hydro", "MZ_Air"}
    by_case = {instance.case: instance for instance in ConcurrentFakePhysical.instances}
    assert all(instance.initialize_count == 1 for instance in by_case.values())
    assert all(instance.stop_count == 1 for instance in by_case.values())
    assert by_case["SZ_Air"].advance_count == 4
    assert by_case["MZ_Air"].advance_count == 4
    assert by_case["MZ_Hydro"].advance_count == 1
    assert not list(tmp_path.rglob(".execution.lock"))


def test_concurrent_preflight_fails_before_artifacts_threads_or_physical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    source_calls = 0
    physical_calls = 0
    real_prepare = runner._prepare_baseline_run

    def source_commit() -> str:
        nonlocal source_calls
        source_calls += 1
        assert threading.current_thread() is threading.main_thread()
        return "b" * 40

    def prepare(
        plan: BaselineRunPlan,
        *,
        endpoint: str,
        source_commit: str,
        dispatch_mode: str = "strictly_serial",
        suite_identity: str | None = None,
        mpc_freeze_identity: str | None = None,
    ) -> runner._PreparedBaselineRun:
        assert threading.current_thread() is threading.main_thread()
        if plan.case == "MZ_Hydro":
            raise RuntimeError("preflight failed")
        return real_prepare(
            plan,
            endpoint=endpoint,
            source_commit=source_commit,
            dispatch_mode=dispatch_mode,
            suite_identity=suite_identity,
            mpc_freeze_identity=mpc_freeze_identity,
        )

    def physical_factory(endpoint: str) -> ConcurrentFakePhysical:
        nonlocal physical_calls
        physical_calls += 1
        return ConcurrentFakePhysical(endpoint)

    monkeypatch.setattr(runner, "_source_commit", source_commit)
    monkeypatch.setattr(runner, "_prepare_baseline_run", prepare)
    with pytest.raises(RuntimeError, match="preflight failed"):
        runner.execute_baseline_plans_concurrently(
            _plans(),
            suite="preflight-test",
            output_root=tmp_path / "runs",
            lock_root=tmp_path / "locks",
            physical_factory=physical_factory,
        )

    assert source_calls == 1
    assert physical_calls == 0
    assert not (tmp_path / "runs").exists()
    assert not (tmp_path / "locks").exists()


def test_controller_construction_is_a_main_thread_preflight_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    physical_calls = 0

    class RejectedEnhancedController:
        def __init__(self, zones: tuple[str, ...], program: Path) -> None:
            del zones, program
            assert threading.current_thread() is threading.main_thread()
            raise RuntimeError("program preflight failed")

    def physical_factory(endpoint: str) -> ConcurrentFakePhysical:
        nonlocal physical_calls
        physical_calls += 1
        return ConcurrentFakePhysical(endpoint)

    monkeypatch.setattr(runner, "EnhancedRbcController", RejectedEnhancedController)
    with pytest.raises(RuntimeError, match="program preflight failed"):
        runner.execute_baseline_plans_concurrently(
            [BaselineRunPlan("SZ_Air", "enhanced-rbc", evaluation_hours=1)],
            suite="controller-preflight-test",
            output_root=tmp_path / "runs",
            lock_root=tmp_path / "locks",
            physical_factory=physical_factory,
        )

    assert physical_calls == 0
    assert not (tmp_path / "runs").exists()


def test_mpc_model_and_controller_construction_precede_artifacts_and_physical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    physical_calls = 0

    class RejectedMpcController:
        def __init__(self, *args: Any) -> None:
            del args
            assert threading.current_thread() is threading.main_thread()
            raise RuntimeError("MPC construction failed")

    def physical_factory(endpoint: str) -> ConcurrentFakePhysical:
        nonlocal physical_calls
        physical_calls += 1
        return ConcurrentFakePhysical(endpoint)

    monkeypatch.setattr(runner, "_verified_mpc_freeze_identity", lambda: "f" * 64)
    monkeypatch.setattr(runner, "verify_frozen_mpc_model", lambda case: {"valid": True})
    monkeypatch.setattr(
        runner.FittedArxModel,
        "load",
        lambda path: SimpleNamespace(
            identity="m" * 64,
            layout=SimpleNamespace(zones=tuple(load_profile("SZ_Air")["zones"])),
        ),
    )
    monkeypatch.setattr(runner, "HierarchicalMpcController", RejectedMpcController)
    with pytest.raises(RuntimeError, match="MPC construction failed"):
        runner.execute_baseline_plans_concurrently(
            [BaselineRunPlan("SZ_Air", "hierarchical-mpc", evaluation_hours=1)],
            suite="mpc-controller-preflight-test",
            output_root=tmp_path / "runs",
            lock_root=tmp_path / "locks",
            physical_factory=physical_factory,
        )

    assert physical_calls == 0
    assert not (tmp_path / "runs").exists()


def test_artifact_creation_failure_is_finalized_before_terminal_sentinel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    original_create = runner.BaselineArtifacts.create
    physical_calls = 0

    def create_then_fail(self: runner.BaselineArtifacts, *args: Any, **kwargs: Any) -> None:
        original_create(self, *args, **kwargs)
        raise RuntimeError("artifact create failed")

    def physical_factory(endpoint: str) -> ConcurrentFakePhysical:
        nonlocal physical_calls
        physical_calls += 1
        return ConcurrentFakePhysical(endpoint)

    monkeypatch.setattr(runner.BaselineArtifacts, "create", create_then_fail)
    with pytest.raises(runner.ConcurrentBaselineExecutionError) as raised:
        runner.execute_baseline_plans_concurrently(
            [BaselineRunPlan("SZ_Air", "basic-rbc", evaluation_hours=1)],
            suite="artifact-failure-test",
            output_root=tmp_path / "runs",
            lock_root=tmp_path / "locks",
            physical_factory=physical_factory,
        )

    failed_run = Path(raised.value.summary["failed_runs"][0]["run_dir"])
    assert physical_calls == 0
    assert (failed_run / "failure_details.json").is_file()
    assert (failed_run / "failure.json").is_file()
    manifest = json.loads((failed_run / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["secret_scan_status"] == "completed"
    assert manifest["secret_exposure_count"] == 0


def test_method_degraded_result_is_completed_without_resubmission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")
    calls: list[str] = []

    def execute(
        prepared: runner._PreparedBaselineRun,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        calls.append(prepared.plan.case)
        return {
            "case": prepared.plan.case,
            "controller": prepared.plan.controller,
            "classification": (
                "METHOD-DEGRADED" if prepared.plan.case == "MZ_Hydro" else "BASELINE-PASS"
            ),
            "run_dir": str(tmp_path / prepared.plan.case),
            "run_identity": prepared.run_identity,
            "test_id": f"test-{prepared.plan.case}",
        }

    monkeypatch.setattr(runner, "_execute_prepared_concurrent_arm", execute)
    result = runner.execute_baseline_plans_concurrently(
        _plans(),
        suite="method-degraded-test",
        output_root=tmp_path / "runs",
        lock_root=tmp_path / "locks",
        physical_factory=ConcurrentFakePhysical,
    )

    assert sorted(calls) == ["MZ_Air", "MZ_Hydro", "SZ_Air"]
    assert len(calls) == 3
    assert result["failed_runs"] == []
    assert result["completed_runs"][1]["classification"] == "METHOD-DEGRADED"


def test_suite_evidence_rejects_duplicate_cross_arm_test_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake-boptest")

    def execute(
        prepared: runner._PreparedBaselineRun,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        return {
            "case": prepared.plan.case,
            "controller": prepared.plan.controller,
            "classification": "BASELINE-PASS",
            "run_dir": str(tmp_path / prepared.plan.case),
            "run_identity": prepared.run_identity,
            "test_id": "duplicated-test-id",
        }

    monkeypatch.setattr(runner, "_execute_prepared_concurrent_arm", execute)
    with pytest.raises(runner.ConcurrentBaselineExecutionError) as raised:
        runner.execute_baseline_plans_concurrently(
            _plans(),
            suite="duplicate-test-id",
            output_root=tmp_path / "runs",
            lock_root=tmp_path / "locks",
            physical_factory=ConcurrentFakePhysical,
        )

    assert raised.value.summary["suite_evidence_valid"] is False
    assert "cross_arm_test_identity" in raised.value.summary["suite_evidence_errors"]


def test_mpc_formal_suite_uses_the_dynamic_concurrent_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plans = _plans()
    calls: list[tuple[Sequence[BaselineRunPlan], str]] = []

    def execute(selected: Sequence[BaselineRunPlan], *, suite: str) -> dict[str, Any]:
        calls.append((selected, suite))
        return {"execution": "dynamic_concurrent"}

    monkeypatch.setattr(runner, "mpc_formal_evaluation_plans", lambda: plans)
    monkeypatch.setattr(runner, "execute_baseline_plans_concurrently", execute)

    assert runner.execute_mpc_formal_suite() == {"execution": "dynamic_concurrent"}
    assert calls == [(plans, "mpc-formal")]
