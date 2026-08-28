from __future__ import annotations

import pytest

from h3c.experiments.profiles import load_profile
from h3c.memory.working import select_completed_frames
from h3c.runtime.occupancy import (
    documented_occupancy_active,
    effective_count,
    hourly_route,
    resolve_missing_occupancy_values,
)
from h3c.runtime.protocol import (
    forecast_points,
    resolve_forecast_missing_occupancy,
    site_power,
)
from h3c.runtime.weather import weather_condition_inputs, weather_view


@pytest.mark.parametrize("hours", [1, 2, 3])
def test_working_memory_uses_exact_completed_hour_window(hours: int) -> None:
    frames = [
        {"hour": hour, "zone": "zone1", "complete": True, "cost": hour + 0.123456}
        for hour in range(6)
    ]
    selected = select_completed_frames(
        frames, current_hour=6, zone="zone1", working_memory_hours=hours
    )
    assert [frame["hour"] for frame in selected] == list(range(6 - hours, 6))
    assert all(frame["hour"] < 6 for frame in selected)


def test_incomplete_working_memory_window_is_omitted() -> None:
    frames = [{"hour": 5, "zone": "zone1", "complete": False}]
    assert (
        select_completed_frames(frames, current_hour=6, zone="zone1", working_memory_hours=1) == []
    )


def test_weather_view_matches_registered_four_step_summary() -> None:
    view = weather_view(
        [293.15, 293.65, 294.15, 294.65, 295.15],
        [0.0, 100.0, 200.0, 300.0, 400.0],
    )
    assert view["outdoor_temp_change_next_1h_c"] == 2.0
    assert view["solar_irr_max_next_1h_w_m2"] == 400.0
    assert view["solar_irr_mean_next_1h_w_m2"] == 250.0
    assert len(view["weather_next_steps"]) == 4
    assert weather_condition_inputs(view) == {
        "outdoor_temp_change_next_1h_c": 2.0,
        "solar_irr_max_next_1h_w_m2": 400.0,
        "solar_irr_mean_next_1h_w_m2": 250.0,
    }


def test_official_occupancy_window_and_route() -> None:
    policy = {
        "mode": "official_hvac_window",
        "window_start_minute": 360,
        "window_end_minute": 1140,
        "interval": "half_open",
        "source": "case documentation",
    }
    assert effective_count(policy, 6 * 3600, 3.0) == 3.0
    assert effective_count(policy, 19 * 3600, 3.0) == 0.0
    route = hourly_route(6, {"zone1": 0.0}, {"zone1": 3.0})
    assert route["thinking_mode"] == "low"
    assert route["route_triggers"] == ["forecast_occupancy"]


@pytest.mark.parametrize(
    ("time_seconds", "documented_occupied", "preceding", "expected"),
    [
        (18429300, True, 50.0, 50.0),
        (19031400, False, 25.0, 0.0),
        (19163700, False, 25.0, 0.0),
        (19377000, False, 25.0, 0.0),
        (19597500, False, 25.0, 0.0),
    ],
)
def test_hydronic_missing_occupancy_uses_documented_calendar(
    time_seconds: int,
    documented_occupied: bool,
    preceding: float,
    expected: float,
) -> None:
    policy = load_profile("MZ_Hydro")["occupancy"]
    assert documented_occupancy_active(policy, time_seconds) is documented_occupied
    values, events = resolve_missing_occupancy_values(
        policy,
        [preceding, None],
        start_time_seconds=time_seconds - 900,
        step_seconds=900,
    )
    assert values == [preceding, expected]
    assert len(events) == 1
    assert events[0]["time_seconds"] == time_seconds
    assert events[0]["documented_occupied"] is documented_occupied
    assert events[0]["resolved_value"] == expected


def test_missing_occupancy_fails_without_policy_or_occupied_previous_step() -> None:
    raw_policy = {"mode": "raw_count_positive", "source": "fixture"}
    with pytest.raises(ValueError, match="missing without a policy"):
        resolve_missing_occupancy_values(
            raw_policy,
            [None],
            start_time_seconds=19031400,
            step_seconds=900,
        )
    hydronic_policy = load_profile("MZ_Hydro")["occupancy"]
    with pytest.raises(ValueError, match="no finite previous step"):
        resolve_missing_occupancy_values(
            hydronic_policy,
            [None],
            start_time_seconds=18429300,
            step_seconds=900,
        )


def test_missing_nonoccupancy_forecast_field_remains_fail_closed() -> None:
    profile = load_profile("MZ_Hydro")
    points = forecast_points(profile)
    forecast: dict[str, list[float | None]] = {point: [1.0, 1.0] for point in points}
    forecast[profile["global_inputs"]["outdoor_temperature"]][1] = None
    with pytest.raises(ValueError, match="TDryBul at index 1 is not a finite number"):
        resolve_forecast_missing_occupancy(
            profile,
            forecast,
            points,
            2,
            forecast_phase="evaluation",
            start_time_seconds=19008000,
            step_seconds=900,
        )


@pytest.mark.parametrize("invalid", [True, "0", float("nan"), float("inf"), float("-inf")])
def test_power_meter_invalid_values_fail_closed(invalid: object) -> None:
    profile = load_profile("SZ_Air")
    meters = profile["global_inputs"]["power_meters"]
    state: dict[str, object] = {point: 0.0 for point in meters}
    state[meters[0]] = invalid
    with pytest.raises(ValueError, match="power meter"):
        site_power(profile, state)


def test_missing_power_meter_fails_closed() -> None:
    profile = load_profile("SZ_Air")
    meters = profile["global_inputs"]["power_meters"]
    state = {point: 0.0 for point in meters[1:]}
    with pytest.raises(ValueError, match="missing power meter"):
        site_power(profile, state)
