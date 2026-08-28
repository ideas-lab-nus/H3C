from __future__ import annotations

import copy
import dataclasses
import json
from pathlib import Path

import pytest

from h3c.causal.workflow import confirm_graph
from h3c.offline.contracts import (
    OfflineContractError,
    OnboardingSpec,
    bind_edge_provenance,
    load_onboarding_spec,
    mapping_warnings,
    merge_profile_template,
    standard_variables,
    validate_causal_proposal,
    validate_mapping,
)


def _spec(repository_root: Path) -> OnboardingSpec:
    return load_onboarding_spec(
        repository_root / "configs" / "onboarding" / "example_spec.json", repository_root
    )


def _mapping() -> dict[str, object]:
    return {
        "mapping_schema": "h3c_semantic_mapping",
        "schema_version": 1,
        "case_id": "ExampleCooling",
        "zones": {
            "office": {
                "description": "Office zone",
                "temperature_sensor": "office_temperature_y",
                "cooling_setpoint_actuator": "office_cooling_setpoint_u",
                "occupancy_forecast": "office_occupancy_y",
            }
        },
        "global_inputs": {
            "outdoor_temperature": "outdoor_temperature_y",
            "solar_irradiance": "global_solar_y",
            "electricity_price": "electricity_price_y",
            "power_meters": ["cooling_power_y", "fan_power_y"],
        },
    }


def _causal() -> dict[str, object]:
    return {
        "proposal_schema": "h3c_causal_discovery_proposal",
        "schema_version": 1,
        "case_id": "ExampleCooling",
        "edges": [
            {
                "source": "cooling_setpoint",
                "relation": "Positive Corr",
                "target": "zone_temp",
                "tags": ["Delayed", "Strong Impact"],
                "timing": "delayed",
                "undirected": False,
                "evidence_source_ids": ["physics_note"],
                "rationale": "The zone temperature follows its cooling setpoint after thermal response.",
            }
        ],
        "adjacency": [],
    }


def test_mapping_is_source_grounded_and_only_fills_profile_mapping(
    repository_root: Path,
) -> None:
    spec = _spec(repository_root)
    mapping = validate_mapping(_mapping(), spec)
    candidate = merge_profile_template(spec, mapping)
    template = json.loads(spec.case_profile_template.read_text(encoding="utf-8"))
    assert candidate["zones"] == mapping["zones"]
    assert candidate["global_inputs"] == mapping["global_inputs"]
    for field in set(template) - {"zones", "global_inputs"}:
        assert candidate[field] == template[field]
    assert mapping_warnings(mapping) == []
    variables = standard_variables(mapping)
    serialized = json.dumps(variables)
    assert "office_temperature_y" not in serialized
    assert {node["id"] for node in variables["nodes"]} == {
        "zone_temp",
        "cooling_setpoint",
        "occupancy",
        "power_meters",
        "outdoor_temp",
        "solar_irr",
        "electricity_price",
    }


@pytest.mark.parametrize("failure", ["unknown", "duplicate", "extra"])
def test_mapping_fail_closed_counterexamples(repository_root: Path, failure: str) -> None:
    spec = _spec(repository_root)
    mapping = copy.deepcopy(_mapping())
    zones = mapping["zones"]
    assert isinstance(zones, dict)
    office = zones["office"]
    assert isinstance(office, dict)
    if failure == "unknown":
        office["temperature_sensor"] = "invented_point_y"
    elif failure == "duplicate":
        office["occupancy_forecast"] = office["temperature_sensor"]
    else:
        office["control_goal"] = "not allowed"
    with pytest.raises(OfflineContractError):
        validate_mapping(mapping, spec)


