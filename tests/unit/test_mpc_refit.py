from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import h3c_baselines.cli as baseline_cli
import h3c_baselines.mpc.refit as refit
from h3c_baselines.mpc.training import EpisodeData
from h3c_baselines.mpc.vector_arx import (
    ArxLayout,
    FittedArxModel,
    Scaling,
    expected_model_identity,
    with_pmv_robust_margin,
)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _configuration() -> dict[str, Any]:
    return {
        "case_order": ["Case"],
        "fit_checkpoints": [8, 16, 32, 64],
        "holdout_episodes": 4,
    }


def _profile() -> dict[str, Any]:
    return {
        "evaluation_start_day": 10,
        "zones": {"z": {}},
        "comfort": {
            "dynamic_clothing": False,
            "metabolic_rate": 1.1,
            "relative_humidity_percent": 50.0,
            "air_velocity_m_s": 0.1,
            "winter_clothing_insulation": 1.0,
            "summer_clothing_insulation": 0.5,
            "clothing_transition_low_c": 10.0,
            "clothing_transition_high_c": 26.0,
        },
    }


def _episode(
    case_dir: Path,
    *,
    role: str,
    episode: int,
    lane: int,
    fallback_count: int = 0,
    rows: int = 9,
) -> Path:
    path = case_dir / "episodes" / f"{role}-{episode:03d}-lane-{lane}"
    path.mkdir(parents=True)
    start = 3 * 86400
    np.savez_compressed(
        path / "trajectory.npz",
        times=np.arange(rows, dtype=np.int64) * 900 + start,
        outputs=np.column_stack((np.linspace(24.0, 25.0, rows), np.linspace(100.0, 120.0, rows))),
        controls=np.full((rows, 1), 25.0),
        disturbances=np.zeros((rows, 5)),
    )
    _write_json(
        path / "manifest.json",
        {
            "role": role,
            "episode": episode,
            "lane": lane,
            "test_id": f"test-lane-{lane}",
            "start_time_seconds": start,
            "warmup_period_seconds": 7 * 86400,
            "steps": rows - 1,
            "reward": -1.0,
            "peak_occupied_absolute_pmv": 0.6,
            "fallback_count": fallback_count,
            "recovery_step_count": 0,
        },
    )
    return path


def _source_bank(
    root: Path,
    *,
    frozen_manifest: bool = False,
) -> tuple[Path, Path]:
    source = root / "outputs" / "baselines" / "mpc" / "training" / "failed"
    case_dir = source / "Case"
    source.mkdir(parents=True)
    source_commit = "a" * 40
    _write_json(
        source / "resolved_plan.json",
        {
            "schema": "h3c_hierarchical_mpc_training_plan",
            "schema_version": 1,
            "execution": True,
            "source_commit": source_commit,
            "case_order": ["Case"],
            "fit_checkpoints": [8, 16, 32, 64],
            "holdout_episodes": 4,
            "workers": 4,
            "warmup_days_per_episode": 7,
            "training_week_days_before_evaluation": 7,
        },
    )
    _write_json(
        source / "failure.json",
        {
            "schema": "h3c_hierarchical_mpc_training_failure",
            "schema_version": 1,
            "source_commit": source_commit,
            "secret_exposure_count": 0,
        },
    )
    episode_paths = [
        *[_episode(case_dir, role="fit", episode=index, lane=index) for index in range(4)],
        _episode(case_dir, role="basic_reference", episode=0, lane=0, rows=13),
        *[_episode(case_dir, role="holdout", episode=index, lane=index) for index in range(4)],
    ]
    fallback = {8: 0, 16: 1, 32: 0, 64: 0}
    for checkpoint, count in fallback.items():
        episode_path = _episode(
            case_dir,
            role="validation",
            episode=checkpoint,
            lane=0,
            fallback_count=count,
        )
        episode_paths.append(episode_path)
        _write_json(
            case_dir / "checkpoints" / f"checkpoint-{checkpoint:03d}.json",
            {
                "checkpoint_fit_episodes": checkpoint,
                "closed_loop_validation": {
                    "fallback_count": count,
                    "peak_occupied_absolute_pmv": 0.6,
                    "reward": -1.0,
                },
            },
        )
    if frozen_manifest:
        counts = {
            lane: sum(
                json.loads((path / "manifest.json").read_text(encoding="utf-8"))["lane"] == lane
                for path in episode_paths
            )
            for lane in range(4)
        }
        _write_json(
            case_dir / "frozen_model" / "training_manifest.json",
            {
                "schema": "h3c_hierarchical_mpc_training_manifest",
                "schema_version": 1,
                "case": "Case",
                "source_commit": source_commit,
                "training_output": case_dir.relative_to(root).as_posix(),
                "lane_lifecycle": [
                    {
                        "lane": lane,
                        "test_id": f"test-lane-{lane}",
                        "select_count": 1,
                        "initialize_count": counts[lane],
                        "stop_count": 1,
                        "warmup_days_per_initialize": 7,
                    }
                    for lane in range(4)
                ],
            },
        )
    return source, case_dir


