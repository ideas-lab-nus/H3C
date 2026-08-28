# Archived-protocol RBC/DRL reproduction result

Date: 2026-08-29

## Scope

The `legacy-replay` diagnostic ran the archived physical reset protocol once, strictly serially,
without DeepSeek calls or an explicit vanilla prefix:

- SZ_Air: seven-day basic RBC and C-DRL;
- MZ_Hydro: five-day basic RBC, C-DRL and H-DRL;
- MZ_Air: seven-day basic RBC, C-DRL and H-DRL.

All eight runs completed as `BASELINE-PASS`. This classification establishes artifact and physical
execution integrity; it does not by itself establish identity with a historical policy trajectory.
Generated evidence is under `outputs/baselines/runs/legacy-replay/`; the aggregate report is
`outputs/baselines/reports/baseline-report-20260828T162907Z/`.

## Reproduction metrics

| Case | Controller | Cost | Energy (kWh) | Reward | Zone-h | PMV·h | Peak | TV (°C) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| SZ_Air | basic RBC | 5.942864 | 60.809304 | -716.581369 | 0.00 | 0.0000 | 0.18 | 70.000 |
| SZ_Air | C-DRL | 5.275260 | 57.648942 | -636.512743 | 1.00 | 0.0150 | 0.52 | 78.074 |
| MZ_Hydro | basic RBC | 177.382582 | 1151.676261 | -267.039670 | 0.00 | 0.0000 | 0.19 | 100.000 |
| MZ_Hydro | C-DRL, pre-repair | 136.611371 | 887.101237 | -211.998656 | 4.50 | 0.1200 | 0.56 | 589.273 |
| MZ_Hydro | H-DRL, pre-repair | 144.383612 | 937.058686 | -227.935855 | 0.75 | 0.0075 | 0.51 | 1280.486 |
| MZ_Air | basic RBC | 180.356170 | 1679.150356 | -669.670556 | 0.50 | 0.0050 | 0.51 | 280.000 |
| MZ_Air | C-DRL | 144.751014 | 1412.727073 | -580.719004 | 52.00 | 2.9200 | 0.72 | 1561.294 |
| MZ_Air | H-DRL | 123.736115 | 1178.138871 | -5090.218041 | 331.00 | 81.0350 | 1.39 | 1313.266 |

The RBC agreement with archived totals, especially the exact Hydronic cost and energy agreement,
shows that testcase selection, evaluation start, static controls and physical reset are healthy.
It does not prove a DRL checkpoint or observation contract.

## SZ_Air conclusion

The surviving PPO checkpoint is the same epoch-297 file used by the archived evaluator (SHA-256
`abd5d1...cc553`). The observation order, normalization, history initialization, action mapping and
full seven-day setpoint trace reproduce; maximum action difference from the archived trace is about
`0.002 °C`. The current reward total is computed by the common H3C metric owner, whereas the old
evaluation omitted a declared smoothness term. The policy migration is healthy; the reward-number
difference is accounting, not control drift.

## MZ_Hydro finding and repair

The extended PPO epoch-650 and MAPPO epoch-700 checkpoint bytes are correct. Observation order,
MAPPO local order, history offsets, occupancy, physical action mapping and static controls also
match the delivered training owner. One real migration defect was found: training normalized the
historical action feature against `288.15–308.15 K` (15–35 °C), while the first H3C migration used
the physical action bounds `293.15–303.15 K` (20–30 °C). This doubled the network input magnitude
at the physical endpoints. Commit `4e961c1d38a49f317c20695f287c019d395c88c9` separates the
observation scale from the unchanged 20–30 °C physical action bounds and adds 20/25/30 °C tests.

Two fresh post-repair diagnostic arms completed under that source:

| Controller | Cost | Energy (kWh) | Reward | Zone-h | PMV·h | Peak | TV (°C) |
|---|---:|---:|---:|---:|---:|---:|---:|
| C-DRL | 138.410302 | 899.126659 | -213.660089 | 2.25 | 0.0575 | 0.55 | 579.368 |
| H-DRL | 144.680585 | 939.031497 | -227.820713 | 0.00 | 0.0000 | 0.50 | 1220.053 |

Evidence is under `outputs/baselines/runs/legacy-replay-hydro-normalization-repair/`; figures and
tables are under `outputs/baselines/reports/baseline-report-20260828T171728Z/`.

The repair is necessary but does not reproduce the delivered final totals (`133.984251` for PPO
and `131.346282` for MAPPO). The delivery retained aggregate metrics and model hashes but not the
raw final trajectories. Therefore a remaining evaluator/input-state difference is still under
audit and the post-repair numbers must not be described as a strict replay of the delivered run.

The original wrappers cast observations and bounds to `float32` before min-max normalization. The
migrated owner initially performed the arithmetic in `float64` and cast only the result. This has
also been corrected because it changes deterministic policy inputs, although the measured action
difference is only about `9.2e-6` and cannot plausibly explain the remaining KPI gap. The two
post-repair physical runs above predate this final arithmetic correction and must not be relabelled
as evidence from the later source.

## MZ_Air checkpoint conclusions

The centralized PPO uses the surviving 295,680-step checkpoint and the tensor contract saved in
`FinalMZAIR.ipynb`. The archived CSV was instead written by a separate `Visualization.ipynb`
runtime, and it records neither checkpoint hash nor pre-action observation. The current checkpoint
reproduces H3C inference exactly but not the CSV's first action; none of the other surviving PPO
candidates reproduces the archived trajectory. The first observable divergence is therefore the
step-zero policy action, not BOPTEST initialization or accumulated physical drift. Because the
historical input/model identity is missing, the current C-DRL result is a surviving-checkpoint
reconstruction rather than a strict replay.

The hierarchical MAPPO case has a stronger provenance failure. The currently readable epoch-298
checkpoint (`2b6b1c...f35a10`) and the saved 33-dimensional evaluator contract deterministically
produce the H3C actions. They do not produce the first action in the archived CSV. None of the eight
surviving MAPPO checkpoints does. The saved `Visfinal` execution stopped at a checkpoint-load error;
the later CSV contains no checkpoint hash and must have come from an unsaved or different runtime
state. Consequently, the current H-DRL result is a reconstruction with the surviving checkpoint,
not a reproduction of the historical paper trajectory. It is not valid to choose another surviving
checkpoint by evaluation KPI merely to approach the old result.

## Current decision boundary

- Keep SZ_Air C-DRL as a verified migration.
- Keep the Hydronic observation-scale repair; do not alter physical action bounds.
- Do not claim strict Hydronic equality until the remaining old-owner difference is resolved or
  bounded.
- Label the current MZ_Air H-DRL policy as a surviving-checkpoint reconstruction unless the exact
  successful historical actor bytes or a checkpoint-bound trajectory are recovered.
- MPC remains outside this diagnostic.
