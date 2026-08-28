# Offline Mapping and HITL Causal Discovery Preregistration

## 1. Identity and scope

- Date: 2026-08-28
- Task branch: `codex/h3c-offline-onboarding-20260828`
- Starting implementation commit: `8cbf352f48536969f401d8f76cf394fcd580dc5f`
- Product boundary: add a reproducible, optional offline onboarding workflow to H3C.
- Online boundary: the existing Orchestrator, Zone Executor, Reflector, control law,
  prompts, profiles, run artifacts, and physical execution path are unchanged.
- Concurrent-run boundary: the active MZ_Hydro experiment in its separate worktree is
  read-only to this task. This task must not inspect its partial logs, alter its source,
  or consume its BOPTEST/API resources.

This task does not call DeepSeek, does not call BOPTEST, does not regenerate the three
existing mappings or causal graphs, and does not modify their stable edge identifiers.
It does not modify `Revision1/`, LaTeX, Figure 3, or historical run evidence, and it does
not push.

## 2. Research and engineering question

Can a new H3C user reproducibly onboard an unseen cooling case by:

1. asking a Mapping Agent to identify only the required semantic BMS points;
2. pausing for real human approval or revision;
3. deterministically translating the approved mapping into standardized variables;
4. asking a Causal Discovery Agent for a structured H3C graph proposal;
5. pausing for a second real human approval or revision; and
6. freezing the result through the existing graph validator, stable-edge-ID owner, and
   `confirm_graph` implementation?

The offline workflow uses Microsoft Agent Framework for typed executors,
`ctx.request_info()`, `RequestInfoEvent`, and checkpoint/resume. It does not migrate the
online control agents to that framework.

## 3. Frozen dependency and provider boundary

The optional installation group is frozen to:

```toml
offline = [
  "agent-framework-core==1.15.0",
  "agent-framework-openai==1.14.0",
]
```

The base H3C installation must remain usable without this extra. Framework/provider
imports are confined to the offline execution surface and must not be imported or
initialized by online commands.

The default provider contract is an OpenAI-compatible DeepSeek endpoint configured by
environment-variable names declared in the onboarding spec. Secrets are never stored;
only the variable names and a non-reversible secret identity may enter a workspace.
Every Mapping and Causal Discovery request must serialize:

```json
{"reasoning_effort": "low"}
```

and must omit both `temperature` and `top_p`. This explicitly supersedes the historical
Mapping `temperature=0.0` and Causal Discovery `temperature=0.2`. Unsupported providers
fail closed instead of silently changing thinking or sampling behavior. Framework and
SDK automatic retries are disabled. A network interruption preserves the checkpoint;
the operator must explicitly resume, and a previously successful cached stage must not
be called again.

No real provider request is authorized or required by this implementation task.

## 4. Frozen workflow and human contract

The only allowed order is:

```text
Mapping proposal -> human Mapping review -> deterministic profile candidate
-> causal proposal -> human causal review -> existing confirm_graph -> verification
```

The two review gateways are human interfaces, not LLM critics. Each reply is exactly one
of:

- `approve`
- `revise <feedback>`
- `abort`

Each stage permits at most ten model generations by default. A spec may lower, but not
raise, the limit. `revise` creates a new generation with the previous proposal and exact
human critique. `abort` is terminal and cannot export. Checkpoints bind the workflow
identity, source documents, resolved spec, cached successful calls, and ordered review
events. `resume` rejects any identity mismatch.

## 5. Frozen public CLI

```text
h3c offline discover --spec <onboarding-spec>
h3c offline discover --spec <onboarding-spec> --reviewer <name> --execute
h3c offline resume <workspace> --reviewer <name> --execute
h3c offline verify <workspace>
h3c offline export <workspace> \
  --case-profile <new-path> \
  --graph <new-path> \
  --provenance <new-path>
```

Without `--execute`, `discover` only prints the resolved plan; it must not create a
workspace, read a secret value, import/initialize Agent Framework, or call a model.
`export` accepts only a completed, untampered, independently verified workspace whose
two stages were approved. Every target must be absent; overwrite is forbidden. Existing
`h3c graph prepare/propose/validate/confirm/derive` commands remain compatible and share
the same graph validation owner.

