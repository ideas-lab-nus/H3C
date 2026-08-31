# H3C Context Compaction Preregistration — 2026-08-31

## Question

Can the three H3C Agent request contexts be compiled from one canonical typed context into a shorter, explicit `common + rows` representation without losing data, changing the model-output contracts, or changing any control mechanism?

## Exact base and scope

- Base implementation: `16dfa81a5153f31238e6e6fda2a64da5736a0869`.
- Scope: production prompt text, production context rendering, Reflector lesson transport, eligible long-term-experience slot projection, offline verification, and generated English/Chinese complete-hour documentation.
- No model API call, BOPTEST call, physical run, paper edit, LaTeX edit, Figure 3 edit, or push is authorised in this stage.

## Frozen invariants

- Control program, patch wire JSON, parser, action semantics, causal admission, Budget, Safety, interpreter, and settlement are unchanged.
- `occupancy_routed` low-thinking is unchanged.
- Orchestrator, Executor, and Reflector decision ownership is unchanged.
- Working-memory and three-regime long-term-experience canonical data are unchanged.
- No custom reference, run-length, range, or token-deletion DSL is introduced.

## Independent variables

1. Remove model-irrelevant or duplicated prompt prose and model-visible project abbreviations.
2. Compile homogeneous records into explicit `common`, scalar `rows`, and separate nested `details`; compile aligned four-step arrays into scalar step rows.
3. Let a Reflector Lesson contain more than one sentence while retaining the existing 480-character transport bound.
4. When long-term experience is enabled, expose to Reflector only regime slots observed in the completed hour, ordered by first observed step.
5. Organize working memory into explicit time semantics, current state, recent raw state history, control-action history, and deterministic derived features. Derived features are limited to transformations of completed evidence already present in the record; they do not add targets, action recommendations, future signals, or hidden control rules.

## Baseline and fixed targets

The frozen MZ Air complete-hour fixture gives these pre-change `system + user` character baselines:

| Role | Baseline | Required reduction |
|---|---:|---:|
| Orchestrator | 11,621 | at least 40% |
| Executor | about 10,700 | at least 35% |
| Reflector | 9,817 | at least 40% |

The five-zone working-memory block must decrease by at least 60%. The later user requirement to add explicit current-state semantics, raw history, action history, and deterministic derived features makes the one-zone Executor block a richer view rather than a pure duplicate-removal target; its reduction is reported separately and must not be increased by deleting one of those required layers. Compression is reported only after the lossless and contract gates pass.

## Acceptance gates

- Decoding every compact view equals its normalized canonical input exactly.
- Every pre-change Agent-input field has an explicit migration entry; there are no unexplained deletions.
- Zero, false, missing values, empty lists, Unicode, and delimiter-containing text round-trip correctly.
- `common` extraction is structural and depth-preserving; coincidental equality across different semantic paths is never merged.
- Zone order and step order are stable; conflicting repeated owners fail closed.
- Working-memory time semantics identify the 15-minute physical step, 60-minute Agent decision interval, the hour-start state, and post-action outcomes. Current state is the last completed outcome. Trend, change, variation, reversal, and discomfort features are deterministically replayable from the raw state/action rows.
- Model-visible prompts contain neither `CAOL` nor `CAO` and omit the eleven user-identified redundant instruction classes.
- Table cells contain scalar values only, never serialized JSON arrays or objects.
- All six patch operations pass the existing causal-on/off parser and validator unchanged.
- Reflector gates cover single-regime, multi-regime, memory-off, multi-sentence Lesson, and invalid CRUD cases.
- Historical frozen model outputs still pass the existing parser and program replay.
- Tests, prompt goldens, Ruff, strict mypy, documentation freshness, and secret scan pass.

## Failure and interpretation

Any field loss, owner conflict, ordering drift, parser/validator change, memory-off leakage, or missed target blocks adoption. Passing this stage establishes only:

`DATA-LOSSLESS / CONTRACT-COMPATIBLE / BEHAVIOR-UNVERIFIED`

It does not establish token, latency, or closed-loop control equivalence. Those require a separately approved real-model and BOPTEST preregistration after human review of the generated complete-hour inputs.
