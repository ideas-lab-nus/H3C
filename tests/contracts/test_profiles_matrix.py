from __future__ import annotations

from h3c.experiments.matrix import (
    PAPER_AGENT_LABELS,
    _file_sha256,
    graph_mutation,
    paper_agent_plan_items,
    plan_suite,
)
from h3c.experiments.profiles import profiles


def test_public_json_digest_is_independent_of_formatting_and_line_endings(tmp_path) -> None:
    compact = tmp_path / "compact.json"
    formatted = tmp_path / "formatted.json"
    compact.write_bytes(b'{"b":2,"a":[1,3]}\n')
    formatted.write_bytes(b'{\r\n  "a": [1, 3],\r\n  "b": 2\r\n}\r\n')
    assert _file_sha256(compact) == _file_sha256(formatted)


def test_three_profiles_are_complete_and_configuration_owned() -> None:
    loaded = profiles()
    assert set(loaded) == {"SZ_Air", "MZ_Hydro", "MZ_Air"}
    assert [len(loaded[name]["zones"]) for name in ("SZ_Air", "MZ_Hydro", "MZ_Air")] == [
        1,
        2,
        5,
    ]
    expected_formal_days = {"SZ_Air": 7, "MZ_Hydro": 5, "MZ_Air": 7}
    for name, profile in loaded.items():
        assert profile["protocol"] == {
            "initialization_mode": "evaluation_start_internal_warmup",
            "internal_warmup_days": 7,
            "formal_evaluation_days": expected_formal_days[name],
            "initial_setpoint_c": 25.0,
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
        == 16824
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


def test_paper_agent_matrix_matches_the_27_reported_configuration_groups() -> None:
    loaded = profiles()
    matrix = plan_suite("paper-agent")
    named_matrix = paper_agent_plan_items()

    assert len(matrix) == 27
    assert [plan for _, plan in named_matrix] == matrix
    assert [label for label, _ in named_matrix] == list(PAPER_AGENT_LABELS) * 3
    assert all(plan.controller == "h3c_agent" for plan in matrix)
    expected_profiles = ["SZ_Air"] * 9 + ["MZ_Hydro"] * 9 + ["MZ_Air"] * 9
    assert [plan.profile for plan in matrix] == expected_profiles
    assert all(plan.long_term_memory is False for plan in matrix)
    assert all(
        plan.evaluation_hours
        == int(loaded[plan.profile]["protocol"]["formal_evaluation_days"]) * 24
        for plan in matrix
    )
    identities = [plan.identity(loaded[plan.profile]) for plan in matrix]
    assert len(identities) == len(set(identities))

    all_agent_identities = {
        plan.identity(loaded[plan.profile])
        for plan in plan_suite("all")
        if plan.controller == "h3c_agent"
    }
    paper_without_zero_memory = {
        plan.identity(loaded[plan.profile]) for plan in matrix if plan.working_memory_hours != 0
    }
    assert paper_without_zero_memory == all_agent_identities
    assert not any(
        plan.controller == "h3c_agent" and plan.working_memory_hours == 0
        for plan in plan_suite("all")
    )

    for case in ("SZ_Air", "MZ_Hydro", "MZ_Air"):
        case_plans = [plan for plan in matrix if plan.profile == case]
        assert len(case_plans) == 9
        expected_factors = (
            (1, True, True, "occupancy_routed", None),
            (0, True, True, "occupancy_routed", None),
            (2, True, True, "occupancy_routed", None),
            (3, True, True, "occupancy_routed", None),
            (1, False, True, "occupancy_routed", None),
            (1, True, True, "occupancy_routed", graph_mutation("missing_solar_zone_edge")),
            (
                1,
                True,
                True,
                "occupancy_routed",
                graph_mutation(
                    "immediate_solar_zone_edge" if case == "MZ_Hydro" else "delayed_solar_zone_edge"
                ),
            ),
            (1, True, False, "occupancy_routed", None),
            (1, True, True, "all_roles_disabled", None),
        )
        assert [
            (
                plan.working_memory_hours,
                plan.causal_enabled,
                plan.coordination_enabled,
                plan.thinking_policy,
                plan.graph_mutation,
            )
            for plan in case_plans
        ] == list(expected_factors)
        assert case_plans[5].graph_mutation == graph_mutation("missing_solar_zone_edge")
        expected_timing_mutation = (
            "immediate_solar_zone_edge" if case == "MZ_Hydro" else "delayed_solar_zone_edge"
        )
        assert case_plans[6].graph_mutation == graph_mutation(expected_timing_mutation)
        assert case_plans[7].coordination_enabled is False
        assert case_plans[8].thinking_policy == "all_roles_disabled"

        base = case_plans[0].method_config()
        expected_differences = (
            set(),
            {"working_memory_hours"},
            {"working_memory_hours"},
            {"working_memory_hours"},
            {"causal_enabled"},
            {"graph_mutation"},
            {"graph_mutation"},
            {"coordination_enabled"},
            {"thinking_policy"},
        )
        for plan, expected in zip(case_plans, expected_differences, strict=True):
            candidate = plan.method_config()
            differences = {
                key for key in set(base) | set(candidate) if base.get(key) != candidate.get(key)
            }
            assert differences == expected

    assert (
        sum(plan.expected_agent_calls(len(loaded[plan.profile]["zones"])) for plan in matrix)
        == 18984
    )
