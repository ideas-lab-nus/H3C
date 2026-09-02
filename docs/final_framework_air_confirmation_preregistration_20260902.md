# Final-framework Air-case confirmation preregistration (2026-09-02)

## Decision and research question

After the final framework produced an execution-healthy MZ Hydro result that beat frozen eRBC
reward while satisfying the occupied peak PMV boundary, the user authorized one SZ Air arm and one
MZ Air arm to run in parallel. The question is whether the same generic framework satisfies the
registered reward and engineering-comfort criteria in the two Air cases.

## Frozen method

The method is the code at `8b82bb967f583b64d1a885eb632659efe4485660`; any later launch commit may
contain only this release note, result documentation, and this preregistration. The launch manifest
must record the exact clean source commit. Both arms use:

- provider `baseten-deepseek`;
- model `deepseek-ai/DeepSeek-V4-Flash-0731`;
- provider-native strict JSON schema;
- `occupancy_routed` low thinking;
- one-hour working memory;
- long-term memory off;
- causal, coordination, Budget, program validation, and action assurance on;
- seven-day internal BOPTEST warm-up and zero explicit control prefix;
- the case owner's frozen formal evaluation boundary and occupancy definition.

No Prompt, controller, reward, Safety, causal rule, Budget, program operation, parameter bound,
model setting, or acceptance criterion may differ by case. No long-term-memory experiment is part of
this confirmation.

## Arms and criteria

| Arm | Formal window | Expected advances | Expected logical calls | Reward criterion | Peak criterion |
|---|---:|---:|---:|---:|---:|
| SZ Air | 168 h | 672 | 504 | reward `> -640.504177761107` | occupied peak `|PMV| <= 0.70` |
| MZ Air | 168 h | 672 | 1176 | reward `> -559.1299559533957` | occupied peak `|PMV| <= 0.70` |

Each arm uses an independent worktree, output owner, execution lock, Provider session affinity,
fresh BOPTEST test identity, and fresh run directory. The two arms may run in parallel; physical
steps remain strictly ordered within each test. Zone Executors retain their existing within-hour
parallelism.

## Failure and recovery

Registered transient HTTP 429/500/502/503/504/529 and connection/read-timeout failures may retry
the identical payload at most twice, for three requests total. An eligible control-neutral terminal
failure may use a fresh run/test physical replay of the complete atomic-hour prefix. The failed
directory and test remain immutable, completed Agent calls are not resent, and replay integrity
must pass before new decisions. Poor KPI, semantic/model-contract degradation, or ordinary
deterministic rejection never triggers a rerun.

Any repair that changes the Prompt, control method, model setting, reward, KPI, or acceptance
criteria requires user review before another physical call.

## Monitoring and reporting

Each arm is assigned to its own Codex task, not the launch task. That task must create and own its
native 20-minute heartbeat, verify liveness from atomic artifacts, report same-prefix KPI against
frozen eRBC, handle only eligible mechanical recovery, and publish the terminal verification and
generated result package under `outputs/reports/final-framework-20260902/<CASE>/`.

The launch task records exact source, PID, lock, run identity, test identity, and task identity, then
stops monitoring. No paper, LaTeX, Figure 3, long-term-memory, MPC, or unrelated source change is
authorized.
