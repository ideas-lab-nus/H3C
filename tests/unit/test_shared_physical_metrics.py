from __future__ import annotations

from h3c.outputs.physical_metrics import compute_physical_metrics


def test_shared_physical_metrics_compute_cost_comfort_and_dynamics() -> None:
    performance = [
        {"step_cost": 1.0, "total_power_w": 1000.0, "step_reward": -1.0},
        {"step_cost": 2.0, "total_power_w": 2000.0, "step_reward": -2.0},
    ]
    zones = [
        {
            "zone": "z",
            "step": 0,
            "final_setpoint_c": 25.0,
            "effective_occupancy": 1.0,
            "pmv": 0.6,
        },
        {
            "zone": "z",
            "step": 1,
            "final_setpoint_c": 24.0,
            "effective_occupancy": 1.0,
            "pmv": 0.4,
        },
    ]
    result = compute_physical_metrics(performance, zones)
    assert result["physical"]["total_cost"] == 3.0
    assert result["physical"]["energy_kwh"] == 0.75
    assert result["physical"]["discomfort_zone_hours"] == 0.25
    assert result["setpoint_dynamics"] == {
        "total_variation_c": 1.0,
        "direction_reversals": 0,
        "occupied_comfort_band_crossings": 1,
    }
