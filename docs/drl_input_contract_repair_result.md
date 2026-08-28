# Frozen DRL input-contract repair result

Date: 2026-08-29

Implementation commit: `efc411e`

Physical reproduction status: complete (`8/8 BASELINE-PASS`)

## Outcome

The copied training-computer code identified and closed two adapter defects without changing any checkpoint, action mapping, static control, public reward, KPI, evaluation window, or BOPTEST profile:

1. Time-feature normalization is now an explicit frozen-policy property. SZ Air retains `[-1,1]`; both MZ Hydro policies and both MZ Air policies use the historical `[0,1]` fallback before symmetric min-max normalization.
2. DRL policies now receive PMV from a policy-only clothing state based on the original 96 consecutive 15-minute outdoor forecast samples. The public cross-controller comfort/reward/KPI owner remains unchanged and separately logged.

The implementation has no case-name branch. All five registry entries declare their time bounds, and malformed or missing values fail closed.

## Source evidence

| Contract owner | SHA-256 | Finding |
|---|---|---|
| `BESTEST_AIR/FinalSZAIR.ipynb` | `f7909ca720317878c17f49d43e481d810ca201f550407a6a7db208fcce013ab6` | SZ sin/cos bounds explicitly `[-1,1]` |
| `MZ_OFFICE_AIR/FinalMZAIR.ipynb` | `c34d4e5f45a322ab15bd0773e42ba2166553643adfb13e20b538590a02a19b3e` | MZ Air C-DRL uses `[0,1]` fallback and 96-sample clothing input |
| `MZ_OFFICE_AIR/.ipynb_checkpoints/Visfinal-checkpoint.ipynb` | `b284c410bb3ee8da36d23b21a8b23f8024bf00ff07e4fb1d34a9e64f7c474980` | MZ Air H-DRL CSV writer, same `[0,1]` and 96-sample contracts |
| archived MZ Air H-DRL CSV | `ca2110902be747f5b49841c33d498995f0cf1dea5e9cdabf0f955f84373c047e` | first applied setpoints provide an independent five-action oracle |
| delivered Hydro `rl_retraining_v2.py` | `8d1f57930521285dd109ab39a735bf83e15b74158dec38560da7b9fa2a08278e` | PPO/MAPPO environment uses `[0,1]`, 96 samples, 45D/33D contracts |
| `MZ_OFFICE_HYDRONIC/FinalMZHydronic.ipynb` | `0cba50b2abee0243d2af9526e35c1c82ece7ee68ee14fb948bde66413ec7f32a` | independent training-computer confirmation of the Hydro fallback |

## MZ Air checkpoint correction

The retained H-DRL checkpoint is the correct epoch-298 model (`2b6b1c...f35a10`). With only the first normalized time feature corrected from `0` to `-1` at midnight, it predicts:

```text
[0.42137632, 0.16059324, 0.89593881, 0.51246583, 0.60008305]
```

The archived CSV implies:

```text
[0.42137671, 0.16059306, 0.89593762, 0.51246411, 0.60008466]
```

The maximum difference is below `2e-6`. The earlier statement that none of the retained MAPPO checkpoints reproduced the CSV was caused by testing them through the incorrect migrated time normalization. That adverse conclusion remains in the historical result note with an explicit supersession banner.

MZ Air C-DRL remains a different provenance class. Its historical evaluator loaded a mutable `best_model_ppo.zip`, and no archived trajectory binds that file to a hash. The registered epoch-281 checkpoint remains the training-log-best reconstruction; no new KPI or action match was used to replace it.

## Other audited contracts

The copied owners confirm that the following migrated behavior was already correct and was not changed:

- global and local observation dimensions and order;
- per-zone policy/action order;
- temperature, action and power history offsets and cold starts;
- forecast current-plus-four indexing;
- occupancy encoding;
- residual bases, hard action bounds and BOPTEST actuator dictionaries;
- Air AHU/heating static controls and Hydro minimum-setpoint controls;
- checkpoint bytes and deterministic CPU inference.

## Verification

- Focused observation, independent-action, policy-comfort and fake-runtime gates: `41 passed`.
- Frozen checkpoint verification: five SHA/byte identities and five CPU loads passed.
- Ruff check: passed.
- Ruff format check: passed for 162 files.
- Strict mypy: 112 source/test/tool files passed.
- Current shared checkout pytest: `302 passed`, with one repository-structure failure caused solely by ignored `outputs/.uv-cache` dependency caches containing nested `.git` directories.
- Exact `efc411e` archive initialized as a clean standalone repository: `303 passed`; the cache-only failure is absent.
- Legacy reproduction dry plan remains eight fresh serial arms: SZ 7 days, Hydro 5 days, MZ Air 7 days.

