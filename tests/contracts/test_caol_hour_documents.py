from __future__ import annotations

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
        assert "ELIGIBLE LONG-TERM EXPERIENCE SLOTS" in document
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
