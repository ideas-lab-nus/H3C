# Baseten compatibility and MZ Air 06:00–12:00 preregistration

Date: 2026-08-31
Frozen parent source: `b6aaad2b30019e4c73253605f8f37d55f0e74f18`

## Research questions

1. Can the same frozen H3C request and Prompt contract run against the official DeepSeek endpoint and Baseten's hosted `deepseek-ai/DeepSeek-V4-Flash-0731` endpoint?
2. Does the finalized context protocol remain structurally and behaviorally healthy in a real MZ Air occupied-start diagnostic window?
3. Under a strictly serial, fresh-test protocol, how do the two providers differ in observed latency, token accounting, estimated cost, model-contract health, and physical outcomes?

This is a six-hour diagnostic, not a formal seven-day method result. Starting at 06:00 after BOPTEST's internal warm-up is not equivalent to inheriting Agent decisions made from 00:00 to 06:00.

## Frozen method and window

- case: `MZ_Air`;
- diagnostic window: `mz-air-06-12`, day 199 06:00–12:00;
- duration: six hours / 24 physical steps;
- seven-day BOPTEST internal warm-up, no explicit controlled prefix;
- one-hour working memory, long-term experience disabled;
- C0 context, `occupancy_routed` low thinking;
- causal graph, coordination, canonical P0 program, Budget, Safety, action assurance, reward, and metrics unchanged;
- five zone Executor calls remain concurrent inside each H3C hour.

Each H3C arm must produce exactly 6 Orchestrator, 30 Executor, and 6 Reflector logical calls. Provider selection may change only the endpoint, model identifier, API-key owner, provider-specific transient status set, and Baseten session-affinity header. System/user Prompts and the remaining request contract must be byte-identical for matching logical inputs.

## Provider contracts

Official DeepSeek uses the configured official endpoint, model `deepseek-v4-flash`, and `H3C_MODEL_API_KEY`. Baseten uses `https://inference.baseten.co/v1`, model `deepseek-ai/DeepSeek-V4-Flash-0731`, and `BASETEN_API_KEY`. Both send JSON mode, thinking enabled, `reasoning_effort=low`, and omit `temperature` and `top_p` for routed-low calls. Baseten uses one run-specific `x-session-affinity` value and additionally treats HTTP 529 as a bounded transient response. No unbounded retry is permitted.

## Preflight and hard stops

Before physical execution, one frozen production-rendered Agent input is sent once to Baseten. The preflight must confirm a nonempty JSON object response, exact response-model identity, parseable usage, a secret-free evidence record, and the frozen request fields. It is not retried.

Common source, timeline, initialization/advance, identity, secret, or evidence corruption stops all unstarted arms. A credential, API, or response-contract failure confined to one provider stops only that provider arm; the remaining registered arms may continue. Ordinary Agent schema rejection, deterministic patch rejection, fallback, or poor KPI is adverse method evidence but does not by itself invalidate an otherwise auditable physical trajectory.

## Strict serial order

1. official DeepSeek H3C;
2. after completion, stop, PID exit, lock removal, and verification: Baseten H3C;
3. after the same barrier: zero-API canonical P0/eRBC.

Every arm receives a fresh BOPTEST test identity and one attempt. There is no resume or lucky rerun. No PID, physical test, or model call may overlap between arms.

## Frozen analysis

For each H3C provider, report 06:00–09:00 and 06:00–12:00 schema/finish/fallback/retry status; HTTP 429/503/529; per-role and total p50/p95 latency; Executor-batch, simulated-hour, and wall-clock duration; prompt, reasoning, completion, cache-hit, and total tokens; completion tokens per second; and estimated cost using the price applicable at analysis time. UTC service intervals are reported because serial execution leaves provider load and price-time confounding.

For both H3C arms and fresh eRBC, report reward, cost, energy, zone-hours, PMV-hours, occupied peak absolute PMV, total variation, and reversals. Audit allocation, patch/no-change, validation disposition, Lesson-to-next-working-memory propagation, program/action propagation, fallback, and model-format degradation. A historical 06:00–12:00 slice may be contextual only and is not a matched arm.

Final labels are `PROVIDER-COMPATIBLE` or `PROVIDER-INCOMPATIBLE`, `FASTER` or `NOT-FASTER`, `LOWER-COST` or `NOT-LOWER-COST`, and `CONTEXT-BEHAVIOR-HEALTHY` or `METHOD-DEGRADED`. After the three-arm report, stop for user review. Do not launch the seven-day MZ Air arms, push, or modify the paper.
