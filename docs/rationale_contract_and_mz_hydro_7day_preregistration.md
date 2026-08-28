# Rationale contract repair and MZ_Hydro seven-day comparison preregistration

Status: frozen on 2026-08-28 before changing production code, Prompt bytes,
schemas, runtime artifacts, verification, reports, fixtures, case duration, or
calling the model/BOPTEST services.

## Public ruling and evidence boundary

The user ruled that Orchestrator and Executor `rationale` text is non-execution
audit information. A 240-character storage convention is not a valid condition
for accepting an otherwise-valid allocation or patch. Under the new contract:

- every rationale must still be a string and must remain nonempty after
  whitespace stripping;
- legal rationale text has no method-level character limit, is never truncated,
  and is preserved in full in both raw and parsed evidence;
- rationale length may be reported as non-decisional telemetry only;
- length alone cannot cause model-contract degradation, allocation fallback,
  patch rejection, or a tool-generated deterministic `no_change`;
- the provider request and its existing output-token boundary are unchanged;
- Reflector's one-sentence `insight_text` contract is outside this ruling and
  remains unchanged.

This is a non-execution text-contract correction, not a control-method design.
It changes no control law, model, thinking route, weather surface, causal graph,
coordination rule, working memory, action assurance, BOPTEST point mapping, or
KPI definition. Consequently no new method claim or literature-derived control
mechanism is introduced.

The final-source release matrix under runtime source
`8a58a84c7e82e3dd48b0e72cf065033c895edcd0` remains immutable historical
evidence interpreted by that source's old contract. Its reports, completions,
raw streams, and classifications must not be rewritten, copied into a new run,
or reverified as though they were produced by the new source.

## Implementation question and sole behavioral variable

Question: after removing only the rationale-length decision, do the production
parser, schema validators, control-validation chain, artifact writer, metrics,
reporter, and verifier preserve otherwise-valid Orchestrator allocations and
Executor patches exactly while every genuinely executable or structural error
continues to fail closed?

The sole behavioral variable is the validation meaning of Orchestrator
`rationale_per_zone` values and Executor operation `rationale`: exact-zone,
nonempty strings remain required, but string length is not an acceptance
criterion. The old Orchestrator truncation/normalization exception and its
model-contract degradation path are retired. A single production-owned
rationale telemetry representation must expose original parsed lengths without
normalizing text or influencing control.

The implementation must synchronize:

1. the paired English/Chinese Prompt owner and rendered machine contracts;
2. role parsing and validation;
3. program and allocation validation;
4. raw and parsed artifact persistence;
5. production verification, metrics, and report rendering;
6. schema identities, golden fixtures, documentation, and negative tests.

Unknown fields, invalid bare JSON, incorrect root/list shape, missing fields,
non-string or blank rationale, zone-set mismatch, invalid program content,
causal admissibility/direction proof/budget/settlement failures, identity,
secret, transport, physical lifecycle, and evidence-integrity checks remain
strict and fail closed.

## Frozen offline replay corpus and gates

The replay corpus is post-result diagnostic input drawn read-only from all final
source `8a58a84` release-smoke responses whose Orchestrator or Executor rationale
exceeded 240 characters. It contains exactly eleven raw outputs: all six
SZ_Air Orchestrator allocations (rationale lengths 297, 295, 280, 308, 308,
and 351) plus five MZ_Air Executor `no_change` patches (477, 364, 264, 246,
and 242). The tracked fixture must bind the old source, run identity, role,
hour/step/zone, raw output, parsed rationale lengths, and fixture hash. This
selection is not represented as a prospective result; it is a fixed regression
corpus for the already-observed failure mode.

Before any real call, require all of the following:

- all eleven raw outputs replay through the final production parser/validator;
- every Orchestrator allocation preserves the complete rationale and otherwise
  identical allocation, then passes normal allocation and settlement checks;
- every Executor patch preserves the complete rationale and proceeds to the
  normal program-validation chain rather than becoming a schema-generated
  `no_change`;
- raw and parsed text, length telemetry, metrics, and report fields agree;
- no code path slices, clips, truncates, or substitutes accepted rationale text;
- tampering with raw/parsed rationale or length telemetry fails verification;
- invalid bare JSON, an unknown `id` on `no_change`, empty/non-string rationale,
  and genuinely invalid control content remain rejected;
