from __future__ import annotations

from typing import Any

import pytest

from h3c.control.program import (
    ProgramError,
    apply_patch,
    program_hash,
    run_program,
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
