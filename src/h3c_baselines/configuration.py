"""Typed baseline plans and the frozen formal matrix."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from h3c.experiments.profiles import load_profile, repository_root

CONTROLLERS = ("basic-rbc", "enhanced-rbc", "c-drl", "h-drl", "linear-mpc")
CONDITIONING_MODES = ("explicit_vanilla_prefix", "legacy_internal_warmup")


def _merge_profile(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and value.get("__replace__") is True:
            result[key] = deepcopy(
                {name: item for name, item in value.items() if name != "__replace__"}
            )
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_profile(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


@dataclass(frozen=True)
class BaselineRunPlan:
    case: str
    controller: str
    evaluation_hours: int = 168
    conditioning_mode: str = "explicit_vanilla_prefix"
    profile_overrides: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.controller not in CONTROLLERS:
            raise ValueError(f"unknown baseline controller: {self.controller}")
        if self.evaluation_hours <= 0 or self.evaluation_hours > 168:
            raise ValueError("evaluation hours must be in [1, 168]")
        if self.conditioning_mode not in CONDITIONING_MODES:
            raise ValueError(f"unknown conditioning mode: {self.conditioning_mode}")
        profile = load_profile(self.case)
        if self.controller == "h-drl" and len(profile["zones"]) == 1:
            raise ValueError("H-DRL is not defined for the single-zone case")

    def resolved(self) -> dict[str, Any]:
        overrides = deepcopy(self.profile_overrides or {})
        profile = _merge_profile(load_profile(self.case), overrides)
        value = {
            "schema": "h3c_baseline_run_plan",
            "schema_version": 1,
            "case": self.case,
            "controller": self.controller,
            "evaluation_hours": self.evaluation_hours,
            "conditioning_mode": self.conditioning_mode,
            "profile_overrides": overrides,
            "case_profile": profile,
        }
        value["plan_identity"] = hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return value


def load_formal_suite(path: Path | None = None) -> dict[str, Any]:
    source = path or repository_root() / "configs" / "baselines" / "formal_drl.json"
    value = cast(dict[str, Any], json.loads(source.read_text(encoding="utf-8")))
    if value.get("schema") != "h3c_baseline_suite" or value.get("name") not in {
        "formal-drl",
        "formal-7d",
    }:
        raise ValueError("baseline suite schema is invalid")
    return value


def load_mpc_suite() -> dict[str, Any]:
    """Load the retained optional MPC contract without adding it to the DRL benchmark."""
    return load_formal_suite(repository_root() / "configs" / "baselines" / "formal_7d.json")


def load_legacy_replay_suite() -> dict[str, Any]:
    source = repository_root() / "configs" / "baselines" / "legacy_replay.json"
    value = cast(dict[str, Any], json.loads(source.read_text(encoding="utf-8")))
    if (
        value.get("schema") != "h3c_baseline_suite"
        or value.get("schema_version") != 1
        or value.get("name") != "legacy-replay"
        or value.get("conditioning_mode") != "legacy_internal_warmup"
    ):
        raise ValueError("legacy replay suite schema is invalid")
    return value


def formal_evaluation_plans() -> list[BaselineRunPlan]:
    suite = load_formal_suite()
    return [
        BaselineRunPlan(
            case=case,
            controller=controller,
            evaluation_hours=int(load_profile(case)["protocol"]["formal_evaluation_days"]) * 24,
        )
        for case in suite["case_order"]
        for controller in suite["controller_order"][case]
    ]


def legacy_replay_plans() -> list[BaselineRunPlan]:
    suite = load_legacy_replay_suite()
    overrides = suite.get("profile_overrides", {})
    return [
        BaselineRunPlan(
            case=case,
            controller=controller,
            evaluation_hours=int(suite["evaluation_hours"][case]),
            conditioning_mode=str(suite["conditioning_mode"]),
            profile_overrides=deepcopy(overrides.get(case, {})),
        )
        for case in suite["case_order"]
        for controller in suite["controller_order"][case]
    ]


def formal_identification_cases() -> list[tuple[str, int]]:
    suite = load_formal_suite()
    identification_days = suite.get("mpc_identification_days", {})
    return [
        (case, int(identification_days[case]))
        for case in suite["case_order"]
        if "linear-mpc" in suite["controller_order"][case]
    ]
