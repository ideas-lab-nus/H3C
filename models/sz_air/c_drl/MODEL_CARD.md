# SZ_Air centralized PPO

- Checkpoint: `best_model_ppo.zip`
- Training identity: epoch 297, 798,336 environment steps
- Inference: one centralized Stable-Baselines3 PPO policy, CPU, deterministic action
- Tensor contract: 36 observations → 1 residual action
- Action contract: 25 °C base plus a residual in [-5, 5] °C, clamped to [20, 30] °C
- Selection: highest training-log mean return; no formal evaluation result was used
- Cold start: legacy action history is 24 °C; temperature history repeats the first observation

The immutable byte count and SHA-256 are owned by `models/registry.json`.
