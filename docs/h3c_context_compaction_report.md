# H3C Agent Context Compaction and Clock-Semantics Report

## Outcome

The production context compiler now renders model inputs from one typed canonical object using clock time, semantic field owners and compact scalar properties/tables. This report's compilation and character-accounting stage made no DeepSeek or BOPTEST call. A later, separately preregistered Baseten wire-contract regression is reported in `executor_output_envelope_recovery_result_20260901.md`. Character counts below are exact `system + user` lengths from the frozen MZ Air documentation fixture; they are not token, latency or behavior claims.

Prompt-bundle identity: `sha256:d496d0ca7f2cb809626a4f8413391dabbff8bfc0f1a1735856cf2c72b08b9305`. This is SHA-256 over the sorted canonical map of role/language prompt hashes in `tests/fixtures/prompts/caol_prompt_golden.json`, excluding `schema_version`.

## Final evidence-closed view

| Representative request | Previous candidate `8d3eecc` | Observed-context evidence | Registered reward feedback and objective guidance | Final excluding both new channels | Final total |
|---|---:|---:|---:|---:|---:|
| Orchestrator | 5,441 | 986 | 284 | 5,199 | 6,469 |
| East Executor, memory on | 6,942 | 434 | 284 | 7,204 | 7,922 |
| Reflector, memory on | 5,555 | 982 | 1,611 | 5,560 | 8,153 |
| **Three-role total** | **17,938** | **2,402** | **2,179** | **17,963** | **22,544** |

The 2,402-character observed-context channel closes Reflector Lesson support. The separately registered reward channel adds the unchanged objective sentence to each role and exposes the completed interval's exact four-step reward breakdown to the Reflector fixture. With both new information channels removed for a like-for-like comparison, the three-role aggregate remains only 25 characters larger than `8d3eecc`.

The Executor retains 262 additional non-evidence characters and Reflector retains five. These are deliberate contract clarification for dynamic allowance semantics, causal IDs, rule identifiers, zero-based indices, `then.value` types, memory references, and the exact historical `{"patch":[{...}]}` wire envelope. The user explicitly accepted this small difference rather than compressing away semantic detail. Character count is therefore a regression guard, not an optimization objective.

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
