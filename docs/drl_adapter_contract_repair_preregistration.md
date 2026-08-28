# DRL inference-contract repair and mixed-duration formal benchmark

Status: frozen before any new BOPTEST evaluation on 2026-08-28.

## Why the earlier DRL results are not accepted

The first clean-repository baseline execution was physically complete, but its shared observation
adapter incorrectly forced different archived policies into one history and local-observation
layout. The resulting DRL trajectories are retained as adverse migration evidence and are not used
as performance evidence. The RBC trajectories remain valid for their recorded seven-day protocol,
but are not a one-variable reproduction of the old notebook runs because the clean repository uses
an explicit seven-day same-test-id vanilla prefix before evaluation.

The confirmed adapter differences are:

- SZ_Air and MZ_Hydro past slots exclude the current/newly observed sample;
- MZ_Air past slots include the latest sample;
- MZ_Air policy occupancy is the raw forecast converted to a binary mask, not the later official
  HVAC-window effective occupancy used for physical KPI and RBC decisions;
- MZ_Hydro MAPPO orders own-zone features before shared features, while MZ_Air MAPPO orders shared
  features before own-zone features;
- the archived MZ_Air centralized evaluation loaded the checkpoint with SHA-256
  `368a19d8852203534aac2e416ba368853c9f47d4a6d40c527c0d0140a3ede477`, not the later checkpoint
  used in the rejected migration run.

## User decisions

1. SZ_Air and MZ_Air use their exact archived evaluation checkpoints. MZ_Hydro keeps the newly
   trained, user-designated PPO and MAPPO checkpoints.
2. SZ_Air and MZ_Air evaluate seven days; MZ_Hydro evaluates the five occupied weekdays only.
3. MPC is outside this benchmark and is neither identified nor evaluated.

These decisions supersede the seven-day Hydro comparison for future baseline evidence without
rewriting that historical run or its report.

## Registered implementation repair

The registry explicitly owns, per model, temperature/action/power history offsets, missing-history
behavior, policy occupancy encoding, and MAPPO local layout. No case-name branch is added to the
observation builder. Checkpoint SHA-256 and byte count are verified before load. Tests compare three
successive history windows against independently transcribed archived owners and freeze the complete
observation-to-action-to-BOPTEST path.

No reward weight, normalization bound, action scale, residual base, BOPTEST mapping, official
physical occupancy, static control, comfort calculation, or KPI owner changes.

## Fresh formal benchmark

The registered suite is `formal-drl`:

- SZ_Air: basic RBC, enhanced RBC, C-DRL; 168 evaluation hours;
- MZ_Hydro: basic RBC, enhanced RBC, C-DRL, H-DRL; 120 evaluation hours;
- MZ_Air: basic RBC, enhanced RBC, C-DRL, H-DRL; 168 evaluation hours.

Every arm is fresh and strictly serial:

```text
7-day BOPTEST server warm-up
→ same-test-id 7-day vanilla RBC prefix
→ case-declared evaluation
```

Each arm runs once. Initialization/advance, checkpoint identity, inference dimension, artifact or
secret failure is a hard stop. Poor reward, comfort or energy performance remains valid evidence.
The suite makes no DeepSeek call and does not run MPC.

## Interpretation of MZ_Air occupancy and cost

Changing only an occupied step to unoccupied raises the basic-RBC cooling setpoint from 25 °C to
30 °C and should weakly reduce cooling cost at that step. The observed increase from an old notebook
RBC result to the clean-repository RBC result therefore cannot be attributed to reduced occupancy.
Those runs also differ in the explicit seven-day prefix, physical boundary state and complete
trajectory; they are not an occupancy-only experiment. A causal occupancy effect would require a
paired run with every other identity fixed. The formal benchmark instead keeps one physical
occupancy/KPI owner while giving each frozen MZ_Air policy the raw-binary occupancy representation it
was trained to consume.

## Gates before execution

- all five checkpoints verify and load on CPU;
- three-step old-owner history tests, occupancy tests, both MAPPO layouts and golden inference pass;
- the dry suite resolves exactly 11 evaluation arms with durations 7/5/7 and no MPC identification;
- fake BOPTEST lifecycle, metrics, verifier, secret and artifact tests pass;
- full pytest, Ruff check/format and strict mypy pass;
- the implementation and this preregistration are committed before the first physical arm.
