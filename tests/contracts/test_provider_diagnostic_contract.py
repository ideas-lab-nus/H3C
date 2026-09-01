from __future__ import annotations

from typing import Any

import pytest

from h3c.agents.contracts import executor_response_schema
from h3c.experiments.matrix import RunPlan
from h3c.experiments.profiles import load_profile
from h3c.experiments.settings import (
    evaluation_start_seconds,
    load_diagnostic_window_catalog,
    load_runtime_contract,
)
from h3c.runtime.clients import (
    model_request_contract,
    model_request_identity,
    provider_neutral_request_identity,
)


def _agent(provider: str) -> RunPlan:
    return RunPlan(
        profile="MZ_Air",
        controller="h3c_agent",
        working_memory_hours=1,
        causal_enabled=True,
        coordination_enabled=True,
        thinking_policy="occupancy_routed",
        graph_mutation=None,
        evaluation_hours=6,
        long_term_memory=False,
        model_provider=provider,
        diagnostic_window="mz-air-06-12",
    )


def test_registered_diagnostic_window_has_one_timeline_owner() -> None:
    profile = load_profile("MZ_Air")
    window = load_diagnostic_window_catalog()["mz-air-06-12"]
    assert window["evaluation_start_offset_seconds"] == 6 * 3600
    assert window["evaluation_hours"] == 6
    assert evaluation_start_seconds(profile, "mz-air-06-12") == 199 * 86400 + 6 * 3600
    assert _agent("deepseek-official").evaluation_start_seconds(profile) == 199 * 86400 + 6 * 3600


@pytest.mark.parametrize("profile", ["SZ_Air", "MZ_Hydro"])
def test_diagnostic_window_rejects_wrong_case(profile: str) -> None:
    with pytest.raises(ValueError, match="diagnostic window does not match"):
        RunPlan(
            profile=profile,
            controller="h3c_agent",
            working_memory_hours=1,
            causal_enabled=True,
            coordination_enabled=True,
            thinking_policy="occupancy_routed",
            graph_mutation=None,
            evaluation_hours=6,
            model_provider="deepseek-official",
            diagnostic_window="mz-air-06-12",
        )


def test_provider_changes_run_identity_but_not_neutral_request_identity() -> None:
    runtime = load_runtime_contract()
    official = runtime["model"]["providers"]["deepseek-official"]
    baseten = runtime["model"]["providers"]["baseten-deepseek"]
    official_request = model_request_contract(
        model=official["model"],
        system="same system",
        user="same user",
        thinking_mode="low",
    )
    baseten_request = model_request_contract(
        model=baseten["model"],
        system="same system",
        user="same user",
        thinking_mode="low",
    )
    assert model_request_identity(official_request) != model_request_identity(baseten_request)
    assert provider_neutral_request_identity(official_request) == provider_neutral_request_identity(
        baseten_request
    )
    profile: dict[str, Any] = load_profile("MZ_Air")
    assert _agent("deepseek-official").identity(profile) != _agent("baseten-deepseek").identity(
        profile
    )


def test_provider_contracts_freeze_request_and_retry_differences() -> None:
    model = load_runtime_contract()["model"]
    assert model["default_provider"] == "baseten-deepseek"
    official = model["providers"]["deepseek-official"]
    baseten = model["providers"]["baseten-deepseek"]
    assert official["retryable_status_codes"] == [429, 503]
    assert baseten["retryable_status_codes"] == [429, 500, 502, 503, 504, 529]
    assert official["session_affinity_header"] is None
    assert baseten["session_affinity_header"] == "x-session-affinity"
    assert official["response_format"] == "json_object"
    assert baseten["response_format"] == "json_schema"
    low = model_request_contract(
        model=baseten["model"], system="system", user="user", thinking_mode="low"
    )
    assert low["thinking"] == {"type": "enabled"}
    assert low["reasoning_effort"] == "low"
    assert "temperature" not in low and "top_p" not in low


def test_baseten_structured_executor_request_uses_the_parser_owned_schema() -> None:
    model = load_runtime_contract()["model"]["providers"]["baseten-deepseek"]
    schema = executor_response_schema(causal_enabled=True, long_term_memory=False)
    request = model_request_contract(
        model=model["model"],
        system="system",
        user="user",
        thinking_mode="low",
        response_format=model["response_format"],
        response_schema=schema,
    )
    assert request["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "h3c_agent_response",
            "strict": True,
            "schema": schema,
        },
    }
    assert request["thinking"] == {"type": "enabled"}
    assert request["reasoning_effort"] == "low"
    assert "temperature" not in request and "top_p" not in request
