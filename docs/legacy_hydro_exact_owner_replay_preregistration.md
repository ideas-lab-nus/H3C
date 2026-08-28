# Hydronic exact-owner replay preregistration

Date: 2026-08-29

## Question

After correcting the migrated Hydronic action-history normalization, do the user-designated
epoch-650 PPO and epoch-700 MAPPO checkpoints reproduce their delivered five-day results when run
through the delivered evaluator and wrapper themselves? This diagnostic separates an H3C adapter
issue from a historical environment/device result that can no longer be reconstructed.

## Frozen inputs

- Checkpoints are the files registered in `models/registry.json`; no result-based checkpoint
  selection is allowed.
- The production owner is the delivered
  `Revision1/MZ_Hydronic_Final_PPO_MAPPO_1h_Epoch700_20260822/project/CASE_TEST` source:
  `rl_retraining_wave2.rollout_policy`, its `NormalizedObservationWrapper`, and
  `rl_retraining_v3.V3ForecastProvider(include_validation=True)`.
- Inference is deterministic on CPU. The diagnostic does not test an unrecorded historical GPU
  execution.
- The physical protocol is the delivered held-out validation protocol: day 220, 480 fifteen-minute
  steps, with the delivered seven-day BOPTEST warm-up and no explicit vanilla prefix.
- Outputs are written only under a new ignored H3C diagnostic directory. No historical delivery
  file is modified.

## Execution

Run exactly two fresh physical arms, strictly serially: PPO first, then MAPPO. Each arm receives a
fresh BOPTEST test identity and is attempted once. There is no resume, retry, lucky rerun, training,
DeepSeek call, or modification of either evaluator or checkpoint.

For each arm preserve the delivered validation trajectory, actions, aggregate metrics, checkpoint
identity, evaluator-source identity, device, lifecycle, and stop outcome. A real
initialization/advance/stop failure, changed test identity, missing trajectory, or corrupt evidence
hard-stops the diagnostic before the next arm.

## Interpretation

- If the delivered owner reproduces the H3C corrected trajectory/KPI, the remaining difference
  from the archived aggregate is not an H3C adapter defect; it is an unbound historical
  environment/device/run identity.
- If the delivered owner reproduces the archived aggregate while H3C does not, compare the two
  trajectories at the first divergent observation/action and repair only that evidenced adapter
  difference.
- Intermediate values do not authorize checkpoint reselection or tuning. The original adverse
  evidence and all fresh outputs remain preserved.

