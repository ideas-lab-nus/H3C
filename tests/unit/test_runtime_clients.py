from __future__ import annotations

import asyncio
import http.client
import json
import socket
import ssl
import urllib.error
import urllib.request
from typing import Any

import pytest

from h3c.agents.roles import ModelCallContext
from h3c.runtime.clients import (
    BoptestHttpClient,
    OpenAICompatibleModelClient,
    TransportError,
    _request_json,
    normalized_usage,
)


class _Response:
    status = 200

    def __init__(self, body: bytes = b"{}") -> None:
        self.body = body

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def test_no_payload_request_does_not_claim_to_contain_json(monkeypatch: Any) -> None:
    requests: list[urllib.request.Request] = []

    def open_request(request: urllib.request.Request, timeout: float) -> _Response:
        assert timeout == 600.0
        requests.append(request)
        return _Response()

    monkeypatch.setattr(urllib.request, "urlopen", open_request)

    _request_json("POST", "http://physical.invalid/testcases/example/select")
    _request_json("PUT", "http://physical.invalid/step/example", payload={"step": 900})

    empty, json_request = requests
    assert empty.data is None
    assert empty.get_header("Content-type") is None
    assert json_request.data == b'{"step": 900}'
    assert json_request.get_header("Content-type") == "application/json"


@pytest.mark.parametrize(
    ("status", "retryable", "retry_after"),
    [(429, True, 2.5), (503, True, 2.5), (500, False, None)],
)
def test_http_retry_registration_is_limited_to_429_and_503(
    monkeypatch: Any, status: int, retryable: bool, retry_after: float | None
) -> None:
    def fail(request: urllib.request.Request, timeout: float) -> _Response:
        del request, timeout
        raise urllib.error.HTTPError(
            "https://model.invalid",
            status,
            "registered failure",
            {"Retry-After": "2.5"},
            None,
        )

    monkeypatch.setattr(urllib.request, "urlopen", fail)

    with pytest.raises(TransportError) as raised:
        _request_json("POST", "https://model.invalid", payload={"x": 1})

    assert raised.value.retryable is retryable
    assert raised.value.error_type == f"http_{status}"
    assert raised.value.retry_after_seconds == retry_after


