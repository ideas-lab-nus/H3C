# H3C Agent Context Compaction Report

## Outcome

The model-facing inputs are now compiled from typed context rather than assembled as nested JSON inside Markdown inside JSON strings. The new views retain explicit time semantics, current state, recent raw history, applied control history, deterministic derived features, and optional eligible long-term experiences.

No model or BOPTEST call was made. These figures are exact serialized-character counts from the frozen MZ Air complete-hour fixture, not token or latency claims.

Candidate prompt-bundle manifest identity: `sha256:4c0af97a4c26ea15a2107503a76d1c0d6a1edd6b6b461bd39f4c8bde94c63165`. Individual role/language prompt hashes remain frozen in `tests/fixtures/prompts/caol_prompt_golden.json`.

## Role-level results

| Role and representative request | Base | New | Reduction |
|---|---:|---:|---:|
| Orchestrator | 11,621 | 5,456 | 53.1% |
| East Executor, memory on | 10,715 | 6,953 | 35.1% |
| Reflector, memory on | 9,817 | 5,677 | 42.2% |

All fixed role-level targets passed.

## Working-memory results

| View | Base block | New block | Reduction | Interpretation |
|---|---:|---:|---:|---|
| Five-zone Orchestrator | 6,020 | 1,909 | 68.3% | Multi-zone duplicate removal passed the 60% target. |
| One-zone Executor | 2,088 | 1,543 | 26.1% | Smaller, but intentionally enriched with the newly required time/current/history/action/derived layers. |

The one-zone view is not shortened by deleting the user-required layers. Its absolute size remains lower than the old block while adding deterministic trend, change, variation, reversal, and discomfort features.

## What changed structurally

- Shared site results and cross-zone fields are emitted once.
- Five-zone histories are oriented around one explicit sample/step axis instead of repeating zone, step, phase, occupancy, setpoint, and assurance text for every Cartesian row.
- Values constant across the hour are emitted once globally or once per zone; only varying measurements remain in the time table.
- Current state is explicitly identified as the final post-action sample rather than duplicated as another full record.
- Completed proposal proof internals remain in audit evidence but are not repeated as next-hour decision context.
- Control parameters use one scalar table; rules retain compact JSON because their condition trees are non-homogeneous.
- Common operation fields and rule structure are defined once in the Executor output contract.
- Reflector memory operations use one common-field table instead of four repeated object definitions.

## Prompt cleanup

Model-visible prompts no longer contain project abbreviations such as `CAOL`/`CAO`, runtime implementation statements about missing blocks, offline/oracle warnings for inaccessible data, verifier implementation prose, or special encouragement of `no_change`. `no_change` appears only as one operation in the operation table.

Reflector still performs one completed-hour Lesson task and, only when the optional memory module is enabled, one eligible-slot CRUD decision. Multi-sentence Lessons are accepted within the existing 480-character transport bound.

## Limits of this evidence

Character reduction is not token reduction, latency reduction, or behavioral equivalence. The output contract and deterministic replay path are compatible, but model decisions under the new inputs have not been tested. A real API/BOPTEST study requires a separate user-approved preregistration after review of the generated English and Chinese complete-hour examples.
