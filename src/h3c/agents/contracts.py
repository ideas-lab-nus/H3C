"""Single owner for Agent-facing JSON contracts."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

PATCH_OPERATIONS = (
    "set_param",
    "add_rule",
    "replace_rule",
    "remove_rule",
    "move_rule",
    "no_change",
)

ALLOCATION_CONTRACT_SPEC: dict[str, Any] = {
    "fields": ("site_cap_c", "zone_budgets_c", "priority", "rationale_per_zone"),
    "causal_field": "causal_edge_ids",
    "per_zone_cap_c": 5.0,
    "site_cap_rule": "must_equal_supplied_site_cap",
    "zone_set_rule": "all_and_only_configured_zones",
    "budget_rule": "finite_nonnegative_each_and_sum_not_above_site_cap",
    "site_cap_need_not_be_fully_allocated": True,
    "priority_rule": "each_configured_zone_exactly_once_in_descending_priority",
    "rationale_rule": "all_and_only_configured_zones_with_nonempty_strings",
    "causal_rule": "unique_nonempty_subset_of_visible_ids_including_a_site_edge",
}

_PATCH_CONTRACT: dict[str, Any] = {
    "root": {"required": ["patch"], "patch": "list with exactly one operation"},
    "operations": {
        "no_change": {"required": ["op", "rationale"], "optional": []},
        "set_param": {
            "required": ["op", "param", "to", "causal_edge_ids", "rationale"],
            "optional": [],
        },
        "add_rule": {
            "required": ["op", "rule", "causal_edge_ids", "rationale"],
            "optional": ["index"],
        },
        "replace_rule": {
            "required": ["op", "rule", "causal_edge_ids", "rationale"],
            "optional": [],
        },
        "remove_rule": {
            "required": ["op", "id", "causal_edge_ids", "rationale"],
            "optional": [],
        },
        "move_rule": {
            "required": ["op", "id", "to_index", "causal_edge_ids", "rationale"],
            "optional": [],
        },
    },
    "rule": {
        "required": ["id", "when", "then"],
        "when_item": {"required": ["field", "op", "value"]},
        "then": {"required": ["op"], "value_for": ["set_residual", "step_setpoint"]},
    },
    "causal_edge_ids": "stable IDs from the supplied structured edge objects",
    "rationale": "nonempty string",
}


def rationale_length_telemetry(role: str, rationales: Mapping[str, str]) -> dict[str, Any]:
    """Report rationale character lengths without influencing any decision."""
    if role not in {"orchestrator", "executor"}:
        raise ValueError("rationale telemetry role is invalid")
    if (
        not isinstance(rationales, Mapping)
        or not rationales
        or any(
            not isinstance(scope, str)
            or not scope
            or not isinstance(value, str)
            or not value.strip()
            for scope, value in rationales.items()
        )
    ):
        raise ValueError("rationale telemetry requires nonempty string values")
    lengths = {scope: len(value) for scope, value in rationales.items()}
    return {
        "telemetry_schema": "h3c_rationale_length_telemetry",
        "schema_version": 1,
        "role": role,
        "character_lengths": lengths,
        "maximum_character_length": max(lengths.values()),
        "decision_use": "none",
    }


def patch_contract(*, causal_enabled: bool = True) -> dict[str, Any]:
    """Return the exact public patch contract for one causal mode."""
    view = copy.deepcopy(_PATCH_CONTRACT)
    if not causal_enabled:
        for operation in view["operations"].values():
            operation["required"] = [
                field for field in operation["required"] if field != "causal_edge_ids"
            ]
        view.pop("causal_edge_ids")
    return view


def compact_patch_contract(*, causal_enabled: bool = True, language: str = "en") -> str:
    """Render the unchanged patch wire contract without repeating common fields per operation."""
    causal_line = (
        "Modifying operation also requires causal_edge_ids.\n"
        if causal_enabled and language == "en"
        else "所有修改类操作还必须包含 causal_edge_ids。\n"
        if causal_enabled
        else ""
    )
    intro = (
        "patch: list of exactly one operation.\nCommon required fields: op, rationale.\n"
        if language == "en"
        else "root：patch 是仅包含一个 operation 的列表。\n"
        "所有 operation 公共必填：op、rationale。\n"
    )
    operation_table = (
        "| op | additional required | optional |\n"
        "| --- | --- | --- |\n"
        "| no_change | — | — |\n"
        "| set_param | param, to | — |\n"
        "| add_rule | rule | index |\n"
        "| replace_rule | rule | — |\n"
        "| remove_rule | id | — |\n"
        "| move_rule | id, to_index | — |\n"
    )
    rule = (
        "rule: id, when, then. when item: field, op, value. then: op, plus value for "
        "set_residual or step_setpoint."
        if language == "en"
        else "rule 必须包含 id、when、then。每个 when 条件必须包含 field、op、value。"
        "then 必须包含 op；set_residual 或 step_setpoint 还必须包含 value。"
    )
    return intro + causal_line + operation_table + rule


def allocation_contract(*, causal_enabled: bool = True) -> tuple[str, ...]:
    fields = list(ALLOCATION_CONTRACT_SPEC["fields"])
    if causal_enabled:
        fields.append(str(ALLOCATION_CONTRACT_SPEC["causal_field"]))
    return tuple(fields)


def allocation_constraint_text(*, causal_enabled: bool, language: str) -> str:
    """Render the exact allocation rules consumed by the deterministic validator."""
    causal = (
        " causal_edge_ids: unique, nonempty, visible-ID subset including a site edge."
        if causal_enabled and language == "en"
        else " causal_edge_ids：可见 ID 的无重复非空子集，且含场地边。"
        if causal_enabled
        else ""
    )
    if language == "en":
        return (
            "site_cap_c=input. zone_budgets_c: keys=zones; each finite in "
            f"[0,{ALLOCATION_CONTRACT_SPEC['per_zone_cap_c']:g}]; sum≤cap; unused allowed. "
            "priority=permutation(zones), highest first. rationale_per_zone: keys=zones; values "
            "nonempty." + causal
        )
    return (
        "site_cap_c = 输入值。budgets/rationales 的区域键 = 配置区域。"
        f"每区额度：有限且在 [0,{ALLOCATION_CONTRACT_SPEC['per_zone_cap_c']:g}]；总和 ≤ cap，允许未用满。"
        "priority：区域全排列，优先级从高到低。理由不能为空。" + causal
    )
