from __future__ import annotations

from h3c.experiments.profiles import load_profile, repository_root
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
