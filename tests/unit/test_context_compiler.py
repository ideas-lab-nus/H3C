from __future__ import annotations

import copy
import json
import re
from typing import Any

import pytest

from h3c.agents.context_compiler import (
    ContextBuilder,
    compile_working_memory,
    decode_compact_context,
    decode_working_memory,
    factor_common_rows,
)
from h3c.agents.time_context import action_and_outcome_times, decision_window


def _completed_record(zone: str, temperature: float = 24.0) -> dict[str, Any]:
    steps = [40, 41, 42, 43]
    return {
        "hour": 10,
        "zone": zone,
        "context": {
            "regime_step_coverage": {"steady_state_occupancy": steps},
            "initial_observation": {
                "zone_temperature_c": temperature,
                "current_occupancy": 1.0,
                "last_occupancy": 1.0,
                "occupancy_next_steps": [1.0, 1.0, 1.0, 1.0],
                "last_pmv": 0.2,
                "last_setpoint_c": 25.0,
            },
        },
        "action": {
            "proposal": {"op": "no_change", "rationale": "温度 | 稳定"},
            "admission": {"status": "accepted", "completed_validation_stages": []},
            "program_version_before": 0,
            "program_version_after": 0,
            "actual_setpoints_c": [25.0, 25.0, 25.0, 25.0],
            "matched_rules": ["hold", "hold", "hold", "hold"],
            "shield": [
                {
                    "step": step,
                    "actuator_bounds": False,
                    "setpoint_rate_limit": False,
                    "comfort_recovery": False,
                }
                for step in steps
            ],
        },
        "outcome": {
            "zone_temperatures_c": [temperature + value for value in (0.1, 0.2, 0.3, 0.4)],
            "pmv": [0.21, 0.22, 0.23, 0.24],
            "effective_occupancy": [1.0, 1.0, 1.0, 1.0],
            "site_cost": 1.25,
            "site_energy_kwh": 2.5,
            "discomfort_zone_hours": 0.0,
            "discomfort_pmv_hours": 0.0,
            "occupied_peak_absolute_pmv": 0.24,
            "setpoint_total_variation_c": 0.0,
            "setpoint_direction_reversals": 0,
        },
        "lesson": "Temperature rose gradually. Comfort remained inside the observed band.",
    }


def test_common_rows_preserves_scalars_empty_lists_unicode_and_delimiters() -> None:
    records = [
        {
            "zone": "东|区",
            "zero": 0,
            "flag": False,
            "empty": [],
            "same_path": {"value": 3},
            "different": 1,
        },
        {
            "zone": "西区",
            "zero": 0,
            "flag": False,
            "empty": [],
            "same_path": {"value": 3},
            "different": 2,
        },
    ]
    view = factor_common_rows(records, identity_fields=("zone",))
    builder = ContextBuilder()
    builder.add_common_rows("ROWS", records, identity_fields=("zone",))
    compiled = builder.build()
    assert decode_compact_context(compiled.compact_view) == compiled.canonical_ir
    assert view["common"] == {
        "zero": 0,
        "flag": False,
        "empty": [],
        "same_path": {"value": 3},
    }
    assert "\\u007c" in compiled.agent_view
    assert compiled.audit_view["round_trip_equal"] is True


def test_working_memory_has_explicit_time_state_action_and_derived_layers() -> None:
    records = [_completed_record("EAS"), _completed_record("WES", 24.5)]
    view = compile_working_memory(records)
    assert decode_working_memory(view) == records
    hour = view["hours"][0]
    assert isinstance(hour, dict)
    assert set(hour) == {
        "hour",
        "clock",
        "time_semantics",
        "site_result",
        "hourly_decision",
        "current_state",
        "recent_state_history",
        "action_history",
        "occupancy_forecast",
        "derived_features",
    }
    builder = ContextBuilder()
    builder.add_working_memory("WORKING MEMORY", records)
    rendered = builder.build().agent_view
    for label in (
        "completed_interval",
        "recent_state_history",
        "control_action_history",
        "state_times",
        "derived_features",
    ):
        assert label in rendered
    assert "10:00" in rendered and "11:00" in rendered
    assert not any(
        token in rendered for token in ("decision_hour", "sample_index", "physical_step", '"step":')
    )
    assert "[25.0,25.0" not in rendered
    assert '"[{\\"' not in rendered


def test_clock_context_marks_midnight_without_a_date_or_year() -> None:
    start = 23 * 3600 + 45 * 60
    window = decision_window(start)
    assert window["current_time"] == "23:45"
    assert window["control_interval"] == "[23:45, next day 00:45)"
    assert window["action_times"] == [
        "23:45",
        "next day 00:00",
        "next day 00:15",
        "next day 00:30",
    ]
    assert window["forecast_outcome_times"][-1] == "next day 00:45"
    actions, outcomes = action_and_outcome_times(start)
    assert all(action != outcome for action, outcome in zip(actions, outcomes, strict=True))
    assert not re.search(r"\b\d{4}-\d{2}-\d{2}\b", json.dumps(window))


def test_working_memory_fails_closed_when_repeated_site_owner_disagrees() -> None:
    east = _completed_record("EAS")
    west = _completed_record("WES")
    west["outcome"]["site_cost"] = 9.0
    with pytest.raises(ValueError, match="site-result owners disagree"):
        compile_working_memory([east, west])


def test_compact_view_is_independent_of_input_mutation() -> None:
    record = _completed_record("EAS")
    builder = ContextBuilder()
    builder.add_working_memory("WORKING MEMORY", [record])
    compiled = builder.build()
    snapshot = copy.deepcopy(compiled.canonical_ir)
    record["lesson"] = "changed"
    assert compiled.canonical_ir == snapshot
