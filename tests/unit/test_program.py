from __future__ import annotations

import copy
from typing import Any

import pytest

from h3c.control.program import (
    MAX_PROGRAM_RULES,
    ProgramError,
    apply_patch,
    cited_weather_drivers,
    current_interpreter_derivation,
    interpreter_semantics,
    program_hash,
    rule_effects_if_matched,
    run_program,
    setpoint_effect_facts,
)
from h3c.memory.ledger import ProgramLedger


def test_canonical_program_matches_oracle(
    canonical_program: dict[str, Any], oracle_fixture: dict[str, Any]
) -> None:
    assert program_hash(canonical_program) == oracle_fixture["canonical_program_hash"]
    for fixture in oracle_fixture["interpreter"]:
        actual = run_program(canonical_program, fixture["observation"])
        expected = fixture["expected"]
        assert actual["setpoint"] == pytest.approx(expected["setpoint"])
        assert actual["base_setpoint"] == pytest.approx(expected["base_setpoint"])
        assert actual["base"] == pytest.approx(expected["base"])
        assert actual["residual"] == pytest.approx(expected["residual"])
        assert actual["matched_rule"] == expected["matched_rule"]
        assert actual["exempt_rate"] is expected["exempt_rate"]
        assert actual["branch"] == expected["semantic_branch"]


def _observation(
    *, current: float, previous: float, last_setpoint: float, last_pmv: float = 0.0
) -> dict[str, Any]:
    return {
        "current_occupancy": current,
        "last_occupancy": previous,
        "last_pmv": last_pmv,
        "last_setpoint": last_setpoint,
        "occ_ahead": [current, current, current, current],
    }


@pytest.mark.parametrize(
    ("action", "observation", "expected"),
    (
        (
            {"op": "set_residual", "value": 0.0},
            _observation(current=0, previous=0, last_setpoint=26.85),
            30.0,
        ),
        (
            {"op": "hold_setpoint"},
            _observation(current=0, previous=0, last_setpoint=26.85),
            26.85,
        ),
        (
            {"op": "hold_setpoint"},
            _observation(current=0, previous=0, last_setpoint=20.0),
            25.0,
        ),
        (
            {"op": "step_setpoint", "value": 0.3},
            _observation(current=1, previous=1, last_setpoint=26.0),
            26.3,
        ),
        (
            {"op": "step_setpoint", "value": 0.3},
            _observation(current=1, previous=0, last_setpoint=30.0),
            25.3,
        ),
    ),
)
def test_three_rule_actions_follow_the_published_interpreter_semantics(
    canonical_program: dict[str, Any],
    action: dict[str, Any],
    observation: dict[str, Any],
    expected: float,
) -> None:
    program = copy.deepcopy(canonical_program)
    current = 1 if observation["current_occupancy"] else 0
    program["rules"] = [
        {
            "id": "semantic_fixture",
            "when": [{"field": "occupied_now", "op": "==", "value": current}],
            "then": action,
        }
    ]
    assert run_program(program, observation)["setpoint"] == pytest.approx(expected)
    projected = next(
        row
        for row in rule_effects_if_matched(program, observation)[action["op"]]
        if row["matching_current_occupancy"] == int(bool(observation["current_occupancy"]))
        and row["matching_previous_occupancy"] == int(bool(observation["last_occupancy"]))
    )
    assert projected[
        "interpreter_setpoint_c_after_residual_and_hard_clips_before_assurance"
    ] == pytest.approx(expected)


def test_ordered_program_executes_only_the_first_matching_rule(
    canonical_program: dict[str, Any],
) -> None:
    program = copy.deepcopy(canonical_program)
    program["rules"] = [
        {
            "id": "first",
            "when": [{"field": "occupied_now", "op": "==", "value": 1}],
            "then": {"op": "set_residual", "value": 1.0},
        },
        {
            "id": "second",
            "when": [
                {"field": "occupied_now", "op": "==", "value": 1},
                {"field": "last_pmv", "op": ">", "value": -0.5},
            ],
            "then": {"op": "set_residual", "value": -1.0},
        },
    ]
    result = run_program(
        program,
        _observation(current=1, previous=1, last_setpoint=25.0, last_pmv=0.0),
    )
    assert result["matched_rule"] == "first"
    assert result["rules_fired"] == ["first"]
    assert result["setpoint"] == pytest.approx(26.0)


