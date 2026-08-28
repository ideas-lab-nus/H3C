# MZ_Air centralized PPO

- Checkpoint: `best_model_ppo.zip`
- Training identity: epoch 281, 755,328 environment steps
- Inference: one centralized Stable-Baselines3 PPO policy, CPU, deterministic action
- Tensor contract: 81 observations → 5 residual actions
- Policy zone order: `cor, nor, sou, eas, wes` (explicitly different from profile order)
- Action contract: 25 °C base plus residual [-5, 5] °C, clamped to [20, 30] °C
- Selection: highest training-log mean return; no formal evaluation result was used

The archived model does not prove its random seed; the card therefore makes no seed claim.
