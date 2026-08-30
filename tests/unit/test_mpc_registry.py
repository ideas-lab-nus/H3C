from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import h3c_baselines.mpc.registry as registry
import h3c_baselines.mpc.training as training
from h3c_baselines.mpc.vector_arx import (
    ArxLayout,
    FittedArxModel,
    Scaling,
    expected_model_identity,
)

CASES = ["CaseA", "CaseB", "CaseC"]


def _robust_attestation(model: FittedArxModel) -> dict[str, Any]:
    return {
        "robust_margin": {
            "scope": "case_specific_estimate_common_formula",
            "estimator": "p95_absolute_occupied_pmv_prediction_residual",
            "quantile": 0.95,
            "order_statistic": "higher",
            "calibration_episode": "episodes/validation-032-lane-0",
            "sample_count": 100,
            "pmv_margin": model.pmv_robust_margin,
            "internal_comfort_band": 0.5 - model.pmv_robust_margin,
            "application": "internal_soft_comfort_band_only",
        },
        "terminal_reference": {
            "target_offset_steps": 4,
            "calibration_occupancy_source": ("basic_reference.disturbances[timestamp=origin+4]"),
            "runtime_owner": "effective_occupancy_forecast(step+4)",
            "terminal_zone_targets": 100,
            "terminal_occupied_zone_targets": 50,
        },
    }


def _configuration() -> dict[str, Any]:
    return {
        "case_order": CASES,
        "excitation": {
            "occupied_bounds_c": [23.5, 26.5],
            "unoccupied_bounds_c": [20.0, 30.0],
        },
    }


def _model() -> FittedArxModel:
    layout = ArxLayout(("zone",), ("outdoor", "solar", "occupancy", "sin", "cos"))
    base = FittedArxModel(
        layout,
        np.asarray([24.0, 100.0]),
        np.zeros((layout.feature_dimension, layout.output_dimension)),
        Scaling(
            np.zeros(layout.feature_dimension),
            np.ones(layout.feature_dimension),
            np.zeros(layout.output_dimension),
            np.ones(layout.output_dimension),
        ),
        1.0,
        "placeholder",
        0.1,
    )
    return FittedArxModel(
        base.layout,
        base.intercept,
        base.coefficients,
        base.scaling,
        base.ridge_alpha,
        expected_model_identity(base),
        base.pmv_robust_margin,
    )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _workspaces(root: Path) -> tuple[Path, Path, dict[str, Any]]:
    (root / "models").mkdir()
    refit = root / "outputs" / "baselines" / "mpc" / "refit" / "refit"
    validation = root / "outputs" / "baselines" / "mpc" / "validation" / "validation"
    model = _model()
    robust = _robust_attestation(model)
    for case in CASES:
        candidate = refit / case / "candidate_model"
        candidate.mkdir(parents=True)
        model.save(candidate / "model_coefficients.npz")
        _write_json(
            candidate / "model_card.json",
            {
                "case": case,
                "model_identity": model.identity,
                "robust_margin": robust["robust_margin"],
            },
        )
        _write_json(
            candidate / "candidate_report.json",
            {
                "case": case,
                "model_identity": model.identity,
                "calibration": {"terminal_reference": robust["terminal_reference"]},
            },
        )
    results = [
        {
            "case": case,
            "test_id": f"fresh-{case}",
            "model_identity": model.identity,
            "steps": 668,
            "reward": -1.0,
            "fallback_count": 0,
            "occupied_peak_absolute_pmv": 0.6,
            "eligible": True,
        }
        for case in CASES
    ]
    _write_json(
        validation / "resolved_plan.json",
        {
            "candidate_gates": [
                {
                    "case": case,
                    "model_identity": model.identity,
                    "valid": True,
                    "checks": {
                        "recomputed_persistence_gate": True,
                        "source_prediction_finite": True,
                        "source_beats_persistence": True,
                    },
                }
                for case in CASES
            ]
        },
    )
    _write_json(
        validation / "completion.json",
        {
            "schema": "h3c_hierarchical_mpc_validation_completion",
            "validation_source_commit": "a" * 40,
            "refit_verification_identity": "b" * 64,
            "refit_workspace": refit.relative_to(root).as_posix(),
            "cases": results,
        },
    )
    return refit, validation, {"valid": True, "cases": results}


