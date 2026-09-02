"""Fast collection gate and deferred, zero-network full-run finalization."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from h3c.experiments.matrix import RunPlan
from h3c.outputs.artifacts import PERFORMANCE_COLUMNS, STREAM_FILES, RunArtifacts
from h3c.outputs.metrics import compute_run_metrics


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} is not a JSON object")
    return value


def _rows(path: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{line_number} is not a JSON object")
        result.append(value)
    return result


def _performance(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != PERFORMANCE_COLUMNS:
            raise ValueError("performance.csv header does not match the registered schema")
        rows = [dict(row) for row in reader]
    if any(any(value is None for value in row.values()) for row in rows):
        raise ValueError("performance.csv contains an incomplete row")
    return rows


def _identity(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _plan(resolved: dict[str, Any]) -> RunPlan:
    method = resolved["method"]
    return RunPlan(
        profile=str(resolved["case_profile"]["profile"]),
        controller=str(method["controller"]),
        working_memory_hours=int(method["working_memory_hours"]),
        causal_enabled=bool(method["causal_enabled"]),
        coordination_enabled=bool(method["coordination_enabled"]),
        thinking_policy=str(method["thinking_policy"]),
        graph_mutation=method.get("graph_mutation"),
        evaluation_hours=int(method["evaluation_hours"]),
        long_term_memory=bool(method.get("long_term_memory", False)),
        model_provider=resolved.get("model_provider"),
        diagnostic_window=method.get("diagnostic_window"),
    )


def collection_gate(run_dir: Path) -> dict[str, Any]:
    """Run the bounded, no-network collection-completeness checks."""
    directory = run_dir.resolve()
    checks: dict[str, bool] = {}
    errors: list[str] = []
    required = {
        "resolved_config.yaml",
        "manifest.json",
        "metrics.json",
        "forecast_inputs.json",
        "performance.csv",
        "dispatch_state.json",
        "completed_hour_checkpoint.json",
        *STREAM_FILES,
    }
    missing = sorted(name for name in required if not (directory / name).is_file())
    checks["required_artifacts"] = not missing
    checks["no_terminal_failure"] = not (directory / "failure.json").exists()
    checks["full_audit_not_started"] = not any(
        (directory / name).exists() for name in ("verification.json", "completion.json")
    )
    checks["no_pending_publication"] = not any(directory.glob(".*.pending"))
    if missing:
        errors.append(f"missing artifacts: {missing}")
    try:
        if missing:
            raise ValueError("required artifacts are missing")
        resolved = _object(directory / "resolved_config.yaml")
        manifest = _object(directory / "manifest.json")
        dispatch = _object(directory / "dispatch_state.json")
        checkpoint = _object(directory / "completed_hour_checkpoint.json")
        recorded_metrics = _object(directory / "metrics.json")
        _object(directory / "forecast_inputs.json")
        streams = {name: _rows(directory / name) for name in STREAM_FILES}
        performance = _performance(directory / "performance.csv")

        plan = _plan(resolved)
        profile = resolved["case_profile"]
        zones = tuple(profile["zones"])
        hours = plan.evaluation_hours
        steps = hours * 4
        calls = plan.expected_agent_calls(len(zones))
        run_identity = str(manifest["run_identity"])
        test_id = str(dispatch.get("test_id", ""))
        execution_identity = resolved["execution_identity"]

        checks["agent_collection_contract"] = plan.controller == "h3c_agent"

        checks["run_identity"] = (
            bool(run_identity)
            and run_identity == _identity(execution_identity)
            and dispatch.get("run_identity") == run_identity
            and checkpoint.get("run_identity") == run_identity
        )
        checks["source_and_plan_identity"] = manifest.get(
            "source_commit"
        ) == execution_identity.get("source_commit") and execution_identity.get(
            "plan_identity"
        ) == plan.identity(profile)
        checks["dispatch_stopped"] = dispatch == {
            "artifact_schema": "h3c_dispatch_state",
            "schema_version": 1,
            "run_identity": run_identity,
            "dispatch_mode": "auto",
            "status": "STOPPED",
            "test_id": test_id,
            "testcase": profile["testcase"],
        } and bool(test_id)
        checks["final_checkpoint"] = checkpoint == {
            "artifact_schema": "h3c_completed_hour_checkpoint",
            "schema_version": 1,
            "run_identity": run_identity,
            "test_id": test_id,
            "completed_hour": hours - 1,
            "completed_step": steps - 1,
            "next_step": steps,
            "program_versions": checkpoint.get("program_versions"),
        } and (
            isinstance(checkpoint.get("program_versions"), dict)
            and set(checkpoint["program_versions"]) == set(zones)
            and all(
                isinstance(version, int) and not isinstance(version, bool) and version >= 0
                for version in checkpoint["program_versions"].values()
            )
        )
        checks["lifecycle"] = manifest.get("lifecycle") == {
            "initialize_count": 1,
            "stop_count": 1,
            "test_id_changes": 0,
            "conditioning_advance_count": 0,
        }
        checks["row_counts"] = (
            len(performance) == steps
            and len(streams["zone_steps.jsonl"]) == steps * len(zones)
            and len(streams["hourly_decisions.jsonl"]) == hours
            and len(streams["program_updates.jsonl"]) == hours * len(zones)
            and len(streams["caol_records.jsonl"]) == hours * len(zones)
            and len(streams["agent_calls.jsonl"]) == calls
            and len(streams["raw_model_io.jsonl"]) == calls
            and len(streams["model_request_attempts.jsonl"]) >= calls
            and (plan.long_term_memory or len(streams["long_term_memory_crud.jsonl"]) == 0)
        )
        evaluation_start = plan.evaluation_start_seconds(profile)
        expected_times = [evaluation_start + step * 900 for step in range(steps)]
        checks["continuous_timeline"] = (
            [int(row["step"]) for row in performance] == list(range(steps))
            and [int(row["hour"]) for row in performance] == [step // 4 for step in range(steps)]
            and [int(float(row["time_seconds"])) for row in performance] == expected_times
        )
        zone_rows = streams["zone_steps.jsonl"]
        checks["zone_rows"] = all(
            int(row.get("step", -1)) == step
            and int(row.get("hour", -1)) == step // 4
            and row.get("zone") in zones
            and row.get("test_id") == test_id
            and int(row.get("action_time_seconds", -1)) == evaluation_start + step * 900
            and int(row.get("outcome_time_seconds", -1)) == evaluation_start + (step + 1) * 900
            and isinstance(row.get("observation"), dict)
            and isinstance(row.get("interpreter"), dict)
            and isinstance(row.get("action_assurance"), dict)
            and isinstance(row.get("outcome"), dict)
            for step in range(steps)
            for row in zone_rows[step * len(zones) : (step + 1) * len(zones)]
        ) and all(
            {row["zone"] for row in zone_rows[step * len(zones) : (step + 1) * len(zones)]}
            == set(zones)
            for step in range(steps)
        )
        lifecycle_rows = [
            row for row in streams["timing.jsonl"] if row.get("phase") == "physical_lifecycle"
        ]
        checks["terminal_time"] = (
            len(lifecycle_rows) == 4
            and [row.get("event") for row in lifecycle_rows]
            == ["initialized", "evaluation_started", "evaluation_completed", "stopped"]
            and int(lifecycle_rows[-1].get("time_seconds", -1)) == evaluation_start + steps * 900
            and all(row.get("test_id") == test_id for row in lifecycle_rows)
        )
        recomputed_metrics = compute_run_metrics(directory)
        checks["metrics_recomputed"] = recomputed_metrics == recorded_metrics
        checks["program_replay_recorded"] = manifest.get("program_replay_verified") is True
        checks["agent_call_count"] = manifest.get("expected_agent_calls") == calls
        checks["secret_scan"] = manifest.get("secret_exposure_count") == 0 and manifest.get(
            "secret_scan_status"
        ) in {"completed", "not_applicable"}
    except Exception as error:
        errors.append(f"{type(error).__name__}: {error}")
        recomputed_metrics = None
        run_identity = ""
        test_id = ""
        hours = 0
        steps = 0
        calls = 0

    failed = sorted(name for name, passed in checks.items() if not passed)
    errors.extend(f"failed check: {name}" for name in failed)
    eligible = not errors and bool(checks) and all(checks.values())
    return {
        "artifact_schema": "h3c_collection_complete",
        "schema_version": 1,
        "status": "COLLECTION-COMPLETE" if eligible else "COLLECTION-INCOMPLETE",
        "audit_status": "FULL-AUDIT-PENDING" if eligible else "FULL-AUDIT-BLOCKED",
        "collection_eligible": eligible,
        "run_identity": run_identity,
        "test_id": test_id,
        "completed_evaluation_hours": hours,
        "physical_steps": steps,
        "logical_agent_calls": calls,
        "checks": checks,
        "errors": errors,
        **({"metrics": recomputed_metrics} if recomputed_metrics is not None else {}),
    }


def finalize_run(run_dir: Path) -> dict[str, Any]:
    """Run one deferred full audit and publish its terminal evidence atomically."""
    directory = run_dir.resolve()
    marker = _object(directory / "collection_complete.json")
    dispatch = _object(directory / "dispatch_state.json")
    if marker.get("collection_eligible") is not True:
        raise ValueError("run did not pass the collection-complete gate")
    if marker.get("audit_status") != "FULL-AUDIT-PENDING":
        raise ValueError("run is not pending a full audit")
    if dispatch.get("status") != "STOPPED":
        raise ValueError("run must be stopped before finalization")
    if any(
        (directory / name).exists()
        for name in ("failure.json", "verification.json", "completion.json")
    ):
        raise ValueError("run already has terminal or full-audit evidence")
    recomputed_collection = collection_gate(directory)
    comparable_marker = {
        key: value for key, value in marker.items() if key not in {"finished_at", "elapsed_seconds"}
    }
    if recomputed_collection != comparable_marker:
        raise ValueError("collection-complete evidence changed before full audit")

    from h3c.outputs.verification import verify_run

    artifacts = RunArtifacts.open_existing(directory)
    verification = verify_run(directory, require_completion=False)
    artifacts.write_verification(verification)
    if verification.get("completion_eligible") is not True:
        artifacts.publish_failure(
            {
                "status": "failed",
                "classification": verification.get("classification", "RUN-INVALID"),
                "run_identity": marker["run_identity"],
                "finished_at": datetime.now(UTC).isoformat(),
                "failure_type": "full_audit_failed",
                "error_type": "RunAcceptanceFailure",
                "retryable": False,
                "provider_response_received": False,
                "failure_count": 1,
            }
        )
        return {
            "status": "FULL-AUDIT-FAILED",
            "run_dir": str(directory),
            "verification": verification,
        }
    completion = {
        "status": "complete",
        "classification": verification["classification"],
        "run_identity": marker["run_identity"],
        "finished_at": datetime.now(UTC).isoformat(),
        "elapsed_seconds": marker.get("elapsed_seconds"),
    }
    completion_path = artifacts.publish_completion(completion)
    return {
        "status": "complete",
        "run_dir": str(directory),
        "verification": verification,
        "completion": str(completion_path),
    }