def test_http_529_is_retryable_only_for_the_baseten_provider_contract(
    monkeypatch: Any,
) -> None:
    def fail(request: urllib.request.Request, timeout: float) -> _Response:
        del request, timeout
        raise urllib.error.HTTPError(
            "https://inference.baseten.co/v1/chat/completions",
            529,
            "overloaded",
            {"Retry-After": "1.25"},
            None,
        )

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    with pytest.raises(TransportError) as official:
        _request_json("POST", "https://model.invalid", payload={"x": 1})
    assert official.value.retryable is False

    with pytest.raises(TransportError) as baseten:
        _request_json(
            "POST",
            "https://inference.baseten.co/v1/chat/completions",
            payload={"x": 1},
            retryable_status_codes=frozenset({429, 500, 502, 503, 504, 529}),
        )
    assert baseten.value.retryable is True
    assert baseten.value.retry_after_seconds == 1.25


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_baseten_transient_http_status_has_three_total_attempts(
    monkeypatch: Any, status: int
) -> None:
    requests = 0
    sleeps: list[float] = []
    rows: list[tuple[str, dict[str, Any]]] = []

    def open_request(request: urllib.request.Request, timeout: float) -> _Response:
        nonlocal requests
        del request, timeout
        requests += 1
        if requests < 3:
            raise urllib.error.HTTPError(
                "https://inference.baseten.co/v1/chat/completions",
                status,
                "transient",
                {},
                None,
            )
        return _Response(
            json.dumps(_model_response(model="deepseek-ai/DeepSeek-V4-Flash-0731")).encode("utf-8")
        )

    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr(urllib.request, "urlopen", open_request)
    monkeypatch.setattr(asyncio, "sleep", sleep)
    client = OpenAICompatibleModelClient(
        endpoint="https://inference.baseten.co/v1",
        api_key="secret-not-recorded",
        model="deepseek-ai/DeepSeek-V4-Flash-0731",
        sink=lambda name, row: rows.append((name, dict(row))),
        retry_count_limit=2,
        retry_backoff_seconds=(1.0, 2.0),
        provider_id="baseten-deepseek",
        retryable_status_codes=(429, 500, 502, 503, 504, 529),
    )

    asyncio.run(
        client.complete(
            context=ModelCallContext(0, 0, 0),
            role="orchestrator",
            system="system",
            user="user",
            thinking_mode="low",
        )
    )

    attempts = [row for name, row in rows if name == "model_request_attempts.jsonl"]
    assert requests == 3
    assert sleeps == [1.0, 2.0]
    assert [row["attempt_number"] for row in attempts] == [1, 2, 3]
    assert [row["error_type"] for row in attempts] == [
        f"http_{status}",
        f"http_{status}",
        None,
    ]
    assert [row["will_retry"] for row in attempts] == [True, True, False]


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_baseten_transient_http_status_exhausts_after_three_total_attempts(
    monkeypatch: Any, status: int
) -> None:
    requests = 0
    sleeps: list[float] = []
    rows: list[tuple[str, dict[str, Any]]] = []

    def open_request(request: urllib.request.Request, timeout: float) -> _Response:
        nonlocal requests
        del request, timeout
        requests += 1
        raise urllib.error.HTTPError(
            "https://inference.baseten.co/v1/chat/completions",
            status,
            "transient",
            {},
            None,
        )

    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr(urllib.request, "urlopen", open_request)
    monkeypatch.setattr(asyncio, "sleep", sleep)
    client = OpenAICompatibleModelClient(
        endpoint="https://inference.baseten.co/v1",
        api_key="secret-not-recorded",
        model="deepseek-ai/DeepSeek-V4-Flash-0731",
        sink=lambda name, row: rows.append((name, dict(row))),
        retry_count_limit=2,
        retry_backoff_seconds=(1.0, 2.0),
        provider_id="baseten-deepseek",
        retryable_status_codes=(429, 500, 502, 503, 504, 529),
    )

    with pytest.raises(TransportError, match=f"HTTP {status}"):
        asyncio.run(
            client.complete(
                context=ModelCallContext(0, 0, 0),
                role="orchestrator",
                system="system",
                user="user",
                thinking_mode="low",
            )
        )

    attempts = [row for name, row in rows if name == "model_request_attempts.jsonl"]
    assert requests == 3
    assert sleeps == [1.0, 2.0]
    assert [row["attempt_number"] for row in attempts] == [1, 2, 3]
    assert [row["will_retry"] for row in attempts] == [True, True, False]
    assert all(row["error_type"] == f"http_{status}" for row in attempts)


def test_baseten_session_affinity_is_sent_but_not_logged(monkeypatch: Any) -> None:
    rows: list[tuple[str, dict[str, Any]]] = []
    captured_headers: list[dict[str, str]] = []
    captured_payloads: list[dict[str, Any]] = []

    def request(*args: Any, **kwargs: Any) -> dict[str, Any]:
        del args
        captured_headers.append(dict(kwargs["headers"]))
        captured_payloads.append(dict(kwargs["payload"]))
        return _model_response(model="deepseek-ai/DeepSeek-V4-Flash-0731")

    monkeypatch.setattr("h3c.runtime.clients._request_json", request)
    client = OpenAICompatibleModelClient(
        endpoint="https://inference.baseten.co/v1",
        api_key="baseten-secret-not-recorded",
        model="deepseek-ai/DeepSeek-V4-Flash-0731",
        sink=lambda name, row: rows.append((name, dict(row))),
        retry_count_limit=0,
        retry_backoff_seconds=(),
        provider_id="baseten-deepseek",
        extra_headers={"x-session-affinity": "run-specific-affinity"},
        retryable_status_codes=(429, 500, 502, 503, 504, 529),
        response_format="json_schema",
    )
    schema = {
        "type": "object",
        "properties": {"patch": {"type": "array"}},
        "required": ["patch"],
        "additionalProperties": False,
    }
    asyncio.run(
        client.complete(
            context=ModelCallContext(0, 0, 0),
            role="orchestrator",
            system="system",
            user="user",
            thinking_mode="low",
            response_schema=schema,
        )
    )
    assert captured_headers == [
        {
            "Authorization": "Bearer baseten-secret-not-recorded",
            "x-session-affinity": "run-specific-affinity",
        }
    ]
    assert captured_payloads[0]["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "h3c_agent_response",
            "strict": True,
            "schema": schema,
        },
    }
    evidence = json.dumps(rows)
    assert "baseten-secret-not-recorded" not in evidence
    assert "run-specific-affinity" not in evidence
    call = next(row for name, row in rows if name == "agent_calls.jsonl")
    assert call["model_provider"] == "baseten-deepseek"


