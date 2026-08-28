from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from h3c.agents.contracts import rationale_length_telemetry
from h3c.agents.roles import (
    ModelContractError,
    resolve_executor_model_output,
    resolve_orchestrator_model_output,
)
from h3c.causal.graph import load_graph
from h3c.control.budget import BudgetLedger, site_cap_max, validated_fallback_allocation
from h3c.control.program import load_program
from h3c.control.validation import validate_candidate
from h3c.outputs.verification import _rationale_persistence


def _fixture(repository_root: Path) -> dict[str, Any]:
    path = repository_root / "tests" / "fixtures" / "overlong_rationale_replay.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    oracle = json.loads(
        (repository_root / "tests" / "fixtures" / "oracle_equivalence.json").read_text(
            encoding="utf-8"
        )
    )["historical_rationale_replay"]
    assert set(oracle) == {"path", "source_commit", "case_count", "sha256"}
    assert oracle["path"] == "tests/fixtures/overlong_rationale_replay.json"
    # Git stores this tracked JSON fixture with LF. Windows may materialize the
    # same unmodified blob with CRLF, so hash its canonical repository text
    # representation rather than platform checkout bytes.
    canonical_bytes = path.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(canonical_bytes).hexdigest() == oracle["sha256"]
    assert value["source_commit"] == oracle["source_commit"]
    assert len(value["cases"]) == oracle["case_count"] == 11
    return cast(dict[str, Any], value)


def test_all_historical_overlong_outputs_preserve_complete_parsed_rationale(
    repository_root: Path,
) -> None:
    fixture = _fixture(repository_root)
    sz_graph = load_graph(repository_root / "configs" / "graphs" / "sz_air_confirmed.json")
    mz_graph = load_graph(repository_root / "configs" / "graphs" / "mz_air_confirmed.json")
    mz_zones = list(mz_graph.zones)
    mz_site_nodes = {str(node["id"]) for node in mz_graph.nodes if node["scope"] == "site"}
    mz_site_edges = [edge.identifier for edge in mz_graph.edges if edge.target in mz_site_nodes]
    mz_allocation, _ = validated_fallback_allocation(
        mz_zones,
        None,
        site_cap_c=site_cap_max(mz_zones),
        causal_enabled=True,
        causal_edge_ids=mz_site_edges,
        allowed_causal_edge_ids=set(mz_graph.by_id),
        site_causal_edge_ids=set(mz_site_edges),
    )
    executor_count = 0
    orchestrator_count = 0
    for case in fixture["cases"]:
        raw = case["raw_output"]
        decoded = json.loads(raw)
        if case["role"] == "orchestrator":
            orchestrator_count += 1
            site_nodes = {str(node["id"]) for node in sz_graph.nodes if node["scope"] == "site"}
            site_edges = {edge.identifier for edge in sz_graph.edges if edge.target in site_nodes}
            allocation, telemetry = resolve_orchestrator_model_output(
                raw,
                ["zone1"],
                causal_enabled=True,
                allowed_causal_edge_ids=set(sz_graph.by_id),
                site_causal_edge_ids=site_edges,
            )
            assert allocation == decoded
            assert allocation["rationale_per_zone"] == decoded["rationale_per_zone"]
            expected_lengths = case["rationale_lengths"]
            assert telemetry == rationale_length_telemetry(
                "orchestrator", allocation["rationale_per_zone"]
            )
            assert telemetry["character_lengths"] == expected_lengths
            assert telemetry["decision_use"] == "none"
        else:
            executor_count += 1
            patch, telemetry = resolve_executor_model_output(raw, causal_enabled=True)
            assert patch == decoded["patch"][0]
            rationale = patch["rationale"]
            assert rationale == decoded["patch"][0]["rationale"]
            expected_length = next(iter(case["rationale_lengths"].values()))
            assert telemetry == rationale_length_telemetry("executor", {"operation": rationale})
            assert telemetry["character_lengths"] == {"operation": expected_length}
            program = load_program(
                repository_root / "configs" / "programs" / "canonical_cooling_program.json",
                case["zone"],
            )
            result = validate_candidate(
                patch,
                program,
                graph=mz_graph,
                ledger=BudgetLedger(mz_allocation, mz_zones),
                zone=case["zone"],
                step=case["step"],
                causal_enabled=True,
                coordination_enabled=True,
            )
            assert result.accepted is True
            assert result.patch["rationale"] == rationale
    assert (orchestrator_count, executor_count) == (6, 5)


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        '{"patch":[{"op":"no_change","id":"unknown","rationale":"hold"}]}',
        '{"patch":[{"op":"no_change","rationale":""}]}',
        '{"patch":[{"op":"no_change","rationale":7}]}',
    ],
)
def test_executor_structural_and_rationale_errors_still_fail_closed(raw: str) -> None:
    with pytest.raises(ModelContractError):
        resolve_executor_model_output(raw, causal_enabled=True)


@pytest.mark.parametrize(
    "rationale",
    ["", "   ", 7, None],
)
def test_orchestrator_empty_or_nonstring_rationale_still_fails_closed(
    rationale: object,
) -> None:
    raw = json.dumps(
        {
            "site_cap_c": 0.0,
            "zone_budgets_c": {"zone1": 0.0},
            "priority": ["zone1"],
            "rationale_per_zone": {"zone1": rationale},
        }
    )
    with pytest.raises(ModelContractError):
        resolve_orchestrator_model_output(raw, ["zone1"], causal_enabled=False)


