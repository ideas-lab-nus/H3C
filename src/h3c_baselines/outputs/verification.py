"""Fail-closed verification for non-Agent baseline evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from h3c_baselines.models import model_entry, verify_checkpoint
from h3c_baselines.outputs.metrics import compute_baseline_metrics

FORBIDDEN_AGENT_FILES = {
    "agent_calls.jsonl",
    "raw_model_io.jsonl",
    "hourly_decisions.jsonl",
    "program_updates.jsonl",
    "zone_steps.jsonl",
    "model_request_attempts.jsonl",
}


def _load(path: Path) -> dict[str, Any]:
    candidate = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(candidate, dict):
        raise ValueError(f"{path.name} is not an object")
    return candidate


def verify_baseline_run(run_dir: Path, *, require_completion: bool = True) -> dict[str, Any]:
    manifest = _load(run_dir / "manifest.json")
    resolved = _load(run_dir / "resolved_config.json")
    metrics = compute_baseline_metrics(run_dir)
    case = str(manifest["case"])
    controller = str(manifest["controller"])
    expected_steps = int(resolved["evaluation_hours"]) * 4
    zone_count = len(resolved["case_profile"]["zones"])
    action_rows = sum(
        1 for line in (run_dir / "actions.jsonl").read_text(encoding="utf-8").splitlines() if line
    )
    performance_rows = (
        sum(1 for _ in (run_dir / "performance.csv").read_text(encoding="utf-8").splitlines()) - 1
    )
    checks: dict[str, bool] = {
        "source_commit_present": isinstance(manifest.get("source_commit"), str)
        and len(manifest["source_commit"]) == 40,
        "controller_identity": controller == resolved["controller"],
        "evaluation_steps": performance_rows == expected_steps,
        "zone_action_rows": action_rows == expected_steps * zone_count,
        "initialize_once": manifest["lifecycle"]["initialize_count"] == 1,
        "conditioning_count": manifest["lifecycle"]["conditioning_advance_count"] == 672,
        "evaluation_count": manifest["lifecycle"]["evaluation_advance_count"] == expected_steps,
        "stop_once": manifest["lifecycle"]["stop_count"] == 1,
        "test_id_unchanged": manifest["lifecycle"]["test_id_changes"] == 0,
        "prefix_identity_present": isinstance(manifest.get("conditioning_prefix_identity"), str),
        "boundary_identity_present": isinstance(manifest.get("evaluation_boundary_identity"), str),
        "native_kpis_present": (run_dir / "native_boptest_kpis.json").is_file(),
        "secret_scan_complete": manifest.get("secret_scan_status") == "completed",
        "secret_absent": manifest.get("secret_exposure_count") == 0,
        "no_agent_evidence": not any((run_dir / name).exists() for name in FORBIDDEN_AGENT_FILES),
        "metrics_recomputed": _load(run_dir / "metrics.json") == metrics,
    }
    if controller in {"c-drl", "h-drl"}:
        entry = model_entry(case, controller)
        expected = verify_checkpoint(entry)
        recorded = _load(run_dir / "model_identity.json")
        checks["model_identity"] = all(
            recorded.get(name) == expected[name] for name in ("bytes", "sha256")
        )
        checks["policy_rows"] = all(
            (run_dir / name).is_file() for name in ("observations.jsonl", "policy_inference.jsonl")
        )
    if controller == "linear-mpc":
        checks["mpc_identity_present"] = isinstance(manifest.get("mpc_model_identity"), str)
        checks["mpc_streams_present"] = all(
            (run_dir / name).is_file() for name in ("predictions.jsonl", "solver_trace.jsonl")
        )
    errors = sorted(name for name, passed in checks.items() if not passed)
    execution_integrity = not errors
    classification = (
        "RUN-INVALID"
        if not execution_integrity
        else "METHOD-DEGRADED"
        if metrics["controller"]["method_degraded"]
        else "BASELINE-PASS"
    )
    if require_completion:
        completion = _load(run_dir / "completion.json")
        checks["completion_classification"] = completion.get("classification") == classification
        if not checks["completion_classification"]:
            errors.append("completion_classification")
            execution_integrity = False
            classification = "RUN-INVALID"
    return {
        "verification_schema": "h3c_baseline_verification",
        "schema_version": 1,
        "checks": checks,
        "errors": sorted(set(errors)),
        "execution_integrity": execution_integrity,
        "completion_eligible": execution_integrity,
        "classification": classification,
        "metrics_identity": hashlib.sha256(
            json.dumps(metrics, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
