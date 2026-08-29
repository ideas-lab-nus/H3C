from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from h3c.offline.artifacts import OfflineArtifactError
from h3c.offline.artifacts import source_commit as offline_source_commit
from h3c.runtime.source_identity import committed_source_identity


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        [
            "git",
            "-c",
            "user.name=H3C Test",
            "-c",
            "user.email=h3c-test@example.invalid",
            "-C",
            str(repository),
            *arguments,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def test_committed_source_identity_requires_clean_repository_root(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init")
    source = repository / "source.txt"
    source.write_text("frozen\n", encoding="utf-8")
    _git(repository, "add", "source.txt")
    _git(repository, "commit", "-m", "initial")
    expected = _git(repository, "rev-parse", "HEAD")

    assert committed_source_identity(repository) == expected

    source.write_text("dirty\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="clean committed Git worktree"):
        committed_source_identity(repository)
    with pytest.raises(OfflineArtifactError, match="clean committed repository root"):
        offline_source_commit(repository)

    source.write_text("frozen\n", encoding="utf-8")
    (repository / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="clean committed Git worktree"):
        committed_source_identity(repository)

    nested = repository / "nested"
    nested.mkdir()
    with pytest.raises(RuntimeError, match="repository root"):
        committed_source_identity(nested)
