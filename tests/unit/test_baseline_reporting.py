"""Focused tests for baseline report calculations and source discovery."""

from pathlib import Path

import pytest

from h3c_baselines.outputs.reporting import (
    _cumulative,
    _discover_runs,
    _historical_verification_is_compatible,
    _registered_benchmark_keys,
)


def test_cumulative_cost_preserves_every_step() -> None:
    assert _cumulative([0.25, 0.5, 1.0]) == [0.25, 0.75, 1.75]
    assert _cumulative([]) == []


def test_multiple_report_roots_discover_unique_completed_runs(tmp_path: Path) -> None:
    roots = [tmp_path / "formal", tmp_path / "mpc-formal"]
    expected: list[Path] = []
    for index, root in enumerate(roots):
        run = root / f"run-{index}"
        run.mkdir(parents=True)
        (run / "completion.json").write_text("{}\n", encoding="utf-8")
        (run / "metrics.json").write_text("{}\n", encoding="utf-8")
        expected.append(run.resolve())
    assert _discover_runs(roots) == sorted(expected, key=str)
    with pytest.raises(ValueError, match="duplicate"):
        _discover_runs([roots[0], roots[0]])


def test_registered_baseline_matrix_has_fourteen_unique_arms() -> None:
    keys = _registered_benchmark_keys()
    assert len(keys) == 14
    assert any(key[:2] == ("SZ_Air", "hierarchical-mpc") for key in keys)
    assert any(key[:2] == ("MZ_Hydro", "h-drl") for key in keys)


def test_historical_verification_compatibility_is_narrow() -> None:
    current = {
        "checks": {
            "metrics_recomputed": True,
            "execution_identity": False,
            "execution_identity_schema": False,
            "completion_identity": False,
        },
        "errors": [
            "completion_identity",
            "execution_identity",
            "execution_identity_schema",
        ],
        "metrics_identity": "metrics",
    }
    persisted = {
        "execution_integrity": True,
        "completion_eligible": True,
        "errors": [],
        "classification": "BASELINE-PASS",
        "metrics_identity": "metrics",
    }
    completion = {"classification": "BASELINE-PASS"}
    assert _historical_verification_is_compatible(current, persisted, completion)
    current["checks"]["metrics_recomputed"] = False
    current["errors"].append("metrics_recomputed")
    assert not _historical_verification_is_compatible(current, persisted, completion)
