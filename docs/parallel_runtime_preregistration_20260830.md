# Dependency-aware parallel runtime preregistration

Date: 2026-08-30
Frozen parent: `7b8a4f820583a4d0ed3522b313b43913b463ce4d`

## Question

Can independent BOPTEST arms and same-hour zone Executor requests run concurrently without
changing H3C's causal order, deterministic program settlement, model request identity, physical
trajectory semantics, or evidence completeness?

## Registered change

- BOPTEST dispatch is `auto`: a fresh test is selected, `status/{testid}` is the resource owner,
  and initialization begins only after status is `Running`. `Queued` waits without model calls or
  physical initialization. No local integer worker limit is introduced.
- Model calls in independent processes may overlap. Within one H3C hour the Orchestrator finishes
  first, all zone Executors are issued concurrently, every issued Executor finishes or fails, then
  proposals settle in frozen allocation-priority/configured-zone order. Four physical steps finish
  before the Reflector is called.
- Every request receives an immutable explicit context and a stable zero-based `call_ordinal`.
  Evidence is joined by `logical_call_identity`; JSONL arrival order is not semantic order.
- HTTP 429 and 503 join the existing bounded identical-request retry contract. `Retry-After`, when
  valid, takes precedence over the registered local backoff. No other HTTP response is made
  retryable.
- A terminal Executor transport failure waits for every already-issued zone request, records all
  attempts, selects the primary failure in configured-zone order, and stops the hour before program
  settlement or physical advance.
- The runtime atomically publishes current dispatch state and the last fully completed hour for
  long-run monitoring. These files do not authorize resume.

## Invariants

The Prompt text, output schemas, controller program, causal admission, budget accounting, action
assurance, occupancy, comfort, weather, physical protocol, evaluation window, and expected O/E/R
logical-call counts do not change. Memory-v1 remains an optional Prompt surface with the same
semantics. Orchestrator and Reflector are not moved across their causal barriers.

## Acceptance gates

1. Delayed fake Executors demonstrate real overlap and inverted completion while retaining the
   correct zone/request identities and deterministic settlement.
2. Single and multiple terminal Executor transport failures leave zero updates and zero physical
   advances for the failed hour while preserving every issued attempt.
3. The verifier accepts interleaved call/attempt evidence after grouping by logical identity and
   rejects duplicate identity, duplicate ordinal, wrong-zone identity, missing attempts, or an
   incomplete Executor batch followed by settlement.
4. A queued fake BOPTEST test is never initialized until its status becomes `Running`.
5. A 120-hour fake run preserves O/E/R=`120/240/120` and 480 logical calls.
6. Targeted pytest, Ruff, formatting, strict mypy for changed owners, staged-file secret scan, and
   staged-manifest inspection pass before commit.

## Hard stops and prohibited actions

BOPTEST initialization/advance, test identity, secret, or evidence corruption remains a hard stop.
Retries remain bounded and identical-payload. This implementation does not call DeepSeek or
BOPTEST, run a physical experiment, modify historical evidence or the paper, push, resume, or
introduce a fixed concurrency cap.
