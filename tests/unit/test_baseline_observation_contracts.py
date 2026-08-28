from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from h3c.experiments.profiles import load_profile
from h3c.runtime.comfort import ComfortModel
from h3c.runtime.protocol import control_input
from h3c_baselines.controllers.drl import FrozenDrlController
from h3c_baselines.models import model_entry
from h3c_baselines.policies.mappo_adapter import HierarchicalMappoPolicy
from h3c_baselines.policies.normalization import symmetric_minmax
from h3c_baselines.policies.observation_contracts import ObservationPacket, PolicyObservationBuilder
from h3c_baselines.runtime.runner import (
    _legacy_policy_daily_outdoor_mean_c,
    _legacy_policy_pmv,
)


def _state(profile: dict[str, object]) -> dict[str, float]:
    zones = profile["zones"]
    global_inputs = profile["global_inputs"]
    assert isinstance(zones, dict) and isinstance(global_inputs, dict)
    evaluation_start_day = profile["evaluation_start_day"]
    assert isinstance(evaluation_start_day, int)
    state = {"time": float(evaluation_start_day * 86400)}
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


def _columns(packet: ObservationPacket, prefix: str) -> list[float]:
    return [
        float(packet.raw[index])
        for index, name in enumerate(packet.columns)
        if name.startswith(prefix)
    ]


def _updated_state(profile: dict[str, object], update_index: int) -> dict[str, float]:
    state = _state(profile)
    zones = profile["zones"]
    assert isinstance(zones, dict)
    for zone_index, zone in enumerate(zones.values()):
        assert isinstance(zone, dict)
        state[str(zone["temperature_sensor"])] = (
            299.15 + 2.0 * (update_index - 1) + zone_index * 0.1
        )
    return state


def test_legacy_normalization_does_not_clip() -> None:
    result = symmetric_minmax(
        np.asarray([-1.0, 3.0, np.nan]),
        np.asarray([0.0, 0.0, 0.0]),
        np.asarray([1.0, 1.0, 1.0]),
    )
    assert result.tolist() == [-3.0, 5.0, -1.0]


def test_policy_comfort_uses_96_consecutive_quarter_hour_samples() -> None:
    profile = load_profile("MZ_Air")
    point = str(profile["global_inputs"]["outdoor_temperature"])
    values = [273.15 + index for index in range(200)]
    forecast = {point: values}
    assert _legacy_policy_daily_outdoor_mean_c(profile, forecast, step=0) == pytest.approx(47.5)
    assert _legacy_policy_daily_outdoor_mean_c(profile, forecast, step=96) == pytest.approx(143.5)
    public_hourly_mean = sum(value - 273.15 for value in values[:97:4]) / 25
    assert public_hourly_mean == pytest.approx(48.0)

    with pytest.raises(ValueError, match="lacks 96 consecutive samples"):
        _legacy_policy_daily_outdoor_mean_c(profile, {point: values[:95]}, step=0)


def test_policy_comfort_updates_daily_and_returns_policy_specific_pmv() -> None:
    profile = load_profile("MZ_Air")
    point = str(profile["global_inputs"]["outdoor_temperature"])
    forecast = {point: [283.15] * 96 + [303.15] * 96}
    comfort = ComfortModel(profile["comfort"])
    start = int(profile["evaluation_start_day"]) * 86400
    temperatures = {"cor": 25.0}

    first = _legacy_policy_pmv(comfort, profile, forecast, temperatures, step=0, action_time=start)
    first_clothing = comfort.clothing_insulation
    same_day = _legacy_policy_pmv(
        comfort, profile, forecast, temperatures, step=1, action_time=start + 900
    )
    assert comfort.clothing_insulation == first_clothing
    assert same_day == first

    second = _legacy_policy_pmv(
        comfort, profile, forecast, temperatures, step=96, action_time=start + 86400
    )
    assert comfort.clothing_insulation != first_clothing
    assert second != first


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


