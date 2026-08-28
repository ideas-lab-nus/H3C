from __future__ import annotations

from typing import Any

from h3c.assurance.action import ACTION_ASSURANCE_ORDER, action_assurance


def _proposal(setpoint: float, *, base: float = 25.0, exempt: bool = False) -> dict[str, Any]:
    return {"setpoint": setpoint, "base": base, "exempt_rate": exempt}


def _observation(
    *, previous: float = 25.0, pmv: float = 0.0, current: float = 1, last: float = 1
) -> dict[str, Any]:
    return {
        "last_setpoint": previous,
        "last_pmv": pmv,
        "current_occupancy": current,
        "last_occupancy": last,
    }


def test_action_assurance_order_and_rate_limit() -> None:
    final, audit = action_assurance(_proposal(27.0), _observation())
    assert audit["order"] == list(ACTION_ASSURANCE_ORDER)
    assert final == 26.0
    assert audit["setpoint_rate_limit_triggered"] is True
    assert audit["comfort_recovery_triggered"] is False
    assert audit["actuator_bounds_triggered"] is False


def test_comfort_recovery_precedes_rate_limit() -> None:
    final, audit = action_assurance(
        _proposal(24.0, base=26.0), _observation(previous=26.0, pmv=0.8)
    )
    assert final == 25.0
    assert audit["comfort_recovery_triggered"] is True
    assert audit["comfort_recovery_reason"] == "occupied_hot_pmv_reset"
    assert audit["setpoint_rate_limit_triggered"] is False


def test_actuator_bounds_are_last_and_mandatory() -> None:
    final, audit = action_assurance(
        _proposal(35.0, base=30.0, exempt=True),
        _observation(previous=30.0, current=0, last=0),
    )
    assert final == 30.0
    assert audit["actuator_bounds_triggered"] is True
    assert audit["actuator_bound"] == "upper"
