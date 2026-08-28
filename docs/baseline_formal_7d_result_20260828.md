# Seven-day RBC, frozen-DRL and short-data MPC baseline result

## Evidence boundary

- Production source: `e83972e5320e3658e44d5417fb0dafe1a8aed12f`.
- Execution date: 2026-08-28.
- Matrix: three independent MPC identification trajectories followed by fourteen fresh formal
  evaluations.
- Every evaluation used one fresh BOPTEST test identity, seven days of server warm-up, the
  same-test-id seven-day vanilla-RBC prefix, and a seven-day evaluation (672 15-minute steps).
- All fourteen manifests report one initialize, 672 conditioning advances, 672 evaluation
  advances, one stop, no test-ID change, a completed secret scan and zero secret exposure.
- The public `h3c-baseline verify` command passed for all fourteen run directories.
- Result classification: 11 `BASELINE-PASS`, 3 `METHOD-DEGRADED`, 0 `RUN-INVALID`.

The generated source report is
`outputs/baselines/reports/baseline-report-20260828T090521Z/`. It contains the JSON and CSV
tables plus one time-series figure for every formal arm. Generated run data remain ignored; this
document is the tracked result summary.

## Formal metrics

| Case | Controller | Classification | Cost | Energy (kWh) | Reward | Zone-h | PMV·h | Peak \|PMV\| |
|---|---|---|---:|---:|---:|---:|---:|---:|
| SZ_Air | basic RBC | BASELINE-PASS | 5.986701 | 61.276888 | -721.767327 | 0.00 | 0.0000 | 0.18 |
| SZ_Air | enhanced RBC | BASELINE-PASS | 5.350975 | 55.711703 | -645.256799 | 0.00 | 0.0000 | 0.39 |
| SZ_Air | C-DRL | BASELINE-PASS | 5.311307 | 58.231680 | -641.031318 | 1.25 | 0.0200 | 0.53 |
| SZ_Air | linear MPC | METHOD-DEGRADED | 5.260109 | 53.585117 | -12125.549319 | 42.50 | 18.5875 | 1.66 |
| MZ_Hydro | basic RBC | BASELINE-PASS | 182.994821 | 1188.155972 | -275.370229 | 0.00 | 0.0000 | 0.19 |
| MZ_Hydro | enhanced RBC | BASELINE-PASS | 123.530880 | 808.699085 | -186.179586 | 0.00 | 0.0000 | 0.47 |
| MZ_Hydro | C-DRL | BASELINE-PASS | 143.408376 | 931.033786 | -220.687137 | 3.50 | 0.0925 | 0.54 |
| MZ_Hydro | H-DRL | BASELINE-PASS | 152.132101 | 987.289662 | -241.715695 | 0.25 | 0.0025 | 0.51 |
| MZ_Hydro | linear MPC | METHOD-DEGRADED | 104.762182 | 680.695328 | -858.779209 | 79.25 | 10.1075 | 0.84 |
| MZ_Air | basic RBC | BASELINE-PASS | 207.525150 | 1836.241678 | -772.053857 | 0.75 | 0.0225 | 0.55 |
| MZ_Air | enhanced RBC | BASELINE-PASS | 160.493878 | 1463.226231 | -597.668353 | 0.00 | 0.0000 | 0.48 |
| MZ_Air | C-DRL | BASELINE-PASS | 149.774904 | 1497.541690 | -761.673397 | 75.50 | 8.0750 | 0.77 |
| MZ_Air | H-DRL | BASELINE-PASS | 169.415906 | 1536.276156 | -1176.195064 | 114.00 | 15.9000 | 0.93 |
| MZ_Air | linear MPC | METHOD-DEGRADED | 159.409713 | 1540.775374 | -615.279927 | 35.75 | 1.4675 | 0.61 |

## Comparison with enhanced RBC

Cost and energy changes below use each case's enhanced RBC as the denominator. Negative is lower.

| Case | Controller | Cost change | Energy change | Comfort consequence |
|---|---|---:|---:|---|
| SZ_Air | C-DRL | -0.741% | +4.523% | 1.25 zone-h; 0.0200 PMV·h |
| SZ_Air | linear MPC | -1.698% | -3.817% | 42.50 zone-h; 18.5875 PMV·h |
| MZ_Hydro | C-DRL | +16.091% | +15.127% | 3.50 zone-h; 0.0925 PMV·h |
| MZ_Hydro | H-DRL | +23.153% | +22.084% | 0.25 zone-h; 0.0025 PMV·h |
| MZ_Hydro | linear MPC | -15.194% | -15.828% | 79.25 zone-h; 10.1075 PMV·h |
| MZ_Air | C-DRL | -6.679% | +2.345% | 75.50 zone-h; 8.0750 PMV·h |
| MZ_Air | H-DRL | +5.559% | +4.992% | 114.00 zone-h; 15.9000 PMV·h |
| MZ_Air | linear MPC | -0.676% | +5.300% | 35.75 zone-h; 1.4675 PMV·h |

Enhanced RBC reduced both cost and energy relative to basic RBC in every case while preserving
zero comfort exceedance in SZ_Air and MZ_Hydro and improving MZ_Air comfort. The frozen DRL
policies executed cleanly and reproducibly, but none dominated enhanced RBC across cost, energy
and comfort under this protocol. The new evidence is therefore retained as a valid adverse or
mixed baseline result; checkpoints were not changed after evaluation.

## MPC identification and degradation

All cases used the same four-lag, four-step vector ARX structure and the same registered ridge
grid. Selection used chronological validation and mean standardized output RMSE.

| Case | Identification days | Rows (train/validation) | Selected alpha | Validation score | Evaluation fallback |
|---|---:|---:|---:|---:|---:|
| SZ_Air | 7 | 669 (573/96) | 0.01 | 0.129407 | 5 / 672 |
| MZ_Hydro | 5 | 477 (381/96) | 100 | 0.446769 | 2 / 672 |
| MZ_Air | 7 | 669 (573/96) | 0.000001 | 0.144859 | 95 / 672 |

The fallback paths were explicit enhanced-RBC actions: SZ_Air had five SLSQP iteration-limit
events; MZ_Hydro had one iteration-limit and one incompatible-constraint event; MZ_Air had 80
iteration-limit and 15 incompatible-constraint events. Consequently all three MPC arms are
`METHOD-DEGRADED` even where cost or energy decreased. Their comfort losses and MZ_Air's high
fallback rate are consistent with the preregistered limitation: a short, low-excitation eRBC
trajectory is insufficient for a dependable predictive controller. No fallback is hidden as a
pure MPC action.

## Interpretation boundary

- The old paper values were used only as a migration sanity reference. This fresh 7+7+7 protocol,
  current KPI owner and fixed formal boundaries supersede older evaluation windows; models were
  not selected or altered to reproduce the old table.
- `BASELINE-PASS` means the frozen controller, lifecycle, identity and artifacts are valid. It does
  not mean the controller is better than enhanced RBC.
- `METHOD-DEGRADED` is a method classification caused by at least one optimizer fallback, not an
  infrastructure or evidence failure.
- These results do not modify H3C's online Agent control chain, offline onboarding workflow,
  paper, LaTeX or historical evidence.
