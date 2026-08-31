# H3C Agent Context Field Migration

This manifest maps every production input owner affected by the 2026-08-31 context compiler. The normalized canonical typed object remains the fact owner. Compact model rendering does not mutate runtime objects.

## Labels and role sections

| Previous model-visible label | New model-visible label | Change |
|---|---|---|
| `CAOL WORKING MEMORY` | `WORKING MEMORY` | Display name only; internal compatibility names are unchanged. |
| `CURRENT HOUR DETERMINISTIC CAO` | `COMPLETED HOUR EVIDENCE` | Display name only. |
| Repeated JSON/Markdown/escaped-JSON blocks | Typed `common`, scalar `rows`, and separate nested `details` | Values and order are retained. |
| Executor program plus separate edit limits | `CONTROL SPECIFICATION` | One view; parser, patch wire contract, and validator remain unchanged. |

## Working-memory mapping

| Canonical path | Model-facing owner |
|---|---|
| `hour` | Hour header and explicit time semantics. |
| `zone` | Ordered zone scope and zone columns/rows. |
| `context.initial_observation.zone_temperature_c` | Recent-state sample 0 temperature. |
| `context.initial_observation.current_occupancy` | Recent-state sample 0 occupancy. |
| `context.initial_observation.last_pmv` | Recent-state sample 0 PMV. |
| `context.initial_observation.last_setpoint_c` | Recent-state sample 0 setpoint. |
| `context.initial_observation.occupancy_next_steps` | Decision-time occupancy forecast with explicit `step_ahead`. |
| Other `context.initial_observation` fields | Completed-hour decision context. |
| `context.regime_step_coverage` | Control-action regime by physical step. |
| `action.proposal` | Completed-hour decision, excluding proof-only duplicates in the next model view. |
| `action.admission.status` | Completed-hour gate result. |
| `action.program_version_before/after` | Completed-hour program transition. |
| `action.actual_setpoints_c` | Control-action history by physical step. |
| `action.matched_rules` | Control-action history by physical step. |
| `action.shield` | Per-step assurance result; shared values are emitted once. |
| `outcome.zone_temperatures_c` | Recent-state samples 1–4. |
| `outcome.pmv` | Recent-state samples 1–4. |
| `outcome.effective_occupancy` | Recent-state samples 1–4. |
| `outcome.site_cost` and `outcome.site_energy_kwh` | One site-result owner per completed hour. |
| `outcome.discomfort_zone_hours`, `outcome.discomfort_pmv_hours`, `outcome.occupied_peak_absolute_pmv`, `outcome.setpoint_total_variation_c`, `outcome.setpoint_direction_reversals` | Deterministic derived-feature block. |
| `lesson` | Completed-hour decision summary; multi-sentence text is preserved after whitespace normalization. |

The compiler additionally derives temperature, PMV, and setpoint changes over the last physical step and the completed hour, plus temperature slope per hour. These use only samples 0–4 of the completed record. They introduce no future signal, target, action recommendation, or control rule.

## Audit-only proof fields

The following fields remain in canonical, human-debug, compact, and audit views, but are not repeated in the next Agent's rendered working history because they are verifier evidence rather than a new decision fact:

- `action.admission.completed_validation_stages`;
- `action.proposal.causal_edge_ids`;
- `action.proposal.expected_effects`;
- `action.proposal.consistent_program_direction_proof`.

The model-facing completed decision still contains the proposal operation and rationale, admission disposition, program-version transition, applied actions, assurance results, and physical outcomes. No audit evidence is deleted from disk or from the reversible compiled representation.

## Control specification aliases

The audit view retains original field names. The Agent view uses shorter self-explaining display names only where the meaning is unchanged: `bounds_source → source`, `a_rule_you_add → new_rule`, `conditions_may_test → condition_fields`, `compared_against → comparison_value`, `actions → action_types`, `most_rules_at_once → max_rules`, `weather_condition_values → weather_literals`, and `parameter_references → parameter_refs`.

## Long-term-experience modes

- Memory off: no long-term-experience heading, slot, revision, CRUD operation, or `memory_refs` field is rendered.
- Memory on: only regimes actually observed in the completed hour are shown, in first-observed-step order. The canonical three-slot store and append-only CRUD audit remain unchanged.

No operation semantics, causal admission, Budget, Safety, interpreter behavior, settlement order, or physical action mapping changed.