def _patch_source_owners(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(refit, "repository_root", lambda: root)
    monkeypatch.setattr(refit, "load_hierarchical_mpc_config", _configuration)
    monkeypatch.setattr(refit, "load_profile", lambda _case: _profile())


def test_source_roles_reconstruct_exact_partition_and_lane_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _ = _source_bank(tmp_path, frozen_manifest=True)
    _patch_source_owners(monkeypatch, tmp_path)

    roles = refit._case_roles("Case", source)
    summary = refit._role_summary(roles)

    assert summary["episodes"]["adaptive_validation"] == [
        "episodes/validation-008-lane-0",
        "episodes/validation-032-lane-0",
    ]
    assert summary["episodes"]["calibration"] == "episodes/validation-064-lane-0"
    assert summary["episodes"]["excluded_fallback"] == ["episodes/validation-016-lane-0"]
    assert len(summary["episodes"]["holdout"]) == 4
    assert all(row["test_identity_count"] == 1 for row in summary["lane_lifecycle"])
    assert all(row["frozen_manifest_cross_checked"] is True for row in summary["lane_lifecycle"])


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("test_id", "different-test", "test identity is unstable"),
        ("reward", float("nan"), "episode metrics are invalid"),
        ("fallback_count", -1, "episode metrics are invalid"),
    ],
)
def test_source_episode_tampering_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    message: str,
) -> None:
    source, case_dir = _source_bank(tmp_path)
    _patch_source_owners(monkeypatch, tmp_path)
    manifest_path = case_dir / "episodes" / "validation-032-lane-0" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[field] = value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        refit._case_roles("Case", source)


def test_source_plan_and_failure_commit_must_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _ = _source_bank(tmp_path)
    _patch_source_owners(monkeypatch, tmp_path)
    failure_path = source / "failure.json"
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    failure["source_commit"] = "b" * 40
    failure_path.write_text(json.dumps(failure), encoding="utf-8")

    with pytest.raises(ValueError, match="plan/failure identity is inconsistent"):
        refit._resolve_source_run(source)


def _constant_model(layout: ArxLayout) -> FittedArxModel:
    base = FittedArxModel(
        layout=layout,
        intercept=np.asarray([24.0, 100.0]),
        coefficients=np.zeros((layout.feature_dimension, layout.output_dimension)),
        scaling=Scaling(
            feature_mean=np.zeros(layout.feature_dimension),
            feature_scale=np.ones(layout.feature_dimension),
            output_mean=np.zeros(layout.output_dimension),
            output_scale=np.ones(layout.output_dimension),
        ),
        ridge_alpha=1.0,
        identity="placeholder",
    )
    return FittedArxModel(
        base.layout,
        base.intercept,
        base.coefficients,
        base.scaling,
        base.ridge_alpha,
        expected_model_identity(base),
    )


