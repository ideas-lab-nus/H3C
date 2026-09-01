"""Run one non-physical provider preflight with a frozen production-rendered input."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from h3c.agents.contracts import orchestrator_response_schema
from h3c.agents.prompts import system_prompt
from h3c.agents.roles import (
    ModelCallContext,
    ModelContractError,
    Orchestrator,
    resolve_orchestrator_model_output,
)
from h3c.causal.graph import load_graph
from h3c.experiments.profiles import repository_root
from h3c.experiments.settings import load_model_provider_contract, load_runtime_contract
from h3c.runtime.clients import OpenAICompatibleModelClient, model_request_contract


def _write_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")


def _frozen_orchestrator_input() -> tuple[str, str, list[str], set[str], set[str]]:
    root = repository_root()
    fixture = json.loads(
        (root / "tests" / "fixtures" / "caol_complete_hour_mz_air.json").read_text(encoding="utf-8")
    )
    zones = [str(zone) for zone in fixture["zones"]]
    graph = load_graph(root / "configs" / "graphs" / "mz_air_confirmed.json")
    site_edges = [edge.as_object() for edge in graph.edges if edge.target == "power_meters"]
    zone_coupling = {
        zone: {
            "zone_temperature_c": float(fixture["zone_state"][zone]["zone_temperature_c"]),
            "pmv": float(fixture["zone_state"][zone]["last_pmv"]),
            "occupancy": 1.0,
            "setpoint_c": float(fixture["zone_state"][zone]["last_setpoint"]),
            "occupancy_at_interval_end": 1.0,
            "precool_offset_from_unoccupied_base_c": -5.0,
            "resulting_precool_setpoint_c": 25.0,
            "temp_rise_to_warm_pmv_edge_c": float(
                fixture["zone_state"][zone]["comfort_headroom_c"]["warmer_c"]
            ),
            "temp_drop_to_cool_pmv_edge_c": float(
                fixture["zone_state"][zone]["comfort_headroom_c"]["cooler_c"]
            ),
        }
        for zone in zones
    }
    context = Orchestrator.build_context(
        hour=0,
        decision_time_seconds=199 * 86400 + 6 * 3600,
        zones=zones,
        site_state=fixture["site_state"],
        zone_coupling=zone_coupling,
        causal_edges=site_edges,
        previous_allocation=None,
        previous_utilisation=None,
        working_memory=None,
        allocation_limits={
            "zones": zones,
            "site_cap_c": 10.0,
            "per_zone_reserved_cap_c": 5.0,
        },
    )
    return (
        system_prompt("orchestrator", language="en"),
        context.agent_view,
        zones,
        set(graph.by_id),
        {edge.identifier for edge in graph.edges if edge.target == "power_meters"},
    )


async def _run(provider: str, output: Path) -> dict[str, Any]:
    contract = load_model_provider_contract(provider)
    endpoint_environment = contract["endpoint_environment_variable"]
    endpoint = (
        str(contract["fixed_endpoint"])
        if contract["fixed_endpoint"] is not None
        else os.environ.get(str(endpoint_environment), "")
    ).rstrip("/")
    key_environment = str(contract["api_key_environment_variable"])
    api_key = os.environ.get(key_environment, "")
    if not endpoint or not api_key:
        raise ValueError("selected provider endpoint or API key is unavailable")
    output.mkdir(parents=True, exist_ok=False)

    system, user, zones, allowed_edges, site_edges = _frozen_orchestrator_input()
    rows: dict[str, list[dict[str, Any]]] = {}

    def sink(name: str, row: Mapping[str, Any]) -> None:
        value = dict(row)
        rows.setdefault(name, []).append(value)
        _write_jsonl(output / name, value)

    session_header = contract["session_affinity_header"]
    extra_headers = (
        {str(session_header): f"h3c-preflight-{uuid.uuid4().hex}"}
        if isinstance(session_header, str) and session_header
        else None
    )
    client = OpenAICompatibleModelClient(
        endpoint=endpoint,
        api_key=api_key,
        model=str(contract["model"]),
        sink=sink,
        retry_count_limit=0,
        retry_backoff_seconds=(),
        provider_id=provider,
        extra_headers=extra_headers,
        retryable_status_codes=tuple(contract["retryable_status_codes"]),
        response_format=str(contract["response_format"]),
    )
    started_at = datetime.now(UTC).isoformat()
    output_text = await client.complete(
        context=ModelCallContext(hour=0, step=0, call_ordinal=0, zone=None),
        role="orchestrator",
        system=system,
        user=user,
        thinking_mode="low",
        response_schema=orchestrator_response_schema(zones=tuple(zones), causal_enabled=True),
    )
    contract_error: str | None = None
    try:
        parsed_root = json.loads(output_text)
        root_is_object = isinstance(parsed_root, dict)
    except (json.JSONDecodeError, TypeError):
        root_is_object = False
    try:
        resolve_orchestrator_model_output(
            output_text,
            zones,
            causal_enabled=True,
            allowed_causal_edge_ids=allowed_edges,
            site_causal_edge_ids=site_edges,
            expected_site_cap_c=10.0,
            expected_per_zone_reserved_cap_c=5.0,
        )
        schema_valid = True
    except (ModelContractError, TypeError, ValueError) as error:
        schema_valid = False
        contract_error = type(error).__name__

    calls = rows.get("agent_calls.jsonl", [])
    raw = rows.get("raw_model_io.jsonl", [])
    request_parameters = raw[0].get("request_parameters", {}) if len(raw) == 1 else {}
    usage = calls[0].get("usage", {}) if len(calls) == 1 else {}
    expected_contract = model_request_contract(
        model=str(contract["model"]),
        system=system,
        user=user,
        thinking_mode="low",
        response_format=str(contract["response_format"]),
        response_schema=(
            orchestrator_response_schema(zones=tuple(zones), causal_enabled=True)
            if contract["response_format"] == "json_schema"
            else None
        ),
    )
    checks = {
        "one_call": len(calls) == len(raw) == 1,
        "provider_identity": len(calls) == 1 and calls[0].get("model_provider") == provider,
        "response_model_identity": len(calls) == 1
        and calls[0].get("response_model") == contract["model"],
        "request_contract": request_parameters
        == {key: value for key, value in expected_contract.items() if key != "messages"},
        "json_object_response": root_is_object,
        "orchestrator_schema": schema_valid,
        "usage_available": isinstance(usage, dict) and usage.get("available") is True,
        "no_retry": len(rows.get("model_request_attempts.jsonl", [])) == 1,
    }
    secret_occurrences = sum(
        path.read_bytes().count(api_key.encode("utf-8"))
        for path in output.iterdir()
        if path.is_file()
    )
    checks["secret_free"] = secret_occurrences == 0
    summary = {
        "preflight_schema": "h3c_model_provider_preflight",
        "schema_version": 1,
        "provider": provider,
        "model": contract["model"],
        "started_at": started_at,
        "finished_at": datetime.now(UTC).isoformat(),
        "provider_neutral_request_identity": (
            calls[0].get("provider_neutral_request_identity") if len(calls) == 1 else None
        ),
        "checks": checks,
        "contract_error_type": contract_error,
        "passed": all(checks.values()),
    }
    temporary = output / "preflight_summary.json.tmp"
    temporary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output / "preflight_summary.json")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=tuple(load_runtime_contract()["model"]["providers"]),
        default="baseten-deepseek",
    )
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    summary = asyncio.run(_run(arguments.provider, arguments.output.resolve()))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "failed", "error_type": type(error).__name__}))
        sys.exit(1)