@pytest.mark.parametrize(
    ("case", "controller", "expected"),
    [
        ("SZ_Air", "c-drl", [0.0, 1.0]),
        ("MZ_Hydro", "c-drl", [-1.0, 1.0]),
        ("MZ_Hydro", "h-drl", [-1.0, 1.0]),
        ("MZ_Air", "c-drl", [-1.0, 1.0]),
        ("MZ_Air", "h-drl", [-1.0, 1.0]),
    ],
)
def test_policy_specific_midnight_time_normalization_matches_training_owner(
    case: str, controller: str, expected: list[float]
) -> None:
    profile = load_profile(case)
    builder = PolicyObservationBuilder(profile, model_entry(case, controller))
    builder.reset(_state(profile))
    packet = builder.build(
        _golden_forecast(profile),
        step=0,
        action_time_seconds=int(profile["evaluation_start_day"]) * 86400,
        step_seconds=900,
    )
    assert packet.normalized[:2].tolist() == expected


def test_mz_air_mappo_reproduces_archived_evaluator_first_action() -> None:
    """Independent D-drive Visfinal/CSV oracle, not generated by this adapter."""
    shared = [
        *([-1.0] * 4),
        0.4440000057220459,
        0.4386087656021118,
        0.43383172154426575,
        0.42913880944252014,
        0.42399999499320984,
        *([-1.0] * 5),
        *([-0.4174000024795532] * 5),
    ]
    temperature = {
        "cor": 0.0569603256881237,
        "nor": 0.09369752556085587,
        "sou": 0.11005368083715439,
        "eas": 0.10731387883424759,
        "wes": 0.138329416513443,
    }
    local = {
        zone: np.asarray(
            [
                -1.0,
                1.0,
                *shared,
                *([temperature[zone]] * 5),
                0.0,
                0.0,
                *([-0.9599999785423279 if zone == "cor" else -1.0] * 5),
            ],
            dtype=np.float32,
        )
        for zone in ("cor", "nor", "sou", "eas", "wes")
    }
    expected = np.asarray(
        [
            0.421376705169678,
            0.1605930626392364,
            0.8959376215934754,
            0.5124641060829163,
            0.600084662437439,
        ]
    )
    policy = HierarchicalMappoPolicy(model_entry("MZ_Air", "h-drl"))
    actual = policy.predict(local)
    assert actual == pytest.approx(expected, abs=2e-6)

    wrong_time = {zone: values.copy() for zone, values in local.items()}
    for values in wrong_time.values():
        values[0] = 0.0
    assert not np.allclose(policy.predict(wrong_time), expected, atol=1e-3)


def test_mz_air_policy_order_is_independent_of_profile_order() -> None:
    profile = load_profile("MZ_Air")
    entry = model_entry("MZ_Air", "c-drl")
    assert list(profile["zones"]) == ["cor", "eas", "nor", "sou", "wes"]
    assert entry["policy_zone_order"] == ["cor", "nor", "sou", "eas", "wes"]


