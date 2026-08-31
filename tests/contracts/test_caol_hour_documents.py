from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def test_complete_hour_documents_match_production_renderer(repository_root: Path) -> None:
    completed = subprocess.run(
        [sys.executable, "tools/generate_caol_hour_io_docs.py", "--check"],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    for language in ("en", "zh"):
        document = (repository_root / "docs" / f"h3c_complete_hour_io_{language}.md").read_text(
            encoding="utf-8"
        )
        assert "ACTIVE LONG-TERM EXPERIENCES" in document
        assert "WORKING MEMORY" in document
        assert "memory_operations" in document
        assert "Memory-off East Executor complete request" in document
        assert "ACTIVE LONG-TERM EXPERIENCE SLOTS" in document
        assert "EMPTY LONG-TERM EXPERIENCE SLOTS" in document
        assert "[omitted]" not in document.lower()
        assert "<!-- omitted" not in document.lower()
        fence = "`" * 3
        blocks = re.findall(
            re.escape(fence + "json") + r"\n(.*?)\n" + re.escape(fence),
            document,
            re.DOTALL,
        )
        requests = [
            value
            for value in (json.loads(block) for block in blocks)
            if isinstance(value, dict) and "messages" in value
        ]
        assert requests
        for request in requests:
            model_text = "\n".join(str(message["content"]) for message in request["messages"])
            assert re.search(r"\bCAO(?:L)?\b", model_text) is None
            dynamic_text = str(request["messages"][1]["content"])
            assert not re.search(
                r"\b(?:decision_hour|latest_completed_step|target_action_steps|"
                r"sample_index|physical_step|time_seconds)\b|\"step(?:_ahead)?\"\s*:",
                dynamic_text,
            )
            assert re.search(r"\b\d{4}-\d{2}-\d{2}\b", dynamic_text) is None


def test_semantic_clock_character_counts_and_prompt_bundle_identity(
    repository_root: Path,
) -> None:
    document = (repository_root / "docs" / "h3c_complete_hour_io_en.md").read_text(encoding="utf-8")
    fence = "`" * 3
    blocks = re.findall(
        re.escape(fence + "json") + r"\n(.*?)\n" + re.escape(fence),
        document,
        re.DOTALL,
    )
    requests = [
        value
        for value in (json.loads(block) for block in blocks)
        if isinstance(value, dict) and "messages" in value
    ]
    totals = tuple(
        sum(len(str(message["content"])) for message in requests[index]["messages"])
        for index in (0, 2, 6)
    )
    assert totals == (5441, 6942, 5555)
    assert sum(totals) <= 18086

    golden = json.loads(
        (repository_root / "tests" / "fixtures" / "prompts" / "caol_prompt_golden.json").read_text(
            encoding="utf-8"
        )
    )
    golden.pop("schema_version")
    payload = json.dumps(golden, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    bundle_identity = hashlib.sha256(payload).hexdigest()
    report = (repository_root / "docs" / "h3c_context_compaction_report.md").read_text(
        encoding="utf-8"
    )
    assert f"sha256:{bundle_identity}" in report
