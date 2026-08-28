from __future__ import annotations

import copy
from typing import Any

import pytest

from h3c.offline.contracts import OfflineContractError
from h3c.offline.model import validate_wire_request


def test_offline_wire_request_requires_thinking_low_without_sampling() -> None:
    request = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "test"}],
        "reasoning_effort": "low",
    }
    assert validate_wire_request(request) == request


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reasoning_effort", None),
        ("reasoning_effort", "medium"),
        ("temperature", 0),
        ("top_p", 1),
    ],
)
def test_offline_wire_request_fail_closed_counterexamples(field: str, value: object) -> None:
    request: dict[str, Any] = {"model": "m", "messages": [], "reasoning_effort": "low"}
    candidate = copy.deepcopy(request)
    if value is None:
        candidate.pop(field)
    else:
        candidate[field] = value
    with pytest.raises(OfflineContractError):
        validate_wire_request(candidate)
