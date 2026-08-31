# H3C Agent Context Compaction and Clock-Semantics Report

## Outcome

The production context compiler now renders model inputs from one typed canonical object using clock time, semantic field owners and compact scalar properties/tables. No DeepSeek or BOPTEST call was made. Character counts below are exact `system + user` lengths from the frozen MZ Air documentation fixture; they are not token, latency or behavior claims.

Prompt-bundle identity: `sha256:a8a2a097be305b3611355d2f62cbace64f70f432969ed49970a59ac36c312fc7`. This is SHA-256 over the sorted canonical map of role/language prompt hashes in `tests/fixtures/prompts/caol_prompt_golden.json`, excluding `schema_version`.

## Final evidence-closed view

| Representative request | Previous candidate `8d3eecc` | New observed evidence | Final excluding new evidence | Final total | Non-evidence delta |
|---|---:|---:|---:|---:|---:|
| Orchestrator | 5,441 | 986 | 5,199 | 6,185 | -242 |
| East Executor, memory on | 6,942 | 434 | 7,142 | 7,576 | +200 |
| Reflector, memory on | 5,555 | 982 | 5,560 | 6,542 | +5 |
| **Three-role total** | **17,938** | **2,402** | **17,901** | **20,303** | **-37** |

The 2,402-character increase is the newly registered four-action-time evidence needed to close Reflector Lesson support: outdoor temperature, solar irradiance, electricity price, warm/cool PMV headroom and the comfort-score limit. With that evidence removed for a like-for-like comparison, the three-role aggregate is 37 characters smaller than `8d3eecc`.

The Executor retains 200 additional non-evidence characters and Reflector retains five. These are deliberate contract clarification for dynamic allowance semantics, causal IDs, rule identifiers, zero-based indices, `then.value` types and memory references. The user explicitly accepted this small difference rather than compressing away semantic detail. Character count is therefore a regression guard, not an optimization objective.

## Working-memory block

| View | Pre-compaction raw | C0 compact | S₂ clocked compact | S₂ vs raw |
|---|---:|---:|---:|---:|
| Five-zone Orchestrator | 6,020 | 1,909 | 2,685 including 986 evidence / 1,699 excluding it | 71.8% less excluding new evidence |
| One-zone Executor | 2,088 | 1,543 | 1,835 including 434 evidence / 1,401 excluding it | 32.9% less excluding new evidence |

S₂ retains all required layers: completed interval, recent raw state history, action/outcome history, prior decision forecast, deterministic change/stability features and Lesson. Constant values are factored once while their applicable clock list remains explicit.

## Structural changes

- Model-visible internal coordinates (`decision_hour`, `step`, `sample_index`, `physical_step`, `step_ahead`, and second counters) are replaced by `HH:MM` clocks. They remain in canonical/audit evidence.
- Top-level scalar objects use `field: value`; homogeneous records use `common + rows`; heterogeneous patches remain grouped by operation.
- Orchestrator current zone state, control context, prior Budget use and site forecast have distinct owners.
- Executor current state appears once; its previous interval endpoint is represented by the current-state section rather than repeated in working memory.
- Reflector receives one completed interval, with site result, decision, raw states, actions, outcomes and derived features each represented once. Active and empty long-term slots are separate.
- The allocation constraints rendered to the model and those enforced by `validate_allocation()` share `ALLOCATION_CONTRACT_SPEC`, including the dynamic `per_zone_reserved_cap_c` owner and the visible `target=power_meters` causal requirement.
- `previous_rationale_per_zone` remains in canonical/audit evidence but is excluded from Orchestrator model input.
- `common_when` is gone; every rule carries a complete `when`. Heterogeneous decision records are grouped under named operation blocks.
- Reflector receives `OBSERVED CONTEXT HISTORY` from completed action times only. Audit-only evidence pointers verify that fixture Lessons resolve against this completed evidence, not long-term experience slots.

## Limits

Round-trip equality establishes data preservation, not model decision equivalence. This candidate remains:

`DATA-LOSSLESS / CONTRACT-ALIGNED / TIME-EXPLICIT / SEMANTICALLY-EXPLICIT / EVIDENCE-CLOSED / BEHAVIOR-UNVERIFIED`
