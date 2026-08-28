from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from h3c.causal.graph import derive_variant, load_graph
from h3c.control.program import load_program
from h3c.experiments.matrix import RunPlan, plan_suite
from h3c.experiments.profiles import ProfileError, load_profile, validate_profile
from h3c.experiments.settings import (
    load_graph_mutation_catalog,
    load_runtime_contract,
    load_suite_contract,
)


def test_case_profile_missing_point_fails_closed() -> None:
    profile = load_profile("SZ_Air")
    del profile["zones"]["zone1"]["temperature_sensor"]
    with pytest.raises(ProfileError, match="zone mapping"):
        validate_profile(profile)


def test_physical_protocol_drift_fails_closed() -> None:
    profile = load_profile("SZ_Air")
    profile["protocol"]["server_warmup_days"] = 6
    with pytest.raises(ProfileError, match="physical protocol"):
        validate_profile(profile)


def test_unsupported_formal_evaluation_duration_fails_closed() -> None:
    profile = load_profile("MZ_Hydro")
    profile["protocol"]["formal_evaluation_days"] = 6
    with pytest.raises(ProfileError, match="physical protocol"):
        validate_profile(profile)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("calendar_origin_utc", "2021-01-01T00:00:00", "calendar origin"),
        ("occupied_window_end_minute", 420, "window"),
        ("documented_occupancy_rule", "forward_fill", "rules"),
        ("holiday_month_days", ["02-30"], "holiday dates"),
    ],
)
def test_missing_occupancy_policy_drift_fails_closed(
    field: str, value: object, message: str
) -> None:
    profile = load_profile("MZ_Hydro")
    profile["occupancy"]["missing_value_resolution"][field] = value
    with pytest.raises(ProfileError, match=message):
        validate_profile(profile)


def test_runtime_and_suite_contracts_are_strict(tmp_path: Path) -> None:
    runtime = load_runtime_contract()
    assert runtime["schema_version"] == 2
    assert runtime["model"]["retry_count"] == 2
    assert runtime["model"]["retry_backoff_seconds"] == [1.0, 2.0]
    suite = load_suite_contract()
    assert suite["profile_order"] == ["SZ_Air", "MZ_Hydro", "MZ_Air"]
    assert suite["graph_timing_mutation_by_profile"] == {
        "SZ_Air": "delayed_solar_zone_edge",
        "MZ_Hydro": "immediate_solar_zone_edge",
        "MZ_Air": "delayed_solar_zone_edge",
    }
    drifted = json.loads(json.dumps(runtime))
    drifted["model"]["retry_count"] = 3
    path = tmp_path / "runtime_contract_rejected.json"
    path.write_text(json.dumps(drifted), encoding="utf-8")
    with pytest.raises(ValueError, match="request contract is not frozen"):
        load_runtime_contract(path)

    drifted = json.loads(json.dumps(runtime))
    drifted["model"]["retry_backoff_seconds"] = [0.0, 0.0]
    path = tmp_path / "runtime_backoff_rejected.json"
    path.write_text(json.dumps(drifted), encoding="utf-8")
    with pytest.raises(ValueError, match="request contract is not frozen"):
        load_runtime_contract(path)

    drifted = json.loads(json.dumps(runtime))
    drifted["model"]["api_key_environment_variable"] = "literal-secret-value"
    path = tmp_path / "runtime_environment_rejected.json"
    path.write_text(json.dumps(drifted), encoding="utf-8")
    with pytest.raises(ValueError, match="model request contract"):
        load_runtime_contract(path)


def test_configuration_tree_uses_honest_strict_json(repository_root: Path, tmp_path: Path) -> None:
    declarations = [
        path
        for path in (repository_root / "configs").rglob("*")
        if path.is_file() and path.name != "README.md"
    ]
    assert declarations
    assert all(path.suffix == ".json" for path in declarations)
    assert list((repository_root / "configs").rglob("*.yaml")) == []
    assert list((repository_root / "configs").rglob("*.yml")) == []
    for path in declarations:
        assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)

    yaml_like = tmp_path / "runtime.json"
    yaml_like.write_text("runtime_schema: h3c_runtime_contract\n", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_runtime_contract(yaml_like)


def test_all_registered_configuration_files_resolve_through_production_loaders(
    repository_root: Path,
) -> None:
    mutations = load_graph_mutation_catalog()
    assert set(mutations) == {
        "missing_solar_zone_edge",
        "delayed_solar_zone_edge",
        "immediate_solar_zone_edge",
    }
    for profile_name in ("SZ_Air", "MZ_Hydro", "MZ_Air"):
        profile = load_profile(profile_name)
        graph = load_graph(repository_root / profile["graph"])
        assert graph.profile == profile_name
        assert graph.zones == tuple(profile["zones"])
        for zone in profile["zones"]:
            program = load_program(repository_root / profile["program"], zone)
            assert program["zone"] == zone

    graph_plans = plan_suite("graph-sensitivity")
    assert len(graph_plans) == 6
    for plan in graph_plans:
        profile = load_profile(plan.profile)
        graph = load_graph(repository_root / profile["graph"])
        assert plan.graph_mutation is not None
        variant = derive_variant(graph, plan.graph_mutation)
        assert variant.mutation == plan.graph_mutation


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("controller", "unknown", "controller"),
        ("working_memory_hours", 0, "working memory"),
        ("evaluation_hours", 7, "evaluation hours"),
        ("thinking_policy", "unknown", "thinking policy"),
    ],
)
def test_run_plan_rejects_unregistered_factor_values(
    field: str, value: object, message: str
) -> None:
    kwargs: dict[str, object] = {
        "profile": "SZ_Air",
        "controller": "h3c_agent",
        "working_memory_hours": 1,
        "causal_enabled": True,
        "coordination_enabled": True,
        "thinking_policy": "occupancy_routed",
        "graph_mutation": None,
        "evaluation_hours": 6,
    }
    kwargs[field] = value
    with pytest.raises(ValueError, match=message):
        RunPlan(**kwargs)  # type: ignore[arg-type]


def test_run_plan_rejects_unregistered_or_inapplicable_graph_mutation() -> None:
    def plan(mutation: dict[str, Any]) -> RunPlan:
        return RunPlan(
            profile="MZ_Hydro",
            controller="h3c_agent",
            working_memory_hours=1,
            causal_enabled=True,
            coordination_enabled=True,
            thinking_policy="occupancy_routed",
            graph_mutation=mutation,
            evaluation_hours=6,
        )

    with pytest.raises(ValueError, match="not a registered"):
        plan({"kind": "remove_edge", "edge": {}})
    with pytest.raises(ValueError, match="requires one immediate"):
        plan(load_graph_mutation_catalog()["delayed_solar_zone_edge"])
