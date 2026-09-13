# Processed paper results

This directory contains processed, publication-facing tables for *Causality-Constrained
Hierarchical LLM Agents for Online Rule Adaptation in Building HVAC Control*. The files support
independent checking of reported values and regeneration of paper tables and figures without
exposing credentials, private service metadata, or raw model messages.

## Files

| File | Contents |
|---|---|
| `h3c_agent_run_metrics.csv` | One row for each of the 81 completed H3C trajectories: three cases, nine Agent configurations, and three repetitions. |
| `h3c_agent_group_summary.csv` | Mean, sample standard deviation, and constituent values for the 27 case--configuration groups. |
| `main_comparison_statistics.csv` | Case-level summary statistics for the basic RBC, enhanced RBC, hierarchical MPC, PPO, MAPPO, and H3C main comparison. |
| `reward_advantage_timeseries.csv` | Hourly and cumulative reward difference between the standard H3C configuration and the frozen enhanced RBC. |
| `program_disposition_hourly.csv` | Hourly counts and fractions of Policy Adapter outcomes used in the rule-adaptation timeline. |
| `program_update_records.csv` | Classified zone-hour Policy Adapter outcomes for the nine standard H3C trajectories. |
| `paper_agent_matrix.json` | The 27 resolved case--configuration plans for one paper repetition. Configuration JSON is hashed after canonical key ordering and serialization, so formatting and line endings do not change its identity. |
| `provenance.json` | Derivation notes, recorded input identities, and companion-repository publication status. |
| `manifest.json` | SHA-256, byte count, row count, and H3C source-history provenance. |

## Interpretation

The configuration labels are `STANDARD`, `B1_WM0`, `B2_WM2`, `B3_WM3`, `B4_CausalOff`,
`B5_MissingSolarZoneEdge`, `B6_EdgeTiming`, `B7_CoordOff`, and `B8_NoThinking`. See
[`docs/paper_reproduction.md`](../../docs/paper_reproduction.md) for the exact factor changed by
each label.

`reward` is the common trajectory reward reported in the paper. `zone_h` and `pmv_h` are additive
comfort metrics accumulated across zones. `tv_c` sums absolute consecutive changes in applied
zone setpoints, and `reversals` counts changes in the sign of nonzero consecutive setpoint
increments. `v_state_c` is the state-conditioned program-variation metric in degrees Celsius per
zone-hour. `r_int_fraction` is the union intervention rate for comfort recovery and setpoint-rate
limiting. Token, latency, retry, fallback, and API-cost fields follow the operational definitions
in the paper. `retried_logical_call_count` counts logical calls that needed at least one repeated
request; `additional_request_attempt_count` counts the repeated wire requests themselves.

The 81 rows record five source commits because later campaigns incorporated control-neutral
transport and runtime-state publication fixes. All five commits remain in the released Git
history. The manifest records their exact trajectory counts. Repeat labels identify independent
executions, whereas the deterministic run identity intentionally remains the same for repeated
executions of one configuration.

These are processed research outputs, not raw simulator trajectories or model-service records.
No row contains a BOPTEST test identifier, local evidence path, model message, endpoint, or
credential. The verifier checks file identities, resolves the 27 plans from the live planner,
recomputes group and main-comparison statistics, closes the operational accounting, and validates
the rule-update and reward time-series tables. Run it from the repository root:

```console
python tools/verify_paper_reference_results.py
```
