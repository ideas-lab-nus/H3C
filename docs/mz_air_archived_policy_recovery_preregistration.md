# MZ Air archived-policy recovery diagnostic

Status: frozen before implementation and before any new BOPTEST trajectory on 2026-08-29.

## Question

Can the archived seven-day MZ Air DRL behavior be recovered by using the policy artifact and
episode-start history semantics retained in the user's complete training directory, without
changing the physical case, reward, static controls, action mapping, or KPI calculation?

## Evidence that supersedes the earlier reconstruction

The earlier H3C reconstruction registered a centralized PPO checkpoint at 295,680 steps with
SHA-256 `368a19d8852203534aac2e416ba368853c9f47d4a6d40c527c0d0140a3ede477`.
The complete training directory subsequently supplied by the user retains a different final
best-policy artifact:

- `multizone_office_simple_air_residual_transfer/models_drl/bake/best_model_ppo.zip`;
- SHA-256 `7385e6d9e05593f7aff529f4559ad7f5527b4a25f3d82fddae4646c08b29e11a`;
- 755,328 embedded steps;
- epoch 281, which is the maximum `MeanReward` row in the retained 300-epoch training log.

The retained `MAPPO.ipynb` evaluation owner also initializes each zone with one measured
temperature. At the first decision it uses that value for `current` and `p1`, but fills unavailable
`p2` through `p4` with fixed 298.15 K. The earlier H3C registry instead repeated the measured
temperature into every missing slot. This is an input-contract migration error.

The historical PPO and MAPPO validation CSV files do not record checkpoint hashes. They remain
comparison evidence, not proof that either current file generated every archived action.

## Frozen repair

1. Replace only the MZ Air centralized PPO artifact and registry identity with the retained epoch-281
   best checkpoint above.
2. Change only MZ Air MAPPO `temperature_missing` from `repeat_earliest` to `fixed_25`.
3. Preserve the 81-dimensional global order, 33-dimensional MAPPO local order, binary raw
   occupancy, 25 C residual base, five-zone order `cor,nor,sou,eas,wes`, deterministic CPU
   inference, and float32 normalization arithmetic.
4. Preserve physical actions exactly: AHU supply setpoint 17 C, heating setpoints 15 C, cooling
   residual bounds 20--30 C, and all activation flags enabled.
5. Preserve the archived reset protocol: MZ Air day 199, BOPTEST internal seven-day warm-up, no
   explicit vanilla prefix, and seven evaluation days.

No reward, PMV, occupancy/KPI, power-meter, BOPTEST mapping, static-control, or reporting owner may
change in this diagnostic.

## Offline gates

- checkpoint byte count, SHA-256 and embedded step identity;
- exact first three global/local history windows against `FinalMZAIR.ipynb` and `MAPPO.ipynb`;
- complete observation-to-action-to-BOPTEST golden fixtures for both MZ Air policies;
- negative tests for alternate missing-history behavior, feature order and model identity;
- targeted baseline tests, Ruff, formatting and strict type checking for changed production files.

## Physical diagnostic

After the repair is committed, run exactly two fresh arms, strictly serially:

1. MZ Air C-DRL, seven days;
2. MZ Air H-DRL, seven days.

Each arm is one attempt, deterministic CPU, with a fresh test id and the frozen archived reset
protocol. Initialization/advance, model identity, inference dimension, secret or artifact failure
is a hard stop. Poor KPI performance is valid evidence and is not a reason to retry or reselect a
checkpoint. Existing Basic RBC and prior DRL trajectories remain immutable.

## Interpretation

The diagnostic can establish whether the newly recovered artifact and corrected cold-start
contract explain the migration gap. It cannot retroactively bind a checkpoint to a historical CSV
that omitted model identity, and it does not select a model by new evaluation performance.
