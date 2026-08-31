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

DEFAULT_PER_ZONE_RESERVED_CAP_C = 5.0

ALLOCATION_CONTRACT_SPEC: dict[str, Any] = {
    "fields": ("site_cap_c", "zone_budgets_c", "priority", "rationale_per_zone"),
    "causal_field": "causal_edge_ids",
    "per_zone_reserved_cap_field": "per_zone_reserved_cap_c",
    "site_cap_rule": "must_equal_supplied_site_cap",
    "zone_set_rule": "all_and_only_configured_zones",
    "budget_rule": "finite_nonnegative_each_and_sum_not_above_site_cap",
    "site_cap_need_not_be_fully_allocated": True,
    "priority_rule": "each_configured_zone_exactly_once_in_descending_priority",
    "rationale_rule": "all_and_only_configured_zones_with_nonempty_strings",
    "causal_rule": (
        "unique_nonempty_subset_of_visible_ids_including_an_edge_targeting_power_meters"
    ),
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
    "identifier_semantics": {
        "add_rule": "rule.id must be new",
        "replace_rule": "rule.id must already exist",
        "remove_rule": "id must already exist",
        "move_rule": "id must already exist",
    },
    "index_semantics": {
        "add_rule.index": "zero-based integer in [0, number of current rules]; omitted means append",
        "move_rule.to_index": "zero-based integer in [0, number of current rules - 1]",
    },
    "then_value_semantics": (
        'finite number, {"param":name}, or {"neg_param":name}; hold_setpoint has no value'
    ),
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
        "Edits also require causal_edge_ids: unique, nonempty visible IDs.\n"
        if causal_enabled and language == "en"
        else "修改类操作还需 causal_edge_ids：当前可见 ID 的无重复非空列表。\n"
        if causal_enabled
        else ""
    )
    intro = (
        "patch contains exactly one operation. Common fields: op, rationale.\n"
        if language == "en"
        else "patch 仅含一个 operation；公共字段：op、rationale。\n"
    )
    operation_rows = []
    for operation in PATCH_OPERATIONS:
        contract = _PATCH_CONTRACT["operations"][operation]
        additional = [
            field
            for field in contract["required"]
            if field not in {"op", "rationale", "causal_edge_ids"}
        ]
        required_text = ",".join(additional) or "none"
        optional_text = ",".join(contract["optional"])
        suffix = f"; optional={optional_text}" if optional_text else ""
        operation_rows.append(f"{operation}: required={required_text}{suffix}")
    operation_table = "Operations:\n" + "\n".join(operation_rows) + "\n"
    rule = (
        "rule={id,when:[{field,op,value}],then:{op,value?}}."
        if language == "en"
        else "rule={id,when:[{field,op,value}],then:{op,value?}}。"
    )
    semantics = _PATCH_CONTRACT
    if language == "en":
        detail = (
            " IDs: add=new rule.id; replace=existing rule.id; remove/move=existing id. "
            "Zero-based indices: add index 0..N (default N); move to_index 0..N-1. "
            'then.value: finite number | {"param":name} | {"neg_param":name}; omit for '
            "hold_setpoint."
        )
    else:
        detail = (
            " ID：add 用新 rule.id；replace 用已有 rule.id；remove/move 用已有 id。"
            "索引从 0 开始：add index 为 0..N（默认 N）；move to_index 为 0..N-1。"
            'then.value：有限数值 | {"param":name} | {"neg_param":name}；hold_setpoint 省略 value。'
        )
    if not semantics["identifier_semantics"] or not semantics["index_semantics"]:
        raise ValueError("patch contract semantics are incomplete")
    return intro + causal_line + operation_table + rule + detail


def allocation_contract(*, causal_enabled: bool = True) -> tuple[str, ...]:
    fields = list(ALLOCATION_CONTRACT_SPEC["fields"])
    if causal_enabled:
        fields.append(str(ALLOCATION_CONTRACT_SPEC["causal_field"]))
    return tuple(fields)


def allocation_constraint_text(*, causal_enabled: bool, language: str) -> str:
    """Render the exact allocation rules consumed by the deterministic validator."""
    causal = (
        " causal_edge_ids: unique, nonempty, visible-ID subset including at least one visible "
        "edge with target=power_meters."
        if causal_enabled and language == "en"
        else " causal_edge_ids：可见 ID 的无重复非空子集，且至少包含一条 "
        "target=power_meters 的可见边。"
        if causal_enabled
        else ""
    )
    if language == "en":
        return (
            "site_cap_c=input. zone_budgets_c: keys=zones; each finite in "
            "[0,per_zone_reserved_cap_c]; sum≤cap; unused allowed. "
            "priority=permutation(zones), highest first. rationale_per_zone: keys=zones; values "
            "nonempty." + causal
        )
    return (
        "site_cap_c = 输入值。budgets/rationales 的区域键 = 配置区域。"
        "每区额度：有限且在 [0,per_zone_reserved_cap_c]；总和 ≤ cap，允许未用满。"
        "priority：区域全排列，优先级从高到低。理由不能为空。" + causal
    )
