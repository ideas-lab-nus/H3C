import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from h3c.outputs import verification


def _write(path: Path, value: dict[str, Any]) -> bytes:
    payload = (json.dumps(value, sort_keys=True) + "\n").encode()
    path.write_bytes(payload)
    return payload


def test_zero_call_recertification_is_append_only_and_binds_original_terminals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = {"runtime_schema": "historical", "schema_version": 1}
    _write(tmp_path / "resolved_config.yaml", {"runtime_contract": runtime})
    _write(
        tmp_path / "manifest.json",
        {"run_identity": "run-1", "source_commit": "1" * 40},
    )
    failure_payload = _write(tmp_path / "failure.json", {"status": "failed"})
    verification_payload = _write(tmp_path / "verification.json", {"classification": "RUN-INVALID"})
    expected_result = {
        "trajectory_status": "EXECUTION-HEALTHY",
        "model_contract_status": "DEGRADED",
    }
    calls: list[tuple[Path, bool, dict[str, Any] | None]] = []

    def _verify(
        run_dir: Path,
        *,
        require_completion: bool = True,
        historical_runtime_contract: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        calls.append((run_dir, require_completion, historical_runtime_contract))
        return expected_result

    monkeypatch.setattr(verification, "verify_run", _verify)
    output = tmp_path / "recertification.json"
    artifact = verification.recertify_run(
        tmp_path,
        output_path=output,
        recertifier_source_commit="2" * 40,
    )

    assert calls == [(tmp_path.resolve(), False, runtime)]
    assert artifact["recertifier"]["external_calls"] == 0
    assert artifact["result"] == expected_result
    hashes = artifact["source_run"]["original_terminal_artifacts_sha256"]
    assert hashes == {
        "failure.json": hashlib.sha256(failure_payload).hexdigest(),
        "verification.json": hashlib.sha256(verification_payload).hexdigest(),
    }
    assert (tmp_path / "failure.json").read_bytes() == failure_payload
    assert (tmp_path / "verification.json").read_bytes() == verification_payload
    with pytest.raises(FileExistsError):
        verification.recertify_run(
            tmp_path,
            output_path=output,
            recertifier_source_commit="2" * 40,
        )