def test_long_rationale_does_not_admit_genuinely_invalid_control_content(
    repository_root: Path,
) -> None:
    rationale = "audit " * 1_000
    raw = json.dumps(
        {
            "patch": [
                {
                    "op": "set_param",
                    "param": "not_a_parameter",
                    "to": 0.0,
                    "rationale": rationale,
                }
            ]
        }
    )
    patch, telemetry = resolve_executor_model_output(raw, causal_enabled=False)
    assert telemetry["maximum_character_length"] == len(rationale)
    program = load_program(
        repository_root / "configs" / "programs" / "canonical_cooling_program.json",
        "zone1",
    )
    result = validate_candidate(
        patch,
        program,
        graph=None,
        ledger=None,
        zone="zone1",
        step=0,
        causal_enabled=False,
        coordination_enabled=False,
    )
    assert result.accepted is False
    assert result.rejection is not None
    assert result.rejection.code == "unknown_param"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {
                "patch": [{"op": "no_change", "rationale": "hold"}],
                "rationale": "duplicate audit text",
            },
            {"op": "no_change", "rationale": "hold"},
        ),
        (
            {
                "patch": [{"op": "no_change", "rationale": "hold"}],
                "root": {"patch": [{"op": "no_change", "rationale": "hold"}]},
            },
            {"op": "no_change", "rationale": "hold"},
        ),
        (
            {
                "patch": [
                    {
                        "op": "replace_rule",
                        "id": "occupied_reset",
                        "rule": {
                            "id": "occupied_reset",
                            "when": [{"field": "occupied_now", "op": "==", "value": 1}],
                            "then": {"op": "set_residual", "value": 0.0},
                        },
                        "rationale": "replace the same identified rule",
                    }
                ]
            },
            {
                "op": "replace_rule",
                "rule": {
                    "id": "occupied_reset",
                    "when": [{"field": "occupied_now", "op": "==", "value": 1}],
                    "then": {"op": "set_residual", "value": 0.0},
                },
                "rationale": "replace the same identified rule",
            },
        ),
    ],
)
def test_executor_accepts_only_registered_control_neutral_wrappers(
    payload: dict[str, Any], expected: dict[str, Any]
) -> None:
    patch, telemetry = resolve_executor_model_output(json.dumps(payload), causal_enabled=False)
    assert patch == expected
    assert telemetry == rationale_length_telemetry("executor", {"operation": expected["rationale"]})


@pytest.mark.parametrize(
    "payload",
    [
        {
            "patch": [{"op": "no_change", "rationale": "hold"}],
            "root": {"patch": [{"op": "no_change", "rationale": "different"}]},
        },
        {
            "patch": [
                {
                    "op": "replace_rule",
                    "id": "different_rule",
                    "rule": {
                        "id": "occupied_reset",
                        "when": [{"field": "occupied_now", "op": "==", "value": 1}],
                        "then": {"op": "set_residual", "value": 0.0},
                    },
                    "rationale": "conflicting selector",
                }
            ]
        },
        {
            "patch": [{"op": "no_change", "rationale": "hold"}],
            "unexpected": "field",
        },
    ],
)
def test_executor_rejects_ambiguous_or_unknown_wrappers(payload: dict[str, Any]) -> None:
    with pytest.raises(ModelContractError):
        resolve_executor_model_output(json.dumps(payload), causal_enabled=False)


def test_orchestrator_accepts_only_a_single_valid_allocation_wrapper() -> None:
    allocation = {
        "site_cap_c": 0.0,
        "zone_budgets_c": {"zone1": 0.0},
        "priority": ["zone1"],
        "rationale_per_zone": {"zone1": "hold"},
    }
    parsed, telemetry = resolve_orchestrator_model_output(
        json.dumps({"allocation_contract": allocation}),
        ["zone1"],
        causal_enabled=False,
    )
    assert parsed == allocation
    assert telemetry == rationale_length_telemetry(
        "orchestrator", cast(dict[str, str], allocation["rationale_per_zone"])
    )
    with pytest.raises(ModelContractError):
        resolve_orchestrator_model_output(
            json.dumps({"allocation_contract": allocation, "extra": 1}),
            ["zone1"],
            causal_enabled=False,
        )


def test_rationale_verifier_compares_public_patch_not_internal_proof_fields() -> None:
    raw_patch = {
        "op": "set_param",
        "param": "pmv_band_hi",
        "to": 0.4,
        "rationale": "adjust the public program parameter",
    }
    stored_patch = {
        **raw_patch,
        "expected_effects": [{"node": "zone_temp", "direction": "down"}],
        "consistent_program_direction_proof": {"program_direction": "down"},
    }
    assert _rationale_persistence(
        method={
            "controller": "h3c_agent",
            "causal_enabled": False,
            "coordination_enabled": False,
            "evaluation_hours": 1,
        },
        raw_calls=[
            {
                "role": "executor",
                "hour": 0,
                "zone": "zone1",
                "output": json.dumps({"patch": [raw_patch]}),
            }
        ],
        updates=[
            {
                "hour": 0,
                "zone": "zone1",
                "status": "accepted",
                "patch": stored_patch,
                "rationale_telemetry": rationale_length_telemetry(
                    "executor", {"operation": cast(str, raw_patch["rationale"])}
                ),
            }
        ],
        decisions=[],
        zones=["zone1"],
        allowed_edge_ids=None,
        shared_power_edge_ids=None,
    )
