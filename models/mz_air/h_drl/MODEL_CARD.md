# MZ_Air hierarchical MAPPO

- Checkpoint: `mappo_best.pt`
- Training identity: epoch 298, 801,024 environment steps
- Inference: five independent actor means on CPU; central critic is not used
- Tensor contract: global 81 observations, local 33 observations per actor
- Policy zone order: `cor, nor, sou, eas, wes`
- Action contract: 25 °C base plus residual [-5, 5] °C, clamped to [20, 30] °C
- Selection: highest training-log mean return; no formal evaluation result was used

The immutable byte count and SHA-256 are owned by `models/registry.json`.
