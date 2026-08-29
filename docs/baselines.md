# Independent RBC, DRL, and hierarchical MPC baselines

The baseline package shares H3C's case profiles, physical initialization, BOPTEST client,
occupancy, comfort, reward, execution lock, and metric owners. It does not import the online Agent
or causal-control chain.

## Registered protocol

`configs/baselines/formal.json` defines the 11-arm formal matrix. Every arm is fresh and strictly
serial:

1. select one BOPTEST test identity;
2. configure dynamic electricity price and a 900-second step;
3. initialize at the case evaluation start with a seven-day internal warm-up;
4. apply no explicit prefix controls;
5. evaluate for seven days in SZ_Air/MZ_Air or five days in MZ_Hydro;
6. stop the same test identity once.

SZ_Air and MZ_Hydro use raw occupancy. MZ_Air public control and KPI calculations use official
occupancy, `[06:00,19:00) AND raw > 0`; the frozen policy observation preserves its registered
raw-binary occupancy feature.

## Controllers

- **Basic RBC** applies 25 °C when the case's public occupancy is positive and 30 °C otherwise,
  together with declared static controls.
- **P0 / enhanced RBC** executes H3C's canonical cooling program through the shared program
  interpreter and action-assurance owner.
- **C-DRL** loads one deterministic PPO policy.
- **H-DRL** loads two MAPPO actors for MZ_Hydro or five for MZ_Air. The single-zone case has no
  H-DRL arm.
- **Hierarchical MPC** fits one shared four-lag, four-step vector-ARX structure per case from
  repeated, fully warmed episodes in the seven days before evaluation. An hourly building
  coordinator and 15-minute zone QPs use the common cost, comfort, and smoothness objective.
  Any deterministic P0 fallback is exposed as method degradation.

The two-rate coordinator/zone decomposition follows established building-control practice: an
upper layer uses global state to generate references while faster local controllers optimize
zone energy and comfort. The single permitted feedback reconciliation mirrors the one-iteration
inter-layer communication used to address information mismatch in recent hierarchical MPC. See
[Long et al., ACC 2016](https://people.kth.se/~kallej/papers/building_acc16long.pdf) and
[Hierarchical MPC for building energy management, Applied Energy 372 (2024),
123780](https://doi.org/10.1016/j.apenergy.2024.123780). H3C uses a deliberately transparent
data-driven vector-ARX/QP realization so the same equations and tuning contract apply to all
three cases.

## Frozen policy contract

`models/registry.json` is the checkpoint identity owner. Each load verifies the exact SHA-256 and
byte count before deterministic CPU inference. Per-policy adapters retain:

- observation and forecast column order;
- normalization bounds and floating-point arithmetic;
- history depth, offsets, and cold-start action;
- centralized or per-actor local feature order;
- residual action base and zone-to-actuator mapping;
- policy-only comfort and occupancy features used during training.

The MAPPO critic is not used during evaluation. Golden fixtures trace captured observation → raw
vector → normalized vector → actor input → raw action → setpoint → BOPTEST payload.

## Commands

```console
h3c-baseline models verify
h3c-baseline run --case MZ_Air --controller c-drl
h3c-baseline suite formal
h3c-baseline mpc train --case all --workers 4 --max-fit-episodes 64
h3c-baseline mpc verify-model --case MZ_Air
h3c-baseline suite mpc-formal
h3c-baseline verify outputs/baselines/runs/<suite>/<case>/<run_id>
h3c-baseline report outputs/baselines/runs/formal
```

Commands print a resolved plan by default. `--execute` enables BOPTEST. Reports use the common H3C
metric owner and generate Markdown, JSON, CSV, and cost/power/temperature/PMV/occupancy/setpoint
figures.

Each run preserves the exact raw and resolved forecast bundle in `forecast_inputs.json`; the
verifier independently reconstructs any documented missing-occupancy resolution before accepting
the physical trajectory.
