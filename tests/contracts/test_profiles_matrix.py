from __future__ import annotations

from h3c.experiments.matrix import plan_release_smoke, plan_suite
from h3c.experiments.profiles import profiles


def test_three_profiles_are_complete_and_configuration_owned() -> None:
    loaded = profiles()
    assert set(loaded) == {"SZ_Air", "MZ_Hydro", "MZ_Air"}
    assert [len(loaded[name]["zones"]) for name in ("SZ_Air", "MZ_Hydro", "MZ_Air")] == [
        1,
        2,
        5,
    ]
    expected_formal_days = {"SZ_Air": 7, "MZ_Hydro": 7, "MZ_Air": 7}
    for name, profile in loaded.items():
        assert profile["protocol"] == {
            "server_warmup_days": 7,
            "vanilla_conditioning_days": 7,
            "formal_evaluation_days": expected_formal_days[name],
            "occupied_vanilla_setpoint_c": 25.0,
            "unoccupied_vanilla_setpoint_c": 30.0,
        }


def test_all_matrix_deduplicates_main_and_one_hour_memory_identity() -> None:
    loaded = profiles()
    main_agents = [plan for plan in plan_suite("main") if plan.controller == "h3c_agent"]
    memory_one = [plan for plan in plan_suite("memory") if plan.working_memory_hours == 1]
    assert {plan.profile: plan.identity(loaded[plan.profile]) for plan in main_agents} == {
        plan.profile: plan.identity(loaded[plan.profile]) for plan in memory_one
    }

    matrix = plan_suite("all")
    assert sum(plan.controller == "deterministic_baseline" for plan in matrix) == 3
    assert sum(plan.controller == "h3c_agent" for plan in matrix) == 24
    identities = [plan.identity(loaded[plan.profile]) for plan in matrix]
    assert len(identities) == len(set(identities)) == 27
    assert all(
        plan.evaluation_hours
        == int(loaded[plan.profile]["protocol"]["formal_evaluation_days"]) * 24
        for plan in matrix
    )
    assert (
        sum(plan.expected_agent_calls(len(loaded[plan.profile]["zones"])) for plan in matrix)
        == 18312
    )

    graph_plans = plan_suite("graph-sensitivity")
    timing_kinds = {
        plan.profile: plan.graph_mutation["kind"]
        for plan in graph_plans
        if plan.graph_mutation is not None and plan.graph_mutation["kind"] != "remove_edge"
    }
    assert timing_kinds == {
        "SZ_Air": "change_immediate_to_delayed",
        "MZ_Hydro": "change_delayed_to_immediate",
        "MZ_Air": "change_immediate_to_delayed",
    }


def test_release_smoke_has_registered_runs_and_call_budget() -> None:
    loaded = profiles()
    matrix = plan_release_smoke()
    assert len(matrix) == 13
    assert sum(plan.controller == "deterministic_baseline" for plan in matrix) == 3
    assert sum(plan.controller == "h3c_agent" for plan in matrix) == 10
    assert (
        sum(plan.expected_agent_calls(len(loaded[plan.profile]["zones"])) for plan in matrix) == 372
    )
