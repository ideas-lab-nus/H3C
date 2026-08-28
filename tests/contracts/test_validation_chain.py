from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from h3c.causal.graph import ConfirmedGraph, load_graph
from h3c.control.budget import (
    BudgetLedger,
    site_cap_max,
    validate_allocation,
)
from h3c.control.program import validate_patch_shape
from h3c.control.validation import VALIDATION_STAGES, validate_candidate


def _allocation(graph: ConfirmedGraph) -> dict[str, Any]:
    zones = ["zone1"]
    site_power_edge = next(
        edge
        for edge in graph.edges
        if edge.source == "cooling_setpoint" and edge.target == "power_meters"
    )
    return {
        "site_cap_c": site_cap_max(zones),
        "zone_budgets_c": {"zone1": site_cap_max(zones)},
        "priority": zones,
        "rationale_per_zone": {"zone1": "single-zone bounded allocation"},
        "causal_edge_ids": [site_power_edge.identifier],
    }


def test_zero_allocation_still_requires_complete_priority() -> None:
    allocation = {
        "site_cap_c": 0.0,
        "zone_budgets_c": {"zone1": 0.0},
        "priority": [],
        "rationale_per_zone": {"zone1": "no allowance needed"},
    }
    with pytest.raises(ValueError, match="priority must be a permutation"):
        validate_allocation(allocation, ["zone1"], causal_enabled=False)

    allocation["priority"] = ["zone1"]
    validate_allocation(allocation, ["zone1"], causal_enabled=False)


def test_registered_validation_chain_accepts_one_direction_patch(
    repository_root: Path, canonical_program: dict[str, Any]
) -> None:
    graph = load_graph(repository_root / "configs" / "graphs" / "sz_air_confirmed.json")
    actuator_thermal_edge = next(
        edge
        for edge in graph.edges
        if edge.source == "cooling_setpoint" and edge.target == "zone_temp"
    )
    patch = {
        "op": "set_param",
        "param": "pmv_band_hi",
        "to": 0.4,
        "causal_edge_ids": [actuator_thermal_edge.identifier],
        "rationale": "tighten the active upper threshold",
    }
    ledger = BudgetLedger(_allocation(graph), ["zone1"])
    result = validate_candidate(
        patch,
        canonical_program,
        graph=graph,
        ledger=ledger,
        zone="zone1",
        step=0,
    )
    assert result.accepted is True
    assert result.completed_stages == VALIDATION_STAGES
    assert result.patch.get("consistent_program_direction_proof")
    site_power_edge = next(
        edge
        for edge in graph.edges
        if edge.source == "cooling_setpoint" and edge.target == "power_meters"
    )
    assert site_power_edge.identifier in result.patch["causal_edge_ids"]


def test_missing_edge_cannot_be_cited(
    repository_root: Path, canonical_program: dict[str, Any]
) -> None:
    graph = load_graph(repository_root / "configs" / "graphs" / "sz_air_confirmed.json")
    patch = {
        "op": "set_param",
        "param": "pmv_band_hi",
        "to": 0.4,
        "causal_edge_ids": ["ce_deadbeef"],
        "rationale": "invalid citation",
    }
    result = validate_candidate(
        patch,
        canonical_program,
        graph=graph,
        ledger=BudgetLedger(_allocation(graph), ["zone1"]),
        zone="zone1",
        step=0,
    )
    assert result.accepted is False
    assert result.rejection is not None
    assert result.rejection.stage == "causal_admissibility"
    assert result.rejection.code == "unknown_edge_id"


def test_causal_disabled_path_has_no_graph_or_causal_patch_fields(
    canonical_program: dict[str, Any],
) -> None:
    patch = {
        "op": "set_param",
        "param": "pmv_band_hi",
        "to": 0.4,
        "rationale": "same executable edit without causal module",
    }
    result = validate_candidate(
        patch,
        canonical_program,
        graph=None,
        ledger=None,
        zone="zone1",
        step=0,
        causal_enabled=False,
        coordination_enabled=False,
    )
    assert result.accepted is True
    assert result.completed_stages == ("program_validation",)
    assert all("causal" not in key and "edge" not in key for key in result.patch)


