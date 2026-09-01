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
            "proposal": {
                "op": "no_change",
                "rationale": "温度 | 稳定",
                "causal_edge_ids": ["ce_audit_only"],
            },
            "deterministic_program_effect": {
                "program_direction": "up",
                "expected_effects": [{"node": "zone_temp", "direction": "up"}],
            },
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


def _add_objective_feedback(record: dict[str, Any], *, local_scale: float = 1.0) -> None:
    record["outcome"]["objective_feedback"] = {
        "interval_reward": -10.0,
        "site_step_reward": [-1.0, -2.0, -3.0, -4.0],
        "site_energy_penalty": [0.8, 1.8, 2.8, 3.8],
        "site_comfort_penalty": [0.1, 0.1, 0.1, 0.1],
        "site_smoothness_penalty": [0.1, 0.1, 0.1, 0.1],
        "zone_comfort_penalty_contribution": [
            local_scale * value for value in (0.01, 0.02, 0.03, 0.04)
        ],
        "zone_smoothness_penalty_contribution": [
            local_scale * value for value in (0.04, 0.03, 0.02, 0.01)
        ],
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
    assert "deterministic_program_effect" in rendered
    assert "program_direction" in rendered
    assert "ce_audit_only" not in rendered


def test_objective_feedback_is_lossless_clocked_and_role_scoped() -> None:
    east = _completed_record("EAS")
    west = _completed_record("WES", 24.5)
    _add_objective_feedback(east)
    _add_objective_feedback(west, local_scale=2.0)
    records = [east, west]

    view = compile_working_memory(records)
    assert decode_working_memory(view) == records
    feedback = view["hours"][0]["objective_feedback"]
    assert feedback["interval_reward"] == -10.0

    orchestrator_builder = ContextBuilder()
    orchestrator_builder.add_working_memory("WORKING MEMORY", records)
    orchestrator_text = orchestrator_builder.build().agent_view
    assert orchestrator_text.count("site_reward_history") == 1
    assert "zone_penalty_contributions" not in orchestrator_text
    for action, outcome in zip(
        ("10:00", "10:15", "10:30", "10:45"),
        ("10:15", "10:30", "10:45", "11:00"),
        strict=True,
    ):
        assert action in orchestrator_text and outcome in orchestrator_text

    executor_builder = ContextBuilder()
    executor_builder.add_working_memory("WORKING MEMORY", [east])
    assert "zone_penalty_contributions" in executor_builder.build().agent_view

    reflector_builder = ContextBuilder()
    reflector_builder.add_working_memory(
        "COMPLETED CONTROL INTERVAL",
        records,
        presentation="completed_interval",
    )
    reflector_text = reflector_builder.build().agent_view
    assert "zone_penalty_contributions" in reflector_text
    assert "EAS" in reflector_text and "WES" in reflector_text


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


def test_orchestrator_projection_can_hide_prior_patch_rationale_without_data_loss() -> None:
    record = _completed_record("EAS")
    builder = ContextBuilder()
    builder.add_working_memory(
        "WORKING MEMORY",
        [record],
        decision_rationale_visible=False,
    )
    compiled = builder.build()
    assert "温度 | 稳定" not in compiled.agent_view
    assert (
        compiled.canonical_ir["WORKING MEMORY"][0]["action"]["proposal"]["rationale"]
        == "温度 | 稳定"
    )
    assert decode_compact_context(compiled.compact_view) == compiled.canonical_ir


def test_completed_observed_context_history_is_clocked_and_lossless() -> None:
    record = _completed_record("EAS")
    record["context"].update(
        {
            "abs_pmv_score_limit": 0.5,
            "observed_context_history": {
                "outdoor_temperature_c": [30.0, 30.2, 30.4, 30.6],
                "solar_irradiance_w_m2": [500.0, 520.0, 540.0, 560.0],
                "electricity_price": [0.1, 0.11, 0.12, 0.13],
                "temp_rise_to_warm_pmv_edge_c": [0.8, 0.7, 0.6, 0.5],
                "temp_drop_to_cool_pmv_edge_c": [2.0, 2.1, 2.2, 2.3],
            },
        }
    )
    builder = ContextBuilder()
    builder.add_working_memory(
        "COMPLETED CONTROL INTERVAL",
        [record],
        reference_hour=10,
        reference_time_seconds=14 * 3600,
        presentation="completed_interval",
    )
    compiled = builder.build()
    assert decode_compact_context(compiled.compact_view) == compiled.canonical_ir
    assert "OBSERVED CONTEXT HISTORY" in compiled.agent_view
    for time in ("14:00", "14:15", "14:30", "14:45"):
        assert time in compiled.agent_view
    for field in (
        "outdoor_temperature_c",
        "solar_irradiance_w_m2",
        "electricity_price",
        "EAS.temp_rise_to_warm_pmv_edge_c",
        "EAS.temp_drop_to_cool_pmv_edge_c",
    ):
        assert field in compiled.agent_view
