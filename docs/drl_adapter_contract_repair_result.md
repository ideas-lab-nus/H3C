# Frozen DRL adapter repair and 7/5/7 benchmark result

Date: 2026-08-28  
Runtime source: `9eaa760a3e9c72a3bbb6f4d862be6d06919243b3`  
Suite: `formal-drl`  
Status: 11/11 `BASELINE-PASS`; MPC excluded

## Scope and identities

This result implements the user decisions that SZ_Air and MZ_Air use the checkpoints from their
archived evaluation workflows, MZ_Hydro uses the newly delivered extended-training checkpoints,
and the formal evaluation windows are seven days for both Air cases and five occupied weekdays
for MZ_Hydro. All arms used a fresh BOPTEST target, seven days of server warm-up, and a same-test-id
seven-day vanilla-RBC prefix before evaluation.

The frozen checkpoint identities are:

| Case | Controller | Frozen checkpoint identity |
|---|---|---|
| SZ_Air | C-DRL | PPO epoch 297, SHA-256 `abd5d1adb751...cc553` |
| MZ_Hydro | C-DRL | PPO epoch 650, SHA-256 `beba50eb178a...9e90a` |
| MZ_Hydro | H-DRL | MAPPO epoch 700, SHA-256 `3644b477c4e0...fd7a` |
| MZ_Air | C-DRL | archived evaluation PPO at 295,680 steps, SHA-256 `368a19d88522...de477` |
| MZ_Air | H-DRL | archived MAPPO epoch 298, SHA-256 `2b6b1c2c83f4...f35a10` |

The legacy notebooks were used as read-only executable-contract oracles. The repaired adapters now
preserve the model-specific history offsets, cold starts, occupancy representation, local MAPPO
column order, policy zone order, normalization and residual action mapping. In particular, the
archived MZ_Air MAPPO workflow uses actor order `cor,nor,sou,eas,wes`, local columns ordered as
time, shared power/weather/price, own temperature/PMV/action, and own raw-binary occupancy, followed
by the action mapping `25 °C + 5 × residual`. The current implementation matches those semantics.

## Results

Cost and energy are physical-window totals. PMV·h is occupied exceedance beyond the registered
comfort threshold, not average absolute PMV.

| Case | Controller | Cost | Energy (kWh) | Reward | Zone-h | PMV·h | Peak `|PMV|` |
|---|---|---:|---:|---:|---:|---:|---:|
| SZ_Air | basic RBC | 5.986701 | 61.276888 | -721.767327 | 0.00 | 0.0000 | 0.18 |
| SZ_Air | enhanced RBC | 5.350975 | 55.711703 | -645.256799 | 0.00 | 0.0000 | 0.39 |
| SZ_Air | C-DRL | 5.312097 | 58.174989 | -640.990893 | 1.00 | 0.0150 | 0.52 |
| MZ_Hydro | basic RBC | 182.994821 | 1188.155972 | -275.370229 | 0.00 | 0.0000 | 0.19 |
| MZ_Hydro | enhanced RBC | 123.530880 | 808.699085 | -186.179586 | 0.00 | 0.0000 | 0.47 |
| MZ_Hydro | C-DRL | 141.630571 | 919.697887 | -220.042901 | 4.75 | 0.1350 | 0.56 |
| MZ_Hydro | H-DRL | 149.747581 | 971.877644 | -235.372291 | 0.25 | 0.0025 | 0.51 |
| MZ_Air | basic RBC | 207.525150 | 1836.241678 | -772.053857 | 0.75 | 0.0225 | 0.55 |
| MZ_Air | enhanced RBC | 160.493878 | 1463.226231 | -597.668353 | 0.00 | 0.0000 | 0.48 |
| MZ_Air | C-DRL | 152.325685 | 1503.543680 | -617.396787 | 58.75 | 3.3025 | 0.67 |
| MZ_Air | H-DRL | 130.838855 | 1251.942836 | -5469.265953 | 308.75 | 81.7875 | 1.39 |

Relative to each case's enhanced RBC:

- SZ_Air C-DRL changes cost by -0.727% and energy by +4.421%, with 1.00 zone-h of comfort
  exceedance. Its cost is again close to the archived evaluation result, supporting the adapter
  repair.
- MZ_Hydro C-DRL changes cost by +14.652% and energy by +13.726%; H-DRL changes cost by +21.223%
  and energy by +20.178%. The five-day time series shows high-frequency setpoint movement and
  stronger cooling than enhanced RBC. Because both new policies now use their exact training-time
  observation and action contracts, this adverse result is attributed to the delivered policies
  under the common protocol rather than a remaining migration mismatch.
- MZ_Air C-DRL changes cost by -5.089% but energy by +2.755%, with 58.75 zone-h. H-DRL changes cost
  by -18.477% and energy by -14.440%, but has 308.75 zone-h and peak `|PMV|=1.39`. The H-DRL trace
  uses high cooling setpoints for long occupied periods: its low cost is an unacceptable
  energy-comfort tradeoff, not a successful overall controller.

## Occupancy and MZ_Air cost

The newer official occupancy rule did not cause the observed MZ_Air basic-RBC cost increase. In
the current basic-RBC trajectory, approximately 207.51968 of total cost 207.52515 occurs on steps
where at least one zone is effectively occupied; only about 0.00547 occurs while all zones are
unoccupied. Fewer occupied steps therefore act in the expected cost-reducing direction.

The old and current totals are not a single-factor occupancy experiment. The archived evaluation
initialized directly into its evaluation scenario with the old internal conditioning behavior;
the current benchmark uses an exact seven-day server warm-up and an explicit same-test-id
seven-day vanilla prefix. These produce a different physical boundary state, weather trajectory
conditioning and accumulated plant state. A causal occupancy-cost claim would require a paired run
from the same boundary with only the occupancy rule changed. No such claim is made here.

Policy input and KPI occupancy deliberately have separate owners: frozen MZ_Air policies receive
the raw forecast converted to the binary mask on which they were trained, while physical comfort
and KPI accounting retain the current official effective occupancy definition.

## Evidence and limits

The generated local report is
`outputs/baselines/reports/baseline-report-20260828T121728Z/`; it contains the machine-readable
table, individual-run plots, cross-controller time-series figures, and a summary figure. Generated
run and report artifacts remain ignored by Git.

One earlier C-DRL attempt reached the prefix before discovering that the integrated environment
lacked the optional baseline dependencies. Its incomplete workspace is preserved as infrastructure
evidence and is not counted. Runtime source `9eaa760` adds a dependency, checkpoint and controller
preflight before any artifact creation or BOPTEST initialization. The complete suite then passed
with 286 tests, Ruff check/format, strict mypy over 110 source files, and CPU load/SHA verification
for all five checkpoints.

The earlier `baseline_formal_7d_result_20260828.md` remains immutable adverse migration evidence.
It must not be combined with this corrected-source result. This benchmark does not include MPC and
does not modify the H3C online controller.
