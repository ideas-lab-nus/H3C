# MZ_Air hierarchical MAPPO

- Checkpoint: `mappo_best.pt`
- Training identity: epoch 298, 801,024 environment steps
- Inference: five independent actor means on CPU; central critic is not used
- Tensor contract: global 81 observations, local 33 observations per actor
- Policy zone order: `cor, nor, sou, eas, wes`
- Local actor order: time, shared power/weather/price, own temperature/PMV/action, own raw-binary
  occupancy; histories include the latest sample
- Action contract: 25 °C base plus residual [-5, 5] °C, clamped to [20, 30] °C
- Selection: highest training-log mean return; no formal evaluation result was used

## Provenance limitation

This is the currently readable epoch-298 checkpoint. Its bytes and the saved `Visfinal.ipynb`
tensor contract are internally reproducible, but they cannot be cryptographically bound to the
legacy `mappo_validation_air_5zone.csv` trajectory. The saved notebook stopped at a checkpoint
load error, the later CSV records no checkpoint hash, and none of the eight surviving MAPPO
checkpoints reproduces that CSV's first action. Results from this file must therefore be described
as a reconstruction with the surviving checkpoint, not as an exact replay of the historical
H-DRL trajectory.

The immutable byte count and SHA-256 are owned by `models/registry.json`.