def test_agent_semantic_projection_uses_interpreter_owners() -> None:
    semantics = interpreter_semantics()
    assert semantics["rule_evaluation"] == "top_to_bottom_first_matching_rule_only"
    assert set(semantics["action_formulas"]) == {
        "set_residual",
        "step_setpoint",
        "hold_setpoint",
    }
    assert MAX_PROGRAM_RULES == 8
    assert setpoint_effect_facts(current_occupancy=0, applied_setpoint_c=26.85) == {
        "regime_base_setpoint_c": 30.0,
        "setpoint_offset_from_regime_base_c": pytest.approx(-3.15),
        "cooling_effect_relative_to_regime_base": "more_cooling_than_regime_base",
    }


def test_current_interpreter_derivation_is_the_executable_result(
    canonical_program: dict[str, Any],
) -> None:
    program = copy.deepcopy(canonical_program)
    program["rules"] = [
        {
            "id": "retain_unoccupied_setpoint",
            "when": [{"field": "occupied_now", "op": "==", "value": 0}],
            "then": {"op": "hold_setpoint"},
        }
    ]
    observation = _observation(current=0, previous=0, last_setpoint=26.85)
    derivation = current_interpreter_derivation(program, observation)
    result = run_program(program, observation)
    assert derivation == {
        "rule_match_status": "matched",
        "first_matching_rule_id": "retain_unoccupied_setpoint",
        "first_matching_action": {"op": "hold_setpoint"},
        "regime_base_setpoint_c": result["base_setpoint"],
        "last_physical_setpoint_c": 26.85,
        "residual_after_clamp_c": result["residual"],
        "interpreter_setpoint_before_assurance_c": result["setpoint"],
        "setpoint_change_from_last_physical_c": 0.0,
        "cooling_effect_relative_to_last_physical_setpoint": (
            "unchanged_from_last_physical_setpoint"
        ),
        "interpreter_branch": result["branch"],
    }


def test_rule_effect_projection_closes_occupancy_onset_anchor_semantics(
    canonical_program: dict[str, Any],
) -> None:
    projection = rule_effects_if_matched(
        canonical_program,
        _observation(current=0, previous=0, last_setpoint=30.0),
    )
    anchor = next(item for item in projection["set_residual"] if item["rule_id"] == "anchor")
    assert anchor == {
        "rule_id": "anchor",
        "rule_order_index": 3,
        "matching_current_occupancy": 1,
        "matching_previous_occupancy": 0,
        "resolved_value_c": 0.0,
        "regime_base_setpoint_c": 25.0,
        "formula": "regime_base_setpoint_c + resolved_value_c",
        "last_setpoint_basis": "independent_of_visible_current_last_physical_setpoint",
        "visible_current_last_physical_setpoint_c": 30.0,
        "candidate_setpoint_c": 25.0,
        "interpreter_setpoint_c_after_residual_and_hard_clips_before_assurance": 25.0,
        "offset_from_regime_base_c": 0.0,
        "cooling_effect_relative_to_regime_base": "at_regime_base",
    }


