# Frozen DRL input-contract repair result

Date: 2026-08-29

Implementation commit: `efc411e`

Physical reproduction status: not started at the time of this note

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

No DeepSeek call, BOPTEST run, model training, MPC work, paper/LaTeX/Figure edit, history deletion, or push occurred during this repair.
