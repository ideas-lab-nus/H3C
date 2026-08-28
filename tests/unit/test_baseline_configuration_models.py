from __future__ import annotations

import pytest

from h3c_baselines.configuration import (
    BaselineRunPlan,
    formal_evaluation_plans,
    formal_identification_cases,
    legacy_replay_plans,
)
from h3c_baselines.models import load_registry, verify_all_checkpoints


def test_formal_drl_matrix_has_no_mpc_identification_and_eleven_evaluation_arms() -> None:
    assert formal_identification_cases() == []
    plans = formal_evaluation_plans()
    assert len(plans) == 11
    assert {plan.case: plan.evaluation_hours for plan in plans} == {
        "SZ_Air": 168,
        "MZ_Hydro": 120,
        "MZ_Air": 168,
    }
    assert [(plan.case, plan.controller) for plan in plans[:3]] == [
        ("SZ_Air", "basic-rbc"),
        ("SZ_Air", "enhanced-rbc"),
        ("SZ_Air", "c-drl"),
    ]


def test_single_zone_hierarchical_drl_is_fail_closed() -> None:
    with pytest.raises(ValueError, match="single-zone"):
        BaselineRunPlan("SZ_Air", "h-drl")


def test_legacy_replay_matrix_freezes_archived_protocol_without_mpc() -> None:
    plans = legacy_replay_plans()
    assert [(plan.case, plan.controller) for plan in plans] == [
        ("SZ_Air", "basic-rbc"),
        ("SZ_Air", "c-drl"),
        ("MZ_Hydro", "basic-rbc"),
        ("MZ_Hydro", "c-drl"),
        ("MZ_Hydro", "h-drl"),
        ("MZ_Air", "basic-rbc"),
        ("MZ_Air", "c-drl"),
        ("MZ_Air", "h-drl"),
    ]
    assert {plan.case: plan.evaluation_hours for plan in plans} == {
        "SZ_Air": 168,
        "MZ_Hydro": 120,
        "MZ_Air": 168,
    }
    assert all(plan.conditioning_mode == "legacy_internal_warmup" for plan in plans)
    mz_air = next(plan.resolved() for plan in plans if plan.case == "MZ_Air")
    assert mz_air["case_profile"]["occupancy"] == {
        "mode": "raw_count_positive",
        "source": "Archived FinalMZAIR evaluation workflow",
    }
    assert mz_air["case_profile"]["objective"]["smoothness_scale"] == 0.193466


def test_five_checkpoint_identities_match_the_registry() -> None:
    assert len(load_registry()["models"]) == 5
    result = verify_all_checkpoints(load_cpu=False)
    assert result["verified"] is True
    assert len(result["models"]) == 5


def test_all_checkpoints_load_on_cpu() -> None:
    result = verify_all_checkpoints(load_cpu=True)
    assert all(row["cpu_load_verified"] is True for row in result["models"].values())
