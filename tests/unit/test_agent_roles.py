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
    ("insight", "expected"),
    [
        (
            "PMV 1.0125 increased. Cost 0.0 remained low.",
            "PMV 1.0125 increased. Cost 0.0 remained low.",
        ),
        ("第一句包含 1.0125。第二句包含 0.0。", "第一句包含 1.0125。第二句包含 0.0。"),
        ("one line\nsecond line", "one line second line"),
    ],
)
def test_clean_insight_preserves_multiple_sentences_and_normalizes_space(
    insight: str, expected: str
) -> None:
    assert clean_insight(insight) == expected


def test_clean_insight_rejects_non_string_input() -> None:
    assert clean_insight(1.0125) is None


def test_reflector_off_contract_accepts_one_lesson_per_zone() -> None:
    reflector = Reflector(
        StaticModelClient(
            json.dumps(
                {
                    "hourly_lessons": [
                        {
                            "zone": "zone1",
                            "lesson": "PMV 1.0125 and cost 0.0 remained stable.",
                        }
                    ]
                }
            )
        )
    )
    result = asyncio.run(
        reflector.summarize(
            context=ModelCallContext(0, 3, 0),
            user="CURRENT HOUR DETERMINISTIC CAO",
            causal_enabled=True,
            thinking_mode="disabled",
            zones=["zone1"],
        )
    )
    assert result.clean
    assert result.lessons == {"zone1": "PMV 1.0125 and cost 0.0 remained stable."}
    assert result.operations == {}


def test_reflector_memory_contract_is_structured_and_zone_isolated() -> None:
    reflector = Reflector(
        StaticModelClient(
            json.dumps(
                {
                    "hourly_lessons": [
                        {"zone": "zone1", "lesson": "The zone retained heat."},
                        {"zone": "zone2", "lesson": "The response stayed stable."},
                    ],
                    "memory_operations": [
                        {
                            "zone": "zone1",
                            "op": "add",
                            "regime": "steady_state_occupancy",
                            "experience": "Cooling response is gradual during sustained occupancy.",
                        },
                        {"zone": "zone2", "op": "invalid"},
                    ],
                }
            )
        )
    )
    result = asyncio.run(
        reflector.summarize(
            context=ModelCallContext(0, 3, 0),
            user="CURRENT HOUR DETERMINISTIC CAO",
            causal_enabled=True,
            thinking_mode="disabled",
            zones=["zone1", "zone2"],
            long_term_memory=True,
        )
    )
    assert result.lessons == {
        "zone1": "The zone retained heat.",
        "zone2": "The response stayed stable.",
    }
    assert result.operations == {
        "zone1": {
            "zone": "zone1",
            "op": "add",
            "regime": "steady_state_occupancy",
            "experience": "Cooling response is gradual during sustained occupancy.",
        }
    }
    assert {issue["code"] for issue in result.issues} == {
        "invalid_operation_shape",
        "missing_memory_operation",
    }


def test_reflector_rejects_wrong_root_for_active_mode() -> None:
    reflector = Reflector(
        StaticModelClient(
            json.dumps({"hourly_lessons": [{"zone": "zone1", "lesson": "Only a Lesson."}]})
        )
    )
    with pytest.raises(ModelContractError, match="active root contract"):
        asyncio.run(
            reflector.summarize(
                context=ModelCallContext(0, 3, 0),
                user="CURRENT HOUR DETERMINISTIC CAO",
                causal_enabled=True,
                thinking_mode="disabled",
                zones=["zone1"],
                long_term_memory=True,
            )
        )
