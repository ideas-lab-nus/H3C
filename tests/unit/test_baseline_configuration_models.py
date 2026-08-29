from __future__ import annotations

import pytest

from h3c_baselines.cli import _parser
from h3c_baselines.configuration import (
    BaselineRunPlan,
    formal_evaluation_plans,
)
from h3c_baselines.models import load_registry, verify_all_checkpoints


def test_formal_matrix_has_no_mpc_identification_and_eleven_evaluation_arms() -> None:
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
    assert all(plan.controller != "linear-mpc" for plan in plans)


def test_linear_mpc_is_not_a_public_baseline_command() -> None:
    with pytest.raises(SystemExit):
        _parser().parse_args(["run", "--case", "SZ_Air", "--controller", "linear-mpc"])


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
