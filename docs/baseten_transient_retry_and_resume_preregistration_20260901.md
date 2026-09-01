# Baseten transient retry and atomic-prefix resume preregistration

## User ruling and scope

On 2026-09-01 the user required future processes to retry transient HTTP
500/502/503/504 service errors at most twice (three requests total per logical
call), and to prefer an evidence-qualified resume/replay after later
interruptions instead of restarting from the beginning. This change is not
loaded into the already-running MZ Air, SZ Air, or MZ Hydro processes and does
not alter their checkout, PID, lock, run, test, or evidence.

## Frozen method boundary

- Prompt, model, thinking, sampling, output schema, control program, causal
  admission, Budget, Safety, reward, KPI, and acceptance criteria do not change.
- Baseten provider-native structured output, session affinity, and model name
  do not change.
- A failed source run is immutable. Resume never appends to its directory,
  overwrites its failure marker, or reuses its BOPTEST test identity.
- Model-contract degradation, deterministic rejection, controller fallback, or
  poor KPI never triggers resume or a method rerun.

## Bounded Baseten retry contract

- Baseten retryable HTTP statuses are exactly 429, 500, 502, 503, 504, and 529.
- retry_count remains two, hence each logical call has at most three HTTP
  attempts.
- A valid Retry-After takes precedence; otherwise the existing one- and
  two-second backoffs apply.
- Every attempt is recorded in model_request_attempts.jsonl under one stable
  logical-call identity.
- Authentication, request/schema errors, other ordinary 4xx responses, invalid
  response contracts, and model-content errors are not retried.
- The Official DeepSeek status set and BOPTEST retry policy remain unchanged.

This status policy follows Baseten's HTTP-client guidance, which identifies
429/500/502/503/504 plus connection and read-timeout failures as transient and
explicitly excludes request/authentication errors such as 400/401/403/404/422:
<https://docs.baseten.co/inference/http-client-configuration>. Baseten also
recommends a reused connection pool. The current client creates independent
standard-library requests, so pooling is a valid later transport optimization,
but it is not bundled into this minimal retry/resume change: adopting it would
change the core HTTP client and dependency owner while formal processes are
live. Existing 600-second request timeout also remains unchanged in this patch.

## Resume eligibility

The command `h3c resume <failed-run> --execute` is eligible only when all of the
following hold:

1. the source has an atomic failure marker, no completion marker, and an atomic
   completed-hour checkpoint;
2. the failure is terminal transport or another explicitly registered
   control-neutral infrastructure failure;
3. source physical/timeline/test/secret/program/action/KPI evidence passes the
   prefix verifier;
4. only evidence through the last atomic completed-hour checkpoint enters the
   imported prefix; any partial next-hour calls or at most four physical steps
   remain preserved solely in the failed source and are replayed in the fresh
   run rather than trusted or spliced;
5. profile, method, Prompt/model/provider identity match; only registered
   retry/resume mechanical source changes may differ;
6. long-term memory is off until its CRUD state has a dedicated replay owner;
7. the old test, PID, and lock have been released.

## Resume semantics

- Create a fresh run directory, fresh BOPTEST test, and independent lock.
- Initialize the same physical window, then replay final controls for steps zero
  through completed_step without recalling Agents for completed hours.
- Recompute and compare observation, program interpretation, action assurance,
  physical outcome, and KPI at every replayed step; any mismatch fails closed.
- Replay accepted program updates from P0 and restore completed working memory,
  previous allocation/Budget utilisation, rejection feedback, fallback count,
  and cumulative metrics.
- Only after the physical prefix and Agent state match may new Agent calls begin
  at next_step.
- The recovery run records source identity, checkpoint, imported stream hashes,
  and replay result. The source remains a failed run; the new run has explicit
  recovery lineage.

## Acceptance

- Unit tests cover each of 500/502/503/504 with success after retry and
  exhaustion at three total attempts, plus a non-retried 400/401.
- Fake BOPTEST proves no completed Agent call is repeated, physical replay
  advance count equals checkpoint next_step, and remaining hours complete.
- Tampered checkpoint/action/program/working-memory/forecast/test/outcome
  evidence fails closed.
- The preserved 13-hour SZ Air HTTP500 run is audited offline without network
  access or source mutation.
- Targeted and full pytest, Ruff, format, strict mypy, and staged secret scan
  pass.

This preregistration does not authorize changing or restarting the three live
formal arms, a new physical/API experiment, push, or paper modification.
