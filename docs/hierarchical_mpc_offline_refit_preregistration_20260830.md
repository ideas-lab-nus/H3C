# Hierarchical MPC offline-refit recovery preregistration

Date: 2026-08-30

## Question and immutable source

The preserved training suite
`outputs/baselines/mpc/training/20260829T155735636396Z-3d327838` contains a complete
seven-day identification bank for all three cases but terminated because the MZ Air
closed-loop candidates exceeded the registered physical PMV gate.  This recovery asks whether
the already collected, causally prior trajectories can support a better calibrated instance of
the same four-lag, four-step vector-ARX hierarchical MPC.

The source suite remains immutable.  The recovery is a pure offline transformation: it does not
select a BOPTEST test case, initialize or advance a simulation, call DeepSeek, collect another
episode, or synthesize a target.  A run creates a new `outputs/baselines/mpc/refit/` workspace only
when `--execute` is explicit; the default command is a dry plan.

## Frozen episode roles

For each case, episode identity is taken from the saved manifest and cross-checked against the
registered checkpoint report.  Roles are assigned in the original checkpoint order:

- every PRBS/GBN `fit` episode and the one `basic_reference` episode enter the fit set;
- the first two validation episodes with zero fallback enter the adaptive fit set;
- the last validation episode with zero fallback is the sole residual-calibration episode;
- every validation with a fallback is excluded;
- any remaining zero-fallback validation is unused rather than silently reassigned;
- all four whole-episode holdouts remain isolated from coefficient/scaling fit and calibration.
  They are used only for the existing finite ridge-alpha selection and the registered
  model-versus-persistence open-loop gate (`holdout_use` is
  `alpha_selection_and_persistence_gate_only`; `final_fit_includes_holdout` remains false).

At least three zero-fallback validation episodes are required.  Every role set is disjoint and
each source manifest and trajectory is hashed in the refit evidence.  The fit still constructs
history inside one episode at a time, so no ARX row crosses an episode boundary.
Source admission also requires exact registered timelines (672 actions for fit, holdout, and
Basic RBC; 668 for validation), contiguous fit IDs, and the frozen four-lane assignment
(`episode mod 4` for fit/holdout and lane 0 for Basic/validation).

## Calibration and controller semantics

The ARX layout, variables, four lags, four-step horizon, fixed ridge grid, objective weights,
control-support bounds, hourly coordinator, 15-minute zone optimizers, and one-feedback limit are
unchanged.

For every calibration origin, the saved real controls and disturbances produce a four-step model
rollout.  PMV is recomputed with the shared comfort owner for both predicted and observed zone
temperatures.  Occupancy for each scored target is joined by timestamp to the complete saved
Basic-RBC reference; in particular, the terminal calibration score uses the real
`occupancy(k+4)`, never the disturbance at `k+3` or the validation trajectory's duplicated
terminal row.  This is a calibration audit source, not the runtime terminal-reference owner.
All exogenous disturbance columns on shared non-terminal timestamps must exactly match the
Basic-RBC reference before calibration is allowed.
Each case receives its own robust-margin estimate from the same common formula: the empirical
95th percentile (the deterministic `higher` order statistic) of that case's absolute occupied PMV
residuals (`scope=case_specific_estimate_common_formula`).  A case fails offline eligibility
if the residual set is empty or non-finite, or if the margin is not in `[0, 0.5)`.

The margin does not change the public reward or add a hard PMV constraint.  It only tightens the
MPC's internal soft-exceedance reference from `0.5` to `0.5 - margin`; physical validation keeps
the unchanged zero-fallback and peak occupied absolute PMV `<= 0.70` gates.  Between hourly
coordinator updates, the newly appended fourth control reference is rebuilt from the actual
effective-occupancy forecast at `k+4`, using the existing Basic-RBC 25/30 schedule, before applying
the unchanged identification-support bounds.  The four-row ARX/QP horizon remains `k..k+3`;
`occupancy(k+4)` is a separate terminal-reference input.

## Offline gates and transaction boundary

Each candidate must have finite coefficients and calibration statistics and must beat the same
persistence predictor on the isolated whole-episode holdout for all registered output metrics.
The workspace records source-file hashes, exact episode roles, row counts, disjointness checks,
holdout quality, terminal-occupancy provenance, calibration residual statistics, robust margin,
and model identity.

Verification independently rebuilds the ridge fit and calibrated candidate from the immutable
source bank, then compares the exact coefficients, scaling, alpha, fit report, margin, and model
identity.  Coordinated edits to the staged model card, report, and coefficient file therefore fail.

`completion.json` is written atomically only after all three cases pass and the workspace secret
scan is clean.  Candidate files remain staged inside that refit workspace; no case is promoted to
`models/mpc/` by this command, so an adverse case cannot leave a partial frozen suite.  Failure
evidence is retained in the new workspace.

## Next physical decision

Offline completion authorizes no result claim.  A later, separately launched fresh validation per
case must still demonstrate a finite controller, better-than-persistence model identity, zero
fallback, and occupied peak absolute PMV at most 0.70.  Any failed case stops the MPC sequence;
there is no data recollection, retry, resume, partial freeze, or formal arm from this recovery.
