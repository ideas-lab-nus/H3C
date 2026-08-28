"""Human-readable baseline tables and controller time-series figures."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from h3c.experiments.profiles import repository_root


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} is not an object")
    return value


def _run_summary(run_dir: Path) -> dict[str, Any]:
    manifest = _load(run_dir / "manifest.json")
    metrics = _load(run_dir / "metrics.json")
    completion = _load(run_dir / "completion.json")
    return {
        "case": manifest["case"],
        "controller": manifest["controller"],
        "classification": completion["classification"],
        **metrics["physical"],
        **metrics["setpoint_dynamics"],
        "fallback_count": metrics["controller"]["fallback_count"],
        "run_dir": str(run_dir),
    }


def _plot_run(run_dir: Path, destination: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise RuntimeError("install H3C[baselines] to generate baseline figures") from error
    with (run_dir / "performance.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError("cannot plot an empty baseline run")
    hours = [index * 0.25 for index in range(len(rows))]
    temperatures = [json.loads(row["zone_temperatures_c"]) for row in rows]
    setpoints = [json.loads(row["zone_setpoints_c"]) for row in rows]
    pmv = [json.loads(row["zone_pmv"]) for row in rows]
    occupancy = [json.loads(row["zone_occupancy"]) for row in rows]
    power = [float(row["total_power_w"]) for row in rows]
    resolved = _load(run_dir / "resolved_config.json")
    zones = list(resolved["case_profile"]["zones"])
    figure, axes = plt.subplots(5, 1, figsize=(12, 14), sharex=True)
    for zone in range(len(temperatures[0])):
        label = zones[zone]
        axes[0].plot(hours, [row[zone] for row in temperatures], label=label)
        axes[1].plot(hours, [row[zone] for row in setpoints])
        axes[2].plot(hours, [row[zone] for row in pmv])
        axes[3].step(hours, [row[zone] for row in occupancy], where="post")
    axes[0].set_ylabel("Temperature (°C)")
    axes[0].legend(ncol=min(5, len(temperatures[0])))
    axes[1].set_ylabel("Setpoint (°C)")
    axes[2].axhspan(-0.5, 0.5, color="#2ca02c", alpha=0.1)
    axes[2].set_ylabel("PMV")
    axes[3].set_ylabel("Occupancy")
    axes[4].plot(hours, power, color="#d62728")
    axes[4].set_ylabel("Power (W)")
    axes[4].set_xlabel("Evaluation hour")
    for axis in axes:
        axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def generate_report(source: Path, output_root: Path | None = None) -> dict[str, Any]:
    target = source.resolve()
    if (target / "completion.json").is_file():
        runs = [target]
    else:
        runs = sorted(
            path.parent
            for path in target.rglob("completion.json")
            if (path.parent / "metrics.json").is_file()
        )
    if not runs:
        raise ValueError("report source contains no completed baseline runs")
    destination = (
        output_root
        or repository_root()
        / "outputs"
        / "baselines"
        / "reports"
        / datetime.now(UTC).strftime("baseline-report-%Y%m%dT%H%M%SZ")
    ).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    summaries = [_run_summary(run) for run in runs]
    report = {
        "schema": "h3c_baseline_report",
        "schema_version": 1,
        "run_count": len(summaries),
        "runs": summaries,
    }
    (destination / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    columns = tuple(summaries[0])
    with (destination / "results.csv").open("x", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(summaries)
    lines = [
        "# H3C baseline report",
        "",
        "| Case | Controller | Classification | Cost | Energy (kWh) | Reward | Zone-h | PMV·h |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['case']} | {row['controller']} | {row['classification']} | "
            f"{row['total_cost']:.6f} | {row['energy_kwh']:.6f} | {row['reward']:.6f} | "
            f"{row['discomfort_zone_hours']:.3f} | {row['discomfort_pmv_hours']:.6f} |"
        )
    (destination / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for index, run in enumerate(runs):
        summary = summaries[index]
        _plot_run(
            run,
            destination / f"{summary['case']}_{summary['controller']}_timeseries.png",
        )
    return {"report_dir": str(destination), "run_count": len(runs)}
