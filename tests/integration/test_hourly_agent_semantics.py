from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from h3c.agents.prompts import Role
from h3c.agents.roles import ModelCallContext
from h3c.control.budget import validated_fallback_allocation
from h3c.control.program import load_program
from h3c.experiments.matrix import RunPlan
from h3c.experiments.profiles import repository_root
from h3c.memory.caol import empty_regime_store
from h3c.memory.ledger import ProgramLedger
from h3c.outputs.artifacts import RunArtifacts
from h3c.runtime.clients import TransportError
from h3c.runtime.engine import ExecutorBatchTransportError, _agent_hour


def _plan() -> RunPlan:
    return RunPlan(
        profile="SZ_Air",
        controller="h3c_agent",
        working_memory_hours=1,
        causal_enabled=False,
        coordination_enabled=True,
        thinking_policy="all_roles_disabled",
        graph_mutation=None,
        evaluation_hours=6,
    )


def _programs(zones: list[str]) -> dict[str, ProgramLedger]:
    source = repository_root() / "configs" / "programs" / "canonical_cooling_program.json"
    return {zone: ProgramLedger(load_program(source, zone), causal_enabled=False) for zone in zones}


def _observation() -> dict[str, Any]:
    return {
        "zone_temperature_c": 24.0,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "next_hour_occupancy": 1.0,
        "occ_ahead": [1.0, 1.0, 1.0, 1.0],
        "last_pmv": 0.1,
        "last_setpoint": 25.0,
        "electricity_price": 0.1,
        "outdoor_temp_c": 25.0,
        "solar_irr": 100.0,
        "comfort_headroom_c": {"warmer_c": 1.0, "cooler_c": 2.0},
    }


def _artifacts(tmp_path: Path, name: str) -> RunArtifacts:
    artifacts = RunArtifacts(tmp_path, "hourly-semantics", "SZ_Air", name)
    artifacts.create({}, {})
    return artifacts


class PriorityModel:
    def __init__(self, priority: list[str]) -> None:
        self.priority = priority
        self.calls: list[tuple[Role, str | None, str]] = []

    async def complete(
        self,
        *,
        context: ModelCallContext,
        role: Role,
        system: str,
        user: str,
        thinking_mode: str,
    ) -> str:
        del system, thinking_mode
        self.calls.append((role, context.zone, user))
        if role == "orchestrator":
            return json.dumps(
                {
                    "site_cap_c": 5.0,
                    "zone_budgets_c": {"zoneA": 0.0, "zoneB": 0.0},
                    "priority": self.priority,
                    "rationale_per_zone": {"zoneA": "first", "zoneB": "second"},
                }
            )
        if role == "executor":
            return json.dumps(
                {
                    "patch": [
                        {
                            "op": "set_param",
                            "param": "pmv_step_c",
                            "to": 3.3,
                            "rationale": "shared residual candidate",
                        }
                    ]
                }
            )
        raise AssertionError("Reflector is outside _agent_hour")


@pytest.mark.parametrize(
    ("priority", "accepted_zone", "rejected_zone"),
    [(["zoneA", "zoneB"], "zoneA", "zoneB"), (["zoneB", "zoneA"], "zoneB", "zoneA")],
)
def test_two_phase_proposals_use_uncharged_snapshots_then_priority_settlement(
    tmp_path: Path,
    priority: list[str],
    accepted_zone: str,
    rejected_zone: str,
) -> None:
    zones = ["zoneA", "zoneB"]
    model = PriorityModel(priority)
    _, _, audit, updates, _ = asyncio.run(
        _agent_hour(
            plan=_plan(),
            hour=0,
            step=0,
            zones=zones,
            observations={zone: _observation() for zone in zones},
            site_state={},
            route={"thinking_mode": "disabled"},
            graph=None,
            programs=_programs(zones),
            caol_records=[],
            executor_records=[],
            long_term_store=empty_regime_store(zones),
            client=model,
            artifacts=_artifacts(tmp_path, "-".join(priority)),
            previous_allocation=None,
            previous_utilisation=None,
            previous_ledger=None,
            last_rejection_by_zone={zone: None for zone in zones},
        )
    )
    assert [(role, zone) for role, zone, _ in model.calls] == [
        ("orchestrator", None),
        ("executor", "zoneA"),
        ("executor", "zoneB"),
    ]
    executor_users = [user for role, _, user in model.calls if role == "executor"]
    assert len(executor_users) == 2
    assert all('"shared_pool_available_before_settlement_c":5.0' in user for user in executor_users)
    assert all('"zone_reserved_allowance_c":0.0' in user for user in executor_users)
    assert audit is not None and audit["settlement_order"] == priority
    by_zone = {row["zone"]: row for row in updates}
    assert by_zone[accepted_zone]["status"] == "accepted"
    assert by_zone[rejected_zone]["status"] == "rejected"
    assert by_zone[rejected_zone]["rejection"]["code"] == "energy_budget_exhausted"
    assert {row["zone"] for row in updates} == set(zones)


