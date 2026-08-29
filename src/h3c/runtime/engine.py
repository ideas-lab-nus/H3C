"""Strictly serial H3C physical execution engine."""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from h3c.agents.roles import (
    Executor,
    ModelClient,
    ModelContractError,
    Orchestrator,
    Reflector,
)
from h3c.causal.graph import ConfirmedGraph, derive_variant, load_graph
from h3c.control.budget import (
    BudgetLedger,
    allocation_fallback_audit,
    site_cap_max,
    validated_fallback_allocation,
)
from h3c.control.program import load_program, program_hash
from h3c.control.program_execution import build_program_observations, execute_zone_programs
from h3c.control.validation import validate_candidate
from h3c.experiments.matrix import RunPlan
from h3c.experiments.profiles import load_profile, repository_root
from h3c.experiments.settings import load_runtime_contract
from h3c.memory.ledger import ProgramLedger
from h3c.memory.working import (
    completed_executor_records,
    completed_summary_frame,
    recent_outcome_summary,
    reflector_results_view,
    select_completed_frames,
    select_executor_records,
)
from h3c.outputs.artifacts import RunArtifacts
from h3c.outputs.metrics import compute_run_metrics
from h3c.outputs.verification import verify_run
from h3c.runtime.clients import (
    BoptestHttpClient,
    OpenAICompatibleModelClient,
    TransportError,
)
from h3c.runtime.comfort import MetricsAccumulator, comfort_headroom, step_reward
from h3c.runtime.execution_lock import physical_execution_lock
from h3c.runtime.occupancy import effective_count, hourly_route
from h3c.runtime.protocol import (
    EvaluationBoundaryState,
    PhysicalClient,
    build_forecast_evidence,
    control_input,
    forecast_points,
    initialize_evaluation_boundary,
    require_time,
    resolve_forecast_missing_occupancy,
    site_power,
    zone_temperature_c,
)
from h3c.runtime.source_identity import committed_source_identity
from h3c.runtime.weather import weather_condition_inputs, weather_view

PhysicalFactory = Callable[[str], PhysicalClient]
ModelFactory = Callable[[RunArtifacts, str], ModelClient]


