# Operator guide

## Dry planning

Run, suite, and smoke commands are dry by default. Inspect the printed profile,
method factors, run identities, and expected call total before adding
`--execute`. `h3c smoke release-6h` must resolve to 3 zero-model baselines,
10 Agent arms, and 372 expected model calls.

The historical final-source 13-arm release smoke is complete: it recorded 372 confirmed
logical responses in 372 outbound attempts, with zero transport retry. Preserved
superseded/failed runs contribute another 344 confirmed responses and one
outbound attempt whose provider completion is unknown. The cumulative record is
therefore 716 confirmed responses and 717 outbound attempts. The release smoke
has zero calls remaining. Under the current seven-day Hydro declaration, the
three-case `all` suite dry plan contains 18,312 logical calls. This task
authorizes only the separately preregistered focused Hydro smoke and Hydro
baseline/Agent pair, not that full suite. Planned calls must never be reported
as calls already made.

## Environment

Set the following locally. Never commit the values or copy credentials into a
run directory.

- `H3C_BOPTEST_ENDPOINT`
- `H3C_MODEL_ENDPOINT`
- `H3C_MODEL_API_KEY`

The model name, endpoint/key environment-variable names, and request parameters
are frozen in `configs/experiments/runtime.json`. Thinking-enabled calls use low reasoning
effort without sampling parameters. No-thinking calls use temperature 0 and
top-p 1. Every request is stateless.

## Execution

Before a release smoke:

1. Obtain an explicit release from the root audit Session. Until that release,
   no physical arm may start, including a zero-model baseline, and the stale
   execution lock must remain untouched.
2. Confirm the worktree is clean and record the actual branch `HEAD` that will
   be written into runtime identity; a prior implementation-only commit is not
   an acceptable substitute.
3. Run pytest, Ruff, strict mypy, configuration validation, golden Prompt and
   behavior fixtures, and fake-BOPTEST integration tests.
4. Confirm the release-smoke preregistration and graph variants are committed.
5. Execute one fresh arm at a time. For each real arm, record the process id,
   target, control, unique completion path, and a dedicated ten-minute completion
   heartbeat.
6. Do not inspect partial result logs while an arm is live. On completion, stop
   its heartbeat, run `h3c verify`, report the arm, and follow only the registered
   next branch.

Use `--arm-index 0` through `--arm-index 12` to select exactly one registered
release-smoke arm for independent supervision. Run indices in ascending order;
the unfiltered command remains the complete dry plan.

Every formal suite also accepts `--arm-index <n>` so that one registered arm can
be supervised and verified before the next arm starts. An omitted evaluation
duration resolves to the selected profile's formal duration; an explicit value
must be either the registered six-hour smoke or that same formal duration.

Do not launch the three-case formal suite as part of the focused Hydro work.
Current formal evaluation is profile-owned and seven days for every profile.

`h3c report <run-or-suite-directory>` reports one explicit completed run or one
suite directory. Comparisons fail closed when source, protocol, conditioning
prefix, or evaluation-boundary identities are incompatible. Generated JSON,
Markdown, and time-series references remain under `outputs/reports` unless an
explicit output directory is supplied.

## Failure handling

Never resume or delete a failed directory. Transport, physical lifecycle,
identity, secret, and artifact failures stop serial execution. Valid deterministic
patch rejections and poor KPI values remain recorded method outcomes. A safe,
single-call model-contract rejection completes the physical lifecycle without a
retry and may publish an atomic
`EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED` completion. It must never be reported
as the clean `RELEASE-PASS` class.

The only internal request retry is the runtime-contract-owned model transport
recovery: at most two extra attempts after a reset/abort/broken pipe, timeout,
DNS failure, truncated response, or TLS EOF. It waits one second and then two
seconds, reuses the identical logical request, and cannot advance BOPTEST or
apply an action between attempts. HTTP/provider responses, authentication,
rate limits, malformed JSON, role/schema rejection, and BOPTEST requests are
not retried. Inspect `model_request_attempts.jsonl` for each attempt and its
provider-charge status; an interrupted response is conservatively marked as
having unknown provider-side charge status.

If the bounded attempts terminate without a response, the run remains
`RUN-INVALID`. After physical stop, H3C performs the final secret scan and writes
partial metrics plus fail-closed verification so the terminal attempt contract
can be independently audited. It does not publish completion and serial
execution does not start the next arm.

If an execution lock already exists, H3C reports the exact lock path and recorded
PID and never removes it automatically. The operator must first inspect the PID
and process command line read-only. Only after proving that no matching process
is alive may the operator manually remove that exact lock file; never delete a
lock merely because it is old.

## Human graph review

`h3c graph prepare` creates a candidate document; it does not discover or
confirm causal structure. A human or authorized external review process must
edit and inspect the structured nodes, sources, adjacency, and edges before
`propose`, and must explicitly approve the proposed file before `confirm` records
the reviewer and date. Command execution is not a substitute for human review.

For onboarding a new case from building documents, use `h3c offline discover`
rather than treating `h3c graph prepare` as discovery. The optional offline
workflow performs Mapping review first, then causal review, and only then calls
the same graph confirmation owner. Installation, specification, interruption,
resume, verification, and no-overwrite export are documented in
`docs/offline_onboarding.md`.
