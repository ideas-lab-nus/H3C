from __future__ import annotations

import pytest

from h3c_baselines.configuration import (
    BaselineRunPlan,
    formal_evaluation_plans,
    formal_identification_cases,
)
from h3c_baselines.models import load_registry, verify_all_checkpoints


def test_formal_matrix_has_three_identification_and_fourteen_evaluation_arms() -> None:
    assert formal_identification_cases() == [("SZ_Air", 7), ("MZ_Hydro", 5), ("MZ_Air", 7)]
    plans = formal_evaluation_plans()
    assert len(plans) == 14
    assert [(plan.case, plan.controller) for plan in plans[:4]] == [
        ("SZ_Air", "basic-rbc"),
        ("SZ_Air", "enhanced-rbc"),
        ("SZ_Air", "c-drl"),
        ("SZ_Air", "linear-mpc"),
    ]


def test_single_zone_hierarchical_drl_is_fail_closed() -> None:
    with pytest.raises(ValueError, match="single-zone"):
        BaselineRunPlan("SZ_Air", "h-drl")


def test_five_checkpoint_identities_match_the_registry() -> None:
    assert len(load_registry()["models"]) == 5
    result = verify_all_checkpoints(load_cpu=False)
    assert result["verified"] is True
    assert len(result["models"]) == 5


def test_all_checkpoints_load_on_cpu() -> None:
    result = verify_all_checkpoints(load_cpu=True)
    assert all(row["cpu_load_verified"] is True for row in result["models"].values())
