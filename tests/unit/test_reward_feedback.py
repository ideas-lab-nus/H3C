from __future__ import annotations

import math

from h3c.runtime.comfort import COMFORT_BAND, step_reward, step_reward_breakdown


def _legacy_reward(
    *,
    cost: float,
    pmv: list[float],
    occupancy: list[float],
    setpoints_c: list[float],
    previous_setpoints_c: list[float],
    objective: dict[str, float],
) -> float:
    zone_count = len(pmv)
    comfort_penalty = sum(
        max(0.0, abs(float(value)) - COMFORT_BAND) ** 2
        for value, count in zip(pmv, occupancy, strict=True)
        if float(count) > 0
    )
    smoothness = sum(
        abs(float(current) - float(previous))
        for current, previous in zip(setpoints_c, previous_setpoints_c, strict=True)
    )
    return -(
        float(objective["energy_weight"])
        * float(objective["energy_scale"])
        * float(cost)
        / zone_count
        + float(objective["comfort_weight"])
        * float(objective["comfort_scale"])
        * comfort_penalty
        / zone_count
        + float(objective["smoothness_weight"])
        * float(objective["smoothness_scale"])
        * smoothness
        / zone_count
    )


def test_reward_breakdown_preserves_frozen_reward_bit_for_bit() -> None:
    values = {
        "cost": 0.173019,
        "pmv": [0.73, -0.41, 0.62],
        "occupancy": [2.0, 0.0, 1.0],
        "setpoints_c": [24.7, 25.3, 23.9],
        "previous_setpoints_c": [25.0, 25.0, 24.5],
        "objective": {
            "energy_weight": 1.17,
            "energy_scale": 987.3,
            "comfort_weight": 2.03,
            "comfort_scale": 77.7,
            "smoothness_weight": 0.41,
            "smoothness_scale": 1.91,
        },
    }
    expected = _legacy_reward(**values)
    actual = step_reward(**values)
    breakdown = step_reward_breakdown(**values, zone_names=("A", "B", "C"))
    assert actual.hex() == expected.hex()
    assert float(breakdown["reward"]).hex() == expected.hex()
    assert math.isclose(
        -float(breakdown["reward"]),
        float(breakdown["site_energy_penalty"])
        + float(breakdown["site_comfort_penalty"])
        + float(breakdown["site_smoothness_penalty"]),
        rel_tol=0.0,
        abs_tol=0.0,
    )
    assert set(breakdown["zone_comfort_penalty_contributions"]) == {"A", "B", "C"}
    assert breakdown["zone_comfort_penalty_contributions"]["B"] == 0.0
