"""Package the three registered fully audited H3C results without changing sources."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from h3c.outputs.physical_metrics import compute_physical_metrics

PROMPT_BUNDLE_IDENTITY = "823dcf9e0f0992237cd1adbac480cc2a8b3c1d13e5c67fcc5930d451ff1fabe9"


@dataclass(frozen=True)
class ResultSpec:
    case: str
    evaluation_hours: int
    source_commit: str
    package_name: str
    current: Path
    lineage: tuple[tuple[str, Path], ...] = ()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_manifest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _copy_verified_tree(source: Path, target: Path) -> dict[str, Any]:
    if not source.is_dir():
        raise FileNotFoundError(source)
    before = _tree_manifest(source)
    shutil.copytree(source, target)
    after = _tree_manifest(target)
    if before != after:
        raise ValueError(f"copied evidence differs from source: {source}")
    return {
        "file_count": len(before),
        "bytes": sum((source / relative).stat().st_size for relative in before),
        "tree_manifest_sha256": hashlib.sha256(
            json.dumps(before, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }


def _read_performance(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for line in file:
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path} contains a non-object JSON line")
            rows.append(value)
    return rows


def _assert_recomputed_metrics(run: Path, metrics: dict[str, Any]) -> None:
    zone_steps = _read_jsonl(run / "zone_steps.jsonl")
    recomputed = compute_physical_metrics(
        _read_performance(run / "performance.csv"),
        [
            {
                "zone": row["zone"],
                "step": row["step"],
                "final_setpoint_c": row["final_setpoint_c"],
                "effective_occupancy": row["outcome"]["effective_occupancy"],
                "pmv": row["outcome"]["pmv"],
            }
            for row in zone_steps
        ],
    )
    for group in ("physical", "setpoint_dynamics"):
        for name, expected in metrics[group].items():
            actual = recomputed[group][name]
            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=1e-12):
                    raise ValueError(f"metric mismatch for {group}.{name}: {actual} != {expected}")
            elif actual != expected:
                raise ValueError(f"metric mismatch for {group}.{name}: {actual!r} != {expected!r}")


def _specs(project_root: Path) -> tuple[ResultSpec, ...]:
    return (
        ResultSpec(
            case="SZ_Air",
            evaluation_hours=168,
            source_commit="23186b2c499e02c042018f71f22ee61b5510b910",
            package_name=(
                "SZ_Air__Baseten-DSV4Flash0731__WM1__CausalOn__GraphFull__"
                "CoordOn__ThinkOccupancyRoutedLow__Eval168h__R01__src23186b2"
            ),
            current=project_root
            / "H3C_Final_SZAir_Baseten_20260902_Worktree"
            / "outputs/runs/single-run/SZ_Air/20260902T053717018009Z-045a957bd0e6",
        ),
        ResultSpec(
            case="MZ_Hydro",
            evaluation_hours=120,
            source_commit="8b82bb967f583b64d1a885eb632659efe4485660",
            package_name=(
                "MZ_Hydro__Baseten-DSV4Flash0731__WM1__CausalOn__GraphFull__"
                "CoordOn__ThinkOccupancyRoutedLow__Eval120h__R01__src8b82bb9"
            ),
            current=project_root
            / "H3C_Hydro_Effect_Semantics_Baseten_20260901_Worktree"
            / "outputs/runs/resume-run/MZ_Hydro/20260902T023130261026Z-3ac40543e425",
            lineage=(
                (
                    "L01",
                    project_root
                    / "H3C_Hydro_Effect_Semantics_Baseten_20260901_Worktree"
                    / "outputs/runs/single-run/MZ_Hydro/20260902T005008232278Z-96c50e57c18c",
                ),
                (
                    "L02",
                    project_root
                    / "H3C_Hydro_Effect_Semantics_Baseten_20260901_Worktree"
                    / "outputs/runs/resume-run/MZ_Hydro/20260902T005419009852Z-76b195e0d4b7",
                ),
                (
                    "L03",
                    project_root
                    / "H3C_Hydro_Effect_Semantics_Baseten_20260901_Worktree"
                    / "outputs/runs/resume-run/MZ_Hydro/20260902T021330814876Z-3ac40543e425",
                ),
            ),
        ),
        ResultSpec(
            case="MZ_Air",
            evaluation_hours=168,
            source_commit="8becfad87d0acf6f91a687879c3da7eff5847a45",
            package_name=(
                "MZ_Air__Baseten-DSV4Flash0731__WM1__CausalOn__GraphFull__"
                "CoordOn__ThinkOccupancyRoutedLow__Eval168h__R01__src8becfad"
            ),
            current=project_root
            / "H3C_Final_MZAir_Baseten_20260902_Worktree"
            / "outputs/runs/resume-run/MZ_Air/20260902T094521604903Z-0c9ded6c6041",
            lineage=(
                (
                    "L01",
                    project_root
                    / "H3C_Final_MZAir_Baseten_20260902_Worktree"
                    / "outputs/runs/single-run/MZ_Air/20260902T053717223407Z-57f043e175f9",
                ),
            ),
        ),
    )


def _result(spec: ResultSpec) -> dict[str, Any]:
    manifest = _json(spec.current / "manifest.json")
    resolved = _json(spec.current / "resolved_config.yaml")
    metrics = _json(spec.current / "metrics.json")
    verification = _json(spec.current / "verification.json")
    completion = _json(spec.current / "completion.json")
    checkpoint = _json(spec.current / "completed_hour_checkpoint.json")
    dispatch = _json(spec.current / "dispatch_state.json")
    _assert_recomputed_metrics(spec.current, metrics)
    if manifest["source_commit"] != spec.source_commit:
        raise ValueError(f"{spec.case} source commit changed")
    if not (
        verification.get("execution_integrity") is True
        and verification.get("completion_eligible") is True
        and verification.get("performance_evaluation", {}).get("passed") is True
        and dispatch.get("status") == "STOPPED"
        and checkpoint.get("completed_hour") == spec.evaluation_hours - 1
    ):
        raise ValueError(f"{spec.case} is not a fully audited valid result")
    return {
        "result_schema": "h3c_valid_result",
        "schema_version": 1,
        "case": spec.case,
        "package": spec.package_name,
        "method": resolved["method"],
        "provider": resolved["model_provider"],
        "model": resolved["runtime_contract"]["model"]["providers"][resolved["model_provider"]][
            "model"
        ],
        "source_commit": manifest["source_commit"],
        "prompt_bundle_identity": PROMPT_BUNDLE_IDENTITY,
        "run_identity": manifest["run_identity"],
        "test_id": dispatch["test_id"],
        "classification": verification["classification"],
        "trajectory_status": "EXECUTION-HEALTHY",
        "model_contract_status": (
            "CLEAN" if verification.get("model_contract_clean") is True else "DEGRADED"
        ),
        "performance_status": "REWARD-PMV-PASS",
        "metrics": metrics,
        "completion": completion,
    }


def _readme(result: dict[str, Any], *, language: str) -> str:
    physical = result["metrics"]["physical"]
    dynamics = result["metrics"]["setpoint_dynamics"]
    if language == "zh":
        return (
            f"# {result['case']} 有效 H3C 结果\n\n"
            "本包保存一条已完成完整审计的正式 H3C 轨迹。原始运行目录保持不变；"
            "`evidence/current` 是逐字节复制，`evidence/L*` 保存恢复谱系。\n\n"
            f"- 分类：`{result['classification']}`\n"
            f"- 轨迹：`{result['trajectory_status']}`\n"
            f"- 模型合同：`{result['model_contract_status']}`\n"
            f"- 性能：`{result['performance_status']}`\n"
            f"- Reward：{physical['reward']}\n"
            f"- Cost：{physical['total_cost']}\n"
            f"- Energy (kWh)：{physical['energy_kwh']}\n"
            f"- Zone-h：{physical['discomfort_zone_hours']}\n"
            f"- PMV-h：{physical['discomfort_pmv_hours']}\n"
            f"- Occupied peak |PMV|：{physical['occupied_peak_absolute_pmv']}\n"
            f"- TV (°C)：{dynamics['total_variation_c']}\n"
            f"- Reversals：{dynamics['direction_reversals']}\n\n"
            "`checksums.sha256` 覆盖除其自身外的全部文件。只有 verification 中的"
            " execution integrity、completion eligibility 与 performance gate 均通过，"
            "本轨迹才进入此目录。模型合同退化已完整保留，未改写为 clean。\n"
        )
    return (
        f"# {result['case']} valid H3C result\n\n"
        "This package preserves one formal H3C trajectory that completed the full audit. "
        "The source run remains untouched; `evidence/current` is a byte copy and "
        "`evidence/L*` preserves recovery lineage.\n\n"
        f"- Classification: `{result['classification']}`\n"
        f"- Trajectory: `{result['trajectory_status']}`\n"
        f"- Model contract: `{result['model_contract_status']}`\n"
        f"- Performance: `{result['performance_status']}`\n"
        f"- Reward: {physical['reward']}\n"
        f"- Cost: {physical['total_cost']}\n"
        f"- Energy (kWh): {physical['energy_kwh']}\n"
        f"- Zone-h: {physical['discomfort_zone_hours']}\n"
        f"- PMV-h: {physical['discomfort_pmv_hours']}\n"
        f"- Occupied peak |PMV|: {physical['occupied_peak_absolute_pmv']}\n"
        f"- TV (°C): {dynamics['total_variation_c']}\n"
        f"- Reversals: {dynamics['direction_reversals']}\n\n"
        "`checksums.sha256` covers every file except itself. A trajectory enters this directory "
        "only when execution integrity, completion eligibility, and the performance gate pass. "
        "Any model-contract degradation remains disclosed and is not relabeled clean.\n"
    )


def package_results(project_root: Path, target_root: Path, packager_commit: str) -> None:
    target_root.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for spec in _specs(project_root):
        result = _result(spec)
        package = target_root / spec.package_name
        if package.exists():
            raise FileExistsError(f"result package already exists: {package}")
        evidence = package / "evidence"
        evidence.mkdir(parents=True)
        copy_integrity: dict[str, Any] = {
            "current": _copy_verified_tree(spec.current, evidence / "current")
        }
        lineage_rows = []
        for label, source in spec.lineage:
            copy_integrity[label] = _copy_verified_tree(source, evidence / label)
            lineage_rows.append({"label": label, "source_run": str(source.resolve())})
        provenance = {
            "provenance_schema": "h3c_valid_result_provenance",
            "schema_version": 1,
            "packager_source_commit": packager_commit,
            "prompt_bundle_identity": PROMPT_BUNDLE_IDENTITY,
            "source_current_run": str(spec.current.resolve()),
            "copied_evidence": {
                "current": "evidence/current",
                **{row["label"]: f"evidence/{row['label']}" for row in lineage_rows},
            },
            "copy_integrity": copy_integrity,
            "lineage": lineage_rows,
            "source_commit": spec.source_commit,
            "run_identity": result["run_identity"],
            "test_id": result["test_id"],
        }
        _write_json(package / "result.json", result)
        _write_json(package / "provenance.json", provenance)
        (package / "README.md").write_text(_readme(result, language="en"), encoding="utf-8")
        (package / "README_zh.md").write_text(_readme(result, language="zh"), encoding="utf-8")
        files = sorted(
            path
            for path in package.rglob("*")
            if path.is_file() and path.name != "checksums.sha256"
        )
        (package / "checksums.sha256").write_text(
            "".join(f"{_sha256(path)}  {path.relative_to(package).as_posix()}\n" for path in files),
            encoding="utf-8",
        )
        summaries.append(
            {
                "case": spec.case,
                "package": spec.package_name,
                "source_commit": spec.source_commit,
                "run_identity": result["run_identity"],
                "test_id": result["test_id"],
                "classification": result["classification"],
                **result["metrics"]["physical"],
                **result["metrics"]["setpoint_dynamics"],
            }
        )
    _write_json(
        target_root / "index.json",
        {
            "index_schema": "h3c_valid_results_index",
            "schema_version": 1,
            "results": summaries,
        },
    )
    columns = list(summaries[0])
    with (target_root / "index.csv").open("x", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(summaries)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    packager_commit = subprocess.run(
        ["git", "-c", f"safe.directory={repository.as_posix()}", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    package_results(args.project_root.resolve(), args.target_root.resolve(), packager_commit)


if __name__ == "__main__":
    main()
