from __future__ import annotations

import asyncio
import csv
import json
import shutil
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from h3c.agents.prompts import Role
from h3c.causal.graph import load_graph
from h3c.experiments.matrix import RunPlan, plan_suite
from h3c.experiments.profiles import repository_root
from h3c.experiments.settings import load_runtime_contract
from h3c.outputs.artifacts import RunArtifacts
from h3c.outputs.reporting import generate_report
from h3c.outputs.verification import verify_run
from h3c.runtime import engine as runtime_engine
from h3c.runtime.clients import (
    OpenAICompatibleModelClient,
    TransportError,
    model_logical_call_identity,
    model_request_body,
    model_request_contract,
    model_request_identity,
)
from h3c.runtime.engine import execute_serial


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    values = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert all(isinstance(value, dict) for value in values)
    return values


def _write_jsonl(path: Path, values: Sequence[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(value, sort_keys=True) + "\n" for value in values),
        encoding="utf-8",
    )


class FakePhysicalClient:
    def __init__(self) -> None:
        self.test_id: str | None = None
        self.time_seconds = 0
        self.initialize_count = 0
        self.advance_count = 0
        self.forecast_count = 0
        self.stop_count = 0

    def initialize(
        self, testcase: str, start_time_seconds: int, warmup_period_seconds: int
    ) -> dict[str, Any]:
        assert testcase == "bestest_air"
        assert warmup_period_seconds == 7 * 86400
        self.initialize_count += 1
        self.test_id = "fake-test-id"
        self.time_seconds = start_time_seconds
        return self._state()

    def forecast(
        self, points: Sequence[str], horizon_seconds: int, interval_seconds: int
    ) -> dict[str, list[float | None]]:
        self.forecast_count += 1
        count = horizon_seconds // interval_seconds + 1
        values: dict[str, list[float | None]] = {}
        for point in points:
            if point == "TDryBul":
                values[point] = [298.15] * count
            elif point == "HGloHor":
                values[point] = [100.0] * count
            elif point == "PriceElectricPowerDynamic":
                values[point] = [0.1] * count
            else:
                values[point] = [1.0] * count
        return values

    def advance(self, controls: Mapping[str, float]) -> dict[str, Any]:
        assert "con_oveTSetCoo_u" in controls
        self.advance_count += 1
        self.time_seconds += 900
        return self._state()

    def stop(self) -> None:
        assert self.test_id == "fake-test-id"
        self.stop_count += 1
        self.test_id = None

    def _state(self) -> dict[str, Any]:
        return {
            "time": self.time_seconds,
            "zon_reaTRooAir_y": 297.15,
            "fcu_reaPCoo_y": 100.0,
            "fcu_reaPFan_y": 20.0,
            "fcu_reaPHea_y": 0.0,
        }


class FakeModelClient:
    def __init__(
        self,
        artifacts: RunArtifacts,
        model: str,
        causal_id: str,
        *,
        causal_enabled: bool = True,
        reject_executor_output: bool = False,
        reject_orchestrator_output: bool = False,
        overlong_orchestrator_rationale: bool = False,
        overlong_executor_rationale: bool = False,
        reflector_decimal_insight: bool = False,
        zero_allocation: bool = False,
        recover_first_call_transport: bool = False,
    ) -> None:
        self.artifacts = artifacts
        self.model = model
        self.causal_id = causal_id
        self.causal_enabled = causal_enabled
        self.reject_executor_output = reject_executor_output
        self.reject_orchestrator_output = reject_orchestrator_output
        self.overlong_orchestrator_rationale = overlong_orchestrator_rationale
        self.overlong_executor_rationale = overlong_executor_rationale
        self.reflector_decimal_insight = reflector_decimal_insight
        self.zero_allocation = zero_allocation
        self.recover_first_call_transport = recover_first_call_transport
        self._transport_recovered = False
        self.context: dict[str, Any] = {}
        self.retry_count = 0

    def set_context(self, **context: Any) -> None:
        self.context = context

    async def complete(
        self,
        *,
        role: Role,
        system: str,
        user: str,
        thinking_mode: str,
    ) -> str:
        if role == "orchestrator":
            if self.zero_allocation:
                assert '"zones":["zone1"]' in user
                assert '"site_cap_c":2.5' in user
                assert '"per_zone_cap_c":5.0' in user
            if self.reject_orchestrator_output:
                output = json.dumps(
                    {
                        "site_cap_c": 15.0,
                        "zone_budgets_c": {"zone1": 15.0},
                        "priority": ["zone1"],
                        "rationale_per_zone": {
                            "zone1": (
                                "x" * 241
                                if self.overlong_orchestrator_rationale
                                else "invalid over-cap allocation"
                            )
                        },
                        **({"causal_edge_ids": [self.causal_id]} if self.causal_enabled else {}),
                    }
                )
            else:
                allocation = {
                    "site_cap_c": 0.0 if self.zero_allocation else 2.5,
                    "zone_budgets_c": {"zone1": 0.0 if self.zero_allocation else 2.5},
                    "priority": ["zone1"],
                    "rationale_per_zone": {
                        "zone1": (
                            "x" * 241
                            if self.overlong_orchestrator_rationale
                            else "bounded hourly allowance"
                        )
                    },
                }
                if self.causal_enabled:
                    allocation["causal_edge_ids"] = [self.causal_id]
                output = json.dumps(allocation)
        elif role == "executor":
            output = (
                json.dumps({"unexpected": True})
                if self.reject_executor_output
                else json.dumps(
                    {
                        "patch": [
                            {
                                "op": "no_change",
                                "rationale": (
                                    "y" * 500 if self.overlong_executor_rationale else "hold"
                                ),
                            }
                        ]
                    }
                )
            )
        else:
            output = json.dumps(
                {
                    "pairs": (
                        [
                            {
                                "zone": "zone1",
                                "insight_text": "PMV 1.0125 and cost 0.0 remained stable.",
                            }
                        ]
                        if self.reflector_decimal_insight
                        else []
                    )
                }
            )
        request_contract = model_request_contract(
            model=self.model,
            system=system,
            user=user,
            thinking_mode=thinking_mode,
        )
        request_parameters = {
            key: value for key, value in request_contract.items() if key != "messages"
        }
        request_identity = model_request_identity(request_contract)
        request_body = model_request_body(request_contract)
        logical_call_identity = model_logical_call_identity(
            self.context,
            role,
            thinking_mode,
            request_identity,
        )
        maximum_attempts = load_runtime_contract()["model"]["retry_count"] + 1
        attempt_number = 1
        if self.recover_first_call_transport and not self._transport_recovered:
            self.artifacts.append_jsonl(
                "model_request_attempts.jsonl",
                {
                    **self.context,
                    "role": role,
                    "thinking_mode": thinking_mode,
                    "request_model": self.model,
                    "logical_call_identity": logical_call_identity,
                    "request_identity": request_identity,
                    "request_body": request_body,
                    "attempt_number": 1,
                    "maximum_attempts": maximum_attempts,
                    "outcome": "request_failed",
                    "retryable": True,
                    "will_retry": True,
                    "error_type": "ConnectionResetError",
                    "provider_charge_status": "unknown_after_request_failure",
                    "elapsed_seconds": 0.0,
                },
            )
            self._transport_recovered = True
            self.retry_count += 1
            attempt_number = 2
        self.artifacts.append_jsonl(
            "model_request_attempts.jsonl",
            {
                **self.context,
                "role": role,
                "thinking_mode": thinking_mode,
                "request_model": self.model,
                "logical_call_identity": logical_call_identity,
                "request_identity": request_identity,
                "request_body": request_body,
                "attempt_number": attempt_number,
                "maximum_attempts": maximum_attempts,
                "outcome": "response_received",
                "retryable": False,
                "will_retry": False,
                "error_type": None,
                "provider_charge_status": "confirmed_response_usage_recorded",
                "elapsed_seconds": 0.0,
            },
        )
        common = {
            **self.context,
            "role": role,
            "thinking_mode": thinking_mode,
            "logical_call_identity": logical_call_identity,
            "request_identity": request_identity,
            "attempt_count": attempt_number,
            "transport_retry_count": attempt_number - 1,
            "request_model": self.model,
            "response_model": self.model,
            "finish_reason": "stop",
            "usage": {
                "available": True,
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2,
                "reasoning_tokens": 0,
                "cache_hit_tokens": 0,
                "cache_miss_tokens": 1,
            },
            "provider_usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2,
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": 1,
            },
            "elapsed_seconds": 0.0,
        }
        self.artifacts.append_jsonl("agent_calls.jsonl", {**common, "status": "received"})
        self.artifacts.append_jsonl(
            "raw_model_io.jsonl",
            {
                **common,
                "system": system,
                "user": user,
                "output": output,
                "request_parameters": request_parameters,
            },
        )
        return output


