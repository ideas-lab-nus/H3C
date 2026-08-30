"""Three bounded Agent roles with deterministic prompt and output contracts."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from h3c.agents.contracts import (
    allocation_contract,
    rationale_length_telemetry,
)
from h3c.agents.dynamic_prompt import (
    COOLING_CONTROL_DOMAIN,
    block,
    executor_observation_view,
    merged_block,
    parameter_rule_limits,
    render_executor_working_memory,
    strip_audit_fields,
    visible_glossary_lines,
)
from h3c.agents.prompts import Role, system_prompt
from h3c.control.budget import validate_allocation
from h3c.control.program import validate_patch_shape


@dataclass(frozen=True)
class ModelCallContext:
    hour: int
    step: int
    call_ordinal: int
    zone: str | None = None

    def __post_init__(self) -> None:
        if min(self.hour, self.step, self.call_ordinal) < 0:
            raise ValueError("model call context indices must be nonnegative")
        if self.zone is not None and not self.zone:
            raise ValueError("model call context zone must be nonempty when present")

    def as_mapping(self) -> dict[str, Any]:
        context: dict[str, Any] = {
            "hour": self.hour,
            "step": self.step,
            "call_ordinal": self.call_ordinal,
        }
        if self.zone is not None:
            context["zone"] = self.zone
        return context


class ModelClient(Protocol):
    async def complete(
        self,
        *,
        context: ModelCallContext,
        role: Role,
        system: str,
        user: str,
        thinking_mode: str,
    ) -> str: ...


def parse_bare_json(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str) or raw.lstrip().startswith("```"):
        raise ValueError("model output must be one bare JSON object")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("model output is not valid bare JSON") from error
    if not isinstance(value, dict):
        raise ValueError("model output root must be an object")
    return value


class ModelContractError(ValueError):
    """A model response failed the exact role contract without a transport failure."""

    def __init__(self, message: str, raw_output: str) -> None:
        super().__init__(message)
        self.raw_output = raw_output


def resolve_orchestrator_model_output(
    raw: str,
    zones: Sequence[str],
    *,
    causal_enabled: bool,
    allowed_causal_edge_ids: set[str] | None = None,
    site_causal_edge_ids: set[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve one raw Orchestrator response through the production contract."""
    try:
        allocation = parse_bare_json(raw)
        if set(allocation) == {"allocation_contract"}:
            wrapped = allocation["allocation_contract"]
            if not isinstance(wrapped, dict):
                raise ValueError("Orchestrator allocation_contract wrapper must contain an object")
            allocation = dict(wrapped)
        if set(allocation) != set(allocation_contract(causal_enabled=causal_enabled)):
            raise ValueError("Orchestrator output does not match the exact allocation contract")
        validate_allocation(
            allocation,
            zones,
            causal_enabled=causal_enabled,
            allowed_causal_edge_ids=allowed_causal_edge_ids,
            site_causal_edge_ids=site_causal_edge_ids,
        )
        telemetry = rationale_length_telemetry("orchestrator", allocation["rationale_per_zone"])
    except ValueError as error:
        raise ModelContractError(str(error), raw) from error
    return allocation, telemetry


