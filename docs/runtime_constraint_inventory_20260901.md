# H3C Runtime Constraint Inventory (2026-09-01)

This inventory is descriptive and test-facing. It does not add a runtime gate.

## Allowed runtime owners

| Owner | Production implementation | Frozen scope |
|---|---|---|
| Output and executable DSL contract | `h3c.agents.roles`, `h3c.control.program` | JSON/output shape, operation fields, identifiers, indices, finite values, program syntax and executable program invariants |
| ProgramCheck | `apply_patch`, `program_delta` | Frozen program validity and computable program effect |
| CausalProof | `causal_admissibility` | Referenced confirmed edges, direction compatibility and consistent whole-program direction proof |
| Offline graph compilation | graph onboarding and confirmation workflow | Discovery and confirmation are offline only, never an online patch veto |
| Retired checks | none | Previously retired checks remain retired |
| Coordination Budget | `BudgetLedger`, `validate_allocation`, `validated_fallback_allocation` | Frozen reserved/shared allowance and deterministic settlement only |
| Action assurance | `action_assurance` | Frozen comfort-recovery, setpoint-rate and actuator-bound order; the optional extra guard remains disabled |
| Interpreter and initial policy | `ProgramLedger`, `evaluate_program`, case P0 files | P0, `pmv_step_c=0.3`, interpreter and action mapping remain unchanged |

The sole ordered patch-admission chain is `VALIDATION_STAGES` in
`h3c.control.validation`:

```text
program_validation
causal_admissibility
consistent_program_direction_proof
energy_budget_validation
```

No reward field participates in that chain, action assurance, causal proof,
Budget settlement or program interpretation. Completed-interval reward is
retrospective observed outcome feedback only.

## Explicitly absent

The production runtime contains no reward threshold or reward veto, cooldown,
minimum hold time, reversal ban, added PMV recovery rule, delayed-edge control
law, Hydro-specific prompt/parameter/rule, or verifier-driven action gate.

The terminal reward/PMV criteria in
`configs/evaluation/reward_pmv_release_criteria.json` are evaluation-only and
are never imported by a controller, validator, interpreter or safety module.