@pytest.mark.parametrize(
    ("case", "controller", "temperature_sequences", "action_sequences", "power_sequences"),
    [
        (
            "SZ_Air",
            "c-drl",
            [
                [297.15, 297.15, 297.15, 297.15, 297.15],
                [299.15, 297.15, 297.15, 297.15, 297.15],
                [301.15, 299.15, 297.15, 297.15, 297.15],
            ],
            [
                [298.15, 298.15, 298.15, 298.15],
                [298.15, 298.15, 298.15, 298.15],
                [299.15, 298.15, 298.15, 298.15],
            ],
            [[0.0] * 4, [0.0] * 4, [0.25, 0.0, 0.0, 0.0]],
        ),
        (
            "MZ_Hydro",
            "c-drl",
            [
                [297.15, 298.15, 298.15, 298.15, 298.15],
                [299.15, 297.15, 298.15, 298.15, 298.15],
                [301.15, 299.15, 297.15, 298.15, 298.15],
            ],
            [[298.15], [298.15], [299.15]],
            [[0.0] * 4, [0.0] * 4, [0.25, 0.0, 0.0, 0.0]],
        ),
        (
            "MZ_Air",
            "c-drl",
            [
                [297.15, 297.15, 298.15, 298.15, 298.15],
                [299.15, 299.15, 297.15, 298.15, 298.15],
                [301.15, 301.15, 299.15, 297.15, 298.15],
            ],
            [[298.15], [299.15], [300.15]],
            [[0.0] * 4, [0.25, 0.0, 0.0, 0.0], [0.5, 0.25, 0.0, 0.0]],
        ),
        (
            "MZ_Air",
            "h-drl",
            [
                [297.15, 297.15, 297.15, 297.15, 297.15],
                [299.15, 299.15, 297.15, 297.15, 297.15],
                [301.15, 301.15, 299.15, 297.15, 297.15],
            ],
            [[298.15], [299.15], [300.15]],
            [[0.0] * 4, [0.25, 0.0, 0.0, 0.0], [0.5, 0.25, 0.0, 0.0]],
        ),
    ],
)
def test_history_windows_match_the_independent_legacy_owner_contract(
    case: str,
    controller: str,
    temperature_sequences: list[list[float]],
    action_sequences: list[list[float]],
    power_sequences: list[list[float]],
) -> None:
    profile = load_profile(case)
    entry = model_entry(case, controller)
    builder = PolicyObservationBuilder(profile, entry)
    builder.reset(_state(profile))
    zone = str(entry["policy_zone_order"][0])
    forecast = _golden_forecast(profile)
    maximum_power = float(profile["performance"]["maximum_power_w"])
    for index in range(3):
        if index:
            setpoints = {
                candidate: 25.0 + index + zone_index * 0.1
                for zone_index, candidate in enumerate(entry["policy_zone_order"])
            }
            builder.update(
                _updated_state(profile, index),
                setpoints,
                dict.fromkeys(entry["policy_zone_order"], index * 0.1),
                maximum_power * 0.25 * index,
            )
        packet = builder.build(
            forecast,
            step=index,
            action_time_seconds=int(profile["evaluation_start_day"]) * 86400 + index * 900,
            step_seconds=900,
        )
        assert _columns(packet, f"temperature_{zone}") == pytest.approx(
            temperature_sequences[index]
        )
        action_prefix = "action_zone1" if case == "SZ_Air" else "last_action"
        action_values = _columns(packet, action_prefix)
        if case != "SZ_Air":
            action_values = action_values[:1]
        assert action_values == pytest.approx(action_sequences[index])
        assert _columns(packet, "power_norm") == pytest.approx(power_sequences[index])


def test_mz_air_policy_uses_raw_binary_occupancy_at_midnight() -> None:
    profile = load_profile("MZ_Air")
    builder = PolicyObservationBuilder(profile, model_entry("MZ_Air", "c-drl"))
    builder.reset(_state(profile))
    packet = builder.build(
        _golden_forecast(profile),
        step=0,
        action_time_seconds=int(profile["evaluation_start_day"]) * 86400,
        step_seconds=900,
    )
    assert _columns(packet, "occupancy_cor") == [1.0] * 5


@pytest.mark.parametrize("controller", ["c-drl", "h-drl"])
def test_hydro_action_history_uses_the_archived_15_to_35_c_observation_scale(
    controller: str,
) -> None:
    profile = load_profile("MZ_Hydro")
    entry = model_entry("MZ_Hydro", controller)
    builder = PolicyObservationBuilder(profile, entry)
    builder.reset(_state(profile))
    forecast = _golden_forecast(profile)
    start = int(profile["evaluation_start_day"]) * 86400

    expected = ((25.0, 0.0), (25.0, 0.0), (20.0, -0.5), (30.0, 0.5))
    updates = (20.0, 30.0, 25.0)
    for step, (raw_c, normalized) in enumerate(expected):
        packet = builder.build(
            forecast,
            step=step,
            action_time_seconds=start + step * 900,
            step_seconds=900,
        )
        index = packet.columns.index("last_action_0")
        assert packet.raw[index] == pytest.approx(raw_c + 273.15)
        assert packet.normalized[index] == pytest.approx(normalized)
        if step < len(updates):
            builder.update(
                _updated_state(profile, step + 1),
                dict.fromkeys(entry["policy_zone_order"], updates[step]),
                dict.fromkeys(entry["policy_zone_order"], 0.0),
                0.0,
            )


