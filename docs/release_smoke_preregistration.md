# Release-smoke preregistration

Status: frozen before any release-smoke API or physical-service call on
2026-08-27.

Post-freeze protocol correction: the user restored MZ_Hydro formal evaluation
to five days while SZ_Air and MZ_Air remain seven days. The release evaluation,
matrix, and 372-call budget remain six-hour and unchanged. The source-consistent
release sequence restarts under
`formal_hydronic_five_day_protocol_preregistration.md`; earlier run directories
remain preserved as superseded evidence.

## Question and scope

This release smoke asks whether the clean H3C repository can execute every
registered production surface through the real model and physical-service paths
while preserving its frozen identity, physical protocol, evidence contract, and
fail-closed verification. It is an integration release gate, not a formal
performance experiment and not evidence for a general KPI claim.

The implementation under test is commit
`c13ce856512e11be629810ac1431ed0805884b22`, including the profile-specific
graph-timing ruling in `f118f8f278ab31607a64728b41a5d55fd559a0d8`. The source
commit recorded in every run manifest must be the later clean commit containing
this preregistration and current-state update. No tracked method, Prompt, config,
runtime, or verifier file may change between that commit and the final smoke arm.

The formal suite is outside scope and must not be started.

## Frozen matrix and call budget

Execute the following arms once, fresh, and in ascending index order. The CLI
selection is `h3c smoke release-6h --arm-index INDEX --execute`.

| Index | Profile | Controller or unique factor | Expected model calls |
|---:|---|---|---:|
| 0 | SZ_Air | deterministic baseline | 0 |
| 1 | MZ_Hydro | deterministic baseline | 0 |
| 2 | MZ_Air | deterministic baseline | 0 |
| 3 | SZ_Air | H3C Agent, one-hour working memory | 18 |
| 4 | MZ_Hydro | H3C Agent, one-hour working memory | 24 |
| 5 | MZ_Air | H3C Agent, one-hour working memory | 42 |
| 6 | MZ_Air | two-hour working memory | 42 |
| 7 | MZ_Air | three-hour working memory | 42 |
| 8 | MZ_Air | causal layer disabled with zero causal surface | 42 |
| 9 | MZ_Air | confirmed solar-to-zone edge removed | 42 |
| 10 | MZ_Air | solar-to-zone timing changed Immediate to Delayed | 42 |
| 11 | MZ_Air | independent zone coordination | 36 |
| 12 | MZ_Air | thinking disabled for all roles | 42 |

The frozen total is three zero-model baselines, ten Agent arms, and 372 model
calls. MZ_Air one-hour memory is the same identity as its main H3C Agent arm and
is not duplicated. There are no retries, replacement calls, resumed workspaces,
or lucky reruns.

## Frozen physical and request protocol

Every arm selects a fresh test and uses one continuous test identifier:

1. Request seven days of server warm-up at initialization.
2. Advance seven explicit days of vanilla control on that same test identifier,
   using a 25°C cooling setpoint when occupied and 30°C when unoccupied.
3. Carry only the physical boundary state into evaluation. Start Agent state at
   program version zero with an empty accepted ledger and empty working memory.
4. Evaluate six hours at 15-minute control steps. Only these 24 steps contribute
   to performance metrics.
5. Stop the same test exactly once.

The model is `deepseek-v4-flash` with JSON-object response format. Routed
thinking calls send enabled thinking and low reasoning effort without sampling
parameters. Disabled-thinking calls send temperature zero and top-p one. All
requests are stateless. Transport and model retry counts are both zero.

## Serial supervision and evidence

Before arm zero, the worktree must be clean and all offline gates below must be
green. For each arm:

1. Record its index, profile, method identity, exact command, process identifier,
   target testcase, control mode, and exact new `completion.json` path.
2. Create a dedicated native ten-minute heartbeat for that exact completion
   path. The heartbeat reads no partial run logs and stays silent while the file
   is absent.
3. Do not start another API or physical arm while the current process or
   heartbeat is active.
4. When completion appears, read it once, stop the heartbeat, run `h3c verify`
   on the completed run, record the result, and only then continue.
5. If the process exits without completion, inspect the completed failure
   artifacts once, classify the stop rule below, and never reuse that directory.

Each run must contain the exact artifact set registered in the repository, with
`completion.json` written atomically last. Reports are written only to
`outputs/reports` after arm execution.

## Acceptance gates

Before execution, require pytest, Ruff, strict mypy, configuration loading,
Prompt and behavior golden fixtures, fake physical-service integration,
repository identifier scan, secret-value scan, nested-repository scan, and Git
whitespace check to pass. The complete formal matrix must still resolve to three
baseline and 24 unique Agent identities, and all six formal graph-sensitivity
arms must derive a declared single difference.

For every completed real arm, the production verifier must pass all applicable
checks:

- exact physical lifecycle and evaluation counts;
- exact model-call and raw-input/output log counts;
- request and response model identity, provider usage, and non-truncated finish;
- JSON-object and role-output schemas;
- deterministic proposal settlement through the applicable ordered validation
  chain;
- hourly thinking route;
- full accepted-ledger replay, current program version, and program hash;
- mandatory action-assurance order on every zone step;
- coordinated allocation and energy-budget accounting, or complete omission for
  independent coordination;
- resolved confirmed graph and declared mutation, or complete causal-surface
  omission when causal control is disabled;
- zero retry, transport error, fallback, and secret exposure counts.

After completion, inspect genuine recorded system input, user input, model output,
request parameters, and deterministic settlement for representative
Orchestrator, Executor, and Reflector calls. Coverage must include routed
thinking, all-roles disabled thinking, causal-off omission, a graph mutation, and
independent coordination. Inspection occurs only after the relevant arm has
stopped.

## Stop and continuation rules

Hard-stop the remaining sequence on a source/method/run identity mismatch,
initialization or physical advance failure, changed test identifier, secret
exposure, missing/corrupt evidence, non-atomic completion, retry, transport
error, fallback, or inability to enforce strict serialization. Preserve the
failed directory and report the failure.

An ordinary model JSON/schema rejection or deterministic patch rejection is
recorded without retry. A model JSON/schema rejection makes that arm fail its
release acceptance but does not prevent continuing later fresh independent arms.
A deterministic patch rejection within an otherwise valid schema is an expected
method outcome. Poor KPI values are recorded and do not stop the release sequence.
No observed KPI or model output may be used to modify this preregistration or the
frozen implementation during the sequence.
