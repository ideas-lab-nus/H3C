"""Verify dynamic Prompt fixtures against the frozen read-only legacy owners.

This tool performs no model or physical-service calls. It materializes the
recorded Git tree in a temporary directory, invokes only the three historical
dynamic builders with the tracked representative input, and compares their
rendered bytes with the tracked fixtures.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git(repository: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={repository.as_posix()}",
            *arguments,
        ],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _load_json(path: Path) -> dict[str, Any]:
    value: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _legacy_renders(snapshot_root: Path, representative: Mapping[str, Any]) -> dict[str, str]:
    scripts = snapshot_root / "Revision1" / "Phase2.5_Scripts"
    agents = scripts / "agents_v25"
    sys.path[:0] = [str(agents), str(scripts)]
    try:
        orchestrator_module = importlib.import_module("agent_b_orchestrator")
        executor_module = importlib.import_module("agent_b_executor")
        reflector_module = importlib.import_module("agent_c_reflector")

        options = representative["options"]
        if not isinstance(options, dict):
            raise ValueError("representative options must be an object")
        orchestrator_input = dict(representative["orchestrator"])
        executor_input = dict(representative["executor"])
        reflector_input = dict(representative["reflector"])
        program = representative["program"]

        orchestrator = orchestrator_module.Orchestrator.build_user(
            **orchestrator_input,
            long_term_memory=None,
            orchestration_config=options["orchestration_config"],
            causal_config=options["causal_config"],
            causal_reference_mode=options["causal_reference_mode"],
            input_efficiency_config=options["input_efficiency_config"],
            control_domain_config=None,
        )
        executor = executor_module.Executor.build_user(
            **executor_input,
            spec=program,
            initial_spec=program,
            param_box=executor_module.Executor.param_box_view(
                program,
                options["input_extensions_config"],
                None,
            ),
            rule_local_step_guidance=False,
            orchestrator_rationale=None,
            causal_config=options["causal_config"],
            causal_reference_mode=options["causal_reference_mode"],
            input_efficiency_config=options["input_efficiency_config"],
            input_extensions_config=options["input_extensions_config"],
            control_domain_config=None,
            coordination_mode_config=options["coordination_mode_config"],
        )
        reflector = reflector_module.Reflector.build_user(
            **reflector_input,
            causal_config=options["causal_config"],
        )
        return {
            "orchestrator_old.txt": str(orchestrator),
            "executor_old.txt": str(executor),
            "reflector_old.txt": str(reflector),
        }
    finally:
        del sys.path[:2]


def _extract_trusted_git_archive(archive: bytes, destination: Path) -> None:
    """Extract a local Git archive without relying on version-specific filters."""
    destination = destination.resolve()
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as source_archive:
        members = source_archive.getmembers()
        for member in members:
            target = (destination / member.name).resolve()
            if not target.is_relative_to(destination):
                raise ValueError("legacy Git archive contains an escaping path")
            if member.issym() or member.islnk():
                raise ValueError("legacy Git archive must not contain links")
            if not member.isfile() and not member.isdir():
                raise ValueError("legacy Git archive contains an unsupported member type")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            source = source_archive.extractfile(member)
            if source is None:
                raise ValueError("legacy Git archive file has no readable content")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read())


def verify(legacy_repository: Path) -> dict[str, Any]:
    h3c_root = Path(__file__).resolve().parents[1]
    repository = legacy_repository.resolve()
    if not (repository / ".git").exists():
        raise ValueError("--legacy-repository must name the read-only historical Git repository")
    fixture_root = h3c_root / "tests" / "fixtures" / "prompts"
    provenance = _load_json(fixture_root / "provenance.json")
    representative_path = fixture_root / "representative_input.json"
    representative = _load_json(representative_path)
    representative_bytes = _canonical_json(representative)
    expected_input = provenance["representative_input"]
    if not isinstance(expected_input, dict):
        raise ValueError("representative input provenance must be an object")
    if _sha256(representative_bytes) != expected_input.get("canonical_json_sha256"):
        raise ValueError("representative input identity does not match provenance")
    if len(representative_bytes) != expected_input.get("canonical_length_bytes"):
        raise ValueError("representative input canonical length does not match provenance")

    commit = provenance["oracle_source_commit"]
    if not isinstance(commit, str) or len(commit) != 40:
        raise ValueError("oracle source commit must be a full commit identity")
    owners = provenance["oracle_owners"]
    if not isinstance(owners, dict) or not owners:
        raise ValueError("oracle owners must be a non-empty object")
    owner_results: dict[str, dict[str, str]] = {}
    for semantic_owner, declaration in owners.items():
        if not isinstance(semantic_owner, str) or not isinstance(declaration, dict):
            raise ValueError("each oracle owner must be a named object")
        path = declaration.get("legacy_source_path")
        expected_hash = declaration.get("source_blob_sha256")
        if not isinstance(path, str) or not path.startswith("Revision1/"):
            raise ValueError("oracle owner path must name an exact legacy source")
        source = _git(repository, "show", f"{commit}:{path}")
        actual_hash = _sha256(source)
        if actual_hash != expected_hash:
            raise ValueError(f"legacy source hash mismatch for {path}")
        owner_results[semantic_owner] = {
            "legacy_source_path": path,
            "source_blob_sha256": actual_hash,
        }

    archive = _git(repository, "archive", "--format=tar", commit, "Revision1/Phase2.5_Scripts")
    with tempfile.TemporaryDirectory(prefix="h3c-prompt-oracle-") as temporary:
        snapshot_root = Path(temporary)
        _extract_trusted_git_archive(archive, snapshot_root)
        rendered = _legacy_renders(snapshot_root, representative)

    fixture_results: dict[str, dict[str, Any]] = {}
    for name, actual in rendered.items():
        expected = (fixture_root / name).read_text(encoding="utf-8")
        if actual != expected:
            raise ValueError(f"legacy renderer output differs from frozen fixture {name}")
        fixture_results[name] = {
            "length": len(actual),
            "sha256": _sha256(actual.encode("utf-8")),
        }
        if fixture_results[name] != provenance["fixtures"].get(name):
            raise ValueError(f"fixture provenance mismatch for {name}")
    return {
        "status": "verified",
        "oracle_source_commit": commit,
        "representative_input_sha256": _sha256(representative_bytes),
        "owners": owner_results,
        "fixtures": fixture_results,
        "api_or_physical_calls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify tracked Prompt fixtures against a read-only legacy Git repository."
    )
    parser.add_argument(
        "--legacy-repository",
        required=True,
        type=Path,
        help="path to the historical Git repository containing the recorded oracle commit",
    )
    arguments = parser.parse_args()
    print(json.dumps(verify(arguments.legacy_repository), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
