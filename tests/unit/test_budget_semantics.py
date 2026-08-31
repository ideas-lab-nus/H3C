from __future__ import annotations

import pytest

from h3c.control.budget import BudgetLedger, validate_allocation


def _allocation() -> dict[str, object]:
    return {
        "site_cap_c": 5.0,
        "zone_budgets_c": {"east": 2.0, "west": 1.0},
        "priority": ["east", "west"],
        "rationale_per_zone": {"east": "first", "west": "second"},
    }


def test_budget_ledger_separates_reserved_and_shared_pool_consumption() -> None:
    allocation = _allocation()
    ledger = BudgetLedger(allocation, ["east", "west"])
    assert (
        ledger.energy_budget_validation("east", 2.3, parameter="fixture_program_delta", step=0)
        is None
    )
    usage = ledger.utilisation()
    assert usage["reserved_allowance_by_zone_c"] == {"east": 2.0, "west": 1.0}
    assert usage["reserved_consumption_by_zone_c"] == {"east": 2.0, "west": 0.0}
    assert usage["residual_initial_c"] == 2.0
    assert usage["residual_used_by"] == {"east": 0.3}
    assert usage["residual_left_c"] == 1.7


def test_allocation_must_equal_the_supplied_site_cap_when_bound() -> None:
    allocation = _allocation()
    validate_allocation(
        allocation,
        ["east", "west"],
        causal_enabled=False,
        expected_site_cap_c=5.0,
    )
    with pytest.raises(ValueError, match="equal the supplied site cap"):
        validate_allocation(
            allocation,
            ["east", "west"],
            causal_enabled=False,
            expected_site_cap_c=4.0,
        )


def test_nondefault_per_zone_reserved_cap_is_the_validator_owner() -> None:
    allocation = {
        "site_cap_c": 4.0,
        "zone_budgets_c": {"east": 1.75, "west": 2.25},
        "priority": ["west", "east"],
        "rationale_per_zone": {"east": "bounded east", "west": "bounded west"},
    }
    validate_allocation(
        allocation,
        ["east", "west"],
        causal_enabled=False,
        expected_site_cap_c=4.0,
        expected_per_zone_reserved_cap_c=2.25,
    )
    with pytest.raises(ValueError, match="zone allocation is outside its bound"):
        validate_allocation(
            allocation,
            ["east", "west"],
            causal_enabled=False,
            expected_site_cap_c=4.0,
            expected_per_zone_reserved_cap_c=2.0,
        )

    ledger = BudgetLedger(
        allocation,
        ["east", "west"],
        per_zone_reserved_cap_c=2.25,
    )
    assert ledger.snapshot("east") == {
        "remaining_c": 1.75,
        "site_residual_c": 0.0,
        "priority_rank": 2,
    }
