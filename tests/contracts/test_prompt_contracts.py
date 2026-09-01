from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest

from h3c.agents.prompts import Language, Role, assert_causal_disabled_text_clean, system_prompt
from h3c.agents.roles import (
    Executor,
    ModelContractError,
    Orchestrator,
    Reflector,
    resolve_executor_memory_model_output,
    resolve_executor_model_output,
    resolve_orchestrator_model_output,
)
from h3c.memory.ledger import ProgramLedger


@pytest.mark.parametrize(
    ("role", "language", "long_term_memory"),
    [
        (role, language, enabled)
        for language in ("en", "zh")
        for role in ("orchestrator", "executor", "reflector")
        for enabled in (False, True)
        if not (role == "orchestrator" and enabled)
    ],
)
def test_canonical_system_prompt_matches_context_golden(
    role: Role,
    language: Language,
    long_term_memory: bool,
    repository_root: Path,
) -> None:
    prompt = system_prompt(
        role,
        language=language,
        long_term_memory=long_term_memory,
    )
    golden = json.loads(
        (repository_root / "tests/fixtures/prompts/caol_prompt_golden.json").read_text(
            encoding="utf-8"
        )
    )
    expected = golden[f"{role}_{'on' if long_term_memory else 'off'}_{language}"]
    assert len(prompt) == expected["length"]
    assert hashlib.sha256(prompt.encode("utf-8")).hexdigest() == expected["sha256"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_rationale_prompt_has_no_length_semantics_and_reflector_uses_lessons(
    language: Language,
) -> None:
    orchestrator = system_prompt("orchestrator", language=language)
    executor = system_prompt("executor", language=language)
    reflector = system_prompt("reflector", language=language)
    assert "240" not in orchestrator + executor
    assert "short rationale" not in (orchestrator + executor).lower()
    assert "short string" not in (orchestrator + executor).lower()
    assert "简短理由" not in orchestrator + executor
    assert (
        ("values nonempty" in orchestrator)
        if language == "en"
        else ("理由不能为空" in orchestrator)
    )
    assert (
        'Root object exactly: {"patch":[{...}]}' in executor
        if language == "en"
        else '根对象必须精确为 {"patch":[{...}]}' in executor
    )
    assert "single-line Lesson" not in reflector and "单行 Lesson" not in reflector


@pytest.mark.parametrize("long_term_memory", [False, True])
def test_executor_prompt_and_parser_share_the_singleton_list_envelope(
    long_term_memory: bool,
) -> None:
    prompt = system_prompt("executor", long_term_memory=long_term_memory)
    assert 'Root object exactly: {"patch":[{...}]}' in prompt

    operation = {"op": "no_change", "rationale": "Keep the current specification."}
    if long_term_memory:
        root = {"patch": [operation], "memory_refs": []}
        patch, _, references = resolve_executor_memory_model_output(
            json.dumps(root), causal_enabled=True
        )
        assert references == []
    else:
        patch, _ = resolve_executor_model_output(
            json.dumps({"patch": [operation]}), causal_enabled=True
        )
    assert patch == operation


@pytest.mark.parametrize(
    "invalid",
    [
        {"op": "no_change", "rationale": "flat operation"},
        {"patch": {"op": "no_change", "rationale": "object not list"}},
        {"patch": []},
        {
            "patch": [
                {"op": "no_change", "rationale": "first"},
                {"op": "no_change", "rationale": "second"},
            ]
        },
    ],
)
def test_executor_parser_rejects_noncanonical_envelopes(invalid: dict[str, Any]) -> None:
    with pytest.raises(ModelContractError):
        resolve_executor_model_output(json.dumps(invalid), causal_enabled=True)


@pytest.mark.parametrize("role", ["orchestrator", "executor", "reflector"])
def test_causal_disabled_system_prompt_has_zero_leakage(role: Role) -> None:
    prompt = system_prompt(role, causal_enabled=False)
    assert_causal_disabled_text_clean(prompt)


def test_orchestrator_dynamic_limits_match_final_w_cooling_projection() -> None:
    user = Orchestrator.build_user(
        hour=0,
        zones=["zoneB", "zoneA"],
        site_state={},
        zone_coupling={},
        causal_edges=None,
        previous_allocation=None,
        previous_utilisation=None,
        working_memory=None,
        allocation_limits={
            "zones": ["zoneB", "zoneA"],
            "site_cap_c": 5.0,
            "per_zone_reserved_cap_c": 3.25,
        },
    )
    assert 'zones: ["zoneB","zoneA"]' in user
    assert "site_cap_c: 5.0" in user
    assert "per_zone_reserved_cap_c: 3.25" in user
    assert "site_cap_max_c" not in user and "priority_contract" not in user

    valid = {
        "site_cap_c": 5.0,
        "zone_budgets_c": {"zoneB": 3.25, "zoneA": 1.75},
        "priority": ["zoneB", "zoneA"],
        "rationale_per_zone": {"zoneB": "first", "zoneA": "second"},
    }
    parsed, _ = resolve_orchestrator_model_output(
        json.dumps(valid),
        ["zoneB", "zoneA"],
        causal_enabled=False,
        expected_site_cap_c=5.0,
        expected_per_zone_reserved_cap_c=3.25,
    )
    assert parsed == valid
    valid["zone_budgets_c"] = {"zoneB": 3.26, "zoneA": 1.74}
    with pytest.raises(ModelContractError, match="zone allocation is outside its bound"):
        resolve_orchestrator_model_output(
            json.dumps(valid),
            ["zoneB", "zoneA"],
            causal_enabled=False,
            expected_site_cap_c=5.0,
            expected_per_zone_reserved_cap_c=3.25,
        )


def test_orchestrator_allocation_limits_have_one_exact_role_builder_owner() -> None:
    with pytest.raises(ValueError, match="exact resolved cooling fields"):
        Orchestrator.build_user(
            hour=0,
            zones=["zone1"],
            site_state={},
            zone_coupling={},
            causal_edges=None,
            previous_allocation=None,
            previous_utilisation=None,
            working_memory=None,
            allocation_limits={"priority_contract": {}},
        )


def test_executor_receives_current_program_but_not_internal_ledger(
    canonical_program: dict[str, Any],
) -> None:
    ledger = ProgramLedger(canonical_program)
    user = Executor.build_user(
        hour=4,
        zone="zone1",
        observation={"last_pmv": 0.2},
        current_executable_program=ledger.prompt_view(),
        causal_edges=[],
        allowance={"remaining_c": 1.0},
        working_memory=None,
    )
    assert "CONTROL SPECIFICATION" in user
    assert oracle_fixture_absent(user)


def oracle_fixture_absent(user: str) -> bool:
    forbidden = ("accepted_updates", "program_hash_before", "version_before")
    return all(token not in user for token in forbidden)


def test_missing_blocks_are_omitted_not_rendered(canonical_program: dict[str, Any]) -> None:
    user = Executor.build_user(
        hour=0,
        zone="zone1",
        observation={"last_pmv": 0.0},
        current_executable_program=ProgramLedger(canonical_program).prompt_view(),
        causal_edges=None,
        allowance=None,
        working_memory=None,
    )
    assert "CONFIRMED CAUSAL EDGES" not in user
    assert "ALLOWANCE" not in user
    assert "WORKING MEMORY" not in user
    assert "ACTIVE LONG-TERM EXPERIENCE SLOTS" not in user
    assert "N/A" not in user and "null" not in user


def test_memory_off_has_zero_long_term_surface_and_on_is_executor_reflector_only() -> None:
    forbidden = ("long-term", "memory_refs", "memory_operations", "expected_revision")
    executor_off = system_prompt("executor")
    reflector_off = system_prompt("reflector")
    assert all(token not in (executor_off + reflector_off) for token in forbidden)

    executor_on = system_prompt("executor", long_term_memory=True)
    reflector_on = system_prompt("reflector", long_term_memory=True)
    orchestrator = system_prompt("orchestrator")
    assert "memory_refs" in executor_on
    assert "memory_operations" in reflector_on
    assert all(token not in orchestrator for token in forbidden)

    completed_hour = [
        {
            "hour": 6,
            "zone": "zone1",
            "context": {
                "regime_step_coverage": {"steady_state_occupancy": [24, 25, 26, 27]},
                "initial_observation": {
                    "zone_temperature_c": 24.0,
                    "current_occupancy": 1.0,
                    "last_occupancy": 1.0,
                    "occupancy_next_steps": [1.0, 1.0, 1.0, 1.0],
                    "last_pmv": 0.2,
                    "last_setpoint_c": 25.0,
                },
            },
            "action": {
                "actual_setpoints_c": [25.0, 25.0, 25.0, 25.0],
                "matched_rules": ["hold", "hold", "hold", "hold"],
                "shield": [
                    {
                        "step": step,
                        "actuator_bounds": False,
                        "setpoint_rate_limit": False,
                        "comfort_recovery": False,
                    }
                    for step in (24, 25, 26, 27)
                ],
            },
            "outcome": {
                "zone_temperatures_c": [24.0, 24.0, 24.0, 24.0],
                "pmv": [0.2, 0.2, 0.2, 0.2],
                "effective_occupancy": [1.0, 1.0, 1.0, 1.0],
                "site_cost": 1.0,
                "site_energy_kwh": 2.0,
                "discomfort_zone_hours": 0.0,
                "discomfort_pmv_hours": 0.0,
                "occupied_peak_absolute_pmv": 0.2,
                "setpoint_total_variation_c": 0.0,
                "setpoint_direction_reversals": 0,
            },
        }
    ]
    executor_user_off = Executor.build_user(
        hour=7,
        zone="zone1",
        observation={
            "zone_temperature_c": 24.0,
            "last_pmv": 0.2,
            "current_occupancy": 1.0,
            "last_occupancy": 1.0,
            "last_setpoint": 25.0,
            "occ_ahead": [1.0, 1.0, 1.0, 1.0],
        },
        current_executable_program={"program_version": 0, "params": {}, "rules": []},
        causal_edges=None,
        allowance=None,
        working_memory=completed_hour,
    )
    assert "WORKING MEMORY" in executor_user_off
    assert "ACTIVE LONG-TERM EXPERIENCE SLOTS" not in executor_user_off
    for internal_coordinate in (
        "decision_hour",
        "sample_index",
        "physical_step",
        '"step":',
        '"step_ahead":',
        "time_seconds",
    ):
        assert internal_coordinate not in executor_user_off
    assert not re.search(r"\b\d{4}-\d{2}-\d{2}\b", executor_user_off)

    rounded_equivalent_observation = {
        "zone_temperature_c": 24.00004,
        "last_pmv": 0.20004,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_setpoint": 25.00004,
        "occ_ahead": [1.0, 1.0, 1.0, 1.0],
    }
    Executor.build_user(
        hour=7,
        zone="zone1",
        observation=rounded_equivalent_observation,
        current_executable_program={"program_version": 0, "params": {}, "rules": []},
        causal_edges=None,
        allowance=None,
        working_memory=completed_hour,
    )

    conflicting_observation = {
        "zone_temperature_c": 24.0,
        "last_pmv": 0.21,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_setpoint": 25.0,
        "occ_ahead": [1.0, 1.0, 1.0, 1.0],
    }
    with pytest.raises(ValueError, match="disagrees with working-memory endpoint"):
        Executor.build_user(
            hour=7,
            zone="zone1",
            observation=conflicting_observation,
            current_executable_program={"program_version": 0, "params": {}, "rules": []},
            causal_edges=None,
            allowance=None,
            working_memory=completed_hour,
        )

    reflector_user_off = Reflector.build_user(current_hour_cao=completed_hour)
    assert "COMPLETED CONTROL INTERVAL" in reflector_user_off
    assert "LONG-TERM EXPERIENCE SLOTS" not in reflector_user_off
    assert "06:00" in reflector_user_off and "07:00" in reflector_user_off


def test_model_visible_prompts_omit_internal_abbreviations_and_redundant_runtime_prose() -> None:
    prompts = "\n".join(
        system_prompt(role, long_term_memory=True)
        for role in ("orchestrator", "executor", "reflector")
    )
    assert not re.search(r"\bCAO(?:L)?\b", prompts)
    forbidden = (
        "omit unavailable",
        "offline logs",
        "oracle signals",
        "deterministic validator derives",
        "no_change is one available",
        "Invalid Lessons",
    )
    assert all(fragment not in prompts for fragment in forbidden)


def test_completed_reward_is_only_a_quantitative_reference_in_all_role_prompts() -> None:
    english = [
        system_prompt(role, language="en", causal_enabled=True, long_term_memory=False)
        for role in ("orchestrator", "executor", "reflector")
    ]
    objective = "Maintain comfort while reducing energy cost as much as possible."
    reference = (
        "The reward from a completed interval is a quantitative reference for the same "
        "frozen trade-off among energy cost, comfort, and action smoothness; a higher "
        "cumulative reward indicates a better overall result."
    )
    for prompt in english:
        assert objective in prompt
        assert reference in prompt
        lowered = prompt.lower()
        assert "maximize reward" not in lowered
        assert "erbc" not in lowered
        assert "reward threshold" not in lowered


def test_dynamic_prompt_fixture_provenance_is_self_consistent(repository_root: Path) -> None:
    fixture_root = repository_root / "tests" / "fixtures" / "prompts"
    provenance: dict[str, Any] = json.loads(
        (fixture_root / "provenance.json").read_text(encoding="utf-8")
    )
    assert provenance["schema_version"] == 2
    assert re.fullmatch(r"[0-9a-f]{40}", provenance["oracle_source_commit"])
    for declaration in provenance["oracle_owners"].values():
        assert set(declaration) == {"legacy_source_path", "source_blob_sha256"}
        assert declaration["legacy_source_path"].startswith("Revision1/")
        assert re.fullmatch(r"[0-9a-f]{64}", declaration["source_blob_sha256"])
    representative = provenance["representative_input"]
    assert set(representative) == {"path", "canonical_json_sha256", "canonical_length_bytes"}
    representative_path = repository_root / representative["path"]
    representative_value = json.loads(representative_path.read_text(encoding="utf-8"))
    representative_bytes = json.dumps(
        representative_value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert len(representative_bytes) == representative["canonical_length_bytes"]
    assert (
        hashlib.sha256(representative_bytes).hexdigest() == representative["canonical_json_sha256"]
    )
    for name, expected in provenance["fixtures"].items():
        content = (fixture_root / name).read_text(encoding="utf-8")
        assert len(content) == expected["length"]
        assert hashlib.sha256(content.encode("utf-8")).hexdigest() == expected["sha256"]