def test_non_json_response_is_allowed_only_for_explicit_no_json_contract(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: _Response(b"Test stopped successfully"),
    )

    assert (
        _request_json(
            "PUT",
            "http://physical.invalid/stop/example",
            response_json_required=False,
        )
        == {}
    )
    with pytest.raises(TransportError, match="invalid JSON") as raised:
        _request_json("PUT", "http://physical.invalid/initialize/example")
    assert raised.value.retryable is False
    assert raised.value.error_type == "response_json_invalid"
    assert raised.value.provider_response_received is True


@pytest.mark.parametrize(
    ("failure", "error_type"),
    [
        (ConnectionResetError("reset"), "ConnectionResetError"),
        (ConnectionAbortedError("aborted"), "ConnectionAbortedError"),
        (BrokenPipeError("broken"), "BrokenPipeError"),
        (TimeoutError("timeout"), "TimeoutError"),
        (socket.gaierror("dns"), "gaierror"),
        (http.client.IncompleteRead(b"partial", 10), "IncompleteRead"),
        (ssl.SSLEOFError(8, "eof"), "SSLEOFError"),
        (ssl.SSLZeroReturnError(6, "closed"), "SSLZeroReturnError"),
    ],
)
def test_registered_network_failures_are_the_precise_retryable_transport_classes(
    monkeypatch: Any, failure: BaseException, error_type: str
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: (_ for _ in ()).throw(failure),
    )

    with pytest.raises(TransportError) as raised:
        _request_json("POST", "https://model.invalid/chat/completions", payload={"x": 1})

    assert raised.value.retryable is True
    assert raised.value.error_type == error_type


def test_connection_refusal_is_not_silently_treated_as_a_transient_retry(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: (_ for _ in ()).throw(ConnectionRefusedError("refused")),
    )

    with pytest.raises(TransportError) as raised:
        _request_json("POST", "https://model.invalid/chat/completions", payload={"x": 1})

    assert raised.value.retryable is False
    assert raised.value.error_type == "ConnectionRefusedError"