## 6. Mapping contract

The Mapping system prompt preserves the historical role and intent:

- “Master Systems Integrator for Smart Buildings”;
- positive Observation and Control requirements;
- all power sensors;
- `_u` actuator and `_y` measurement naming hints; and
- extraction of only user-requested points.

The structured Mapping output owns only:

- zone description;
- zone temperature sensor;
- cooling setpoint actuator;
- occupancy forecast;
- outdoor temperature forecast;
- solar irradiance forecast;
- electricity price forecast; and
- all power meters.

It cannot generate or change runtime windows, BOPTEST testcase selection, static control
values, occupancy logic, objective weights, comfort settings, or action assurance. Those
fields come exclusively from the human-maintained case-profile template. A deterministic
merge inserts only the approved mapping fields.

The Mapping gate is strict: required keys, no unknown keys, nonempty values, no duplicate
or conflicting point roles, and exact point membership in the source document or optional
structured inventory. `_u/_y` mismatches are warnings requiring human judgment, not an
automatic truth source. The Mapping proposal and merged profile candidate are displayed
together before approval.

## 7. Causal Discovery contract

The Causal Discovery prompt preserves the historical role and intent:

- “Building Physics & Thermodynamics Expert”;
- standardized variable names only, never BMS point identifiers;
- relations among setpoint, zone temperature, power, occupancy, and weather; and
- previous proposal plus exact user critique on revision.

The output is a structured proposal compatible with the current H3C graph schema. The
human view includes readable arrows, an edge table, raw structured JSON, evidence source,
and qualitative timing tags. Unsupported historical `Threshold` or numeric lag/cooldown
semantics are intentionally not restored.

The Agent may cite only source IDs declared by the onboarding spec. On approval:

- `confirmed_causal_graph.json` uses the existing runtime schema and stable-ID owner; and
- `causal_provenance.json` records source IDs, Agent rationale, human feedback, and
  confirmation round keyed by stable edge ID, without changing edge identity.

Human approval cannot bypass the existing graph schema, stable ID, or `confirm_graph`
validation.

## 8. Artifact, secret, and completion contract

Each executed workflow writes only below:

```text
outputs/offline/<case>/<workflow_id>/
```

with the registered resolved spec, source manifest, Mapping/Causal proposals and review
events, confirmed mapping, profile candidate, confirmed graph, provenance, model-call and
raw-I/O audit, checkpoints, verification, and completion artifacts. Generated contents
are ignored by Git.

Each model-call record binds role, sequence, model and endpoint identity, framework
version, prompt hashes, `reasoning_effort=low`, absence of sampling fields, input/output,
usage, latency, and checkpoint identities. Secret values may not appear in any artifact.
`completion.json` is written atomically and last, only after both approvals, graph/profile
validation, provenance validation, artifact consistency, and a real secret scan pass.

## 9. Acceptance gates

The implementation passes only when all of the following are green:

1. strict Mapping schema, exact point membership, duplicate/conflict rejection, and
   protected profile-template merge;
2. standardized variables contain no BMS point IDs;
3. strict graph endpoint/relation/tag/source/stable-ID checks through existing owners;
4. approve, revise, abort, process-exit checkpoint, and new-process resume paths;
5. successful cached stages are not regenerated on resume;
6. incomplete/tampered workspaces, review events, unknown sources, illegal edges, and
   existing export targets fail closed;
7. fake Agent Framework/provider integration covers the full workflow without network;
8. serialized wire requests contain `reasoning_effort=low` and omit `temperature` and
   `top_p`; manifest/log/request discrepancies fail;
9. missing optional dependencies and providers have actionable errors;
10. source Prompt oracle, new golden fixtures, and an explicit migration-difference list;
11. current three profiles and confirmed graphs load unchanged and retain exact stable IDs;
12. base install leaves all online CLI commands usable and imports no Agent Framework;
13. full pytest, Ruff check/format, strict mypy, lock, CLI/config/secret, and independent
    repository-root gates pass.

This task has no physical or model-output KPI and no post-result branch. Any discovered
need to modify online control behavior, existing mappings/graphs, provider sampling
semantics, or the active Hydro source requires a new user decision.