def _patch_owners(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    verification: dict[str, Any],
) -> None:
    monkeypatch.setattr(registry, "repository_root", lambda: root)
    monkeypatch.setattr(registry, "load_hierarchical_mpc_config", _configuration)
    monkeypatch.setattr(
        registry,
        "load_profile",
        lambda _case: {"evaluation_start_day": 10},
    )
    monkeypatch.setattr(
        registry,
        "verify_validation_workspace",
        lambda _workspace: verification,
    )
    monkeypatch.setattr(registry, "secret_occurrences", lambda _path: 0)


def test_three_case_suite_is_published_by_exactly_one_directory_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, validation, verification = _workspaces(tmp_path)
    _patch_owners(monkeypatch, tmp_path, verification)
    real_replace = os.replace
    replacements: list[tuple[Path, Path]] = []

    def replace(source: str | Path, target: str | Path) -> None:
        replacements.append((Path(source), Path(target)))
        real_replace(source, target)

    monkeypatch.setattr(registry.os, "replace", replace)

    result = registry.freeze_validated_mpc_suite(validation)

    target = tmp_path / "models" / "mpc"
    assert result["valid"] is True
    assert len(replacements) == 1
    assert replacements[0][1] == target
    assert replacements[0][0].name.startswith(".mpc-")
    assert replacements[0][0].name.endswith(".pending")
    assert not replacements[0][0].exists()
    assert (target / "freeze_manifest.json").is_file()
    assert all((target / case / "model_coefficients.npz").is_file() for case in CASES)
    manifest = json.loads((target / "freeze_manifest.json").read_text(encoding="utf-8"))
    payload_keys = (
        "validation_workspace",
        "validation_completion_sha256",
        "validation_source_commit",
        "refit_verification_identity",
        "refit_workspace",
        "case_order",
        "model_identities",
        "validation_results",
        "source_bundles",
        "refit_candidate_gates",
    )
    assert (
        registry._identity({key: manifest[key] for key in payload_keys})
        == result["freeze_identity"]
    )
    card = json.loads((target / "CaseA" / "model_card.json").read_text(encoding="utf-8"))
    training_manifest = json.loads(
        (target / "CaseA" / "training_manifest.json").read_text(encoding="utf-8")
    )
    assert (
        card["robust_calibration_attestation"]
        == training_manifest["robust_calibration_attestation"]
        == manifest["source_bundles"][0]["robust_calibration_attestation"]
    )
    assert registry.verify_frozen_mpc_suite(target)["valid"] is True


