# Hydro interpreter-semantics prompt evaluation

Date: 2026-09-02

## Contract and baseline failure cluster

The Executor's task, output JSON, six specification patch operations, three rule action
types, five editable parameters, P0 program, interpreter, admission chain, Budget,
Safety and reward are unchanged. The baseline is source
`0901c098047422be9dc0d04c6e6148ced0504403`.

Two preserved Hydro mechanisms define the failure cluster:

1. a comparator edit was described with the opposite match-frequency effect; and
2. an unoccupied rule was changed from `set_residual(0)` to `hold_setpoint`, after
   which the physical setpoint remained near 26.9 C although Agent text treated the
   branch as if it returned to the 30 C unoccupied base.

Both defects are interpretation errors about the existing DSL. They are not missing
actions and are not evidence for a new runtime veto.

## Candidate beam

| Candidate | Change | Offline disposition |
|---|---|---|
| Baseline | Historical input and output | Retained as adverse evidence |
| Semantics-only | Ordered first match and the three exact action formulas | Necessary but does not expose the current consequence |
| Semantics plus derived facts | Semantics-only plus current interpreter derivation, rule capacity, and completed-action base/offset/effect facts | Selected for validation |

The selected candidate adds one concise Executor decision instruction. It does not add
an admission rule. All deterministic facts are produced by the same functions and
constants used by the executable interpreter.

## Offline tests

The following cases passed:

- unoccupied `set_residual(0)` returns to the 30 C base;
- unoccupied `hold_setpoint` retains the previous physical setpoint, subject to the
  existing residual and actuator clipping;
- occupied `step_setpoint(+v)` uses the previous physical setpoint;
- occupancy-onset `step_setpoint(+v)` uses the occupied base;
- negative steps and clipping preserve their existing behavior;
- overlapping rules execute only the first match;
- an eight-rule program reports zero remaining add slots without disabling replace,
  remove or move;
- current derivation equals `run_program()` output;
- four-step completed-action facts equal physical setpoints and survive compact-view
  encode/decode;
- a complete legacy working-memory record can omit the new field group, while a partial
  new group fails closed;
- frozen P0, graphs, validation chain, causal modules, action assurance and reward owner
  are byte-for-byte unchanged from the baseline commit.

Quality gates:

| Gate | Result |
|---|---:|
| Targeted interpreter/context/Prompt/document tests | 81 passed |
| Full pytest | 525 passed |
| Ruff | passed |
| Ruff format check | 231 files formatted |
| Strict mypy | 81 source files passed |
| Generated document freshness | passed |

## Context accounting

Character count is descriptive, not a selection threshold.

| Representative request | Before | Selected candidate | Change |
|---|---:|---:|---:|
| Orchestrator | 6,469 | 6,499 | +30 |
| Executor | 8,012 | 9,277 | +1,265 |
| Reflector | 8,406 | 9,069 | +663 |

The Executor system Prompt grows by 69 English characters and 19 Chinese characters.
The remaining growth is structured dynamic evidence. No useful content was deleted to
compensate for this increase.

Prompt bundle:
`sha256:b1a3416c71861a63252723ca0f0c4f9bd7c059a4cbdcbaf801e5bcbc08e0dc3f`.

## Frozen Baseten inputs

Before any external call, the production renderer rebuilt and froze six Hydro inputs
from preserved physical/program evidence. Each new input includes the selected
interpreter semantics and derived facts.

| Source evidence | Hour | Zone | Source logical call | New user SHA-256 |
|---|---:|---|---|---|
| Reward-feedback adverse run | 55 | NZ | `ff77c4cd3a2101a0c6ec1089b6bfb19d2605b73c3c2b4da71489dd68b10b1cff` | `44486a8b7e0e33825ca44528e36570d4086e172853ef98ad69ebad7f15b8bb0a` |
| Effect-semantics recovery | 41 | SZ | `2a5422f37bb0bd5814caf16f3b9c889892ec07c958d82d159556aabaabd1a6a4` | `3373505696f2cb0da68075a7de37bd9ba2db639bf6b71d0bce7db3815132a151` |
| Effect-semantics recovery | 55 | NZ | `7aec515692434ac8cb7d1bac6c5ce987cf37178f3cef60b87d7e7535ec6e5105` | `c0c3c9e5e50a20edf98e734c785f639308b01a212933c735e0cd94f659b8d5fc` |
| Effect-semantics recovery | 57 | SZ | `394e308b8fc28978d37f87320660b9ea27152de19cde01f03d47547c0f640eb6` | `60e723f1d8788cf5291fe3202f7840b3b4400d0416e3553cbfc229c0dd4fdb73` |
| Effect-semantics recovery | 67 | SZ | `b065b9acd180c8ac9fb367e59095ce16b9126e5fc834826b17030968225cdb7d` | `5e2bd21104b3df12e6dfdd58c1719e3d27dd071a80892a65d47d276818760c65` |
| Effect-semantics recovery | 92 | SZ | `367cea334fa1b68e94ddfe29a70d8b0b6e8f9f6c27bfbc6f579610b5fc502f2a` | `1ef7ab104db93f591542e7480f998e3b51f88e97c1349ac96a5cae963ac9dc05` |

## First Provider result and semantic disposition

All six calls completed without retry with `finish_reason=stop`, exact Baseten model
identity, strict JSON output, a valid output envelope, complete usage and no secret
exposure. This establishes structural compatibility only.

Semantic review failed on two mandatory cases:

1. hour 55 NZ described the occupancy-onset `anchor` as using the 30 C unoccupied
   base. The rule requires `occupied_now=1` and `occupied_last=0`; the actual base is
   25 C, so `set_residual(0)` is 25 C and `set_residual(-3.5)` is 21.5 C, not 26.5 C;
2. hour 67 SZ described unoccupied `set_residual(0)` as 25 C and replacement
   `hold_setpoint` at 26.85 C as energy saving. The actual unoccupied base is 30 C;
   the current action returns to 30 C, while hold retains 3.15 C of additional cooling.

The other four responses do not repair these contradictions. Several structurally
valid model patches were independently rejected by the unchanged registered runtime
validator; those ordinary rejections are not the reason for failing the semantic gate.

Disposition:

```text
STRUCTURAL-PASS / SEMANTIC-FAIL / HYDRO-NOT-ELIGIBLE
```

The next candidate is preregistered in
`docs/hydro_rule_effect_projection_preregistration_20260902.md`. It adds per-rule
matching-state projections from the interpreter owner, not a control constraint.
