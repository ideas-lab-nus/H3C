# Executor-envelope matched Provider rerun preregistration

Status: frozen before either physical arm is selected or initialized.

## Question

After restoring the historical `{"patch":[{...}]}` Executor wire contract, do
Official DeepSeek and Baseten both complete the same real MZ Air 06:00--12:00
diagnostic with substantially fewer Executor schema rejections and healthy
physical/identity/evidence execution?

## Frozen method

Both arms use the exact same committed source, Prompt bundle, user context,
profile and controller:

- case/profile: `MZ_Air`;
- diagnostic window: registered `mz-air-06-12` (day 199, 06:00--12:00);
- internal warm-up: seven days;
- evaluation: six hours, 24 physical steps;
- expected model calls: O/E/R = 6/30/6, total 42;
- working memory: one completed interval;
- long-term experience: off;
- causal and coordinated Budget layers: on;
- Prompt: neutral C0 with the repaired exact Executor root envelope;
- thinking: `occupancy_routed`, routed calls use thinking enabled and
  `reasoning_effort=low` with no `temperature` or `top_p`;
- transport recovery: unchanged bounded runtime contract (at most two retries
  for registered transient statuses only).

The only experimental variable is Provider:

1. `deepseek-official` / `deepseek-v4-flash`;
2. `baseten-deepseek` / `deepseek-ai/DeepSeek-V4-Flash-0731`.

No eRBC arm is rerun because the existing zero-API arm under this physical
window is unaffected by the Prompt-only repair.

## Parallel execution ruling

The user explicitly changed this rerun from serial to parallel on 2026-09-01.
Both independent arms may be submitted immediately from separate worktrees,
output owners, PIDs, locks, run identities and fresh BOPTEST test identities.
Within each arm the frozen dependency order remains:

```text
Orchestrator -> five parallel Executors -> deterministic settlement
-> four physical steps -> Reflector
```

Provider latency and total wall-clock comparisons must disclose concurrent-load
confounding. Response contracts, physical KPIs and method behavior remain valid
matched-arm observations when identity and evidence gates pass.

## Gates and classification

Each arm must have one initialize, 24 ordered advances, one normal stop, one
fresh test identity, 42 logical calls, exact Provider/model identity, no secret
exposure and replayable program/action/KPI evidence. The verifier classification
is based on physical/identity/timeline/evidence fields rather than command exit
code alone.

Report separately:

- JSON, exact Executor envelope, schema, finish reason, fallback and retry;
- latency and normalized prompt/reasoning/completion usage by role;
- accepted/rejected operation distribution and rejection reasons;
- reward, cost, energy, zone-h, PMV-h, occupied peak PMV, TV and reversals;
- comparison with each other and the existing matched-window eRBC result.

Ordinary model-contract degradation, deterministic patch rejection or poor KPI
continues to completion and does not trigger a lucky rerun. A mechanical
environment, Provider wiring, failure-sentinel, BOPTEST initialize/advance,
identity, secret or evidence failure is preserved and diagnosed; only a
control-neutral repair may launch a fresh replacement. A change to Prompt,
controller, model settings, KPI or acceptance criteria requires user review.

## Boundaries

Do not resume or overwrite historical runs. Do not modify the control method,
paper, LaTeX or Figure 3. Do not push. After both arms are terminal and verified,
produce the matched report and stop for user review; do not start the seven-day
MZ Air experiments automatically.
