"""Export or check the exact Agent matrix used by the paper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from h3c.experiments.matrix import paper_agent_matrix_payload

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reference_results" / "paper_2026" / "paper_agent_matrix.json"


def _render() -> str:
    return (
        json.dumps(
            paper_agent_matrix_payload(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    output = arguments.output.resolve()
    rendered = _render()
    if arguments.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"paper Agent matrix is stale: {output}")
        print(f"Verified paper Agent matrix: {output}")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote paper Agent matrix: {output}")


if __name__ == "__main__":
    main()