def test_rule_effect_projection_closes_unoccupied_hold_semantics(
    canonical_program: dict[str, Any],
) -> None:
    # This is the actual pre-edit information available to the Executor: the target
    # rule's matching-state base/result plus the generic proposed-action formula.
    assert (
        interpreter_semantics()["action_formulas"]["hold_setpoint"]
        == "candidate_setpoint_c = last_physical_setpoint_c"
    )
    projection = rule_effects_if_matched(
        canonical_program,
        _observation(current=0, previous=0, last_setpoint=26.85),
    )
    unoccupied = [
        item for item in projection["set_residual"] if item["rule_id"] == "unoccupied_hold"
    ]
    assert [item["matching_previous_occupancy"] for item in unoccupied] == [0, 1]
    assert all(item["resolved_value_c"] == 0.0 for item in unoccupied)
    assert all(item["regime_base_setpoint_c"] == 30.0 for item in unoccupied)
    assert all(
        item["last_setpoint_basis"] == "independent_of_visible_current_last_physical_setpoint"
        for item in unoccupied
    )
    assert all(item["visible_current_last_physical_setpoint_c"] == 26.85 for item in unoccupied)
    assert all(
        item["interpreter_setpoint_c_after_residual_and_hard_clips_before_assurance"] == 30.0
        for item in unoccupied
    )
    assert all(
        item["cooling_effect_relative_to_regime_base"] == "at_regime_base" for item in unoccupied
    )

    edited = copy.deepcopy(canonical_program)
    next(item for item in edited["rules"] if item["id"] == "unoccupied_hold")["then"] = {
        "op": "hold_setpoint"
    }
    held = next(
        item
        for item in rule_effects_if_matched(
            edited,
            _observation(current=0, previous=0, last_setpoint=26.85),
        )["hold_setpoint"]
        if item["rule_id"] == "unoccupied_hold"
    )
    assert held[
        "interpreter_setpoint_c_after_residual_and_hard_clips_before_assurance"
    ] == pytest.approx(26.85)
    assert held["last_setpoint_basis"] == "uses_visible_current_last_physical_setpoint"
    assert held["visible_current_last_physical_setpoint_c"] == pytest.approx(26.85)
    assert held["cooling_effect_relative_to_regime_base"] == "more_cooling_than_regime_base"


def test_patch_and_full_ledger_replay_are_identical(canonical_program: dict[str, Any]) -> None:
    patch = {
        "op": "set_param",
        "param": "pmv_band_hi",
        "to": 0.4,
        "causal_edge_ids": ["ce_00000000"],
        "rationale": "tighten the current upper band",
    }
    expected = apply_patch(canonical_program, patch)
    ledger = ProgramLedger(canonical_program)
    update = ledger.commit(patch, step=4, hour=1)
    replayed = ledger.replay()
    assert program_hash(replayed) == program_hash(expected)
    assert update.program_hash_after == program_hash(expected)
    assert ledger.prompt_view()["program_version"] == 1
    assert "accepted_updates" not in ledger.prompt_view()


def test_patch_rejects_unknown_fields(canonical_program: dict[str, Any]) -> None:
    patch = {
        "op": "set_param",
        "param": "pmv_band_hi",
        "to": 0.4,
        "causal_edge_ids": ["ce_00000000"],
        "rationale": "bounded edit",
        "direct_setpoint": 20,
    }
    with pytest.raises(ProgramError, match="unknown patch fields"):
        apply_patch(canonical_program, patch)


def test_weather_rule_requires_explicit_weather_input(canonical_program: dict[str, Any]) -> None:
    rule = {
        "id": "weather_save",
        "when": [
            {"field": "occupied_now", "op": "==", "value": 1},
            {"field": "outdoor_temp_change_next_1h_c", "op": ">=", "value": 0.5},
        ],
        "then": {"op": "step_setpoint", "value": 0.3},
    }
    patch = {
        "op": "add_rule",
        "rule": rule,
        "index": 0,
        "causal_edge_ids": ["ce_00000000"],
        "rationale": "use the declared weather condition",
    }
    candidate = apply_patch(canonical_program, patch)
    observation = {
        "current_occupancy": 1,
        "last_occupancy": 1,
        "last_pmv": 0.2,
        "last_setpoint": 25.0,
        "occ_ahead": [1, 1, 1, 1],
    }
    with pytest.raises(ProgramError, match="weather condition input is missing"):
        run_program(candidate, observation)


