"""Small evidence-integrity helpers shared by baseline run types."""

from __future__ import annotations

import os
from pathlib import Path

from h3c.experiments.settings import load_runtime_contract


def secret_occurrences(output_dir: Path) -> int:
    """Count the configured model secret only in the newly generated output tree."""
    environment_name = load_runtime_contract()["model"]["api_key_environment_variable"]
    secret = os.environ.get(environment_name, "")
    if not secret:
        return 0
    count = 0
    for path in output_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".csv", ".txt"}:
            count += path.read_text(encoding="utf-8", errors="ignore").count(secret)
    return count
