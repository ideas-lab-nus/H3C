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