def test_weather_citation_scope_is_limited_to_rules_affected_by_patch(
    canonical_program: dict[str, Any],
) -> None:
    program = apply_patch(
        canonical_program,
        {
            "op": "add_rule",
            "rule": {
                "id": "solar_rule",
                "when": [{"field": "solar_irr_max_next_1h_w_m2", "op": ">=", "value": 400.0}],
                "then": {"op": "step_setpoint", "value": 0.3},
            },
            "index": 0,
            "causal_edge_ids": ["ce_00000000"],
            "rationale": "add a weather-conditioned rule",
        },
    )
    unrelated = {
        "op": "replace_rule",
        "rule": {
            "id": "occupied_hold",
            "when": [{"field": "occupied_now", "op": "==", "value": 1}],
            "then": {"op": "set_residual", "value": 1.5},
        },
        "causal_edge_ids": ["ce_00000000"],
        "rationale": "change only the non-weather occupied rule",
    }
    assert cited_weather_drivers(unrelated, program) == set()

    affected = copy.deepcopy(unrelated)
    affected["rule"] = copy.deepcopy(program["rules"][0])
    affected["rule"]["then"]["value"] = 0.2
    assert cited_weather_drivers(affected, program) == {"solar_irr"}


def test_parameter_weather_citation_scope_follows_actual_references(
    canonical_program: dict[str, Any],
) -> None:
    assert (
        cited_weather_drivers(
            {
                "op": "set_param",
                "param": "pmv_band_lo",
                "to": -0.5,
                "causal_edge_ids": ["ce_00000000"],
                "rationale": "change the PMV comparator",
            },
            canonical_program,
        )
        == set()
    )

    program = copy.deepcopy(canonical_program)
    program["rules"].insert(
        0,
        {
            "id": "solar_param_rule",
            "when": [{"field": "solar_irr_max_next_1h_w_m2", "op": ">=", "value": 400.0}],
            "then": {"op": "step_setpoint", "value": {"param": "pmv_step_c"}},
        },
    )
    assert cited_weather_drivers(
        {
            "op": "set_param",
            "param": "pmv_step_c",
            "to": 0.2,
            "causal_edge_ids": ["ce_00000000"],
            "rationale": "change a parameter used by a weather rule",
        },
        program,
    ) == {"solar_irr"}


def test_exact_direction_proof_fails_before_combinatorial_witness_expansion(
    canonical_program: dict[str, Any],
) -> None:
    first = apply_patch(
        canonical_program,
        {
            "op": "add_rule",
            "index": 0,
            "rule": {
                "id": "weather_partition_0",
                "when": [
                    {
                        "field": "outdoor_temp_change_next_1h_c",
                        "op": ">=",
                        "value": 1.0,
                    },
                    {
                        "field": "solar_irr_max_next_1h_w_m2",
                        "op": ">=",
                        "value": 300.0,
                    },
                    {
                        "field": "solar_irr_mean_next_1h_w_m2",
                        "op": ">=",
                        "value": 200.0,
                    },
                ],
                "then": {"op": "hold_setpoint"},
            },
            "rationale": "first legal weather partition fixture",
        },
        causal_enabled=False,
    )
    with pytest.raises(ProgramError) as captured:
        apply_patch(
            first,
            {
                "op": "add_rule",
                "index": 0,
                "rule": {
                    "id": "weather_partition_1",
                    "when": [
                        {
                            "field": "outdoor_temp_change_next_1h_c",
                            "op": ">=",
                            "value": 10.0,
                        },
                        {
                            "field": "solar_irr_max_next_1h_w_m2",
                            "op": ">=",
                            "value": 600.0,
                        },
                        {
                            "field": "solar_irr_mean_next_1h_w_m2",
                            "op": ">=",
                            "value": 500.0,
                        },
                    ],
                    "then": {"op": "set_residual", "value": 1.0},
                },
                "rationale": "second legal weather partition fixture",
            },
            causal_enabled=False,
        )
    assert captured.value.code == "direction_proof_complexity_limit"


