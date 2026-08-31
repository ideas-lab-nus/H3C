# MZ Air CAOL and three-regime experience preregistration

## Research question and frozen source boundary

This experiment asks whether replacing the former Agent-visible frame history with one completed
Context–Action–Outcome–Lesson record per zone-hour improves MZ Air control stability, and whether a
separate three-regime long-term experience module adds value beyond CAOL alone.

Implementation starts from private `main@7ce6fd5` plus the already reviewed dependency-aware
parallel runtime and BOPTEST status compatibility commits. The experiment source is frozen by the
commit made after all offline gates below pass. No result may be used to alter that commit.

The only method changes are:

1. CAOL becomes the sole Agent-visible working memory. Runtime deterministically constructs
   Context, Action, and Outcome from the four completed steps; Reflector generates only Lesson.
2. An optional module maintains exactly one zone-specific experience slot for each of
   `unoccupied`, `occupancy_transition`, and `steady_state_occupancy`. Reflector may perform at
   most one CAS-protected operation per zone per hour. Executor references are audit-only.
3. Verifier distinguishes execution/identity/evidence failures from recoverable model-contract or
   CRUD degradation. Memory-off leakage remains a method-identity failure.

The experiment does not change `pmv_step_c`, operation semantics, Executor operation guidance,
program direction proof, causal admission, Budget, Safety, P0, action mapping, C0 Prompt structure,
or the `occupancy_routed` low-thinking policy. It adds no delayed cooldown, pre-occupancy PMV rule,
or other anti-oscillation control law.

## Offline gates

Before any external call or physical trajectory, the frozen source must pass:

- Prompt golden checks for English/Chinese and memory-on/off surfaces;
- CAOL-only Agent-visible working-memory checks;
- exact three-regime classification and fixed-slot CRUD replay;
- memory-off zero leakage;
- historical/fake physical replay, including parallel Executor ordering;
- complete pytest, Ruff, strict mypy, generated-document freshness, staged-manifest review, and
  staged-file secret scan.

The bilingual complete-hour documents are generated from the same frozen MZ Air fixture through
production renderers and deterministic owners. They make no API or BOPTEST call and are not
performance evidence.

## Two fresh parallel arms

Both arms use MZ Air day 199, one seven-day BOPTEST internal warm-up, zero explicit prefix, seven
formal days, the official `[06:00,19:00) AND raw>0` occupancy owner, `k=1`, C0,
`occupancy_routed` low thinking, the same program, graph, coordination, Budget, Safety, reward and
action mapping, and independent checkout/output/lock/test identities.

1. `CAOL-only`: long-term experience disabled. No memory/CRUD/reference surface is allowed.
2. `CAOL+regime-memory`: the exact optional three-slot module enabled.

The arms are submitted concurrently. Within each hour the dependency order remains Orchestrator,
parallel zone Executors, deterministic settlement, four physical steps, Reflector. There is no
retry, resume or lucky rerun. Initialization/advance, identity, secret or evidence failure stops
only the affected arm and preserves its evidence. Schema, finish-length, reference or CRUD errors
are method degradation and do not stop an otherwise healthy physical arm.

## Frozen decision thresholds

Each arm is evaluated against frozen eRBC reward `-559.1299559533957` and must satisfy all of:

- reward greater than `-559.1299559533957`;
- occupied peak absolute PMV no greater than `0.70`;
- setpoint direction reversals fewer than `323`;
- setpoint total variation below `477.9 °C`.

Three-regime experience becomes the recommended default only if it also beats CAOL-only reward,
its slot operations match runtime regime evidence, and at least one full replayable chain exists:

`CAOL Lesson → regime-slot CRUD → active experience → Executor reference → proposal → admission → action → outcome`.

Otherwise CAOL remains the production working-memory design and the three-regime module remains
default-off and explicitly ablatable. All adverse outcomes remain evidence. The experiment stops
at a local review point without push or paper/LaTeX/Figure 3 edits.