def test_profile_template_cannot_prepopulate_agent_owned_mapping(
    repository_root: Path, tmp_path: Path
) -> None:
    spec = _spec(repository_root)
    raw = json.loads(spec.case_profile_template.read_text(encoding="utf-8"))
    raw["zones"] = {"prewritten": {}}
    replacement = tmp_path / "invalid_template.json"
    replacement.write_text(json.dumps(raw), encoding="utf-8")
    spec = dataclasses.replace(spec, case_profile_template=replacement)
    with pytest.raises(OfflineContractError, match="empty placeholders"):
        merge_profile_template(spec, validate_mapping(_mapping(), spec))


def test_causal_proposal_reuses_graph_owner_and_stable_ids(repository_root: Path) -> None:
    spec = _spec(repository_root)
    mapping = validate_mapping(_mapping(), spec)
    validated = validate_causal_proposal(_causal(), spec, mapping)
    graph = confirm_graph(
        validated["graph_proposal"], reviewer="Engineer", date="2026-08-28"
    ).resolved()
    assert graph["edges"][0]["id"].startswith("ce_")
    assert "Delayed" in graph["edges"][0]["tags"]
    assert validated["edge_provenance"][0]["evidence_source_ids"] == ["physics_note"]
    assert validated["edge_provenance"][0]["stable_edge_id"] == graph["edges"][0]["id"]


def test_edge_provenance_binds_by_stable_id_not_list_position(repository_root: Path) -> None:
    spec = _spec(repository_root)
    proposal = copy.deepcopy(_causal())
    edges = proposal["edges"]
    assert isinstance(edges, list)
    edges.append(
        {
            "source": "outdoor_temp",
            "relation": "Positive Corr",
            "target": "zone_temp",
            "tags": ["Immediate", "Strong Impact"],
            "timing": "immediate",
            "undirected": False,
            "evidence_source_ids": ["physics_note"],
            "rationale": "Outdoor conditions directly affect the zone temperature.",
        }
    )
    validated = validate_causal_proposal(proposal, spec, validate_mapping(_mapping(), spec))
    graph = confirm_graph(
        validated["graph_proposal"], reviewer="Engineer", date="2026-08-28"
    ).resolved()
    bound = bind_edge_provenance(
        graph["edges"],
        list(reversed(validated["edge_provenance"])),
        confirmed_round=2,
        human_feedback=["retain both mechanisms"],
    )
    rationale_by_id = {
        item["stable_edge_id"]: item["agent_rationale"] for item in validated["edge_provenance"]
    }
    assert [item["stable_edge_id"] for item in bound] == [edge["id"] for edge in graph["edges"]]
    assert all(item["agent_rationale"] == rationale_by_id[item["stable_edge_id"]] for item in bound)
    tampered = copy.deepcopy(validated["edge_provenance"])
    tampered[0]["stable_edge_id"] = "ce_00000000"
    with pytest.raises(OfflineContractError, match="exactly cover"):
        bind_edge_provenance(graph["edges"], tampered, confirmed_round=2, human_feedback=[])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source", "office_temperature_y"),
        ("relation", "Threshold"),
        ("timing", "lag_steps=2"),
        ("evidence_source_ids", ["invented_source"]),
    ],
)
def test_causal_proposal_rejects_bms_ids_unsupported_semantics_and_sources(
    repository_root: Path, field: str, value: object
) -> None:
    spec = _spec(repository_root)
    proposal = copy.deepcopy(_causal())
    edges = proposal["edges"]
    assert isinstance(edges, list) and isinstance(edges[0], dict)
    edges[0][field] = value
    with pytest.raises(OfflineContractError):
        validate_causal_proposal(proposal, spec, validate_mapping(_mapping(), spec))


def test_onboarding_spec_rejects_sampling_or_unsupported_provider_surface(
    repository_root: Path, tmp_path: Path
) -> None:
    raw = json.loads(
        (repository_root / "configs" / "onboarding" / "example_spec.json").read_text(
            encoding="utf-8"
        )
    )
    raw["provider"]["temperature"] = 0
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(OfflineContractError, match="provider fields"):
        load_onboarding_spec(path, repository_root)
