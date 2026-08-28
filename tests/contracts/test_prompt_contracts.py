from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest

from h3c.agents.prompts import Language, Role, assert_causal_disabled_text_clean, system_prompt
from h3c.agents.roles import Executor, Orchestrator, Reflector
from h3c.memory.ledger import ProgramLedger


@pytest.mark.parametrize("role", ["orchestrator", "executor", "reflector"])
def test_canonical_system_prompt_matches_oracle_bytes(
    role: Role, oracle_fixture: dict[str, Any]
) -> None:
    prompt = system_prompt(role)
    expected = oracle_fixture["system_prompts"][role]
    assert len(prompt) == expected["length"]
    assert hashlib.sha256(prompt.encode("utf-8")).hexdigest() == expected["sha256"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_rationale_prompt_has_no_length_semantics_while_reflector_is_unchanged(
    language: Language,
) -> None:
    orchestrator = system_prompt("orchestrator", language=language)
    executor = system_prompt("executor", language=language)
    reflector = system_prompt("reflector", language=language)
    assert "240" not in orchestrator + executor
    assert "short rationale" not in (orchestrator + executor).lower()
    assert "short string" not in (orchestrator + executor).lower()
    assert "简短理由" not in orchestrator + executor
    assert "nonempty string" in orchestrator
    assert "nonempty rationale" in executor if language == "en" else "非空理由" in executor
    assert "short sentence" in reflector if language == "en" else "短句" in reflector


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
            "per_zone_cap_c": 5.0,
        },
    )
    assert '"zones":["zoneB","zoneA"]' in user
    assert '"site_cap_c":5.0' in user
    assert '"per_zone_cap_c":5.0' in user
    assert "site_cap_max_c" not in user and "priority_contract" not in user


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
    assert "CURRENT EXECUTABLE PROGRAM" in user
    assert oracle_fixture_absent(user)


def oracle_fixture_absent(user: str) -> bool:
    forbidden = ("accepted_updates", "program_hash_before", "version_before")
    return all(token not in user for token in forbidden)


def test_missing_blocks_are_omitted_not_rendered(canonical_program: dict[str, Any]) -> None:
    user = Executor.build_user(
        hour=0,
        zone="zone1",
        observation={"last_pmv": 0.0},
        current_executable_program={"program": canonical_program},
        causal_edges=None,
        allowance=None,
        working_memory=None,
    )
    assert "CONFIRMED CAUSAL EDGES" not in user
    assert "ALLOWANCE" not in user
    assert "WORKING MEMORY" not in user
    assert "N/A" not in user and "null" not in user


def _dynamic_prompt_inputs(repository_root: Path) -> tuple[str, str, str]:
    fixture = json.loads(
        (
            repository_root / "tests" / "fixtures" / "prompts" / "representative_input.json"
        ).read_text(encoding="utf-8")
    )
    orchestrator_input = fixture["orchestrator"]
    budget_box = orchestrator_input["budget_box"]
    orchestrator = Orchestrator.build_user(
        hour=orchestrator_input["hour"],
        zones=orchestrator_input["zones"],
        site_state=orchestrator_input["site_nodes"],
        zone_coupling=orchestrator_input["zone_coupling"],
        causal_edges=orchestrator_input["site_edges"],
        previous_allocation=orchestrator_input["previous_allocation"],
        previous_utilisation=orchestrator_input["previous_utilisation"],
        working_memory=orchestrator_input["working_memory"],
        allocation_limits={
            "zones": orchestrator_input["zones"],
            "site_cap_c": budget_box["site_max_c"],
            "per_zone_cap_c": budget_box["per_zone_max_c"],
        },
    )

    executor_input = fixture["executor"]
    exposed_observation = executor_input["observations"]
    exposed_to_runtime = {
        "occupancy_next_steps": "occ_ahead",
        "zone_temp_c": "zone_temperature_c",
        "last_setpoint_c": "last_setpoint",
        "price_now": "electricity_price",
    }
    observation = {
        exposed_to_runtime.get(key, key): value for key, value in exposed_observation.items()
    }
    memory = copy.deepcopy(executor_input["working_memory"])
    for record in memory:
        shield = record["validation"]["shield"]
        shield["actuator_limit_applied"] = shield.pop("s" + "1")
        shield["rate_limit_applied"] = shield.pop("s" + "2")
        shield["comfort_interlock_applied"] = shield.pop("s" + "3")
    program = fixture["program"]
    executor = Executor.build_user(
        hour=executor_input["step"] // 4,
        zone=executor_input["zone"],
        observation=observation,
        current_executable_program={
            "program_version": executor_input["program_version"],
            "params": program["params"],
            "rules": program["rules"],
        },
        causal_edges=executor_input["edges"],
        allowance=executor_input["budget"],
        working_memory=memory,
        recent_outcome_summary=executor_input["recent_outcome_summary"],
        rejection_feedback=executor_input["repair_info"],
    )
    reflector_input = fixture["reflector"]
    reflector = Reflector.build_user(
        current_hour_results=reflector_input["current_hour_results"],
        working_memory=reflector_input["working_memory"],
    )
    return orchestrator, executor, reflector


def test_dynamic_user_prompts_match_read_only_final_w_oracle_bytes(
    repository_root: Path,
) -> None:
    rendered = _dynamic_prompt_inputs(repository_root)
    fixture_root = repository_root / "tests" / "fixtures" / "prompts"
    names = ("orchestrator_old.txt", "executor_old.txt", "reflector_old.txt")
    for actual, name in zip(rendered, names, strict=True):
        expected = (fixture_root / name).read_text(encoding="utf-8")
        assert actual == expected


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
