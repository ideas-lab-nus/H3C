from __future__ import annotations

import json
from pathlib import Path

import pytest

from h3c.experiments.matrix import RunPlan
from h3c.outputs.artifacts import ArtifactError, RunArtifacts
from h3c.runtime.engine import execute_serial


def test_completion_is_atomic_last_and_classification_bound(tmp_path: Path) -> None:
    artifacts = RunArtifacts(tmp_path, "main", "Demo", "fresh-run")
    artifacts.create(
        {"case_profile": {"profile": "Demo"}, "method": {}},
        {"run_identity": "identity"},
    )
    assert not (artifacts.run_dir / "completion.json").exists()

    artifacts.write_metrics({"metrics_schema": "fixture"})
    artifacts.write_verification(
        {
            "completion_eligible": True,
            "classification": "EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED",
        }
    )
    with pytest.raises(ArtifactError, match="classification"):
        artifacts.publish_completion(
            {
                "status": "complete",
                "classification": "RELEASE-PASS",
                "run_identity": "identity",
            }
        )
    assert not (artifacts.run_dir / "completion.json").exists()

    completion_path = artifacts.publish_completion(
        {
            "status": "complete",
            "classification": "EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED",
            "run_identity": "identity",
        }
    )
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    assert completion["classification"] == "EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED"
    assert completion_path.stat().st_mtime_ns >= max(
        path.stat().st_mtime_ns
        for path in artifacts.run_dir.iterdir()
        if path.is_file() and path != completion_path
    )
    assert not (artifacts.run_dir / ".completion.pending").exists()


def test_execution_invalid_verification_cannot_publish_completion(tmp_path: Path) -> None:
    artifacts = RunArtifacts(tmp_path, "main", "Demo", "invalid-run")
    artifacts.create({}, {"run_identity": "identity"})
    artifacts.write_metrics({})
    artifacts.write_verification({"completion_eligible": False, "classification": "RUN-INVALID"})
    with pytest.raises(ArtifactError, match="execution-invalid"):
        artifacts.publish_completion(
            {
                "status": "complete",
                "classification": "RUN-INVALID",
                "run_identity": "identity",
            }
        )
    assert not (artifacts.run_dir / "completion.json").exists()


def test_collection_completion_is_atomic_and_freezes_runtime_evidence(tmp_path: Path) -> None:
    artifacts = RunArtifacts(tmp_path, "main", "Demo", "collected-run")
    artifacts.create({}, {"run_identity": "identity"})
    artifacts.write_metrics({})
    marker = artifacts.publish_collection_complete(
        {
            "artifact_schema": "h3c_collection_complete",
            "schema_version": 1,
            "status": "COLLECTION-COMPLETE",
            "audit_status": "FULL-AUDIT-PENDING",
            "collection_eligible": True,
            "run_identity": "identity",
        }
    )
    assert marker.is_file()
    assert not (artifacts.run_dir / ".collection_complete.pending").exists()
    with pytest.raises(ArtifactError, match="cannot change"):
        artifacts.append_jsonl("timing.jsonl", {"event": "late"})
    with pytest.raises(ArtifactError, match="cannot change"):
        artifacts.append_performance([0] * 10)
    with pytest.raises(ArtifactError, match="current run state"):
        artifacts.replace_manifest({"run_identity": "changed"})


def test_failure_is_atomic_terminal_and_mutually_exclusive_with_completion(
    tmp_path: Path,
) -> None:
    artifacts = RunArtifacts(tmp_path, "main", "Demo", "failed-run")
    artifacts.create({}, {"run_identity": "identity"})
    artifacts.write_metrics({})
    artifacts.write_verification({"completion_eligible": False, "classification": "RUN-INVALID"})

    failure_path = artifacts.publish_failure(
        {
            "status": "failed",
            "classification": "RUN-INVALID",
            "run_identity": "identity",
            "failure_type": "terminal_transport_error",
        }
    )

    assert json.loads(failure_path.read_text(encoding="utf-8"))["status"] == "failed"
    assert not (artifacts.run_dir / ".failure.pending").exists()
    with pytest.raises(ArtifactError, match="completion has already been attempted"):
        artifacts.publish_completion(
            {
                "status": "complete",
                "classification": "RUN-INVALID",
                "run_identity": "identity",
            }
        )
    with pytest.raises(ArtifactError, match="current run state"):
        artifacts.replace_manifest({"run_identity": "changed"})


def test_early_failure_can_be_published_before_metrics_and_verification(tmp_path: Path) -> None:
    artifacts = RunArtifacts(tmp_path, "main", "Demo", "early-failure")
    artifacts.create({}, {"run_identity": "identity"})
    failure_path = artifacts.publish_failure(
        {
            "status": "failed",
            "classification": "RUN-INVALID",
            "run_identity": "identity",
            "failure_type": "terminal_runtime_error",
        }
    )
    assert json.loads(failure_path.read_text(encoding="utf-8"))["failure_type"] == (
        "terminal_runtime_error"
    )


def test_existing_execution_lock_reports_path_and_pid_without_deleting(
    tmp_path: Path,
) -> None:
    lock = tmp_path / ".execution.lock"
    lock.write_text("4242", encoding="utf-8")
    plan = RunPlan(
        profile="SZ_Air",
        controller="deterministic_baseline",
        working_memory_hours=1,
        causal_enabled=False,
        coordination_enabled=False,
        thinking_policy="all_roles_disabled",
        graph_mutation=None,
        evaluation_hours=6,
    )
    with pytest.raises(RuntimeError) as captured:
        execute_serial([plan], suite="lock-test", output_root=tmp_path)
    message = str(captured.value)
    assert str(lock) in message
    assert "recorded PID=4242" in message
    assert "remove the stale lock manually only after confirming no run is active" in message
    assert lock.read_text(encoding="utf-8") == "4242"
