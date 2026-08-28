from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from h3c.offline.artifacts import (
    OfflineArtifactError,
    OfflineWorkspace,
    read_json,
    source_file_records,
    write_atomic_json,
    write_new_json,
)
from h3c.offline.contracts import (
    OnboardingSpec,
    load_onboarding_spec,
    object_identity,
)
from h3c.offline.framework_workflow import (
    ReviewRequest,
    ReviewResponse,
    StartOnboarding,
    WorkflowFinished,
    build_workflow,
)
from h3c.offline.model import ModelGeneration
from h3c.offline.service import _resume_identity
from h3c.offline.verification import export_workspace, finalize_workspace, verify_workspace

FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "offline_prompts"
MAPPING = json.loads((FIXTURE_ROOT / "representative_mapping.json").read_text(encoding="utf-8"))
CAUSAL = json.loads(
    (FIXTURE_ROOT / "representative_causal_proposal.json").read_text(encoding="utf-8")
)


class ScriptedAgents:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    async def _generate(
        self,
        role: str,
        system_prompt: str,
        user_prompt: str,
        sequence: int,
        workspace: OfflineWorkspace,
        output: dict[str, Any],
    ) -> ModelGeneration:
        self.calls.append(role)
        wire = {
            "model": "fake-offline-model",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "reasoning_effort": "low",
        }
        response_text = json.dumps(output, ensure_ascii=False, sort_keys=True)
        response_identity = object_identity(output)
        wire_identity = object_identity(wire)
        workspace.append(
            "raw_model_io.jsonl",
            {
                "artifact_schema": "h3c_offline_raw_model_io",
                "schema_version": 1,
                "role": role,
                "sequence": sequence,
                "wire_request": wire,
                "wire_request_identity": wire_identity,
                "response_text": response_text,
                "response_identity": response_identity,
            },
        )
        workspace.append(
            "model_calls.jsonl",
            {
                "artifact_schema": "h3c_offline_model_call",
                "schema_version": 1,
                "role": role,
                "sequence": sequence,
                "model": "fake-offline-model",
                "endpoint_identity": workspace.manifest()["provider"]["endpoint_identity"],
                "framework_versions": workspace.manifest()["framework_versions"],
                "system_prompt_sha256": hashlib.sha256(system_prompt.encode()).hexdigest(),
                "user_prompt_sha256": hashlib.sha256(user_prompt.encode()).hexdigest(),
                "reasoning_effort": "low",
                "temperature_absent": True,
                "top_p_absent": True,
                "wire_request_identity": wire_identity,
                "response_identity": response_identity,
                "usage": {"total_tokens": 1},
                "latency_seconds": 0.01,
                "state_checkpoint_before": "before",
                "state_checkpoint_after": "after",
                "status": "confirmed_response",
            },
        )
        return ModelGeneration(response_text, copy.deepcopy(output))

    async def generate_mapping(
        self, system_prompt: str, user_prompt: str, sequence: int, workspace: OfflineWorkspace
    ) -> ModelGeneration:
        return await self._generate(
            "semantic_mapping", system_prompt, user_prompt, sequence, workspace, MAPPING
        )

    async def generate_causal(
        self, system_prompt: str, user_prompt: str, sequence: int, workspace: OfflineWorkspace
    ) -> ModelGeneration:
        return await self._generate(
            "causal_discovery", system_prompt, user_prompt, sequence, workspace, CAUSAL
        )

    async def close(self) -> None:
        return None


class InterruptingMappingAgents(ScriptedAgents):
    async def generate_mapping(
        self, system_prompt: str, user_prompt: str, sequence: int, workspace: OfflineWorkspace
    ) -> ModelGeneration:
        self.calls.append("semantic_mapping_interrupted")
        wire = {
            "model": "fake-offline-model",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "reasoning_effort": "low",
        }
        workspace.append(
            "model_calls.jsonl",
            {
                "artifact_schema": "h3c_offline_model_call",
                "schema_version": 1,
                "role": "semantic_mapping",
                "sequence": sequence,
                "model": "fake-offline-model",
                "endpoint_identity": workspace.manifest()["provider"]["endpoint_identity"],
                "framework_versions": workspace.manifest()["framework_versions"],
                "system_prompt_sha256": hashlib.sha256(system_prompt.encode()).hexdigest(),
                "user_prompt_sha256": hashlib.sha256(user_prompt.encode()).hexdigest(),
                "reasoning_effort": "low",
                "temperature_absent": True,
                "top_p_absent": True,
                "wire_request_identity": object_identity(wire),
                "wire_request": wire,
                "latency_seconds": 0.01,
                "state_checkpoint_before": "before",
                "state_checkpoint_after": None,
                "status": "failed",
                "failure_category": "network_interruption",
                "resumable": True,
                "error_type": "ConnectionResetError",
                "error": "simulated provider interruption",
            },
        )
        raise ConnectionResetError("simulated provider interruption")


