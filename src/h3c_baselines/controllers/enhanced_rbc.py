"""Canonical H3C cooling program used without Agent program updates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from h3c.assurance.action import action_assurance
from h3c.control.program import load_program, run_program


class EnhancedRbcController:
    def __init__(self, zones: Sequence[str], program_path: Path) -> None:
        self.zones = tuple(zones)
        self.programs = {zone: load_program(program_path, zone) for zone in self.zones}

    def decide(
        self,
        *,
        occupancy: Mapping[str, float],
        future_occupancy: Mapping[str, Sequence[float]],
        last_setpoints_c: Mapping[str, float],
        last_pmv: Mapping[str, float],
        last_occupancy: Mapping[str, float],
    ) -> tuple[dict[str, float], dict[str, Any]]:
        setpoints: dict[str, float] = {}
        diagnostics: dict[str, Any] = {}
        for zone in self.zones:
            observation = {
                "current_occupancy": float(occupancy[zone]),
                "occ_ahead": [float(value) for value in future_occupancy[zone]],
                "last_setpoint": float(last_setpoints_c[zone]),
                "last_pmv": float(last_pmv[zone]),
                "last_occupancy": float(last_occupancy[zone]),
            }
            proposal = run_program(self.programs[zone], observation)
            setpoint, assurance = action_assurance(proposal, observation)
            setpoints[zone] = setpoint
            diagnostics[zone] = {"interpreter": proposal, "action_assurance": assurance}
        return setpoints, diagnostics
