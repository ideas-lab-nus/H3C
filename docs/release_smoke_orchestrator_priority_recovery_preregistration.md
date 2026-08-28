# Orchestrator priority-contract recovery preregistration

Status: frozen on 2026-08-27 after the first paid release arm stopped and before
any implementation change or further model/BOPTEST call.

## Preserved failure

Source `c70a933562dde2bfcaa016a95da28587e379e24a` completed the physical
SZ_Air Agent trajectory in
`outputs/runs/release-6h/SZ_Air/20260827T074845610101Z-eb6952102fe6`.
It made exactly 18 DeepSeek calls: six each for Orchestrator, Executor, and
Reflector. The physical lifecycle was one initialize, 672 vanilla-conditioning
advances, 24 evaluation advances, and one stop. Retry, transport, fallback, and
secret-exposure counts were zero.

No completion was published because production verification rejected
`json_schema` and `coordination_surface`. At hours zero and one, Orchestrator
returned zero site cap, zero zone budget, and an empty priority list. The output
had the exact declared keys, but the budget contract requires priority to be a
permutation of all configured zones. Hours two through five returned a complete
priority and were accepted. This directory remains a real 18-call failed arm and
must never be reported as passing release smoke.

A subsequent MZ_Hydro arm was stopped immediately when the review arrived. Its
directory
`outputs/runs/release-6h/MZ_Hydro/20260827T075311895219Z-bd424bfed381`
has no completion, initialize, advance, or model call and remains preserved.

## Root cause and single change

The deterministic allocation validator is correct and matches the historical
budget semantics: priority must list every configured zone exactly once. The
stable canonical Orchestrator system Prompt says to choose a priority order but
its dynamic `ALLOCATION LIMITS` block supplied only numeric caps. It did not
state that the complete priority permutation remains mandatory when all
allowances are zero.

The only behavior change is for `Orchestrator.build_user` to add a structured
priority contract inside `ALLOCATION LIMITS`:

- required members are the configured zones;
- every configured zone appears exactly once;
- the rule applies when the site cap is zero.

The role builder owns this invariant so runtime callers cannot drift. The stable
system Prompt bytes, Agent roles, output fields, allocation validator,
BudgetLedger, budget charging, Executor allowance, causal surface, model request
parameters, physical protocol, and verifier remain unchanged. No output repair,
fallback, retry, default allocation, or case-name branch is introduced.

## Required gates and fresh execution

Before another real call:

1. the canonical system-Prompt byte/hash fixture must remain unchanged;
2. a production-path render test must prove the dynamic priority contract is
   present for a zero-allocation scenario and names every configured zone;
3. a reverse test must prove the validator still rejects an empty priority even
   when cap and budgets are zero;
4. fake physical Agent execution with zero allocation and complete priority must
   pass schema, coordination, budget, call-count, lifecycle, and full verifier
   gates;
5. all pytest, Ruff, strict mypy, public-identifier, secret, nested-repository,
   config, matrix, and whitespace gates must pass;
6. BOPTEST endpoint/container/image/source identities must again match the
   preserved old server.

Because tracked source identity changes, earlier baselines and the failed paid
arm remain superseded evidence. The final release sequence restarts fresh from
arm zero on one clean commit. The 18 failed calls remain part of actual spend;
the new source-consistent release plan still contains 372 calls. This is an
explicit wiring recovery, not a retry of the same method identity. Formal suite
execution remains prohibited.

The user has explicitly retained Python 3.13.2 and thermal-comfort package
3.9.8; only BOPTEST server identity is an environment-consistency gate.