def test_case_specific_mappo_local_layouts_match_legacy_actor_inputs() -> None:
    for case, shared_first in (("MZ_Hydro", False), ("MZ_Air", True)):
        profile = load_profile(case)
        entry = model_entry(case, "h-drl")
        builder = PolicyObservationBuilder(profile, entry)
        builder.reset(_state(profile))
        packet = builder.build(
            _golden_forecast(profile),
            step=0,
            action_time_seconds=int(profile["evaluation_start_day"]) * 86400,
            step_seconds=900,
        )
        indices = {name: index for index, name in enumerate(packet.columns)}
        zone = str(entry["policy_zone_order"][0])
        local = packet.local_normalized[zone]
        temperature = packet.normalized[indices[f"temperature_{zone}_0"]]
        power = packet.normalized[indices["power_norm_0"]]
        assert local[2] == (power if shared_first else temperature)


@pytest.mark.parametrize(
    ("field", "invalid_value", "message"),
    [
        ("temperature_past_offset", 2, "policy history offset is invalid"),
        ("action_past_offset", -1, "policy history offset is invalid"),
        ("power_past_offset", 3, "policy history offset is invalid"),
        ("temperature_missing", "zero", "temperature missing-value rule is invalid"),
        ("occupancy_encoding", "binary_effective", "occupancy encoding is invalid"),
        (
            "action_observation_bounds_k",
            [303.15, 293.15],
            "policy action-observation bounds are invalid",
        ),
        (
            "time_observation_bounds",
            [1.0, -1.0],
            "policy time-observation bounds are invalid",
        ),
    ],
)
def test_policy_contract_rejects_unregistered_history_or_occupancy_semantics(
    field: str, invalid_value: object, message: str
) -> None:
    entry = deepcopy(model_entry("MZ_Air", "c-drl"))
    entry[field] = invalid_value
    with pytest.raises(ValueError, match=message):
        PolicyObservationBuilder(load_profile("MZ_Air"), entry)


def test_policy_contract_rejects_unregistered_mappo_local_layout() -> None:
    entry = deepcopy(model_entry("MZ_Air", "h-drl"))
    entry["local_observation_layout"] = "zone_interleaved"
    with pytest.raises(ValueError, match="local MAPPO observation layout is invalid"):
        PolicyObservationBuilder(load_profile("MZ_Air"), entry)


def test_policy_contract_requires_registered_time_bounds() -> None:
    entry = deepcopy(model_entry("MZ_Air", "h-drl"))
    del entry["time_observation_bounds"]
    with pytest.raises(KeyError, match="time_observation_bounds"):
        PolicyObservationBuilder(load_profile("MZ_Air"), entry)


def test_policy_normalization_uses_legacy_float32_arithmetic() -> None:
    values = np.asarray([299.123456789], dtype=np.float64)
    lower = np.asarray([288.15], dtype=np.float64)
    upper = np.asarray([308.15], dtype=np.float64)
    expected = np.asarray(
        2.0
        * (values.astype(np.float32) - lower.astype(np.float32))
        / (upper.astype(np.float32) - lower.astype(np.float32))
        - 1.0,
        dtype=np.float32,
    )
    float64_then_cast = (2.0 * (values - lower) / (upper - lower) - 1.0).astype(np.float32)

    actual = symmetric_minmax(values, lower, upper)

    assert np.array_equal(actual, expected)
    assert not np.array_equal(actual, float64_then_cast)


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
