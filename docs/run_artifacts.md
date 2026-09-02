# Run artifact contract

Run paths are `outputs/runs/<suite>/<profile>/<run_id>/`. A run directory is
created only if absent and is never appended to or overwritten. An eligible
`h3c resume` recovery creates a different run directory and fresh BOPTEST test,
replays the source's atomic completed-hour physical prefix, and records the
immutable source lineage in `resolved_config.yaml` and `timing.jsonl`.

All editable declarations under `configs/` are strict JSON files. The historical
artifact filename `resolved_config.yaml` is retained as a public run-contract
name, but its bytes are canonical JSON (which is also valid YAML). It freezes the
complete case profile, method switches, runtime request contract, resolved
confirmed graph and declared mutation when applicable. A graph-disabled run
contains no resolved graph payload.

`manifest.json` binds the source commit, plan identity, endpoint identities,
model contract, expected role-call count, lifecycle counts, replay result, and
retry/transport/fallback/secret counters. A clean release requires terminal
transport, fallback, and secret counters to be zero. The retry counter may be
nonzero only when the attempt stream independently proves a bounded recovery of
a registered transient model connection failure. A validated deterministic allocation fallback is recorded as a
model-contract degradation, never hidden as a clean result. The manifest also
counts every configured occupancy missing-value resolution. Agent manifests
distinguish a pending secret scan from a completed scan; the final success and
failure paths both perform the real scan before freezing the manifest. Endpoint
identities are hashes of endpoint names; credentials and credential-derived
hashes are never recorded.

The JSON-lines streams retain physical conditioning, per-zone control steps,
hourly routing/settlement, program admission outcomes, role calls, raw prompt and
model content, every model wire attempt, and timing. `model_request_attempts.jsonl`
keeps request/logical identities, attempt order, retryability, outcome, and
latency without recording the endpoint or credential. It also distinguishes a
confirmed response with recorded usage from an interrupted request whose
provider-side charge status is unknown. Conditioning rows distinguish raw occupancy from its
resolved value. Every evaluation zone-step row records the frozen test id, and
the timing stream records exact initialized/evaluation-start/evaluation-complete/
stopped lifecycle events with that same id. It also records the point, phase,
index, absolute time, documented occupancy class, rule, preceding value,
resolved value, and source for every permitted occupancy resolution.
`forecast_inputs.json` preserves the exact source and resolved forecast bundle used by the
evaluation. The online and baseline verifiers replay the shared missing-occupancy resolution
owner from that source bundle and require both the resolved values and emitted audit events to
match.
`performance.csv` and `metrics.json` contain only the evaluation window.

For a recovery run, imported completed-prefix Agent call/attempt evidence is
joined to newly issued calls by logical identity. Every physical prefix step is
executed again from the registered initial state under the fresh test identity;
observation, program interpretation, action assurance, action, outcome and KPI
must match before the first new Agent call. The verifier recomputes the prefix
identity and recovery lineage and rejects reuse of the source test identity.

Artifact schema version 3 ties each valid Orchestrator/Executor raw output to the
complete parsed rationale stored in `hourly_decisions.jsonl` or
`program_updates.jsonl`. The same rows carry character-length telemetry with
`decision_use=none`; no normalization or truncation field exists. Metrics and
reports aggregate counts, totals, and maxima without using length to classify or
control a run.

The verifier does not trust logged booleans or aggregate counts. It rechecks the
exact CSV/JSON-lines schemas and timelines, per-step zone set, physical and cost
alignment, reward, action assurance, full program ledger and validation chain,
shared-budget settlement, role/raw-call correspondence, request/usage contract,
model attempt/retry accounting, model and plan identity, conditioning prefix,
evaluation boundary, metrics,
thinking route, causal/coordination surfaces, graph stable IDs and declared
single mutation, occupancy-resolution classification, failure counters, and
completion ordering.
It also recomputes raw-to-parsed rationale equality and every length telemetry
field; raw, parsed, telemetry, or metric tampering is execution-invalid.

The default synchronous path runs the full pre-completion verification once.
Only a complete, evidence-consistent physical lifecycle may then publish
`completion.json` through a flushed atomic rename. A completion records either
`RELEASE-PASS` or `EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED`; only the first is
a clean release result. `RUN-INVALID` is a verifier classification and must not
publish `completion.json`. Directory existence, a manifest, or partial logs
never mean that a run completed.

Batch execution may instead use `--defer-full-verification`. After BOPTEST has
stopped, the bounded collection gate parses every declared stream, checks the
final atomic checkpoint, lifecycle and identities, verifies exact row and call
counts and the continuous timeline, recomputes KPI through the production
metrics owner, and requires a completed zero-exposure secret scan. It then
atomically publishes `collection_complete.json` with
`COLLECTION-COMPLETE / FULL-AUDIT-PENDING`. That marker freezes the core runtime
evidence and permits the physical execution lock to be released; it is not a
fully audited result and is not eligible for the valid-results dataset.

`h3c finalize <run-directory>` accepts only a stopped, collection-complete run,
rechecks the collection evidence, and performs exactly one full zero-network
audit. It may then add `verification.json` and the final atomic
`completion.json`. An execution-invalid audit publishes terminal failure
evidence instead. Repeated finalization is rejected.

A terminal model-transport failure takes a separate fail-closed finalization
path: it first completes the secret scan and manifest, then writes partial
`metrics.json` and recomputed `verification.json`, and never publishes
`completion.json`. The terminal verifier reconstructs the exact next logical
call, request body and identity, attempt order, retry count, retryability, and
provider-charge status from `model_request_attempts.jsonl`. Partial physical KPI
values describe only rows already present and are not comparable completed-run
metrics.
