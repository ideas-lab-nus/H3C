# MZ_Hydro hierarchical MAPPO

- Checkpoint: `epoch_0700_steps_001344000.mappo.pt`
- Training identity: epoch 700, 1,344,000 environment steps
- Inference: two independent actor means (`NZ`, `SZ`) on CPU; central critic is not used
- Tensor contract: global 45 observations, local 33 observations per actor
- Action contract: occupied 25 °C / unoccupied 30 °C base plus residual [-5, 5] °C
- Selection: user-designated extended-training checkpoint
- Limitation: the original report marked convergence false (criteria C1 and C4 failed)

The checkpoint is frozen for honest evaluation, not claimed to be fully converged.
