# Unified baseline evaluation result

Date: 2026-08-29

Physical-run source: `05aba1e11d552ba8a25f859a4a54c8e0e93d40e7`

Reporting implementation: `5e6176c`

Status: 11/11 formal arms and 2/2 MZ Air occupancy-factor arms completed as
`BASELINE-PASS`; no run was resumed or repeated.

## Evidence boundary

All formal arms used a fresh BOPTEST test identity, a 15-minute control step, dynamic electricity
price, one initialization with a seven-day BOPTEST internal warm-up, no application-level prefix,
and one stop. SZ Air and MZ Air were evaluated for seven days; MZ Hydro was evaluated for five
days. Public occupancy was raw for SZ Air and MZ Hydro and
`[06:00,19:00) AND raw > 0` for MZ Air. Frozen MZ Air DRL policies retained their registered
raw-binary occupancy feature.

The generated identity-safe report is
`outputs/baselines/reports/baseline-report-20260829T042957Z/`. It contains JSON, CSV, Markdown,
full run/model identities, native BOPTEST KPIs, and one six-panel time-series figure per arm.

## Formal metrics

| Case | Controller | Cost | Energy (kWh) | Reward | Zone-h | PMV·h | Peak | TV (°C) | Reversals | Crossings |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SZ_Air | Basic RBC | 5.942864 | 60.809304 | -716.581369 | 0.00 | 0.0000 | 0.18 | 70.000 | 13 | 0 |
| SZ_Air | P0 / eRBC | 5.310738 | 55.255547 | -640.504178 | 0.00 | 0.0000 | 0.39 | 70.000 | 13 | 0 |
| SZ_Air | C-DRL | 5.274997 | 57.646601 | -636.481286 | 1.00 | 0.0150 | 0.52 | 78.087 | 124 | 4 |
| MZ_Hydro | Basic RBC | 177.382582 | 1151.676261 | -267.039670 | 0.00 | 0.0000 | 0.19 | 100.000 | 18 | 0 |
| MZ_Hydro | P0 / eRBC | 118.922079 | 778.326369 | -179.354184 | 0.00 | 0.0000 | 0.47 | 100.600 | 20 | 0 |
| MZ_Hydro | C-DRL | 133.983467 | 871.429676 | -206.858987 | 0.00 | 0.0000 | 0.49 | 660.137 | 398 | 0 |
| MZ_Hydro | H-DRL | 131.348523 | 853.591687 | -209.425929 | 2.75 | 0.0525 | 0.55 | 1335.464 | 360 | 20 |
| MZ_Air | Basic RBC | 195.405424 | 1712.296224 | -727.184779 | 0.00 | 0.0000 | 0.49 | 350.000 | 65 | 0 |
| MZ_Air | P0 / eRBC | 150.039335 | 1357.086625 | -559.129956 | 0.00 | 0.0000 | 0.50 | 362.600 | 75 | 0 |
| MZ_Air | C-DRL | 164.310971 | 1530.660913 | -618.978700 | 0.00 | 0.0000 | 0.50 | 1260.692 | 551 | 0 |
| MZ_Air | H-DRL | 141.393851 | 1368.312715 | -545.786362 | 20.25 | 0.9400 | 0.65 | 1350.201 | 1168 | 39 |

The common reward is the current shared cross-controller metric. It is not an archived evaluator
reward.

## Comparison with P0 / eRBC

Cost and energy changes below use the same-case P0/eRBC as denominator. Negative is lower.

| Case | Controller | Cost change | Energy change | Comfort and stability consequence |
|---|---|---:|---:|---|
| SZ_Air | C-DRL | -0.673% | +4.327% | 1.00 zone-h, 0.0150 PMV·h, 124 reversals |
| MZ_Hydro | C-DRL | +12.665% | +11.962% | no comfort exceedance, but TV 660.137°C |
| MZ_Hydro | H-DRL | +10.449% | +9.670% | 2.75 zone-h, 0.0525 PMV·h, TV 1335.464°C |
| MZ_Air | C-DRL | +9.512% | +12.790% | no comfort exceedance, but TV 1260.692°C |
| MZ_Air | H-DRL | -5.762% | +0.827% | 20.25 zone-h, 0.9400 PMV·h, 1168 reversals |

P0/eRBC reduced both cost and energy relative to Basic RBC in all three cases while retaining zero
public comfort exceedance. No DRL controller dominated P0/eRBC across cost, energy, comfort, and
action stability. This is a valid mixed/adverse baseline result, not a controller-identity failure.

## MZ Air occupancy factor

The paired diagnostic changed only Basic RBC's public occupancy rule under the same production
source.

| Occupancy rule | Cost | Energy (kWh) | Reward | Zone-h | PMV·h | TV (°C) |
|---|---:|---:|---:|---:|---:|---:|
| Raw occupancy | 180.356170 | 1679.150356 | -670.831352 | 0.50 | 0.0050 | 280.0 |
| Official occupancy | 195.405424 | 1712.296224 | -727.184779 | 0.00 | 0.0000 | 350.0 |

Official occupancy increased cost by 8.344% and energy by 1.974% while removing the small public
comfort exceedance. This does not mean that an unoccupied step intrinsically consumes more. In
this trajectory, raw-positive periods outside the official window changed from a 25°C occupied
action to a 30°C unoccupied action, increasing daily setpoint movement and the subsequent occupied
recovery load. The conclusion is specific to this paired trajectory.