class RunAcceptanceFailure(RuntimeError):
    def __init__(self, run_dir: Path, verification: Mapping[str, Any]) -> None:
        super().__init__(f"run failed pre-completion verification: {verification['errors']}")
        self.run_dir = run_dir
        self.verification = dict(verification)


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _identity(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _source_commit() -> str:
    return committed_source_identity()


def _resolved_plan(plan: RunPlan) -> tuple[dict[str, Any], ConfirmedGraph | None]:
    root = repository_root()
    profile = load_profile(plan.profile)
    method = plan.method_config()
    resolved: dict[str, Any] = {"case_profile": profile, "method": method}
    graph: ConfirmedGraph | None = None
    if plan.causal_enabled:
        graph = load_graph(root / profile["graph"])
        if graph.profile != profile["profile"] or graph.zones != tuple(profile["zones"]):
            raise ValueError("confirmed graph identity does not match the case profile")
        if plan.graph_mutation is not None:
            graph = derive_variant(graph, plan.graph_mutation)
        resolved["resolved_graph"] = graph.resolved()
        if plan.graph_mutation is not None:
            resolved["graph_mutation"] = copy.deepcopy(plan.graph_mutation)
    return resolved, graph


def _endpoint_identity(endpoint: str) -> str:
    return hashlib.sha256(endpoint.rstrip("/").encode("utf-8")).hexdigest()


def _secret_occurrences(directory: Path, secret: str) -> int:
    if not secret:
        return 0
    needle = secret.encode("utf-8")
    return sum(
        path.read_bytes().count(needle)
        for path in directory.iterdir()
        if path.is_file() and path.name != ".execution.lock"
    )


def _real_physical_factory(endpoint: str) -> PhysicalClient:
    return BoptestHttpClient(endpoint)


def _set_model_context(client: ModelClient, **context: Any) -> None:
    setter = getattr(client, "set_context", None)
    if callable(setter):
        setter(**context)


def _graph_edges(graph: ConfirmedGraph | None) -> list[dict[str, Any]] | None:
    return None if graph is None else [edge.as_object() for edge in graph.edges]


def _site_graph_edges(graph: ConfirmedGraph | None) -> list[dict[str, Any]] | None:
    if graph is None:
        return None
    site_nodes = {str(node["id"]) for node in graph.nodes if node["scope"] == "site"}
    return [edge.as_object() for edge in graph.edges if edge.target in site_nodes]


def _shared_power_edge_ids(graph: ConfirmedGraph | None) -> set[str] | None:
    if graph is None:
        return None
    return {edge.identifier for edge in graph.edges if edge.target == "power_meters"}


def _forecast_slice(
    forecast: Mapping[str, Sequence[float]], point: str, step: int, count: int = 5
) -> list[float]:
    values = list(forecast[point][step : step + count])
    if len(values) != count:
        raise ValueError("evaluation forecast slice is incomplete")
    return [float(value) for value in values]


def _hour_observations(
    *,
    profile: Mapping[str, Any],
    forecast: Mapping[str, Sequence[float]],
    step: int,
    time_seconds: int,
    state: Mapping[str, Any],
    last_setpoint: Mapping[str, float],
    last_pmv: Mapping[str, float],
    last_occupancy: Mapping[str, float],
    pmv_of_temperature: Callable[[float], float],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], dict[str, float], dict[str, float]]:
    global_inputs = profile["global_inputs"]
    weather = weather_view(
        _forecast_slice(forecast, global_inputs["outdoor_temperature"], step),
        _forecast_slice(forecast, global_inputs["solar_irradiance"], step),
    )
    weather_conditions = weather_condition_inputs(weather)
    current_occupancy: dict[str, float] = {}
    next_hour_occupancy: dict[str, float] = {}
    future_occupancy: dict[str, list[float]] = {}
    temperatures: dict[str, float] = {}
    for zone, mapping in profile["zones"].items():
        raw = _forecast_slice(forecast, mapping["occupancy_forecast"], step)
        effective = [
            effective_count(profile["occupancy"], time_seconds + offset * 900, value)
            for offset, value in enumerate(raw)
        ]
        current_occupancy[zone] = effective[0]
        next_hour_occupancy[zone] = effective[4]
        future_occupancy[zone] = effective[1:5]
        temperatures[zone] = zone_temperature_c(profile, state, zone)
    program_observations = build_program_observations(
        tuple(profile["zones"]),
        current_occupancy=current_occupancy,
        future_occupancy=future_occupancy,
        last_setpoints_c=last_setpoint,
        last_pmv=last_pmv,
        last_occupancy=last_occupancy,
    )
    observations: dict[str, dict[str, Any]] = {}
    for zone in profile["zones"]:
        temperature = temperatures[zone]
        observations[zone] = {
            "zone_temperature_c": temperature,
            **program_observations[zone],
            "next_hour_occupancy": next_hour_occupancy[zone],
            "electricity_price": float(forecast[global_inputs["electricity_price"]][step]),
            "outdoor_temp_c": round(
                float(forecast[global_inputs["outdoor_temperature"]][step]) - 273.15, 2
            ),
            "solar_irr": round(float(forecast[global_inputs["solar_irradiance"]][step]), 1),
            "comfort_headroom_c": comfort_headroom(pmv_of_temperature, temperature),
            **weather,
            **weather_conditions,
        }
    site_state = {
        "outdoor_temp_c": round(
            float(forecast[global_inputs["outdoor_temperature"]][step]) - 273.15, 2
        ),
        "solar_irr": round(float(forecast[global_inputs["solar_irradiance"]][step]), 1),
        "price_now": round(float(forecast[global_inputs["electricity_price"]][step]), 5),
        "price_next_hour": round(float(forecast[global_inputs["electricity_price"]][step + 4]), 5),
        **weather,
    }
    return observations, site_state, current_occupancy, next_hour_occupancy


def _zone_coupling_view(
    zones: Sequence[str],
    observations: Mapping[str, Mapping[str, Any]],
    programs: Mapping[str, ProgramLedger],
    executor_records: Sequence[Mapping[str, Any]],
    previous_ledger: BudgetLedger | None,
) -> dict[str, Any]:
    coupling: dict[str, Any] = {}
    for zone in zones:
        observation = observations[zone]
        row: dict[str, Any] = {
            "current_setpoint_c": round(float(observation["last_setpoint"]), 2),
            "last_pmv": round(float(observation["last_pmv"]), 3),
            "current_occupancy": round(float(observation["current_occupancy"]), 1),
            "next_hour_occupancy": round(float(observation["next_hour_occupancy"]), 1),
            "temp_targets": {
                "precool_residual_c": programs[zone].current_program["params"]["precool_residual_c"]
            },
            "comfort_headroom_c": observation.get("comfort_headroom_c"),
        }
        occupied_events = [
            record
            for record in executor_records
            if record.get("scope", {}).get("zone") == zone
            and float(record.get("observation", {}).get("current_occupancy", 0.0)) > 0
        ][-4:]
        if occupied_events:
            more = sum(
                float(event["outcome"]["final_setpoint"]) <= 20.0 + 1e-6
                for event in occupied_events
            )
            less = sum(
                float(event["outcome"]["final_setpoint"]) >= 30.0 - 1e-6
                for event in occupied_events
            )
            if more:
                row["occupied_share_with_no_room_to_ask_for_more"] = round(
                    more / len(occupied_events), 3
                )
            if less:
                row["occupied_share_with_no_room_to_ask_for_less"] = round(
                    less / len(occupied_events), 3
                )
        if previous_ledger is not None:
            row["granted_c"] = round(previous_ledger.granted[zone], 4)
            row["used_c"] = round(previous_ledger.used[zone], 4)
        coupling[zone] = row
    return coupling


