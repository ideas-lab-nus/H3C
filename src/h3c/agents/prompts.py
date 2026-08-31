"""Canonical paired source for the three production system prompts."""

from __future__ import annotations

import copy
import re
from typing import Any, Literal

from h3c.agents.contracts import (
    allocation_constraint_text,
    allocation_contract,
    compact_patch_contract,
)

Role = Literal["orchestrator", "executor", "reflector"]
Language = Literal["en", "zh"]


def _unit(
    section_id: str,
    title_en: str,
    body_en: str,
    title_zh: str,
    body_zh: str,
    kind: str = "constraint",
) -> dict[str, str]:
    return {
        "id": section_id,
        "title_en": title_en,
        "body_en": body_en,
        "title_zh": title_zh,
        "body_zh": body_zh,
        "kind": kind,
    }


def _causal_unit(
    section_id: str,
    title_en: str,
    body_en: str,
    title_zh: str,
    body_zh: str,
) -> dict[str, str]:
    unit = _unit(
        section_id,
        title_en,
        body_en,
        title_zh,
        body_zh,
        kind="information",
    )
    unit["conditional"] = "causal"
    return unit


PAIRED_PROMPT_UNITS: dict[Role, list[dict[str, str]]] = {
    "orchestrator": [
        _unit(
            "role",
            "ROLE",
            "Allocate cross-zone allowance over action_times in control_interval.",
            "角色",
            "在 control_interval 的 action_times 上分配跨区域共享额度。",
        ),
        _unit(
            "decision",
            "DECISION",
            "Balance comfort and energy cost from the supplied state, forecast, working memory and previous Budget use. Output allocation, priority and per-zone rationales.",
            "决策",
            "使用当前状态、预测、工作记忆与上一时段 Budget，在舒适和能源成本间权衡。输出额度、优先级及每区一条额度或优先级理由。",
        ),
        _unit(
            "hard_boundaries",
            "HARD BOUNDARIES",
            "For accepted program changes, charge_c = max over proof states of max(0, setpoint_before_c - setpoint_after_c); not cumulative action, power or pre-cooling offset.",
            "硬边界",
            "Budget 只覆盖 control_interval 内获准的程序修改。charge_c = 证明状态空间中 max(0, 修改前设定点 - 修改后设定点) 的最大值；不是累计动作、功率或预冷偏移。",
        ),
        _unit(
            "output",
            "OUTPUT",
            "Bare JSON only.",
            "输出",
            "仅返回裸 JSON。",
        ),
    ],
    "executor": [
        _unit(
            "role",
            "ROLE",
            "Maintain one zone's control specification.",
            "角色",
            "维护一个区域的可执行控制规格。",
        ),
        _unit(
            "decision",
            "DECISION",
            "Use the current observation, comfort headroom, causal evidence, allowance and WORKING MEMORY to propose one atomic operation. Seek energy savings with |PMV| ≤ 0.5. Do not predict interpreter output.",
            "决策",
            "使用当前观测、舒适余量、因果证据、额度与 WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。",
        ),
        _unit(
            "hard_boundaries",
            "HARD BOUNDARIES",
            "For an accepted program change, charge_c = max over proof states of max(0, setpoint_before_c - setpoint_after_c); it is not cumulative action, power or pre-cooling offset. Edit only through the control specification and operation contract; do not output a direct setpoint.",
            "硬边界",
            "获准程序修改的 charge_c = 证明状态空间中 max(0, 修改前设定点 - 修改后设定点) 的最大值；不是累计动作、功率或预冷偏移。只通过控制规格和操作契约修改，不输出直接设定点。",
        ),
        _unit(
            "output",
            "OUTPUT",
            'Return exactly one bare root JSON object: {"patch":[{...}]}. Return no prose, Markdown fence or unknown fields. Operation contract:\n',
            "输出",
            '只返回一个精确的 root JSON 对象：{"patch":[{...}]}。不要返回解释文字、Markdown 围栏或未知字段。操作契约：\n',
        ),
    ],
    "reflector": [
        _unit(
            "role",
            "ROLE",
            "Interpret the deterministic results for the supplied completed control interval.",
            "角色",
            "解释输入中已完成控制时段的确定性结果。",
        ),
        _unit(
            "evidence",
            "EVIDENCE",
            "From each zone's completed Context, Action and Outcome, derive one Lesson that captures a useful observed relationship or trade-off for later control.",
            "证据",
            "从每个区域已完成的 Context、Action 与 Outcome 中提炼一条 Lesson，概括对后续控制有意义的已观察关系或权衡。",
            "information",
        ),
        _unit(
            "hard_boundaries",
            "HARD BOUNDARIES",
            "Ground each Lesson in the completed-interval evidence. Express an observation, relationship or trade-off rather than an action command, target or unsupported causal claim.",
            "硬边界",
            "每条 Lesson 都应基于已完成控制时段的证据，表达观察、关系或权衡，而不是动作命令、目标或无证据因果结论。",
        ),
        _unit(
            "output",
            "OUTPUT",
            'Return one bare JSON object of the form {"hourly_lessons":[{"zone":...,"lesson":...}]}. Include every supplied zone exactly once. Return no prose, Markdown fence or unknown fields.',
            "输出",
            '返回形如 {"hourly_lessons":[{"zone":...,"lesson":...}]} 的裸 JSON 对象。每个给定区域必须恰好出现一次。不返回解释文字、Markdown 围栏或未知字段。',
        ),
    ],
}


