# Independent RBC, DRL and short-data MPC baselines

The baseline package is independent of H3C's Agent control chain. It reuses only physical case
profiles, the BOPTEST client/lifecycle, official occupancy and comfort owners, canonical enhanced
RBC, reward calculation, execution lock, and physical KPI calculation. It does not import an
Orchestrator, Executor, Reflector or causal admission path.

## Registered evaluation protocol

`configs/baselines/formal_drl.json` is the current suite owner. It registers eleven fresh RBC/DRL
evaluations and deliberately excludes MPC. Each evaluation uses:

```text
7-day BOPTEST server warm-up
→ same-test-id 7-day vanilla prefix (occupied 25 °C / otherwise 30 °C)
→ case-declared evaluation (Air: 7 days; MZ_Hydro: 5 occupied weekdays)
```

All physical arms are strictly serial and use a fresh test identity. Prefix observations never
enter formal KPI. Frozen policies reset their history at the evaluation boundary exactly as in
training. A poor result is still a valid result; initialization/advance, model identity, DRL
inference or evidence corruption is invalid.

## RBC definitions

- **basic RBC** applies 25 °C whenever official effective occupancy is positive and 30 °C
  otherwise, together with the case's declared static controls.
- **enhanced RBC** executes the same canonical cooling program, interpreter and deterministic
  action-assurance path used by the H3C physical configuration. There is no second handwritten
  copy of the rules.

## Frozen DRL inference

`models/registry.json` is the machine-readable identity owner and each checkpoint has a model
card. Training code is not shipped. The migration preserves, per checkpoint:

- global observation columns and forecast ordering;
- normalization bounds, including legacy bounds that look unusual;
- action-history depth and cold-start action;
- centralized or per-actor local observation order;
- residual action base and zone-to-actuator mapping;
- deterministic CPU inference.

The MAPPO central critic was used during training only. Online action generation loads actor
weights: two actors for MZ_Hydro and five for MZ_Air. The single-zone case has one centralized PPO
policy and deliberately has no invented H-DRL arm.

The golden fixture in `tests/fixtures/baseline_policy_inference_golden.json` traces captured
observation → raw vector → normalized vector → local actor vector → raw action → setpoint → full
BOPTEST payload. It also protects the two case-specific legacy MAPPO local orderings:

```text
MZ_Hydro: time → own temperature/PMV/action → shared power/weather/price → own occupancy
MZ_Air:   time → shared power/weather/price → own temperature/PMV/action → own occupancy
```

The MZ_Air policy zone order is `cor,nor,sou,eas,wes`; actuator payloads are mapped by zone name,
not by the case-profile display order.

### Source provenance

- SZ_Air PPO was selected from the archived `SZ_AIR/models_drl4` records by best training-log
  mean reward.
- MZ_Air PPO/MAPPO are the exact checkpoints used by the archived evaluation workflows; the PPO
  archive embeds 295,680 steps and does not retain an authoritative epoch-to-file map.
- MZ_Hydro PPO/MAPPO are the user-designated extended-training checkpoints from
  `Revision1/MZ_Hydronic_Final_PPO_MAPPO_1h_Epoch700_20260822`.

Evaluation results were not used for checkpoint selection. The Hydro extended run did not meet
all of its historical preregistered convergence criteria, so its model cards state that caveat.

## Common vector ARX model

All cases use the same model family:

\[
y_{k+1}=c+\sum_{j=0}^{3}A_jy_{k-j}+\sum_{j=0}^{3}B_ju_{k-j}+Ed_k.
\]

The output vector is zone temperatures plus total site power; controls are zone cooling
setpoints; disturbances are outdoor temperature, solar irradiance, per-zone effective occupancy,
and daily sine/cosine time encoding. Training-only scaling is fitted from the identification
trajectory. The final chronological day is validation. A shared ridge grid
`[1e-6, 1e-4, 1e-2, 1, 100]` minimizes mean standardized output RMSE, breaking exact ties toward
the larger penalty, then refits the selected model on all identification data.

Identification is a separate fresh eRBC trajectory immediately before the case's evaluation
window: seven days for SZ_Air/MZ_Air and five days for MZ_Hydro. The evaluation boundary and every
evaluation arm remain physically independent; no evaluation row can enter fitting or selection.

## Receding-horizon optimizer

Every 15 minutes, SLSQP optimizes four future 15-minute setpoints per zone with bounds
`[20,30] °C`, a deterministic enhanced-RBC warm start, and the current H3C reward components:

```text
energy/cost + occupied PMV exceedance + setpoint smoothness
```

Only the first action is applied. Negative predicted power is clamped to zero and counted.
Optimization failure deterministically applies enhanced RBC for that step and marks the entire
arm `METHOD-DEGRADED`; it is never reported as a pure MPC success.

This baseline intentionally uses short, low-excitation eRBC data. It is suitable for a fair,
transparent reviewer comparison but should not be interpreted as a fully tuned predictive
controller. The limitation is preserved even if the physical result is favorable.

## Commands and output

```console
h3c-baseline models verify
h3c-baseline run --case MZ_Air --controller c-drl
h3c-baseline suite formal-drl
h3c-baseline verify outputs/baselines/runs/<suite>/<case>/<run_id>
h3c-baseline report outputs/baselines/runs/formal-drl
```

Dry plans do not connect to BOPTEST. Add `--execute` only after reviewing the resolved plan.
The current suite runs eleven RBC/DRL evaluations in registered order. Output schemas and metrics
are summarized in [`outputs/README.md`](../outputs/README.md). The optional MPC implementation is
not part of this benchmark.

The superseded first complete 7+7+7 baseline execution is summarized in
[`baseline_formal_7d_result_20260828.md`](baseline_formal_7d_result_20260828.md). The tracked note
binds the result to its production source while the generated trajectories and figures remain
under ignored `outputs/baselines/` directories.

The corrected per-policy adapter and current 7/5/7 RBC/DRL benchmark are frozen in
[`drl_adapter_contract_repair_preregistration.md`](drl_adapter_contract_repair_preregistration.md).
Its completed 11-arm result, checkpoint identities, occupancy interpretation and time-series
findings are recorded in
[`drl_adapter_contract_repair_result.md`](drl_adapter_contract_repair_result.md).
