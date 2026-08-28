# Hierarchical Causal-Constrained Control (H3C)

H3C is a clean, cooling-only implementation of hierarchical causal-constrained
agents for building control. It is structured so this directory can become an
independent GitHub repository without carrying historical experiment machinery.
Accordingly, repository metadata at `H3C/.git` is valid when this directory is
used as the repository root; nested `.git` metadata below managed content such
as `src/`, `configs/`, `tests/`, `tools/`, `docs/`, or `outputs/` is forbidden.

Orchestrator and Executor rationales are audit-only nonempty strings. H3C keeps
their raw and parsed text in full, reports character lengths as non-decisional
telemetry, and never changes a control decision merely because rationale text is
long. Structural JSON, program, causal, budget, settlement, identity, and secret
contracts remain fail closed.

The parser accepts a small set of control-neutral model wrappers seen in real
runs: a sole `allocation_contract` wrapper around an otherwise valid allocation,
an extra root audit rationale, an exactly duplicated `root.patch`, and a
`replace_rule.id` equal to `rule.id`. Every normalized control object still goes
through the same strict validators; conflicting or unknown fields are rejected.

The implementation was migrated from a read-only production oracle at source
commit `ca272196891a90b2a8e26b7b7a12e3508882b670`. Physical and paid commands are
dry plans unless `--execute` is supplied.

## Repository layout

- `src/h3c/`: production package and the `h3c` command.
- `configs/`: case, experiment, graph, executable-program, and offline-onboarding declarations.
- `tests/`: unit, integration, contract, and tracked golden fixtures.
- `docs/`: architecture, protocols, migration decisions, and operator guidance.
- `outputs/`: ignored run artifacts and generated reports.

Generated artifacts belong under `outputs/runs/`, `outputs/reports/`, and
`outputs/offline/`. They are not source evidence and are not committed.

## Install and verify

Python 3.11 or newer is required.

```console
uv sync --extra dev
uv run ruff check src tests
uv run mypy --strict src/h3c tests
uv run pytest
```

`pyproject.toml` and `uv.lock` are the dependency source of truth. The generated
`requirements.txt` and `requirements-offline.txt` files are pip-compatible
exports for environments that do not use uv; do not edit them independently.

Install the isolated Mapping and HITL causal-discovery workflow only when it is
needed:

```console
uv sync --extra offline
```

## Command surface

The following commands print a resolved dry plan and make no API or physical
service calls unless `--execute` is present:

```console
h3c run --profile SZ_Air
h3c suite main
h3c suite memory
h3c suite causal-ablation
h3c suite graph-sensitivity
h3c suite coordination-ablation
h3c suite thinking-ablation
h3c suite all
h3c smoke release-6h
```

Completed run directories can be checked and summarized with:

```console
h3c verify outputs/runs/<suite>/<profile>/<run_id>
h3c report outputs/runs/<suite>/<profile>/<run_id>
h3c report outputs/runs/<suite>
```

The human-in-the-loop graph workflow is:

```console
h3c graph prepare --profile SZ_Air --source <source> --output <prepared-file>
h3c graph propose --input <prepared-file> --output <proposed-file>
h3c graph validate --input <proposed-file>
h3c graph confirm --input <proposed-file> --reviewer <name> --date <date> --output <confirmed-file>
h3c graph derive --input <confirmed-file> --mutation <mutation-file> --output <variant-file>
```

`prepare` only creates a machine-readable candidate. A human or external review
process must edit and review its structured nodes and edges before `propose` and
must explicitly approve the proposed content before `confirm`. Running these
commands is not, by itself, human confirmation.

New cooling cases can be onboarded through two real human review pauses:

```console
h3c offline discover --spec configs/onboarding/example_spec.json
h3c offline discover --spec configs/onboarding/example_spec.json --reviewer <name> --execute
h3c offline resume outputs/offline/<case>/<workflow_id> --reviewer <name> --execute
h3c offline verify outputs/offline/<case>/<workflow_id>
h3c offline export outputs/offline/<case>/<workflow_id> \
  --case-profile configs/cases/<new-case>.json \
  --graph configs/graphs/<new-case>_confirmed.json \
  --provenance configs/graphs/<new-case>_provenance.json
```

This optional workflow uses Microsoft Agent Framework for offline Mapping and
causal discovery only. Online control remains on H3C's custom deterministic
runtime. See [offline onboarding](docs/offline_onboarding.md).

See [architecture](docs/architecture.md), [physical protocol](docs/physical_protocol.md),
[run artifacts](docs/run_artifacts.md), [graph provenance](docs/graph_provenance.md),
[offline onboarding](docs/offline_onboarding.md), and the
[operator guide](docs/operator_guide.md). The completed Hydro compatibility
review is recorded in [its post-result note](docs/hydro_schema_compatibility_review.md).
