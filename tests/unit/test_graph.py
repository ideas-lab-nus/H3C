from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from h3c.causal.graph import (
    GraphError,
    derive_variant,
    load_graph,
    stable_edge_id,
    validate_graph,
)


@pytest.mark.parametrize(
    "filename,profile",
    [
        ("sz_air_confirmed.json", "SZ_Air"),
        ("mz_hydro_confirmed.json", "MZ_Hydro"),
        ("mz_air_confirmed.json", "MZ_Air"),
    ],
)
def test_confirmed_graphs_have_valid_stable_identifiers(
    repository_root: Path, filename: str, profile: str
) -> None:
    graph = load_graph(repository_root / "configs" / "graphs" / filename)
    assert graph.profile == profile
    assert len(graph.by_id) == len(graph.edges)
    for edge in graph.edges:
        assert edge.identifier == stable_edge_id(
            edge.source, edge.relation, edge.target, edge.tags, edge.undirected
        )


def test_graph_variants_are_single_declared_differences(repository_root: Path) -> None:
    canonical = load_graph(repository_root / "configs" / "graphs" / "mz_air_confirmed.json")
    selector = {
        "source": "solar_irr",
        "relation": "Positive Corr",
        "target": "zone_temp",
    }
    missing = derive_variant(canonical, {"kind": "remove_edge", "edge": selector})
    delayed = derive_variant(canonical, {"kind": "change_immediate_to_delayed", "edge": selector})
    assert len(missing.edges) == len(canonical.edges) - 1
    unchanged_missing = {edge.identifier for edge in missing.edges}
    selected = next(
        edge
        for edge in canonical.edges
        if edge.source == "solar_irr" and edge.target == "zone_temp"
    )
    assert selected.identifier not in unchanged_missing
    delayed_edge = next(
        edge for edge in delayed.edges if edge.source == "solar_irr" and edge.target == "zone_temp"
    )
    assert delayed_edge.identifier != selected.identifier
    assert "Delayed" in delayed_edge.tags and "Immediate" not in delayed_edge.tags
    canonical_other = {
        edge.identifier for edge in canonical.edges if edge.identifier != selected.identifier
    }
    delayed_other = {
        edge.identifier for edge in delayed.edges if edge.identifier != delayed_edge.identifier
    }
    assert delayed_other == canonical_other


def test_multizone_hydronic_timing_variant_changes_delayed_to_immediate(
    repository_root: Path,
) -> None:
    canonical = load_graph(repository_root / "configs" / "graphs" / "mz_hydro_confirmed.json")
    selector = {
        "source": "solar_irr",
        "relation": "Positive Corr",
        "target": "zone_temp",
    }
    immediate = derive_variant(
        canonical,
        {"kind": "change_delayed_to_immediate", "edge": selector},
    )
    selected = next(
        edge
        for edge in canonical.edges
        if edge.source == "solar_irr" and edge.target == "zone_temp"
    )
    replacement = next(
        edge
        for edge in immediate.edges
        if edge.source == "solar_irr" and edge.target == "zone_temp"
    )
    assert "Delayed" in selected.tags and "Immediate" not in selected.tags
    assert "Immediate" in replacement.tags and "Delayed" not in replacement.tags
    assert replacement.identifier != selected.identifier
    canonical_other = {
        edge.identifier for edge in canonical.edges if edge.identifier != selected.identifier
    }
    immediate_other = {
        edge.identifier for edge in immediate.edges if edge.identifier != replacement.identifier
    }
    assert immediate_other == canonical_other


def test_timing_mutation_in_wrong_direction_fails_closed(repository_root: Path) -> None:
    canonical = load_graph(repository_root / "configs" / "graphs" / "mz_hydro_confirmed.json")
    selector = {
        "source": "solar_irr",
        "relation": "Positive Corr",
        "target": "zone_temp",
    }
    with pytest.raises(GraphError, match="requires one immediate edge"):
        derive_variant(canonical, {"kind": "change_immediate_to_delayed", "edge": selector})