@pytest.mark.parametrize(
    "identifiers",
    [[], ["not-an-edge"], ["ce_deadbeef"], ["ce_deadbeef", "ce_deadbeef"]],
)
def test_orchestrator_causal_references_are_unique_known_and_formatted(
    repository_root: Path, identifiers: list[str]
) -> None:
    graph = load_graph(repository_root / "configs" / "graphs" / "sz_air_confirmed.json")
    allocation = _allocation(graph)
    allocation["causal_edge_ids"] = identifiers
    with pytest.raises(ValueError):
        validate_allocation(
            allocation,
            ["zone1"],
            causal_enabled=True,
            allowed_causal_edge_ids=set(graph.by_id),
            site_causal_edge_ids={
                edge.identifier for edge in graph.edges if edge.target == "power_meters"
            },
        )


def test_orchestrator_reference_must_reach_shared_power_surface(repository_root: Path) -> None:
    graph = load_graph(repository_root / "configs" / "graphs" / "sz_air_confirmed.json")
    zone_edge = next(edge for edge in graph.edges if edge.target == "zone_temp")
    allocation = _allocation(graph)
    allocation["causal_edge_ids"] = [zone_edge.identifier]
    with pytest.raises(ValueError, match="shared-power site edge"):
        validate_allocation(
            allocation,
            ["zone1"],
            causal_enabled=True,
            allowed_causal_edge_ids=set(graph.by_id),
            site_causal_edge_ids={
                edge.identifier for edge in graph.edges if edge.target == "power_meters"
            },
        )


def test_rationale_length_never_changes_allocation_or_patch_acceptance(
    repository_root: Path,
) -> None:
    graph = load_graph(repository_root / "configs" / "graphs" / "sz_air_confirmed.json")
    allocation = _allocation(graph)
    rationale = "x" * 10_000
    allocation["rationale_per_zone"] = {"zone1": rationale}
    validate_allocation(
        allocation,
        ["zone1"],
        causal_enabled=True,
        allowed_causal_edge_ids=set(graph.by_id),
        site_causal_edge_ids={
            edge.identifier for edge in graph.edges if edge.target == "power_meters"
        },
    )
    patch = {
        "op": "no_change",
        "rationale": rationale,
    }
    validate_patch_shape(patch, causal_enabled=True)
    assert allocation["rationale_per_zone"]["zone1"] == rationale
    assert patch["rationale"] == rationale


@pytest.mark.parametrize(
    "rationale",
    [{"other-zone": "x" * 241}, {"zone1": 241}, {"zone1": " " * 241}],
)
def test_allocation_rejects_wrong_zone_type_or_empty_rationale(
    repository_root: Path, rationale: dict[str, Any]
) -> None:
    graph = load_graph(repository_root / "configs" / "graphs" / "sz_air_confirmed.json")
    allocation = _allocation(graph)
    allocation["rationale_per_zone"] = rationale
    with pytest.raises(ValueError, match="nonempty string"):
        validate_allocation(
            allocation,
            ["zone1"],
            causal_enabled=True,
            allowed_causal_edge_ids=set(graph.by_id),
            site_causal_edge_ids={
                edge.identifier for edge in graph.edges if edge.target == "power_meters"
            },
        )


@pytest.mark.parametrize("fault", ["extra_root", "over_cap", "unknown_edge"])
def test_long_rationale_does_not_mask_other_allocation_contract_errors(
    repository_root: Path, fault: str
) -> None:
    graph = load_graph(repository_root / "configs" / "graphs" / "sz_air_confirmed.json")
    allocation = copy.deepcopy(_allocation(graph))
    allocation["rationale_per_zone"] = {"zone1": "x" * 241}
    if fault == "extra_root":
        allocation["unexpected"] = True
    elif fault == "over_cap":
        allocation["site_cap_c"] = 3.0
    else:
        allocation["causal_edge_ids"] = ["ce_deadbeef"]
    with pytest.raises(ValueError):
        validate_allocation(
            allocation,
            ["zone1"],
            causal_enabled=True,
            allowed_causal_edge_ids=set(graph.by_id),
            site_causal_edge_ids={
                edge.identifier for edge in graph.edges if edge.target == "power_meters"
            },
        )
