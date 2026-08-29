# Unified evaluation protocol preregistration

Date: 2026-08-29  
Status: approved before implementation and physical execution

## Question

Can the deterministic and frozen-policy baselines, and future H3C runs, use one
evaluation boundary while preserving each controller's established input contract?

## Registered protocol

Each arm uses a fresh BOPTEST test identity, a 900-second control step and dynamic
electricity pricing. BOPTEST is initialized directly at the evaluation start and
receives a seven-day internal warm-up. There is no explicit controlled prefix.

| Case | Evaluation start | Evaluation duration |
|---|---:|---:|
| SZ_Air | day 203 | 168 h |
| MZ_Hydro | day 220 | 120 h |
| MZ_Air | day 199 | 168 h |

SZ_Air and MZ_Hydro use raw positive occupancy. MZ_Air control and public KPI
accounting use the documented half-open HVAC window `[06:00,19:00)` combined with
positive raw occupancy. Frozen MZ_Air DRL policies continue to receive their
training-time raw-binary occupancy input.

The canonical H3C program plus the action-assurance chain is the registered P0/eRBC.
All methods use the current shared reward and KPI owner. Archived evaluator rewards
may be reported only as non-comparable audit values.

## Registered physical runs

1. One MZ_Air Basic RBC diagnostic with raw occupancy.
2. One fresh eleven-arm formal suite from a single committed source:
   - SZ_Air: Basic RBC, P0/eRBC, C-DRL;
   - MZ_Hydro: Basic RBC, P0/eRBC, C-DRL, H-DRL;
   - MZ_Air: Basic RBC, P0/eRBC, C-DRL, H-DRL.

The MZ_Air formal Basic RBC arm is the official-occupancy member of the occupancy
comparison. Runs are strictly serial, one attempt per arm, with no DeepSeek call,
resume or lucky rerun.

## Frozen method boundaries

Checkpoint identities, policy observation order, history offsets, normalization,
clothing/PMV input, residual action mapping, static controls and case evaluation
windows remain unchanged. The protocol change must not alter Prompt or Agent logic.

## Acceptance

- one initialize, seven-day internal warm-up, zero explicit conditioning advances,
  the registered evaluation count and one stop;
- common source, testcase, scenario, model and controller identities;
- recomputed public metrics and readable physical/action evidence;
- deterministic P0 actions come from the same production owner in H3C and baselines;
- prior Basic/DRL cost and energy reproduce within 0.1%, except where the registered
  MZ_Air official-occupancy control surface changes the action;
- DRL setpoint differences against an applicable archived trajectory remain within
  0.01 degrees C.

Initialization/advance failure, identity mismatch, secret exposure or corrupt
evidence is a hard stop. Poor KPI is recorded, not retried.

## Delivery and publication stop

The result table, time-series figures, verification status and local commits are
shown to the user before publication. No push is permitted until the user explicitly
approves those results and commits.