def _repository(tmp_path: Path, repository_root: Path) -> tuple[Path, OnboardingSpec]:
    root = tmp_path / "repository"
    for relative in (
        "configs/onboarding/example_spec.json",
        "configs/onboarding/example_case_profile_template.json",
        "configs/programs/canonical_cooling_program.json",
        "docs/examples/example_building_points.md",
        "docs/examples/example_point_inventory.json",
        "docs/examples/example_causal_source.md",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repository_root / relative, target)
    spec = load_onboarding_spec(root / "configs/onboarding/example_spec.json", root)
    return root, spec


def _workspace(root: Path, spec: OnboardingSpec) -> OfflineWorkspace:
    path = root / "outputs" / "offline" / spec.case_id / "workflow-test"
    (path / "checkpoints").mkdir(parents=True)
    write_new_json(path / "resolved_spec.json", spec.public())
    write_new_json(
        path / "source_manifest.json",
        {
            "artifact_schema": "h3c_offline_source_manifest",
            "schema_version": 1,
            "workflow_id": "workflow-test",
            "workflow_identity": "workflow-identity",
            "case_id": spec.case_id,
            "created_at_utc": "2026-08-28T00:00:00+00:00",
            "source_commit": "0" * 40,
            "spec_identity": spec.identity,
            "source_files": source_file_records(spec),
            "provider": {
                "kind": "openai_compatible",
                "endpoint_env": "H3C_OFFLINE_MODEL_ENDPOINT",
                "endpoint_identity": hashlib.sha256(b"https://provider.invalid").hexdigest(),
                "api_key_env": "H3C_OFFLINE_MODEL_API_KEY",
                "secret_identity": hashlib.sha256(b"test-workspace-secret").hexdigest(),
                "model_env": "H3C_OFFLINE_MODEL_ID",
                "model": "fake-offline-model",
                "reasoning_effort": "low",
                "temperature_absent": True,
                "top_p_absent": True,
                "automatic_retries": 0,
            },
            "framework_versions": {
                "agent-framework-core": "1.15.0",
                "agent-framework-openai": "1.14.0",
            },
            "model_call_limits": {"mapping": 3, "causal_discovery": 3},
            "secret_scan_status": "pending",
            "secret_exposure_count": None,
        },
    )
    write_atomic_json(
        path / "checkpoints" / "application_state.json",
        {
            "state_schema": "h3c_offline_workflow_state",
            "schema_version": 1,
            "workflow_identity": "workflow-identity",
            "stage": "created",
            "mapping_round": 0,
            "causal_round": 0,
            "aborted": False,
            "abort_reason": None,
            "latest_framework_checkpoint": None,
        },
    )
    return OfflineWorkspace.open(path)


async def _events(stream: Any) -> tuple[ReviewRequest | None, str | None, WorkflowFinished | None]:
    request: ReviewRequest | None = None
    request_id: str | None = None
    finished: WorkflowFinished | None = None
    async for event in stream:
        if event.type == "request_info":
            assert isinstance(event.data, ReviewRequest)
            request = event.data
            request_id = event.request_id
        elif event.type == "output":
            assert isinstance(event.data, WorkflowFinished)
            finished = event.data
    return request, request_id, finished