def resolve_executor_model_output(
    raw: str, *, causal_enabled: bool
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve one raw Executor response without applying a control decision."""
    try:
        root = parse_bare_json(raw)
        root_fields = set(root)
        if root_fields == {"patch", "rationale"}:
            audit_rationale = root["rationale"]
            if not isinstance(audit_rationale, str) or not audit_rationale.strip():
                raise ValueError("Executor root rationale must be a nonempty audit string")
        elif root_fields == {"patch", "root"}:
            duplicate = root["root"]
            if not isinstance(duplicate, dict) or set(duplicate) != {"patch"}:
                raise ValueError("Executor root wrapper must contain only the duplicate patch")
            if duplicate["patch"] != root["patch"]:
                raise ValueError("Executor root wrapper conflicts with the canonical patch")
        elif root_fields != {"patch"}:
            raise ValueError("Executor output contains unsupported root fields")
        if not isinstance(root["patch"], list) or len(root["patch"]) != 1:
            raise ValueError("Executor output must contain exactly one patch operation")
        raw_patch = root["patch"][0]
        if not isinstance(raw_patch, dict):
            raise ValueError("Executor patch operation must be an object")
        patch = dict(raw_patch)
        if patch.get("op") == "replace_rule" and "id" in patch:
            rule = patch.get("rule")
            if not isinstance(rule, dict) or patch["id"] != rule.get("id"):
                raise ValueError("Executor replace_rule id conflicts with rule.id")
            patch.pop("id")
        validate_patch_shape(patch, causal_enabled=causal_enabled)
        telemetry = rationale_length_telemetry("executor", {"operation": patch["rationale"]})
    except (KeyError, TypeError, ValueError) as error:
        raise ModelContractError(str(error), raw) from error
    return dict(patch), telemetry


@dataclass
class Orchestrator:
    client: ModelClient
    last_rationale_telemetry: dict[str, Any] | None = field(init=False, default=None)

    @staticmethod
    def build_user(
        *,
        hour: int,
        zones: Sequence[str],
        site_state: Mapping[str, Any],
        zone_coupling: Mapping[str, Any],
        causal_edges: Sequence[Mapping[str, Any]] | None,
        previous_allocation: Mapping[str, Any] | None,
        previous_utilisation: Mapping[str, Any] | None,
        working_memory: Sequence[Mapping[str, Any]] | None,
        allocation_limits: Mapping[str, Any],
    ) -> str:
        del hour
        expected_limits = {"zones", "site_cap_c", "per_zone_cap_c"}
        if set(allocation_limits) != expected_limits:
            raise ValueError("allocation limits must use the exact resolved cooling fields")
        if list(allocation_limits["zones"]) != list(zones):
            raise ValueError("allocation-limit zones must preserve configured zone order")
        site = strip_audit_fields(site_state)
        coupling = strip_audit_fields(zone_coupling)
        edges = strip_audit_fields(causal_edges)
        previous = strip_audit_fields(previous_allocation)
        utilisation = strip_audit_fields(previous_utilisation)
        memory = strip_audit_fields(working_memory)
        glossary = visible_glossary_lines(
            site, memory, coupling, previous, utilisation, allocation_limits
        )
        return "".join(
            (
                block("CAUSAL EVIDENCE", edges, tabular=True),
                block("ALLOCATION LIMITS", allocation_limits),
                block("CONTROL DOMAIN", COOLING_CONTROL_DOMAIN),
                block("WHAT SOME OF THE FIELD NAMES MEAN", glossary),
                block("WORKING MEMORY", memory, tabular=True),
                merged_block("CROSS-ZONE CONSTRAINTS", (("zone coupling", coupling, False),)),
                merged_block(
                    "PREVIOUS ALLOCATION AND UTILISATION",
                    (
                        ("previous allocation", previous, False),
                        ("previous utilisation", utilisation, False),
                    ),
                ),
                block("CURRENT SITE STATE AND FORECAST", site),
            )
        )

    async def allocate(
        self,
        *,
        context: ModelCallContext,
        zones: Sequence[str],
        user: str,
        causal_enabled: bool,
        thinking_mode: str,
        allowed_causal_edge_ids: set[str] | None = None,
        site_causal_edge_ids: set[str] | None = None,
    ) -> dict[str, Any]:
        self.last_rationale_telemetry = None
        raw = await self.client.complete(
            context=context,
            role="orchestrator",
            system=system_prompt("orchestrator", causal_enabled=causal_enabled),
            user=user,
            thinking_mode=thinking_mode,
        )
        allocation, self.last_rationale_telemetry = resolve_orchestrator_model_output(
            raw,
            zones,
            causal_enabled=causal_enabled,
            allowed_causal_edge_ids=allowed_causal_edge_ids,
            site_causal_edge_ids=site_causal_edge_ids,
        )
        return allocation


@dataclass
class Executor:
    client: ModelClient
    last_rationale_telemetry: dict[str, Any] | None = field(init=False, default=None)

    @staticmethod
    def build_user(
        *,
        hour: int,
        zone: str,
        observation: Mapping[str, Any],
        current_executable_program: Mapping[str, Any],
        causal_edges: Sequence[Mapping[str, Any]] | None,
        allowance: Mapping[str, Any] | None,
        working_memory: Sequence[Mapping[str, Any]] | None,
        recent_outcome_summary: Mapping[str, Any] | None = None,
        rejection_feedback: Mapping[str, Any] | None = None,
    ) -> str:
        del hour, zone
        observation_view = strip_audit_fields(executor_observation_view(observation))
        program_view = strip_audit_fields(current_executable_program)
        edges = strip_audit_fields(causal_edges)
        budget = strip_audit_fields(allowance)
        memory = strip_audit_fields(working_memory)
        summary = strip_audit_fields(recent_outcome_summary)
        rejection = strip_audit_fields(rejection_feedback)
        limits = parameter_rule_limits()
        glossary = visible_glossary_lines(
            observation_view,
            program_view,
            *([{"allocation": budget}] if budget is not None else []),
            memory,
            summary,
            rejection,
            limits,
        )
        rendered_memory = render_executor_working_memory(memory)
        return "".join(
            (
                block("CURRENT EXECUTABLE PROGRAM P_h", program_view),
                block("PARAMETER AND RULE LIMITS", limits),
                block("CAUSAL EVIDENCE", edges, tabular=True),
                block("CONTROL DOMAIN", COOLING_CONTROL_DOMAIN),
                block("WHAT SOME OF THE FIELD NAMES MEAN", glossary),
                block("ALLOCATION", {"allocation": budget} if budget is not None else None),
                block("WORKING MEMORY", rendered_memory),
                block("RECENT OUTCOME SUMMARY", summary),
                block("LAST REJECTION", rejection),
                block("ZONE OBSERVATION", observation_view),
            )
        )

    async def propose(
        self,
        *,
        context: ModelCallContext,
        user: str,
        causal_enabled: bool,
        coordination_enabled: bool,
        thinking_mode: str,
    ) -> dict[str, Any]:
        raw = await self.client.complete(
            context=context,
            role="executor",
            system=system_prompt(
                "executor",
                causal_enabled=causal_enabled,
                coordination_enabled=coordination_enabled,
            ),
            user=user,
            thinking_mode=thinking_mode,
        )
        self.last_rationale_telemetry = None
        patch, self.last_rationale_telemetry = resolve_executor_model_output(
            raw, causal_enabled=causal_enabled
        )
        return patch


_SENTENCE_END = re.compile(r"(?<!\d)\.|\.(?!\d)|[!?。！？]")


def clean_insight(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    sentence_ends = list(_SENTENCE_END.finditer(text))
    if (
        not text
        or "\r" in text
        or "\n" in text
        or len(sentence_ends) > 1
        or (sentence_ends and text[sentence_ends[0].end() :].strip())
    ):
        return None
    return text


@dataclass
class Reflector:
    client: ModelClient

    @staticmethod
    def build_user(
        *,
        current_hour_results: Mapping[str, Any],
        working_memory: Sequence[Mapping[str, Any]] | None,
    ) -> str:
        results = strip_audit_fields(current_hour_results)
        memory = strip_audit_fields(working_memory)
        glossary = visible_glossary_lines(results, memory)
        return "".join(
            (
                block("WHAT SOME OF THE FIELD NAMES MEAN", glossary),
                block("CURRENT HOUR RESULTS", results, tabular=True),
                block("WORKING MEMORY", memory, tabular=True),
            )
        )

    async def summarize(
        self,
        *,
        context: ModelCallContext,
        user: str,
        causal_enabled: bool,
        thinking_mode: str,
        zones: Sequence[str],
    ) -> list[dict[str, str]]:
        raw = await self.client.complete(
            context=context,
            role="reflector",
            system=system_prompt("reflector", causal_enabled=causal_enabled),
            user=user,
            thinking_mode=thinking_mode,
        )
        try:
            payload = parse_bare_json(raw)
            if set(payload) != {"pairs"} or not isinstance(payload["pairs"], list):
                raise ValueError("Reflector output must contain exactly a pairs list")
            accepted: list[dict[str, str]] = []
            seen: set[str] = set()
            for pair in payload["pairs"]:
                if not isinstance(pair, Mapping) or set(pair) != {"zone", "insight_text"}:
                    raise ValueError("Reflector pair does not match the exact contract")
                zone = pair["zone"]
                insight = clean_insight(pair["insight_text"])
                if zone not in zones or zone in seen or insight is None:
                    raise ValueError("Reflector pair has an invalid zone or insight")
                seen.add(str(zone))
                accepted.append({"zone": str(zone), "insight_text": insight})
        except ValueError as error:
            raise ModelContractError(str(error), raw) from error
        return accepted