def test_unconfirmed_graph_fails_closed(repository_root: Path, tmp_path: Path) -> None:
    source = repository_root / "configs" / "graphs" / "sz_air_confirmed.json"
    raw = json.loads(source.read_text(encoding="utf-8"))
    raw["confirmation"]["status"] = "proposed"
    path = tmp_path / "proposed.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(GraphError, match="fully confirmed"):
        load_graph(path)


def _mutate_relation(raw: dict[str, Any]) -> None:
    raw["edges"][0]["relation"] = "causes"


def _mutate_undirected_type(raw: dict[str, Any]) -> None:
    raw["edges"][0]["undirected"] = "false"


def _mutate_unknown_tag(raw: dict[str, Any]) -> None:
    raw["edges"][0]["tags"].append("Speculative")


def _mutate_both_timing_tags(raw: dict[str, Any]) -> None:
    raw["edges"][0]["tags"].append("Delayed")


def _mutate_no_timing_tag(raw: dict[str, Any]) -> None:
    raw["edges"][0]["tags"] = ["Strong Impact"]


def _mutate_node_extra_field(raw: dict[str, Any]) -> None:
    raw["nodes"][0]["description"] = "extra"


def _mutate_duplicate_node(raw: dict[str, Any]) -> None:
    raw["nodes"].append(copy.deepcopy(raw["nodes"][0]))


def _mutate_node_scope(raw: dict[str, Any]) -> None:
    raw["nodes"][0]["scope"] = "building"


def _mutate_empty_source(raw: dict[str, Any]) -> None:
    raw["sources"] = [" "]


def _mutate_duplicate_source(raw: dict[str, Any]) -> None:
    raw["sources"].append(raw["sources"][0])


def _mutate_adjacency_self_loop(raw: dict[str, Any]) -> None:
    raw["zones"] = ["zone1", "zone2"]
    raw["adjacency"] = [["zone1", "zone1"]]


def _mutate_adjacency_duplicate(raw: dict[str, Any]) -> None:
    raw["zones"] = ["zone1", "zone2"]
    raw["adjacency"] = [["zone1", "zone2"], ["zone2", "zone1"]]


def _mutate_adjacency_unknown_endpoint(raw: dict[str, Any]) -> None:
    raw["zones"] = ["zone1", "zone2"]
    raw["adjacency"] = [["zone1", "zone3"]]


def _mutate_zones_not_list(raw: dict[str, Any]) -> None:
    raw["zones"] = "zone1"


def _mutate_invalid_date(raw: dict[str, Any]) -> None:
    raw["confirmation"]["date"] = "2026-02-30"


def _mutate_wrong_edge_identifier(raw: dict[str, Any]) -> None:
    raw["edges"][0]["id"] = "ce_00000000"


@pytest.mark.parametrize(
    "mutate",
    [
        _mutate_relation,
        _mutate_undirected_type,
        _mutate_unknown_tag,
        _mutate_both_timing_tags,
        _mutate_no_timing_tag,
        _mutate_node_extra_field,
        _mutate_duplicate_node,
        _mutate_node_scope,
        _mutate_empty_source,
        _mutate_duplicate_source,
        _mutate_adjacency_self_loop,
        _mutate_adjacency_duplicate,
        _mutate_adjacency_unknown_endpoint,
        _mutate_zones_not_list,
        _mutate_invalid_date,
        _mutate_wrong_edge_identifier,
    ],
)
def test_confirmed_graph_rejects_strict_schema_counterexamples(
    repository_root: Path, mutate: Callable[[dict[str, Any]], None]
) -> None:
    raw: dict[str, Any] = json.loads(
        (repository_root / "configs" / "graphs" / "sz_air_confirmed.json").read_text(
            encoding="utf-8"
        )
    )
    mutate(raw)
    with pytest.raises(GraphError):
        validate_graph(raw)