def _baseline() -> RunPlan:
    return RunPlan(
        profile="SZ_Air",
        controller="deterministic_baseline",
        working_memory_hours=1,
        causal_enabled=False,
        coordination_enabled=False,
        thinking_policy="all_roles_disabled",
        graph_mutation=None,
        evaluation_hours=6,
    )


def _hydronic_baseline() -> RunPlan:
    return RunPlan(
        profile="MZ_Hydro",
        controller="deterministic_baseline",
        working_memory_hours=1,
        causal_enabled=False,
        coordination_enabled=False,
        thinking_policy="all_roles_disabled",
        graph_mutation=None,
        evaluation_hours=6,
    )


def _agent() -> RunPlan:
    return RunPlan(
        profile="SZ_Air",
        controller="h3c_agent",
        working_memory_hours=1,
        causal_enabled=True,
        coordination_enabled=True,
        thinking_policy="occupancy_routed",
        graph_mutation=None,
        evaluation_hours=6,
    )


def _causal_off_agent() -> RunPlan:
    return RunPlan(
        profile="SZ_Air",
        controller="h3c_agent",
        working_memory_hours=1,
        causal_enabled=False,
        coordination_enabled=True,
        thinking_policy="occupancy_routed",
        graph_mutation=None,
        evaluation_hours=6,
    )


def _independent_agent() -> RunPlan:
    return RunPlan(
        profile="SZ_Air",
        controller="h3c_agent",
        working_memory_hours=1,
        causal_enabled=True,
        coordination_enabled=False,
        thinking_policy="occupancy_routed",
        graph_mutation=None,
        evaluation_hours=6,
    )


def _no_thinking_agent() -> RunPlan:
    return RunPlan(
        profile="SZ_Air",
        controller="h3c_agent",
        working_memory_hours=1,
        causal_enabled=True,
        coordination_enabled=True,
        thinking_policy="all_roles_disabled",
        graph_mutation=None,
        evaluation_hours=6,
    )


def _shared_power_edge_id(profile: str = "SZ_Air") -> str:
    graph = load_graph(
        repository_root() / "configs" / "graphs" / f"{profile.lower()}_confirmed.json"
    )
    return next(
        edge.identifier
        for edge in graph.edges
        if edge.target == "power_meters" and edge.source != "cooling_setpoint"
    )


class WrongInitializeTimePhysical(FakePhysicalClient):
    def initialize(
        self, testcase: str, start_time_seconds: int, warmup_period_seconds: int
    ) -> dict[str, Any]:
        state = super().initialize(testcase, start_time_seconds, warmup_period_seconds)
        return {**state, "time": start_time_seconds + 900}


class FailingAdvancePhysical(FakePhysicalClient):
    def advance(self, controls: Mapping[str, float]) -> dict[str, Any]:
        raise TransportError("synthetic advance failure")


class FailingForecastPhysical(FakePhysicalClient):
    def forecast(
        self, points: Sequence[str], horizon_seconds: int, interval_seconds: int
    ) -> dict[str, list[float | None]]:
        self.forecast_count += 1
        raise TransportError("synthetic forecast contract failure")


class HydronicMissingOccupancyPhysical(FakePhysicalClient):
    def initialize(
        self, testcase: str, start_time_seconds: int, warmup_period_seconds: int
    ) -> dict[str, Any]:
        assert testcase == "multizone_office_simple_hydronic"
        assert start_time_seconds == 18403200
        assert warmup_period_seconds == 7 * 86400
        self.initialize_count += 1
        self.test_id = "fake-test-id"
        self.time_seconds = start_time_seconds
        return self._state()

    def forecast(
        self, points: Sequence[str], horizon_seconds: int, interval_seconds: int
    ) -> dict[str, list[float | None]]:
        self.forecast_count += 1
        count = horizon_seconds // interval_seconds + 1
        values: dict[str, list[float | None]] = {}
        for point in points:
            if point == "TDryBul":
                values[point] = [298.15] * count
            elif point == "HGloHor":
                values[point] = [100.0] * count
            elif point == "PriceElectricPowerDynamic":
                values[point] = [0.1] * count
            else:
                series: list[float | None] = [50.0] * count
                for timestamp in (18429300, 19031400):
                    offset = timestamp - self.time_seconds
                    if offset >= 0 and offset % interval_seconds == 0:
                        index = offset // interval_seconds
                        if index < count:
                            series[index] = None
                values[point] = series
        return values

    def advance(self, controls: Mapping[str, float]) -> dict[str, Any]:
        assert "bms_oveTZonSetMaxNz_u" in controls
        assert "bms_oveTZonSetMaxSz_u" in controls
        self.advance_count += 1
        self.time_seconds += 900
        return self._state()

    def _state(self) -> dict[str, Any]:
        return {
            "time": self.time_seconds,
            "structure_reaTZonNz_y": 297.15,
            "structure_reaTZonSz_y": 297.15,
            "heating_cooling_reaPFcuNz_y": 100.0,
            "heating_cooling_reaPFcuSz_y": 100.0,
            "heating_cooling_reaPProCoo_y": 20.0,
            "heating_cooling_reaPProHea_y": 0.0,
        }


