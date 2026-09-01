# H3C Completed-Interval Reward Feedback Contract

## Purpose and boundary

The unchanged control objective is:

> Maintain comfort while reducing energy cost as much as possible.

The completed-interval reward is a quantitative reference for that same frozen
trade-off. It is an observed outcome, not a new objective, control command,
admission rule, safety rule or baseline target. No eRBC value, future reward or
counterfactual reward is exposed.

## Exact owner

`h3c.runtime.comfort.step_reward_breakdown` is the single owner. It preserves
the exact legacy operation order for the scalar reward:

```text
energy_penalty = energy_weight * energy_scale * site_cost / zone_count
comfort_penalty = comfort_weight * comfort_scale * sum(zone_comfort) / zone_count
smoothness_penalty = smoothness_weight * smoothness_scale * sum(zone_smoothness) / zone_count
reward = -(energy_penalty + comfort_penalty + smoothness_penalty)
```

`step_reward()` delegates to this owner and returns the same IEEE-754 value as
before. Per-zone comfort and smoothness contributions are explanatory terms;
the shared site energy term is never attributed to a zone.

## Time alignment

Only after an action outcome is physically observed does the runtime attach:

- site step reward;
- site energy, comfort and smoothness penalties;
- local-zone comfort and smoothness contributions.

Four completed steps are aggregated into the next decision's one-hour working
memory. Action and outcome clocks remain explicit and separated by 15 minutes.
The interval reward equals the sum of the four displayed site step rewards.
The current or future interval never receives a reward value.

## Role views

- Orchestrator: one site-level four-row objective-feedback table.
- Executor: the same site table plus only its own zone contributions.
- Reflector: the site table and all zone contributions for the completed interval.

The feedback does not change the output schema or any runtime validator.