class DelayedPriorityModel(PriorityModel):
    def __init__(self) -> None:
        super().__init__(["zoneB", "zoneA"])
        self.active_executors = 0
        self.maximum_active_executors = 0
        self.executor_completion_order: list[str] = []

    async def complete(
        self,
        *,
        context: ModelCallContext,
        role: Role,
        system: str,
        user: str,
        thinking_mode: str,
    ) -> str:
        if role != "executor":
            return await super().complete(
                context=context,
                role=role,
                system=system,
                user=user,
                thinking_mode=thinking_mode,
            )
        assert context.zone is not None
        self.calls.append((role, context.zone, user))
        self.active_executors += 1
        self.maximum_active_executors = max(self.maximum_active_executors, self.active_executors)
        await asyncio.sleep(0.02 if context.zone == "zoneA" else 0.001)
        self.executor_completion_order.append(context.zone)
        self.active_executors -= 1
        return json.dumps(
            {
                "patch": [
                    {
                        "op": "set_param",
                        "param": "pmv_step_c",
                        "to": 3.3,
                        "rationale": "shared residual candidate",
                    }
                ]
            }
        )


def test_executor_requests_overlap_and_completion_order_does_not_change_settlement(
    tmp_path: Path,
) -> None:
    zones = ["zoneA", "zoneB"]
    model = DelayedPriorityModel()
    _, _, audit, updates, _ = asyncio.run(
        _agent_hour(
            plan=_plan(),
            hour=0,
            step=0,
            zones=zones,
            observations={zone: _observation() for zone in zones},
            site_state={},
            route={"thinking_mode": "disabled"},
            graph=None,
            programs=_programs(zones),
            caol_records=[],
            executor_records=[],
            long_term_store=empty_regime_store(zones),
            client=model,
            artifacts=_artifacts(tmp_path, "delayed-priority"),
            previous_allocation=None,
            previous_utilisation=None,
            previous_ledger=None,
            last_rejection_by_zone={zone: None for zone in zones},
        )
    )

    assert model.maximum_active_executors == 2
    assert model.executor_completion_order == ["zoneB", "zoneA"]
    assert audit is not None and audit["settlement_order"] == ["zoneB", "zoneA"]
    assert [row["zone"] for row in updates] == ["zoneB", "zoneA"]


class FailingExecutorBatchModel(PriorityModel):
    def __init__(self, failed_zones: set[str]) -> None:
        super().__init__(["zoneA", "zoneB"])
        self.failed_zones = failed_zones

    async def complete(
        self,
        *,
        context: ModelCallContext,
        role: Role,
        system: str,
        user: str,
        thinking_mode: str,
    ) -> str:
        if role != "executor":
            return await super().complete(
                context=context,
                role=role,
                system=system,
                user=user,
                thinking_mode=thinking_mode,
            )
        assert context.zone is not None
        await asyncio.sleep(0.02 if context.zone == "zoneA" else 0.001)
        if context.zone in self.failed_zones:
            raise TransportError(
                f"terminal transport for {context.zone}",
                error_type="TimeoutError",
            )
        return json.dumps({"patch": [{"op": "no_change", "rationale": "hold"}]})


