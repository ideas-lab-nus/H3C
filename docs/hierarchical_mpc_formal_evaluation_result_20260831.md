# Hierarchical MPC formal evaluation result (2026-08-31)

## Scope and identity

The three fitted vector-ARX models were frozen without changing their data,
coefficients, reward, weights, robust margins, optimizer, solver, controller, or
fallback behavior. The formal suite ran once per case from source commit
`53983f2411fe536435c708c88f3adada3080d393` and freeze identity
`f5cf1873428d81ad0ab9f5d60abbb564788a202683aa047865175f04cc78a467`.

The original validation result remains visible: SZ Air entered the registry through
the explicit post-result `METHOD-DEGRADED-VALIDATION` path after one validation
fallback; MZ Hydro and MZ Air were `BASELINE-READY`. Formal execution classification
is reported separately below.

| Case | Window | Test identity | Run identity | Formal execution |
|---|---:|---|---|---|
| SZ Air | 168 h | `4f0b5c71-f31a-49fc-9611-ad20cdf9788e` | `07105570839a…` | `METHOD-DEGRADED` |
| MZ Hydro | 120 h | `73aa7015-5d5c-4e82-bfd0-803a2379b4ab` | `9954bed3f594…` | `BASELINE-PASS` |
| MZ Air | 168 h | `7df2b13b-c5da-4ca3-b1eb-527a82d764ea` | `f028b98b764b…` | `BASELINE-PASS` |

All three runs passed trajectory recomputation, controller replay, lifecycle,
test-identity continuity, model identity, native KPI, secret, and completion checks.
The concurrent suite evidence identity is
`01110593a406bec25858b71a91b231e0f004128c08078cd8bee414af3770d51c`.

## Formal MPC results

| Case | Cost | Energy (kWh) | Reward | Zone-h | PMV·h | Peak \|PMV\| | TV (°C) | Reversals | Crossings | Fallbacks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SZ Air | 5.510229 | 55.963611 | -670.610306 | 1.750 | 0.090000 | 0.570 | 185.952 | 264 | 10 | 1 |
| MZ Hydro | 119.634309 | 777.274964 | -180.148199 | 0.000 | 0.000000 | 0.480 | 79.355 | 271 | 0 | 0 |
| MZ Air | 155.401137 | 1385.508414 | -591.127379 | 5.500 | 0.427500 | 0.780 | 718.531 | 1124 | 24 | 0 |

## Comparison with the frozen RBC/DRL baselines

Positive reward deltas mean that MPC achieved the better objective value. Cost and
energy deltas are relative percentages, so negative values favor MPC.

| Case | Comparator | Reward delta | Reward delta (%) | Cost delta (%) | Energy delta (%) |
|---|---|---:|---:|---:|---:|
| SZ Air | Basic RBC | +45.971 | +6.42 | -7.28 | -7.97 |
| SZ Air | P0/eRBC | -30.106 | -4.70 | +3.76 | +1.28 |
| SZ Air | C-DRL | -34.129 | -5.36 | +4.46 | -2.92 |
| MZ Hydro | Basic RBC | +86.891 | +32.54 | -32.56 | -32.51 |
| MZ Hydro | P0/eRBC | -0.794 | -0.44 | +0.60 | -0.14 |
| MZ Hydro | C-DRL | +26.711 | +12.91 | -10.71 | -10.80 |
| MZ Hydro | H-DRL | +29.278 | +13.98 | -8.92 | -8.94 |
| MZ Air | Basic RBC | +136.057 | +18.71 | -20.47 | -19.08 |
| MZ Air | P0/eRBC | -31.997 | -5.72 | +3.57 | +2.09 |
| MZ Air | C-DRL | +27.851 | +4.50 | -5.42 | -9.48 |
| MZ Air | H-DRL | -45.341 | -8.31 | +9.91 | +1.26 |

Reward ranking within each case was:

1. SZ Air: C-DRL, P0/eRBC, hierarchical MPC, Basic RBC.
2. MZ Hydro: P0/eRBC, hierarchical MPC, C-DRL, H-DRL, Basic RBC.
3. MZ Air: H-DRL, P0/eRBC, hierarchical MPC, C-DRL, Basic RBC.

The central result is therefore consistent across all three cases: hierarchical MPC
outperformed Basic RBC on the registered reward, but it did not dominate the stronger
baselines. Hydro was effectively tied with P0/eRBC (0.44% lower reward) and clearly
outperformed both DRL controllers while retaining zero PMV discomfort. MZ Air
outperformed C-DRL but trailed P0/eRBC and H-DRL. SZ Air trailed P0/eRBC and C-DRL and
incurred modest discomfort.

## Solver and prediction diagnostics

| Case | Optimized steps | Fallbacks | Mean elapsed/step (s) | Coordinator iterations p95/max | Zone iterations p95/max | Feedback steps |
|---|---:|---:|---:|---:|---:|---:|
| SZ Air | 671/672 | 1 | 0.070 | 900 / 16,025 | 19,875 / 33,375 | 37 |
| MZ Hydro | 480/480 | 0 | 0.228 | 1,025 / 1,850 | 325 / 3,500 | 166 |
| MZ Air | 672/672 | 0 | 0.623 | 1,075 / 7,475 | 2,325 / 7,050 | 331 |

The sole formal fallback occurred in SZ Air at step 4 in the building coordinator:
OSQP reached its registered 50,000-iteration limit (primal residual `0.001826`, dual
residual `0.0000182`) and the existing enhanced-RBC fallback was applied. No run was
retried or tuned.

Post-hoc one-step diagnostics compare each optimized step's first predicted output with
the same step's post-action physical outcome:

| Case | Temperature RMSE (°C) | Site-power RMSE (W) |
|---|---|---:|
| SZ Air | zone1: 0.480 | 62.4 |
| MZ Hydro | NZ: 0.066; SZ: 0.071 | 2,443.5 |
| MZ Air | zones: 0.239–0.319 | 2,915.6 |

The temperature models are usable, especially for Hydro, while the multi-zone site-power
models are materially less accurate. This is consistent with the deliberately short,
low-diversity identification week and helps explain why MPC is competitive but not
uniformly superior. These diagnostics are explanatory and did not change model selection
or the formal results.

## Interpretation and review point

The result is sufficient to establish a real, reproducible hierarchical-MPC baseline:
all three controllers completed the formal windows, all beat Basic RBC on reward, and two
ran without fallback. It should not be described as a universally superior controller.
SZ Air must retain its `METHOD-DEGRADED` label, and MZ Air's peak `|PMV|=0.78` and frequent
small setpoint reversals should be reported as adverse performance rather than tuned away.

The unified report contains the exact 14-arm CSV/JSON/Markdown outputs, fourteen per-run
trajectory figures, and three case-level controller comparison figures at:

`outputs/baselines/reports/baseline-report-20260830T170338Z/`

No online H3C Agent code, paper source, LaTeX, or Figure 3 was changed, and nothing was
pushed. Integration remains pending explicit user review and approval.
