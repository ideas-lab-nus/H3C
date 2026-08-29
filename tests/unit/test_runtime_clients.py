from __future__ import annotations

import asyncio
import http.client
import json
import socket
import ssl
import urllib.request
from typing import Any

import pytest

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


def _model_response(content: str = '{"patch":[]}') -> dict[str, Any]:
    return {
        "model": "deepseek-v4-flash",
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
    client.set_context(hour=0, step=0, zone="zone1")

    assert (
        asyncio.run(
            client.complete(
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


def test_model_request_does_not_retry_a_nonretryable_response_error(
    monkeypatch: Any,
) -> None:
    rows: list[tuple[str, dict[str, Any]]] = []
    calls = 0

    def request(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        raise TransportError(
            "HTTP 401",
            error_type="http_401",
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

    with pytest.raises(TransportError, match="HTTP 401"):
        asyncio.run(
            client.complete(
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
    assert attempts[0]["error_type"] == "http_401"
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

    def response(method: str, url: str, **kwargs: object) -> dict[str, object]:
        requests.append((method, url, kwargs.get("payload")))
        if url.endswith("/select"):
            return {"testid": "persistent-lane"}
        if "/initialize/" in url:
            return {"payload": {"time": kwargs["payload"]["start_time"]}}  # type: ignore[index]
        return {}

    monkeypatch.setattr("h3c.runtime.clients._request_json", response)
    client = BoptestHttpClient("http://physical.invalid")
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
