# DRL time-feature contract repair and legacy reproduction preregistration

Date: 2026-08-29  
Status: preregistered before production-code change or new physical run  
Starting implementation HEAD: `67b5966`

## Question

Can the frozen DRL policies be replayed with the exact time-feature normalization used by their original training/evaluation owners, and does that correction explain the previously observed MZ Air H-DRL divergence without selecting a checkpoint from new KPI results?

## New evidence and correction boundary

Read-only inspection of the code copied from the training computer establishes that the time-feature normalization is policy specific:

- `BESTEST_AIR/FinalSZAIR.ipynb` explicitly assigns `[-1, 1]` bounds to `obs_sin_time` and `obs_cos_time`.
- `MZ_OFFICE_AIR/Visualization.ipynb` and `MZ_OFFICE_AIR/Visfinal.ipynb` fall back to `[0, 1]` for those two columns.
- `Revision1/MZ_Hydronic_Final_PPO_MAPPO_1h_Epoch700_20260822/project/CASE_TEST/rl_retraining_v2.py`, which owns the delivered Hydro continuation models' environment, also falls back to `[0, 1]` for those columns.

The current H3C adapter hard-codes `[-1, 1]` for every policy. At midnight this preserves `(sin, cos)=(0, 1)` for SZ Air but converts it to `(-1, 1)` for MZ Air and Hydro, contrary to those owners.

A direct, pre-change inference check further shows that changing only the MZ Air H-DRL time bound to `[0, 1]` makes the retained `mappo_best.pt` first action agree with the archived evaluation CSV to approximately `1e-6`. Therefore the earlier conclusion that the MZ Air H-DRL checkpoint had not been recovered is superseded as a migration diagnosis; its historical evidence remains unchanged.

MZ Air C-DRL is different: the archived evaluator loaded a mutable `models_drl/best_model_ppo.zip`, and none of the retained candidates inspected so far exactly reproduces the archived first action. This repair will not choose a C-DRL checkpoint by new evaluation KPI.

## Single implementation variable

Add a required, validated `time_observation_bounds` field to every frozen policy registry entry and make the observation builder use that field:

| Policy | Frozen bounds |
|---|---|
| SZ Air C-DRL | `[-1.0, 1.0]` |
| MZ Hydro C-DRL | `[0.0, 1.0]` |
| MZ Hydro H-DRL | `[0.0, 1.0]` |
| MZ Air C-DRL | `[0.0, 1.0]` |
| MZ Air H-DRL | `[0.0, 1.0]` |

No case-name branch is permitted. No model bytes, observation ordering, other bounds, history behavior, occupancy encoding, action mapping, reward, static control, BOPTEST profile, evaluation duration, or KPI definition may change in this repair.

## Offline acceptance gates

1. Registry validation rejects absent, malformed, non-finite, or non-increasing time bounds.
2. Independent source-accounted fixtures prove the expected normalized midnight time pair for each policy.
3. The retained MZ Air H-DRL checkpoint reproduces the archived first raw action from the legacy evaluation path within a fixed numerical tolerance; changing its time bounds back to `[-1,1]` must fail that oracle.
4. SZ Air retains its existing independent action oracle; changing it to `[0,1]` must fail.
5. Hydro fixtures are regenerated only after a direct comparison to the delivered training/evaluation owner, not from the migrated adapter alone.
6. Existing observation/history/action-order tests, checkpoint hashes, full pytest, Ruff, format, strict mypy, model verification, dry plans, and secret/scope checks pass.

## Fresh physical reproduction matrix

After all offline gates pass, run each arm once, fresh and strictly serial, using the legacy reproduction profile and the corrected committed source:

| Case | Evaluation window | Arms |
|---|---:|---|
| SZ Air | 7 days | Basic RBC, C-DRL |
| MZ Hydro | 5 occupied days | Basic RBC, C-DRL, H-DRL |
| MZ Air | 7 days | Basic RBC, C-DRL, H-DRL |

The Basic RBC arms are physical/protocol references, not affected-policy claims. Each policy is fixed before the first new result. No checkpoint substitution, tuning, retry for KPI, resume, or lucky rerun is allowed. A poor KPI is a valid result. Initialization/advance failure, checkpoint or source identity mismatch, inference failure, secret hit, or evidence corruption is a hard stop.

Each real long run must have its own process/control/completion identity and native 10-minute completion heartbeat. Completion is verified before the next arm starts. No DeepSeek call, MPC work, training, paper/LaTeX/Figure change, history rewrite, or push is in scope.

## Reporting

The result report will separate:

- exact contract recovery (input/action equivalence),
- physical reproduction under the current frozen BOPTEST protocol,
- checkpoint provenance uncertainty (especially MZ Air C-DRL), and
- differences from old paper numbers caused by an explicitly identified protocol, model, or adapter identity.

New KPI results will not be used to select a different model.
