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
- Selection: exact checkpoint loaded by the archived `FinalMZAIR.ipynb` evaluation workflow; no
  new evaluation result was used to select or modify it

The archived model does not prove its random seed; the card therefore makes no seed claim.
