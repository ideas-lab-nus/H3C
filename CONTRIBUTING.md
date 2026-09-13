# Contributing

Contributions that improve correctness, documentation, portability, or offline verification are
welcome. Open an issue before proposing a change to the scientific protocol, prompts, control
logic, causal contract, reward, or evaluation windows.

## Development setup

```console
uv sync --frozen --extra dev --extra offline --extra baselines
uv run --no-sync pytest
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy src tools/export_paper_agent_matrix.py tools/verify_paper_reference_results.py tools/verify_canonical_runtime.py
```

Physical and model-service commands are dry plans by default. Pull requests must not execute paid
model calls or BOPTEST experiments in CI, include credentials or private endpoints, overwrite run
evidence, or silently change a registered scientific identity.

Keep changes focused. Add a regression test for behavioral code changes, update the relevant
machine-readable contract, and describe any scientific compatibility boundary in the pull request.
