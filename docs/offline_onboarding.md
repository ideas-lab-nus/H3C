# Offline Mapping and HITL causal discovery

This workflow onboards a new cooling case without changing H3C's online control
runtime. Microsoft Agent Framework coordinates two offline model agents and two
real human review pauses:

```text
building documents
  -> SemanticMappingAgent
  -> human mapping review
  -> deterministic standardized-variable extraction
  -> CausalDiscoveryAgent
  -> human causal review
  -> existing graph validator, stable edge IDs, and confirm_graph
```

The online Orchestrator, Zone Executors, and Reflector do not import or initialize
Agent Framework.

## Install

The framework dependency is optional:

```console
uv sync --frozen --extra offline
```

Use `uv sync --frozen --extra dev --extra offline` when developing or testing this
workflow. A base installation without the extra keeps every existing online CLI
command available.

## Prepare an onboarding specification

Copy `configs/onboarding/example_spec.json` and its human-maintained case-profile
template. The specification declares:

- a portable case ID;
- one UTF-8 building document;
- an optional exact point inventory;
- the nonmapping case-profile template;
- one or more allowed causal evidence sources with stable source IDs;
- environment-variable names for an OpenAI-compatible endpoint, key, and model;
- a one-to-ten generation limit for each Agent stage.

The specification never contains a credential. The template owns testcase,
physical protocol, static controls, occupancy, objectives, comfort, performance,
and executable-program selection. Its `zones` and `global_inputs` fields must be
empty placeholders; only those two fields are filled from an approved mapping.

Set the environment named by the specification, for example:

```text
H3C_OFFLINE_MODEL_ENDPOINT=https://api.deepseek.com
H3C_OFFLINE_MODEL_API_KEY=<local secret>
H3C_OFFLINE_MODEL_ID=<model supporting reasoning_effort=low>
```

Do not put the values in the specification, terminal transcript, or workspace.

## Dry plan and execute

Dry planning reads and validates the specification but does not read provider
environment variables, create a workspace, import Agent Framework, or call a
model:

```console
h3c offline discover --spec configs/onboarding/example_spec.json
```

Execution requires an explicitly named human reviewer:

```console
h3c offline discover --spec configs/onboarding/example_spec.json \
  --reviewer "Engineer Name" --execute
```

The CLI prints the workspace path before the first model call. At each review
pause it displays the structured proposal and accepts exactly one of:

```text
approve
revise <specific feedback>
abort
```

Mapping review also displays the merged profile candidate. Causal review displays
readable arrows, the edge table, raw JSON, evidence IDs, and qualitative timing
tags. An approval is a human event, not another model call.

The pinned Agent Framework release implements `ctx.request_info()` and emits the
pending request as a generic `WorkflowEvent` whose type is `request_info`; it
does not export a separate Python class named `RequestInfoEvent`. H3C checks that
real event type, request ID, and typed `ReviewRequest` payload before accepting a
human reply, and persists it through `FileCheckpointStorage`.

Both model roles always send `reasoning_effort=low`. The final serialized request
must omit `temperature` and `top_p`; the request hook and verifier reject any
framework/provider default that violates this contract. OpenAI SDK automatic
retry is zero.

## Resume after an interruption

Agent Framework file checkpoints are stored after each workflow step and pending
human request. A provider network interruption is logged as one failed generation
and counts against that stage's limit. Resume is explicit:

```console
h3c offline resume outputs/offline/<case>/<workflow_id> \
  --reviewer "Engineer Name" --execute
```

Resume requires the same workflow, source specification, endpoint identity,
model, and secret identity. A completed or aborted workspace cannot resume. Only
an audited network interruption with a captured low-thinking/no-sampling request
is resumable; malformed output, schema failure, unsupported provider behavior, or
other nonnetwork model failure is not silently rerun. Successfully completed
stages are restored from checkpoint and are not called again.

## Verify and export

After both approvals, H3C replays the mapping, graph, provenance, review events,
model calls, wire identities, source hashes, framework checkpoint, and secret
scan. `completion.json` is written atomically last.

```console
h3c offline verify outputs/offline/<case>/<workflow_id>
h3c offline export outputs/offline/<case>/<workflow_id> \
  --case-profile configs/cases/<new-case>.json \
  --graph configs/graphs/<new-case>_confirmed.json \
  --provenance configs/graphs/<new-case>_provenance.json
```

Export accepts only a completed, independently verified workspace. All three
targets must be distinct, inside the repository, and absent; H3C never overwrites
an existing official profile or graph.

## Workspace contents

Generated workspaces live under `outputs/offline/<case>/<workflow_id>/` and are
ignored by Git. They contain the resolved specification and source manifest,
Mapping and causal proposals, human review events, confirmed mapping, profile
candidate, confirmed graph, separate causal provenance, model/raw I/O logs,
Agent Framework checkpoints, verification, and final completion.

Existing SZ_Air, MZ_Hydro, and MZ_Air mappings and confirmed graphs are tracked
inputs. This workflow does not regenerate or rewrite them, and their stable edge
IDs remain governed by the existing graph owner.

Every provenance entry is bound to a confirmed edge by its computed stable edge
ID rather than list position. Reordering proposals cannot attach an explanation
or source citation to the wrong physical edge.
