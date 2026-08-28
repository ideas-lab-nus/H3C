from __future__ import annotations

import ast
import re
from pathlib import Path

PROJECT_DESCRIPTION = (
    "Hierarchical Causal-Constrained Control (H3C) for cooling-only building control"
)
MANAGED_CONTENT_ROOTS = ("src", "configs", "tests", "tools", "docs", "outputs")


def _nested_git_metadata(repository_root: Path) -> list[str]:
    return sorted(
        candidate.relative_to(repository_root).as_posix()
        for name in MANAGED_CONTENT_ROOTS
        for candidate in (repository_root / name).rglob(".git")
    )


def test_required_repository_structure_exists(repository_root: Path) -> None:
    required = (
        "AGENTS.md",
        "pyproject.toml",
        "requirements.txt",
        "requirements-offline.txt",
        "README.md",
        "LICENSE",
        ".env.example",
        "src/h3c/agents",
        "src/h3c/control",
        "src/h3c/assurance",
        "src/h3c/causal",
        "src/h3c/memory",
        "src/h3c/runtime",
        "src/h3c/experiments",
        "src/h3c/outputs",
        "src/h3c/offline",
        "configs/cases",
        "configs/experiments",
        "configs/graphs",
        "configs/programs",
        "configs/onboarding",
        "tests/unit",
        "tests/integration",
        "tests/contracts",
        "tests/fixtures",
        "tools/verify_legacy_prompt_oracle.py",
        "docs",
        "outputs/README.md",
        "outputs/runs",
        "outputs/reports",
        "outputs/offline",
    )
    assert all((repository_root / item).exists() for item in required)
    assert _nested_git_metadata(repository_root) == []
    readme = (repository_root / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# Hierarchical Causal-Constrained Control (H3C)")
    pyproject = (repository_root / "pyproject.toml").read_text(encoding="utf-8")
    assert f'description = "{PROJECT_DESCRIPTION}"' in pyproject
    assert "MIT License" in (repository_root / "LICENSE").read_text(encoding="utf-8")


def test_root_git_metadata_is_allowed_but_nested_git_is_rejected(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    for name in MANAGED_CONTENT_ROOTS:
        (tmp_path / name).mkdir()
    assert _nested_git_metadata(tmp_path) == []

    (tmp_path / "src" / "vendor" / ".git").mkdir(parents=True)
    assert _nested_git_metadata(tmp_path) == ["src/vendor/.git"]


def test_public_files_do_not_use_retired_short_identifiers(repository_root: Path) -> None:
    forbidden = [
        left + right
        for left, right in (
            ("S", "1"),
            ("S", "2"),
            ("S", "3"),
            ("C", "5"),
            ("C", "8"),
            ("G", "0"),
            ("p", "25"),
            ("v", "25"),
        )
    ]
    pattern = re.compile(
        r"(?<![A-Za-z0-9])(?:" + "|".join(forbidden) + r")(?![A-Za-z0-9])",
        re.IGNORECASE,
    )
    roots = (
        repository_root / "src",
        repository_root / "configs",
        repository_root / "docs",
        repository_root / "tests",
        repository_root / "tools",
    )
    standalone = (
        repository_root / "README.md",
        repository_root / "AGENTS.md",
        repository_root / "outputs" / "README.md",
        repository_root / "pyproject.toml",
        repository_root / ".env.example",
    )
    hits: list[str] = []
    paths = [path for root in roots for path in root.rglob("*") if path.is_file()]
    paths.extend(standalone)
    oracle_audit_files = {
        repository_root / "tests" / "fixtures" / "prompts" / "provenance.json",
        repository_root / "tests" / "fixtures" / "prompts" / "representative_input.json",
        repository_root / "tools" / "verify_legacy_prompt_oracle.py",
    }
    for path in paths:
        if path.name == "uv.lock" or "__pycache__" in path.parts:
            continue
        if path in oracle_audit_files:
            # These internal audit fixtures must retain exact legacy paths and
            # field names. They are the only narrow exceptions to semantic names.
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if pattern.search(content):
            hits.append(path.relative_to(repository_root).as_posix())
    assert hits == []


def test_completion_documentation_matches_two_layer_acceptance(repository_root: Path) -> None:
    generated_outputs = (repository_root / "outputs" / "README.md").read_text(encoding="utf-8")
    physical_protocol = (repository_root / "docs" / "physical_protocol.md").read_text(
        encoding="utf-8"
    )
    run_artifacts = (repository_root / "docs" / "run_artifacts.md").read_text(encoding="utf-8")
    for document in (generated_outputs, physical_protocol, run_artifacts):
        normalized = " ".join(document.split())
        assert "EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED" in normalized
        assert "RUN-INVALID" in normalized
        assert "must not publish `completion.json`" in normalized


def test_terminal_transport_documentation_matches_evidence_finalization(
    repository_root: Path,
) -> None:
    generated_outputs = (repository_root / "outputs" / "README.md").read_text(encoding="utf-8")
    run_artifacts = (repository_root / "docs" / "run_artifacts.md").read_text(encoding="utf-8")
    for document in (generated_outputs, run_artifacts):
        normalized = " ".join(document.split())
        assert "terminal model-transport failure" in normalized
        assert "secret scan" in normalized
        assert "metrics.json" in normalized
        assert "verification.json" in normalized
    assert "No `completion.json` is published" in " ".join(generated_outputs.split())
    assert "never publishes `completion.json`" in " ".join(run_artifacts.split())


def test_production_source_has_no_case_identity_control_literals(repository_root: Path) -> None:
    forbidden = {
        "bestest_air",
        "multizone_office_simple_hydronic",
        "multizone_office_simple_air",
        "SZ_Air",
        "MZ_Hydro",
        "MZ_Air",
    }
    hits: list[tuple[str, str]] = []
    for path in (repository_root / "src" / "h3c").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value in forbidden
            ):
                hits.append((path.relative_to(repository_root).as_posix(), node.value))
    assert hits == []


def test_graph_source_documents_exist(repository_root: Path) -> None:
    import json

    for path in (repository_root / "configs" / "graphs").glob("*_confirmed.json"):
        graph = json.loads(path.read_text(encoding="utf-8"))
        for source in graph["sources"]:
            document = source.split("#", 1)[0]
            assert (repository_root / document).is_file()


def test_agent_framework_is_isolated_to_offline_package(repository_root: Path) -> None:
    hits: list[str] = []
    for path in (repository_root / "src" / "h3c").rglob("*.py"):
        if "offline" in path.relative_to(repository_root / "src" / "h3c").parts:
            continue
        content = path.read_text(encoding="utf-8")
        if "agent_framework" in content or "agent-framework" in content:
            hits.append(path.relative_to(repository_root).as_posix())
    assert hits == []
