from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from h3c.cli import build_parser, main

_DRY_CLI_IMPORT_SENTINEL = r"""
import importlib.abc
import json
import sys

blocked = (
    "h3c.runtime.engine",
    "h3c.runtime.clients",
    "pythermalcomfort",
    "agent_framework",
    "openai",
)

class BlockHeavyRuntimeImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == name or fullname.startswith(name + ".") for name in blocked):
            raise RuntimeError("dry CLI imported forbidden module: " + fullname)
        return None

sys.meta_path.insert(0, BlockHeavyRuntimeImports())
from h3c.cli import main

main(json.loads(sys.argv[1]))
loaded = sorted(
    name
    for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in blocked)
)
if loaded:
    raise RuntimeError("dry CLI loaded forbidden modules: " + ", ".join(loaded))
"""


def _run_isolated_dry_cli(repository: Path, arguments: list[str]) -> dict[str, object]:
    environment = os.environ.copy()
    source = str(repository / "src")
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source if not existing_pythonpath else os.pathsep.join((source, existing_pythonpath))
    )
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "-c", _DRY_CLI_IMPORT_SENTINEL, json.dumps(arguments)],
        cwd=repository,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert time.perf_counter() - started < 5.0
    value = json.loads(completed.stdout)
    assert isinstance(value, dict)
    return value


def test_physical_commands_default_to_dry_plan(capsys: pytest.CaptureFixture[str]) -> None:
    main(["run", "--profile", "SZ_Air"])
    output = json.loads(capsys.readouterr().out)
    assert output["mode"] == "dry_plan"
    assert output["run_count"] == 1


def test_retired_smoke_command_is_not_public() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["smoke", "release-6h"])


@pytest.mark.parametrize(
    ("arguments", "expected_runs", "expected_calls"),
    [
        (["run", "--profile", "MZ_Hydro"], 1, 4 * 120),
        (["suite", "all"], 27, 16824),
    ],
)
def test_dry_plans_do_not_import_runtime_or_thermal_comfort(
    arguments: list[str], expected_runs: int, expected_calls: int
) -> None:
    repository = Path(__file__).parents[2]
    output = _run_isolated_dry_cli(repository, arguments)
    assert output["mode"] == "dry_plan"
    assert output["run_count"] == expected_runs
    assert output["expected_agent_calls"] == expected_calls


def test_graph_validation_does_not_import_runtime_or_thermal_comfort(tmp_path: Path) -> None:
    proposal = {
        "graph_schema": "causal_graph_proposal",
        "schema_version": 1,
        "profile": "Demo",
        "workflow_status": "proposed",
        "sources": ["engineering source"],
        "nodes": [
            {"id": "cooling_setpoint", "scope": "zone"},
            {"id": "zone_temp", "scope": "zone"},
        ],
        "edges": [
            {
                "source": "cooling_setpoint",
                "relation": "Positive Corr",
                "target": "zone_temp",
                "tags": ["Immediate", "Strong Impact"],
                "timing": "immediate",
            }
        ],
        "zones": ["north"],
        "adjacency": [],
    }
    input_path = tmp_path / "proposal.json"
    input_path.write_text(json.dumps(proposal), encoding="utf-8")
    output = _run_isolated_dry_cli(
        Path(__file__).parents[2], ["graph", "validate", "--input", str(input_path)]
    )
    assert output["valid"] is True


def test_offline_discovery_defaults_to_secret_free_dry_plan_without_optional_imports() -> None:
    repository = Path(__file__).parents[2]
    offline_root = repository / "outputs" / "offline"
    before = sorted(path.relative_to(offline_root) for path in offline_root.rglob("*"))
    output = _run_isolated_dry_cli(
        repository,
        [
            "offline",
            "discover",
            "--spec",
            str(repository / "configs" / "onboarding" / "example_spec.json"),
        ],
    )
    assert output["mode"] == "dry_plan"
    assert output["maximum_model_calls"] == {
        "semantic_mapping": 3,
        "causal_discovery": 3,
        "total": 6,
    }
    provider = output["provider"]
    assert isinstance(provider, dict)
    assert provider["reasoning_effort"] == "low"
    assert provider["temperature_absent"] is True
    assert provider["top_p_absent"] is True
    assert output["will_create_workspace"] is False
    assert output["will_call_model"] is False
    after = sorted(path.relative_to(offline_root) for path in offline_root.rglob("*"))
    assert after == before


def test_hydronic_single_run_defaults_to_profile_formal_duration(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["run", "--profile", "MZ_Hydro"])
    output = json.loads(capsys.readouterr().out)
    assert output["runs"][0]["method"]["evaluation_hours"] == 120
    with pytest.raises(SystemExit):
        main(["run", "--profile", "MZ_Hydro", "--evaluation-hours", "168"])


@pytest.mark.parametrize(
    "flag",
    [
        ["--working-memory-hours", "2"],
        ["--causal-off"],
        ["--independent-coordination"],
        ["--no-thinking"],
        ["--graph-mutation", "missing-solar-zone-edge"],
    ],
)
def test_baseline_rejects_agent_only_flags(flag: list[str]) -> None:
    with pytest.raises(SystemExit, match="Agent-only"):
        main(["run", "--profile", "SZ_Air", "--baseline", *flag])


def test_causal_off_rejects_hidden_graph_mutation_identity() -> None:
    with pytest.raises(ValueError, match="causal-off"):
        main(
            [
                "run",
                "--profile",
                "SZ_Air",
                "--causal-off",
                "--graph-mutation",
                "missing-solar-zone-edge",
            ]
        )


def test_suite_arm_and_report_positional_target_are_auditable(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    main(["suite", "main", "--arm-index", "1"])
    output = json.loads(capsys.readouterr().out)
    assert output["run_count"] == 1
    assert output["runs"][0]["profile"] == "MZ_Hydro"
    args = build_parser().parse_args(["report", str(tmp_path)])
    assert args.target == tmp_path