def _machine_contract(role: Role, causal_enabled: bool, language: Language) -> str:
    if role == "orchestrator":
        names = allocation_contract(causal_enabled=causal_enabled)
        prefix = " Keys exactly: " if language == "en" else " 字段仅限："
        return (
            prefix
            + ", ".join(names)
            + ". "
            + allocation_constraint_text(causal_enabled=causal_enabled, language=language)
        )
    if role == "executor":
        return compact_patch_contract(causal_enabled=causal_enabled, language=language)
    return ""


_CAUSAL_TOKENS = (
    "causal",
    "graph",
    "causal_edge_ids",
    "expected_effects",
    "derived_from_edge",
)


def assert_causal_disabled_text_clean(text: str) -> None:
    lowered = text.lower()
    leaked = [token for token in _CAUSAL_TOKENS if token in lowered]
    if re.search(r"\bce_[0-9a-f]{8}\b", text, re.IGNORECASE):
        leaked.append("edge_identifier")
    if leaked:
        raise ValueError(f"causal module text leaked in disabled prompt: {leaked}")


def system_prompt(
    role: Role,
    *,
    causal_enabled: bool = True,
    language: Language = "en",
    coordination_enabled: bool = True,
    long_term_memory: bool = False,
) -> str:
    rows: list[str] = []
    for unit in PAIRED_PROMPT_UNITS[role]:
        if unit.get("conditional") == "causal" and not causal_enabled:
            continue
        title = unit["title_en"] if language == "en" else unit["title_zh"]
        body = unit["body_en"] if language == "en" else unit["body_zh"]
        if role == "executor" and unit["id"] == "decision" and not causal_enabled:
            body = body.replace("causal evidence, ", "")
            body = body.replace("因果证据、", "")
        if role == "reflector" and unit["id"] == "hard_boundaries" and not causal_enabled:
            body = body.replace(" or unsupported causal claim", " or unsupported claim")
            body = body.replace("或无证据因果结论", "或无证据结论")
        if role == "executor" and not coordination_enabled:
            if unit["id"] == "decision":
                body = body.replace("allowance and ", "").replace("额度与 ", "")
            elif unit["id"] == "hard_boundaries":
                if language == "en":
                    body = (
                        "Operate only through the supplied control specification and operation "
                        "contract; do not write Python, a complete controller or a direct setpoint."
                    )
                else:
                    body = "只能通过给定控制规格与操作契约工作；不得编写 Python、完整控制器或直接设定点。"
        if unit["id"] == "output" and role in ("executor", "orchestrator"):
            body += _machine_contract(role, causal_enabled, language)
        if role == "executor" and unit["id"] == "output" and long_term_memory:
            body = (
                'Return bare JSON {"patch":[{...}],"memory_refs":'
                '[{"regime":...,"revision":...}]}. memory_refs cites only active experiences '
                "used and may be empty. No prose, fence or "
                "extra fields. Operation contract:\n"
                if language == "en"
                else '返回裸 JSON：{"patch":[{...}],"memory_refs":'
                '[{"regime":...,"revision":...}]}。包含一个操作。memory_refs 只引用实际使用的'
                "有效经验，也可为空。不返回解释文字、Markdown 围栏或额外字段。操作契约：\n"
            )
            body += _machine_contract(role, causal_enabled, language)
        if role == "reflector" and unit["id"] == "evidence" and long_term_memory:
            body = (
                "For each zone, derive one useful observed relationship or trade-off from "
                "completed Context, Action and Outcome. Compare it with shown eligible regime "
                "slots; select at most one memory operation."
                if language == "en"
                else "对每个区域，从已完成的 Context、Action 与 Outcome 中提炼一条有用的已观察关系"
                "或权衡；将其与展示的合格状态槽比较，并最多选择一个记忆操作。"
            )
        if role == "reflector" and unit["id"] == "hard_boundaries" and long_term_memory:
            body = (
                "Lessons are evidence-grounded observations, relationships or trade-offs, not "
                "commands, targets or unsupported claims. Experiences describe the zone's "
                "run-wide thermal response, control preference or trade-off for the named regime. "
                "Modify only a shown eligible regime; replace/delete uses its revision."
                if language == "en"
                else "Lesson 是基于证据的观察、关系或权衡，不是命令、目标或无依据结论。存储经验"
                "描述该区域在指定状态下贯穿运行的热响应、控制偏好或权衡。只修改展示的合格状态；"
                "replace/delete 使用其 revision。"
            )
        if role == "reflector" and unit["id"] == "output" and long_term_memory:
            body = (
                'Bare JSON only: {"hourly_lessons":[{"zone":...,"lesson":...}],'
                '"memory_operations":[...]}. Each zone appears once per list. Every memory '
                "operation requires zone and op; additional fields:\n"
                "| op | required |\n| --- | --- |\n| no_change | — |\n"
                "| add | regime, experience |\n| replace | regime, expected_revision, experience |\n"
                "| delete | regime, expected_revision |\nNo prose, fence or extra fields."
                if language == "en"
                else '返回裸 JSON：{"hourly_lessons":[{"zone":...,"lesson":...}],'
                '"memory_operations":[...]}；每个给定区域在两个列表中各出现一次。每个记忆操作'
                "都需要 zone 与 op，额外必填字段：\n| op | 必填 |\n| --- | --- |\n"
                "| no_change | — |\n| add | regime, experience |\n"
                "| replace | regime, expected_revision, experience |\n"
                "| delete | regime, expected_revision |\n不返回解释文字、Markdown 围栏或额外字段。"
            )
        rows.append(title + "\n" + body)
    rendered = "\n\n".join(rows) + "\n"
    if not causal_enabled:
        assert_causal_disabled_text_clean(rendered)
    return rendered


def prompt_units(role: Role | None = None) -> Any:
    return copy.deepcopy(PAIRED_PROMPT_UNITS if role is None else PAIRED_PROMPT_UNITS[role])


ORCHESTRATOR_SYSTEM_PROMPT = system_prompt("orchestrator")
EXECUTOR_SYSTEM_PROMPT = system_prompt("executor")
REFLECTOR_SYSTEM_PROMPT = system_prompt("reflector")
