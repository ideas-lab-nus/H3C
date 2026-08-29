from __future__ import annotations

from copy import deepcopy
from typing import Any

from h3c.control.program import load_program
from h3c.control.program_execution import execute_zone_programs
from h3c.experiments.profiles import load_profile, repository_root
from h3c.runtime.engine import _hour_observations
from h3c_baselines.controllers.basic_rbc import basic_rbc_setpoints
from h3c_baselines.controllers.enhanced_rbc import EnhancedRbcController


def test_basic_rbc_uses_only_effective_occupancy() -> None:
    assert basic_rbc_setpoints(("a", "b"), {"a": 1.0, "b": 0.0}) == {
        "a": 25.0,
        "b": 30.0,
    }


def test_enhanced_rbc_reuses_canonical_program_and_action_assurance() -> None:
    profile = load_profile("SZ_Air")
    controller = EnhancedRbcController(
        tuple(profile["zones"]), repository_root() / profile["program"]
    )
    setpoints, diagnostics = controller.decide(
        occupancy={"zone1": 1.0},
        future_occupancy={"zone1": [1.0] * 4},
        last_setpoints_c={"zone1": 25.0},
        last_pmv={"zone1": 0.6},
        last_occupancy={"zone1": 1.0},
    )
    assert setpoints == {"zone1": 24.7}
    assert diagnostics["zone1"]["interpreter"]["matched_rule"] == "pmv_lower"
    assert diagnostics["zone1"]["action_assurance"]["final_setpoint"] == 24.7


def test_enhanced_rbc_matches_shared_program_execution_owner_field_by_field() -> None:
    profile = load_profile("MZ_Hydro")
    zones = tuple(profile["zones"])
    program_path = repository_root() / profile["program"]
    occupancy = {zones[0]: 1.0, zones[1]: 0.0}
    future = {zones[0]: [1.0, 1.0, 0.0, 0.0], zones[1]: [0.0, 0.0, 1.0, 1.0]}
    last_setpoints = {zones[0]: 25.0, zones[1]: 30.0}
    last_pmv = {zones[0]: 0.7, zones[1]: -0.2}
    last_occupancy = {zones[0]: 1.0, zones[1]: 0.0}

    controller = EnhancedRbcController(zones, program_path)
    actual_setpoints, actual_diagnostics = controller.decide(
        occupancy=occupancy,
        future_occupancy=future,
        last_setpoints_c=last_setpoints,
        last_pmv=last_pmv,
        last_occupancy=last_occupancy,
    )

    programs = {zone: load_program(program_path, zone) for zone in zones}
    observations = {
        zone: {
            "current_occupancy": occupancy[zone],
            "occ_ahead": future[zone],
            "last_setpoint": last_setpoints[zone],
            "last_pmv": last_pmv[zone],
            "last_occupancy": last_occupancy[zone],
        }
        for zone in zones
    }
    proposals, expected_setpoints, audits = execute_zone_programs(programs, observations)
    assert actual_setpoints == expected_setpoints
    assert actual_diagnostics == {
        zone: {"interpreter": proposals[zone], "action_assurance": audits[zone]} for zone in zones
    }


def test_h3c_and_enhanced_rbc_project_identical_program_observations(
    monkeypatch: Any,
) -> None:
    profile = load_profile("MZ_Hydro")
    zones = tuple(profile["zones"])
    start = int(profile["evaluation_start_day"]) * 86400
    forecast = {
        profile["global_inputs"]["outdoor_temperature"]: [293.15] * 5,
        profile["global_inputs"]["solar_irradiance"]: [100.0] * 5,
        profile["global_inputs"]["electricity_price"]: [0.1] * 5,
        profile["zones"][zones[0]]["occupancy_forecast"]: [1.0, 1.0, 1.0, 0.0, 0.0],
        profile["zones"][zones[1]]["occupancy_forecast"]: [0.0, 0.0, 1.0, 1.0, 1.0],
    }
    state = {
        "time": start,
        profile["zones"][zones[0]]["temperature_sensor"]: 298.15,
        profile["zones"][zones[1]]["temperature_sensor"]: 299.15,
    }
    last_setpoints = {zones[0]: 25.0, zones[1]: 30.0}
    last_pmv = {zones[0]: 0.7, zones[1]: -0.2}
    last_occupancy = {zones[0]: 1.0, zones[1]: 0.0}
    h3c_observations, _, current, _ = _hour_observations(
        profile=profile,
        forecast=forecast,
        step=0,
        time_seconds=start,
        state=state,
        last_setpoint=last_setpoints,
        last_pmv=last_pmv,
        last_occupancy=last_occupancy,
        pmv_of_temperature=lambda temperature: (temperature - 25.0) / 5.0,
    )

    captured: dict[str, dict[str, Any]] = {}

    def capture_execution(
        programs: dict[str, dict[str, Any]], observations: dict[str, dict[str, Any]]
    ) -> tuple[dict[str, dict[str, Any]], dict[str, float], dict[str, dict[str, Any]]]:
        captured.update(deepcopy(observations))
        return execute_zone_programs(programs, observations)

    monkeypatch.setattr(
        "h3c_baselines.controllers.enhanced_rbc.execute_zone_programs", capture_execution
    )
    controller = EnhancedRbcController(zones, repository_root() / profile["program"])
    setpoints, diagnostics = controller.decide(
        occupancy=current,
        future_occupancy={zone: h3c_observations[zone]["occ_ahead"] for zone in zones},
        last_setpoints_c=last_setpoints,
        last_pmv=last_pmv,
        last_occupancy=last_occupancy,
    )
    program_keys = {
        "current_occupancy",
        "occ_ahead",
        "last_setpoint",
        "last_pmv",
        "last_occupancy",
    }
    assert captured == {
        zone: {key: value for key, value in h3c_observations[zone].items() if key in program_keys}
        for zone in zones
    }
    programs = {zone: load_program(repository_root() / profile["program"], zone) for zone in zones}
    proposals, expected_setpoints, audits = execute_zone_programs(programs, h3c_observations)
    assert setpoints == expected_setpoints
    assert diagnostics == {
        zone: {"interpreter": proposals[zone], "action_assurance": audits[zone]} for zone in zones
    }
