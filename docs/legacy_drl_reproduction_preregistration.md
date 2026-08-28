# Legacy RBC/DRL reproduction preregistration

Date: 2026-08-28

## Question

Determine whether differences between the archived RBC/DRL results and the current
conditioned-prefix benchmark come from checkpoint inference or from the physical initialization,
fixed-control, occupancy and reward protocol.

## Frozen matrix

The independent `legacy-replay` suite runs once, strictly serially, with no DeepSeek calls:

- SZ_Air: basic RBC and C-DRL for seven days;
- MZ_Hydro: basic RBC, C-DRL and H-DRL for five days;
- MZ_Air: basic RBC, C-DRL and H-DRL for seven days.

Each arm selects a fresh BOPTEST test, initializes directly at the archived evaluation start with
the testcase's seven-day internal warm-up, resets policy history at that boundary, and performs no
explicit vanilla-RBC prefix. Evaluation fixed controls and frozen policy checkpoints remain the
ones already captured from the archived workflows. Occupancy uses the archived raw-count contract;
MZ_Air also restores archived `smoothness_scale=0.193466`. All other KPI calculations use the
current shared metric owners.

## Interpretation

The primary comparison is trajectory and metric agreement with the archived evaluation files,
especially the first physical boundary state, setpoints, power, cost and reward. Agreement supports
protocol drift as the cause. Persistent disagreement with matched boundary and inputs points to a
remaining inference, checkpoint or BOPTEST-version difference. These replay arms do not replace the
current common-prefix benchmark and are not a new cross-controller fairness claim.

Initialization/advance, checkpoint identity or evidence failure stops the sequence. Poor KPI is a
result, not a rerun trigger. No arm is resumed or retried, and existing results remain immutable.