## Fresh physical reproduction

All arms used exact source `c6f97b6fd4f0521f487e79ac12c781188534a3b2`, a fresh BOPTEST test identity, the archived internal-warmup evaluation protocol, and one attempt. The eight runs completed with independently recomputed metrics and `BASELINE-PASS`; fallback, model-load, lifecycle, identity, evidence, and secret failures were all zero.

| Case | Controller | Cost | Energy (kWh) | Reward | Zone-h | PMV·h | Peak | TV (°C) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| SZ_Air | basic RBC | 5.942864 | 60.809304 | -716.581369 | 0.00 | 0.0000 | 0.18 | 70.000 |
| SZ_Air | C-DRL | 5.274997 | 57.646601 | -636.481286 | 1.00 | 0.0150 | 0.52 | 78.087 |
| MZ_Hydro | basic RBC | 177.382582 | 1151.676261 | -267.039670 | 0.00 | 0.0000 | 0.19 | 100.000 |
| MZ_Hydro | C-DRL | 133.983467 | 871.429676 | -206.858987 | 0.00 | 0.0000 | 0.49 | 660.137 |
| MZ_Hydro | H-DRL | 131.348523 | 853.591687 | -209.425929 | 2.75 | 0.0525 | 0.55 | 1335.464 |
| MZ_Air | basic RBC | 180.356170 | 1679.150356 | -669.670556 | 0.50 | 0.0050 | 0.51 | 280.000 |
| MZ_Air | C-DRL | 164.310971 | 1530.660913 | -614.003947 | 0.00 | 0.0000 | 0.50 | 1260.692 |
| MZ_Air | H-DRL | 141.393851 | 1368.312715 | -540.511888 | 20.25 | 0.9400 | 0.65 | 1350.201 |

Relative to each fresh basic RBC, cost/energy changes were `-11.24%/-5.20%` for SZ C-DRL, `-24.47%/-24.33%` for Hydro C-DRL, `-25.95%/-25.88%` for Hydro H-DRL, `-8.90%/-8.84%` for MZ Air C-DRL, and `-21.60%/-18.51%` for MZ Air H-DRL.

The aggregate report and all eight time-series figures are under `outputs/baselines/reports/baseline-report-20260828T195538Z/`. Generated runs are under `outputs/baselines/runs/legacy-replay-contract-repair/`.

## Historical replay checks

The Hydro outputs now reproduce the independently delivered extended-training aggregates to numerical simulation tolerance:

- C-DRL: current cost/energy `133.983467 / 871.429676`, delivered `133.984251 / 871.434834`; both have zero comfort exceedance.
- H-DRL: current cost/energy `131.348523 / 853.591687`, delivered `131.346282 / 853.577235`; both have `2.75 zone-h` and `0.0525 PMV·h`.

The MZ Air H-DRL check is stronger because the archived 672-row trajectory exists. Against `mappo_validation_air_5zone.csv`, the fresh run has identical timestamps and maximum differences of approximately `0.00058 °C` in setpoint, `0.00014 °C` in zone temperature, and `0.55 W` in total power. Current total cost/energy are `141.393851 / 1368.312715`; archived totals are `141.393901 / 1368.312933`. The current common-metric reward is `-540.511888` versus the archived evaluator's `-538.964063`; this small accounting difference does not represent control drift.

Therefore the earlier catastrophic MZ Air H-DRL reward and comfort result was an adapter defect, not a wrong MAPPO checkpoint. The repaired trace has peak occupied `|PMV|=0.65` and `20.25 zone-h`, instead of the pre-repair `1.39` and `331 zone-h`.

MZ Air C-DRL remains intentionally qualified: it is the epoch-281 training-log-best checkpoint from the complete final archive, but no checkpoint-bound historical action trajectory exists. Its new physical result is healthy and substantially better than the prior migrated result, but it is a best-supported reconstruction rather than a cryptographically exact paper-trajectory replay.

No DeepSeek call, model training, MPC work, paper/LaTeX/Figure edit, history deletion, or push occurred during this repair and reproduction.
