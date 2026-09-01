"""Prepare and execute the preregistered Hydro interpreter-semantics probe."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from h3c.agents.contracts import executor_response_schema
from h3c.agents.prompts import system_prompt
from h3c.agents.roles import (
    Executor,
    ModelCallContext,
    ModelContractError,
    resolve_executor_model_output,
)
from h3c.causal.graph import load_graph
from h3c.control.budget import BudgetLedger
from h3c.control.program import (
    ProgramError,
    apply_patch,
    current_interpreter_derivation,
    load_program,
)
from h3c.control.validation import validate_candidate
from h3c.experiments.settings import load_model_provider_contract
from h3c.memory.caol import build_hourly_cao
from h3c.memory.ledger import ProgramLedger
from h3c.runtime.clients import OpenAICompatibleModelClient, model_request_contract


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _parse_sample(value: str) -> tuple[int, int, str]:
    source_text, hour_text, zone = value.split(":", 2)
    return int(source_text), int(hour_text), zone


def _row(
    rows: Sequence[Mapping[str, Any]],
    *,
    hour: int,
    zone: str,
) -> dict[str, Any]:
    matches = [dict(item) for item in rows if int(item["hour"]) == hour and item["zone"] == zone]
    if len(matches) != 1:
        raise ValueError(f"expected one row for hour={hour}, zone={zone}; got {len(matches)}")
    return matches[0]


def _program_before_hour(
    *,
    repository: Path,
    run: Path,
    profile: Mapping[str, Any],
    method: Mapping[str, Any],
    hour: int,
    zone: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ledger = ProgramLedger(
        load_program(repository / str(profile["program"]), zone),
        causal_enabled=bool(method["causal_enabled"]),
    )
    updates = sorted(
        (
            row
            for row in _read_jsonl(run / "program_updates.jsonl")
            if row["zone"] == zone and int(row["hour"]) < hour
        ),
        key=lambda item: int(item["hour"]),
    )
    for update in updates:
        before = int(update["program_version_before"])
        after = int(update["program_version_after"])
        if update["status"] != "accepted" or after == before:
            continue
        committed = ledger.commit(
            update["patch"],
            step=int(update["step"]),
            hour=int(update["hour"]),
            weather_enabled=bool(method["weather_enabled"]),
        )
        if (
            committed.version_before != before
            or committed.version_after != after
            or committed.program_hash_before != update["program_hash_before"]
            or committed.program_hash_after != update["program_hash_after"]
        ):
            raise ValueError("program replay diverged from frozen evidence")
    current = _row(
        _read_jsonl(run / "program_updates.jsonl"),
        hour=hour,
        zone=zone,
    )
    if ledger.version != int(current["program_version_before"]):
        raise ValueError("program version before frozen call is inconsistent")
    return ledger.prompt_view(), ledger.replay(weather_enabled=bool(method["weather_enabled"]))


def _working_memory(
    *,
    run: Path,
    hour: int,
    zone: str,
) -> list[dict[str, Any]]:
    if hour == 0:
        return []
    previous_hour = hour - 1
    step_rows = sorted(
        (
            row
            for row in _read_jsonl(run / "zone_steps.jsonl")
            if int(row["hour"]) == previous_hour and row["zone"] == zone
        ),
        key=lambda item: int(item["step"]),
    )
    decision = _row(
        _read_jsonl(run / "program_updates.jsonl"),
        hour=previous_hour,
        zone=zone,
    )
    rebuilt = build_hourly_cao(
        hour=previous_hour,
        zone=zone,
        step_rows=step_rows,
        program_decision=decision,
    )
    persisted = _row(
        _read_jsonl(run / "caol_records.jsonl"),
        hour=previous_hour,
        zone=zone,
    )
    if "lesson" in persisted:
        rebuilt["lesson"] = persisted["lesson"]
    return [rebuilt]


def _build_input(
    *,
    repository: Path,
    run: Path,
    source_index: int,
    hour: int,
    zone: str,
) -> dict[str, Any]:
    resolved = json.loads((run / "resolved_config.yaml").read_text(encoding="utf-8"))
    profile = resolved["case_profile"]
    method = resolved["method"]
    if profile["profile"] != "MZ_Hydro" or bool(method["long_term_memory"]):
        raise ValueError("probe source must be MZ Hydro with long-term memory off")
    zone_rows = [
        row
        for row in _read_jsonl(run / "zone_steps.jsonl")
        if int(row["hour"]) == hour and row["zone"] == zone
    ]
    zone_rows.sort(key=lambda item: int(item["step"]))
    if len(zone_rows) != 4:
        raise ValueError("frozen Executor input lacks one complete physical hour")
    first_step = zone_rows[0]
    program, validation_program = _program_before_hour(
        repository=repository,
        run=run,
        profile=profile,
        method=method,
        hour=hour,
        zone=zone,
    )
    hourly = next(
        row for row in _read_jsonl(run / "hourly_decisions.jsonl") if int(row["hour"]) == hour
    )
    allocation = dict(hourly["orchestration"]["allocation_audit"])
    allowance = BudgetLedger(allocation, tuple(profile["zones"])).snapshot(zone)
    previous_update = (
        _row(_read_jsonl(run / "program_updates.jsonl"), hour=hour - 1, zone=zone)
        if hour > 0
        else None
    )
    rejection = None if previous_update is None else previous_update.get("rejection")
    observation = dict(first_step["observation"])
    decision_time = int(first_step["action_time_seconds"])
    user = Executor.build_user(
        hour=hour,
        decision_time_seconds=decision_time,
        zone=zone,
        observation=observation,
        current_executable_program=program,
        causal_edges=resolved["resolved_graph"]["edges"],
        allowance=allowance,
        working_memory=_working_memory(run=run, hour=hour, zone=zone),
        long_term_experiences=None,
        rejection_feedback=rejection,
    )
    system = system_prompt("executor", causal_enabled=True, long_term_memory=False)
    source_raw = _row(
        [row for row in _read_jsonl(run / "raw_model_io.jsonl") if row["role"] == "executor"],
        hour=hour,
        zone=zone,
    )
    required_fragments = (
        "top_to_bottom_first_matching_rule_only",
        "current_interpreter_derivation",
        "regime_base_setpoint_c",
        "setpoint_offset_from_regime_base_c",
        "cooling_effect_relative_to_regime_base",
        "rule_capacity",
        "RULE EFFECTS IF MATCHED — set_residual",
        "RULE EFFECTS IF MATCHED — step_setpoint",
        "RULE EFFECTS IF MATCHED — hold_setpoint",
        "rule_order_index",
        "visible_current_last_physical_setpoint_c",
        "interpreter_setpoint_c_after_residual_and_hard_clips_before_assurance",
    )
    if any(fragment not in user for fragment in required_fragments):
        raise ValueError("production render lacks preregistered interpreter-semantics facts")
    return {
        "source_index": source_index,
        "source_run": str(run),
        "source_logical_call_identity": source_raw["logical_call_identity"],
        "hour": hour,
        "step": int(source_raw["step"]),
        "zone": zone,
        "system": system,
        "user": user,
        "system_sha256": _sha256_text(system),
        "user_sha256": _sha256_text(user),
        "program": program,
        "validation_program": validation_program,
        "observation": observation,
        "graph_path": str(repository / str(profile["graph"])),
        "weather_enabled": bool(method["weather_enabled"]),
    }


def _prepare(
    *,
    repository: Path,
    sources: Sequence[Path],
    samples: Sequence[tuple[int, int, str]],
    output: Path,
) -> dict[str, Any]:
    if len(samples) != 6 or len(set(samples)) != 6:
        raise ValueError("probe requires exactly six unique frozen samples")
    output.mkdir(parents=True, exist_ok=False)
    inputs = [
        _build_input(
            repository=repository,
            run=sources[source_index],
            source_index=source_index,
            hour=hour,
            zone=zone,
        )
        for source_index, hour, zone in samples
    ]
    _write_jsonl(output / "prepared_inputs.jsonl", inputs)
    manifest = {
        "probe_schema": "h3c_hydro_interpreter_semantics_probe_inputs",
        "schema_version": 2,
        "prepared_at": datetime.now(UTC).isoformat(),
        "source_runs": [str(path) for path in sources],
        "samples": [
            {
                "source_index": row["source_index"],
                "hour": row["hour"],
                "zone": row["zone"],
                "source_logical_call_identity": row["source_logical_call_identity"],
                "system_sha256": row["system_sha256"],
                "user_sha256": row["user_sha256"],
            }
            for row in inputs
        ],
    }
    (output / "input_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


async def _execute(output: Path) -> dict[str, Any]:
    inputs = _read_jsonl(output / "prepared_inputs.jsonl")
    manifest = json.loads((output / "input_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 2 or any(
        "validation_program" not in row for row in inputs
    ):
        raise ValueError("probe inputs do not contain full executable validation programs")
    provider = "baseten-deepseek"
    contract = load_model_provider_contract(provider)
    key_name = str(contract["api_key_environment_variable"])
    api_key = os.environ.get(key_name, "")
    endpoint = str(contract["fixed_endpoint"] or "").rstrip("/")
    if not endpoint or not api_key:
        raise ValueError("Baseten endpoint or API key is unavailable")
    evidence: dict[str, list[dict[str, Any]]] = {}

    def sink(name: str, row: Mapping[str, Any]) -> None:
        evidence.setdefault(name, []).append(dict(row))

    affinity_header = str(contract["session_affinity_header"])
    client = OpenAICompatibleModelClient(
        endpoint=endpoint,
        api_key=api_key,
        model=str(contract["model"]),
        sink=sink,
        retry_count_limit=0,
        retry_backoff_seconds=(),
        provider_id=provider,
        extra_headers={affinity_header: f"h3c-interpreter-probe-{uuid.uuid4().hex}"},
        retryable_status_codes=tuple(contract["retryable_status_codes"]),
        response_format=str(contract["response_format"]),
    )
    schema = executor_response_schema(causal_enabled=True, long_term_memory=False)

    async def call(index: int, row: Mapping[str, Any]) -> str:
        return await client.complete(
            context=ModelCallContext(
                hour=int(row["hour"]),
                step=int(row["step"]),
                call_ordinal=index,
                zone=str(row["zone"]),
            ),
            role="executor",
            system=str(row["system"]),
            user=str(row["user"]),
            thinking_mode="low",
            response_schema=schema,
        )

    outputs = await asyncio.gather(*(call(index, row) for index, row in enumerate(inputs)))
    for name, rows in evidence.items():
        _write_jsonl(output / name, rows)
    calls = evidence.get("agent_calls.jsonl", [])
    raw_rows = evidence.get("raw_model_io.jsonl", [])
    attempts = evidence.get("model_request_attempts.jsonl", [])
    call_index = {int(row["call_ordinal"]): row for row in calls}
    raw_index = {int(row["call_ordinal"]): row for row in raw_rows}
    samples: list[dict[str, Any]] = []
    all_structural = True
    for index, (row, output_text) in enumerate(zip(inputs, outputs, strict=True)):
        call_row = call_index.get(index, {})
        raw_row = raw_index.get(index, {})
        error_type: str | None = None
        patch: dict[str, Any] | None = None
        validation_status: str | None = None
        validation_program = row["validation_program"]
        before = current_interpreter_derivation(validation_program, row["observation"])
        after: dict[str, Any] | None = None
        try:
            patch, _ = resolve_executor_model_output(output_text, causal_enabled=True)
            graph = load_graph(Path(str(row["graph_path"])))
            validation = validate_candidate(
                patch,
                validation_program,
                graph=graph,
                ledger=None,
                zone=str(row["zone"]),
                step=int(row["step"]),
                causal_enabled=True,
                coordination_enabled=False,
                weather_enabled=bool(row["weather_enabled"]),
            )
            if validation.accepted:
                validation_status = "accepted_without_budget_settlement"
            else:
                rejection = validation.rejection
                if rejection is None:
                    raise ValueError("rejected validation is missing its rejection evidence")
                validation_status = f"registered_rejection:{rejection.code}"
            if validation.candidate_program is not None:
                after = current_interpreter_derivation(
                    validation.candidate_program,
                    row["observation"],
                )
            else:
                try:
                    candidate = apply_patch(
                        validation_program,
                        patch,
                        causal_enabled=True,
                        weather_enabled=bool(row["weather_enabled"]),
                    )
                    after = current_interpreter_derivation(candidate, row["observation"])
                except ProgramError:
                    after = None
        except (ModelContractError, TypeError, ValueError, json.JSONDecodeError) as error:
            error_type = type(error).__name__
        expected_request = model_request_contract(
            model=str(contract["model"]),
            system=str(row["system"]),
            user=str(row["user"]),
            thinking_mode="low",
            response_format=str(contract["response_format"]),
            response_schema=schema,
        )
        request_ok = raw_row.get("request_parameters") == {
            key: value for key, value in expected_request.items() if key != "messages"
        }
        structural = (
            patch is not None
            and error_type is None
            and request_ok
            and call_row.get("finish_reason") == "stop"
            and call_row.get("response_model") == contract["model"]
            and call_row.get("model_provider") == provider
        )
        all_structural = all_structural and structural
        samples.append(
            {
                "hour": row["hour"],
                "zone": row["zone"],
                "system_sha256": row["system_sha256"],
                "user_sha256": row["user_sha256"],
                "operation": None if patch is None else patch.get("op"),
                "rationale": None if patch is None else patch.get("rationale"),
                "validation_status": validation_status,
                "current_derivation_before": before,
                "current_derivation_after": after,
                "finish_reason": call_row.get("finish_reason"),
                "elapsed_seconds": call_row.get("elapsed_seconds"),
                "usage": call_row.get("usage"),
                "request_contract_passed": request_ok,
                "contract_error_type": error_type,
                "structural_passed": structural,
            }
        )
    secret_occurrences = sum(
        path.read_bytes().count(api_key.encode("utf-8"))
        for path in output.iterdir()
        if path.is_file()
    )
    summary = {
        "probe_schema": "h3c_hydro_interpreter_semantics_probe_result",
        "schema_version": 1,
        "provider": provider,
        "model": contract["model"],
        "input_manifest_sha256": _sha256_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        ),
        "finished_at": datetime.now(UTC).isoformat(),
        "samples": samples,
        "checks": {
            "six_calls": len(calls) == len(raw_rows) == len(attempts) == len(inputs) == 6,
            "no_retry": len(attempts) == 6
            and all(int(row.get("attempt_number", 0)) == 1 for row in attempts),
            "all_structural_contracts": all_structural,
            "secret_free": secret_occurrences == 0,
            "semantic_review_pending": True,
        },
        "structural_passed": all_structural and secret_occurrences == 0,
    }
    (output / "probe_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "execute"))
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--source-run", action="append", type=Path, default=[])
    parser.add_argument("--sample", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.mode == "prepare":
        if arguments.repository is None:
            raise ValueError("prepare mode requires --repository")
        summary = _prepare(
            repository=arguments.repository.resolve(),
            sources=[path.resolve() for path in arguments.source_run],
            samples=[_parse_sample(value) for value in arguments.sample],
            output=arguments.output.resolve(),
        )
    else:
        summary = asyncio.run(_execute(arguments.output.resolve()))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "failed", "error_type": type(error).__name__}))
        sys.exit(1)
