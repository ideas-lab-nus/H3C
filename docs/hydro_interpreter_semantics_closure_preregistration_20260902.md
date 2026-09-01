# Hydro interpreter-semantics closure preregistration

Date: 2026-09-02

## Research question

Can the generic H3C method avoid the observed Hydro action-semantics error when the
Executor is shown the exact semantics of the already-existing executable program,
without changing P0, the interpreter, the action vocabulary, admission constraints,
Safety, reward, or any case-specific setting?

## Frozen baseline and attributable defect

The baseline is source `0901c098047422be9dc0d04c6e6148ced0504403`.
Its preserved recovery trajectory was stopped after 104 atomic hours when an accepted
SZ rule changed the unoccupied branch from `set_residual(0)` to `hold_setpoint`.  The
interpreter correctly retained the previous physical setpoint near 26.9 C instead of
returning to the 30 C unoccupied base, but subsequent Agent text treated the branch as
if it required no cooling energy.  The current Agent input names
`set_residual`, `step_setpoint`, and `hold_setpoint`, but does not state their exact
interpreter formulas or the ordered first-match rule.

## Candidate comparison

- `baseline`: unchanged source `0901c09`, represented by the preserved historical outputs.
- `semantics-only`: the baseline plus the exact ordered-first-match and three action
  formulas projected from the interpreter owner.
- `semantics-plus-derived-facts`: the semantics-only candidate plus deterministic
  current/history facts: regime base setpoint, applied
  setpoint offset from that base, cooling effect relative to that base, and current
  rule capacity. This is the implementation candidate.

Only the semantics-plus-derived-facts candidate may advance to a model call or physical
run. Character count is descriptive,
not an acceptance threshold; no useful semantic content will be removed to offset the
new facts.

## Exact method change

The interpreter becomes the single owner of:

- occupied and unoccupied base setpoints;
- residual and actuator bounds;
- maximum rule count;
- ordered first-match execution;
- the exact `set_residual`, `step_setpoint`, and `hold_setpoint` formulas.

The Executor control-specification view receives a concise projection of that owner and
the current `used / maximum / remaining` rule capacity.  The current decision state and
the four completed action rows receive deterministic base/offset/effect facts computed
from already-visible occupancy and physical setpoints.

These additions are observations and interpreter semantics.  They do not participate in
ProgramCheck, CausalProof, Budget, Safety, settlement, or physical action calculation.

## Frozen boundaries

This work does not change:

- the canonical P0 JSON or its six rules and five parameters;
- the six specification patch operations;
- the three rule action types;
- the rule-count maximum of eight;
- the deterministic interpreter result for any program and observation;
- ProgramCheck, the registered causal-proof constraints, Budget, the registered action
  assurance order, the disabled graph shield, action mapping, reward,
  PMV thresholds, model settings, or acceptance thresholds;
- the provider-native strict JSON schema, C0 Prompt structure,
  `occupancy_routed` low thinking, or long-term-memory-off identity;
- any case-specific Prompt, parameter, rule, or branch.

## Offline evaluation

The same frozen cases are used for baseline evidence and implementation-candidate tests.
Development cases cover:

1. unoccupied `set_residual(0)` returning to the 30 C base;
2. unoccupied `hold_setpoint` retaining the last physical setpoint;
3. occupied `step_setpoint(+v)` using the last physical setpoint;
4. occupancy onset `step_setpoint(+v)` using the occupied base rather than the last
   unoccupied setpoint;
5. overlapping rules proving ordered first-match behavior;
6. an eight-rule program showing zero remaining add slots.

Holdout cases cover negative step values, actuator/residual clipping, and a program below
the rule maximum.

Required gates:

- the interpreter outputs and canonical P0 hash are unchanged from C0;
- rendered action semantics are generated from the same constants/functions used by the
  interpreter;
- compact working memory remains exactly reversible to its canonical records;
- every historical output schema still parses without rewriting;
- derived action facts equal replayed physical setpoints for all four steps;
- no new runtime rejection path or validator condition exists;
- targeted tests, full pytest, Ruff, format check, strict mypy, generated-document
  freshness, staged manifest review, and staged secret scan pass;
- the canonical environment and target `uv.lock` match.

## Baseten non-physical validation

After a clean method commit, six frozen real Hydro Executor inputs will be sent to the
already-authorized Baseten DeepSeek endpoint without BOPTEST.  The exact input identities
and source hours/zones will be recorded before dispatch.  Calls use provider-native
strict JSON schema, thinking enabled with `reasoning_effort=low`, no temperature/top_p,
and no retry for ordinary model-contract or semantic failure.

All six must have healthy request/model/secret identity, `finish_reason=stop`, valid
existing Executor output schema, and no final rationale or proposed-program replay that
contradicts the displayed first-match/action semantics.  Outputs are not selected for a
preferred operation or apparent KPI benefit.  Any failure blocks the physical run.

## Hydro physical confirmation

Only after every offline and non-physical gate passes, launch one fresh MZ Hydro arm:

- Baseten `deepseek-ai/DeepSeek-V4-Flash-0731`;
- provider-native strict JSON schema;
- C0, `occupancy_routed` low thinking;
- one-hour working memory, long-term memory off;
- seven-day internal warm-up and 120 evaluation hours;
- fresh run directory, fresh BOPTEST test identity, one method attempt;
- registered transient errors may retry twice, for three identical requests total;
- an eligible infrastructure interruption may use the existing fresh-run/fresh-test
  physical-prefix replay contract; poor KPI or model degradation may not.

The run is monitored every 20 minutes using atomic completed-hour evidence.  Registered
pass remains:

```text
reward > -179.35418363224142
occupied peak absolute PMV <= 0.70
healthy physical/source/run/test/timeline/secret/evidence identity
```

No SZ Air or MZ Air run follows automatically.  No push or paper/LaTeX/Figure 3 change is
authorized.
