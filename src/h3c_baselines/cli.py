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
    formal_identification_cases,
    legacy_replay_plans,
)
from h3c_baselines.models import verify_all_checkpoints
from h3c_baselines.mpc.identification import verify_identification_run
from h3c_baselines.outputs.reporting import generate_report
from h3c_baselines.outputs.verification import verify_baseline_run
from h3c_baselines.runtime.runner import (
    execute_baseline_plans,
    execute_formal_suite,
    execute_legacy_replay_suite,
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
        choices=("basic-rbc", "enhanced-rbc", "c-drl", "h-drl", "linear-mpc"),
    )
    run.add_argument(
        "--mpc-identification",
        type=Path,
        help="completed identification run required when executing linear MPC",
    )
    run.add_argument("--execute", action="store_true")
    suite = commands.add_parser("suite", help="resolve or execute a registered suite")
    suite.add_argument("name", choices=("formal-drl", "legacy-replay"))
    suite.add_argument("--execute", action="store_true")
    verify = commands.add_parser("verify")
    verify.add_argument("run_directory", type=Path)
    report = commands.add_parser("report")
    report.add_argument("source", type=Path)
    return parser


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _verify_output(path: Path) -> dict[str, Any]:
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") == "h3c_mpc_identification_manifest":
        return verify_identification_run(path)
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
        identification_dirs: dict[str, Path] = {}
        if plan.controller == "linear-mpc":
            if arguments.mpc_identification is None:
                raise ValueError("--mpc-identification is required to execute linear MPC")
            identification = arguments.mpc_identification.resolve()
            verified = verify_identification_run(identification)
            if verified["execution_integrity"] is not True:
                raise ValueError("the selected MPC identification run is invalid")
            identification_dirs[plan.case] = identification
        _print(
            execute_baseline_plans(
                [plan], suite="manual", mpc_identification_dirs=identification_dirs
            )
        )
        return 0
    if arguments.command == "suite":
        plans = (
            legacy_replay_plans()
            if arguments.name == "legacy-replay"
            else formal_evaluation_plans()
        )
        dry = {
            "execution": False,
            "suite": arguments.name,
            "identification_runs": [
                {"case": case, "days": days} for case, days in formal_identification_cases()
            ]
            if arguments.name == "formal-drl"
            else [],
            "evaluation_runs": [plan.resolved() for plan in plans],
        }
        if not arguments.execute:
            _print(dry)
            return 0
        _print(
            execute_legacy_replay_suite()
            if arguments.name == "legacy-replay"
            else execute_formal_suite()
        )
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
