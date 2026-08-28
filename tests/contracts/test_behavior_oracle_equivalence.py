from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from h3c.assurance.action import ACTION_ASSURANCE_ORDER, action_assurance
from h3c.causal.graph import load_graph
from h3c.control.budget import BudgetLedger
from h3c.control.program import load_program, program_hash
from h3c.control.validation import VALIDATION_STAGES, validate_candidate
from h3c.memory.ledger import ProgramLedger
from h3c.runtime.comfort import MetricsAccumulator
from h3c.runtime.weather import weather_view


def test_accepted_update_current_program_history_version_and_hash_match_oracle(
    canonical_program: dict[str, Any], oracle_fixture: dict[str, Any]
) -> None:
    expected = oracle_fixture["accepted_program_update"]
    assert program_hash(canonical_program) == expected["initial_hash"]
    ledger = ProgramLedger(canonical_program, causal_enabled=False)
    update = ledger.commit(expected["patch"], step=expected["step"], hour=1)
    view = ledger.prompt_view()
    assert update.version_before == expected["version_before"]
    assert update.version_after == expected["version_after"]
    assert update.program_hash_after == expected["program_hash_after"]
    assert view["program_version"] == expected["version_after"]
    assert view["params"] == expected["current_program"]["params"]
    assert [rule["id"] for rule in view["rules"]] == expected["current_program"]["rule_ids"]
    assert [
        {
            "operation": item.patch["op"],
            "step": item.step,
            "target": item.patch["param"],
            "value": item.patch["to"],
        }
        for item in ledger.accepted_updates
    ] == expected["history_view"]
    assert program_hash(ledger.replay()) == expected["program_hash_after"]
    assert "accepted_updates" not in view


def test_causal_direction_and_energy_budget_match_oracle(
    repository_root: Path, oracle_fixture: dict[str, Any]
) -> None:
    expected = oracle_fixture["causal_program_admission"]
    program = load_program(
        repository_root / "configs" / "programs" / "canonical_cooling_program.json", "cor"
    )
    program["params"]["precool_residual_c"] = -4.0
    assert program_hash(program) == expected["source_program_hash"]
    graph = load_graph(repository_root / "configs" / "graphs" / "mz_air_confirmed.json")
    zones = list(graph.zones)
    allocation = {
        "site_cap_c": 5.0,
        "zone_budgets_c": {zone: (5.0 if zone == "cor" else 0.0) for zone in zones},
        "priority": zones,
        "rationale_per_zone": {zone: "fixture" for zone in zones},
        "causal_edge_ids": [expected["completed_causal_edge_ids"][1]],
    }
    budget = BudgetLedger(allocation, zones)
    assert budget.snapshot("cor") == oracle_fixture["energy_budget"]["before"]
    result = validate_candidate(
        expected["input_patch"],
        program,
        graph=graph,
        ledger=budget,
        zone="cor",
        step=10,
    )
    assert result.accepted is expected["accepted"]
    assert result.completed_stages == VALIDATION_STAGES
    assert result.candidate_program is not None
    assert result.effect is not None
    assert program_hash(result.candidate_program) == expected["candidate_program_hash"]
    assert list(result.effect["directions"]) == expected["direction_values"]
    assert result.effect["max_extra_energy_actuation_c"] == expected["energy_intensive_movement_c"]
    assert result.patch["causal_edge_ids"] == expected["completed_causal_edge_ids"]
    assert result.patch["expected_effects"] == expected["expected_effects"]
    proof = result.patch["consistent_program_direction_proof"]
    assert proof["program_direction"] == expected["program_direction"]
    assert proof["expected_effects"] == expected["expected_effects"]
    assert budget.snapshot("cor") == oracle_fixture["energy_budget"]["after"]
    utilisation = budget.utilisation()
    assert utilisation["residual_initial_c"] == 0.0
    for key, value in oracle_fixture["energy_budget"]["utilisation"].items():
        assert utilisation[key] == value


def test_action_assurance_matches_oracle_scenarios(oracle_fixture: dict[str, Any]) -> None:
    for scenario in oracle_fixture["action_assurance"]:
        final, audit = action_assurance(scenario["proposal"], scenario["observation"])
        assert audit["order"] == list(ACTION_ASSURANCE_ORDER)
        assert final == scenario["expected"]["final_setpoint"]
        for field, value in scenario["expected"].items():
            assert audit[field] == value, (scenario["name"], field)


def test_weather_view_matches_oracle(oracle_fixture: dict[str, Any]) -> None:
    fixture = oracle_fixture["weather"]
    assert (
        weather_view(fixture["outdoor_temperature_kelvin"], fixture["solar_irradiance"])
        == fixture["expected"]
    )


def test_metrics_match_oracle(oracle_fixture: dict[str, Any]) -> None:
    fixture = oracle_fixture["metrics"]
    values = fixture["input"]
    accumulator = MetricsAccumulator()
    for index in range(len(values["cost"])):
        accumulator.add(
            cost=values["cost"][index],
            power_w=values["power_w"][index],
            reward=values["reward"][index],
            pmv=values["pmv"][index],
            occupancy=values["occupancy"][index],
        )
    actual = accumulator.resolved()
    for name, value in fixture["expected"].items():
        assert actual[name] == pytest.approx(value)
