# Hydro reward-feedback and three-case verification preregistration

Date: 2026-09-01

## Decision provenance

The user made this design decision after reviewing the complete working-memory-only
three-case campaign. The adverse source trajectories and their original terminal
artifacts remain unchanged. This document does not rewrite that post-result decision
as an earlier criterion.

## Research question

Can the existing, case-generic H3C method improve MZ Hydro reward without adding a
new control rule by exposing the frozen objective value and its exact completed-step
penalty decomposition in the existing one-hour working memory?

The original role objective remains unchanged:

> Maintain comfort while reducing energy cost as much as possible.

The only added role guidance is:

> The reward from a completed interval is a quantitative reference for the same
> frozen trade-off among energy cost, comfort, and action smoothness; a higher
> cumulative reward indicates a better overall result.

Reward is feedback about completed physical outcomes. It is not a new independent
goal, an action-admission condition, a Safety rule, a target trajectory, or a
baseline comparison shown to the model.

## Unique method change

The previous completed control interval in working memory gains four exact
step-reward rows and their deterministic decomposition:

- site step reward;
- site energy penalty;
- site comfort penalty;
- site smoothness penalty;
- for an Executor only, that zone's comfort- and smoothness-penalty contributions.

The interval reward is the exact sum of the four completed step rewards. The same
site facts are rendered once for the Orchestrator, once in each zone-specific
Executor request, and once for the Reflector because provider calls are stateless.
No future, counterfactual, eRBC, or target-threshold reward is exposed.

The reward formula, weights, scales, P0, `pmv_step_c=0.3`, interpreter, action
mapping, case profiles, C0 Prompt structure, `occupancy_routed` low thinking,
ProgramCheck, CausalProof, Budget, and the frozen ordered action-assurance chain
remain unchanged.

## Runtime constraint boundary

The runtime control surface remains limited to:

1. the existing wire/output and executable-DSL format;
2. ProgramCheck (historical C0/C6);
3. the existing confirmed-edge, direction-compatibility and whole-program
   direction CausalProof checks;
4. the existing shared Budget settlement;
5. the existing comfort-recovery, setpoint-rate and actuator-bound
   action-assurance chain in its frozen order;
6. the unchanged P0 program, interpreter, and action mapping.

Graph discovery/confirmation remains an offline concern; the previously retired
checks remain retired and the optional extra guard remains off. The implementation
must not add reward thresholds, reward vetoes,
cooldowns, minimum holds, reversal bans, delayed-edge control laws, a new PMV
recovery rule, case-specific Prompt/code/config branches, or verifier-to-runtime
feedback. The constraint inventory is an offline audit artifact only.

## Thinking-length behavior

The Provider does not expose a contract that stops private reasoning at a threshold
and then reserves generation for final JSON. `finish_reason=length` with empty or
invalid content remains model-contract degradation:

- Orchestrator uses the existing validated allocation fallback;
- Executor applies deterministic `no_change`;
- Reflector omits the Lesson;
- physical execution continues when identity, timeline, evidence, and transport are
  otherwise healthy;
- length exhaustion is not retried.

The method does not switch to no-thinking, a second model, or a two-stage call.

## Pre-run gates

Before any new physical arm:

1. prove the old `step_reward()` and new breakdown owner return exactly the same
   reward on frozen fixtures and historical complete trajectories;
2. prove reward appears only after its physical outcome and only in the next
   completed-interval working-memory surface;
3. prove four action/outcome times and four reward rows align through midnight;
4. exercise 120- and 168-hour fake trajectories including all midnights;
5. exercise float-Budget tolerance, dynamic site cap, invalid/missing causal IDs,
   deterministic causal-edge augmentation, `length` plus empty content, missing
   Reflector Lesson, and registered transient retries;
6. prove every runtime veto maps to the frozen constraint inventory;
7. zero-call recertify the three preserved terminal working-memory-only runs while
   preserving their original `failure.json` files;
8. pass targeted tests, full pytest, Ruff, format check, strict mypy, documentation
   freshness, staged-manifest review, and staged secret scan.

## Six Baseten non-physical checks

After the offline gates, issue exactly six non-physical calls using the frozen
historical MZ Hydro hour 34, 79, and 106 inputs for NZ and SZ. These calls use the
production Baseten Provider, strict structured-output contract, C0
`occupancy_routed` low thinking, and the same output schema. They do not initialize
or advance BOPTEST and are not retried for length or ordinary model-contract
failure.

The checks establish only that reward feedback is visible and the existing output
contract remains usable. Outputs are not selected because they look favorable and
do not relax ProgramCheck, CausalProof, Budget, or Safety.

## MZ Hydro formal arm

- case: `MZ_Hydro`;
- Provider/model: Baseten / `deepseek-ai/DeepSeek-V4-Flash-0731`;
- thinking: C0 `occupancy_routed` low;
- one-hour working memory;
- long-term memory off;
- seven-day internal warm-up;
- 120-hour formal evaluation;
- fresh run and BOPTEST test identities;
- one method attempt.

Identical-payload retries are limited to registered transient transport errors,
at most two retries (three total requests). An eligible infrastructure failure may
use the already implemented fresh-run/fresh-test physical replay procedure. Poor
KPI, causal/program/Budget rejection, ordinary schema degradation, fallback, or
length exhaustion does not authorize a lucky rerun.

The arm runs to its terminal physical boundary. A 30-minute heartbeat reports
atomic-prefix KPI against the prior H3C and frozen eRBC evidence.

### Registered Hydro pass

All must hold:

- reward `> -179.35418363224142`;
- occupied peak absolute PMV `<= 0.70`;
- physical execution, source/run/test identity, timeline, secret isolation, and
  evidence integrity are healthy.

TV, reversals, program modifications, and the 07:00--10:00 energy shift are
mechanism diagnostics, not additional control or release gates.

If Hydro fails the registered pass, stop for analysis. Do not add another Prompt,
parameter, rule, or method rerun automatically.

## Conditional three-case confirmation

Only if Hydro passes, freeze the same generic source commit and run one fresh
SZ Air arm and one fresh MZ Air arm in parallel. No case-specific method change is
allowed.

- SZ Air: reward `> -640.504177761107`, occupied peak absolute PMV `<= 0.70`;
- MZ Air: reward `> -559.1299559533957`, occupied peak absolute PMV `<= 0.70`.

Only one preregistered fresh trajectory per case is used. The final engineering
classification is `THREE-CASE-REWARD-PMV-PASS` only if the same method version
passes all three cases. This is an empirical single-run criterion, not a guarantee
over stochastic model outputs.

## Terminal classification

The verifier reports orthogonal statuses:

```text
trajectory_status: EXECUTION-HEALTHY | EXECUTION-INVALID
model_contract_status: CLEAN | DEGRADED
performance_status: REWARD-PMV-PASS | METHOD-DEGRADED
```

Ordinary JSON/schema/semantic/finish/usage/fallback degradation does not by itself
invalidate an otherwise complete and replayable physical trajectory.

## Prohibited scope

No paper, LaTeX, Figure 3, MPC, long-term-memory experiment, baseline rerun, push,
case-specific tuning, or historical evidence mutation is authorized by this
preregistration.
