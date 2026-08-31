from __future__ import annotations

import copy

import pytest

from h3c.memory.caol import (
    active_experiences,
    apply_memory_operations,
    attach_hourly_lessons,
    build_hourly_cao,
    classify_regime,
    empty_regime_store,
    reflector_slot_view,
    resolve_reflector_payload,
    select_caol_working_memory,
    validate_memory_refs,
)


def _observation(current: float, previous: float, ahead: list[float]) -> dict[str, object]:
    return {
        "current_occupancy": current,
        "last_occupancy": previous,
        "occupancy_next_steps": ahead,
        "zone_temperature_c": 24.0,
        "last_pmv": 0.1,
        "last_setpoint": 25.0,
    }


@pytest.mark.parametrize(
    ("observation", "expected"),
    (
        (_observation(0, 0, [0, 0, 0, 0]), "unoccupied"),
        (_observation(0, 0, [0, 0, 0, 1]), "occupancy_transition"),
        (_observation(1, 0, [1, 1, 1, 1]), "occupancy_transition"),
        (_observation(1, 1, [1, 1, 1, 1]), "steady_state_occupancy"),
    ),
)
def test_regime_owner_uses_current_previous_and_visible_four_steps(
    observation: dict[str, object], expected: str
) -> None:
    assert classify_regime(observation) == expected


def _hour_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    occupancies = (
        _observation(0, 0, [0, 0, 1, 1]),
        _observation(0, 0, [0, 1, 1, 1]),
        _observation(1, 0, [1, 1, 1, 1]),
        _observation(1, 1, [1, 1, 1, 1]),
    )
    for step, observation in enumerate(occupancies):
        setpoint = (26.0, 25.5, 25.0, 25.5)[step]
        rows.append(
            {
                "hour": 0,
                "step": step,
                "zone": "EAS",
                "observation": observation,
                "interpreter": {"residual": setpoint - 25.0, "matched_rule": "rule"},
                "action_assurance": {
                    "actuator_bounds_triggered": False,
                    "setpoint_rate_limit_triggered": False,
                    "comfort_recovery_triggered": False,
                },
                "final_setpoint_c": setpoint,
                "outcome": {
                    "zone_temperature_c": 24.0 + step / 10,
                    "pmv": (0.0, 0.0, 0.6, 0.4)[step],
                    "effective_occupancy": (0.0, 0.0, 1.0, 1.0)[step],
                    "power_w": 1000.0,
                    "cost": 0.1,
                },
            }
        )
    return rows


def test_cao_is_deterministic_and_lesson_is_a_separate_attachment() -> None:
    decision = {
        "status": "accepted",
        "patch": {"op": "no_change", "rationale": "observed balance"},
        "completed_validation_stages": ["program_check"],
        "program_version_before": 2,
        "current_program_version": 2,
        "rejection": None,
    }
    cao = build_hourly_cao(
        hour=0,
        zone="EAS",
        step_rows=_hour_rows(),
        program_decision=decision,
    )
    assert set(cao) == {"hour", "zone", "context", "action", "outcome"}
    assert cao["context"]["regime_step_coverage"] == {
        "occupancy_transition": [0, 1, 2],
        "steady_state_occupancy": [3],
    }
    assert cao["outcome"]["site_energy_kwh"] == 1.0
    assert cao["outcome"]["discomfort_zone_hours"] == 0.25
    assert cao["outcome"]["setpoint_direction_reversals"] == 1
    attached = attach_hourly_lessons([cao], {"EAS": "The zone retained heat after cooling."})
    assert attached[0]["lesson"] == "The zone retained heat after cooling."
    assert "lesson" not in cao


def test_caol_is_the_exact_k_hour_working_memory() -> None:
    records = [
        {"hour": hour, "zone": zone, "context": {}, "action": {}, "outcome": {}}
        for hour in range(3)
        for zone in ("EAS", "NOR")
    ]
    assert [
        row["hour"]
        for row in select_caol_working_memory(
            records,
            current_hour=3,
            zone="EAS",
            working_memory_hours=1,
            zones=("EAS", "NOR"),
        )
    ] == [2]
    building = select_caol_working_memory(
        records,
        current_hour=3,
        zone=None,
        working_memory_hours=2,
        zones=("EAS", "NOR"),
    )
    assert [(row["hour"], row["zone"]) for row in building] == [
        (1, "EAS"),
        (1, "NOR"),
        (2, "EAS"),
        (2, "NOR"),
    ]


def test_reflector_off_contract_has_only_lessons() -> None:
    resolution = resolve_reflector_payload(
        {"hourly_lessons": [{"zone": "EAS", "lesson": "Thermal response was slow."}]},
        zones=("EAS",),
        long_term_memory=False,
    )
    assert resolution.clean
    assert resolution.operations == {}
    with pytest.raises(ValueError, match="root contract"):
        resolve_reflector_payload(
            {
                "hourly_lessons": [{"zone": "EAS", "lesson": "Thermal response was slow."}],
                "memory_operations": [{"zone": "EAS", "op": "no_change"}],
            },
            zones=("EAS",),
            long_term_memory=False,
        )


def test_three_slot_crud_is_cas_protected_and_auditable() -> None:
    zones = ("EAS",)
    store = empty_regime_store(zones)
    assert reflector_slot_view(
        store, "EAS", ["occupancy_transition", "steady_state_occupancy"]
    ) == [
        {"regime": "occupancy_transition", "state": "empty"},
        {"regime": "steady_state_occupancy", "state": "empty"},
    ]
    add = {
        "EAS": {
            "zone": "EAS",
            "op": "add",
            "regime": "steady_state_occupancy",
            "experience": "The zone responds gradually under sustained occupancy.",
        }
    }
    store, audits = apply_memory_operations(
        store,
        add,
        zones=zones,
        hour=0,
        observed_regimes={"EAS": ["steady_state_occupancy"]},
    )
    assert audits[0]["status"] == "accepted"
    assert active_experiences(store, "EAS") == [
        {
            "regime": "steady_state_occupancy",
            "revision": 1,
            "experience": "The zone responds gradually under sustained occupancy.",
        }
    ]
    stale = copy.deepcopy(store)
    store, audits = apply_memory_operations(
        store,
        {
            "EAS": {
                "zone": "EAS",
                "op": "replace",
                "regime": "steady_state_occupancy",
                "expected_revision": 2,
                "experience": "A revised experience.",
            }
        },
        zones=zones,
        hour=1,
        observed_regimes={"EAS": ["steady_state_occupancy"]},
    )
    assert store == stale
    assert audits[0]["rejection_code"] == "revision_conflict"


def test_memory_refs_are_audit_only_and_must_match_exposed_regime_revision() -> None:
    exposed = [
        {
            "regime": "unoccupied",
            "revision": 2,
            "experience": "The zone releases stored heat slowly while empty.",
        }
    ]
    valid, invalid = validate_memory_refs(
        [
            {"regime": "unoccupied", "revision": 2},
            {"regime": "unoccupied", "revision": 1},
        ],
        exposed,
    )
    assert valid == [{"regime": "unoccupied", "revision": 2}]
    assert invalid == [{"regime": "unoccupied", "revision": 1}]
