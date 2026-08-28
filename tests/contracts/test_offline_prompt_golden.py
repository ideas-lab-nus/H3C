from __future__ import annotations

import hashlib
import json
from pathlib import Path

from h3c.offline.contracts import (
    load_onboarding_spec,
    read_text_document,
    standard_variables,
)
from h3c.offline.prompts import (
    CAUSAL_SYSTEM_PROMPT,
    MAPPING_SYSTEM_PROMPT,
    render_causal_user_prompt,
    render_mapping_user_prompt,
)


def _identity(value: str) -> dict[str, int | str]:
    encoded = value.encode("utf-8")
    return {"bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()}


def test_offline_system_and_user_prompt_golden(repository_root: Path) -> None:
    fixture_root = repository_root / "tests" / "fixtures" / "offline_prompts"
    mapping = json.loads((fixture_root / "representative_mapping.json").read_text(encoding="utf-8"))
    causal = json.loads(
        (fixture_root / "representative_causal_proposal.json").read_text(encoding="utf-8")
    )
    expected = json.loads((fixture_root / "golden_hashes.json").read_text(encoding="utf-8"))
    spec = load_onboarding_spec(
        repository_root / "configs" / "onboarding" / "example_spec.json",
        repository_root,
    )
    document = read_text_document(spec.building_document)
    assert spec.point_inventory is not None
    inventory = json.loads(spec.point_inventory.read_text(encoding="utf-8"))["points"]
    evidence = {
        source.identifier: read_text_document(source.path) for source in spec.evidence_sources
    }
    variables = standard_variables(mapping)
    rendered = {
        "mapping_system": MAPPING_SYSTEM_PROMPT,
        "mapping_user_initial": render_mapping_user_prompt(spec, document, inventory),
        "mapping_user_revision": render_mapping_user_prompt(
            spec,
            document,
            inventory,
            previous_proposal=mapping,
            reviewer_feedback="Use the documented office zone label.",
        ),
        "causal_system": CAUSAL_SYSTEM_PROMPT,
        "causal_user_initial": render_causal_user_prompt(spec, variables, evidence),
        "causal_user_revision": render_causal_user_prompt(
            spec,
            variables,
            evidence,
            previous_proposal=causal,
            reviewer_feedback="Cite the physics note for the delayed response.",
        ),
    }
    assert expected["schema"] == "h3c_offline_prompt_golden"
    assert expected["version"] == 1
    assert {name: _identity(value) for name, value in rendered.items()} == {
        name: expected[name] for name in rendered
    }
