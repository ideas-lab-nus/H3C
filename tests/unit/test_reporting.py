from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from h3c.outputs.reporting import generate_report


def _write_object(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _metrics() -> dict[str, Any]:
    physical = {
        "total_cost": 1.0,
        "energy_kwh": 2.0,
        "reward": -1.0,
        "discomfort_zone_hours": 0.0,
        "discomfort_pmv_hours": 0.0,
        "occupied_peak_absolute_pmv": 0.2,
    }
    return {
        "physical": physical,
        "program_decisions": {},
        "action_assurance": {},
        "orchestration": {},
        "rationale_telemetry": {
            "decision_use": "none",
            "by_role": {
                "orchestrator": {"maximum_character_length": 300},
                "executor": {"maximum_character_length": 500},
            },
        },
        "model_calls": {},
    }


def _completed_run(
    suite: Path,
    *,
    case: str,
    run_id: str,
    controller: str,
    source: str = "1" * 40,
    prefix: str = "prefix",
    boundary: str = "boundary",
    protocol_days: int = 7,
) -> Path:
    run = suite / case / run_id
    run.mkdir(parents=True)
    _write_object(run / "completion.json", {"status": "complete"})
    _write_object(
        run / "manifest.json",
        {
            "source_commit": source,
            "controller": controller,
            "run_identity": run_id,
            "conditioning_prefix_identity": prefix,
            "evaluation_boundary_identity": boundary,
        },
    )
    _write_object(
        run / "resolved_config.yaml",
        {
            "case_profile": {
                "profile": case,
                "protocol": {
                    "initialization_mode": "evaluation_start_internal_warmup",
                    "internal_warmup_days": 7,
                    "formal_evaluation_days": protocol_days,
                    "initial_setpoint_c": 25.0,
                },
            },
            "method": {"evaluation_hours": 6},
        },
    )
    _write_object(run / "metrics.json", _metrics())
    (run / "performance.csv").write_text("time_seconds\n", encoding="utf-8")
    return run


def _verified(_run_dir: Path) -> dict[str, Any]:
    return {
        "execution_integrity": True,
        "model_contract_clean": True,
        "classification": "RELEASE-PASS",
    }


def test_report_accepts_explicit_single_run_or_compatible_suite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("h3c.outputs.reporting.verify_run", _verified)
    suite = tmp_path / "suite"
    baseline = _completed_run(
        suite,
        case="Demo",
        run_id="baseline",
        controller="deterministic_baseline",
    )
    _completed_run(suite, case="Demo", run_id="agent", controller="h3c_agent")
    single_json, single_markdown = generate_report(baseline, tmp_path / "single-reports")
    suite_json, _ = generate_report(suite, tmp_path / "suite-reports")
    single = json.loads(single_json.read_text(encoding="utf-8"))
    combined = json.loads(suite_json.read_text(encoding="utf-8"))
    assert single["target_kind"] == "run" and len(single["runs"]) == 1
    assert single["schema_version"] == 2
    assert single["runs"][0]["metrics"]["rationale_telemetry"]["decision_use"] == "none"
    assert "Rationale length telemetry" in single_markdown.read_text(encoding="utf-8")
    assert combined["target_kind"] == "suite" and len(combined["runs"]) == 2
    assert len(combined["comparisons"]) == 1
    assert (
        combined["comparisons"][0]["mechanism"]["rationale_telemetry"]["by_role"]
        == _metrics()["rationale_telemetry"]["by_role"]
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source", "2" * 40, "source commits"),
        ("prefix", "different-prefix", "incompatible"),
        ("boundary", "different-boundary", "incompatible"),
        ("protocol_days", 5, "incompatible"),
    ],
)
def test_report_rejects_incompatible_comparison_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    message: str,
) -> None:
    monkeypatch.setattr("h3c.outputs.reporting.verify_run", _verified)
    suite = tmp_path / "suite"
    _completed_run(
        suite,
        case="Demo",
        run_id="baseline",
        controller="deterministic_baseline",
    )
    changed: dict[str, Any] = {field: value}
    _completed_run(
        suite,
        case="Demo",
        run_id="agent",
        controller="h3c_agent",
        **changed,
    )
    with pytest.raises(ValueError, match=message):
        generate_report(suite, tmp_path / "reports")


def test_report_fails_when_target_has_no_eligible_completed_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("h3c.outputs.reporting.verify_run", _verified)
    with pytest.raises(ValueError, match="neither one completed run nor one suite"):
        generate_report(tmp_path, tmp_path / "reports")
