"""Probe Baseten strict structured output on frozen production Executor inputs."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from h3c.agents.contracts import executor_response_schema
from h3c.agents.roles import (
    ModelCallContext,
    ModelContractError,
    resolve_executor_model_output,
)
from h3c.experiments.settings import load_model_provider_contract
from h3c.runtime.clients import OpenAICompatibleModelClient, model_request_contract


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")


def _parse_samples(values: list[str]) -> list[tuple[int, str]]:
    samples: list[tuple[int, str]] = []
    for value in values:
        hour_text, separator, zone = value.partition(":")
        if not separator or not zone:
            raise ValueError("sample must use HOUR:ZONE")
        samples.append((int(hour_text), zone))
    if len(samples) != 6 or len(samples) != len(set(samples)):
        raise ValueError("probe requires exactly six unique samples")
    return samples


def _select_inputs(source_run: Path, samples: list[tuple[int, str]]) -> list[dict[str, Any]]:
    rows = _read_jsonl(source_run / "raw_model_io.jsonl")
    by_sample = {
        (int(row["hour"]), str(row["zone"])): row
        for row in rows
        if row.get("role") == "executor" and row.get("zone") is not None
    }
    missing = [sample for sample in samples if sample not in by_sample]
    if missing:
        raise ValueError(f"source run lacks requested Executor samples: {missing}")
    return [by_sample[sample] for sample in samples]


async def _run(source_run: Path, output: Path, samples: list[tuple[int, str]]) -> dict[str, Any]:
    provider = "baseten-deepseek"
    contract = load_model_provider_contract(provider)
    key_environment = str(contract["api_key_environment_variable"])
    api_key = os.environ.get(key_environment, "")
    endpoint = str(contract["fixed_endpoint"] or "").rstrip("/")
    if not endpoint or not api_key:
        raise ValueError("Baseten endpoint or API key is unavailable")
    output.mkdir(parents=True, exist_ok=False)
    inputs = _select_inputs(source_run, samples)
    schema = executor_response_schema(causal_enabled=True, long_term_memory=False)
    evidence: dict[str, list[dict[str, Any]]] = {}

    def sink(name: str, row: Mapping[str, Any]) -> None:
        value = dict(row)
        evidence.setdefault(name, []).append(value)
        _write_jsonl(output / name, value)

    affinity_header = str(contract["session_affinity_header"])
    client = OpenAICompatibleModelClient(
        endpoint=endpoint,
        api_key=api_key,
        model=str(contract["model"]),
        sink=sink,
        retry_count_limit=0,
        retry_backoff_seconds=(),
        provider_id=provider,
        extra_headers={affinity_header: f"h3c-schema-probe-{uuid.uuid4().hex}"},
        retryable_status_codes=tuple(contract["retryable_status_codes"]),
        response_format=str(contract["response_format"]),
    )

    async def call(index: int, source: Mapping[str, Any]) -> str:
        return await client.complete(
            context=ModelCallContext(
                hour=int(source["hour"]),
                step=int(source["step"]),
                call_ordinal=index,
                zone=str(source["zone"]),
            ),
            role="executor",
            system=str(source["system"]),
            user=str(source["user"]),
            thinking_mode="low",
            response_schema=schema,
        )

    started_at = datetime.now(UTC).isoformat()
    outputs = await asyncio.gather(*(call(index, row) for index, row in enumerate(inputs)))
    calls = evidence.get("agent_calls.jsonl", [])
    raw_rows = evidence.get("raw_model_io.jsonl", [])
    raw_by_sample = {(int(row["hour"]), str(row["zone"])): row for row in raw_rows}
    call_by_sample = {(int(row["hour"]), str(row["zone"])): row for row in calls}
    per_sample: list[dict[str, Any]] = []
    all_structural = True
    for sample, source, output_text in zip(samples, inputs, outputs, strict=True):
        contract_error: str | None = None
        operation: str | None = None
        exact_envelope = False
        try:
            parsed = json.loads(output_text)
            exact_envelope = (
                isinstance(parsed, dict)
                and set(parsed) == {"patch"}
                and isinstance(parsed["patch"], list)
                and len(parsed["patch"]) == 1
            )
            patch, _ = resolve_executor_model_output(output_text, causal_enabled=True)
            operation = str(patch["op"])
            structurally_valid = exact_envelope
        except (json.JSONDecodeError, ModelContractError, TypeError, ValueError) as error:
            structurally_valid = False
            contract_error = type(error).__name__
        raw = raw_by_sample.get(sample, {})
        call_row = call_by_sample.get(sample, {})
        expected_request = model_request_contract(
            model=str(contract["model"]),
            system=str(source["system"]),
            user=str(source["user"]),
            thinking_mode="low",
            response_format=str(contract["response_format"]),
            response_schema=schema,
        )
        request_ok = raw.get("request_parameters") == {
            key: value for key, value in expected_request.items() if key != "messages"
        }
        sample_ok = (
            structurally_valid
            and request_ok
            and call_row.get("finish_reason") == "stop"
            and call_row.get("response_model") == contract["model"]
            and call_row.get("model_provider") == provider
            and isinstance(call_row.get("usage"), Mapping)
            and call_row["usage"].get("available") is True
        )
        all_structural = all_structural and sample_ok
        per_sample.append(
            {
                "hour": sample[0],
                "zone": sample[1],
                "operation": operation,
                "exact_singleton_patch_envelope": exact_envelope,
                "request_contract": request_ok,
                "finish_reason": call_row.get("finish_reason"),
                "response_model": call_row.get("response_model"),
                "usage": call_row.get("usage"),
                "elapsed_seconds": call_row.get("elapsed_seconds"),
                "contract_error_type": contract_error,
                "passed": sample_ok,
            }
        )

    secret_occurrences = sum(
        path.read_bytes().count(api_key.encode("utf-8"))
        for path in output.iterdir()
        if path.is_file()
    )
    attempts = evidence.get("model_request_attempts.jsonl", [])
    checks = {
        "six_calls": len(calls) == len(raw_rows) == len(attempts) == 6,
        "all_structural_contracts": all_structural,
        "no_retry": len(attempts) == 6
        and all(int(row.get("attempt_number", 0)) == 1 for row in attempts),
        "secret_free": secret_occurrences == 0,
    }
    summary = {
        "probe_schema": "h3c_baseten_executor_structured_output_probe",
        "schema_version": 1,
        "provider": provider,
        "model": contract["model"],
        "source_run": str(source_run),
        "started_at": started_at,
        "finished_at": datetime.now(UTC).isoformat(),
        "samples": per_sample,
        "checks": checks,
        "passed": all(checks.values()),
    }
    temporary = output / "probe_summary.json.tmp"
    temporary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output / "probe_summary.json")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample", action="append", required=True)
    arguments = parser.parse_args()
    samples = _parse_samples(arguments.sample)
    summary = asyncio.run(_run(arguments.source_run.resolve(), arguments.output.resolve(), samples))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "failed", "error_type": type(error).__name__}))
        sys.exit(1)