def test_frozen_suite_is_self_contained_and_runtime_loadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, validation, verification = _workspaces(tmp_path)
    _patch_owners(monkeypatch, tmp_path, verification)
    result = registry.freeze_validated_mpc_suite(validation)
    target = Path(result["target"])
    displaced = tmp_path / "validation-evidence-displaced"
    validation.rename(displaced)

    assert registry.verify_frozen_mpc_suite(target)["valid"] is True
    monkeypatch.setattr(training, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(
        training,
        "load_profile",
        lambda _case: {"evaluation_start_day": 10, "zones": {"zone": {}}},
    )
    monkeypatch.setattr(training, "load_hierarchical_mpc_config", _configuration)
    assert training.verify_frozen_mpc_model("CaseA")["valid"] is True


@pytest.mark.parametrize("tamper", ["missing_manifest", "coordinated_robust_change"])
def test_runtime_model_preflight_requires_valid_parent_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tamper: str,
) -> None:
    _, validation, verification = _workspaces(tmp_path)
    _patch_owners(monkeypatch, tmp_path, verification)
    target = Path(registry.freeze_validated_mpc_suite(validation)["target"])
    monkeypatch.setattr(training, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(
        training,
        "load_profile",
        lambda _case: {"evaluation_start_day": 10, "zones": {"zone": {}}},
    )
    monkeypatch.setattr(training, "load_hierarchical_mpc_config", _configuration)

    if tamper == "missing_manifest":
        (target / "freeze_manifest.json").rename(target / "freeze_manifest.absent")
    else:
        for name in ("model_card.json", "training_manifest.json"):
            path = target / "CaseA" / name
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["robust_calibration_attestation"]["robust_margin"]["application"] = (
                "unregistered_application"
            )
            path.write_text(json.dumps(payload), encoding="utf-8")

    checked = training.verify_frozen_mpc_model("CaseA")

    assert checked["valid"] is False
    assert checked["checks"]["transactional_suite_registry"] is False


def test_existing_target_is_never_overwritten_or_deleted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, validation, verification = _workspaces(tmp_path)
    _patch_owners(monkeypatch, tmp_path, verification)
    target = tmp_path / "models" / "mpc"
    target.mkdir(parents=True)
    marker = target / "user-owned.txt"
    marker.write_text("preserve", encoding="utf-8")

    with pytest.raises(ValueError, match="overwrite is forbidden"):
        registry.freeze_validated_mpc_suite(validation)

    assert marker.read_text(encoding="utf-8") == "preserve"
    assert not list((tmp_path / "models").glob(".mpc-*.pending"))


def test_invalid_validation_creates_no_pending_or_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, validation, verification = _workspaces(tmp_path)
    verification["valid"] = False
    _patch_owners(monkeypatch, tmp_path, verification)

    with pytest.raises(ValueError, match="complete verified"):
        registry.freeze_validated_mpc_suite(validation)

    assert not (tmp_path / "models" / "mpc").exists()
    assert not list((tmp_path / "models").glob(".mpc-*.pending"))


def test_staging_failure_preserves_pending_evidence_and_never_publishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, validation, verification = _workspaces(tmp_path)
    _patch_owners(monkeypatch, tmp_path, verification)
    original = registry._stage_case

    def stage_case(**kwargs: Any) -> dict[str, Any]:
        if kwargs["case"] == "CaseC":
            raise ValueError("registered staging fault")
        return original(**kwargs)

    monkeypatch.setattr(registry, "_stage_case", stage_case)

    with pytest.raises(ValueError, match="registered staging fault"):
        registry.freeze_validated_mpc_suite(validation)

    assert not (tmp_path / "models" / "mpc").exists()
    pending = list((tmp_path / "models").glob(".mpc-*.pending"))
    assert len(pending) == 1
    assert (pending[0] / "CaseA" / "model_coefficients.npz").is_file()
    assert (pending[0] / "CaseB" / "model_coefficients.npz").is_file()


def test_extra_file_or_coefficient_tamper_fails_staged_verifier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, validation, verification = _workspaces(tmp_path)
    _patch_owners(monkeypatch, tmp_path, verification)
    result = registry.freeze_validated_mpc_suite(validation)
    target = Path(result["target"])
    (target / "unexpected.txt").write_text("tamper", encoding="utf-8")

    checked = registry.verify_frozen_mpc_suite(target)

    assert checked["valid"] is False
    assert checked["checks"]["exact_file_set"] is False


def test_coordinated_card_and_manifest_hash_tamper_fails_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, validation, verification = _workspaces(tmp_path)
    _patch_owners(monkeypatch, tmp_path, verification)
    target = Path(registry.freeze_validated_mpc_suite(validation)["target"])
    card_path = target / "CaseA" / "model_card.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["provenance"]["refit_model_card_sha256"] = "f" * 64
    card_path.write_text(json.dumps(card), encoding="utf-8")
    manifest_path = target / "freeze_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case_row = next(row for row in manifest["cases"] if row["case"] == "CaseA")
    case_row["model_card_sha256"] = registry._sha256(card_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    checked = registry.verify_frozen_mpc_suite(target)

    assert checked["valid"] is False
    assert checked["case_checks"]["CaseA"] is False


def test_coordinated_robust_attestation_tamper_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, validation, verification = _workspaces(tmp_path)
    _patch_owners(monkeypatch, tmp_path, verification)
    target = Path(registry.freeze_validated_mpc_suite(validation)["target"])
    card_path = target / "CaseA" / "model_card.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["robust_calibration_attestation"]["robust_margin"]["application"] = (
        "unregistered_application"
    )
    card_path.write_text(json.dumps(card), encoding="utf-8")
    manifest_path = target / "freeze_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case_row = next(row for row in manifest["cases"] if row["case"] == "CaseA")
    case_row["model_card_sha256"] = registry._sha256(card_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    checked = registry.verify_frozen_mpc_suite(target)

    assert checked["valid"] is False
    assert checked["case_checks"]["CaseA"] is False
