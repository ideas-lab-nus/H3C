from __future__ import annotations

import asyncio
import json

import pytest

from h3c.agents.prompts import Role
from h3c.agents.roles import ModelCallContext, ModelContractError, Reflector, clean_insight


class StaticModelClient:
    def __init__(self, output: str) -> None:
        self.output = output

    async def complete(
        self,
        *,
        context: ModelCallContext,
        role: Role,
        system: str,
        user: str,
        thinking_mode: str,
    ) -> str:
        del context, role, system, user, thinking_mode
        return self.output


@pytest.mark.parametrize(
    "insight",
    [
        "PMV 1.0125 and cost 0.0 remained stable.",
        "PMV -0.25 remained stable",
        "区域 PMV 为 1.0125，成本为 0.0。",
    ],
)
def test_clean_insight_accepts_one_sentence_with_decimal_points(insight: str) -> None:
    assert clean_insight(insight) == insight


@pytest.mark.parametrize(
    "insight",
    [
        "PMV 1.0125 increased. Cost 0.0 remained low.",
        "第一句包含 1.0125。第二句包含 0.0。",
        "One sentence ended. trailing fragment",
        "one line\nsecond line",
    ],
)
def test_clean_insight_rejects_multiple_sentences_or_lines(insight: str) -> None:
    assert clean_insight(insight) is None


def test_clean_insight_rejects_non_string_input() -> None:
    assert clean_insight(1.0125) is None


def test_reflector_contract_accepts_decimal_insight_without_coercion() -> None:
    output = json.dumps(
        {
            "pairs": [
                {
                    "zone": "zone1",
                    "insight_text": "PMV 1.0125 and cost 0.0 remained stable.",
                }
            ]
        }
    )
    reflector = Reflector(StaticModelClient(output))
    insights = asyncio.run(
        reflector.summarize(
            context=ModelCallContext(0, 3, 0),
            user="CURRENT HOUR RESULTS",
            causal_enabled=True,
            thinking_mode="disabled",
            zones=["zone1"],
        )
    )
    assert insights == [
        {"zone": "zone1", "insight_text": "PMV 1.0125 and cost 0.0 remained stable."}
    ]
def test_experimental_reflector_requires_one_card_for_every_zone_without_length_gate() -> None:
    long_card = "Observed relation " + "x" * 1000
    reflector = Reflector(
        StaticModelClient(
            json.dumps(
                {
                    "pairs": [
                        {"zone": "zone1", "insight_text": long_card},
                        {"zone": "zone2", "insight_text": "Stable relation"},
                    ]
                }
            )
        )
    )
    insights = asyncio.run(
        reflector.summarize(
            context=ModelCallContext(0, 3, 0),
            user="CURRENT HOUR RESULTS",
            causal_enabled=True,
            thinking_mode="disabled",
            zones=["zone1", "zone2"],
            reflector_long_term_memory=True,
        )
    )
    assert insights[0]["insight_text"] == long_card

    incomplete = Reflector(
        StaticModelClient(json.dumps({"pairs": [{"zone": "zone1", "insight_text": "Only one"}]}))
    )
    with pytest.raises(ModelContractError, match="exactly one card"):
        asyncio.run(
            incomplete.summarize(
                context=ModelCallContext(0, 3, 0),
                user="CURRENT HOUR RESULTS",
                causal_enabled=True,
                thinking_mode="disabled",
                zones=["zone1", "zone2"],
                reflector_long_term_memory=True,
            )
        )
