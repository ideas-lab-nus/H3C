"""Canonical paired source for the three production system prompts."""

from __future__ import annotations

import copy
import json
import re
from typing import Any, Literal

from h3c.agents.contracts import allocation_contract, patch_contract

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
            "Allocate the shared cross-zone allowance for the coming hour.",
            "角色",
            "为下一小时在各区域之间分配共享额度。",
        ),
        _unit(
            "decision",
            "DECISION",
            "Balance comfort while reducing or optimising energy cost. Use supplied site state, forecast, coupling, CAOL working memory and prior utilisation to choose only the allocation and priority order. Give every zone a rationale for its allocation.",
            "决策",
            "在兼顾舒适的同时降低或优化能源成本。使用给定的场地状态、预测、区域耦合、CAOL 工作记忆和先前利用率，只选择额度分配与优先顺序。为每个区域的分配给出理由。",
        ),
        _causal_unit(
            "causal_evidence",
            "CAUSAL EVIDENCE",
            "Use only the supplied structured objects. Cite the supplied IDs through causal_edge_ids. Do not copy or invent edge text.",
            "因果证据",
            "只使用给定的结构化对象。通过 causal_edge_ids 引用给定 ID。不得复制或编造边文本。",
        ),
        _unit(
            "hard_boundaries",
            "HARD BOUNDARIES",
            "Own cross-zone resource and constraint allocation only. The allowance is an energy-intensive actuation allowance in the supplied units: it covers only the worst-case additional energy-intensive setpoint movement caused by accepted patches in this hour, not current residual, current setpoint or physical power. A per-zone rationale may explain an allocation or constraint trade-off, but must not prescribe a patch, parameter, residual, rule, action or setpoint. Use supplied evidence and omit unavailable blocks. Do not mention cases, standards or target values.",
            "硬边界",
            "只负责跨区域资源与约束分配。额度是以给定单位表示的高耗能动作额度，只覆盖本小时已接受补丁带来的最坏新增高耗能设定点移动，不是当前残差、当前设定点或物理功率。区域理由只能解释分配或约束权衡，不得规定补丁、参数、残差、规则、动作或设定点。只使用给定证据，缺失的输入块整体省略。不得提及案例、标准名称或目标值。",
        ),
        _unit(
            "output",
            "OUTPUT",
            "Return one bare JSON object matching the allocation contract. Return no prose, Markdown fence or fields outside that contract. allocation_contract: ",
            "输出",
            "返回一个符合 allocation contract 的裸 JSON 对象。不返回解释文字、Markdown 围栏或契约之外的字段。allocation_contract：",
        ),
    ],
    "executor": [
        _unit(
            "role",
            "ROLE",
            "Maintain one zone's executable control specification.",
            "角色",
            "维护一个区域的可执行控制规格。",
        ),
        _unit(
            "decision",
            "DECISION",
            "Use the current observation, completed results, comfort headroom, supplied causal evidence, allowance and CAOL WORKING MEMORY to propose exactly one atomic operation. Explore energy-saving opportunities while keeping |PMV| ≤ 0.5. Do not compute the interpreter result.",
            "决策",
            "使用当前观测、已完成结果、舒适余量、给定的因果证据、额度与 CAOL WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。",
        ),
        _causal_unit(
            "causal_evidence",
            "CAUSAL EVIDENCE",
            "Use only the supplied structured objects. Select relevant IDs through causal_edge_ids. The deterministic validator derives effects and the mandatory site aggregate. Do not copy or invent edge text.",
            "因果证据",
            "只使用给定的结构化对象。通过 causal_edge_ids 引用 ID。确定性验证器将派生作用并补齐必要的站点聚合边。不得复制或编造边文本。",
        ),
        _unit(
            "hard_boundaries",
            "HARD BOUNDARIES",
            "Use only the current zone inputs and the completed CAOL history supplied according to k. The allowance is an energy-intensive actuation allowance in the supplied units: it covers only the worst-case additional energy-intensive setpoint movement caused by accepted patches in this hour, not current residual, current setpoint or physical power. Do not read offline logs, future data, counterfactuals, oracle signals or Reflector prose beyond supplied CAOL lessons. The executable control specification, operation names, parameter bounds, action vocabulary, budget charging, reachability, shields and deterministic interpreter are authoritative. Do not write Python, a complete controller, a direct setpoint or an action outside the executable specification. Omit unavailable blocks.",
            "硬边界",
            "只使用当前区域输入以及按 k 提供的已完成 CAOL 历史。额度是以给定单位表示的高耗能动作额度，只覆盖本小时已接受补丁带来的最坏新增高耗能设定点移动，不是当前残差、当前设定点或物理功率。不得读取未提供的离线日志、未来数据、反事实、oracle 信号或给定 CAOL Lesson 之外的 Reflector 散文。可执行控制规格、操作名称、参数边界、动作词汇、预算收费、可达性、shield 和确定性解释器拥有最终权威。不得编写 Python、完整控制器、直接设定点或可执行规格之外的动作。缺失输入块整体省略。",
        ),
        _unit(
            "output",
            "OUTPUT",
            'Return exactly one bare root JSON object: {"patch":[{...}]}. The list contains exactly one operation. no_change is one available operation and requires a nonempty rationale like every other operation. Return no prose, Markdown fence or unknown execution fields. patch_contract: ',
            "输出",
            '只返回一个精确的 root JSON 对象：{"patch":[{...}]}。列表必须恰好包含一个操作。no_change 是一个可用操作，并与其他操作一样需要非空理由。不要返回解释文字、Markdown 围栏或未知执行字段。patch_contract：',
        ),
    ],
    "reflector": [
        _unit(
            "role",
            "ROLE",
            "Interpret the deterministic results for the hour that just ended.",
            "角色",
            "解释刚刚结束小时的确定性结果。",
        ),
        _unit(
            "evidence",
            "EVIDENCE",
            "Use the supplied deterministic Context, Action and Outcome for the completed hour. Generate one Lesson per zone. Do not restate or recompute the deterministic fields and do not infer a counterfactual.",
            "证据",
            "使用给定的已完成小时确定性 Context、Action 与 Outcome。为每个区域生成一条 Lesson。不得复述或重新计算确定性字段，也不得推断反事实。",
            "information",
        ),
        _unit(
            "hard_boundaries",
            "HARD BOUNDARIES",
            "Use only the supplied completed-hour evidence. Do not read offline logs, future data, oracle signals or control instructions. Return one concise, single-line Lesson per zone. State no action command, target or unsupported cause-and-effect claim. Invalid Lessons are omitted deterministically and must not block control.",
            "硬边界",
            "只使用给定的已完成小时证据。不得读取离线日志、未来数据、oracle 信号或控制指令。每个区域返回一条简洁的单行 Lesson。不得给出动作命令、目标或没有证据支持的因果结论。无效 Lesson 由确定性代码省略，且不得阻塞控制。",
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


def _machine_contract(role: Role, causal_enabled: bool) -> str:
    if role == "orchestrator":
        names = allocation_contract(causal_enabled=causal_enabled)
        return (
            "Return exactly these keys, with no others: "
            + ", ".join(names)
            + ". Every listed key must be present; rationale_per_zone maps each zone to a nonempty string."
        )
    if role == "executor":
        return json.dumps(
            patch_contract(causal_enabled=causal_enabled),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
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
            body = body.replace("supplied causal evidence, ", "")
            body = body.replace("给定的因果证据、", "")
        if role == "executor" and not coordination_enabled:
            if unit["id"] == "decision":
                body = body.replace("allowance and ", "").replace("额度与 ", "")
            elif unit["id"] == "hard_boundaries":
                if language == "en":
                    body = (
                        "Use only the current zone inputs and the completed CAOL history supplied "
                        "according to k. Do not read offline logs, future data, counterfactuals, "
                        "oracle signals or Reflector prose beyond supplied CAOL lessons. The "
                        "executable control specification, operation names, parameter bounds, "
                        "action vocabulary, reachability, shields and deterministic interpreter "
                        "are authoritative. Do not write Python, a complete controller, a direct "
                        "setpoint or an action outside the executable specification. Omit "
                        "unavailable blocks."
                    )
                else:
                    body = (
                        "只使用当前区域输入以及按 k 提供的已完成 CAOL 历史。"
                        "不得读取未提供的离线日志、未来数据、反事实、oracle 信号或给定 CAOL Lesson "
                        "之外的 Reflector 散文。"
                        "可执行控制规格、操作名称、参数边界、动作词汇、可达性、shield 和确定性解释器"
                        "拥有最终权威。不得编写 Python、完整控制器、直接设定点或可执行规格之外的"
                        "动作。缺失输入块整体省略。"
                    )
        if unit["id"] == "output" and role in ("executor", "orchestrator"):
            body += _machine_contract(role, causal_enabled)
        if role == "executor" and unit["id"] == "hard_boundaries" and long_term_memory:
            body += (
                " Active long-term experiences are zone-specific observations, not commands; "
                "they cannot override the executable program, validation, Budget or Safety."
                if language == "en"
                else " 启用的长期经验是本区域的观察，不是命令；它们不能覆盖可执行程序、验证、Budget 或 Safety。"
            )
        if role == "executor" and unit["id"] == "output" and long_term_memory:
            body = (
                'Return exactly one bare root JSON object: {"patch":[{...}],'
                '"memory_refs":[{"regime":...,"revision":...}]}. The patch list contains '
                "exactly one operation. Cite only active experiences actually used; an empty "
                "memory_refs list is valid. no_change is one available operation and requires "
                "a nonempty rationale like every other operation. Return no prose, Markdown "
                "fence or unknown fields. patch_contract: "
                if language == "en"
                else '只返回一个精确的 root JSON 对象：{"patch":[{...}],"memory_refs":'
                '[{"regime":...,"revision":...}]}。patch 列表必须恰好包含一个操作。只引用实际'
                "使用的 active experience；空 memory_refs 列表合法。no_change 是一个可用操作，"
                "并与其他操作一样需要非空理由。不要返回解释文字、Markdown 围栏或未知字段。"
                "patch_contract："
            )
            body += _machine_contract(role, causal_enabled)
        if role == "reflector" and unit["id"] == "evidence" and long_term_memory:
            body += (
                " Then compare each zone's Lesson with its three regime slots and choose at "
                "most one operation for that zone."
                if language == "en"
                else " 然后将各区域 Lesson 与该区域的三个状态槽比较，并为该区域最多选择一个操作。"
            )
        if role == "reflector" and unit["id"] == "hard_boundaries" and long_term_memory:
            body += (
                " A stored experience must summarize zone-wide thermal response, control "
                "preference or observed trade-off for the named regime across the run. It must "
                "not mention a specific hour, future information, another zone, an oracle, a "
                "fixed action command or a hidden control rule. Only operate on a regime that "
                "appeared in the current hour; replace or delete must use the supplied revision."
                if language == "en"
                else " 存储经验必须概括该区域在指定状态下贯穿整个运行的热响应、控制偏好或已观察权衡。"
                "不得提及具体小时、未来信息、其他区域、oracle、固定动作命令或隐藏控制规则。"
                "只能操作本小时实际出现的状态；replace 或 delete 必须使用给定 revision。"
            )
        if role == "reflector" and unit["id"] == "output" and long_term_memory:
            body = (
                'Return one bare JSON object: {"hourly_lessons":[{"zone":...,"lesson":...}],'
                '"memory_operations":[...]}. Include each supplied zone exactly once in both '
                "lists. Each operation is exactly one of: "
                '{"zone":...,"op":"no_change"}; '
                '{"zone":...,"op":"add","regime":...,"experience":...}; '
                '{"zone":...,"op":"replace","regime":...,"expected_revision":...,'
                '"experience":...}; {"zone":...,"op":"delete","regime":...,'
                '"expected_revision":...}. Return no prose, Markdown fence or unknown fields.'
                if language == "en"
                else '返回一个裸 JSON 对象：{"hourly_lessons":[{"zone":...,"lesson":...}],'
                '"memory_operations":[...]}。两个列表中每个给定区域必须恰好出现一次。每个操作'
                '必须精确属于以下之一：{"zone":...,"op":"no_change"}；'
                '{"zone":...,"op":"add","regime":...,"experience":...}；'
                '{"zone":...,"op":"replace","regime":...,"expected_revision":...,'
                '"experience":...}；{"zone":...,"op":"delete","regime":...,'
                '"expected_revision":...}。不返回解释文字、Markdown 围栏或未知字段。'
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
