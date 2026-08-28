from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repository_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def oracle_fixture(repository_root: Path) -> dict[str, Any]:
    value = json.loads(
        (repository_root / "tests" / "fixtures" / "oracle_equivalence.json").read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(value, dict):
        raise ValueError("oracle fixture root must be an object")
    return value


@pytest.fixture()
def canonical_program(repository_root: Path) -> dict[str, Any]:
    from h3c.control.program import load_program

    return load_program(
        repository_root / "configs" / "programs" / "canonical_cooling_program.json",
        "zone1",
    )
