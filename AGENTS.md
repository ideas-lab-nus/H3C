# H3C repository rules

This file is the persistent operating contract for the standalone H3C repository. Current experiment status belongs in run manifests or dated result notes, not here.

## Scientific scope

- H3C is a cooling-only, hierarchical causal-constrained building-control framework. The production architecture is Orchestrator → zone Executors → deterministic settlement and actions → Reflector, with confirmed causal graphs, shared energy budget, CAOL working memory, weather-aware rules, and the mandatory action-assurance chain. Three-regime long-term experience is not part of the production default or current experiment programme. Its explicit `--long-term-memory` interface remains only for reproducibility and future user-authorized ablation; when disabled, its Prompt, schema, runtime and evidence surface is absent.
- Case differences belong in `configs/`; do not add case-name branches to production code or case-specific instructions to shared prompts.
- Causal constraints bound admissible program changes; they are not a hidden control law. Natural-language rationale is audit text and never directly changes allocation, patches, actions, or acceptance.
- Mapping and causal discovery are optional offline onboarding capabilities. They use Microsoft Agent Framework and real human review. Online control remains on H3C's deterministic runtime.
- Preserve adverse results and post-result decisions. Never delete a failed run, rewrite a criterion after seeing results, combine fresh arms, or present a different source commit's trajectory as the current implementation's result.

## Experiment priority

The framework is established. The normal workflow is now: run the registered experiment, collect data, generate figures and analysis, then update the paper and reviewer response. Engineering checks protect that workflow; they must not displace it.

For a frozen source, each arm receives only a lightweight integrity check:

- source/config/case/model/thinking identity;
- warm-up, vanilla prefix, evaluation window, and BOPTEST test identity;
- expected samples and role calls;
- readable core outputs, current-output secret scan, completion, and metrics.

Read existing manifests and logs. Do not build a second long replay system. Full pytest, Ruff, mypy, Prompt golden, standalone export, tamper/fuzz, and full replay run only when their production owner changed and the result can change the next action. Final paper tables and figures receive one independent source/window/KPI review at the aggregate-result milestone.

Ordinary schema rejection, deterministic rejection, fallback, or poor KPI is recorded and the independent sequence continues when actions, physical evidence, and identity remain auditable. Initialization/advance failure, source/profile/test/window mismatch, secret exposure, or corrupt/missing evidence remains a hard stop.

## HERO anti-over-defense

HERO limits the proposed fix and checking cost; it never suppresses a real finding.
The project rule is adapted from [HERO's pinned rules at `bfe4026`](https://github.com/wanshuiyin/HERO-Anti-OverDefense/blob/bfe4026da368823576cbb55195a14c4cf29f6aa2/RULES.md).

- **H — Hashing:** do not add hashes, checksums, or fingerprints unless they replace a materially more expensive operation and change what happens next. Git commit, resolved config, and ordinary field comparison are sufficient for normal identity.
- **E — Edge cases:** defend cases reachable through supported interfaces, documentation, or real project data. Report reachable rare cases; do not build for scenarios that are merely constructible in principle.
- **R — Rubrics:** where judgement is needed, judge. Do not substitute scoring tables, long checklists, stacked reviewers, or re-verification loops for a settled fact.
- **O — Overbuild:** do not add feature flags, migration frameworks, compatibility layers, wrappers, auditors, or guards for unrequested futures.
- HERO does not override explicit user requirements, research integrity, credential safety, non-destructive file handling, or genuine experiment identity.

Before any check, state the live uncertainty, the concrete failure it can expose, and what changes if it fails. If those cannot be named, do not run it. A real experiment covering the same frozen path normally replaces a separate smoke or replay. Say plainly when something is correct; do not manufacture findings. Keep limitations in one section instead of turning every paragraph into a defense transcript.

## Runtime and evidence discipline

- `h3c run` and `h3c suite` are dry plans unless `--execute` is explicit.
- Logical dependencies remain serial, but independent physical arms and model requests may overlap. Every physical arm uses a fresh test identity, checkout, output owner, and execution lock. BOPTEST `Running`/`Queued` status owns capacity; queued arms do not initialize or call the model, and the client does not impose a fixed worker count.
- Within an H3C hour, Orchestrator completes before all zone Executors are issued concurrently; all issued Executors finish before deterministic priority/zone-order settlement, four physical steps, and Reflector. Response arrival order never controls settlement.
- One physical method attempt is launched once; there is no lucky method rerun. Preserve and diagnose every terminated run. A user-approved and preregistered resume/replay uses a fresh run/test identity, replays the atomic completed physical prefix from the same initial state, verifies program/working-memory/Budget/KPI state, and only then continues at the checkpoint. It never appends to the failed directory, reuses the old test, skips unverified physical steps, or merges unrelated runs. If a control-neutral failure is not resume-eligible, stop for user direction rather than silently restarting from the beginning. A repair that changes Prompt, control method, model parameters, KPI, or acceptance criteria still requires user review. Poor KPI and ordinary model-contract degradation do not trigger recovery. Only the configured bounded, identical-payload retry for whitelisted transient model transport errors is allowed within one run. Do not advance BOPTEST between wire attempts; record each attempt and uncertain provider charge.
- Keep raw model I/O, program updates, actions, physical trajectory, metrics, and source/config identity. Generated data belongs under `outputs/`; do not disguise it as source code.
- Keep API keys and endpoint secrets out of configs, prompts, logs, evidence, commits, and terminal output. Scan only new/generated or staged files unless a live reason requires wider scope.
- Do not modify paper LaTeX, figures, or reviewer text unless that task explicitly requests it. Do not push unless the user authorizes the current push.

## Code and dependency ownership

- One behavior has one owner. Do not duplicate schema, prompt, metric, or validation truth across runtime and verifier.
- The one maintained runtime environment for H3C execution is `D:\NUS\Paper\01-Heriachical Control\H3C_CAOL_Final_Worktree\.venv`; its interpreter is `D:\NUS\Paper\01-Heriachical Control\H3C_CAOL_Final_Worktree\.venv\Scripts\python.exe`. Other worktrees must not create their own `.venv`: set `PYTHONPATH=<target-worktree>\src`, invoke that interpreter with `-m h3c.cli`, verify `h3c.__file__` resolves inside the target worktree, and require an identical `uv.lock`. Update the maintained environment in place only when no H3C process is active. If it is absent, damaged, or lock-incompatible, stop instead of creating a substitute environment.
- Keep semantic public names; historical stage/check nicknames do not enter new interfaces.
- `pyproject.toml` plus `uv.lock` are the dependency source of truth. `requirements*.txt` are generated pip-compatibility exports and must not be hand-edited independently.
- Preserve the canonical Prompt unless the task explicitly changes behavior. A compatibility parser may normalize only named, unambiguous, control-neutral forms; unknown or conflicting fields still fail closed.
- Use minimal, targeted tests for changed owners and their real consumers. Do not rerun unchanged gates to demonstrate diligence.

## Sessions and collaboration

The primary Session may choose subagents or dedicated child Sessions for bounded tasks to prevent one context from accumulating the whole project history. Read-only evidence location and independent review may be delegated without a separate prompt. Keep one writer per checkout; API/BOPTEST and external mutations require explicit authorization. A handoff is an index to owners, tests, and remaining risks, not proof that review occurred.

Report actual state: planned, running with a real process/control/completion identity, completed with artifacts, or failed. Work does not continue invisibly after a final response.
