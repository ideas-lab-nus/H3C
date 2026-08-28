from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from h3c.experiments.profiles import profiles
from h3c.runtime.protocol import control_input


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_case_mappings_controls_occupancy_objective_and_actions_match_oracle(
    repository_root: Path,
) -> None:
    fixture = json.loads(
        (repository_root / "tests" / "fixtures" / "oracle_equivalence.json").read_text(
            encoding="utf-8"
        )
    )["case_profiles"]
    loaded = profiles()
    assert set(loaded) == set(fixture)
    for name, expected in fixture.items():
        profile = loaded[name]
        assert profile["testcase"] == expected["testcase"]
        assert profile["evaluation_start_day"] == expected["evaluation_start_day"]
        assert list(profile["zones"]) == expected["zones"]
        assert (
            _digest({"zones": profile["zones"], "global_inputs": profile["global_inputs"]})
            == expected["mapping_sha256"]
        )
        assert _digest(profile["static_controls"]) == expected["static_controls_sha256"]
        assert _digest(profile["occupancy"]) == expected["occupancy_sha256"]
        assert _digest(profile["objective"]) == expected["objective_sha256"]
        action = control_input(profile, {zone: 24.0 for zone in profile["zones"]})
        assert _digest(action) == expected["action_at_24c_sha256"]
        for mapping in profile["zones"].values():
            assert action[mapping["cooling_setpoint_actuator"]] == 297.15
