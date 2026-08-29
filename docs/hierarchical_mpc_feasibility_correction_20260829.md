# Hierarchical MPC feasibility correction

Date: 2026-08-29

## Preserved failed run

The first physical training attempt used source
`1bf5ec3be7a9c27c54b140cf440dc7b612a839d8` and wrote its immutable partial evidence under
`outputs/baselines/mpc/training/20260829T080633752728Z-1bf5ec3b`.  It collected all 64 SZ Air fit
episodes, four whole-episode holdouts, one Basic-RBC reference, and four closed-loop validation
episodes.  Every fitted model beat the registered persistence predictor, but the validation runs
had 263--300 controller fallbacks and occupied peak absolute PMV between 1.03 and 1.66.  No model
was eligible, so the process exited without `completion.json`; no Hydro or MZ Air training and no
formal MPC evaluation started.

The failed evidence is retained and is not resumed, retried, or reclassified.

## Diagnosis

Three production-path mismatches caused the failure:

1. The QP constrained the raw affine site-power prediction to be nonnegative even though the
   registered model semantics deterministically clip negative power to zero.  During the
   coordinator's reconciliation this could require the same predicted power to be both at least
   zero and at most a negative upper reference, producing OSQP `lower bound > upper bound` setup
   failures.
2. Occupied PMV was represented twice: as the registered soft exceedance loss and as an additional
   hard horizon constraint.  The hard copy made otherwise valid optimization problems infeasible
   and converted model uncertainty into controller fallback.  The `0.70` threshold belongs to the
   closed-loop candidate-selection gate, where it is measured from the physical validation
   trajectory.
3. Although identification deliberately limited occupied excitation to 23.5--26.5 degrees
   Celsius, the optimizer could choose occupied setpoints up to 30 degrees Celsius.  In the failed
   validations it chose values above 26.5 degrees for 166--203 occupied steps, exploiting an
   unsupported extrapolation of the short-data ARX model and causing the adverse comfort results.
4. Between hourly coordinator updates, the rolling horizon copied the previous terminal action into
   the new terminal slot before applying that slot's new occupancy.  At an occupancy transition,
   this could copy a 30-degree unoccupied reference into an occupied slot and make the zone QP
   inconsistent with the identification-support bound.
5. One remaining feasible lower-level QP reached the iteration limit because the implementation
   used a 10,000-iteration numerical budget.  The same unchanged QP solves at the registered
   `1e-5` tolerance when the fixed-rho iteration budget is 50,000; the measured replay cost is
   negligible relative to physical simulation.

## Registered correction before the next physical attempt

The next source makes only the following method-alignment corrections:

- site power remains an affine raw prediction inside the QP, while its objective epigraph and
  reported rollout use `max(raw_power, 0)`; every clipped prediction is counted;
- PMV exceedance remains the shared reward's soft quadratic loss; the physical closed-loop
  validation still requires zero fallback and occupied peak absolute PMV at most 0.70;
- MPC inputs are constrained to the identification support already declared by the training
  configuration: 23.5--26.5 degrees when occupied and 20--30 degrees when unoccupied;
- every shifted hourly reference is reprojected against the occupancy of its new horizon slot;
- OSQP keeps the original fixed-rho formulation and `1e-5` tolerance, with only the iteration
  budget increased from 10,000 to 50,000;
- the hourly coordinator, 15-minute zone optimizers, one-feedback limit, ARX structure, variables,
  ridge grid, episode budget, warm-up protocol, reward weights, model-selection criteria, and
  formal windows are unchanged.

Targeted tests must prove that negative-power clipping no longer makes the QP infeasible, that an
unreachable predicted PMV remains auditable instead of causing a solver fallback, and that every
occupied optimized setpoint stays inside the identification support.  A new training attempt must
use a fresh output directory and a new committed source identity.

## Preserved second failed run

The fresh attempt from source `3201840044ab9f4355890f24963c31308b276963` is preserved under
`outputs/baselines/mpc/training/20260829T120558607929Z-32018400`.  SZ Air completed and produced an
eligible candidate.  MZ Hydro then completed 64 fit episodes, four whole-episode holdouts, four
closed-loop validations, and its Basic-RBC reference.  All four Hydro checkpoints beat persistence
and kept occupied peak absolute PMV at 0.63, but they recorded 103, 78, 119, and 72 controller
fallbacks.  Consequently no Hydro checkpoint was eligible, the process exited without
`completion.json`, MZ Air did not start, and no formal MPC arm started.  The staged SZ Air candidate
is retained with this failed run rather than promoted as a partial suite result.

Exact-source replay of the saved Hydro validation inputs reproduced the failures.  Every fallback
was an OSQP maximum-iteration result; predictions were finite and the candidate still beat the
persistence model.  The same replay also exposed a cross-case numerical issue: the QP mixed site
power in watts (order `10^3` to `10^5`) with temperatures and setpoints (order `10^1`).  Increasing
the iteration limit again would conceal this conditioning defect without fixing it.

## Numerical-equivalence correction

Before the next physical attempt, the QP is corrected without relaxing any physical or model
selection criterion:

- internal site-power auxiliary variables and power constraint rows use kilowatts;
- public inputs, predictions, logs, metrics, and physical admissibility checks remain in watts;
- the cost objective is algebraically rescaled so its physical value and reward weight are
  unchanged;
- OSQP uses deterministic adaptive rho with the same global interval of 100 iterations for all
  cases, while keeping the registered `1e-5` solver tolerance and 50,000-iteration ceiling;
- only exact `solved` status is accepted; `solved inaccurate`, maximum-iteration, infeasible, and
  non-finite results still fail closed;
- solver stage, iteration count, and residuals are recorded so another numerical failure is
  attributable rather than reported as an opaque fallback.

Offline replay using the exact SZ Air and MZ Hydro saved price and trajectory inputs produced zero
fallbacks for both candidates under this single configuration.  The ARX structure, training data,
reward weights, action support, PMV gate, zero-fallback eligibility rule, episode budget, and formal
protocol remain unchanged.

Model freezing is also made suite-transactional: each case is staged inside its run directory and
verified there; final `models/mpc/<case>` directories are promoted only after all three cases and
the secret scan pass.  A failed suite now writes `failure.json` and cannot leave a partial model in
the formal model namespace.  This evidence-handling correction does not alter MPC decisions.
