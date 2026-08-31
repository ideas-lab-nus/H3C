# `revise3.txt` disposition matrix

This matrix records the final engineering disposition of the external review against the production protocol based on `8d3eeccd929873f0f2db95367dc282f1b2764519`. It does not claim model-behavior validation.

| Review item | Decision | Final treatment |
|---|---|---|
| Reflector Lessons cite solar, comfort headroom or comfort limits absent from its input | Accepted | The completed canonical record now projects outdoor temperature, solar irradiance, electricity price, warm/cool PMV headroom at all four action times, plus `abs_pmv_score_limit`. Documentation Lesson pointers must resolve against those records. |
| Add `evidence_fields` to Reflector output | Rejected | The established `hourly_lessons` wire stays unchanged. Evidence pointers live only in the deterministic audit/documentation view. |
| Static `[0,5]` Orchestrator limit can drift from configuration | Accepted | One `per_zone_reserved_cap_c` owner drives both Agent rendering and `validate_allocation`; a non-5 synthetic test is required. |
| Require one fixed site causal edge ID | Partially accepted | A fixed ID would over-specialize the protocol. The shared rule instead requires a unique, nonempty visible-ID subset containing at least one currently visible edge with `target=power_meters`. |
| Reserved allowance and shared pool are ambiguous | Accepted | Executor receives zone-owned reserved allowance, the shared pool available before settlement and ascending settlement rank. The prompt states that the pool is site-wide and settled after all proposals. |
| `common`, `constant_by_zone`, `common_when` and adjacent anonymous tables are unclear | Accepted in substance | Visible labels are self-describing; `common_when` is removed and every rule carries a full `when`; heterogeneous records are grouped into named operation blocks. No new global format header or custom DSL is introduced. |
| Remove `previous_rationale_per_zone` from Orchestrator input | Accepted | It remains in canonical/audit evidence but is not model-visible. Numerical ledger fields and previous priority remain. |
| Executor causal IDs, indices, rule IDs and value types are underspecified | Accepted | The parser/validator contract owner renders unique visible edit IDs, new/existing ID rules, zero-based index ranges and exact finite-number/parameter-reference value forms. `no_change` has no causal IDs. |
| Memory references need an exact contract | Accepted | `memory_refs` is a unique subset of shown `(regime, revision)` pairs actually used; memory-off has no memory-ref surface. |
| Rename `hourly_lessons` | Rejected | The wire name is retained for historical parsing and replay compatibility; its prompt meaning is explicitly one Lesson per zone for the completed 60-minute control interval. |
| Stale `ELIGIBLE LONG-TERM EXPERIENCE SLOTS` metadata | Accepted | Production and documentation use exact `ACTIVE LONG-TERM EXPERIENCE SLOTS` and `EMPTY LONG-TERM EXPERIENCE SLOTS`; stale labels are regression-tested. |
| Test three occupancy regimes and six patch operations | Accepted | Offline matrices cover `unoccupied`, `occupancy_transition`, `steady_state_occupancy`, all six operations, invalid IDs/indices/value types, revision conflict, rejected patch and shield evidence. |
| Explicitly set temperature/top-p | Rejected for this identity | The frozen low-thinking request explicitly sends enabled thinking and `reasoning_effort=low`; temperature and top-p remain absent and are verified as absent. |
| Mark this as behavior-final from fixture evidence | Rejected | The result remains `BEHAVIOR-UNVERIFIED`; no API or BOPTEST run is part of this change. |

Final offline classification:

`DATA-LOSSLESS / CONTRACT-ALIGNED / TIME-EXPLICIT / SEMANTICALLY-EXPLICIT / EVIDENCE-CLOSED / BEHAVIOR-UNVERIFIED`
