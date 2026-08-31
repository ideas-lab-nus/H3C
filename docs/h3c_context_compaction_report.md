# H3C Agent Context Compaction and Clock-Semantics Report

## Outcome

The production context compiler now renders model inputs from one typed canonical object using clock time, semantic field owners and compact scalar properties/tables. No DeepSeek or BOPTEST call was made. Character counts below are exact `system + user` lengths from the frozen MZ Air documentation fixture; they are not token, latency or behavior claims.

Prompt-bundle identity: `sha256:ae66d6cf0e4f27ea1e5b9f5561f3c944d46d9f6e6ad65357cce4d8e4134ce875`. This is SHA-256 over the sorted canonical map of role/language prompt hashes in `tests/fixtures/prompts/caol_prompt_golden.json`, excluding `schema_version`.

## C0, S₁ and S₂

| Representative request | C0 `464ef28` | S₁ clock/semantics with legacy duplicate-owner overlay | S₂ production candidate |
|---|---:|---:|---:|
| Orchestrator | 5,456 | 5,926 | 5,441 |
| East Executor, memory on | 6,953 | 7,329 | 6,942 |
| Reflector, memory on | 5,677 | 6,446 | 5,555 |
| **Three-role total** | **18,086** | **19,701** | **17,938** |

S₂ is 148 characters (0.8%) below C0 in the required three-role aggregate. Each representative role is also individually no longer than C0, while S₂ adds explicit action/outcome clocks, unambiguous comfort headroom and precooling fields, exact Budget semantics and the repaired output contract.

S₁ is an offline diagnostic projection, not a retained production renderer. It is exactly S₂ plus the corresponding C0 duplicate-owner blocks extracted from the immutable `464ef28` fixture: Orchestrator `CROSS-ZONE STATUS` (485 characters), Executor `ZONE OBSERVATION` (387), and Reflector the unsplit eligible-slot block (891). This isolates the value of S₂'s cross-block owner removal without claiming that S₁ was executed.

## Working-memory block

| View | Pre-compaction raw | C0 compact | S₂ clocked compact | S₂ vs raw |
|---|---:|---:|---:|---:|
| Five-zone Orchestrator | 6,020 | 1,909 | 1,817 | 69.8% less |
| One-zone Executor | 2,088 | 1,543 | 1,470 | 29.6% less |

S₂ retains all required layers: completed interval, recent raw state history, action/outcome history, prior decision forecast, deterministic change/stability features and Lesson. Constant values are factored once while their applicable clock list remains explicit.

## Structural changes

- Model-visible internal coordinates (`decision_hour`, `step`, `sample_index`, `physical_step`, `step_ahead`, and second counters) are replaced by `HH:MM` clocks. They remain in canonical/audit evidence.
- Top-level scalar objects use `field: value`; homogeneous records use `common + rows`; heterogeneous patches remain grouped by operation.
- Orchestrator current zone state, control context, prior Budget use and site forecast have distinct owners.
- Executor current state appears once; its previous interval endpoint is represented by the current-state section rather than repeated in working memory.
- Reflector receives one completed interval, with site result, decision, raw states, actions, outcomes and derived features each represented once. Active and empty long-term slots are separate.
- The allocation constraints rendered to the model and those enforced by `validate_allocation()` share `ALLOCATION_CONTRACT_SPEC`.

## Limits

Round-trip equality establishes data preservation, not model decision equivalence. This candidate remains:

`DATA-LOSSLESS / CONTRACT-ALIGNED / TIME-EXPLICIT / SEMANTICALLY-EXPLICIT / BEHAVIOR-UNVERIFIED`
