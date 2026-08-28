from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from h3c.experiments.profiles import load_profile
from h3c.runtime.protocol import control_input
from h3c_baselines.controllers.drl import FrozenDrlController
from h3c_baselines.models import model_entry
from h3c_baselines.policies.normalization import symmetric_minmax
from h3c_baselines.policies.observation_contracts import PolicyObservationBuilder


def _state(profile: dict[str, object]) -> dict[str, float]:
    zones = profile["zones"]
    global_inputs = profile["global_inputs"]
    assert isinstance(zones, dict) and isinstance(global_inputs, dict)
    state = {"time": float(int(profile["evaluation_start_day"]) * 86400)}
    for index, zone in enumerate(zones.values()):
        assert isinstance(zone, dict)
        state[str(zone["temperature_sensor"])] = 297.15 + index * 0.1
    for point in global_inputs["power_meters"]:
        state[str(point)] = 100.0
    return state


def _forecast(profile: dict[str, object], length: int = 10) -> dict[str, list[float]]:
    zones = profile["zones"]
    global_inputs = profile["global_inputs"]
    assert isinstance(zones, dict) and isinstance(global_inputs, dict)
    values = {
        str(global_inputs["outdoor_temperature"]): [293.15 + index for index in range(length)],
        str(global_inputs["solar_irradiance"]): [100.0 + index for index in range(length)],
        str(global_inputs["electricity_price"]): [0.1] * length,
    }
    for zone in zones.values():
        assert isinstance(zone, dict)
        values[str(zone["occupancy_forecast"])] = [1.0] * length
    return values


def _golden_forecast(profile: dict[str, object], length: int = 101) -> dict[str, list[float]]:
    zones = profile["zones"]
    global_inputs = profile["global_inputs"]
    assert isinstance(zones, dict) and isinstance(global_inputs, dict)
    values = {
        str(global_inputs["outdoor_temperature"]): [
            293.15 + index * 0.05 for index in range(length)
        ],
        str(global_inputs["solar_irradiance"]): [100.0 + index for index in range(length)],
        str(global_inputs["electricity_price"]): [0.1 + index * 0.0001 for index in range(length)],
    }
    for index, zone in enumerate(zones.values()):
        assert isinstance(zone, dict)
        values[str(zone["occupancy_forecast"])] = [float(index + 1)] * length
    return values


def _identity(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def test_legacy_normalization_does_not_clip() -> None:
    result = symmetric_minmax(
        np.asarray([-1.0, 3.0, np.nan]),
        np.asarray([0.0, 0.0, 0.0]),
        np.asarray([1.0, 1.0, 1.0]),
    )
    assert result.tolist() == [-3.0, 5.0, -1.0]


def test_all_policy_observation_dimensions_and_local_slices() -> None:
    for case, controller in (
        ("SZ_Air", "c-drl"),
        ("MZ_Hydro", "c-drl"),
        ("MZ_Hydro", "h-drl"),
        ("MZ_Air", "c-drl"),
        ("MZ_Air", "h-drl"),
    ):
        profile = load_profile(case)
        entry = model_entry(case, controller)
        builder = PolicyObservationBuilder(profile, entry)
        builder.reset(_state(profile))
        packet = builder.build(
            _forecast(profile),
            step=0,
            action_time_seconds=int(profile["evaluation_start_day"]) * 86400,
            step_seconds=900,
        )
        assert packet.raw.shape == (entry["observation_dimension"],)
        assert packet.normalized.shape == packet.raw.shape
        if controller == "h-drl":
            assert set(packet.local_normalized) == set(entry["policy_zone_order"])
            assert all(
                value.shape == (entry["local_observation_dimension"],)
                for value in packet.local_normalized.values()
            )


def test_mz_air_policy_order_is_independent_of_profile_order() -> None:
    profile = load_profile("MZ_Air")
    entry = model_entry("MZ_Air", "c-drl")
    assert list(profile["zones"]) == ["cor", "eas", "nor", "sou", "wes"]
    assert entry["policy_zone_order"] == ["cor", "nor", "sou", "eas", "wes"]


def test_frozen_policy_inference_matches_migrated_golden_contract() -> None:
    source = Path("tests/fixtures/baseline_policy_inference_golden.json")
    golden = json.loads(source.read_text(encoding="utf-8"))["fixtures"]
    for fixture in golden.values():
        case = fixture["case"]
        controller = fixture["controller"]
        profile = load_profile(case)
        entry = model_entry(case, controller)
        builder = PolicyObservationBuilder(profile, entry)
        builder.reset(_state(profile))
        packet = builder.build(
            _golden_forecast(profile),
            step=0,
            action_time_seconds=int(profile["evaluation_start_day"]) * 86400,
            step_seconds=900,
        )
        occupancy = dict.fromkeys(profile["zones"], 1.0)
        setpoints, diagnostics = FrozenDrlController(case, controller).decide(packet, occupancy)
        assert entry["sha256"] == fixture["model_sha256"]
        assert _identity(list(packet.columns)) == fixture["columns_sha256"]
        assert _identity(packet.raw.tolist()) == fixture["raw_sha256"]
        assert _identity(packet.normalized.tolist()) == fixture["normalized_sha256"]
        assert {
            zone: _identity(value.tolist()) for zone, value in packet.local_normalized.items()
        } == fixture["local_normalized_sha256"]
        assert diagnostics["raw_action"] == fixture["raw_action"]
        assert setpoints == fixture["setpoints_c"]
        assert control_input(profile, setpoints) == fixture["boptest_payload"]
