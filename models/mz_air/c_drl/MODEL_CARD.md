# MZ_Air centralized PPO

- Checkpoint: `best_model_ppo.zip`
- Embedded training counter: 295,680 environment steps; the archive does not retain an
  authoritative epoch-to-file mapping for this exact checkpoint
- Inference: one centralized Stable-Baselines3 PPO policy, CPU, deterministic action
- Tensor contract: 81 observations → 5 residual actions
- Policy zone order: `cor, nor, sou, eas, wes` (explicitly different from profile order)
- Action contract: 25 °C base plus residual [-5, 5] °C, clamped to [20, 30] °C
- Observation contract: temperature/action/power histories include the latest sample; occupancy
  is the raw forecast converted to a binary mask without the later official-HVAC-window filter
- Selection: currently readable checkpoint loaded by the saved `FinalMZAIR.ipynb` workflow; no new
  evaluation result was used to select or modify it

## Provenance limitation

The checkpoint bytes and the saved `FinalMZAIR.ipynb` tensor contract are internally reproducible,
but they cannot be bound to the legacy `drl_validation_air_5zone.csv` trajectory. That CSV was
written by a separate `Visualization.ipynb` runtime and records neither a checkpoint hash nor the
pre-action observation. Its first action is not produced by this checkpoint under the saved
`FinalMZAIR` contract, and none of the other surviving PPO candidates reproduces the archived
trajectory. Results from this file must therefore be described as a reconstruction with the
surviving checkpoint, not as an exact replay of the historical C-DRL trajectory.

The archived model does not prove its random seed; the card therefore makes no seed claim.
