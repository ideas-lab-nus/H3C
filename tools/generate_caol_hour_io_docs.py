"""Generate bilingual complete-hour working-memory/three-regime examples."""

from __future__ import annotations

import argparse
import copy
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from h3c.agents.prompts import system_prompt
from h3c.agents.roles import Executor, Orchestrator, Reflector
from h3c.causal.graph import load_graph
from h3c.control.budget import BudgetLedger, validate_allocation
from h3c.control.program import load_program, program_hash
from h3c.control.program_execution import execute_zone_programs
from h3c.control.validation import validate_candidate
from h3c.experiments.profiles import repository_root
from h3c.memory.caol import (
    REGIMES,
    active_experiences,
    apply_memory_operations,
    attach_hourly_lessons,
    build_hourly_cao,
    empty_regime_store,
    reflector_slot_view,
    resolve_reflector_payload,
    select_caol_working_memory,
    validate_memory_refs,
)
from h3c.memory.ledger import ProgramLedger
from h3c.runtime.clients import model_request_contract

Language = Literal["en", "zh"]


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)


def _code(value: Any, language: str = "json") -> str:
    body = value if isinstance(value, str) else _json(value)
    return f"```{language}\n{body}\n```\n"


def _load_fixture(root: Path) -> dict[str, Any]:
    path = root / "tests" / "fixtures" / "caol_complete_hour_mz_air.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("fixture_schema") != "h3c_caol_complete_hour":
        raise ValueError("unexpected CAOL complete-hour fixture schema")
    return value


def _previous_caol(fixture: Mapping[str, Any], language: Language) -> list[dict[str, Any]]:
    hour = int(fixture["hour"]) - 1
    first_step = int(fixture["first_step"]) - 4
    values: list[dict[str, Any]] = []
    for zone in fixture["zones"]:
        state = fixture["zone_state"][zone]
        lesson = (
            "Stable occupied conditions coincided with positive warm-side comfort headroom."
            if language == "en"
            else "稳定占用状态与正向暖侧舒适余量同时出现。"
        )
        values.append(
            {
                "hour": hour,
                "zone": zone,
                "context": {
                    "regime_step_coverage": {
                        "steady_state_occupancy": list(range(first_step, first_step + 4))
                    },
                    "initial_observation": {
                        "zone_temperature_c": state["zone_temperature_c"],
                        "current_occupancy": 1.0,
                        "last_occupancy": 1.0,
                        "occupancy_next_steps": [1.0, 1.0, 1.0, 1.0],
                        "last_pmv": state["last_pmv"],
                        "last_setpoint_c": state["last_setpoint"],
                    },
                },
                "action": {
                    "proposal": {"op": "no_change", "rationale": "completed-interval fixture"},
                    "admission": {
                        "status": "accepted",
                        "completed_validation_stages": [
                            "causal_admissibility",
                            "consistent_program_direction_proof",
                            "energy_budget_validation",
                            "program_validation",
                        ],
                    },
                    "program_version_before": 0,
                    "program_version_after": 0,
                    "actual_setpoints_c": [25.0, 25.0, 25.0, 25.0],
                    "matched_rules": ["occupied_hold"] * 4,
                    "shield": [
                        {
                            "step": step,
                            "actuator_bounds": False,
                            "setpoint_rate_limit": False,
                            "comfort_recovery": False,
                        }
                        for step in range(first_step, first_step + 4)
                    ],
                },
                "outcome": {
                    "zone_temperatures_c": [state["zone_temperature_c"]] * 4,
                    "pmv": [state["last_pmv"]] * 4,
                    "effective_occupancy": [1.0] * 4,
                    "site_cost": 3.02,
                    "site_energy_kwh": 21.1,
                    "discomfort_zone_hours": 0.0,
                    "discomfort_pmv_hours": 0.0,
                    "occupied_peak_absolute_pmv": state["last_pmv"],
                    "setpoint_total_variation_c": 0.0,
                    "setpoint_direction_reversals": 0,
                },
                "lesson": lesson,
            }
        )
    return values


