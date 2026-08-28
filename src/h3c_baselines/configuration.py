"""Typed baseline plans and the frozen formal matrix."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from h3c.experiments.profiles import load_profile, repository_root

CONTROLLERS = ("basic-rbc", "enhanced-rbc", "c-drl", "h-drl", "linear-mpc")


@dataclass(frozen=True)
class BaselineRunPlan:
    case: str
    controller: str
    evaluation_hours: int = 168

    def __post_init__(self) -> None:
        if self.controller not in CONTROLLERS:
            raise ValueError(f"unknown baseline controller: {self.controller}")
        if self.evaluation_hours <= 0 or self.evaluation_hours > 168:
            raise ValueError("evaluation hours must be in [1, 168]")
        profile = load_profile(self.case)
        if self.controller == "h-drl" and len(profile["zones"]) == 1:
            raise ValueError("H-DRL is not defined for the single-zone case")

    def resolved(self) -> dict[str, Any]:
        profile = load_profile(self.case)
        value = {
            "schema": "h3c_baseline_run_plan",
            "schema_version": 1,
            "case": self.case,
            "controller": self.controller,
            "evaluation_hours": self.evaluation_hours,
            "case_profile": profile,
        }
        value["plan_identity"] = hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return value


def load_formal_suite(path: Path | None = None) -> dict[str, Any]:
    source = path or repository_root() / "configs" / "baselines" / "formal_7d.json"
    value = cast(dict[str, Any], json.loads(source.read_text(encoding="utf-8")))
    if value.get("schema") != "h3c_baseline_suite" or value.get("name") != "formal-7d":
        raise ValueError("baseline suite schema is invalid")
    return value


def formal_evaluation_plans() -> list[BaselineRunPlan]:
    suite = load_formal_suite()
    return [
        BaselineRunPlan(case=case, controller=controller)
        for case in suite["case_order"]
        for controller in suite["controller_order"][case]
    ]


def formal_identification_cases() -> list[tuple[str, int]]:
    suite = load_formal_suite()
    return [(case, int(suite["mpc_identification_days"][case])) for case in suite["case_order"]]