async def _agent_hour(
    *,
    plan: RunPlan,
    hour: int,
    step: int,
    zones: Sequence[str],
    observations: Mapping[str, Mapping[str, Any]],
    site_state: Mapping[str, Any],
    route: Mapping[str, Any],
    graph: ConfirmedGraph | None,
    programs: Mapping[str, ProgramLedger],
    frames: Sequence[Mapping[str, Any]],
    executor_records: Sequence[Mapping[str, Any]],
    client: ModelClient,
    artifacts: RunArtifacts,
    previous_allocation: Mapping[str, Any] | None,
    previous_utilisation: Mapping[str, Any] | None,
    previous_ledger: BudgetLedger | None,
    last_rejection_by_zone: dict[str, Mapping[str, Any] | None],
) -> tuple[
    BudgetLedger | None,
    dict[str, Any] | None,
    dict[str, Any] | None,
    list[dict[str, Any]],
    bool,
]:
    thinking_mode = (
        "disabled" if plan.thinking_policy == "all_roles_disabled" else str(route["thinking_mode"])
    )
    edges = _graph_edges(graph) if plan.causal_enabled else None
    site_edges = _site_graph_edges(graph) if plan.causal_enabled else None
    allowed_edge_ids = None if graph is None else set(graph.by_id)
    shared_power_edge_ids = _shared_power_edge_ids(graph)
    allocation: dict[str, Any] | None = None
    ledger: BudgetLedger | None = None
    raw_rejection: dict[str, Any] | None = None
    fallback_used = False
    fallback_source: str | None = None
    orchestrator_rationale_telemetry: dict[str, Any] | None = None
    resolved_site_cap = site_cap_max(zones)
    if plan.coordination_enabled:
        _set_model_context(client, hour=hour, step=step)
        orchestrator = Orchestrator(client)
        user = orchestrator.build_user(
            hour=hour,
            zones=zones,
            site_state=site_state,
            zone_coupling=_zone_coupling_view(
                zones, observations, programs, executor_records, previous_ledger
            ),
            causal_edges=site_edges,
            previous_allocation=previous_allocation,
            previous_utilisation=previous_utilisation,
            working_memory=select_completed_frames(
                frames,
                current_hour=hour,
                zone=None,
                working_memory_hours=plan.working_memory_hours,
                zones=zones,
            ),
            allocation_limits={
                "zones": list(zones),
                "site_cap_c": resolved_site_cap,
                "per_zone_cap_c": 5.0,
            },
        )
        try:
            allocation = await orchestrator.allocate(
                zones=zones,
                user=user,
                causal_enabled=plan.causal_enabled,
                thinking_mode=thinking_mode,
                allowed_causal_edge_ids=allowed_edge_ids,
                site_causal_edge_ids=shared_power_edge_ids,
            )
            orchestrator_rationale_telemetry = orchestrator.last_rationale_telemetry
        except ModelContractError as error:
            raw_rejection = {
                "code": "orchestrator_model_contract_rejected",
                "message": str(error),
                "raw_output": error.raw_output,
            }
            allocation, fallback_source = validated_fallback_allocation(
                zones,
                previous_allocation,
                site_cap_c=resolved_site_cap,
                causal_enabled=plan.causal_enabled,
                causal_edge_ids=(
                    [edge["id"] for edge in site_edges or ()] if plan.causal_enabled else None
                ),
                allowed_causal_edge_ids=allowed_edge_ids,
                site_causal_edge_ids=shared_power_edge_ids,
            )
            fallback_used = True
        ledger = BudgetLedger(allocation, zones)

    proposals: dict[str, dict[str, Any] | ModelContractError] = {}
    proposal_rationale_telemetry: dict[str, dict[str, Any] | None] = {}
    executor = Executor(client)
    # Production API calls remain strictly serial in frozen profile-zone order.
    # No budget charge occurs until every zone has completed this proposal phase.
    for zone in zones:
        allowance = None if ledger is None else ledger.snapshot(zone)
        user = executor.build_user(
            hour=hour,
            zone=zone,
            observation=observations[zone],
            current_executable_program=programs[zone].prompt_view(),
            causal_edges=edges,
            allowance=allowance,
            working_memory=select_executor_records(
                executor_records,
                current_step=step,
                zone=zone,
                working_memory_hours=plan.working_memory_hours,
            ),
            recent_outcome_summary=recent_outcome_summary(
                executor_records,
                current_step=step,
                zone=zone,
                working_memory_hours=plan.working_memory_hours,
            ),
            rejection_feedback=last_rejection_by_zone[zone],
        )
        _set_model_context(client, hour=hour, step=step, zone=zone)
        try:
            proposals[zone] = await executor.propose(
                user=user,
                causal_enabled=plan.causal_enabled,
                coordination_enabled=plan.coordination_enabled,
                thinking_mode=thinking_mode,
            )
            proposal_rationale_telemetry[zone] = executor.last_rationale_telemetry
        except ModelContractError as error:
            proposals[zone] = error
            proposal_rationale_telemetry[zone] = None

    updates: list[dict[str, Any]] = []
    settlement_order = list(ledger.priority) if ledger is not None else list(zones)
    if set(settlement_order) != set(zones) or len(settlement_order) != len(zones):
        raise ValueError("settlement order must cover exactly the configured zones")
    for zone in settlement_order:
        proposal = proposals[zone]
        version_before = programs[zone].version
        hash_before = program_hash(programs[zone].current_program)
        if isinstance(proposal, ModelContractError):
            rejected_row: dict[str, Any] = {
                "hour": hour,
                "step": step,
                "zone": zone,
                "status": "model_output_rejected",
                "patch": {
                    "op": "no_change",
                    "rationale": "tool-generated no_change after model contract rejection",
                },
                "rationale_telemetry": None,
                "completed_validation_stages": [],
                "rejection": {
                    "stage": "program_validation",
                    "code": "model_output_schema_rejected",
                    "message": str(proposal),
                    "raw_output": proposal.raw_output,
                },
                "program_version_before": version_before,
                "program_version_after": version_before,
                "program_hash_before": hash_before,
                "program_hash_after": hash_before,
                "current_program_version": version_before,
                "current_program_hash": hash_before,
                "replay_verified": bool(programs[zone].replay()),
            }
            artifacts.append_jsonl("program_updates.jsonl", rejected_row)
            updates.append(rejected_row)
            last_rejection_by_zone[zone] = copy.deepcopy(rejected_row["rejection"])
            continue
        validation = validate_candidate(
            proposal,
            programs[zone].current_program,
            graph=graph,
            ledger=ledger,
            zone=zone,
            step=step,
            causal_enabled=plan.causal_enabled,
            coordination_enabled=plan.coordination_enabled,
        )
        settled_row: dict[str, Any] = {
            "hour": hour,
            "step": step,
            "zone": zone,
            "status": "accepted" if validation.accepted else "rejected",
            "patch": copy.deepcopy(dict(validation.patch)),
            "rationale_telemetry": proposal_rationale_telemetry[zone],
            "completed_validation_stages": list(validation.completed_stages),
            "rejection": None if validation.rejection is None else validation.rejection.as_dict(),
            "program_version_before": version_before,
            "program_hash_before": hash_before,
        }
        if validation.accepted and validation.patch["op"] != "no_change":
            update = programs[zone].commit(validation.patch, step=step, hour=hour)
            settled_row["accepted_update"] = update.as_dict()
        settled_row["current_program_version"] = programs[zone].version
        settled_row["current_program_hash"] = program_hash(programs[zone].current_program)
        settled_row["program_version_after"] = settled_row["current_program_version"]
        settled_row["program_hash_after"] = settled_row["current_program_hash"]
        settled_row["replay_verified"] = bool(programs[zone].replay())
        artifacts.append_jsonl("program_updates.jsonl", settled_row)
        updates.append(settled_row)
        last_rejection_by_zone[zone] = (
            copy.deepcopy(settled_row["rejection"]) if settled_row["status"] == "rejected" else None
        )

    coordination_audit: dict[str, Any] | None = None
    if plan.coordination_enabled:
        coordination_audit = {
            "status": "fallback" if fallback_used else "accepted",
            "raw_contract": {
                "status": "rejected" if fallback_used else "accepted",
                "rejection": raw_rejection,
            },
            "rationale_telemetry": orchestrator_rationale_telemetry,
            "fallback": allocation_fallback_audit(
                used=fallback_used,
                reason=(
                    raw_rejection["message"]
                    if fallback_used and raw_rejection is not None
                    else None
                ),
                source=fallback_source if fallback_used else None,
            ),
            "allocation_audit": allocation,
            "settlement_order": settlement_order,
        }
    return ledger, allocation, coordination_audit, updates, fallback_used