def _model_response(
    content: str = '{"patch":[]}', *, model: str = "deepseek-v4-flash"
) -> dict[str, Any]:
    return {
        "model": model,
        "choices": [
            {
                "message": {"content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 1,
            "completion_tokens": 1,
            "total_tokens": 2,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 1,
        },
    }


def test_model_request_retries_one_reset_with_identical_payload(
    monkeypatch: Any,
) -> None:
    captured_payloads: list[str] = []
    sleeps: list[float] = []
    rows: list[tuple[str, dict[str, Any]]] = []

    def request(*args: Any, **kwargs: Any) -> dict[str, Any]:
        captured_payloads.append(json.dumps(kwargs["payload"], allow_nan=False))
        if len(captured_payloads) == 1:
            raise TransportError(
                "reset",
                retryable=True,
                error_type="ConnectionResetError",
            )
        return _model_response()

    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("h3c.runtime.clients._request_json", request)
    monkeypatch.setattr(asyncio, "sleep", sleep)
    client = OpenAICompatibleModelClient(
        endpoint="https://model.invalid",
        api_key="secret-not-recorded",
        model="deepseek-v4-flash",
        sink=lambda name, row: rows.append((name, dict(row))),
        retry_count_limit=2,
        retry_backoff_seconds=(1.0, 2.0),
    )
    assert (
        asyncio.run(
            client.complete(
                context=ModelCallContext(0, 0, 0, "zone1"),
                role="executor",
                system="system",
                user="user",
                thinking_mode="disabled",
            )
        )
        == '{"patch":[]}'
    )

    assert captured_payloads[0] == captured_payloads[1]
    assert sleeps == [1.0]
    assert client.retry_count == 1
    attempt_rows = [row for name, row in rows if name == "model_request_attempts.jsonl"]
    assert [row["attempt_number"] for row in attempt_rows] == [1, 2]
    assert [row["outcome"] for row in attempt_rows] == [
        "request_failed",
        "response_received",
    ]
    assert attempt_rows[0]["will_retry"] is True
    assert attempt_rows[0]["error_type"] == "ConnectionResetError"
    assert attempt_rows[0]["provider_charge_status"] == "unknown_after_request_failure"
    assert attempt_rows[1]["provider_charge_status"] == "confirmed_response_usage_recorded"
    assert attempt_rows[0]["request_identity"] == attempt_rows[1]["request_identity"]
    assert [row["request_body"] for row in attempt_rows] == captured_payloads
    calls = [row for name, row in rows if name == "agent_calls.jsonl"]
    raw = [row for name, row in rows if name == "raw_model_io.jsonl"]
    assert len(calls) == len(raw) == 1
    assert calls[0]["attempt_count"] == 2
    assert calls[0]["transport_retry_count"] == 1
    assert "secret-not-recorded" not in json.dumps(rows)


def test_model_request_exhausts_only_the_registered_transient_retries(
    monkeypatch: Any,
) -> None:
    rows: list[tuple[str, dict[str, Any]]] = []
    sleeps: list[float] = []

    def request(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise TransportError("timeout", retryable=True, error_type="TimeoutError")

    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("h3c.runtime.clients._request_json", request)
    monkeypatch.setattr(asyncio, "sleep", sleep)
    client = OpenAICompatibleModelClient(
        endpoint="https://model.invalid",
        api_key="secret",
        model="deepseek-v4-flash",
        sink=lambda name, row: rows.append((name, dict(row))),
        retry_count_limit=2,
        retry_backoff_seconds=(1.0, 2.0),
    )

    with pytest.raises(TransportError, match="timeout"):
        asyncio.run(
            client.complete(
                context=ModelCallContext(0, 0, 0),
                role="orchestrator",
                system="system",
                user="user",
                thinking_mode="low",
            )
        )

    attempts = [row for name, row in rows if name == "model_request_attempts.jsonl"]
    assert [row["attempt_number"] for row in attempts] == [1, 2, 3]
    assert [row["will_retry"] for row in attempts] == [True, True, False]
    assert sleeps == [1.0, 2.0]
    assert client.retry_count == 2
    assert not [row for name, row in rows if name == "agent_calls.jsonl"]
    assert not [row for name, row in rows if name == "raw_model_io.jsonl"]


def test_registered_503_retry_after_precedes_local_backoff(monkeypatch: Any) -> None:
    rows: list[tuple[str, dict[str, Any]]] = []
    sleeps: list[float] = []
    calls = 0

    def request(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TransportError(
                "HTTP 503",
                retryable=True,
                error_type="http_503",
                provider_response_received=True,
                retry_after_seconds=7.5,
            )
        return _model_response()

    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("h3c.runtime.clients._request_json", request)
    monkeypatch.setattr(asyncio, "sleep", sleep)
    client = OpenAICompatibleModelClient(
        endpoint="https://model.invalid",
        api_key="secret",
        model="deepseek-v4-flash",
        sink=lambda name, row: rows.append((name, dict(row))),
        retry_count_limit=2,
        retry_backoff_seconds=(1.0, 2.0),
    )

    asyncio.run(
        client.complete(
            context=ModelCallContext(0, 0, 0),
            role="orchestrator",
            system="system",
            user="user",
            thinking_mode="low",
        )
    )

    attempts = [row for name, row in rows if name == "model_request_attempts.jsonl"]
    assert sleeps == [7.5]
    assert attempts[0]["error_type"] == "http_503"
    assert attempts[0]["provider_retry_after_seconds"] == 7.5
    assert attempts[0]["retry_delay_seconds"] == 7.5
    assert attempts[0]["provider_charge_status"] == "response_received_usage_unavailable"


@pytest.mark.parametrize("status", [400, 401])
def test_model_request_does_not_retry_a_nonretryable_response_error(
    monkeypatch: Any, status: int
) -> None:
    rows: list[tuple[str, dict[str, Any]]] = []
    calls = 0

    def request(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        raise TransportError(
            f"HTTP {status}",
            error_type=f"http_{status}",
            provider_response_received=True,
        )

    monkeypatch.setattr("h3c.runtime.clients._request_json", request)
    client = OpenAICompatibleModelClient(
        endpoint="https://model.invalid",
        api_key="secret",
        model="deepseek-v4-flash",
        sink=lambda name, row: rows.append((name, dict(row))),
        retry_count_limit=2,
        retry_backoff_seconds=(1.0, 2.0),
    )

    with pytest.raises(TransportError, match=f"HTTP {status}"):
        asyncio.run(
            client.complete(
                context=ModelCallContext(0, 3, 0),
                role="reflector",
                system="system",
                user="user",
                thinking_mode="disabled",
            )
        )

    assert calls == 1
    attempts = [row for name, row in rows if name == "model_request_attempts.jsonl"]
    assert len(attempts) == 1
    assert attempts[0]["retryable"] is False
    assert attempts[0]["will_retry"] is False
    assert attempts[0]["error_type"] == f"http_{status}"
    assert attempts[0]["provider_charge_status"] == "response_received_usage_unavailable"


def test_model_request_does_not_retry_an_invalid_provider_response_contract(
    monkeypatch: Any,
) -> None:
    rows: list[tuple[str, dict[str, Any]]] = []
    calls = 0

    def request(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return {"model": "deepseek-v4-flash", "choices": []}

    monkeypatch.setattr("h3c.runtime.clients._request_json", request)
    client = OpenAICompatibleModelClient(
        endpoint="https://model.invalid",
        api_key="secret",
        model="deepseek-v4-flash",
        sink=lambda name, row: rows.append((name, dict(row))),
        retry_count_limit=2,
        retry_backoff_seconds=(1.0, 2.0),
    )

    with pytest.raises(TransportError, match="response contract") as raised:
        asyncio.run(
            client.complete(
                context=ModelCallContext(0, 3, 0),
                role="reflector",
                system="system",
                user="user",
                thinking_mode="disabled",
            )
        )

    assert calls == 1
    assert raised.value.retryable is False
    assert client.retry_count == 0
    attempts = [row for name, row in rows if name == "model_request_attempts.jsonl"]
    assert len(attempts) == 1
    assert attempts[0]["error_type"] == "model_response_contract_invalid"
    assert attempts[0]["will_retry"] is False
    assert attempts[0]["provider_charge_status"] == "response_received_usage_unavailable"


def test_non_utf8_provider_response_is_one_audited_nonretryable_attempt(
    monkeypatch: Any,
) -> None:
    rows: list[tuple[str, dict[str, Any]]] = []
    calls = 0

    def open_request(request: urllib.request.Request, timeout: float) -> _Response:
        nonlocal calls
        calls += 1
        return _Response(b"\xff")

    monkeypatch.setattr(urllib.request, "urlopen", open_request)
    client = OpenAICompatibleModelClient(
        endpoint="https://model.invalid",
        api_key="secret",
        model="deepseek-v4-flash",
        sink=lambda name, row: rows.append((name, dict(row))),
        retry_count_limit=2,
        retry_backoff_seconds=(1.0, 2.0),
    )

    with pytest.raises(TransportError, match="non-UTF-8") as raised:
        asyncio.run(
            client.complete(
                context=ModelCallContext(0, 3, 0),
                role="reflector",
                system="system",
                user="user",
                thinking_mode="disabled",
            )
        )

    assert calls == 1
    assert raised.value.retryable is False
    assert raised.value.error_type == "response_text_invalid"
    assert client.retry_count == 0
    attempts = [row for name, row in rows if name == "model_request_attempts.jsonl"]
    assert len(attempts) == 1
    assert attempts[0]["will_retry"] is False
    assert attempts[0]["error_type"] == "response_text_invalid"
    assert attempts[0]["provider_charge_status"] == "response_received_usage_unavailable"
    assert not [row for name, row in rows if name == "agent_calls.jsonl"]
    assert not [row for name, row in rows if name == "raw_model_io.jsonl"]


def test_forecast_preserves_explicit_missing_values_for_profile_resolution(
    monkeypatch: Any,
) -> None:
    def response(*args: object, **kwargs: object) -> dict[str, object]:
        return {
            "payload": {
                "TDryBul": [298.15, 298.25],
                "Occupancy[nZ]": [50.0, None],
            }
        }

    monkeypatch.setattr("h3c.runtime.clients._request_json", response)
    client = BoptestHttpClient("http://physical.invalid")
    client.test_id = "example"

    assert client.forecast(["TDryBul", "Occupancy[nZ]"], 900, 900) == {
        "TDryBul": [298.15, 298.25],
        "Occupancy[nZ]": [50.0, None],
    }


def test_selected_test_id_is_reinitialized_with_full_warmup_and_stopped_once(
    monkeypatch: Any,
) -> None:
    requests: list[tuple[str, str, object]] = []
    lifecycle: list[dict[str, Any]] = []

    def response(method: str, url: str, **kwargs: object) -> dict[str, object]:
        requests.append((method, url, kwargs.get("payload")))
        if url.endswith("/select"):
            return {"testid": "persistent-lane"}
        if "/status/" in url:
            return {"payload": "Running"}
        if "/initialize/" in url:
            return {"payload": {"time": kwargs["payload"]["start_time"]}}  # type: ignore[index]
        return {}

    monkeypatch.setattr("h3c.runtime.clients._request_json", response)
    client = BoptestHttpClient("http://physical.invalid")
    client.set_lifecycle_sink(lambda row: lifecycle.append(dict(row)))
    assert client.select_testcase("example") == "persistent-lane"
    first = client.initialize_selected(100, 7 * 86400)
    second = client.initialize_selected(100, 7 * 86400)
    assert first == second == {"time": 100}
    assert client.test_id == "persistent-lane"
    client.stop()
    assert client.test_id is None
    assert sum(url.endswith("/select") for _, url, _ in requests) == 1
    initializes = [row for row in requests if "/initialize/" in row[1]]
    assert len(initializes) == 2
    assert all(row[2] == {"start_time": 100, "warmup_period": 7 * 86400} for row in initializes)
    assert sum("/stop/" in url for _, url, _ in requests) == 1
    assert lifecycle[-1]["event"] == "stopped"
    assert lifecycle[-1]["test_id"] == "persistent-lane"


def test_queued_selection_waits_for_running_before_scenario_and_step(
    monkeypatch: Any,
) -> None:
    requests: list[tuple[str, str]] = []
    statuses = iter(("Queued", "Queued", "Running"))
    sleeps: list[float] = []
    lifecycle: list[dict[str, Any]] = []

    def response(method: str, url: str, **kwargs: object) -> dict[str, object]:
        del kwargs
        requests.append((method, url))
        if url.endswith("/select"):
            return {"testid": "queued-lane"}
        if "/status/" in url:
            return {"payload": next(statuses)}
        return {}

    monkeypatch.setattr("h3c.runtime.clients._request_json", response)
    monkeypatch.setattr("h3c.runtime.clients.time.sleep", lambda seconds: sleeps.append(seconds))
    client = BoptestHttpClient("http://physical.invalid", queue_poll_seconds=0.25)
    client.set_lifecycle_sink(lambda row: lifecycle.append(dict(row)))

    assert client.select_testcase("example") == "queued-lane"

    assert sleeps == [0.25, 0.25]
    status_indexes = [index for index, (_, url) in enumerate(requests) if "/status/" in url]
    scenario_index = next(index for index, (_, url) in enumerate(requests) if "/scenario/" in url)
    step_index = next(index for index, (_, url) in enumerate(requests) if "/step/" in url)
    assert max(status_indexes) < scenario_index < step_index
    assert [row["event"] for row in lifecycle] == [
        "selected",
        "status_changed",
        "status_changed",
        "configured",
    ]
    assert [row["status"] for row in lifecycle if row["event"] == "status_changed"] == [
        "Queued",
        "Running",
    ]
    assert all(row["dispatch_mode"] == "auto" for row in lifecycle)
    assert all(row["test_id"] == "queued-lane" for row in lifecycle)


def test_initialize_selected_rechecks_running_before_initialize(monkeypatch: Any) -> None:
    requests: list[tuple[str, str]] = []
    statuses = iter(("Running", "Queued", "Running"))
    sleeps: list[float] = []
    lifecycle: list[dict[str, Any]] = []

    def response(method: str, url: str, **kwargs: object) -> dict[str, object]:
        requests.append((method, url))
        if url.endswith("/select"):
            return {"testid": "changing-lane"}
        if "/status/" in url:
            return {"payload": next(statuses)}
        if "/initialize/" in url:
            payload = kwargs["payload"]
            assert isinstance(payload, dict)
            return {"payload": {"time": payload["start_time"]}}
        return {}

    monkeypatch.setattr("h3c.runtime.clients._request_json", response)
    monkeypatch.setattr("h3c.runtime.clients.time.sleep", lambda seconds: sleeps.append(seconds))
    client = BoptestHttpClient("http://physical.invalid", queue_poll_seconds=0.5)
    client.set_lifecycle_sink(lambda row: lifecycle.append(dict(row)))

    client.select_testcase("example")
    assert client.initialize_selected(100, 7 * 86400) == {"time": 100}

    assert sleeps == [0.5]
    initialize_index = next(
        index for index, (_, url) in enumerate(requests) if "/initialize/" in url
    )
    assert requests[initialize_index - 1][1].endswith("/status/changing-lane")
    assert lifecycle[-1] == {
        "phase": "physical_dispatch",
        "event": "initialized",
        "dispatch_mode": "auto",
        "test_id": "changing-lane",
        "testcase": "example",
        "status": "Running",
    }


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (b'"Running"', "Running"),
        (b'"Queued"', "Queued"),
        (b'{"payload":"Running"}', "Running"),
        (b'{"payload":"Queued"}', "Queued"),
    ],
)
def test_boptest_status_accepts_only_registered_wire_forms(
    monkeypatch: Any, body: bytes, expected: str
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout: _Response(body))
    client = BoptestHttpClient("http://physical.invalid")
    client.test_id = "example"

    assert client.status() == expected


@pytest.mark.parametrize(
    "body",
    [
        b'"Stopped"',
        b'"running"',
        b"null",
        b"true",
        b"1",
        b"[]",
        b"{}",
        b'{"payload":"Stopped"}',
        b'{"payload":true}',
        b'{"payload":{"status":"Running"}}',
    ],
)
def test_boptest_status_rejects_unregistered_wire_forms(monkeypatch: Any, body: bytes) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout: _Response(body))
    client = BoptestHttpClient("http://physical.invalid")
    client.test_id = "example"

    with pytest.raises(TransportError, match="status") as raised:
        client.status()

    assert raised.value.error_type in {"boptest_status_invalid", "response_json_non_object"}


def test_illegal_status_fails_before_scenario_step_or_initialize(monkeypatch: Any) -> None:
    requests: list[str] = []

    def response(method: str, url: str, **kwargs: object) -> dict[str, object]:
        del method, kwargs
        requests.append(url)
        if url.endswith("/select"):
            return {"testid": "invalid-lane"}
        if "/status/" in url:
            return {"payload": "Stopped"}
        raise AssertionError(f"illegal status reached a mutating endpoint: {url}")

    monkeypatch.setattr("h3c.runtime.clients._request_json", response)
    client = BoptestHttpClient("http://physical.invalid")

    with pytest.raises(TransportError, match="status") as raised:
        client.select_testcase("example")

    assert raised.value.error_type == "boptest_status_invalid"
    assert len(requests) == 2
    assert all(
        fragment not in url
        for url in requests
        for fragment in ("/scenario/", "/step/", "/initialize/")
    )


def test_non_status_endpoint_still_rejects_top_level_status_string(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: _Response(b'"Running"'),
    )

    with pytest.raises(TransportError) as raised:
        _request_json("GET", "http://physical.invalid/measurements/example")

    assert raised.value.error_type == "response_json_non_object"


@pytest.mark.parametrize("interval", [0.0, -1.0, float("nan"), float("inf")])
def test_boptest_queue_poll_interval_must_be_positive_and_finite(interval: float) -> None:
    with pytest.raises(ValueError, match="poll interval"):
        BoptestHttpClient("http://physical.invalid", queue_poll_seconds=interval)


@pytest.mark.parametrize("invalid", ["missing", float("nan"), float("inf"), True])
def test_forecast_reports_the_exact_invalid_point_and_index(
    monkeypatch: Any, invalid: object
) -> None:
    monkeypatch.setattr(
        "h3c.runtime.clients._request_json",
        lambda *args, **kwargs: {"payload": {"TDryBul": [298.15, invalid]}},
    )
    client = BoptestHttpClient("http://physical.invalid")
    client.test_id = "example"

    with pytest.raises(TransportError, match="TDryBul at index 1 is not a finite number"):
        client.forecast(["TDryBul"], 900, 900)


def test_provider_usage_is_normalized_only_when_complete_and_consistent() -> None:
    assert normalized_usage(
        {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "prompt_cache_hit_tokens": 4,
            "prompt_cache_miss_tokens": 6,
            "completion_tokens_details": {"reasoning_tokens": 2},
        }
    ) == {
        "available": True,
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
        "cache_hit_tokens": 4,
        "cache_miss_tokens": 6,
        "reasoning_tokens": 2,
    }


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        (None, "provider_usage_not_an_object"),
        ({"prompt_tokens": 1}, "usage_fields_unavailable"),
        (
            {
                "prompt_tokens": 2,
                "completion_tokens": 1,
                "total_tokens": 3,
                "prompt_cache_hit_tokens": 2,
                "prompt_cache_miss_tokens": 1,
            },
            "cache_accounting_mismatch",
        ),
        (
            {
                "prompt_tokens": 2,
                "completion_tokens": 1,
                "total_tokens": 4,
                "prompt_cache_hit_tokens": 1,
                "prompt_cache_miss_tokens": 1,
            },
            "total_accounting_mismatch",
        ),
        (
            {
                "prompt_tokens": 2,
                "completion_tokens": 1,
                "total_tokens": 3,
                "prompt_cache_hit_tokens": 1,
                "prompt_cache_miss_tokens": 1,
                "reasoning_tokens": 2,
            },
            "reasoning_accounting_mismatch",
        ),
    ],
)
def test_provider_usage_unavailable_reason_is_explicit(raw: object, reason: str) -> None:
    assert normalized_usage(raw)["reason"] == reason