def _observation(
    fixture: Mapping[str, Any],
    zone: str,
    *,
    zone_temperature_c: float,
    last_pmv: float,
    last_setpoint: float,
) -> dict[str, Any]:
    site = fixture["site_state"]
    return {
        "zone_temperature_c": zone_temperature_c,
        "current_occupancy": 1.0,
        "occ_ahead": [1.0, 1.0, 1.0, 1.0],
        "last_setpoint": last_setpoint,
        "last_pmv": last_pmv,
        "last_occupancy": 1.0,
        "next_hour_occupancy": 1.0,
        "electricity_price": site["price_now"],
        "outdoor_temp_c": site["outdoor_temp_c"],
        "solar_irr": site["solar_irr"],
        "comfort_headroom_c": fixture["zone_state"][zone]["comfort_headroom_c"],
        "outdoor_temp_change_next_1h_c": site["outdoor_temp_change_next_1h_c"],
        "solar_irr_max_next_1h_w_m2": site["solar_irr_max_next_1h_w_m2"],
        "solar_irr_mean_next_1h_w_m2": site["solar_irr_mean_next_1h_w_m2"],
        "weather_next_steps": copy.deepcopy(site["weather_next_steps"]),
        "outdoor_temp_threshold_candidates_c": [30.0, 32.0],
        "solar_irr_threshold_candidates_w_m2": [500.0, 650.0],
    }


def _initial_store(fixture: Mapping[str, Any]) -> dict[str, dict[str, dict[str, Any] | None]]:
    zones = fixture["zones"]
    store = empty_regime_store(zones)
    for zone in zones:
        for entry in fixture["active_experiences"][zone]:
            store[zone][entry["regime"]] = copy.deepcopy(entry)
    return store


def _localized_patch(
    fixture: Mapping[str, Any],
    zone: str,
    language: Language,
    thermal_edge_id: str,
) -> dict[str, Any]:
    source = fixture["executor_outputs"][zone]
    patch: dict[str, Any] = {
        "op": source["op"],
        "rationale": source[f"rationale_{language}"],
    }
    for key in ("param", "to"):
        if key in source:
            patch[key] = source[key]
    if patch["op"] != "no_change":
        patch["causal_edge_ids"] = [thermal_edge_id]
    return patch


def _allocation(
    fixture: Mapping[str, Any], language: Language, site_edge_id: str
) -> dict[str, Any]:
    output = copy.deepcopy(fixture["allocation_output"])
    if language == "en":
        output["rationale_per_zone"] = {
            "cor": "Stable core conditions require a bounded share.",
            "eas": "East has the smallest warm-side comfort headroom and receives first priority.",
            "nor": "Stable north conditions require a bounded share.",
            "sou": "South has moderate warm-side headroom and receives second priority.",
            "wes": "West has moderate warm-side headroom and receives third priority.",
        }
    else:
        output["rationale_per_zone"] = {
            "cor": "Core 状态稳定，需要有界额度。",
            "eas": "East 的暖侧舒适余量最小，因此优先级最高。",
            "nor": "North 状态稳定，需要有界额度。",
            "sou": "South 的暖侧余量中等，因此优先级第二。",
            "wes": "West 的暖侧余量中等，因此优先级第三。",
        }
    output["causal_edge_ids"] = [site_edge_id]
    return output


def _reflector_output(
    fixture: Mapping[str, Any], language: Language, *, memory_enabled: bool
) -> dict[str, Any]:
    root: dict[str, Any] = {
        "hourly_lessons": [
            {"zone": zone, "lesson": fixture["lessons"][zone][language]}
            for zone in fixture["zones"]
        ]
    }
    if memory_enabled:
        operations: list[dict[str, Any]] = []
        for zone in fixture["zones"]:
            source = fixture["memory_operations"][zone]
            operation = {"zone": zone, "op": source["op"]}
            for key in ("regime", "expected_revision"):
                if key in source:
                    operation[key] = source[key]
            if source["op"] in {"add", "replace"}:
                operation["experience"] = source[f"experience_{language}"]
            operations.append(operation)
        root["memory_operations"] = operations
    return root