def test_checkpoint_resume_revisions_completion_tamper_and_export(
    tmp_path: Path, repository_root: Path
) -> None:
    root, spec = _repository(tmp_path, repository_root)
    workspace = _workspace(root, spec)
    calls: list[str] = []
    first_agents = ScriptedAgents(calls)

    async def exercise() -> None:
        first_workflow, first_storage = build_workflow(workspace, first_agents)
        request, request_id, _ = await _events(
            first_workflow.run(StartOnboarding(str(workspace.path)), stream=True)
        )
        assert request is not None and request.stage == "mapping" and request_id is not None
        checkpoint = await first_storage.get_latest(workflow_name="h3c-offline-onboarding-v1")
        assert checkpoint is not None
        workspace.update_state(latest_framework_checkpoint=checkpoint.checkpoint_id)

        # Simulate a new process: build a fresh workflow object and restore the
        # pending request. The successful first Mapping call must not repeat.
        second_agents = ScriptedAgents(calls)
        workflow, storage = build_workflow(workspace, second_agents)
        request, request_id, _ = await _events(
            workflow.run(
                checkpoint_id=checkpoint.checkpoint_id,
                responses={
                    request_id: ReviewResponse("Engineer", "revise clarify the office label")
                },
                stream=True,
            )
        )
        assert request is not None and request.stage == "mapping" and request.round == 2
        assert request_id is not None
        request, request_id, _ = await _events(
            workflow.run(responses={request_id: ReviewResponse("Engineer", "approve")}, stream=True)
        )
        assert request is not None and request.stage == "causal" and request_id is not None
        request, request_id, _ = await _events(
            workflow.run(
                responses={request_id: ReviewResponse("Engineer", "revise cite the physics note")},
                stream=True,
            )
        )
        assert request is not None and request.stage == "causal" and request.round == 2
        assert request_id is not None
        request, _, finished = await _events(
            workflow.run(responses={request_id: ReviewResponse("Engineer", "approve")}, stream=True)
        )
        assert request is None
        assert finished is not None and finished.status == "approved"
        latest = await storage.get_latest(workflow_name="h3c-offline-onboarding-v1")
        assert latest is not None
        workspace.update_state(latest_framework_checkpoint=latest.checkpoint_id)

    asyncio.run(exercise())
    assert calls == [
        "semantic_mapping",
        "semantic_mapping",
        "causal_discovery",
        "causal_discovery",
    ]
    final = finalize_workspace(workspace.path, api_key="test-workspace-secret")
    assert final["passed"] is True
    assert (workspace.path / "completion.json").is_file()

    exported = export_workspace(
        workspace.path,
        case_profile=root / "configs" / "cases" / "example.json",
        graph=root / "configs" / "graphs" / "example.json",
        provenance=root / "configs" / "graphs" / "example_provenance.json",
    )
    assert all(Path(path).is_file() for path in exported.values())
    with pytest.raises(OfflineArtifactError, match="overwrite"):
        export_workspace(
            workspace.path,
            case_profile=root / "configs" / "cases" / "example.json",
            graph=root / "configs" / "graphs" / "example.json",
            provenance=root / "configs" / "graphs" / "example_provenance.json",
        )

    tampered = tmp_path / "tampered"
    shutil.copytree(workspace.path, tampered)
    review_path = tampered / "causal_review_events.jsonl"
    rows = [json.loads(line) for line in review_path.read_text(encoding="utf-8").splitlines()]
    rows[-1]["proposal_identity"] = "tampered"
    review_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    assert verify_workspace(tampered, require_completion=False)["passed"] is False

    raw_tampered = tmp_path / "raw-tampered"
    shutil.copytree(workspace.path, raw_tampered)
    raw_path = raw_tampered / "raw_model_io.jsonl"
    raw_rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    raw_rows[0]["wire_request"]["temperature"] = 0
    raw_path.write_text("\n".join(json.dumps(row) for row in raw_rows) + "\n", encoding="utf-8")
    assert verify_workspace(raw_tampered, require_completion=False)["passed"] is False

    call_tampered = tmp_path / "call-tampered"
    shutil.copytree(workspace.path, call_tampered)
    call_path = call_tampered / "model_calls.jsonl"
    call_rows = [json.loads(line) for line in call_path.read_text(encoding="utf-8").splitlines()]
    call_rows[0]["wire_request_identity"] = "0" * 64
    call_path.write_text("\n".join(json.dumps(row) for row in call_rows) + "\n", encoding="utf-8")
    assert verify_workspace(call_tampered, require_completion=False)["passed"] is False

    manifest_tampered = tmp_path / "manifest-tampered"
    shutil.copytree(workspace.path, manifest_tampered)
    manifest_path = manifest_tampered / "source_manifest.json"
    manifest = read_json(manifest_path)
    manifest["provider"]["reasoning_effort"] = "medium"
    write_atomic_json(manifest_path, manifest)
    assert verify_workspace(manifest_tampered, require_completion=False)["passed"] is False

    source_manifest_tampered = tmp_path / "source-manifest-tampered"
    shutil.copytree(workspace.path, source_manifest_tampered)
    source_manifest_path = source_manifest_tampered / "source_manifest.json"
    source_manifest = read_json(source_manifest_path)
    source_manifest["source_files"] = source_manifest["source_files"][:-1]
    write_atomic_json(source_manifest_path, source_manifest)
    assert verify_workspace(source_manifest_tampered, require_completion=False)["passed"] is False


