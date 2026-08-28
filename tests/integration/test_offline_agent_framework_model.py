from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from agent_framework.exceptions import ChatClientException

from h3c.offline.artifacts import OfflineWorkspace, read_jsonl, write_atomic_json, write_new_json
from h3c.offline.contracts import OfflineContractError
from h3c.offline.model import MicrosoftOfflineAgents


def _workspace(path: Path) -> OfflineWorkspace:
    path.mkdir(parents=True)
    (path / "checkpoints").mkdir()
    write_new_json(
        path / "source_manifest.json",
        {"workflow_identity": "workflow-identity", "provider": {"model": "deepseek-chat"}},
    )
    write_new_json(path / "resolved_spec.json", {})
    write_atomic_json(
        path / "checkpoints" / "application_state.json",
        {"stage": "created", "workflow_identity": "workflow-identity"},
    )
    return OfflineWorkspace.open(path)


def test_real_agent_framework_client_serializes_thinking_low_without_sampling(
    tmp_path: Path,
) -> None:
    observed: list[dict[str, object]] = []

    def provider(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        observed.append(body)
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-offline-test",
                "object": "chat.completion",
                "created": 0,
                "model": "deepseek-chat",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": '{"accepted":true}'},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 3,
                    "total_tokens": 13,
                },
            },
            request=request,
        )

    workspace = _workspace(tmp_path / "workspace")
    agents = MicrosoftOfflineAgents(
        endpoint="https://provider.invalid",
        api_key="test-secret-not-written",
        model="deepseek-chat",
        http_transport=httpx.MockTransport(provider),
    )

    async def exercise() -> None:
        try:
            result = await agents.generate_mapping("system instruction", "user input", 1, workspace)
            assert result.parsed == {"accepted": True}
        finally:
            await agents.close()

    asyncio.run(exercise())
    assert len(observed) == 1
    request = observed[0]
    assert request["reasoning_effort"] == "low"
    assert "temperature" not in request
    assert "top_p" not in request
    assert request["model"] == "deepseek-chat"
    assert request["messages"] == [
        {"role": "system", "content": "system instruction"},
        {"role": "user", "content": "user input"},
    ]
    raw = read_jsonl(workspace.path / "raw_model_io.jsonl")
    calls = read_jsonl(workspace.path / "model_calls.jsonl")
    assert raw[0]["wire_request"] == request
    assert calls[0]["reasoning_effort"] == "low"
    assert calls[0]["temperature_absent"] is True
    assert calls[0]["top_p_absent"] is True


def test_real_agent_framework_client_disables_automatic_network_retry(
    tmp_path: Path,
) -> None:
    attempts = 0

    def interrupted_provider(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadError("simulated connection reset", request=request)

    workspace = _workspace(tmp_path / "workspace")
    agents = MicrosoftOfflineAgents(
        endpoint="https://provider.invalid",
        api_key="test-secret-not-written",
        model="deepseek-chat",
        http_transport=httpx.MockTransport(interrupted_provider),
    )

    async def exercise() -> None:
        try:
            with pytest.raises(ChatClientException, match="Connection error"):
                await agents.generate_mapping("system instruction", "user input", 1, workspace)
        finally:
            await agents.close()

    asyncio.run(exercise())
    assert attempts == 1
    assert not (workspace.path / "raw_model_io.jsonl").exists()
    failed = read_jsonl(workspace.path / "model_calls.jsonl")
    assert len(failed) == 1
    assert failed[0]["status"] == "failed"
    assert failed[0]["failure_category"] == "network_interruption"
    assert failed[0]["resumable"] is True
    assert failed[0]["wire_request"]["reasoning_effort"] == "low"
    assert "temperature" not in failed[0]["wire_request"]
    assert "top_p" not in failed[0]["wire_request"]


def test_successful_provider_response_with_invalid_model_json_is_not_resumable(
    tmp_path: Path,
) -> None:
    attempts = 0

    def invalid_model_output(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-invalid-json",
                "object": "chat.completion",
                "created": 0,
                "model": "deepseek-chat",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "not JSON"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 2, "completion_tokens": 2, "total_tokens": 4},
            },
            request=request,
        )

    workspace = _workspace(tmp_path / "workspace")
    agents = MicrosoftOfflineAgents(
        endpoint="https://provider.invalid",
        api_key="test-secret-not-written",
        model="deepseek-chat",
        http_transport=httpx.MockTransport(invalid_model_output),
    )

    async def exercise() -> None:
        try:
            with pytest.raises(OfflineContractError, match="output is not JSON"):
                await agents.generate_mapping("system instruction", "user input", 1, workspace)
        finally:
            await agents.close()

    asyncio.run(exercise())
    assert attempts == 1
    assert not (workspace.path / "raw_model_io.jsonl").exists()
    failed = read_jsonl(workspace.path / "model_calls.jsonl")
    assert len(failed) == 1
    assert failed[0]["failure_category"] == "nonresumable_model_failure"
    assert failed[0]["resumable"] is False
