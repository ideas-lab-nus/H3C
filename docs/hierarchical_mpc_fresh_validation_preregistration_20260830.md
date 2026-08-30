# Hierarchical MPC fresh-validation and model-freeze preregistration

Date: 2026-08-30

## Question and immutable inputs

This stage asks whether all three finite, persistence-beating candidates from one completed
offline-refit workspace pass one fresh closed-loop BOPTEST validation.  The refit workspace is
verified before any test selection and remains immutable.  No new identification data are
collected, no candidate is refit, and no reward, model, threshold, or action support is changed.

## Physical protocol

The natural validation matrix contains exactly one arm for each registered case: `SZ_Air`,
`MZ_Hydro`, and `MZ_Air`.  All three futures are submitted together without a client-side worker
limit.  BOPTEST owns admission through each fresh test ID's `Queued`/`Running` state.  Every arm
uses the evaluation-preceding training week, a complete seven-day internal warm-up, and 668
closed-loop 15-minute advances, leaving four forecast steps for the registered horizon and
terminal occupancy reference.

Every arm has an independent client, test ID, directory, execution lock, and lifecycle evidence.
All submitted
futures are awaited even if another arm fails.  Initialization, advance, test-identity,
lifecycle, secret, and evidence corruption are hard failures.  Controller fallback or a physical
PMV gate failure is preserved as adverse method evidence and is never retried.

## Frozen gates

Each arm must prove:

- the refit workspace and exact candidate identity still pass their source-evidence verifier;
- the candidate is finite and its recomputed source gate beats persistence;
- exactly 668 contiguous advances occurred on one fresh test ID after `Running` admission;
- the step reward, cost, occupied peak absolute PMV, fallback count, timeline, clothing, PMV,
  occupancy-specific action support, and model identity can be recomputed from recorded
  diagnostics and cross-checked against the episode trajectory and manifest;
- fallback count is zero and occupied peak absolute PMV is at most 0.70;
- lifecycle is exactly one select, one configure, one initialize, and one stop, with `Running`
  observed before configure and initialize;
- the validation workspace contains no configured model secret.

One failed case fails the suite.  There is no recollection, resume, retry, lucky rerun, partial
freeze, or formal evaluation from a failed validation.

## Transaction boundary

Only an independently reverified three-case validation suite may be frozen.  The complete model
suite is staged at `models/.mpc-<suite-identity>.pending/`, including all three coefficient
bundles, model cards, training/validation manifests, and a suite freeze manifest.  The registered
target `models/mpc` and the pending path must not already exist.  The freeze identity covers
source-model hashes, independently recomputed persistence gates, physical validation
attestations, and canonical robust-margin/calibration provenance.  The final tracked bundle
remains self-verifiable when ignored run workspaces are absent.  After the entire pending suite
passes identity, provenance, file-set, validation, runtime-load, and secret checks, exactly one
directory-level
`os.replace` publishes it as `models/mpc`.  The implementation never overwrites or deletes an
existing target and never promotes an individual case.

This stage does not run formal MPC evaluation, modify online H3C, call DeepSeek, edit the paper,
or push.