def _render(language: Language, fixture: Mapping[str, Any], root: Path) -> str:
    labels = {
        "en": {
            "title": (
                "H3C complete MZ Air control interval: working memory and optional regime "
                "experience"
            ),
            "intro": (
                "This is one frozen, non-executed documentation fixture. Every prompt is produced "
                "by the production renderer and every deterministic transition below is evaluated "
                "by production validation, program, assurance, working-memory and CRUD owners. It is not a "
                "reported experimental result."
            ),
            "api": "1. Exact API request settings",
            "orch": "2. Orchestrator complete request, output and validation",
            "exec": "3. Five Executor complete requests, outputs and settlement",
            "settle": "4. Deterministic priority settlement",
            "physical": "5. Four executed actions and resulting observations",
            "reflect": "6. Reflector complete request and output",
            "caol": "7. Completed-interval record and next-interval working memory",
            "regime": "8. Three-regime classification",
            "crud": "9. Long-term experience read, CRUD and next-interval Executor input",
            "off": "10. Memory-off exact contract and disappearing fields",
            "request": "Complete serialized request body",
            "output": "Model output",
        },
        "zh": {
            "title": "H3C 完整 MZ Air 控制时段示例：工作记忆与可选状态经验",
            "intro": (
                "这是一个冻结且不执行API/BOPTEST的文档fixture。全部Prompt由生产renderer生成；下方所有"
                "确定性转换均由生产validation、program、assurance、working-memory和CRUD owner计算。它不是实验结果。"
            ),
            "api": "1. 精确API请求设置",
            "orch": "2. Orchestrator完整请求、输出与验证",
            "exec": "3. 五个Executor完整请求、输出与结算",
            "settle": "4. 确定性优先级结算",
            "physical": "5. 四次已执行动作及其结果观测",
            "reflect": "6. Reflector完整请求与输出",
            "caol": "7. 已完成控制时段记录与下一控制时段工作记忆",
            "regime": "8. 三状态判定",
            "crud": "9. 长期经验读取、CRUD与下一控制时段Executor输入",
            "off": "10. Memory-off精确契约与消失字段",
            "request": "完整序列化请求体",
            "output": "模型输出",
        },
    }[language]
    zones = list(fixture["zones"])
    hour = int(fixture["hour"])
    first_step = int(fixture["first_step"])
    graph = load_graph(root / "configs" / "graphs" / "mz_air_confirmed.json")
    edges = [edge.as_object() for edge in graph.edges]
    site_edges = [edge.as_object() for edge in graph.edges if edge.target == "power_meters"]
    thermal_edge_id = next(
        edge.identifier
        for edge in graph.edges
        if edge.source == "cooling_setpoint" and edge.target == "zone_temp"
    )
    site_edge_id = next(
        edge.identifier
        for edge in graph.edges
        if edge.source == "cooling_setpoint" and edge.target == "power_meters"
    )
    previous_caol = _previous_caol(fixture, language)
    previous_ledger = BudgetLedger(fixture["previous_allocation"], zones)
    for event in fixture["previous_budget_events"]:
        rejection = previous_ledger.energy_budget_validation(
            str(event["zone"]),
            float(event["amount_c"]),
            parameter=str(event["parameter"]),
            step=int(event["step"]),
        )
        if rejection is not None:
            raise ValueError("fixture previous Budget event was rejected")
    previous_utilisation = previous_ledger.utilisation()
    observations = {
        zone: _observation(
            fixture,
            zone,
            zone_temperature_c=float(fixture["zone_state"][zone]["zone_temperature_c"]),
            last_pmv=float(fixture["zone_state"][zone]["last_pmv"]),
            last_setpoint=float(fixture["zone_state"][zone]["last_setpoint"]),
        )
        for zone in zones
    }
    programs = {
        zone: ProgramLedger(
            load_program(root / "configs" / "programs" / "canonical_cooling_program.json", zone),
            causal_enabled=True,
        )
        for zone in zones
    }
    zone_coupling = {
        zone: {
            "zone_temperature_c": observations[zone]["zone_temperature_c"],
            "pmv": observations[zone]["last_pmv"],
            "occupancy": 1.0,
            "setpoint_c": observations[zone]["last_setpoint"],
            "occupancy_at_interval_end": 1.0,
            "precool_offset_from_unoccupied_base_c": -5.0,
            "resulting_precool_setpoint_c": 25.0,
            "temp_rise_to_warm_pmv_edge_c": observations[zone]["comfort_headroom_c"]["warmer_c"],
            "temp_drop_to_cool_pmv_edge_c": observations[zone]["comfort_headroom_c"]["cooler_c"],
        }
        for zone in zones
    }
    orchestrator_context = Orchestrator.build_context(
        hour=hour,
        decision_time_seconds=int(fixture["action_time_seconds"]),
        zones=zones,
        site_state=fixture["site_state"],
        zone_coupling=zone_coupling,
        causal_edges=site_edges,
        previous_allocation=fixture["previous_allocation"],
        previous_utilisation=previous_utilisation,
        working_memory=previous_caol,
        allocation_limits={"zones": zones, "site_cap_c": 10.0, "per_zone_cap_c": 5.0},
    )
    orchestrator_user = orchestrator_context.agent_view
    allocation = _allocation(fixture, language, site_edge_id)
    validate_allocation(
        allocation,
        zones,
        causal_enabled=True,
        allowed_causal_edge_ids=set(graph.by_id),
        site_causal_edge_ids={
            edge.identifier for edge in graph.edges if edge.target == "power_meters"
        },
    )
    orchestrator_request = model_request_contract(
        model=fixture["model"],
        system=system_prompt("orchestrator", language=language),
        user=orchestrator_user,
        thinking_mode="low",
    )
    store = _initial_store(fixture)
    ledger = BudgetLedger(allocation, zones)
    executor_material: dict[str, Any] = {}
    executor_contexts: dict[str, Any] = {}
    decisions: dict[str, dict[str, Any]] = {}
    for zone in zones:
        exposed = active_experiences(store, zone)
        executor_context = Executor.build_context(
            hour=hour,
            decision_time_seconds=int(fixture["action_time_seconds"]),
            zone=zone,
            observation=observations[zone],
            current_executable_program=programs[zone].prompt_view(),
            causal_edges=edges,
            allowance=ledger.snapshot(zone),
            working_memory=select_caol_working_memory(
                previous_caol,
                current_hour=hour,
                zone=zone,
                working_memory_hours=1,
                zones=zones,
            ),
            long_term_experiences=exposed,
            rejection_feedback=None,
        )
        executor_contexts[zone] = executor_context
        user = executor_context.agent_view
        patch = _localized_patch(fixture, zone, language, thermal_edge_id)
        output = {
            "patch": [patch],
            "memory_refs": copy.deepcopy(fixture["executor_outputs"][zone]["memory_refs"]),
        }
        valid_refs, invalid_refs = validate_memory_refs(output["memory_refs"], exposed)
        executor_material[zone] = {
            "request": model_request_contract(
                model=fixture["model"],
                system=system_prompt("executor", language=language, long_term_memory=True),
                user=user,
                thinking_mode="low",
            ),
            "output": output,
            "memory_refs": {
                "exposed": exposed,
                "reported": output["memory_refs"],
                "valid": valid_refs,
                "invalid": invalid_refs,
            },
        }
    settlement: list[dict[str, Any]] = []
    for zone in ledger.priority:
        patch = executor_material[zone]["output"]["patch"][0]
        before_version = programs[zone].version
        before_hash = program_hash(programs[zone].current_program)
        validation = validate_candidate(
            patch,
            programs[zone].current_program,
            graph=graph,
            ledger=ledger,
            zone=zone,
            step=first_step,
            causal_enabled=True,
            coordination_enabled=True,
        )
        if validation.accepted and validation.patch["op"] != "no_change":
            programs[zone].commit(validation.patch, step=first_step, hour=hour)
        decision = {
            "hour": hour,
            "step": first_step,
            "zone": zone,
            "status": "accepted" if validation.accepted else "rejected",
            "patch": copy.deepcopy(dict(validation.patch)),
            "completed_validation_stages": list(validation.completed_stages),
            "rejection": None if validation.rejection is None else validation.rejection.as_dict(),
            "program_version_before": before_version,
            "program_version_after": programs[zone].version,
            "program_hash_before": before_hash,
            "program_hash_after": program_hash(programs[zone].current_program),
            "current_program_version": programs[zone].version,
            "current_program_hash": program_hash(programs[zone].current_program),
            "memory_refs": executor_material[zone]["memory_refs"],
        }
        decisions[zone] = decision
        settlement.append(decision)
    step_rows: dict[str, list[dict[str, Any]]] = {zone: [] for zone in zones}
    last_setpoints = {zone: float(observations[zone]["last_setpoint"]) for zone in zones}
    last_pmvs = {zone: float(observations[zone]["last_pmv"]) for zone in zones}
    temperatures = {zone: float(observations[zone]["zone_temperature_c"]) for zone in zones}
    all_steps: list[dict[str, Any]] = []
    for offset in range(4):
        step_observations = {
            zone: _observation(
                fixture,
                zone,
                zone_temperature_c=temperatures[zone],
                last_pmv=last_pmvs[zone],
                last_setpoint=last_setpoints[zone],
            )
            for zone in zones
        }
        proposed, assured, assurance = execute_zone_programs(
            {zone: programs[zone].current_program for zone in zones}, step_observations
        )
        step_document = {"step": first_step + offset, "zones": {}}
        for zone in zones:
            outcome = copy.deepcopy(fixture["post_step_outcomes"][zone][offset])
            row = {
                "hour": hour,
                "step": first_step + offset,
                "zone": zone,
                "action_time_seconds": int(fixture["action_time_seconds"]) + offset * 900,
                "outcome_time_seconds": int(fixture["action_time_seconds"]) + (offset + 1) * 900,
                "observation": step_observations[zone],
                "interpreter": proposed[zone],
                "action_assurance": assurance[zone],
                "final_setpoint_c": assured[zone],
                "outcome": outcome,
            }
            step_rows[zone].append(row)
            step_document["zones"][zone] = row
            last_setpoints[zone] = assured[zone]
            last_pmvs[zone] = float(outcome["pmv"])
            temperatures[zone] = float(outcome["zone_temperature_c"])
        all_steps.append(step_document)
    current_cao = [
        build_hourly_cao(
            hour=hour,
            zone=zone,
            step_rows=step_rows[zone],
            program_decision=decisions[zone],
        )
        for zone in zones
    ]
    reflector_context = Reflector.build_context(
        current_hour_cao=current_cao,
        interval_start_time_seconds=int(fixture["action_time_seconds"]),
        long_term_slots={
            zone: reflector_slot_view(
                store,
                zone,
                [
                    regime
                    for _, regime in sorted(
                        (
                            min(steps),
                            regime,
                        )
                        for record in current_cao
                        if record["zone"] == zone
                        for regime, steps in record["context"]["regime_step_coverage"].items()
                    )
                ],
            )
            for zone in zones
        },
    )
    reflector_user = reflector_context.agent_view
    reflector_output = _reflector_output(fixture, language, memory_enabled=True)
    resolution = resolve_reflector_payload(reflector_output, zones=zones, long_term_memory=True)
    completed_caol = attach_hourly_lessons(current_cao, resolution.lessons)
    observed_regimes = {
        zone: list(completed_caol[index]["context"]["regime_step_coverage"])
        for index, zone in enumerate(zones)
    }
    updated_store, crud_audits = apply_memory_operations(
        store,
        resolution.operations,
        zones=zones,
        hour=hour,
        observed_regimes=observed_regimes,
    )
    next_working_memory = select_caol_working_memory(
        [*previous_caol, *completed_caol],
        current_hour=hour + 1,
        zone=None,
        working_memory_hours=1,
        zones=zones,
    )
    next_eas_observation = _observation(
        fixture,
        "eas",
        zone_temperature_c=temperatures["eas"],
        last_pmv=last_pmvs["eas"],
        last_setpoint=last_setpoints["eas"],
    )
    next_eas_user = Executor.build_user(
        hour=hour + 1,
        decision_time_seconds=int(fixture["action_time_seconds"]) + 3600,
        zone="eas",
        observation=next_eas_observation,
        current_executable_program=programs["eas"].prompt_view(),
        causal_edges=edges,
        allowance=ledger.snapshot("eas"),
        working_memory=select_caol_working_memory(
            [*previous_caol, *completed_caol],
            current_hour=hour + 1,
            zone="eas",
            working_memory_hours=1,
            zones=zones,
        ),
        long_term_experiences=active_experiences(updated_store, "eas"),
        rejection_feedback=None,
    )
    off_eas_user = Executor.build_user(
        hour=hour,
        decision_time_seconds=int(fixture["action_time_seconds"]),
        zone="eas",
        observation=observations["eas"],
        current_executable_program=ProgramLedger(
            load_program(root / "configs" / "programs" / "canonical_cooling_program.json", "eas")
        ).prompt_view(),
        causal_edges=edges,
        allowance=BudgetLedger(allocation, zones).snapshot("eas"),
        working_memory=select_caol_working_memory(
            previous_caol,
            current_hour=hour,
            zone="eas",
            working_memory_hours=1,
            zones=zones,
        ),
        long_term_experiences=None,
        rejection_feedback=None,
    )
    off_reflector_user = Reflector.build_user(
        current_hour_cao=current_cao,
        interval_start_time_seconds=int(fixture["action_time_seconds"]),
    )
    off_output_patch = copy.deepcopy(executor_material["eas"]["output"]["patch"])
    off_reflector_output = _reflector_output(fixture, language, memory_enabled=False)
    generic_settings = {
        "model": fixture["model"],
        "response_format": {"type": "json_object"},
        "thinking": {"type": "enabled"},
        "reasoning_effort": "low",
        "temperature_present": False,
        "top_p_present": False,
        "provider_call_is_stateless": True,
    }
    parts = [f"# {labels['title']}\n\n{labels['intro']}\n\n"]
    parts.append(f"## {labels['api']}\n\n")
    parts.append(_code(generic_settings))
    parts.append(f"## {labels['orch']}\n\n### {labels['request']}\n\n")
    parts.append(_code(orchestrator_request))
    parts.append(f"### {labels['output']}\n\n")
    parts.append(_code(allocation))
    parts.append("### Deterministic validation\n\n")
    parts.append(_code({"accepted": True, "zones": zones, "site_edge_id": site_edge_id}))
    parts.append(f"## {labels['exec']}\n\n")
    for zone in zones:
        parts.append(f"### Executor `{zone}` — {labels['request']}\n\n")
        parts.append(_code(executor_material[zone]["request"]))
        parts.append(f"### Executor `{zone}` — {labels['output']}\n\n")
        parts.append(_code(executor_material[zone]["output"]))
        parts.append(f"### Executor `{zone}` — deterministic memory-reference audit\n\n")
        parts.append(_code(executor_material[zone]["memory_refs"]))
    parts.append(f"## {labels['settle']}\n\n")
    parts.append(_code({"priority": list(ledger.priority), "settled_updates": settlement}))
    parts.append(f"## {labels['physical']}\n\n")
    parts.append(_code(all_steps))
    parts.append(f"## {labels['reflect']}\n\n### {labels['request']}\n\n")
    parts.append(
        _code(
            model_request_contract(
                model=fixture["model"],
                system=system_prompt("reflector", language=language, long_term_memory=True),
                user=reflector_user,
                thinking_mode="low",
            )
        )
    )
    parts.append(f"### {labels['output']}\n\n")
    parts.append(_code(reflector_output))
    parts.append(f"## {labels['caol']}\n\n### Completed-interval records\n\n")
    parts.append(_code(completed_caol))
    parts.append("### Next-interval Orchestrator working memory\n\n")
    parts.append(_code(next_working_memory))
    parts.append("### Next-interval East Executor working memory\n\n")
    parts.append(
        _code(
            select_caol_working_memory(
                [*previous_caol, *completed_caol],
                current_hour=hour + 1,
                zone="eas",
                working_memory_hours=1,
                zones=zones,
            )
        )
    )
    parts.append(f"## {labels['regime']}\n\n")
    parts.append(_code({"registered_regimes": list(REGIMES), "observed_by_zone": observed_regimes}))
    parts.append(f"## {labels['crud']}\n\n### Store before CRUD\n\n")
    parts.append(_code(store))
    parts.append("### Append-only CRUD audit\n\n")
    parts.append(_code(crud_audits))
    parts.append("### Store after CRUD\n\n")
    parts.append(_code(updated_store))
    parts.append("### Complete next-interval East Executor request\n\n")
    parts.append(
        _code(
            model_request_contract(
                model=fixture["model"],
                system=system_prompt("executor", language=language, long_term_memory=True),
                user=next_eas_user,
                thinking_mode="low",
            )
        )
    )
    parts.append(f"## {labels['off']}\n\n")
    parts.append(
        _code(
            {
                "executor_system_removed": ["long-term experience semantics", "memory_refs"],
                "executor_user_removed": ["ACTIVE LONG-TERM EXPERIENCES"],
                "executor_output_removed": ["memory_refs"],
                "reflector_system_removed": ["three-regime comparison", "CRUD operation contract"],
                "reflector_user_removed": ["ELIGIBLE LONG-TERM EXPERIENCE SLOTS"],
                "reflector_output_removed": ["memory_operations"],
                "runtime_output_removed": [
                    "long-term CRUD rows",
                    "Executor memory-reference audit",
                ],
                "orchestrator_removed": [],
                "working_memory_retained": True,
            }
        )
    )
    parts.append("### Memory-off East Executor complete request\n\n")
    parts.append(
        _code(
            model_request_contract(
                model=fixture["model"],
                system=system_prompt("executor", language=language, long_term_memory=False),
                user=off_eas_user,
                thinking_mode="low",
            )
        )
    )
    parts.append("### Memory-off East Executor output\n\n")
    parts.append(_code({"patch": off_output_patch}))
    parts.append("### Memory-off Reflector complete request\n\n")
    parts.append(
        _code(
            model_request_contract(
                model=fixture["model"],
                system=system_prompt("reflector", language=language, long_term_memory=False),
                user=off_reflector_user,
                thinking_mode="low",
            )
        )
    )
    parts.append("### Memory-off Reflector output\n\n")
    parts.append(_code(off_reflector_output))
    parts.append("## 11. Canonical human views and audit hashes\n\n")
    for role_name, context in (
        ("Orchestrator", orchestrator_context),
        ("East Executor", executor_contexts["eas"]),
        ("Reflector", reflector_context),
    ):
        parts.append(f"### {role_name} expanded canonical input\n\n")
        parts.append(context.human_view)
        parts.append(f"### {role_name} audit view\n\n")
        parts.append(_code(context.audit_view))
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = repository_root()
    fixture = _load_fixture(root)
    targets = {
        "en": root / "docs" / "h3c_complete_hour_io_en.md",
        "zh": root / "docs" / "h3c_complete_hour_io_zh.md",
    }
    mismatches: list[str] = []
    for language, target in targets.items():
        rendered = _render(language, fixture, root)
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != rendered:
                mismatches.append(str(target))
        else:
            target.write_text(rendered, encoding="utf-8", newline="\n")
    if mismatches:
        raise SystemExit("generated complete-hour documents are stale: " + ", ".join(mismatches))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