def test_calibration_uses_real_basic_reference_occupancy_at_k_plus_4() -> None:
    layout = ArxLayout(("z",), ("outdoor", "solar", "occupancy", "sin", "cos"))
    model = _constant_model(layout)
    times = np.arange(9, dtype=np.int64) * 900
    outputs = np.column_stack((np.full(9, 25.0), np.full(9, 100.0)))
    controls = np.full((9, 1), 25.0)
    calibration_disturbances = np.zeros((9, 5))
    reference_times = np.arange(13, dtype=np.int64) * 900
    reference_disturbances = np.zeros((13, 5))
    # For origin=3, k+3 is unoccupied while the real k+4 target is occupied.
    reference_disturbances[7, 2] = 1.0
    calibration = EpisodeData(
        "validation",
        64,
        0,
        "test",
        times,
        outputs,
        controls,
        calibration_disturbances,
        -1.0,
        0.6,
        0,
        0,
    )
    basic = EpisodeData(
        "basic_reference",
        0,
        0,
        "test",
        reference_times,
        np.column_stack((np.full(13, 25.0), np.full(13, 100.0))),
        np.full((13, 1), 25.0),
        reference_disturbances,
        -1.0,
        0.6,
        0,
        0,
    )

    report = refit._calibration_report(model, calibration, basic, _profile(), {0: 20.0})

    assert report["terminal_reference"]["target_offset_steps"] == 4
    assert report["terminal_reference"]["terminal_occupied_zone_targets"] == 1
    assert report["residual_count"] == 2
    assert report["scope"] == "case_specific_estimate_common_formula"


def test_margin_changes_bundle_identity_but_zero_preserves_it() -> None:
    model = _constant_model(ArxLayout(("z",), ("outdoor", "solar", "occupancy", "sin", "cos")))

    assert with_pmv_robust_margin(model, 0.0).identity == model.identity
    calibrated = with_pmv_robust_margin(model, 0.1)
    assert calibrated.identity != model.identity
    assert calibrated.identity == expected_model_identity(calibrated)


def test_source_evidence_recomputes_persistence_instead_of_reading_candidate_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _ = _source_bank(tmp_path)
    _patch_source_owners(monkeypatch, tmp_path)
    model = _constant_model(ArxLayout(("z",), ("outdoor", "solar", "occupancy", "sin", "cos")))
    observed: dict[str, int] = {}

    def quality(_model: FittedArxModel, episodes: list[EpisodeData]) -> dict[str, Any]:
        observed["holdout_episode_count"] = len(episodes)
        return {"finite": True, "beats_persistence": True, "owner": "recomputed"}

    monkeypatch.setattr(refit, "open_loop_prediction_quality", quality)
    monkeypatch.setattr(
        refit,
        "_calibration_report",
        lambda *_args, **_kwargs: {"owner": "recomputed"},
    )
    monkeypatch.setattr(refit, "_daily_outdoor_means", lambda _episode: {3: 20.0})

    evidence = refit.recompute_candidate_source_evidence("Case", source, model)

    assert observed["holdout_episode_count"] == 4
    assert evidence["prediction_quality"] == {
        "finite": True,
        "beats_persistence": True,
        "owner": "recomputed",
    }
    assert evidence["holdout_use"] == "alpha_selection_and_persistence_gate_only"
    assert evidence["final_fit_includes_holdout"] is False


def test_refit_cli_is_dry_without_explicit_execute(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        baseline_cli,
        "resolved_refit_plan",
        lambda source: {"execution": False, "source_run": str(source)},
    )

    def forbidden_execute(_source: Path) -> dict[str, Any]:
        raise AssertionError("dry refit must not execute")

    monkeypatch.setattr(baseline_cli, "refit_hierarchical_mpc", forbidden_execute)

    assert baseline_cli.main(["mpc", "refit", "--source-run", "preserved-failure"]) == 0
    assert '"execution": false' in capsys.readouterr().out
