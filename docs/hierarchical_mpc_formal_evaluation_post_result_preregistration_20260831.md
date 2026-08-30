# Hierarchical MPC formal evaluation post-result preregistration (2026-08-31)

This decision was made after the registered fresh validation suite
`outputs/baselines/mpc/validation/20260830T155850602571Z-1b297a29` had terminated.
It does not rewrite that suite's failure or its original zero-fallback criterion.

## Evidence and decision

All three fitted ARX candidates are finite, loadable, and beat their registered
persistence predictors. The three fresh validation arms completed 668 steps with
healthy physical, identity, secret, and artifact evidence. MZ Hydro and MZ Air had
zero controller fallback. SZ Air had one fallback at step 412 because OSQP reached
its registered iteration limit; the enhanced-RBC fallback advanced the physical
trajectory normally. The exact candidate model identities are:

- SZ Air: `f2af2932cae8fb4b8846fc921fbdfcfeec359530bd513b3f4a9cee556e39d231`
- MZ Hydro: `04c02b14a69a23f0e698371aee16c8c9093dd3baee2373984692e617ce4aecb1`
- MZ Air: `b5ee83dfa2670472c8f1db413b90ab582508f5a660d9d3a641dd65c296f4a17e`

The user has now requested formal evaluation when the fitted models are complete.
The candidates are therefore admitted through an explicit post-result,
method-degraded publication path. The original strict publication command remains
unchanged and continues to require zero fallback.

## Frozen scope

The adverse publication path may only accept a terminal validation whose sole
failed suite gate is the zero-fallback eligibility aggregate. It must recompute and
require all three arm artifacts, identities, finite metrics, unique test identities,
refit provenance, model identities, physical lifecycle, and secret checks. It must
preserve each original `eligible` value and fallback count and mark the frozen suite
`post_result_method_degraded`; it must not relabel the original validation as passed.

No data, coefficient, ARX structure, reward, objective weight, robust margin,
optimizer, solver setting, controller behavior, or fallback behavior may change.
The candidate coefficient bytes are copied unchanged into one atomic three-case
registry. Any identity, evidence, initialization/advance, secret, or artifact failure
still fails closed.

## Formal evaluation

After the degraded registry and all three model entries verify, run exactly one
fresh formal arm per case using the registered `mpc-formal` suite:

- SZ Air: 168 h;
- MZ Hydro: 120 h;
- MZ Air: 168 h.

Independent arms may run concurrently under BOPTEST service admission. Every arm
records the full performance trajectory, actions, controller diagnostics, MPC
predictions, and solver trace. No arm is resumed, retried, or tuned from its formal
result. Controller fallback produces `METHOD-DEGRADED`, not `RUN-INVALID`; poor
performance remains valid adverse baseline evidence. Initialization/advance,
identity, secret, or evidence corruption remains a hard stop for that arm.

After all three arms terminate, verify each exact run and produce a 14-arm comparison
against the frozen 11-run RBC/DRL evidence set. Present metrics and time-series plots
for user review. Do not push or change the online H3C Agent implementation before
the user separately approves the MPC result and integration.
