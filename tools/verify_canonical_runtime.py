"""Verify that one target checkout is using the maintained H3C environment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import h3c

CANONICAL_WORKTREE = Path(r"D:\NUS\Paper\01-Heriachical Control\H3C_CAOL_Final_Worktree").resolve()
CANONICAL_INTERPRETER = (CANONICAL_WORKTREE / ".venv" / "Scripts" / "python.exe").resolve()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-worktree", type=Path, required=True)
    arguments = parser.parse_args()
    target = arguments.target_worktree.resolve()
    imported = Path(str(h3c.__file__)).resolve()
    target_source = (target / "src").resolve()
    checks = {
        "canonical_interpreter": Path(sys.executable).resolve() == CANONICAL_INTERPRETER,
        "target_import": imported.is_relative_to(target_source),
        "canonical_lock_exists": (CANONICAL_WORKTREE / "uv.lock").is_file(),
        "target_lock_exists": (target / "uv.lock").is_file(),
        "lock_compatible": False,
    }
    if checks["canonical_lock_exists"] and checks["target_lock_exists"]:
        checks["lock_compatible"] = (CANONICAL_WORKTREE / "uv.lock").read_bytes() == (
            target / "uv.lock"
        ).read_bytes()
    result = {
        "runtime_environment_schema": "h3c_canonical_runtime_verification",
        "schema_version": 1,
        "canonical_worktree": str(CANONICAL_WORKTREE),
        "canonical_interpreter": str(CANONICAL_INTERPRETER),
        "target_worktree": str(target),
        "imported_h3c": str(imported),
        "checks": checks,
        "passed": all(checks.values()),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
