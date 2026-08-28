# Generated outputs

Each run is written to `runs/<suite>/<case>/<run_id>/`. Reports are written to
`reports/`. Both generated trees are ignored by Git; only their placeholder files
are tracked. A completed run writes all declared artifacts before atomically
publishing `completion.json` last.

Offline onboarding workspaces are written to
`offline/<case>/<workflow_id>/`. They are separate from physical runs and reports,
are ignored by Git, and are never treated as experimental evidence. Their schema is
documented in `docs/offline_onboarding.md`.

An approved offline workspace contains `resolved_spec.json`,
`source_manifest.json`, Mapping and causal proposal/review JSONL streams,
`confirmed_mapping.json`, `case_profile_candidate.json`,
`confirmed_causal_graph.json`, `causal_provenance.json`, `model_calls.jsonl`,
`raw_model_io.jsonl`, file checkpoints, `verification.json`, and an atomic final
`completion.json`. Interrupted workspaces intentionally remain incomplete and
can resume only under the documented identity and network-interruption rules.

A complete run contains:

- `resolved_config.yaml`
- `manifest.json`
- `physical_conditioning.jsonl`
- `performance.csv`
- `zone_steps.jsonl`
- `hourly_decisions.jsonl`
- `program_updates.jsonl`
- `agent_calls.jsonl`
- `raw_model_io.jsonl`
- `model_request_attempts.jsonl`
- `timing.jsonl`
- `metrics.json`
- `verification.json`
- `completion.json`, published last by atomic rename

A failed or degraded run is retained in place. A complete, evidence-consistent
physical lifecycle with healthy execution integrity may atomically publish an
`EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED` completion when one or more model
calls violate their contract; that class is not a clean release. A
`RUN-INVALID` or incomplete lifecycle records the artifacts available at the
failure point and must not publish `completion.json`.

After a terminal model-transport failure, the finalization path performs a real
secret scan, freezes the terminal counters in `manifest.json`, writes a partial
`metrics.json`, and writes a fail-closed `verification.json`. Those two files
audit attempt sequencing and failure identity; their physical KPI fields cover
only evaluation rows that actually existed and are not a completed-run result.
No `completion.json` is published.

`model_request_attempts.jsonl` records every model wire attempt separately from
the one-row-per-logical-call `agent_calls.jsonl` and `raw_model_io.jsonl`
streams. A recovered transient connection may therefore make the attempt count
larger than the logical call count; manifest, metrics, and verifier recompute the
difference. BOPTEST remains single-attempt.

When a case declares a documented occupancy missing-value policy,
`physical_conditioning.jsonl` keeps separate raw and resolved occupancy maps,
`timing.jsonl` records each resolution, and `manifest.json` records the exact
resolution count. Other missing forecast fields are never repaired.
