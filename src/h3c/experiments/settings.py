"""Frozen runtime request contract."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from h3c.experiments.profiles import repository_root

ENVIRONMENT_VARIABLE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")


def load_runtime_contract(path: Path | None = None) -> dict[str, Any]:
    source = path or repository_root() / "configs" / "experiments" / "runtime.json"
    value = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {
        "runtime_schema",
        "schema_version",
        "model",
        "physical_service",
    }:
        raise ValueError("runtime contract fields are invalid")
    if value["runtime_schema"] != "h3c_runtime_contract" or value["schema_version"] != 2:
        raise ValueError("unsupported runtime contract schema")
    model = value["model"]
    if not isinstance(model, dict) or set(model) != {
        "name",
        "endpoint_environment_variable",
        "api_key_environment_variable",
        "response_format",
        "thinking_reasoning_effort",
        "no_thinking_temperature",
        "no_thinking_top_p",
        "retry_count",
        "retry_backoff_seconds",
    }:
        raise ValueError("model runtime contract fields are invalid")
    if (
        not isinstance(model["name"], str)
        or not model["name"].strip()
        or model["name"] != model["name"].strip()
        or not isinstance(model["endpoint_environment_variable"], str)
        or ENVIRONMENT_VARIABLE.fullmatch(model["endpoint_environment_variable"]) is None
        or not isinstance(model["api_key_environment_variable"], str)
        or ENVIRONMENT_VARIABLE.fullmatch(model["api_key_environment_variable"]) is None
        or model["response_format"] != "json_object"
        or model["thinking_reasoning_effort"] != "low"
        or model["no_thinking_temperature"] != 0.0
        or model["no_thinking_top_p"] != 1.0
        or model["retry_count"] != 2
        or model["retry_backoff_seconds"] != [1.0, 2.0]
    ):
        raise ValueError("model request contract is not frozen")
    physical = value["physical_service"]
    if (
        not isinstance(physical, dict)
        or set(physical) != {"endpoint_environment_variable", "retry_count"}
        or not isinstance(physical["endpoint_environment_variable"], str)
        or ENVIRONMENT_VARIABLE.fullmatch(physical["endpoint_environment_variable"]) is None
        or physical["retry_count"] != 0
    ):
        raise ValueError("physical service contract is invalid")
    environment_names = {
        model["endpoint_environment_variable"],
        model["api_key_environment_variable"],
        physical["endpoint_environment_variable"],
    }
    if len(environment_names) != 3:
        raise ValueError("runtime credential/environment owners must be distinct")
    return value


def load_suite_contract(path: Path | None = None) -> dict[str, Any]:
    source = path or repository_root() / "configs" / "experiments" / "suites.json"
    value = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {
        "suite_schema",
        "schema_version",
        "profile_order",
        "graph_timing_mutation_by_profile",
    }:
        raise ValueError("suite contract fields are invalid")
    if value["suite_schema"] != "h3c_suite_contract" or value["schema_version"] != 1:
        raise ValueError("unsupported suite contract schema")
    order = value["profile_order"]
    if (
        not isinstance(order, list)
        or not order
        or len(order) != len(set(order))
        or any(not isinstance(name, str) or not name for name in order)
    ):
        raise ValueError("suite profile declarations are invalid")
    timing_mutations = value["graph_timing_mutation_by_profile"]
    registered_mutations = load_graph_mutation_catalog()
    if (
        not isinstance(timing_mutations, dict)
        or set(timing_mutations) != set(order)
        or any(
            not isinstance(name, str) or name not in registered_mutations
            for name in timing_mutations.values()
        )
    ):
        raise ValueError("suite graph timing mutations are invalid")
    return value


def load_graph_mutation_catalog(path: Path | None = None) -> dict[str, dict[str, Any]]:
    source = path or repository_root() / "configs" / "graphs" / "mutations.json"
    value = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {
        "graph_mutation_schema",
        "schema_version",
        "mutations",
    }:
        raise ValueError("graph mutation catalog fields are invalid")
    if (
        value["graph_mutation_schema"] != "h3c_graph_mutation_catalog"
        or value["schema_version"] != 1
    ):
        raise ValueError("unsupported graph mutation catalog schema")
    mutations = value["mutations"]
    if not isinstance(mutations, dict) or set(mutations) != {
        "missing_solar_zone_edge",
        "delayed_solar_zone_edge",
        "immediate_solar_zone_edge",
    }:
        raise ValueError("registered graph mutations are invalid")
    for mutation in mutations.values():
        if (
            not isinstance(mutation, dict)
            or set(mutation) != {"kind", "edge"}
            or mutation["kind"]
            not in {
                "remove_edge",
                "change_immediate_to_delayed",
                "change_delayed_to_immediate",
            }
            or not isinstance(mutation["edge"], dict)
            or set(mutation["edge"]) != {"source", "relation", "target"}
            or any(not isinstance(field, str) or not field for field in mutation["edge"].values())
        ):
            raise ValueError("graph mutation declaration is invalid")
    return copy.deepcopy(mutations)