MZ Air DRL physical cost and energy are unchanged from the repaired replay because their frozen
policy input remains raw-binary occupancy. Their common rewards changed because public reward and
comfort accounting now use official occupancy, as registered.

## Reproduction deviation

The reference is the completed repaired reproduction recorded in
`docs/drl_input_contract_repair_result.md`.

| Case | Controller | Cost deviation | Energy deviation | Reward deviation | Interpretation |
|---|---|---:|---:|---:|---|
| SZ_Air | Basic RBC | 0 | 0 | 0 | Exact at recorded precision |
| SZ_Air | C-DRL | 0 | 0 | 0 | Exact at recorded precision |
| MZ_Hydro | Basic RBC | 0 | 0 | 0 | Exact at recorded precision |
| MZ_Hydro | C-DRL | 0 | 0 | 0 | Exact at recorded precision |
| MZ_Hydro | H-DRL | 0 | 0 | 0 | Exact at recorded precision |
| MZ_Air | Basic RBC | +8.344% | +1.974% | -57.514224 | Registered public occupancy/action change; paired above |
| MZ_Air | C-DRL | 0 | 0 | -4.974753 | Same policy/physical trace; official public reward accounting |
| MZ_Air | H-DRL | 0 | 0 | -5.274474 | Same policy/physical trace; official public reward accounting |

The Hydro values also reproduce the independently delivered extended-training aggregates to the
previously established numerical tolerance. MZ Air H-DRL retains the archived full-trajectory
match; MZ Air C-DRL remains the training-log-best reconstruction because no checkpoint-bound
historical action trajectory exists.

## Native BOPTEST KPIs

| Case | Controller | cost_tot | ener_tot | emis_tot | idis_tot | tdis_tot |
|---|---|---:|---:|---:|---:|---:|
| SZ_Air | Basic RBC | 0.123963 | 1.267096 | 0.838564 | 612.172668 | 72.141619 |
| SZ_Air | P0 / eRBC | 0.110455 | 1.146024 | 0.758439 | 611.515502 | 153.444315 |
| SZ_Air | C-DRL | 0.109923 | 1.202914 | 0.796089 | 610.841421 | 152.371094 |
| MZ_Hydro | Basic RBC | 0.077010 | 0.500662 | 0.071341 | 0.000000 | 0.993037 |
| MZ_Hydro | P0 / eRBC | 0.065016 | 0.424106 | 0.060449 | 0.000000 | 83.691443 |
| MZ_Hydro | C-DRL | 0.068705 | 0.446886 | 0.063745 | 0.000000 | 78.787239 |
| MZ_Hydro | H-DRL | 0.068137 | 0.443152 | 0.063241 | 0.000000 | 82.331333 |
| MZ_Air | Basic RBC | 0.117893 | 1.025480 | 0.349689 | 31.489686 | 101.113092 |
| MZ_Air | P0 / eRBC | 0.090574 | 0.813745 | 0.277487 | 12.255416 | 189.228742 |
| MZ_Air | C-DRL | 0.098932 | 0.912487 | 0.311158 | 3.796677 | 133.491886 |
| MZ_Air | H-DRL | 0.085507 | 0.821351 | 0.280081 | 53.454040 | 164.831374 |

Native KPIs use BOPTEST's own definitions and normalization. They are retained alongside, not
substituted for, the shared cross-controller physical metrics.

## Identity and verification

Every formal run used source `05aba1e11d552ba8a25f859a4a54c8e0e93d40e7` and independently
passed the production verifier. Short run/model identities are:

| Case | Controller | Run identity | Model SHA-256 prefix |
|---|---|---|---|
| SZ_Air | Basic RBC | `712dbbe302c0` | — |
| SZ_Air | P0 / eRBC | `0362f7dbc396` | — |
| SZ_Air | C-DRL | `2db00d0f6b65` | `abd5d1adb751` |
| MZ_Hydro | Basic RBC | `ac33b9fbb816` | — |
| MZ_Hydro | P0 / eRBC | `244d58fe53c9` | — |
| MZ_Hydro | C-DRL | `c20fa3271be2` | `beba50eb178a` |
| MZ_Hydro | H-DRL | `f25230066041` | `3644b477c4e0` |
| MZ_Air | Basic RBC | `32bcb81bdaac` | — |
| MZ_Air | P0 / eRBC | `79242f38f59c` | — |
| MZ_Air | C-DRL | `ede4c64505ff` | `7385e6d9e055` |
| MZ_Air | H-DRL | `dee8a8b1a536` | `2b6b1c2c83f4` |

Full identities are in `report.json`. All runs passed lifecycle, evaluation-boundary, test-ID,
occupancy, trajectory, metric, native-KPI, secret, and completion checks. DRL arms additionally
passed checkpoint and complete policy-input reconstruction.

Post-reporting gates: `308 passed`; Ruff check and format passed for 167 files; strict mypy passed
for 115 source/test/tool files; the offline lock resolved 80 packages. No DeepSeek call, MPC run,
paper/LaTeX/Figure edit, push, resume, retry, or lucky rerun occurred.

## Time-series interpretation

Each figure shows per-zone temperature, setpoint, PMV and occupancy together with cumulative cost
and site power. The clearest adverse patterns are the high-frequency DRL setpoint variation in both
multi-zone cases and the occupied comfort excursions of MZ Air H-DRL. The figures are descriptive;
they do not justify checkpoint selection or post-result controller tuning.

