# H3C Agent Context Semantic and Clock Preregistration — 2026-08-31

## Question

Can the compact three-role H3C context at exact base
`464ef282b8efaf75eb719e746735d22c6cf7a002` replace model-visible integer hour/step/sample
coordinates with explicit `HH:MM` control semantics, remove remaining duplicate fact owners, and clarify
Budget, comfort-headroom, pre-cooling, allocation, and long-term-experience fields without losing canonical
data or changing control behaviour?

## Frozen boundary

This stage changes only the typed context compiler, Agent-facing rendering, shared prompt/validator
contract metadata, deterministic documentation fixtures, offline gates, and generated English/Chinese
complete-hour documentation.

The following remain unchanged:

- Orchestrator, Executor, and Reflector output JSON fields and parsers;
- control program, patch operations, interpreter, action mapping, causal admission, Budget computation,
  Safety, and deterministic settlement;
- working-memory and three-regime long-term-experience information content;
- C0 prompt policy and `occupancy_routed` low-thinking request policy.

No model API call, BOPTEST call, physical run, MZ Air arm, push, paper/LaTeX/Figure 3 edit, or
case-specific control rule is authorised in this stage.

## Independent representation changes

1. Agent views show only clock time (`HH:MM`), intervals, action times, and corresponding outcome
   times. Internal hour, step, sample, absolute seconds, date, and year remain audit-only.
2. The current decision state is the sole owner of current zone temperature, PMV, occupancy,
   setpoint, and temperature distance to each PMV edge. The previous completed interval excludes its
   terminal state when that state is the current decision state.
3. Working memory is organised as completed-interval semantics, recent raw states, executed actions,
   action outcomes, deterministic derived features, previous decision forecast, and Lesson.
4. Comfort distances, pre-cooling program offset/result, previous reserved/shared Budget use, and
   current Executor allowance are renamed by physical meaning. No numerical owner changes.
5. The Budget charge description is aligned with production `program_delta`: across the proof state
   space, the maximum positive cooling-intensive displacement from the before-program setpoint to the
   after-program setpoint. It is not accumulated action, power, or pre-cooling residual.
6. Reflector completed evidence uses one explicit control interval; heterogeneous patches are grouped
   by operation; eligible experience slots are split into active and empty views when and only when
   long-term experience is enabled.

## Candidates

- `C0`: exact compact-context base `464ef28`.
- `S₁`: C0 plus clock time and semantic field/contract repair.
- `S₂`: S₁ plus cross-block single-owner projection. S₂ is the recommended offline candidate only if
  every gate below passes.

No candidate is tested with a model or physical plant in this stage.

## Acceptance gates

- Every compact section decodes exactly to its normalized canonical typed input.
- Agent-facing system and user messages contain no model-visible integer hour/step/sample coordinates,
  calendar dates, or years; audit views retain the internal identities.
- Every action time maps to the outcome exactly 15 minutes later; crossing midnight is rendered with
  `next day` and no date.
- A disagreement between the previous interval's terminal state and the current decision state fails
  closed before rendering.
- Raw four-step forecast and deterministic forecast summary both remain present.
- Comfort-distance, pre-cooling offset/result, and Budget arithmetic pass numerical owner tests.
- Previous allocation/utilisation examples are produced by the production `BudgetLedger`, not copied
  arithmetic.
- Prompt constraints and deterministic validators use one shared structured contract owner.
- Historical frozen outputs parse and replay without rewriting.
- Each S₂ role's total Agent-visible input is no longer than C0 at `464ef28`.
- English and Chinese complete-hour documents, time/field-owner report, external-review disposition
  matrix, and C0/S₁/S₂ comparison are generated and fresh.
- Targeted and full pytest, Ruff, format check, strict mypy, documentation freshness, and staged-file
  secret scan pass.

## Interpretation

Passing this stage establishes only:

`DATA-LOSSLESS / CONTRACT-ALIGNED / TIME-EXPLICIT / SEMANTICALLY-EXPLICIT / BEHAVIOR-UNVERIFIED`

It does not establish token, latency, decision, KPI, or closed-loop equivalence. Those require a
separately authorised behavioural evaluation after human review of the complete Agent inputs.
