"""Verify the processed paper-result package without external services."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from h3c.experiments.matrix import paper_agent_matrix_payload
from h3c.experiments.profiles import profiles
from h3c.outputs.metrics import PRICE_BOOK_ID, USD_PER_MILLION

ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "reference_results" / "paper_2026"
MANIFEST = RESULT_ROOT / "manifest.json"
PAPER_TITLE = (
    "Causality-Constrained Hierarchical LLM Agents for Online Rule Adaptation in Building HVAC "
    "Control"
)
EXPECTED_RESULT_FILES = {
    "h3c_agent_run_metrics.csv",
    "h3c_agent_group_summary.csv",
    "main_comparison_statistics.csv",
    "reward_advantage_timeseries.csv",
    "program_disposition_hourly.csv",
    "program_update_records.csv",
    "paper_agent_matrix.json",
    "provenance.json",
}
PROVENANCE_BOUNDARY = (
    "De-identified processed metrics and classified update outcomes; raw simulator trajectories "
    "and model-service messages are not included."
)
CASES = ("SZ_Air", "MZ_Hydro", "MZ_Air")
REPEATS = ("R01", "R02", "R03")
CONFIGURATIONS = (
    "STANDARD",
    "B1_WM0",
    "B2_WM2",
    "B3_WM3",
    "B4_CausalOff",
    "B5_MissingSolarZoneEdge",
    "B6_EdgeTiming",
    "B7_CoordOff",
    "B8_NoThinking",
)
CASE_CONTRACT = {
    "SZ_Air": {"hours": 168, "zones": 1},
    "MZ_Hydro": {"hours": 120, "zones": 2},
    "MZ_Air": {"hours": 168, "zones": 5},
}
GROUP_FIELDS = {
    "reward": "reward",
    "cost": "cost",
    "energy_kwh": "energy_kwh",
    "zone_h": "zone_h",
    "pmv_h": "pmv_h",
    "occupied_peak_abs_pmv": "occupied_peak_abs_pmv",
    "tv_c": "tv_c",
    "reversals": "reversals",
    "v_state_c": "v_state_c",
    "r_int_fraction": "r_int_fraction",
    "total_ktokens_per_control_hour": "total_ktokens_per_control_hour",
    "effective_llm_latency_s_per_control_hour": "effective_llm_latency_s_per_control_hour",
    "api_cost_usd_per_run": "api_cost_usd_per_run",
    "retries_per_control_hour": "retries_per_control_hour",
    "fallbacks_per_control_hour": "fallbacks_per_control_hour",
}
MAIN_METRIC_TO_RUN_FIELD = {
    "reward": "reward",
    "total_cost": "cost",
    "energy_kwh": "energy_kwh",
    "discomfort_zone_hours": "zone_h",
    "discomfort_pmv_hours": "pmv_h",
    "occupied_peak_absolute_pmv": "occupied_peak_abs_pmv",
    "total_variation_c": "tv_c",
    "direction_reversals": "reversals",
}
MAIN_METHODS = {
    "SZ_Air": ("RBC", "eRBC", "MPC", "PPO", "Ours"),
    "MZ_Hydro": ("RBC", "eRBC", "MPC", "PPO", "MAPPO", "Ours"),
    "MZ_Air": ("RBC", "eRBC", "MPC", "PPO", "MAPPO", "Ours"),
}
DISPOSITION_CATEGORIES = (
    "set_param",
    "add_rule",
    "replace_rule",
    "remove_rule",
    "move_rule",
    "explicit_no_change",
    "deterministic_rejection",
    "schema_fallback",
)
PRIVATE_COLUMNS = {
    "trajectory_key",
    "test_id",
    "run_identity",
    "source_evidence",
    "raw_model_io_sha256",
}
LOCAL_PATH_PATTERN = re.compile(r"(?:(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/Users/|/home/)")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return sum(1 for _ in csv.reader(stream)) - 1


def _read_dict_rows(name: str) -> tuple[list[str], list[dict[str, str]]]:
    path = RESULT_ROOT / name
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or ()), list(reader)


def _close(actual: float, expected: float) -> bool:
    return math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-8)


def _check_close(actual: float, expected: float, label: str, failures: list[str]) -> None:
    if not _close(actual, expected):
        failures.append(f"{label}: {actual!r} != {expected!r}")


def _pipe_values(value: str) -> list[float]:
    return [float(item) for item in value.split("|")]


def _json_values(value: str) -> list[float]:
    payload = json.loads(value)
    if not isinstance(payload, list) or any(not isinstance(item, (int, float)) for item in payload):
        raise ValueError("main-comparison values must be a numeric list")
    return [float(item) for item in payload]


def _sample_sd(values: list[float]) -> float | None:
    return statistics.stdev(values) if len(values) > 1 else None


def _is_ancestor(commit: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT.as_posix()}",
            "merge-base",
            "--is-ancestor",
            commit,
            "HEAD",
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def _verify_manifest(payload: dict[str, Any], failures: list[str]) -> None:
    if payload.get("schema") != "h3c_processed_paper_results":
        failures.append("the paper-result manifest schema differs")
    if payload.get("schema_version") != 1:
        failures.append("the paper-result manifest schema version differs")
    if payload.get("paper_title") != PAPER_TITLE:
        failures.append("the paper title differs in the result manifest")
    file_paths = [str(item.get("path", "")) for item in payload.get("files", [])]
    if len(file_paths) != len(set(file_paths)):
        failures.append("the paper-result manifest contains duplicate file paths")
    if set(file_paths) != EXPECTED_RESULT_FILES:
        failures.append("the paper-result manifest file inventory differs")

    for item in payload["files"]:
        path = RESULT_ROOT / item["path"]
        if not path.is_file():
            failures.append(f"missing file: {item['path']}")
            continue
        if path.stat().st_size != int(item["bytes"]):
            failures.append(f"byte count differs: {item['path']}")
        if _sha256(path) != item["sha256"]:
            failures.append(f"SHA-256 differs: {item['path']}")
        if "data_rows" in item and _csv_rows(path) != int(item["data_rows"]):
            failures.append(f"row count differs: {item['path']}")

    stored_matrix = json.loads(
        (RESULT_ROOT / "paper_agent_matrix.json").read_text(encoding="utf-8")
    )
    live_matrix = paper_agent_matrix_payload()
    if stored_matrix != live_matrix:
        failures.append("paper_agent_matrix.json differs from the live paper-agent planner")
    if len(stored_matrix.get("arms", [])) != int(payload["paper_agent_plan_groups"]):
        failures.append("paper Agent plan count differs from the manifest")
    matrix_item = next(
        (item for item in payload["files"] if item["path"] == "paper_agent_matrix.json"),
        None,
    )
    if matrix_item is None or int(matrix_item.get("records", -1)) != len(
        stored_matrix.get("arms", [])
    ):
        failures.append("paper Agent matrix record count differs")

    provenance = json.loads((RESULT_ROOT / "provenance.json").read_text(encoding="utf-8"))
    if provenance.get("schema") != "h3c_processed_paper_provenance":
        failures.append("the paper-result provenance schema differs")
    if provenance.get("schema_version") != 1:
        failures.append("the paper-result provenance schema version differs")
    if provenance.get("paper_title") != PAPER_TITLE:
        failures.append("the paper title differs in provenance")
    if provenance.get("release_boundary") != PROVENANCE_BOUNDARY:
        failures.append("the processed-result release boundary differs")

    expected_pricebook = {
        "id": PRICE_BOOK_ID,
        "currency": "USD",
        "unit": "per_million_tokens",
        "cached_prompt_tokens": USD_PER_MILLION["cache_hit"],
        "uncached_prompt_tokens": USD_PER_MILLION["cache_miss"],
        "completion_tokens": USD_PER_MILLION["output"],
    }
    if payload["api_cost_pricebook"] != expected_pricebook:
        failures.append("the published API-cost pricebook differs from the metric owner")

    for item in payload["h3c_source_commits"]:
        if not _is_ancestor(item["commit"]):
            failures.append(f"paper source commit is absent from history: {item['commit']}")


def _verify_runs(payload: dict[str, Any], failures: list[str]) -> list[dict[str, str]]:
    fields, runs = _read_dict_rows("h3c_agent_run_metrics.csv")
    leaked = PRIVATE_COLUMNS.intersection(fields)
    if leaked:
        failures.append("private run fields are present: " + ", ".join(sorted(leaked)))
    required_retry_fields = {
        "retried_logical_call_count",
        "additional_request_attempt_count",
    }
    if not required_retry_fields.issubset(fields):
        failures.append("run-level retry accounting fields are missing")

    expected_groups = {(case, config): 3 for case in CASES for config in CONFIGURATIONS}
    actual_groups = Counter((row["case"], row["configuration"]) for row in runs)
    if actual_groups != expected_groups:
        failures.append("the 3 x 9 x 3 Agent matrix is incomplete")
    if {row["repeat"] for row in runs} != set(REPEATS):
        failures.append("the Agent repeat labels are incomplete")

    live_matrix = paper_agent_matrix_payload()
    plan_by_group = {
        (str(arm["case"]), str(arm["paper_label"])): arm for arm in live_matrix["arms"]
    }
    control_hours = 0
    logical_calls = 0
    retried_logical_calls = 0
    additional_attempts = 0
    fallback_totals = Counter[str]()
    for row in runs:
        case = row["case"]
        contract = CASE_CONTRACT.get(case)
        if contract is None:
            continue
        hours = int(row["evaluation_hours"])
        zones = int(row["zones"])
        if hours != contract["hours"] or zones != contract["zones"]:
            failures.append(f"case duration or zone count differs: {case}/{row['repeat']}")
        plan = plan_by_group.get((case, row["configuration"]))
        if plan is None:
            failures.append(f"run row has no paper-agent plan: {case}/{row['configuration']}")
            continue
        checked_calls = int(row["logical_calls_checked"])
        if checked_calls != int(plan["expected_agent_calls"]):
            failures.append(f"logical-call count differs: {case}/{row['configuration']}")

        prompt = int(row["prompt_tokens"])
        completion = int(row["completion_tokens"])
        total = int(row["total_tokens"])
        cached = int(row["cached_prompt_tokens"])
        if total != prompt + completion or not 0 <= cached <= prompt:
            failures.append(
                f"token accounting differs: {case}/{row['configuration']}/{row['repeat']}"
            )
        _check_close(
            float(row["total_ktokens_per_control_hour"]),
            total / (1000.0 * hours),
            f"token rate {case}/{row['configuration']}/{row['repeat']}",
            failures,
        )
        expected_cost = (
            cached * USD_PER_MILLION["cache_hit"]
            + (prompt - cached) * USD_PER_MILLION["cache_miss"]
            + completion * USD_PER_MILLION["output"]
        ) / 1_000_000
        _check_close(
            float(row["api_cost_usd_per_run"]),
            expected_cost,
            f"API cost {case}/{row['configuration']}/{row['repeat']}",
            failures,
        )

        role_fallbacks = {
            "orchestrator_fallbacks": int(row["orchestrator_fallback_count"]),
            "policy_adapter_fallbacks": int(row["policy_adapter_fallback_count"]),
            "reflector_fallbacks": int(row["reflector_fallback_count"]),
        }
        agent_fallbacks = int(row["agent_fallback_count"])
        if agent_fallbacks != sum(role_fallbacks.values()):
            failures.append(f"role fallback counts do not sum: {case}/{row['repeat']}")
        _check_close(
            float(row["fallbacks_per_control_hour"]),
            agent_fallbacks / hours,
            f"fallback rate {case}/{row['configuration']}/{row['repeat']}",
            failures,
        )
        retries = float(row["retries_per_control_hour"]) * hours
        if not _close(retries, round(retries)):
            failures.append(f"retry count is non-integral: {case}/{row['repeat']}")
        retried_calls = int(row["retried_logical_call_count"])
        additional_requests = int(row["additional_request_attempt_count"])
        if not retried_calls <= additional_requests <= 2 * retried_calls:
            failures.append(f"bounded retry relationship differs: {case}/{row['repeat']}")
        if additional_requests != round(retries):
            failures.append(f"retry-rate closure differs: {case}/{row['repeat']}")

        control_hours += hours
        logical_calls += checked_calls
        retried_logical_calls += retried_calls
        additional_attempts += additional_requests
        fallback_totals.update(role_fallbacks)

    source_counts = Counter(row["source_commit"] for row in runs)
    manifest_counts = Counter(
        {item["commit"]: int(item["trajectories"]) for item in payload["h3c_source_commits"]}
    )
    if source_counts != manifest_counts:
        failures.append("the Agent source-commit counts differ from the manifest")

    reported = payload["operational_event_totals"]
    calculated = {
        "control_hours": control_hours,
        "logical_calls": logical_calls,
        "calls_requiring_retry": retried_logical_calls,
        "additional_request_attempts": additional_attempts,
        **fallback_totals,
        "all_agent_fallbacks": sum(fallback_totals.values()),
    }
    for name, value in calculated.items():
        if int(reported[name]) != value:
            failures.append(f"operational total differs: {name}")
    return runs


def _verify_groups(runs: list[dict[str, str]], failures: list[str]) -> None:
    _, groups = _read_dict_rows("h3c_agent_group_summary.csv")
    expected_keys = {(case, config) for case in CASES for config in CONFIGURATIONS}
    if Counter((row["case"], row["configuration"]) for row in groups) != {
        key: 1 for key in expected_keys
    }:
        failures.append("the 27 Agent group summaries are incomplete")
        return

    runs_by_group: defaultdict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in runs:
        runs_by_group[(row["case"], row["configuration"])].append(row)
    for key in runs_by_group:
        runs_by_group[key].sort(key=lambda row: REPEATS.index(row["repeat"]))

    for row in groups:
        key = (row["case"], row["configuration"])
        source = runs_by_group[key]
        if int(row["n"]) != len(source):
            failures.append(f"group n differs: {key}")
        for summary_name, run_name in GROUP_FIELDS.items():
            expected_values = [float(item[run_name]) for item in source]
            stored_values = _pipe_values(row[f"{summary_name}_values"])
            if len(stored_values) != len(expected_values) or any(
                not _close(actual, expected)
                for actual, expected in zip(stored_values, expected_values, strict=True)
            ):
                failures.append(f"group constituent values differ: {key}/{summary_name}")
            _check_close(
                float(row[f"{summary_name}_mean"]),
                statistics.mean(expected_values),
                f"group mean {key}/{summary_name}",
                failures,
            )
            _check_close(
                float(row[f"{summary_name}_sd"]),
                statistics.stdev(expected_values),
                f"group sample SD {key}/{summary_name}",
                failures,
            )
        exceedances = sum(float(item["occupied_peak_abs_pmv"]) > 0.70 for item in source)
        if int(row["peak_pmv_exceedance_count"]) != exceedances:
            failures.append(f"occupied-peak exceedance count differs: {key}")


def _verify_main_comparison(runs: list[dict[str, str]], failures: list[str]) -> dict[str, float]:
    _, rows = _read_dict_rows("main_comparison_statistics.csv")
    expected_keys = {
        (case, method, metric)
        for case, methods in MAIN_METHODS.items()
        for method in methods
        for metric in MAIN_METRIC_TO_RUN_FIELD
    }
    actual_keys = Counter((row["case"], row["method"], row["metric"]) for row in rows)
    if actual_keys != {key: 1 for key in expected_keys}:
        failures.append("the 17 x 8 main-comparison matrix is incomplete")

    standard = {
        (row["case"], row["repeat"]): row for row in runs if row["configuration"] == "STANDARD"
    }
    erbc_reward: dict[str, float] = {}
    for row in rows:
        values = _json_values(row["values"])
        if int(row["n"]) != len(values):
            failures.append(
                f"main-comparison n differs: {row['case']}/{row['method']}/{row['metric']}"
            )
        _check_close(
            float(row["mean"]),
            statistics.mean(values),
            f"main-comparison mean {row['case']}/{row['method']}/{row['metric']}",
            failures,
        )
        expected_sd = _sample_sd(values)
        if expected_sd is None:
            if row["sample_sd"] != "":
                failures.append(
                    "single-trajectory sample SD is not empty: "
                    f"{row['case']}/{row['method']}/{row['metric']}"
                )
        else:
            _check_close(
                float(row["sample_sd"]),
                expected_sd,
                f"main-comparison sample SD {row['case']}/{row['method']}/{row['metric']}",
                failures,
            )

        if row["method"] == "Ours":
            expected_values = [
                float(standard[(row["case"], repeat)][MAIN_METRIC_TO_RUN_FIELD[row["metric"]]])
                for repeat in REPEATS
            ]
            if len(values) != len(expected_values) or any(
                not _close(actual, expected)
                for actual, expected in zip(values, expected_values, strict=True)
            ):
                failures.append(f"Ours does not match STANDARD: {row['case']}/{row['metric']}")
        if row["method"] == "eRBC" and row["metric"] == "reward":
            erbc_reward[row["case"]] = float(row["mean"])
    return erbc_reward


def _verify_reward_timeseries(
    runs: list[dict[str, str]], erbc_reward: dict[str, float], failures: list[str]
) -> None:
    _, rows = _read_dict_rows("reward_advantage_timeseries.csv")
    grouped: defaultdict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["case"], row["repeat"])].append(row)
    expected_keys = {(case, repeat) for case in CASES for repeat in REPEATS}
    if set(grouped) != expected_keys:
        failures.append("reward-advantage time series do not cover the nine standard runs")
        return
    standard_reward = {
        (row["case"], row["repeat"]): float(row["reward"])
        for row in runs
        if row["configuration"] == "STANDARD"
    }
    for key, series in grouped.items():
        case, _ = key
        series.sort(key=lambda row: int(row["hour"]))
        expected_hours = CASE_CONTRACT[case]["hours"]
        if [int(row["hour"]) for row in series] != list(range(1, expected_hours + 1)):
            failures.append(f"reward-advantage hours are incomplete: {key}")
            continue
        cumulative = 0.0
        for row in series:
            proposed = float(row["proposed_hour_reward"])
            reference = float(row["erbc_hour_reward"])
            advantage = proposed - reference
            cumulative += advantage
            _check_close(
                float(row["hour_reward_advantage"]), advantage, f"hour advantage {key}", failures
            )
            _check_close(
                float(row["cumulative_reward_advantage"]),
                cumulative,
                f"cumulative advantage {key}",
                failures,
            )
        _check_close(
            sum(float(row["proposed_hour_reward"]) for row in series),
            standard_reward[key],
            f"standard reward closure {key}",
            failures,
        )
        _check_close(
            sum(float(row["erbc_hour_reward"]) for row in series),
            erbc_reward[case],
            f"enhanced-RBC reward closure {key}",
            failures,
        )


def _verify_program_updates(failures: list[str]) -> None:
    _, updates = _read_dict_rows("program_update_records.csv")
    _, hourly = _read_dict_rows("program_disposition_hourly.csv")
    loaded = profiles()
    expected_update_keys = {
        (case, repeat, hour, zone)
        for case in CASES
        for repeat in REPEATS
        for hour in range(1, CASE_CONTRACT[case]["hours"] + 1)
        for zone in loaded[case]["zones"]
    }
    actual_update_keys = {
        (row["case"], row["repeat"], int(row["hour"]), row["zone"]) for row in updates
    }
    if actual_update_keys != expected_update_keys or len(updates) != len(expected_update_keys):
        failures.append("the standard-run Policy Adapter output rows are incomplete or duplicated")

    accepted_edits = {"set_param", "add_rule", "replace_rule", "remove_rule", "move_rule"}
    expected_status = {
        "explicit_no_change": "accepted",
        "deterministic_rejection": "rejected",
        "schema_fallback": "model_output_rejected",
    }
    counts: Counter[tuple[str, int, str]] = Counter()
    for row in updates:
        category = row["category"]
        before = int(row["program_version_before"])
        after = int(row["program_version_after"])
        same_hash = row["program_hash_before"] == row["program_hash_after"]
        if row["transition_ok"] != "True":
            failures.append(
                f"stored program transition failed: {row['case']}/{row['repeat']}/{row['hour']}"
            )
        if category in accepted_edits:
            if row["status"] != "accepted" or after != before + 1 or same_hash:
                failures.append(f"accepted edit transition differs: {row['case']}/{row['hour']}")
        elif category in expected_status:
            if row["status"] != expected_status[category] or after != before or not same_hash:
                failures.append(f"non-edit transition differs: {row['case']}/{row['hour']}")
        else:
            failures.append(f"unknown Policy Adapter disposition: {category}")
        counts[(row["case"], int(row["hour"]), category)] += 1

    expected_hourly_keys = {
        (case, hour, category)
        for case in CASES
        for hour in range(1, CASE_CONTRACT[case]["hours"] + 1)
        for category in DISPOSITION_CATEGORIES
    }
    actual_hourly_keys = Counter((row["case"], int(row["hour"]), row["category"]) for row in hourly)
    if actual_hourly_keys != {key: 1 for key in expected_hourly_keys}:
        failures.append("the hourly Policy Adapter disposition matrix is incomplete")
        return
    for row in hourly:
        key = (row["case"], int(row["hour"]), row["category"])
        denominator = len(REPEATS) * CASE_CONTRACT[row["case"]]["zones"]
        if int(row["denominator"]) != denominator or int(row["count"]) != counts[key]:
            failures.append(f"hourly disposition count differs: {key}")
        _check_close(
            float(row["fraction"]),
            counts[key] / denominator,
            f"hourly disposition fraction {key}",
            failures,
        )


def _verify_privacy_boundary(payload: dict[str, Any], failures: list[str]) -> None:
    for item in payload["files"]:
        path = RESULT_ROOT / item["path"]
        if path.suffix.lower() not in {".csv", ".json", ".md"}:
            continue
        content = path.read_text(encoding="utf-8-sig")
        if LOCAL_PATH_PATTERN.search(content):
            failures.append(f"machine-local path found in released results: {item['path']}")


def verify() -> dict[str, int]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    _verify_manifest(payload, failures)
    runs = _verify_runs(payload, failures)
    _verify_groups(runs, failures)
    erbc_reward = _verify_main_comparison(runs, failures)
    _verify_reward_timeseries(runs, erbc_reward, failures)
    _verify_program_updates(failures)
    _verify_privacy_boundary(payload, failures)
    if failures:
        raise RuntimeError("Paper-result verification failed:\n- " + "\n- ".join(failures))
    return {
        "files": len(payload["files"]),
        "data_rows": sum(int(item.get("data_rows", 0)) for item in payload["files"]),
        "trajectories": int(payload["completed_agent_trajectories"]),
        "source_commits": len(payload["h3c_source_commits"]),
        "plan_groups": int(payload["paper_agent_plan_groups"]),
    }


if __name__ == "__main__":
    result = verify()
    print(
        "Verified "
        f"{result['files']} paper-result files, {result['data_rows']} tabular data rows, "
        f"{result['trajectories']} processed trajectories, {result['plan_groups']} Agent plans, "
        f"and {result['source_commits']} recorded source commits."
    )
