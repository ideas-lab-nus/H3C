"""Continuous one-initialize physical conditioning protocol."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from h3c.outputs.artifacts import RunArtifacts
from h3c.runtime.comfort import ComfortModel
from h3c.runtime.occupancy import effective_count, resolve_missing_occupancy_values


class PhysicalClient(Protocol):
    test_id: str | None

    def initialize(
        self, testcase: str, start_time_seconds: int, warmup_period_seconds: int
    ) -> dict[str, Any]: ...

    def forecast(
        self, points: Sequence[str], horizon_seconds: int, interval_seconds: int
    ) -> dict[str, list[float | None]]: ...

    def advance(self, controls: Mapping[str, float]) -> dict[str, Any]: ...

    def stop(self) -> None: ...


@dataclass
class ConditioningResult:
    state: dict[str, Any]
    test_id: str
    last_setpoint_c: dict[str, float]
    last_pmv: dict[str, float]
    last_occupancy: dict[str, float]
    comfort: ComfortModel
    occupancy_missing_value_resolution_count: int
    conditioning_prefix_identity: str
    evaluation_boundary_identity: str


def forecast_points(profile: Mapping[str, Any]) -> list[str]:
    global_inputs = profile["global_inputs"]
    points = [
        global_inputs["outdoor_temperature"],
        global_inputs["solar_irradiance"],
        global_inputs["electricity_price"],
    ]
    for zone in profile["zones"].values():
        point = zone["occupancy_forecast"]
        if point not in points:
            points.append(point)
    return points


def validate_forecast(
    forecast: Mapping[str, Sequence[object]], points: Sequence[str], minimum_length: int
) -> None:
    missing = sorted(set(points) - set(forecast))
    if missing:
        raise ValueError(f"forecast bundle is missing configured points: {missing}")
    for point in points:
        values = forecast[point]
        if len(values) < minimum_length:
            raise ValueError(
                f"forecast point {point} has {len(values)} values; "
                f"at least {minimum_length} are required"
            )
        for index, value in enumerate(values):
            finite = (
                not isinstance(value, bool)
                and isinstance(value, (int, float))
                and math.isfinite(float(value))
            )
            if not finite:
                raise ValueError(f"forecast point {point} at index {index} is not a finite number")


def resolve_forecast_missing_occupancy(
    profile: Mapping[str, Any],
    forecast: Mapping[str, Sequence[float | None]],
    points: Sequence[str],
    minimum_length: int,
    *,
    forecast_phase: str,
    start_time_seconds: int,
    step_seconds: int,
) -> tuple[dict[str, list[float]], list[dict[str, Any]]]:
    missing = sorted(set(points) - set(forecast))
    if missing:
        raise ValueError(f"forecast bundle is missing configured points: {missing}")
    candidate: dict[str, list[object]] = {point: list(forecast[point]) for point in points}
    events: list[dict[str, Any]] = []
    occupancy_points = dict.fromkeys(
        zone["occupancy_forecast"] for zone in profile["zones"].values()
    )
    for point in occupancy_points:
        values, point_events = resolve_missing_occupancy_values(
            profile["occupancy"],
            forecast[point],
            start_time_seconds=start_time_seconds,
            step_seconds=step_seconds,
        )
        resolved_values: list[object] = list(values)
        candidate[point] = resolved_values
        events.extend(
            {
                "phase": "occupancy_forecast_missing_value_resolution",
                "forecast_phase": forecast_phase,
                "point": point,
                **event,
            }
            for event in point_events
        )
    validate_forecast(candidate, points, minimum_length)
    normalized: dict[str, list[float]] = {}
    for point in points:
        normalized[point] = []
        for value in candidate[point]:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"forecast point {point} is not numeric after validation")
            normalized[point].append(float(value))
    return normalized, events


def control_input(profile: Mapping[str, Any], setpoints_c: Mapping[str, float]) -> dict[str, float]:
    zones = profile["zones"]
    if set(setpoints_c) != set(zones):
        raise ValueError("setpoints must cover exactly the configured zones")
    controls = {key: float(value) for key, value in profile["static_controls"].items()}
    for zone, value in setpoints_c.items():
        controls[zones[zone]["cooling_setpoint_actuator"]] = float(value) + 273.15
    return controls


def _time(state: Mapping[str, Any], expected: int) -> int:
    value = state.get("time")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("physical state time is missing")
    if not math.isfinite(float(value)) or int(value) != expected:
        raise ValueError("physical state time diverged from the registered timeline")
    return int(value)


def _power(profile: Mapping[str, Any], state: Mapping[str, Any]) -> float:
    total = 0.0
    for point in profile["global_inputs"]["power_meters"]:
        if point not in state:
            raise ValueError(f"physical state is missing power meter: {point}")
        raw = state[point]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError(f"power meter {point} is not numeric")
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError(f"power meter {point} is non-finite")
        total += value
    return total


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _boundary_evidence(
    state: Mapping[str, Any],
    last_setpoint: Mapping[str, float],
    last_pmv: Mapping[str, float],
    last_occupancy: Mapping[str, float],
    comfort: ComfortModel,
) -> dict[str, Any]:
    return {
        "physical_state": dict(state),
        "last_setpoint_c": dict(last_setpoint),
        "last_pmv": dict(last_pmv),
        "last_occupancy": dict(last_occupancy),
        "clothing_insulation": comfort.clothing_insulation,
    }


def _temperature_c(profile: Mapping[str, Any], state: Mapping[str, Any], zone: str) -> float:
    point = profile["zones"][zone]["temperature_sensor"]
    value = float(state[point]) - 273.15
    if not math.isfinite(value):
        raise ValueError("zone temperature is non-finite")
    return value


def run_conditioning(
    client: PhysicalClient,
    profile: Mapping[str, Any],
    artifacts: RunArtifacts,
    *,
    on_initialized: Callable[[str], None] | None = None,
) -> ConditioningResult:
    step_seconds = int(profile["control_step_seconds"])
    protocol = profile["protocol"]
    evaluation_start = int(profile["evaluation_start_day"]) * 86400
    conditioning_steps = int(protocol["vanilla_conditioning_days"]) * 24 * 4
    conditioning_start = evaluation_start - conditioning_steps * step_seconds
    warmup_seconds = int(protocol["server_warmup_days"]) * 86400
    state = client.initialize(profile["testcase"], conditioning_start, warmup_seconds)
    _time(state, conditioning_start)
    test_id = client.test_id
    if not isinstance(test_id, str) or not test_id:
        raise ValueError("physical initialize did not produce a test id")
    artifacts.append_jsonl(
        "timing.jsonl",
        {
            "phase": "physical_lifecycle",
            "event": "initialized",
            "time_seconds": conditioning_start,
            "test_id": test_id,
        },
    )
    if on_initialized is not None:
        on_initialized(test_id)
    points = forecast_points(profile)
    tail_steps = 96
    source_forecast = client.forecast(
        points, (conditioning_steps + tail_steps) * step_seconds, step_seconds
    )
    forecast, resolution_events = resolve_forecast_missing_occupancy(
        profile,
        source_forecast,
        points,
        conditioning_steps + tail_steps + 1,
        forecast_phase="conditioning",
        start_time_seconds=conditioning_start,
        step_seconds=step_seconds,
    )
    for event in resolution_events:
        artifacts.append_jsonl("timing.jsonl", event)
    zones = tuple(profile["zones"])
    last_setpoint = {zone: 25.0 for zone in zones}
    last_pmv = {zone: 0.0 for zone in zones}
    last_occupancy = {zone: 0.0 for zone in zones}
    comfort = ComfortModel(profile["comfort"])
    outdoor_point = profile["global_inputs"]["outdoor_temperature"]
    price_point = profile["global_inputs"]["electricity_price"]
    frozen_test_id = test_id
    prefix_hash = hashlib.sha256()

    for step in range(conditioning_steps):
        if client.test_id != frozen_test_id:
            raise ValueError("test id changed during physical conditioning")
        action_time = conditioning_start + step * step_seconds
        raw_occupancy = {
            zone: source_forecast[mapping["occupancy_forecast"]][step]
            for zone, mapping in profile["zones"].items()
        }
        resolved_occupancy = {
            zone: float(forecast[mapping["occupancy_forecast"]][step])
            for zone, mapping in profile["zones"].items()
        }
        occupancy = {
            zone: effective_count(profile["occupancy"], action_time, resolved)
            for zone, resolved in resolved_occupancy.items()
        }
        setpoints = {
            zone: (
                float(protocol["occupied_vanilla_setpoint_c"])
                if occupancy[zone] > 0
                else float(protocol["unoccupied_vanilla_setpoint_c"])
            )
            for zone in zones
        }
        next_state = client.advance(control_input(profile, setpoints))
        outcome_time = action_time + step_seconds
        _time(next_state, outcome_time)
        if client.test_id != frozen_test_id:
            raise ValueError("test id changed during physical conditioning")
        daily = forecast[outdoor_point][step : step + 97 : 4]
        comfort.update_clothing(
            action_time, sum(float(value) - 273.15 for value in daily) / len(daily)
        )
        temperatures = {zone: _temperature_c(profile, next_state, zone) for zone in zones}
        last_pmv = {zone: comfort.pmv(temperatures[zone]) for zone in zones}
        last_setpoint = setpoints
        last_occupancy = occupancy
        power = _power(profile, next_state)
        row = {
            "step": step,
            "action_time_seconds": action_time,
            "outcome_time_seconds": outcome_time,
            "test_id": frozen_test_id,
            "raw_occupancy": raw_occupancy,
            "resolved_occupancy": resolved_occupancy,
            "effective_occupancy": occupancy,
            "setpoint_c": setpoints,
            "zone_temperature_c": temperatures,
            "zone_pmv": last_pmv,
            "power_w": power,
            "electricity_price": float(forecast[price_point][step]),
        }
        artifacts.append_jsonl("physical_conditioning.jsonl", row)
        prefix_row = {key: value for key, value in row.items() if key != "test_id"}
        prefix_hash.update(_canonical(prefix_row) + b"\n")
        state = next_state

    _time(state, evaluation_start)
    boundary = _boundary_evidence(state, last_setpoint, last_pmv, last_occupancy, comfort)
    boundary_identity = hashlib.sha256(_canonical(boundary)).hexdigest()
    artifacts.append_jsonl(
        "timing.jsonl",
        {
            "phase": "evaluation_boundary",
            "boundary": boundary,
            "evaluation_boundary_identity": boundary_identity,
            "test_id": frozen_test_id,
        },
    )
    return ConditioningResult(
        state=state,
        test_id=frozen_test_id,
        last_setpoint_c=last_setpoint,
        last_pmv=last_pmv,
        last_occupancy=last_occupancy,
        comfort=comfort,
        occupancy_missing_value_resolution_count=len(resolution_events),
        conditioning_prefix_identity=prefix_hash.hexdigest(),
        evaluation_boundary_identity=boundary_identity,
    )


def site_power(profile: Mapping[str, Any], state: Mapping[str, Any]) -> float:
    return _power(profile, state)


def zone_temperature_c(profile: Mapping[str, Any], state: Mapping[str, Any], zone: str) -> float:
    return _temperature_c(profile, state, zone)


def require_time(state: Mapping[str, Any], expected: int) -> int:
    return _time(state, expected)