- Prompt golden tests prove that Orchestrator and Executor no longer request a
  short rationale in either language or machine contract, while Reflector's
  single-sentence language is unchanged;
- pytest, Ruff check/format, strict mypy, `uv lock --check`, Prompt oracle,
  CLI/profile/config/secret/scope/standalone-root, schema, reverse/tamper, and
  fake-physical gates all pass on one clean committed implementation source.

The implementation source is not stable until every tracked production,
fixture, documentation, and test change is committed and the worktree is clean.

## Focused MZ_Hydro six-hour release smoke

After the offline gates pass, execute exactly one fresh main H3C Agent smoke for
`MZ_Hydro`: seven days requested server warm-up, seven explicit days of vanilla
RBC on the same test id (25 degC occupied, 30 degC unoccupied), then six hours
of evaluation from program version zero, an empty accepted ledger, and empty
Agent memory. The expected logical calls are Orchestrator/Executor/Reflector
`6/12/6`, total 24. Model connection transport may use the already-registered
two additional identical-wire attempts after 1 s and 2 s without advancing the
physical service. No model-schema or physical request is retried.

Create a dedicated ten-minute native completion heartbeat after the real process
starts. It may inspect only this arm's unique `completion.json` until completion.

The smoke passes only if production verification returns `RELEASE-PASS`, every
execution-integrity and model-contract check is clean, terminal transport,
fallback, secret, and evidence errors are zero, and every accepted rationale is
preserved raw and parsed with matching non-decisional length telemetry. A
model-contract degradation, terminal process without completion, or any hard
stop below ends the sequence. There is no lucky rerun.

## Frozen full MZ_Hydro comparison

The user explicitly superseded the prior five-day Hydro duration for this new
comparison and requires a complete seven-day evaluation. This changes the
shared experiment duration, not the controller or KPI definitions. The
MZ_Hydro profile therefore declares seven formal evaluation days for both arms.

After and only after the focused smoke passes, automatically execute the
following fresh arms in order under the exact same new source commit:

1. deterministic zero-API baseline: seven-day server warm-up, seven-day vanilla
   RBC prefix, seven-day evaluation; expected model calls zero;
2. main H3C Agent: the identical lifecycle and duration; expected logical calls
   Orchestrator/Executor/Reflector `168/336/168`, total 672, with wire attempts
   accounted separately.

Both arms use separate fresh test ids and run directories but must match on case
profile, point mapping, seven-day protocol, conditioning-prefix identity,
evaluation-boundary identity, source, and physical endpoint identity. Model and
secret identity apply to the Agent arm; the baseline is zero API. The baseline
gets a dedicated three-minute completion heartbeat and the Agent a dedicated
ten-minute heartbeat. Each completion is read once, its own heartbeat is
deleted, production verification runs, and the single registered next arm starts
automatically. Implementation completion, offline gates, smoke completion, and
baseline completion are not user approval points.

No three-case formal suite, ablation, additional smoke, retry run, or push is in
scope.

## Hard stops and outcome handling

Initialization/advance/stop lifecycle failure, test-id change, source/profile/
protocol/prefix/boundary/model/request/endpoint identity mismatch, secret leak,
artifact corruption, incomplete evidence, or exhausted terminal model transport
is a hard stop. The current arm is preserved, no replacement run starts, and the
failure is reported.

Ordinary valid deterministic program, causal, direction, budget, or settlement
rejection is recorded and does not by itself stop a completed Agent arm. Any
remaining invalid JSON/schema response is contained fail closed without retry;
the final Agent classification and all metrics are reported honestly and the
arm is not rerun.

## Frozen final outputs

The final tracked result must bind the new source and provide:

- old/new rationale contract diff and the eleven-output production replay;
- focused smoke identity, verification, contract telemetry, and call accounting;
- baseline/Agent cost, energy, zone-hours, PMV-hours, occupied peak absolute PMV,
  setpoint total variation, direction reversals, comfort crossings, program
  updates, causal/budget rejections, assurance triggers, logical calls, routes,
  wire attempts, tokens, latency, and estimated USD/CNY cost;
- common physical protocol, conditioning-prefix and evaluation-boundary identity,
  timing/time-series references, classification, mechanism interpretation, and
  limitations;
- synchronized architecture/Prompt/artifact/operator docs, current `CLAUDE.md`,
  decision log, notes index, result note, and tracked machine-readable summary.