async def _reflect_hour(
    *,
    plan: RunPlan,
    hour: int,
    step: int,
    zones: Sequence[str],
    route: Mapping[str, Any],
    current_results: Mapping[str, Any],
    frames: Sequence[Mapping[str, Any]],
    client: ModelClient,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    thinking_mode = (
        "disabled" if plan.thinking_policy == "all_roles_disabled" else str(route["thinking_mode"])
    )
    reflector = Reflector(client)
    user = reflector.build_user(
        current_hour_results=current_results,
        working_memory=select_completed_frames(
            frames,
            current_hour=hour,
            zone=None,
            working_memory_hours=plan.working_memory_hours,
            zones=zones,
        ),
    )
    _set_model_context(client, hour=hour, step=step)
    try:
        insights = await reflector.summarize(
            user=user,
            causal_enabled=plan.causal_enabled,
            thinking_mode=thinking_mode,
            zones=zones,
        )
        return insights, {"status": "accepted", "rejection": None}
    except ModelContractError as error:
        return [], {
            "status": "model_output_rejected",
            "rejection": {
                "code": "reflector_model_contract_rejected",
                "message": str(error),
                "raw_output": error.raw_output,
            },
        }


async def _evaluate(
    *,
    plan: RunPlan,
    profile: Mapping[str, Any],
    graph: ConfirmedGraph | None,
    physical: PhysicalClient,
    model: ModelClient | None,
    artifacts: RunArtifacts,
    boundary: EvaluationBoundaryState,
) -> tuple[dict[str, Any], bool, int, int]:
    step_seconds = int(profile["control_step_seconds"])
    evaluation_steps = plan.evaluation_hours * 4
    points = forecast_points(profile)
    source_forecast = physical.forecast(
        points, (evaluation_steps + 96) * step_seconds, step_seconds
    )
    evaluation_start = int(profile["evaluation_start_day"]) * 86400
    forecast, resolution_events = resolve_forecast_missing_occupancy(
        profile,
        source_forecast,
        points,
        evaluation_steps + 97,
        forecast_phase="evaluation",
        start_time_seconds=evaluation_start,
        step_seconds=step_seconds,
    )
    artifacts.write_forecast_inputs(
        build_forecast_evidence(
            points,
            source_forecast,
            forecast,
            start_time_seconds=evaluation_start,
            step_seconds=step_seconds,
        )
    )
    for event in resolution_events:
        artifacts.append_jsonl("timing.jsonl", event)
    zones = tuple(profile["zones"])
    programs = {
        zone: ProgramLedger(
            load_program(repository_root() / profile["program"], zone),
            causal_enabled=plan.causal_enabled,
        )
        for zone in zones
    }
    state = boundary.state
    last_setpoint = dict(boundary.last_setpoint_c)
    last_pmv = dict(boundary.last_pmv)
    last_occupancy = dict(boundary.last_occupancy)
    metrics = MetricsAccumulator()
    frames: list[dict[str, Any]] = []
    executor_records: list[dict[str, Any]] = []
    previous_allocation: Mapping[str, Any] | None = None
    previous_utilisation: Mapping[str, Any] | None = None
    hour_results: list[dict[str, Any]] = []
    route: dict[str, Any] = {}
    ledger: BudgetLedger | None = None
    coordination_audit: dict[str, Any] | None = None
    hour_program_decisions: list[dict[str, Any]] = []
    last_rejection_by_zone: dict[str, Mapping[str, Any] | None] = {zone: None for zone in zones}
    fallback_count = 0

    for step in range(evaluation_steps):
        action_time = evaluation_start + step * step_seconds
        require_time(state, action_time)
        observations, site_state, current_occ, next_occ = _hour_observations(
            profile=profile,
            forecast=forecast,
            step=step,
            time_seconds=action_time,
            state=state,
            last_setpoint=last_setpoint,
            last_pmv=last_pmv,
            last_occupancy=last_occupancy,
            pmv_of_temperature=boundary.comfort.pmv,
        )
        hour = step // 4
        if step % 4 == 0:
            route = hourly_route(hour, current_occ, next_occ)
            hour_results = []
            if plan.controller == "h3c_agent":
                if model is None:
                    raise ValueError("Agent execution requires a model client")
                (
                    ledger,
                    previous_allocation,
                    coordination_audit,
                    hour_program_decisions,
                    fallback_used,
                ) = await _agent_hour(
                    plan=plan,
                    hour=hour,
                    step=step,
                    zones=zones,
                    observations=observations,
                    site_state=site_state,
                    route=route,
                    graph=graph,
                    programs=programs,
                    frames=frames,
                    executor_records=executor_records,
                    client=model,
                    artifacts=artifacts,
                    previous_allocation=previous_allocation,
                    previous_utilisation=previous_utilisation,
                    previous_ledger=ledger,
                    last_rejection_by_zone=last_rejection_by_zone,
                )
                fallback_count += int(fallback_used)

        proposed, assured, assurance_audit = execute_zone_programs(
            {zone: programs[zone].current_program for zone in zones}, observations
        )
        next_state = physical.advance(control_input(profile, assured))
        require_time(next_state, action_time + step_seconds)
        if physical.test_id != boundary.test_id:
            raise ValueError("test id changed during formal evaluation")

        outdoor_point = profile["global_inputs"]["outdoor_temperature"]
        daily = forecast[outdoor_point][step : step + 97 : 4]
        boundary.comfort.update_clothing(
            action_time, sum(float(value) - 273.15 for value in daily) / len(daily)
        )
        temperatures = {zone: zone_temperature_c(profile, next_state, zone) for zone in zones}
        pmv = {zone: boundary.comfort.pmv(temperatures[zone]) for zone in zones}
        power = site_power(profile, next_state)
        price = float(forecast[profile["global_inputs"]["electricity_price"]][step])
        cost = power * step_seconds / 3.6e6 * price
        reward = step_reward(
            cost=cost,
            pmv=[pmv[zone] for zone in zones],
            occupancy=[current_occ[zone] for zone in zones],
            setpoints_c=[assured[zone] for zone in zones],
            previous_setpoints_c=[last_setpoint[zone] for zone in zones],
            objective=profile["objective"],
        )
        metrics.add(
            cost=cost,
            power_w=power,
            reward=reward,
            pmv=[pmv[zone] for zone in zones],
            occupancy=[current_occ[zone] for zone in zones],
        )
        for zone in zones:
            row = {
                "hour": hour,
                "step": step,
                "zone": zone,
                "test_id": boundary.test_id,
                "action_time_seconds": action_time,
                "outcome_time_seconds": action_time + step_seconds,
                "observation": observations[zone],
                "interpreter": proposed[zone],
                "action_assurance": assurance_audit[zone],
                "final_setpoint_c": assured[zone],
                "outcome": {
                    "zone_temperature_c": temperatures[zone],
                    "pmv": pmv[zone],
                    "effective_occupancy": current_occ[zone],
                    "power_w": power,
                    "cost": cost,
                },
            }
            artifacts.append_jsonl("zone_steps.jsonl", row)
            hour_results.append(row)
        artifacts.append_performance(
            (
                action_time,
                hour,
                step,
                power,
                cost,
                reward,
                _canonical([temperatures[zone] for zone in zones]),
                _canonical([assured[zone] for zone in zones]),
                _canonical([pmv[zone] for zone in zones]),
                _canonical([current_occ[zone] for zone in zones]),
            )
        )
        state = next_state
        last_setpoint = assured
        last_pmv = pmv
        last_occupancy = current_occ

        if step % 4 == 3:
            insights: list[dict[str, str]] = []
            reflector_contract: dict[str, Any] | None = None
            new_frames: list[dict[str, Any]] = []
            new_executor_records: list[dict[str, Any]] = []
            for zone in zones:
                zone_rows = [row for row in hour_results if row["zone"] == zone]
                decision = next(
                    (row for row in hour_program_decisions if row.get("zone") == zone),
                    {
                        "hour": hour,
                        "step": hour * 4,
                        "zone": zone,
                        "status": "not_called",
                        "patch": {"op": "no_change", "rationale": "controller has no model"},
                        "current_program_version": programs[zone].version,
                        "current_program_hash": program_hash(programs[zone].current_program),
                        "rejection": None,
                    },
                )
                new_frames.append(
                    completed_summary_frame(
                        hour=hour,
                        zone=zone,
                        step_rows=zone_rows,
                        program_decision=decision,
                    )
                )
                new_executor_records.extend(
                    completed_executor_records(
                        hour=hour,
                        zone=zone,
                        step_rows=zone_rows,
                        program_decision=decision,
                    )
                )
            if plan.controller == "h3c_agent":
                assert model is not None
                insights, reflector_contract = await _reflect_hour(
                    plan=plan,
                    hour=hour,
                    step=step,
                    zones=zones,
                    route=route,
                    current_results=reflector_results_view(new_frames, hour_program_decisions),
                    frames=frames,
                    client=model,
                )
            frames.extend(new_frames)
            executor_records.extend(new_executor_records)
            hourly: dict[str, Any] = {
                "hour": hour,
                "route": route,
                "reflector_summary": insights,
                "reflector_contract": reflector_contract,
                "program_replay": {
                    zone: {
                        "verified": bool(programs[zone].replay()),
                        "version": programs[zone].version,
                        "hash": program_hash(programs[zone].current_program),
                    }
                    for zone in zones
                },
            }
            if plan.coordination_enabled:
                hourly["orchestration"] = coordination_audit
                hourly["energy_budget"] = (
                    {"status": "unavailable"} if ledger is None else ledger.utilisation()
                )
                previous_utilisation = hourly["energy_budget"]
            artifacts.append_jsonl("hourly_decisions.jsonl", hourly)
    replay_verified = all(bool(program.replay()) for program in programs.values())
    return metrics.resolved(), replay_verified, len(resolution_events), fallback_count


async def _execute_one(
    plan: RunPlan,
    *,
    suite: str,
    output_root: Path,
    physical_factory: PhysicalFactory,
    model_factory: ModelFactory | None,
) -> dict[str, Any]:
    resolved, graph = _resolved_plan(plan)
    profile = resolved["case_profile"]
    runtime = load_runtime_contract()
    source_commit = _source_commit()
    physical_environment = runtime["physical_service"]["endpoint_environment_variable"]
    physical_endpoint = os.environ.get(physical_environment, "").rstrip("/")
    if not physical_endpoint:
        raise ValueError(f"{physical_environment} is required for physical execution")
    model_endpoint = ""
    if plan.controller == "h3c_agent":
        model_environment = runtime["model"]["endpoint_environment_variable"]
        key_environment = runtime["model"]["api_key_environment_variable"]
        model_endpoint = os.environ.get(model_environment, "").rstrip("/")
        if not model_endpoint or not os.environ.get(key_environment):
            raise ValueError("model endpoint and API key are required for Agent execution")
    execution_identity = {
        "plan_identity": plan.identity(profile),
        "source_commit": source_commit,
        "runtime_contract": runtime,
        "physical_endpoint_identity": _endpoint_identity(physical_endpoint),
        **(
            {"model_endpoint_identity": _endpoint_identity(model_endpoint)}
            if plan.controller == "h3c_agent"
            else {}
        ),
    }
    run_identity = _identity(execution_identity)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "-" + run_identity[:12]
    artifacts = RunArtifacts(output_root, suite, plan.profile, run_id)
    resolved["runtime_contract"] = runtime
    resolved["execution_identity"] = execution_identity
    manifest: dict[str, Any] = {
        "manifest_schema": "h3c_run_manifest",
        "schema_version": 3,
        "run_identity": run_identity,
        "source_commit": source_commit,
        "controller": plan.controller,
        "expected_agent_calls": plan.expected_agent_calls(len(profile["zones"])),
        "retry_count": 0,
        "transport_error_count": 0,
        "fallback_count": 0,
        "secret_exposure_count": 0,
        "secret_scan_status": ("pending" if plan.controller == "h3c_agent" else "not_applicable"),
        "occupancy_forecast_missing_value_resolution_count": 0,
        "program_replay_verified": False,
        "conditioning_prefix_identity": None,
        "evaluation_boundary_identity": None,
        "lifecycle": {
            "initialize_count": 0,
            "stop_count": 0,
            "test_id_changes": 0,
            "conditioning_advance_count": 0,
        },
    }
    artifacts.create(resolved, manifest)
    physical = physical_factory(physical_endpoint)
    model: ModelClient | None = None
    if plan.controller == "h3c_agent":
        model = (
            model_factory(artifacts, runtime["model"]["name"])
            if model_factory is not None
            else OpenAICompatibleModelClient(
                endpoint=model_endpoint,
                api_key=os.environ[key_environment],
                model=runtime["model"]["name"],
                sink=lambda name, row: artifacts.append_jsonl(name, row),
                retry_count_limit=runtime["model"]["retry_count"],
                retry_backoff_seconds=tuple(runtime["model"]["retry_backoff_seconds"]),
            )
        )
    started = time.perf_counter()
    initialized = False
    stop_attempted = False
    terminal_transport_error: TransportError | None = None

    def record_initialization(_test_id: str) -> None:
        nonlocal initialized
        initialized = True
        manifest["lifecycle"]["initialize_count"] = 1
        artifacts.replace_manifest(manifest)

    try:
        boundary = initialize_evaluation_boundary(
            physical,
            profile,
            artifacts,
            on_initialized=record_initialization,
        )
        manifest["occupancy_forecast_missing_value_resolution_count"] = (
            boundary.occupancy_missing_value_resolution_count
        )
        manifest["conditioning_prefix_identity"] = boundary.conditioning_prefix_identity
        manifest["evaluation_boundary_identity"] = boundary.evaluation_boundary_identity
        manifest["lifecycle"]["conditioning_advance_count"] = 0
        artifacts.append_jsonl(
            "timing.jsonl",
            {"phase": "initialization", "elapsed_seconds": time.perf_counter() - started},
        )
        evaluation_start_seconds = int(profile["evaluation_start_day"]) * 86400
        artifacts.append_jsonl(
            "timing.jsonl",
            {
                "phase": "physical_lifecycle",
                "event": "evaluation_started",
                "time_seconds": evaluation_start_seconds,
                "test_id": boundary.test_id,
            },
        )
        evaluation_started = time.perf_counter()
        _, replay_verified, evaluation_resolution_count, fallback_count = await _evaluate(
            plan=plan,
            profile=profile,
            graph=graph,
            physical=physical,
            model=model,
            artifacts=artifacts,
            boundary=boundary,
        )
        manifest["occupancy_forecast_missing_value_resolution_count"] += evaluation_resolution_count
        artifacts.append_jsonl(
            "timing.jsonl",
            {"phase": "evaluation", "elapsed_seconds": time.perf_counter() - evaluation_started},
        )
        evaluation_end_seconds = evaluation_start_seconds + plan.evaluation_hours * 3600
        artifacts.append_jsonl(
            "timing.jsonl",
            {
                "phase": "physical_lifecycle",
                "event": "evaluation_completed",
                "time_seconds": evaluation_end_seconds,
                "test_id": boundary.test_id,
            },
        )
        stop_attempted = True
        physical.stop()
        artifacts.append_jsonl(
            "timing.jsonl",
            {
                "phase": "physical_lifecycle",
                "event": "stopped",
                "time_seconds": evaluation_end_seconds,
                "test_id": boundary.test_id,
            },
        )
        initialized = False
        manifest["lifecycle"]["stop_count"] = 1
        manifest["program_replay_verified"] = replay_verified
        manifest["fallback_count"] = fallback_count
        manifest["retry_count"] = int(getattr(model, "retry_count", 0))
        if plan.controller == "h3c_agent":
            secret_name = runtime["model"]["api_key_environment_variable"]
            manifest["secret_exposure_count"] = _secret_occurrences(
                artifacts.run_dir, os.environ[secret_name]
            )
            manifest["secret_scan_status"] = "completed"
        artifacts.replace_manifest(manifest)
        metrics = compute_run_metrics(artifacts.run_dir)
        artifacts.write_metrics(metrics)
        verification = verify_run(artifacts.run_dir, require_completion=False)
        artifacts.write_verification(verification)
        if not verification["completion_eligible"]:
            raise RunAcceptanceFailure(artifacts.run_dir, verification)
        if verify_run(artifacts.run_dir, require_completion=False) != verification:
            raise ValueError("pre-completion verification changed after result publication")
        completion = {
            "status": "complete",
            "classification": verification["classification"],
            "run_identity": run_identity,
            "finished_at": datetime.now(UTC).isoformat(),
            "elapsed_seconds": time.perf_counter() - started,
        }
        completion_path = artifacts.publish_completion(completion)
        return {
            "profile": plan.profile,
            "status": "complete",
            "classification": verification["classification"],
            "run_identity": run_identity,
            "completion": str(completion_path),
            "metrics": metrics,
        }
    except TransportError as error:
        manifest["retry_count"] = int(getattr(model, "retry_count", 0))
        manifest["transport_error_count"] += 1
        terminal_transport_error = error
    finally:
        try:
            if (initialized or physical.test_id is not None) and not stop_attempted:
                stop_attempted = True
                physical.stop()
                manifest["lifecycle"]["stop_count"] += 1
        finally:
            if (
                plan.controller == "h3c_agent"
                and artifacts.run_dir.is_dir()
                and not (artifacts.run_dir / "completion.json").exists()
            ):
                secret_name = runtime["model"]["api_key_environment_variable"]
                manifest["secret_exposure_count"] = _secret_occurrences(
                    artifacts.run_dir, os.environ[secret_name]
                )
                manifest["secret_scan_status"] = "completed"
            if artifacts.run_dir.is_dir() and not (artifacts.run_dir / "completion.json").exists():
                artifacts.replace_manifest(manifest)
    if terminal_transport_error is not None:
        metrics = compute_run_metrics(artifacts.run_dir)
        artifacts.write_metrics(metrics)
        verification = verify_run(artifacts.run_dir, require_completion=False)
        artifacts.record_incomplete(metrics=metrics, verification=verification)
        raise terminal_transport_error
    raise AssertionError("execution exited without a result or terminal transport error")


def execute_serial(
    plans: Sequence[RunPlan],
    *,
    suite: str,
    output_root: Path | None = None,
    physical_factory: PhysicalFactory | None = None,
    model_factory: ModelFactory | None = None,
) -> dict[str, Any]:
    if not plans:
        raise ValueError("serial execution requires at least one run")
    root = (output_root or repository_root() / "outputs" / "runs").resolve()
    root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    with physical_execution_lock(root):
        for plan in plans:
            try:
                result = asyncio.run(
                    _execute_one(
                        plan,
                        suite=suite,
                        output_root=root,
                        physical_factory=physical_factory or _real_physical_factory,
                        model_factory=model_factory,
                    )
                )
            except RunAcceptanceFailure as error:
                result = {
                    "profile": plan.profile,
                    "status": "verification_failed",
                    "run_dir": str(error.run_dir),
                    "verification": error.verification,
                }
            results.append(result)
    return {"execution": "serial", "completed_runs": results}
