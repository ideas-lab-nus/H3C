# DRL policy-comfort input repair preregistration

Date: 2026-08-29  
Status: preregistered before policy-comfort implementation or new physical result  
Parent repair: `docs/drl_time_feature_contract_repair_preregistration.md`

## Discovery

After the time-feature repair was preregistered, read-only review of the copied training-machine owners found a second independent adapter difference. The original SZ Air, MZ Hydro, and MZ Air DRL environments update their policy-side clothing state once per 96 control steps from 96 consecutive 15-minute outdoor-temperature forecast samples. They then compute the post-action PMV stored in the next policy observation with that clothing state.

The H3C baseline runner currently computes the shared evaluation comfort state from 25 hourly samples (`step:step+97:4`) and passes that PMV into the DRL observation history. The shared calculation is the current cross-controller KPI owner and must not be changed merely to reproduce a frozen policy input.

## Single implementation variable

For DRL arms only, create a separate policy-input `ComfortModel` state:

- initialize it from the same frozen comfort configuration;
- at each new evaluation day, update clothing from exactly 96 consecutive 15-minute outdoor-temperature samples starting at the current action time;
- compute post-action policy PMV from the next zone temperature;
- pass only this policy PMV to `PolicyObservationBuilder.update`;
- continue using the existing shared comfort state and PMV for public reward, actions logs, performance, KPI, reporting, RBC, MPC, and H3C comparisons.

No Prompt, checkpoint, action, action mapping, public reward, KPI, BOPTEST profile, static control, forecast value, or shared comfort calculation may change. The policy-only PMV and clothing state must be explicitly logged so the separation is auditable.

## Offline gates

1. A unit test proves the policy daily mean uses exactly 96 consecutive values, while the public owner remains the existing 25 hourly values.
2. A two-day fake-runtime test proves the policy clothing update occurs at the first step of each day and policy PMV, rather than public PMV, reaches observation history.
3. Non-DRL controllers do not construct or use the policy comfort state.
4. Existing public reward and KPI fixtures remain byte-for-byte or field-for-field unchanged.
5. Full baseline/H3C tests, Ruff, format, strict mypy, model identity, dry plan, secret, and scope gates pass before the fresh reproduction matrix begins.

The physical matrix and hard-stop rules remain those in the parent preregistration. This addendum does not authorize model selection from new KPI results.
