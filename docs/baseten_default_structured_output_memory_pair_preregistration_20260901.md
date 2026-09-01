# Baseten default, structured-output recovery, and MZ Air memory-pair preregistration

## Decision and evidence boundary

The user selected `baseten-deepseek` as the default online model provider and authorized the
previously planned MZ Air CAOL-only versus three-regime long-term-memory pair to run in parallel.
This addendum is written before any new API call or physical trajectory.

The repaired-envelope Baseten diagnostic from source `0963f893b09359762717d96213406136e50a7a20`
completed all 42 logical calls and 24 physical advances. Its three remaining Executor schema
degradations were:

1. two otherwise parseable edit operations omitted method-required `causal_edge_ids`;
2. one syntactically valid JSON object included an additional empty-string root field.

These are output-generation contract deviations, not excessive causal, program, Budget, Safety,
or physical-runtime checks. Baseten documents structured outputs as supported by all Model API
models, including reasoning-capable models, so these deviations are not accepted as unavoidable
until the provider-native schema path is tested.

## Only allowed implementation changes

1. Change the runtime default provider from `deepseek-official` to `baseten-deepseek`.
2. For Baseten calls only, replace JSON-object mode with OpenAI-compatible strict JSON-schema
   structured output. The schema is generated from the existing role/parser contract owner:
   Orchestrator allocation, Executor single-operation patch, and Reflector lesson/optional-memory
   response. The schema may prevent missing required fields, extra fields, wrong primitive types,
   and wrong root envelopes; it must not make a semantically invalid control operation valid.
3. Keep Official DeepSeek registered as an explicit non-default provider using its existing
   JSON-object request mode.

Frozen and unchanged: all Agent system/user Prompt text, C0, `occupancy_routed` low thinking,
`thinking={type:enabled}`, `reasoning_effort=low`, omission of `temperature/top_p`, model weights,
program operations, causal admission, Budget, Safety, P0, action mapping, reward, KPI definitions,
working-memory content, and three-regime experience mechanics. Structured-output use is part of
the exact request/run identity and evidence.

## Real-API contract gate

Before BOPTEST execution, send exactly six non-physical Baseten calls without retry:

- the three completed diagnostic Executor inputs that produced the deviations above;
- three frozen holdout Executor inputs from the same completed diagnostic.

Every request must use the production renderer, the Baseten strict Executor schema, thinking
enabled with low effort, no `temperature/top_p`, and a secret-free evidence sink. Adoption requires
six provider responses, `finish_reason=stop`, exact response-model identity, parseable usage, exact
singleton patch envelopes, and zero structural schema rejection by the unchanged resolver. A
semantically inadmissible but structurally valid patch is recorded and does not fail this format
gate. Any structured-output API incompatibility or non-structural behavior change stops before
BOPTEST and requires review; no fallback to prompt padding or permissive repair is allowed.

## Parallel MZ Air pair

After targeted and full offline gates, generated-document freshness, staged-manifest review, and
secret scan, freeze one clean source commit and start two independent fresh arms concurrently:

1. `CAOL-only`: `--long-term-memory` absent, with zero memory/CRUD/reference surface.
2. `CAOL+regime-memory`: `--long-term-memory` present, enabling exactly the registered three
   regime slots per zone.

Both arms use the same Baseten default, MZ Air day 199, seven-day internal warm-up, zero explicit
prefix, seven-day formal evaluation, official occupancy owner, `k=1`, C0, occupancy-routed low
thinking, graph, coordination, Budget, Safety, reward, action mapping, and strict role schemas.
They use separate worktrees, output owners, execution locks, run identities, BOPTEST test IDs, and
Baseten session-affinity values. Within each hour the frozen order remains Orchestrator, five
parallel Executors, deterministic settlement, four physical advances, then Reflector.

Each arm receives an independent 30-minute heartbeat. Ordinary semantic rejection, reference/CRUD
rejection, poor KPI, or model-contract degradation continues and is preserved. A physical,
timeline, identity, secret, or evidence hard stop affects only that arm. A fresh replacement is
allowed only after a control-neutral mechanical diagnosis and complete offline gates; no resume,
overwrite, prompt change, criterion change, or lucky performance rerun is allowed.

The frozen thresholds and mechanism-chain requirements remain exactly those in
`docs/mz_air_caol_regime_memory_preregistration_20260831.md`. Completion stops at a local review
point without push or paper/LaTeX/Figure 3 edits.