@pytest.mark.parametrize("failed_zones", [{"zoneA"}, {"zoneA", "zoneB"}])
def test_terminal_executor_batch_waits_for_all_and_never_settles(
    tmp_path: Path, failed_zones: set[str]
) -> None:
    zones = ["zoneA", "zoneB"]
    artifacts = _artifacts(tmp_path, "failed-" + "-".join(sorted(failed_zones)))
    programs = _programs(zones)

    with pytest.raises(ExecutorBatchTransportError) as raised:
        asyncio.run(
            _agent_hour(
                plan=_plan(),
                hour=0,
                step=0,
                zones=zones,
                observations={zone: _observation() for zone in zones},
                site_state={},
                route={"thinking_mode": "disabled"},
                graph=None,
                programs=programs,
                caol_records=[],
                executor_records=[],
                long_term_store=empty_regime_store(zones),
                client=FailingExecutorBatchModel(failed_zones),
                artifacts=artifacts,
                previous_allocation=None,
                previous_utilisation=None,
                previous_ledger=None,
                last_rejection_by_zone={zone: None for zone in zones},
            )
        )

    expected_failures = tuple(zone for zone in zones if zone in failed_zones)
    assert raised.value.failed_zones == expected_failures
    assert raised.value.primary_zone == expected_failures[0]
    assert all(program.version == 0 for program in programs.values())
    assert (artifacts.run_dir / "program_updates.jsonl").read_text(encoding="utf-8") == ""
    timing = [
        json.loads(line)
        for line in (artifacts.run_dir / "timing.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert timing == [
        {
            "event": "terminal_transport_failure",
            "failed_zones": list(expected_failures),
            "hour": 0,
            "issued_zones": zones,
            "phase": "executor_batch",
            "physical_advance_performed": False,
            "primary_failure_zone": expected_failures[0],
            "settlement_performed": False,
            "step": 0,
        }
    ]


class SequencedModel:
    def __init__(self) -> None:
        self.users: list[str] = []

    async def complete(
        self,
        *,
        context: ModelCallContext,
        role: Role,
        system: str,
        user: str,
        thinking_mode: str,
    ) -> str:
        del system, thinking_mode
        if role == "orchestrator":
            return json.dumps(
                {
                    "site_cap_c": 2.5,
                    "zone_budgets_c": {"zone1": 2.5},
                    "priority": ["zone1"],
                    "rationale_per_zone": {"zone1": "bounded"},
                }
            )
        if role != "executor":
            raise AssertionError("Reflector is outside _agent_hour")
        self.users.append(user)
        if context.hour == 0:
            return json.dumps({"patch": [], "unknown": True})
        if context.hour == 1:
            return json.dumps(
                {
                    "patch": [
                        {
                            "op": "set_param",
                            "param": "pmv_step_c",
                            "to": 99.0,
                            "rationale": "invalid bound",
                        }
                    ]
                }
            )
        return json.dumps({"patch": [{"op": "no_change", "rationale": "hold"}]})


def test_last_rejection_propagates_one_hour_and_clears_after_no_change(
    tmp_path: Path,
) -> None:
    model = SequencedModel()
    programs = _programs(["zone1"])
    last_rejection: dict[str, Any] = {"zone1": None}
    previous_allocation: dict[str, Any] | None = None
    previous_utilisation: dict[str, Any] | None = None
    previous_ledger = None
    for hour in range(4):
        (
            previous_ledger,
            previous_allocation,
            _,
            _,
            _,
        ) = asyncio.run(
            _agent_hour(
                plan=_plan(),
                hour=hour,
                step=hour * 4,
                zones=["zone1"],
                observations={"zone1": _observation()},
                site_state={},
                route={"thinking_mode": "disabled"},
                graph=None,
                programs=programs,
                caol_records=[],
                executor_records=[],
                long_term_store=empty_regime_store(["zone1"]),
                client=model,
                artifacts=_artifacts(tmp_path, f"hour-{hour}"),
                previous_allocation=previous_allocation,
                previous_utilisation=previous_utilisation,
                previous_ledger=previous_ledger,
                last_rejection_by_zone=last_rejection,
            )
        )
        previous_utilisation = previous_ledger.utilisation() if previous_ledger else None
    assert "### LAST REJECTION" not in model.users[0]
    assert "model_output_schema_rejected" in model.users[1]
    assert "out_of_box" in model.users[2]
    assert "### LAST REJECTION" not in model.users[3]
    assert last_rejection == {"zone1": None}


def test_validated_fallback_reuses_previous_or_equal_splits_and_revalidates() -> None:
    previous = {
        "site_cap_c": 2.0,
        "zone_budgets_c": {"zoneA": 1.0, "zoneB": 1.0},
        "priority": ["zoneB", "zoneA"],
        "rationale_per_zone": {"zoneA": "prior", "zoneB": "prior"},
    }
    reused, source = validated_fallback_allocation(
        ["zoneA", "zoneB"],
        previous,
        site_cap_c=5.0,
        causal_enabled=False,
        causal_edge_ids=None,
        allowed_causal_edge_ids=None,
        site_causal_edge_ids=None,
    )
    assert source == "previous_valid_allocation"
    assert reused == previous and reused is not previous

    fallback, source = validated_fallback_allocation(
        ["zoneA", "zoneB"],
        {**previous, "zone_budgets_c": {"zoneA": 4.0, "zoneB": 4.0}},
        site_cap_c=5.0,
        causal_enabled=False,
        causal_edge_ids=None,
        allowed_causal_edge_ids=None,
        site_causal_edge_ids=None,
    )
    assert source == "equal_split_current_zones"
    assert fallback["zone_budgets_c"] == {"zoneA": 2.5, "zoneB": 2.5}
    assert fallback["priority"] == ["zoneA", "zoneB"]
