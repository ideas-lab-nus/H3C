"""Archived DRL evaluation boundary used only by the legacy-replay suite."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from typing import Any

from h3c.runtime.comfort import ComfortModel
from h3c.runtime.protocol import ConditioningArtifactSink, ConditioningResult, PhysicalClient


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def run_legacy_internal_warmup(
    client: PhysicalClient,
    profile: Mapping[str, Any],
    artifacts: ConditioningArtifactSink,
    *,
    on_initialized: Callable[[str], None] | None = None,
) -> ConditioningResult:
    """Reproduce the archived evaluation reset without an explicit control prefix."""
    evaluation_start = int(profile["evaluation_start_day"]) * 86400
    warmup_seconds = int(profile["protocol"]["server_warmup_days"]) * 86400
    state = client.initialize(profile["testcase"], evaluation_start, warmup_seconds)
    if int(state.get("time", -1)) != evaluation_start:
        raise ValueError("legacy evaluation initialization returned the wrong time")
    test_id = client.test_id
    if not isinstance(test_id, str) or not test_id:
        raise ValueError("physical initialize did not produce a test id")
    if on_initialized is not None:
        on_initialized(test_id)
    artifacts.append_jsonl(
        "timing.jsonl",
        {
            "phase": "physical_lifecycle",
            "event": "initialized",
            "conditioning_mode": "legacy_internal_warmup",
            "time_seconds": evaluation_start,
            "warmup_period_seconds": warmup_seconds,
            "test_id": test_id,
        },
    )
    zones = tuple(str(zone) for zone in profile["zones"])
    last_setpoint = dict.fromkeys(zones, 25.0)
    last_pmv = dict.fromkeys(zones, 0.0)
    last_occupancy = dict.fromkeys(zones, 0.0)
    comfort = ComfortModel(profile["comfort"])
    boundary = {
        "physical_state": dict(state),
        "last_setpoint_c": last_setpoint,
        "last_pmv": last_pmv,
        "last_occupancy": last_occupancy,
        "clothing_insulation": comfort.clothing_insulation,
    }
    boundary_identity = hashlib.sha256(_canonical(boundary)).hexdigest()
    protocol_identity = hashlib.sha256(
        _canonical(
            {
                "mode": "legacy_internal_warmup",
                "testcase": profile["testcase"],
                "evaluation_start": evaluation_start,
                "warmup_seconds": warmup_seconds,
            }
        )
    ).hexdigest()
    artifacts.append_jsonl(
        "timing.jsonl",
        {
            "phase": "evaluation_boundary",
            "conditioning_mode": "legacy_internal_warmup",
            "boundary": boundary,
            "evaluation_boundary_identity": boundary_identity,
            "test_id": test_id,
        },
    )
    return ConditioningResult(
        state=dict(state),
        test_id=test_id,
        last_setpoint_c=last_setpoint,
        last_pmv=last_pmv,
        last_occupancy=last_occupancy,
        comfort=comfort,
        occupancy_missing_value_resolution_count=0,
        conditioning_prefix_identity=protocol_identity,
        evaluation_boundary_identity=boundary_identity,
    )
