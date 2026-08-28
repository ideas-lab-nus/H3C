"""Exact legacy observation contracts for the five frozen policies."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from h3c.runtime.occupancy import effective_count
from h3c.runtime.protocol import zone_temperature_c
from h3c_baselines.policies.normalization import symmetric_minmax


@dataclass(frozen=True)
class ObservationPacket:
    raw: NDArray[np.float64]
    normalized: NDArray[np.float32]
    local_normalized: dict[str, NDArray[np.float32]]
    columns: tuple[str, ...]


def _axis(values: Sequence[float], bound: tuple[float, float]) -> tuple[list[float], list[float]]:
    return [bound[0]] * len(values), [bound[1]] * len(values)


class PolicyObservationBuilder:
    """Stateful observation builder; state is reset at the formal evaluation boundary."""

    def __init__(self, profile: Mapping[str, Any], model: Mapping[str, Any]) -> None:
        self.profile = profile
        self.zone_order = tuple(str(zone) for zone in model["policy_zone_order"])
        if set(self.zone_order) != set(profile["zones"]):
            raise ValueError("policy zone order does not cover the profile zones")
        self.expected_dimension = int(model["observation_dimension"])
        self.local_dimension = int(model.get("local_observation_dimension", 0))
        self.action_history_steps = int(model["action_history_steps"])
        self.cold_start_action_c = float(model["cold_start_action_c"])
        self.occupancy_encoding = str(model["occupancy_encoding"])
        if self.occupancy_encoding not in {"effective_count", "binary_effective"}:
            raise ValueError("policy occupancy encoding is invalid")
        self.occupancy_upper = float(model["occupancy_upper"])
        self.temperature_history_k: dict[str, list[float]] = {}
        self.action_history_k: dict[str, list[float]] = {}
        self.power_history: list[float] = []
        self.current_pmv: dict[str, float] = {}
        self._initialized = False

    def reset(self, state: Mapping[str, Any]) -> None:
        self.temperature_history_k = {}
        for zone in self.zone_order:
            current = zone_temperature_c(self.profile, state, zone) + 273.15
            self.temperature_history_k[zone] = [current] * 5
        self.action_history_k = {
            zone: [self.cold_start_action_c + 273.15] * self.action_history_steps
            for zone in self.zone_order
        }
        self.power_history = [0.0] * 4
        self.current_pmv = dict.fromkeys(self.zone_order, 0.0)
        self._initialized = True

    def update(
        self,
        state: Mapping[str, Any],
        setpoints_c: Mapping[str, float],
        pmv: Mapping[str, float],
        power_w: float,
    ) -> None:
        if not self._initialized:
            raise ValueError("policy observation history has not been reset")
        maximum_power = float(self.profile["performance"]["maximum_power_w"])
        for zone in self.zone_order:
            temperature_k = zone_temperature_c(self.profile, state, zone) + 273.15
            self.temperature_history_k[zone] = [
                temperature_k,
                *self.temperature_history_k[zone][:4],
            ]
            self.action_history_k[zone] = [
                float(setpoints_c[zone]) + 273.15,
                *self.action_history_k[zone][:3],
            ][: self.action_history_steps]
            self.current_pmv[zone] = float(pmv[zone])
        self.power_history = [float(power_w) / maximum_power, *self.power_history[:3]]

    def _occupancy_forecasts(
        self,
        forecast: Mapping[str, Sequence[float]],
        *,
        step: int,
        action_time_seconds: int,
        step_seconds: int,
    ) -> dict[str, list[float]]:
        values: dict[str, list[float]] = {}
        for zone in self.zone_order:
            point = self.profile["zones"][zone]["occupancy_forecast"]
            resolved = []
            for horizon in range(5):
                count = effective_count(
                    self.profile["occupancy"],
                    action_time_seconds + horizon * step_seconds,
                    float(forecast[point][step + horizon]),
                )
                resolved.append(
                    1.0
                    if self.occupancy_encoding == "binary_effective" and count > 0
                    else float(count)
                )
            values[zone] = resolved
        return values

    def build(
        self,
        forecast: Mapping[str, Sequence[float]],
        *,
        step: int,
        action_time_seconds: int,
        step_seconds: int,
    ) -> ObservationPacket:
        if not self._initialized:
            raise ValueError("policy observation history has not been reset")
        day_fraction = (action_time_seconds % 86400) / 86400.0
        time_values = [
            math.sin(2.0 * math.pi * day_fraction),
            math.cos(2.0 * math.pi * day_fraction),
        ]
        outdoor = [
            float(value)
            for value in forecast[self.profile["global_inputs"]["outdoor_temperature"]][
                step : step + 5
            ]
        ]
        solar = [
            float(value)
            for value in forecast[self.profile["global_inputs"]["solar_irradiance"]][
                step : step + 5
            ]
        ]
        price = [
            float(value)
            for value in forecast[self.profile["global_inputs"]["electricity_price"]][
                step : step + 5
            ]
        ]
        occupancy = self._occupancy_forecasts(
            forecast,
            step=step,
            action_time_seconds=action_time_seconds,
            step_seconds=step_seconds,
        )
        raw: list[float] = []
        lower: list[float] = []
        upper: list[float] = []
        columns: list[str] = []

        def add(name: str, values: Sequence[float], bound: tuple[float, float]) -> None:
            raw.extend(values)
            lo, hi = _axis(values, bound)
            lower.extend(lo)
            upper.extend(hi)
            columns.extend(
                name if len(values) == 1 else f"{name}_{index}" for index in range(len(values))
            )

        add("time", time_values, (-1.0, 1.0))
        for zone in self.zone_order:
            add(f"temperature_{zone}", self.temperature_history_k[zone], (288.15, 308.15))
        add("pmv", [self.current_pmv[zone] for zone in self.zone_order], (-3.0, 3.0))
        if self.action_history_steps == 4 and len(self.zone_order) == 1:
            add(
                "action_zone1",
                self.action_history_k[self.zone_order[0]],
                (293.15, 303.15),
            )
        elif self.action_history_steps == 1:
            add(
                "last_action",
                [self.action_history_k[zone][0] for zone in self.zone_order],
                (293.15, 303.15),
            )
        else:
            raise ValueError("unsupported policy action-history contract")
        add("power_norm", self.power_history, (0.0, 1.0))
        add("outdoor_temperature", outdoor, (263.15, 313.15))
        add("solar_irradiance", solar, (0.0, 1200.0))
        add("electricity_price", price, (0.0, 0.2))
        for zone in self.zone_order:
            add(f"occupancy_{zone}", occupancy[zone], (0.0, self.occupancy_upper))
        raw_array = np.asarray(raw, dtype=np.float64)
        if raw_array.shape != (self.expected_dimension,):
            raise ValueError(
                f"policy observation dimension is {raw_array.size}, expected {self.expected_dimension}"
            )
        normalized = symmetric_minmax(
            raw_array,
            np.asarray(lower, dtype=np.float64),
            np.asarray(upper, dtype=np.float64),
        )
        local: dict[str, NDArray[np.float32]] = {}
        if self.local_dimension:
            column_index = {name: index for index, name in enumerate(columns)}
            for zone_index, zone in enumerate(self.zone_order):
                local_columns = [
                    "time_0",
                    "time_1",
                    *[f"temperature_{zone}_{index}" for index in range(5)],
                    f"pmv_{zone_index}",
                    f"last_action_{zone_index}",
                    *[f"power_norm_{index}" for index in range(4)],
                    *[f"outdoor_temperature_{index}" for index in range(5)],
                    *[f"solar_irradiance_{index}" for index in range(5)],
                    *[f"electricity_price_{index}" for index in range(5)],
                    *[f"occupancy_{zone}_{index}" for index in range(5)],
                ]
                if len(local_columns) != self.local_dimension:
                    raise ValueError("local MAPPO observation dimension is invalid")
                try:
                    local[zone] = normalized[
                        np.asarray([column_index[name] for name in local_columns], dtype=np.int64)
                    ].copy()
                except KeyError as error:
                    raise ValueError("local MAPPO observation column is missing") from error
        return ObservationPacket(raw_array, normalized, local, tuple(columns))