def test_human_abort_is_terminal_without_causal_call_or_completion(
    tmp_path: Path, repository_root: Path
) -> None:
    root, spec = _repository(tmp_path, repository_root)
    workspace = _workspace(root, spec)
    calls: list[str] = []
    agents = ScriptedAgents(calls)

    async def exercise() -> None:
        workflow, storage = build_workflow(workspace, agents)
        request, request_id, _ = await _events(
            workflow.run(StartOnboarding(str(workspace.path)), stream=True)
        )
        assert request is not None and request_id is not None
        _, _, finished = await _events(
            workflow.run(responses={request_id: ReviewResponse("Engineer", "abort")}, stream=True)
        )
        assert finished is not None and finished.status == "aborted"
        latest = await storage.get_latest(workflow_name="h3c-offline-onboarding-v1")
        assert latest is not None
        workspace.update_state(latest_framework_checkpoint=latest.checkpoint_id)

    asyncio.run(exercise())
    assert calls == ["semantic_mapping"]
    assert read_json(workspace.state_path)["aborted"] is True
    assert not (workspace.path / "completion.json").exists()
    assert verify_workspace(workspace.path)["passed"] is False


def test_framework_checkpoint_resumes_after_mapping_transport_interruption(
    tmp_path: Path, repository_root: Path
) -> None:
    root, spec = _repository(tmp_path, repository_root)
    workspace = _workspace(root, spec)
    calls: list[str] = []

    async def exercise() -> None:
        first_workflow, first_storage = build_workflow(workspace, InterruptingMappingAgents(calls))
        with pytest.raises(ConnectionResetError, match="simulated provider interruption"):
            await _events(first_workflow.run(StartOnboarding(str(workspace.path)), stream=True))
        checkpoint = await first_storage.get_latest(workflow_name="h3c-offline-onboarding-v1")
        assert checkpoint is not None
        workspace.update_state(latest_framework_checkpoint=checkpoint.checkpoint_id)

        resumed_workflow, resumed_storage = build_workflow(workspace, ScriptedAgents(calls))
        request, request_id, _ = await _events(
            resumed_workflow.run(checkpoint_id=checkpoint.checkpoint_id, stream=True)
        )
        assert request is not None and request.stage == "mapping"
        assert request_id is not None
        request, request_id, _ = await _events(
            resumed_workflow.run(
                responses={request_id: ReviewResponse("Engineer", "approve")}, stream=True
            )
        )
        assert request is not None and request.stage == "causal"
        assert request_id is not None
        _, _, finished = await _events(
            resumed_workflow.run(
                responses={request_id: ReviewResponse("Engineer", "approve")}, stream=True
            )
        )
        assert finished is not None and finished.status == "approved"
        latest = await resumed_storage.get_latest(workflow_name="h3c-offline-onboarding-v1")
        assert latest is not None
        workspace.update_state(latest_framework_checkpoint=latest.checkpoint_id)

    asyncio.run(exercise())
    assert calls == [
        "semantic_mapping_interrupted",
        "semantic_mapping",
        "causal_discovery",
    ]
    assert finalize_workspace(workspace.path, api_key="test-workspace-secret")["passed"] is True


def test_interrupted_model_generation_counts_toward_stage_limit(
    tmp_path: Path, repository_root: Path
) -> None:
    root, _ = _repository(tmp_path, repository_root)
    spec_path = root / "configs" / "onboarding" / "example_spec.json"
    raw_spec = read_json(spec_path)
    raw_spec["limits"]["mapping_model_calls"] = 1
    write_atomic_json(spec_path, raw_spec)
    spec = load_onboarding_spec(spec_path, root)
    workspace = _workspace(root, spec)
    calls: list[str] = []

    async def exercise() -> None:
        first_workflow, storage = build_workflow(workspace, InterruptingMappingAgents(calls))
        with pytest.raises(ConnectionResetError):
            await _events(first_workflow.run(StartOnboarding(str(workspace.path)), stream=True))
        checkpoint = await storage.get_latest(workflow_name="h3c-offline-onboarding-v1")
        assert checkpoint is not None
        resumed_workflow, _ = build_workflow(workspace, ScriptedAgents(calls))
        with pytest.raises(RuntimeError, match="generation limit"):
            await _events(resumed_workflow.run(checkpoint_id=checkpoint.checkpoint_id, stream=True))

    asyncio.run(exercise())
    assert calls == ["semantic_mapping_interrupted"]


def test_nonnetwork_model_failure_cannot_be_resumed(tmp_path: Path, repository_root: Path) -> None:
    root, spec = _repository(tmp_path, repository_root)
    workspace = _workspace(root, spec)
    workspace.append(
        "model_calls.jsonl",
        {"status": "failed", "resumable": False, "failure_category": "model_json_invalid"},
    )
    with pytest.raises(OfflineArtifactError, match="not an approved network interruption"):
        _resume_identity(
            workspace,
            spec,
            "https://provider.invalid",
            "fake-offline-model",
            "test-workspace-secret",
        )