@pytest.mark.parametrize(
    "patch",
    [
        {"op": "no_change", "rationale": "retain the current program"},
        {
            "op": "set_param",
            "param": "pmv_band_hi",
            "to": 0.4,
            "causal_edge_ids": ["ce_00000000"],
            "rationale": "change one existing parameter",
        },
        {
            "op": "add_rule",
            "index": 0,
            "rule": {
                "id": "weather_observed",
                "when": [
                    {
                        "field": "outdoor_temp_change_next_1h_c",
                        "op": ">=",
                        "value": 0.5,
                    }
                ],
                "then": {"op": "set_residual", "value": 0.2},
            },
            "causal_edge_ids": ["ce_00000000"],
            "rationale": "add a uniquely identified rule at a zero-based index",
        },
        {
            "op": "replace_rule",
            "rule": {
                "id": "occupied_hold",
                "when": [{"field": "occupied_now", "op": "==", "value": 1}],
                "then": {"op": "set_residual", "value": 0.2},
            },
            "causal_edge_ids": ["ce_00000000"],
            "rationale": "replace one existing rule by its identifier",
        },
        {
            "op": "remove_rule",
            "id": "anchor",
            "causal_edge_ids": ["ce_00000000"],
            "rationale": "remove one existing rule by its identifier",
        },
        {
            "op": "move_rule",
            "id": "unoccupied_hold",
            "to_index": 0,
            "causal_edge_ids": ["ce_00000000"],
            "rationale": "move one existing rule to a zero-based index",
        },
    ],
    ids=("no-change", "set-param", "add-rule", "replace-rule", "remove-rule", "move-rule"),
)
def test_all_six_documented_patch_operations_follow_the_runtime_contract(
    canonical_program: dict[str, Any], patch: dict[str, Any]
) -> None:
    candidate = apply_patch(canonical_program, patch)
    if patch["op"] == "no_change":
        assert candidate == canonical_program
    else:
        assert program_hash(candidate) != program_hash(canonical_program)


@pytest.mark.parametrize(
    "patch",
    [
        {
            "op": "add_rule",
            "index": -1,
            "rule": {
                "id": "new_rule",
                "when": [{"field": "occupied_now", "op": "==", "value": 1}],
                "then": {"op": "hold_setpoint"},
            },
            "rationale": "invalid negative insertion index",
        },
        {
            "op": "add_rule",
            "rule": {
                "id": "occupied_hold",
                "when": [{"field": "occupied_now", "op": "==", "value": 1}],
                "then": {"op": "hold_setpoint"},
            },
            "rationale": "identifier is not new",
        },
        {
            "op": "replace_rule",
            "rule": {
                "id": "missing_rule",
                "when": [{"field": "occupied_now", "op": "==", "value": 1}],
                "then": {"op": "hold_setpoint"},
            },
            "rationale": "identifier does not exist",
        },
        {
            "op": "move_rule",
            "id": "occupied_hold",
            "to_index": 99,
            "rationale": "destination is outside the zero-based range",
        },
        {
            "op": "replace_rule",
            "rule": {
                "id": "occupied_hold",
                "when": [{"field": "occupied_now", "op": "==", "value": 1}],
                "then": {"op": "hold_setpoint", "value": 0.0},
            },
            "rationale": "hold setpoint cannot carry a value",
        },
        {
            "op": "replace_rule",
            "rule": {
                "id": "occupied_hold",
                "when": [{"field": "occupied_now", "op": "==", "value": 1}],
                "then": {"op": "set_residual", "value": {"param": "unknown"}},
            },
            "rationale": "parameter reference must name a visible parameter",
        },
    ],
)
def test_patch_identifier_index_and_value_contracts_fail_closed(
    canonical_program: dict[str, Any], patch: dict[str, Any]
) -> None:
    with pytest.raises(ProgramError):
        apply_patch(canonical_program, patch, causal_enabled=False)