def test_fake_physical_baseline_has_one_continuous_lifecycle(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    physical = FakePhysicalClient()
    result = execute_serial(
        [_baseline()],
        suite="fake-baseline",
        output_root=tmp_path,
        physical_factory=lambda endpoint: physical,
    )
    completion = Path(result["completed_runs"][0]["completion"])
    assert physical.initialize_count == 1
    assert physical.forecast_count == 2
    assert physical.advance_count == 672 + 24
    assert physical.stop_count == 1
    assert verify_run(completion.parent)["passed"]
    metrics = json.loads((completion.parent / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["physical"]["evaluation_steps"] == 24
    assert metrics["physical"]["energy_kwh"] == pytest.approx(0.72)
    assert metrics["model_calls"]["by_route"] == {}


def test_hydronic_missing_occupancy_resolution_is_audited_and_verified(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    physical = HydronicMissingOccupancyPhysical()
    result = execute_serial(
        [_hydronic_baseline()],
        suite="fake-hydronic-occupancy-resolution",
        output_root=tmp_path,
        physical_factory=lambda endpoint: physical,
    )
    run_dir = Path(result["completed_runs"][0]["completion"]).parent
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    timing = [
        json.loads(line)
        for line in (run_dir / "timing.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    events = [
        row for row in timing if row["phase"] == "occupancy_forecast_missing_value_resolution"
    ]
    conditioning = [
        json.loads(line)
        for line in (run_dir / "physical_conditioning.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert physical.initialize_count == physical.stop_count == 1
    assert physical.forecast_count == 2
    assert physical.advance_count == 672 + 24
    assert manifest["occupancy_forecast_missing_value_resolution_count"] == 6
    assert len(events) == 6
    assert sum(event["forecast_phase"] == "conditioning" for event in events) == 4
    assert sum(event["forecast_phase"] == "evaluation" for event in events) == 2
    missing_row = conditioning[29]
    assert missing_row["raw_occupancy"] == {"NZ": None, "SZ": None}
    assert missing_row["resolved_occupancy"] == {"NZ": 50.0, "SZ": 50.0}
    assert missing_row["effective_occupancy"] == {"NZ": 50.0, "SZ": 50.0}
    nonoccupancy_events = [event for event in events if event["time_seconds"] == 19031400]
    assert len(nonoccupancy_events) == 4
    assert all(event["resolved_value"] == 0.0 for event in nonoccupancy_events)
    assert verify_run(run_dir)["passed"]

    events[0]["documented_occupied"] = not events[0]["documented_occupied"]
    (run_dir / "timing.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in timing) + "\n",
        encoding="utf-8",
    )
    corrupted = verify_run(run_dir)
    assert corrupted["checks"]["occupancy_forecast_missing_value_resolution"] is False


def test_hydronic_formal_profile_evaluates_five_days(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    plan = next(
        candidate
        for candidate in plan_suite("main")
        if candidate.profile == "MZ_Hydro" and candidate.controller == "deterministic_baseline"
    )
    assert plan.evaluation_hours == 120
    physical = HydronicMissingOccupancyPhysical()
    result = execute_serial(
        [plan],
        suite="fake-hydronic-formal-duration",
        output_root=tmp_path,
        physical_factory=lambda endpoint: physical,
    )
    run_dir = Path(result["completed_runs"][0]["completion"]).parent
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert physical.initialize_count == physical.stop_count == 1
    assert physical.advance_count == 672 + 480
    assert metrics["physical"]["evaluation_steps"] == 480
    assert verify_run(run_dir)["passed"]


def test_fake_agent_runs_hourly_roles_and_full_verifier(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    physical = FakePhysicalClient()
    causal_id = _shared_power_edge_id()
    result = execute_serial(
        [_agent()],
        suite="fake-agent",
        output_root=tmp_path,
        physical_factory=lambda endpoint: physical,
        model_factory=lambda artifacts, model: FakeModelClient(artifacts, model, causal_id),
    )
    run_dir = Path(result["completed_runs"][0]["completion"]).parent
    calls = (run_dir / "agent_calls.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(calls) == 18
    assert physical.initialize_count == physical.stop_count == 1
    verification = verify_run(run_dir)
    assert verification["passed"]
    assert verification["checks"]["deterministic_settlement"]
    metrics = _read_json(run_dir / "metrics.json")
    assert set(metrics) == {
        "metrics_schema",
        "schema_version",
        "physical",
        "setpoint_dynamics",
        "program_decisions",
        "action_assurance",
        "orchestration",
        "rationale_telemetry",
        "model_calls",
    }
    assert metrics["program_decisions"] == {
        "accepted": 0,
        "rejected": 0,
        "no_change": 6,
        "model_output_rejected": 0,
        "validation_stage_counts": {
            "causal_admissibility": 6,
            "consistent_program_direction_proof": 6,
            "energy_budget_validation": 6,
            "program_validation": 6,
        },
        "rejection_code_counts": {},
    }
    assert metrics["action_assurance"]["trigger_counts"] == {
        "actuator_bounds": 0,
        "comfort_recovery": 0,
        "setpoint_rate_limit": 0,
    }
    assert metrics["orchestration"]["hours"] == 6
    assert metrics["rationale_telemetry"] == {
        "decision_use": "none",
        "by_role": {
            "executor": {
                "call_count": 6,
                "rationale_count": 6,
                "total_characters": 24,
                "maximum_character_length": 4,
            },
            "orchestrator": {
                "call_count": 6,
                "rationale_count": 6,
                "total_characters": 144,
                "maximum_character_length": 24,
            },
        },
    }
    assert metrics["model_calls"]["by_role"] == {
        "executor": 6,
        "orchestrator": 6,
        "reflector": 6,
    }
    assert metrics["model_calls"]["transport"] == {
        "attempt_count": 18,
        "retry_count": 0,
        "recovered_logical_call_count": 0,
        "failed_attempt_count": 0,
        "terminal_failed_logical_call_count": 0,
        "confirmed_response_count": 18,
        "unknown_provider_charge_attempt_count": 0,
        "attempt_latency_seconds": {
            "total": 0.0,
            "mean": 0.0,
            "maximum": 0.0,
        },
    }
    assert metrics["model_calls"]["usage"] == {
        "available": True,
        "price_book": "project-fixed-v1",
        "prompt_tokens": 18,
        "completion_tokens": 18,
        "total_tokens": 36,
        "reasoning_tokens": 0,
        "cache_hit_tokens": 0,
        "cache_miss_tokens": 18,
        "estimated_cost_usd": pytest.approx(7.56e-06),
        "estimated_cost_cny": pytest.approx(5.4e-05),
    }

    updates_path = run_dir / "program_updates.jsonl"
    updates = updates_path.read_text(encoding="utf-8").splitlines()
    updates_path.write_text("\n".join(updates[:-1]) + "\n", encoding="utf-8")
    corrupted = verify_run(run_dir)
    assert corrupted["checks"]["deterministic_settlement"] is False


def test_recovered_transient_model_request_is_audited_and_release_passes(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    result = execute_serial(
        [_agent()],
        suite="fake-recovered-model-transport",
        output_root=tmp_path,
        physical_factory=lambda endpoint: FakePhysicalClient(),
        model_factory=lambda artifacts, model: FakeModelClient(
            artifacts,
            model,
            _shared_power_edge_id(),
            recover_first_call_transport=True,
        ),
    )
    completed = result["completed_runs"][0]
    run_dir = Path(completed["completion"]).parent
    manifest = _read_json(run_dir / "manifest.json")
    attempts = _read_jsonl(run_dir / "model_request_attempts.jsonl")
    metrics = _read_json(run_dir / "metrics.json")
    verification = verify_run(run_dir)

    assert completed["classification"] == "RELEASE-PASS"
    assert manifest["retry_count"] == 1
    assert manifest["transport_error_count"] == 0
    assert len(attempts) == 19
    assert [row["outcome"] for row in attempts[:2]] == [
        "request_failed",
        "response_received",
    ]
    assert metrics["model_calls"]["count"] == 18
    assert metrics["model_calls"]["transport"]["attempt_count"] == 19
    assert metrics["model_calls"]["transport"]["retry_count"] == 1
    assert metrics["model_calls"]["transport"]["recovered_logical_call_count"] == 1
    assert metrics["model_calls"]["transport"]["confirmed_response_count"] == 18
    assert metrics["model_calls"]["transport"]["unknown_provider_charge_attempt_count"] == 1
    assert verification["checks"]["model_transport_retry_accounting"] is True
    assert verification["passed"] is True

    for field, value in (
        ("error_type", "http_503"),
        ("will_retry", False),
        ("provider_charge_status", "confirmed_response_usage_recorded"),
    ):
        candidate = tmp_path / f"tampered-recovered-transport-{field}"
        shutil.copytree(run_dir, candidate)
        candidate_attempts = _read_jsonl(candidate / "model_request_attempts.jsonl")
        candidate_attempts[0][field] = value
        _write_jsonl(candidate / "model_request_attempts.jsonl", candidate_attempts)
        tampered = verify_run(candidate)
        assert tampered["checks"]["model_transport_retry_accounting"] is False
        assert tampered["classification"] == "RUN-INVALID"


def test_production_retry_does_not_advance_physical_state_between_attempts(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    physical = FakePhysicalClient()
    causal_id = _shared_power_edge_id()
    active_role: list[Role] = ["orchestrator"]
    observed_advance_counts: list[int] = []
    wire_attempt_count = 0

    def request(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal wire_attempt_count
        wire_attempt_count += 1
        observed_advance_counts.append(physical.advance_count)
        if wire_attempt_count == 1:
            raise TransportError(
                "reset",
                retryable=True,
                error_type="ConnectionResetError",
            )
        if active_role[0] == "orchestrator":
            output = json.dumps(
                {
                    "site_cap_c": 2.5,
                    "zone_budgets_c": {"zone1": 2.5},
                    "priority": ["zone1"],
                    "rationale_per_zone": {"zone1": "bounded hourly allowance"},
                    "causal_edge_ids": [causal_id],
                }
            )
        elif active_role[0] == "executor":
            output = json.dumps({"patch": [{"op": "no_change", "rationale": "hold"}]})
        else:
            output = json.dumps({"pairs": []})
        return {
            "model": "deepseek-v4-flash",
            "choices": [{"message": {"content": output}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2,
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": 1,
            },
        }

    async def no_wait(seconds: float) -> None:
        assert seconds == 1.0

    monkeypatch.setattr("h3c.runtime.clients._request_json", request)
    monkeypatch.setattr(asyncio, "sleep", no_wait)

    class TrackingModelClient:
        def __init__(self, artifacts: RunArtifacts, model: str) -> None:
            self.inner = OpenAICompatibleModelClient(
                endpoint="https://fake-model.invalid/v1",
                api_key="test-only-secret",
                model=model,
                sink=lambda name, row: artifacts.append_jsonl(name, row),
                retry_count_limit=2,
                retry_backoff_seconds=(1.0, 2.0),
            )

        @property
        def retry_count(self) -> int:
            return self.inner.retry_count

        def set_context(self, **context: Any) -> None:
            self.inner.set_context(**context)

        async def complete(
            self,
            *,
            role: Role,
            system: str,
            user: str,
            thinking_mode: str,
        ) -> str:
            active_role[0] = role
            before = physical.advance_count
            output = await self.inner.complete(
                role=role,
                system=system,
                user=user,
                thinking_mode=thinking_mode,
            )
            assert physical.advance_count == before
            return output

    result = execute_serial(
        [_agent()],
        suite="fake-production-model-retry",
        output_root=tmp_path,
        physical_factory=lambda endpoint: physical,
        model_factory=lambda artifacts, model: TrackingModelClient(artifacts, model),
    )
    run_dir = Path(result["completed_runs"][0]["completion"]).parent

    assert observed_advance_counts[:2] == [672, 672]
    assert _read_json(run_dir / "manifest.json")["retry_count"] == 1
    assert verify_run(run_dir)["passed"] is True


def test_production_client_retry_exhaustion_records_verifiable_terminal_evidence(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    secret = "terminal-test-secret"
    monkeypatch.setenv("H3C_MODEL_API_KEY", secret)
    physical_clients: list[FakePhysicalClient] = []
    waits: list[float] = []
    wire_attempts = 0
    scan_calls: list[tuple[Path, str]] = []
    real_secret_scan = runtime_engine._secret_occurrences

    def physical_factory(endpoint: str) -> FakePhysicalClient:
        client = FakePhysicalClient()
        physical_clients.append(client)
        return client

    def reset_request(request: urllib.request.Request, timeout: float) -> None:
        nonlocal wire_attempts
        wire_attempts += 1
        raise ConnectionResetError("synthetic reset")

    async def no_wait(seconds: float) -> None:
        waits.append(seconds)

    def scan(directory: Path, value: str) -> int:
        scan_calls.append((directory, value))
        return real_secret_scan(directory, value)

    runtime = load_runtime_contract()["model"]

    def model_factory(artifacts: RunArtifacts, model: str) -> OpenAICompatibleModelClient:
        return OpenAICompatibleModelClient(
            endpoint="https://fake-model.invalid/v1",
            api_key=secret,
            model=model,
            sink=lambda name, row: artifacts.append_jsonl(name, row),
            retry_count_limit=runtime["retry_count"],
            retry_backoff_seconds=tuple(runtime["retry_backoff_seconds"]),
        )

    monkeypatch.setattr(urllib.request, "urlopen", reset_request)
    monkeypatch.setattr(asyncio, "sleep", no_wait)
    monkeypatch.setattr(runtime_engine, "_secret_occurrences", scan)

    with pytest.raises(TransportError, match="ConnectionResetError"):
        execute_serial(
            [_agent(), _agent()],
            suite="fake-terminal-model-transport",
            output_root=tmp_path,
            physical_factory=physical_factory,
            model_factory=model_factory,
        )

    run_dir = next(tmp_path.rglob("manifest.json")).parent
    manifest = _read_json(run_dir / "manifest.json")
    attempts = _read_jsonl(run_dir / "model_request_attempts.jsonl")
    metrics = _read_json(run_dir / "metrics.json")
    recorded_verification = _read_json(run_dir / "verification.json")
    recomputed_verification = verify_run(run_dir, require_completion=False)

    assert wire_attempts == 3
    assert waits == [1.0, 2.0]
    assert len(physical_clients) == 1
    assert physical_clients[0].initialize_count == physical_clients[0].stop_count == 1
    assert physical_clients[0].advance_count == 672
    assert not (tmp_path / ".execution.lock").exists()
    assert not (run_dir / "completion.json").exists()
    assert _read_jsonl(run_dir / "agent_calls.jsonl") == []
    assert _read_jsonl(run_dir / "raw_model_io.jsonl") == []
    assert manifest["retry_count"] == 2
    assert manifest["transport_error_count"] == 1
    assert manifest["secret_scan_status"] == "completed"
    assert manifest["secret_exposure_count"] == 0
    assert scan_calls == [(run_dir, secret)]
    assert [row["attempt_number"] for row in attempts] == [1, 2, 3]
    assert [row["will_retry"] for row in attempts] == [True, True, False]
    assert len({row["request_body"] for row in attempts}) == 1
    assert len({row["request_identity"] for row in attempts}) == 1
    assert len({row["logical_call_identity"] for row in attempts}) == 1
    transport_metrics = metrics["model_calls"]["transport"]
    assert transport_metrics["attempt_count"] == 3
    assert transport_metrics["retry_count"] == 2
    assert transport_metrics["terminal_failed_logical_call_count"] == 1
    assert transport_metrics["confirmed_response_count"] == 0
    assert transport_metrics["unknown_provider_charge_attempt_count"] == 3
    assert recorded_verification == recomputed_verification
    assert recorded_verification["classification"] == "RUN-INVALID"
    assert recorded_verification["completion_eligible"] is False
    assert recorded_verification["checks"]["model_transport_retry_accounting"] is True
    assert recorded_verification["checks"]["metrics_recomputed"] is True
    assert recorded_verification["checks"]["secret_exposure_count_zero"] is True

    for field, value in (
        ("request_identity", "0" * 64),
        ("request_body", "{}"),
        ("attempt_number", 2),
    ):
        candidate = tmp_path / f"tampered-terminal-transport-{field}"
        shutil.copytree(run_dir, candidate)
        candidate_attempts = _read_jsonl(candidate / "model_request_attempts.jsonl")
        candidate_attempts[-1][field] = value
        _write_jsonl(candidate / "model_request_attempts.jsonl", candidate_attempts)
        tampered = verify_run(candidate, require_completion=False)
        assert tampered["checks"]["model_transport_retry_accounting"] is False
        assert tampered["classification"] == "RUN-INVALID"


def test_verifier_recomputes_single_field_tampering(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    result = execute_serial(
        [_agent()],
        suite="fake-verifier-source",
        output_root=tmp_path,
        physical_factory=lambda endpoint: FakePhysicalClient(),
        model_factory=lambda artifacts, model: FakeModelClient(
            artifacts, model, _shared_power_edge_id()
        ),
    )
    source = Path(result["completed_runs"][0]["completion"]).parent
    assert verify_run(source)["passed"]

    def performance_cost(directory: Path) -> None:
        path = directory / "performance.csv"
        with path.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
            fields = list(rows[0])
        rows[0]["step_cost"] = str(float(rows[0]["step_cost"]) + 1.0)
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def zone_outcome(directory: Path) -> None:
        path = directory / "zone_steps.jsonl"
        rows = _read_jsonl(path)
        rows[0]["outcome"]["pmv"] = float(rows[0]["outcome"]["pmv"]) + 0.25
        _write_jsonl(path, rows)

    def action_assurance_audit(directory: Path) -> None:
        path = directory / "zone_steps.jsonl"
        rows = _read_jsonl(path)
        rows[0]["action_assurance"]["final_setpoint"] = 24.0
        _write_jsonl(path, rows)

    def program_hash_identity(directory: Path) -> None:
        path = directory / "program_updates.jsonl"
        rows = _read_jsonl(path)
        rows[0]["current_program_hash"] = "0" * 64
        _write_jsonl(path, rows)

    def resolved_graph_edge(directory: Path) -> None:
        path = directory / "resolved_config.yaml"
        value = _read_json(path)
        value["resolved_graph"]["edges"][0]["id"] = "ce_00000000"
        _write_json(path, value)

    def raw_call_role(directory: Path) -> None:
        path = directory / "raw_model_io.jsonl"
        rows = _read_jsonl(path)
        rows[0]["role"] = "executor"
        _write_jsonl(path, rows)

    def request_contract(directory: Path) -> None:
        path = directory / "raw_model_io.jsonl"
        rows = _read_jsonl(path)
        rows[0]["request_parameters"]["model"] = "unregistered-model"
        _write_jsonl(path, rows)

    def usage_accounting(directory: Path) -> None:
        path = directory / "agent_calls.jsonl"
        rows = _read_jsonl(path)
        rows[0]["usage"]["total_tokens"] = 3
        _write_jsonl(path, rows)

    def expected_call_count(directory: Path) -> None:
        path = directory / "manifest.json"
        value = _read_json(path)
        value["expected_agent_calls"] = 17
        _write_json(path, value)

    def prefix_action(directory: Path) -> None:
        path = directory / "physical_conditioning.jsonl"
        rows = _read_jsonl(path)
        rows[0]["setpoint_c"]["zone1"] = 24.0
        _write_jsonl(path, rows)

    def boundary_state(directory: Path) -> None:
        path = directory / "timing.jsonl"
        rows = _read_jsonl(path)
        event = next(row for row in rows if row.get("phase") == "evaluation_boundary")
        event["boundary"]["physical_state"]["time"] += 900
        _write_jsonl(path, rows)

    def reported_metric(directory: Path) -> None:
        path = directory / "metrics.json"
        value = _read_json(path)
        value["physical"]["total_cost"] += 1.0
        _write_json(path, value)

    def method_identity(directory: Path) -> None:
        path = directory / "resolved_config.yaml"
        value = _read_json(path)
        value["method"]["working_memory_hours"] = 2
        _write_json(path, value)

    def evaluation_test_id(directory: Path) -> None:
        path = directory / "zone_steps.jsonl"
        rows = _read_jsonl(path)
        rows[0]["test_id"] = "tampered-test-id"
        _write_jsonl(path, rows)

    def attempt_number(directory: Path) -> None:
        path = directory / "model_request_attempts.jsonl"
        rows = _read_jsonl(path)
        rows[0]["attempt_number"] = 2
        _write_jsonl(path, rows)

    def attempt_request_identity(directory: Path) -> None:
        path = directory / "model_request_attempts.jsonl"
        rows = _read_jsonl(path)
        rows[0]["request_identity"] = "0" * 64
        _write_jsonl(path, rows)

    def attempt_outcome(directory: Path) -> None:
        path = directory / "model_request_attempts.jsonl"
        rows = _read_jsonl(path)
        rows[0]["outcome"] = "request_failed"
        _write_jsonl(path, rows)

    def attempt_retryability(directory: Path) -> None:
        path = directory / "model_request_attempts.jsonl"
        rows = _read_jsonl(path)
        rows[0]["retryable"] = True
        _write_jsonl(path, rows)

    def attempt_provider_charge_status(directory: Path) -> None:
        path = directory / "model_request_attempts.jsonl"
        rows = _read_jsonl(path)
        rows[0]["provider_charge_status"] = "unknown_after_request_failure"
        _write_jsonl(path, rows)

    def manifest_retry_count(directory: Path) -> None:
        path = directory / "manifest.json"
        value = _read_json(path)
        value["retry_count"] = 1
        _write_json(path, value)

    mutations: list[tuple[str, Callable[[Path], None], str]] = [
        ("performance-cost", performance_cost, "timeline_and_stream_alignment"),
        ("zone-outcome", zone_outcome, "timeline_and_stream_alignment"),
        ("action-assurance", action_assurance_audit, "action_assurance_recomputed"),
        ("program-hash", program_hash_identity, "program_replay_recomputed"),
        ("graph-edge", resolved_graph_edge, "causal_surface"),
        ("raw-role", raw_call_role, "agent_call_alignment"),
        ("request-contract", request_contract, "usage_contract"),
        ("usage-accounting", usage_accounting, "usage_contract"),
        ("expected-calls", expected_call_count, "agent_call_counts"),
        ("prefix-action", prefix_action, "conditioning_prefix_identity"),
        ("boundary-state", boundary_state, "evaluation_boundary_identity"),
        ("reported-metric", reported_metric, "metrics_recomputed"),
        ("method-identity", method_identity, "manifest_identity"),
        ("evaluation-test-id", evaluation_test_id, "test_id_continuity"),
        ("attempt-number", attempt_number, "model_transport_retry_accounting"),
        (
            "attempt-request-identity",
            attempt_request_identity,
            "model_transport_retry_accounting",
        ),
        ("attempt-outcome", attempt_outcome, "model_transport_retry_accounting"),
        (
            "attempt-retryability",
            attempt_retryability,
            "model_transport_retry_accounting",
        ),
        (
            "attempt-provider-charge-status",
            attempt_provider_charge_status,
            "model_transport_retry_accounting",
        ),
        ("manifest-retry-count", manifest_retry_count, "model_transport_retry_accounting"),
    ]
    for name, mutate, expected_failed_check in mutations:
        candidate = tmp_path / f"tampered-{name}"
        shutil.copytree(source, candidate)
        mutate(candidate)
        verification = verify_run(candidate)
        assert verification["checks"][expected_failed_check] is False, name
        assert verification["classification"] == "RUN-INVALID", name


def test_zero_allocation_keeps_complete_priority_and_coordination_surface(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    physical = FakePhysicalClient()
    causal_id = _shared_power_edge_id()
    result = execute_serial(
        [_agent()],
        suite="fake-zero-allocation",
        output_root=tmp_path,
        physical_factory=lambda endpoint: physical,
        model_factory=lambda artifacts, model: FakeModelClient(
            artifacts,
            model,
            causal_id,
            zero_allocation=True,
        ),
    )
    run_dir = Path(result["completed_runs"][0]["completion"]).parent
    decisions = [
        json.loads(line)
        for line in (run_dir / "hourly_decisions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert all(row["orchestration"]["status"] == "accepted" for row in decisions)
    assert all(
        row["orchestration"]["fallback"]
        == {"used": False, "reason": None, "source": None, "validated": False}
        for row in decisions
    )
    assert all(row["energy_budget"]["site_cap_c"] == 0.0 for row in decisions)
    verification = verify_run(run_dir)
    assert verification["checks"]["json_schema"]
    assert verification["checks"]["coordination_surface"]
    assert verification["passed"]


@pytest.mark.parametrize("overlong_rationale", [False, True])
def test_invalid_orchestrator_uses_validated_fallback_and_degraded_completion(
    tmp_path: Path, monkeypatch: Any, overlong_rationale: bool
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    physical = FakePhysicalClient()
    causal_id = _shared_power_edge_id()
    result = execute_serial(
        [_agent()],
        suite="fake-orchestrator-fallback",
        output_root=tmp_path,
        physical_factory=lambda endpoint: physical,
        model_factory=lambda artifacts, model: FakeModelClient(
            artifacts,
            model,
            causal_id,
            reject_orchestrator_output=True,
            overlong_orchestrator_rationale=overlong_rationale,
        ),
    )
    completed = result["completed_runs"][0]
    run_dir = Path(completed["completion"]).parent
    decisions = [
        json.loads(line)
        for line in (run_dir / "hourly_decisions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert completed["classification"] == "EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED"
    assert physical.initialize_count == physical.stop_count == 1
    assert all(row["orchestration"]["raw_contract"]["status"] == "rejected" for row in decisions)
    for index, row in enumerate(decisions):
        expected_source = "equal_split_current_zones" if index == 0 else "previous_valid_allocation"
        assert row["orchestration"]["fallback"] == {
            "used": True,
            "reason": row["orchestration"]["raw_contract"]["rejection"]["message"],
            "source": expected_source,
            "validated": True,
        }
    assert all(row["orchestration"]["allocation_audit"]["site_cap_c"] == 2.5 for row in decisions)
    verification = verify_run(run_dir)
    assert verification["execution_integrity"] is True
    assert verification["model_contract_clean"] is False
    assert verification["classification"] == "EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED"
    assert verification["checks"]["fallback_count_zero"] is False
    assert verification["checks"]["orchestration_resolution_recomputed"] is True

    allocation_target = tmp_path / f"tampered-fallback-allocation-{overlong_rationale}"
    shutil.copytree(run_dir, allocation_target)
    allocation_rows = _read_jsonl(allocation_target / "hourly_decisions.jsonl")
    allocation_rows[0]["orchestration"]["allocation_audit"]["site_cap_c"] = 0.0
    allocation_rows[0]["orchestration"]["allocation_audit"]["zone_budgets_c"] = {"zone1": 0.0}
    allocation_rows[0]["energy_budget"].update(
        {
            "granted_c": 0.0,
            "used_c": 0.0,
            "utilisation": None,
            "site_cap_c": 0.0,
            "residual_initial_c": 0.0,
            "residual_left_c": 0.0,
            "residual_used_by": {},
        }
    )
    _write_jsonl(allocation_target / "hourly_decisions.jsonl", allocation_rows)
    allocation_tamper = verify_run(allocation_target)
    assert allocation_tamper["checks"]["orchestration_resolution_recomputed"] is False

    for field, value in (
        ("source", "previous_valid_allocation"),
        ("reason", "tampered rejection reason"),
    ):
        target = tmp_path / f"tampered-fallback-{field}-{overlong_rationale}"
        shutil.copytree(run_dir, target)
        rows = _read_jsonl(target / "hourly_decisions.jsonl")
        rows[0]["orchestration"]["fallback"][field] = value
        _write_jsonl(target / "hourly_decisions.jsonl", rows)
        tampered = verify_run(target)
        assert tampered["checks"]["orchestration_resolution_recomputed"] is False


def test_arbitrary_length_rationale_is_preserved_without_control_effect(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    causal_id = _shared_power_edge_id()
    result = execute_serial(
        [_agent()],
        suite="fake-rationale-preservation",
        output_root=tmp_path,
        physical_factory=lambda endpoint: FakePhysicalClient(),
        model_factory=lambda artifacts, model: FakeModelClient(
            artifacts,
            model,
            causal_id,
            overlong_orchestrator_rationale=True,
            overlong_executor_rationale=True,
        ),
    )
    completed = result["completed_runs"][0]
    run_dir = Path(completed["completion"]).parent
    decisions = _read_jsonl(run_dir / "hourly_decisions.jsonl")
    updates = _read_jsonl(run_dir / "program_updates.jsonl")
    raw_rows = _read_jsonl(run_dir / "raw_model_io.jsonl")
    metrics = _read_json(run_dir / "metrics.json")
    assert completed["classification"] == "RELEASE-PASS"
    assert all(row["orchestration"]["status"] == "accepted" for row in decisions)
    assert all(row["orchestration"]["raw_contract"]["status"] == "accepted" for row in decisions)
    assert all(
        row["orchestration"]["fallback"]
        == {"used": False, "reason": None, "source": None, "validated": False}
        for row in decisions
    )
    assert all(
        row["orchestration"]["allocation_audit"]["rationale_per_zone"]["zone1"] == "x" * 241
        for row in decisions
    )
    assert all(
        row["orchestration"]["rationale_telemetry"]["character_lengths"] == {"zone1": 241}
        for row in decisions
    )
    assert all(row["patch"]["rationale"] == "y" * 500 for row in updates)
    assert all(
        row["rationale_telemetry"]["character_lengths"] == {"operation": 500} for row in updates
    )
    assert all(
        json.loads(row["output"])["rationale_per_zone"]["zone1"] == "x" * 241
        for row in raw_rows
        if row["role"] == "orchestrator"
    )
    assert all(
        json.loads(row["output"])["patch"][0]["rationale"] == "y" * 500
        for row in raw_rows
        if row["role"] == "executor"
    )
    assert metrics["rationale_telemetry"]["by_role"]["orchestrator"] == {
        "call_count": 6,
        "rationale_count": 6,
        "total_characters": 1446,
        "maximum_character_length": 241,
    }
    assert metrics["rationale_telemetry"]["by_role"]["executor"] == {
        "call_count": 6,
        "rationale_count": 6,
        "total_characters": 3000,
        "maximum_character_length": 500,
    }
    verification = verify_run(run_dir)
    assert verification["execution_integrity"] is True
    assert verification["model_contract_clean"] is True
    assert verification["checks"]["orchestration_resolution_recomputed"] is True
    assert verification["checks"]["rationale_persistence"] is True
    assert verification["checks"]["coordination_surface"] is True
    assert verification["checks"]["fallback_count_zero"] is True
    assert verification["checks"]["json_schema"] is True
    assert verification["checks"]["role_contract_audit"] is True
    report_json, report_markdown = generate_report(
        run_dir, tmp_path / "rationale-preservation-report"
    )
    report = _read_json(report_json)
    assert report["runs"][0]["metrics"]["rationale_telemetry"] == metrics["rationale_telemetry"]
    assert "Rationale length telemetry" in report_markdown.read_text(encoding="utf-8")

    telemetry_target = tmp_path / "tampered-rationale-telemetry"
    shutil.copytree(run_dir, telemetry_target)
    telemetry_rows = _read_jsonl(telemetry_target / "hourly_decisions.jsonl")
    telemetry_rows[0]["orchestration"]["rationale_telemetry"]["maximum_character_length"] = 240
    _write_jsonl(telemetry_target / "hourly_decisions.jsonl", telemetry_rows)
    telemetry_tamper = verify_run(telemetry_target)
    assert telemetry_tamper["checks"]["rationale_persistence"] is False
    assert telemetry_tamper["classification"] == "RUN-INVALID"

    parsed_target = tmp_path / "tampered-parsed-rationale"
    shutil.copytree(run_dir, parsed_target)
    parsed_rows = _read_jsonl(parsed_target / "program_updates.jsonl")
    parsed_rows[0]["patch"]["rationale"] = "tampered"
    _write_jsonl(parsed_target / "program_updates.jsonl", parsed_rows)
    parsed_tamper = verify_run(parsed_target)
    assert parsed_tamper["checks"]["rationale_persistence"] is False
    assert parsed_tamper["classification"] == "RUN-INVALID"

    raw_target = tmp_path / "tampered-raw-rationale"
    shutil.copytree(run_dir, raw_target)
    tampered_raw_rows = _read_jsonl(raw_target / "raw_model_io.jsonl")
    executor_raw = next(row for row in tampered_raw_rows if row["role"] == "executor")
    payload = json.loads(executor_raw["output"])
    payload["patch"][0]["rationale"] = "raw tamper"
    executor_raw["output"] = json.dumps(payload)
    _write_jsonl(raw_target / "raw_model_io.jsonl", tampered_raw_rows)
    raw_tamper = verify_run(raw_target)
    assert raw_tamper["checks"]["rationale_persistence"] is False
    assert raw_tamper["classification"] == "RUN-INVALID"

    metrics_target = tmp_path / "tampered-rationale-metrics"
    shutil.copytree(run_dir, metrics_target)
    tampered_metrics = _read_json(metrics_target / "metrics.json")
    tampered_metrics["rationale_telemetry"]["by_role"]["executor"]["maximum_character_length"] = 240
    (metrics_target / "metrics.json").write_text(json.dumps(tampered_metrics), encoding="utf-8")
    metrics_tamper = verify_run(metrics_target)
    assert metrics_tamper["checks"]["metrics_recomputed"] is False
    assert metrics_tamper["classification"] == "RUN-INVALID"
    with pytest.raises(ValueError, match="failed execution-integrity verification"):
        generate_report(metrics_target, tmp_path / "tampered-rationale-report")


def test_decimal_reflector_insight_survives_real_contract_and_verifier(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    result = execute_serial(
        [_agent()],
        suite="fake-reflector-decimal-insight",
        output_root=tmp_path,
        physical_factory=lambda endpoint: FakePhysicalClient(),
        model_factory=lambda artifacts, model: FakeModelClient(
            artifacts,
            model,
            _shared_power_edge_id(),
            reflector_decimal_insight=True,
        ),
    )
    run_dir = Path(result["completed_runs"][0]["completion"]).parent
    decisions = _read_jsonl(run_dir / "hourly_decisions.jsonl")
    expected = [{"zone": "zone1", "insight_text": "PMV 1.0125 and cost 0.0 remained stable."}]
    assert all(row["reflector_summary"] == expected for row in decisions)
    assert all(row["reflector_contract"]["status"] == "accepted" for row in decisions)
    verification = verify_run(run_dir)
    assert verification["checks"]["json_schema"] is True
    assert verification["checks"]["role_contract_audit"] is True
    assert verification["passed"] is True


def test_fake_causal_off_has_no_agent_surface_leakage(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    physical = FakePhysicalClient()
    result = execute_serial(
        [_causal_off_agent()],
        suite="fake-causal-off",
        output_root=tmp_path,
        physical_factory=lambda endpoint: physical,
        model_factory=lambda artifacts, model: FakeModelClient(
            artifacts, model, "unused", causal_enabled=False
        ),
    )
    run_dir = Path(result["completed_runs"][0]["completion"]).parent
    surface = "\n".join(
        (run_dir / name).read_text(encoding="utf-8").lower()
        for name in ("agent_calls.jsonl", "raw_model_io.jsonl", "program_updates.jsonl")
    )
    assert "causal" not in surface
    assert verify_run(run_dir)["passed"]


def test_fake_independent_coordination_omits_orchestrator_and_budget(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    physical = FakePhysicalClient()
    result = execute_serial(
        [_independent_agent()],
        suite="fake-independent",
        output_root=tmp_path,
        physical_factory=lambda endpoint: physical,
        model_factory=lambda artifacts, model: FakeModelClient(
            artifacts, model, _shared_power_edge_id()
        ),
    )
    run_dir = Path(result["completed_runs"][0]["completion"]).parent
    calls = [
        json.loads(line)
        for line in (run_dir / "agent_calls.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(calls) == 12
    assert all(row["role"] != "orchestrator" for row in calls)
    assert verify_run(run_dir)["passed"]
    raw_path = run_dir / "raw_model_io.jsonl"
    raw_rows = _read_jsonl(raw_path)
    raw_rows[0]["user"] += "\nALLOCATION"
    _write_jsonl(raw_path, raw_rows)
    assert verify_run(run_dir)["checks"]["coordination_surface"] is False


def test_fake_all_roles_no_thinking_uses_disabled_mode(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    physical = FakePhysicalClient()
    result = execute_serial(
        [_no_thinking_agent()],
        suite="fake-no-thinking",
        output_root=tmp_path,
        physical_factory=lambda endpoint: physical,
        model_factory=lambda artifacts, model: FakeModelClient(
            artifacts, model, _shared_power_edge_id()
        ),
    )
    run_dir = Path(result["completed_runs"][0]["completion"]).parent
    calls = [
        json.loads(line)
        for line in (run_dir / "agent_calls.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert calls and all(row["thinking_mode"] == "disabled" for row in calls)
    assert verify_run(run_dir)["passed"]


def test_model_schema_rejection_records_failure_and_continues_next_fresh_arm(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    monkeypatch.setenv("H3C_MODEL_ENDPOINT", "https://fake-model.invalid/v1")
    monkeypatch.setenv("H3C_MODEL_API_KEY", "test-only-secret")
    physical_clients: list[FakePhysicalClient] = []
    model_count = 0

    def physical_factory(endpoint: str) -> FakePhysicalClient:
        client = FakePhysicalClient()
        physical_clients.append(client)
        return client

    def model_factory(artifacts: RunArtifacts, model: str) -> FakeModelClient:
        nonlocal model_count
        model_count += 1
        return FakeModelClient(
            artifacts,
            model,
            _shared_power_edge_id(),
            reject_executor_output=model_count == 1,
        )

    result = execute_serial(
        [_agent(), _agent()],
        suite="fake-schema-rejection",
        output_root=tmp_path,
        physical_factory=physical_factory,
        model_factory=model_factory,
    )
    rejected, accepted = result["completed_runs"]
    rejected_dir = Path(rejected["completion"]).parent
    accepted_dir = Path(accepted["completion"]).parent
    assert rejected["status"] == "complete"
    assert rejected["classification"] == "EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED"
    assert (rejected_dir / "completion.json").is_file()
    assert _read_json(rejected_dir / "manifest.json")["retry_count"] == 0
    assert len(_read_jsonl(rejected_dir / "model_request_attempts.jsonl")) == 18
    assert (
        json.loads((rejected_dir / "verification.json").read_text(encoding="utf-8"))[
            "model_contract_clean"
        ]
        is False
    )
    assert (accepted_dir / "completion.json").is_file()
    assert len(physical_clients) == 2
    assert all(client.initialize_count == client.stop_count == 1 for client in physical_clients)


def test_initialization_identity_failure_hard_stops_without_completion(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    physical = WrongInitializeTimePhysical()
    with pytest.raises(ValueError, match="registered timeline"):
        execute_serial(
            [_baseline()],
            suite="fake-initialize-failure",
            output_root=tmp_path,
            physical_factory=lambda endpoint: physical,
        )
    assert physical.initialize_count == physical.stop_count == 1
    assert list(tmp_path.rglob("completion.json")) == []
    assert not (tmp_path / ".execution.lock").exists()


def test_transport_failure_hard_stops_serial_matrix_without_retry(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    physical_clients: list[FailingAdvancePhysical] = []

    def physical_factory(endpoint: str) -> FailingAdvancePhysical:
        client = FailingAdvancePhysical()
        physical_clients.append(client)
        return client

    with pytest.raises(TransportError, match="synthetic advance failure"):
        execute_serial(
            [_baseline(), _baseline()],
            suite="fake-transport-failure",
            output_root=tmp_path,
            physical_factory=physical_factory,
        )
    assert len(physical_clients) == 1
    assert physical_clients[0].initialize_count == physical_clients[0].stop_count == 1
    manifest_path = next(tmp_path.rglob("manifest.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["transport_error_count"] == 1
    assert list(tmp_path.rglob("completion.json")) == []


def test_forecast_failure_records_successful_initialize_before_stop(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("H3C_BOPTEST_ENDPOINT", "http://fake.invalid")
    physical = FailingForecastPhysical()

    with pytest.raises(TransportError, match="synthetic forecast contract failure"):
        execute_serial(
            [_baseline(), _baseline()],
            suite="fake-forecast-failure",
            output_root=tmp_path,
            physical_factory=lambda endpoint: physical,
        )

    manifest_path = next(tmp_path.rglob("manifest.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["lifecycle"]["initialize_count"] == 1
    assert manifest["lifecycle"]["conditioning_advance_count"] == 0
    assert manifest["lifecycle"]["stop_count"] == 1
    assert manifest["transport_error_count"] == 1
    assert physical.initialize_count == physical.stop_count == 1
    assert physical.forecast_count == 1
    assert list(tmp_path.rglob("completion.json")) == []
