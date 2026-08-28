from __future__ import annotations

from typing import Any

import pytest

from h3c.memory.working import (
    FUTURE_WEATHER_FIELDS,
    completed_executor_records,
    completed_summary_frame,
    recent_outcome_summary,
    reflector_results_view,
    select_completed_frames,
    select_executor_records,
)


def _step_rows(hour: int, zone: str = "zone1") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset in range(4):
        step = hour * 4 + offset
        rows.append(
            {
                "hour": hour,
                "step": step,
                "zone": zone,
                "observation": {
                    "current_occupancy": 1.0,
                    "last_occupancy": 1.0,
                    "last_pmv": 0.1 + offset / 100,
                    "last_setpoint": 25.0,
                    "zone_temperature_c": 24.0,
                    "next_hour_occupancy": 1.0,
                    "weather_next_steps": [{"step_ahead": 1, "outdoor_temp_c": 30.0}],
                    "solar_irr_max_next_1h_w_m2": 400.0,
                },
                "interpreter": {
                    "residual": 0.0,
                    "setpoint": 25.0,
                    "base": 25.0,
                    "exempt_rate": False,
                    "matched_rule": "occupied_hold",
                },
                "action_assurance": {
                    "order": [
                        "comfort_recovery",
                        "setpoint_rate_limit",
                        "actuator_bounds",
                    ],
                    "interpreter_setpoint": 25.0,
                    "comfort_recovery_triggered": False,
                    "comfort_recovery_reason": None,
                    "comfort_recovery_input_setpoint": 25.0,
                    "comfort_recovery_output_setpoint": 25.0,
                    "setpoint_rate_limit_triggered": False,
                    "setpoint_rate_limit_delta_before_c": 0.0,
                    "setpoint_rate_limit_output_setpoint": 25.0,
                    "actuator_bounds_triggered": False,
                    "actuator_bound": None,
                    "final_setpoint": 25.0,
                },
                "final_setpoint_c": 25.0,
                "outcome": {
                    "zone_temperature_c": 24.0 + offset / 10,
                    "pmv": 0.1 + offset / 100,
                    "effective_occupancy": 1.0,
                    "power_w": 100.0,
                    "cost": 0.03 + offset / 1000,
                },
            }
        )
    return rows


def _decision(
    hour: int,
    *,
    status: str = "accepted",
    patch: dict[str, Any] | None = None,
    rejection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "hour": hour,
        "step": hour * 4,
        "zone": "zone1",
        "status": status,
        "patch": patch or {"op": "no_change", "rationale": "hold"},
        "current_program_version": hour,
        "current_program_hash": "0" * 64,
        "rejection": rejection,
    }


def _records(hours: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for hour in range(hours):
        result.extend(
            completed_executor_records(
                hour=hour,
                zone="zone1",
                step_rows=_step_rows(hour),
                program_decision=_decision(hour),
            )
        )
    return result


@pytest.mark.parametrize(
    ("current_step", "memory_hours", "expected_steps"),
    [
        (0, 1, []),
        (4, 1, [0, 1, 2, 3]),
        (4, 2, []),
        (8, 1, [4, 5, 6, 7]),
        (8, 2, list(range(8))),
        (8, 3, []),
        (12, 3, list(range(12))),
    ],
)
def test_executor_memory_hour_boundaries_omit_incomplete_windows(
    current_step: int, memory_hours: int, expected_steps: list[int]
) -> None:
    selected = select_executor_records(
        _records(3),
        current_step=current_step,
        zone="zone1",
        working_memory_hours=memory_hours,
    )
    assert [record["time"]["step"] for record in selected] == expected_steps
    summary = recent_outcome_summary(
        _records(3),
        current_step=current_step,
        zone="zone1",
        working_memory_hours=memory_hours,
    )
    assert (summary is None) is (not expected_steps)
    if summary is not None:
        assert summary["covered_steps"] == len(expected_steps)


def test_completed_executor_memory_restores_decision_assurance_and_outcome() -> None:
    rejection = {
        "stage": "energy_budget_validation",
        "code": "energy_budget_exhausted",
        "message": "insufficient allowance",
    }
    records = completed_executor_records(
        hour=0,
        zone="zone1",
        step_rows=_step_rows(0),
        program_decision=_decision(
            0,
            status="rejected",
            patch={
                "op": "set_param",
                "param": "pmv_step_c",
                "to": 0.4,
                "causal_edge_ids": ["ce_12345678"],
                "rationale": "candidate",
            },
            rejection=rejection,
        ),
    )
    first = records[0]
    assert first["proposal"]["op"] == "set_param"
    assert first["validation"]["rejected"] is True
    assert first["validation"]["rejection_code"] == "energy_budget_exhausted"
    assert first["validation"]["shield"] == {
        "branch": "normal",
        "proposed": 25.0,
        "setpoint": 25.0,
        "actuator_limit_applied": False,
        "rate_limit_applied": False,
        "comfort_interlock_applied": False,
    }
    assert first["program"] == {"version": 0}
    assert first["outcome"]["final_setpoint"] == 25.0
    assert first["outcome"]["measured"]["pmv"] == 0.1
    assert records[1]["proposal"] == {"status": "not_called", "program_source_step": 0}


def test_future_weather_is_excluded_from_all_memory_and_reflector_views() -> None:
    rows = _step_rows(0)
    decision = _decision(0)
    records = completed_executor_records(
        hour=0,
        zone="zone1",
        step_rows=rows,
        program_decision={
            **decision,
            "weather_next_steps": [{"outdoor_temp_c": 99.0}],
        },
    )
    frame = completed_summary_frame(
        hour=0,
        zone="zone1",
        step_rows=rows,
        program_decision=decision,
    )
    reflector = reflector_results_view([frame], [decision])
    exposed = {
        "executor": select_executor_records(
            records,
            current_step=4,
            zone="zone1",
            working_memory_hours=1,
        ),
        "reflector": reflector,
        "orchestrator": select_completed_frames(
            [frame],
            current_hour=1,
            zone=None,
            working_memory_hours=1,
            zones=["zone1"],
        ),
    }
    serialized = __import__("json").dumps(exposed, sort_keys=True)
    assert all(field not in serialized for field in FUTURE_WEATHER_FIELDS)
    assert "next_hour_occupancy" in serialized
