from __future__ import annotations

from h3c.experiments.matrix import RunPlan, plan_suite


def _main(profile: str) -> RunPlan:
    return next(
        plan
        for plan in plan_suite("main")
        if plan.profile == profile and plan.controller == "h3c_agent"
    )


def _differences(left: dict[str, object], right: dict[str, object]) -> set[str]:
    return {key for key in set(left) | set(right) if left.get(key) != right.get(key)}


def test_each_registered_ablation_changes_only_its_declared_factor() -> None:
    for profile in ("SZ_Air", "MZ_Hydro", "MZ_Air"):
        base = _main(profile).method_config()
        memory = [plan for plan in plan_suite("memory") if plan.profile == profile]
        assert _differences(base, memory[0].method_config()) == set()
        assert _differences(base, memory[1].method_config()) == {"working_memory_hours"}
        assert _differences(base, memory[2].method_config()) == {"working_memory_hours"}
        causal = next(plan for plan in plan_suite("causal-ablation") if plan.profile == profile)
        assert _differences(base, causal.method_config()) == {"causal_enabled"}
        coordination = next(
            plan for plan in plan_suite("coordination-ablation") if plan.profile == profile
        )
        assert _differences(base, coordination.method_config()) == {"coordination_enabled"}
        thinking = next(plan for plan in plan_suite("thinking-ablation") if plan.profile == profile)
        assert _differences(base, thinking.method_config()) == {"thinking_policy"}
        graph = [plan for plan in plan_suite("graph-sensitivity") if plan.profile == profile]
        assert len(graph) == 2
        assert all(_differences(base, plan.method_config()) == {"graph_mutation"} for plan in graph)
