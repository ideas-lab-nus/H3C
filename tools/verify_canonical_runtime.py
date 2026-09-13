"""Verify that one target checkout is using the maintained H3C environment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import h3c


def _venv_interpreter(worktree: Path) -> Path:
    relative = Path("Scripts/python.exe") if sys.platform == "win32" else Path("bin/python")
    return (worktree / ".venv" / relative).resolve()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-worktree", type=Path, required=True)
    parser.add_argument("--maintained-worktree", type=Path, required=True)
    arguments = parser.parse_args()
    target = arguments.target_worktree.resolve()
    maintained = arguments.maintained_worktree.resolve()
    maintained_interpreter = _venv_interpreter(maintained)
    imported = Path(str(h3c.__file__)).resolve()
    target_source = (target / "src").resolve()
    checks = {
        "maintained_interpreter": Path(sys.executable).resolve() == maintained_interpreter,
        "target_import": imported.is_relative_to(target_source),
        "maintained_lock_exists": (maintained / "uv.lock").is_file(),
        "target_lock_exists": (target / "uv.lock").is_file(),
        "lock_compatible": False,
    }
    if checks["maintained_lock_exists"] and checks["target_lock_exists"]:
        checks["lock_compatible"] = (maintained / "uv.lock").read_bytes() == (
            target / "uv.lock"
        ).read_bytes()
    result = {
        "runtime_environment_schema": "h3c_canonical_runtime_verification",
        "schema_version": 1,
        "maintained_worktree": str(maintained),
        "maintained_interpreter": str(maintained_interpreter),
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
