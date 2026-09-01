from __future__ import annotations

import copy

import pytest

from h3c.outputs.verification import _align_expected_caol_with_persisted_schema


def _record() -> dict[str, object]:
    return {
        "hour": 0,
        "zone": "NZ",
        "action": {
            "actual_setpoints_c": [25.0, 25.0, 25.0, 25.0],
            "regime_base_setpoints_c": [25.0, 25.0, 25.0, 25.0],
            "setpoint_offsets_from_regime_base_c": [0.0, 0.0, 0.0, 0.0],
            "cooling_effects_relative_to_regime_base": [
                "at_regime_base",
                "at_regime_base",
                "at_regime_base",
                "at_regime_base",
            ],
        },
    }


def test_legacy_caol_can_omit_the_complete_new_derived_fact_group() -> None:
    expected = _record()
    persisted = copy.deepcopy(expected)
    action = persisted["action"]
    assert isinstance(action, dict)
    for field in (
        "regime_base_setpoints_c",
        "setpoint_offsets_from_regime_base_c",
        "cooling_effects_relative_to_regime_base",
    ):
        action.pop(field)

    aligned = _align_expected_caol_with_persisted_schema(expected, persisted)
    assert aligned == persisted


def test_new_caol_cannot_partially_omit_derived_action_facts() -> None:
    expected = _record()
    persisted = copy.deepcopy(expected)
    action = persisted["action"]
    assert isinstance(action, dict)
    action.pop("cooling_effects_relative_to_regime_base")

    with pytest.raises(ValueError, match="complete group"):
        _align_expected_caol_with_persisted_schema(expected, persisted)
