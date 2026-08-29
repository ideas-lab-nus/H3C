"""Command-line interface for independent H3C baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from h3c.experiments.profiles import load_profile
from h3c_baselines.configuration import (
    BaselineRunPlan,
    formal_evaluation_plans,
)
from h3c_baselines.models import verify_all_checkpoints
from h3c_baselines.outputs.reporting import generate_report
from h3c_baselines.outputs.verification import verify_baseline_run
from h3c_baselines.runtime.runner import (
    execute_baseline_plans,
    execute_formal_suite,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="h3c-baseline")
    commands = parser.add_subparsers(dest="command", required=True)
    models = commands.add_parser("models", help="inspect frozen DRL checkpoints")
    model_commands = models.add_subparsers(dest="models_command", required=True)
    verify_models = model_commands.add_parser("verify")
    verify_models.add_argument("--identity-only", action="store_true")
    run = commands.add_parser("run", help="resolve or execute one formal baseline")
    run.add_argument("--case", required=True, choices=("SZ_Air", "MZ_Hydro", "MZ_Air"))
    run.add_argument(
        "--controller",
        required=True,
        choices=("basic-rbc", "enhanced-rbc", "c-drl", "h-drl"),
    )
    run.add_argument("--execute", action="store_true")
    suite = commands.add_parser("suite", help="resolve or execute a registered suite")
    suite.add_argument("name", choices=("formal",))
    suite.add_argument("--execute", action="store_true")
    verify = commands.add_parser("verify")
    verify.add_argument("run_directory", type=Path)
    report = commands.add_parser("report")
    report.add_argument("source", type=Path)
    return parser


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _verify_output(path: Path) -> dict[str, Any]:
    return verify_baseline_run(path)


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command == "models":
        _print(verify_all_checkpoints(load_cpu=not arguments.identity_only))
        return 0
    if arguments.command == "run":
        evaluation_hours = (
            int(load_profile(arguments.case)["protocol"]["formal_evaluation_days"]) * 24
        )
        plan = BaselineRunPlan(arguments.case, arguments.controller, evaluation_hours)
        if not arguments.execute:
            _print({"execution": False, "plan": plan.resolved()})
            return 0
        _print(execute_baseline_plans([plan], suite="manual"))
        return 0
    if arguments.command == "suite":
        plans = formal_evaluation_plans()
        dry = {
            "execution": False,
            "suite": arguments.name,
            "evaluation_runs": [plan.resolved() for plan in plans],
        }
        if not arguments.execute:
            _print(dry)
            return 0
        _print(execute_formal_suite())
        return 0
    if arguments.command == "verify":
        result = _verify_output(arguments.run_directory.resolve())
        _print(result)
        return 0 if result["execution_integrity"] else 1
    if arguments.command == "report":
        _print(generate_report(arguments.source))
        return 0
    raise AssertionError("unreachable baseline command")


if __name__ == "__main__":
    raise SystemExit(main())
