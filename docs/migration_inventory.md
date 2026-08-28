# Clean-framework migration inventory

This inventory freezes the migration boundary before behavior is copied. The
historical production tree remains a read-only oracle. H3C uses semantic public
names, one owner per behavior, and no case-name branches.

## Owners to migrate

| Historical production responsibility | New owner | Required equivalence |
|---|---|---|
| Orchestrator role and structured cross-zone allocation | `h3c.agents.roles.Orchestrator` | Same hourly allocation and shared energy-intensive movement allowance; the later public contract preserves every nonempty audit rationale in full and reports length only as non-decisional telemetry |
| Zone Executor role and structured atomic program operation | `h3c.agents.roles.Executor` | Same occupancy routing and current-program-only prompt input; a nonempty audit rationale has no character-limit decision and the executable patch still traverses the full validation chain |
| Reflector role | `h3c.agents.roles.Reflector` | Observation summary only; decimal points are not sentence ends, and prose has no validation, audit authority, or downstream control input |
| Stable role policy | `h3c.agents.prompts` | Canonical cooling-only system prompts are byte-for-byte equal for all three roles |
| Dynamic role-input rendering and missing-block omission | `h3c.agents.dynamic_prompt` | Representative Orchestrator, Executor, and Reflector user prompts are byte-for-byte equal to the read-only final cooling builders, including cooling-only control-domain compatibility, coupling, site-edge projection, recent outcome, and last rejection |
| Canonical executable cooling program, patch operations, interpreter, version, and hash | `h3c.control.program` | Same initial program, patch result, branch, residual, setpoint, version, and hash |
| Program structural validation | `h3c.control.validation` | Same accept/reject result and semantic rejection reason |
| Human-confirmed graph loading and stable edge identifiers | `h3c.causal.graph` | Same canonical edges and identifiers; missing edges cannot be cited |
| Causal admissibility and consistent whole-program direction proof | `h3c.causal.admissibility`, `h3c.causal.direction` | Same cited-edge admission and unique direction result |
| Energy-intensive movement budget and settlement ledger | `h3c.control.budget` | Same grant, charge, remaining allowance, and hourly settlement |
| Comfort recovery, setpoint rate limiting, and actuator bounds | `h3c.assurance.action` | Same ordered action result and complete semantic telemetry |
| Bounded working memory projection | `h3c.memory.working` | Same complete proposal/admission/program/action/assurance/outcome history for one, two, and three hours, with future weather excluded |
| Full accepted patch ledger and replay from the initial program | `h3c.memory.ledger` | Same current program, history, version, and hash after replay |
| Four-step weather input, three deterministic summaries, and weather-condition language | `h3c.runtime.weather` | Same raw forecast rows, summaries, condition evaluation, and omission of unavailable fields |
| Effective occupancy, declared missing occupancy resolution, and hourly Executor routing | `h3c.runtime.occupancy` | Same current/forecast effective counts and call schedule; day-220 non-occupancy null remains zero while the new common conditioning null follows the user's documented occupied-time rule |
| Case mapping and static controls | `h3c.experiments.profiles` | Same three-case point mapping and BOPTEST action payloads |
| Observations, forecasts, physical actions, and continuous lifecycle | `h3c.runtime.protocol`, `h3c.runtime.engine` | One initialize, continuous conditioning plus evaluation, one stop, and evaluation-only metrics |
| Provider request identity, raw input/output, and call accounting | `h3c.runtime.clients` | Same stateless request contract and role counts; bounded transient connection retries are explicit per-attempt evidence, never hidden fallback |
| Run artifact schema, metrics, atomic completion, verification, and reports | `h3c.outputs` | All required files, raw-stream metric/identity/replay recomputation, explicit execution/model-contract classification, and completion written last |
| Suite matrices and registered single-factor variants | `h3c.experiments` | Three deterministic baselines and twenty-four unique Agent identities |

## Explicitly omitted

| Historical feature | Omission reason |
|---|---|
| Heating control | Outside the user-selected cooling-only framework |
| Generic multi-domain control abstraction | Would expand the declared method and weaken exact W-only equivalence |
| Direct-actuation-only program replacement | Retired experimental branch, not the selected architecture |
| Split-gain program variant | Retired experiment, not part of the final control program |
| Numeric lag and cooldown logic | Human input is qualitative immediate/delayed structure, not an estimated physical delay |
| Retired numbered checks and stage launchers | Replaced by semantic validation owners and direct production-path tests |
| PMV trend inputs | Not part of the selected prompt information surface |
| Comfort-triggered Executor scheduling | Replaced by hourly execution with occupancy routing |
| Pre-assurance output-adjustment experiment | Outside the mandatory deterministic assurance chain |
| Actuation-efficacy experiment layer | Experimental diagnostic, not the selected method |
| Long-term memory | Only bounded completed-history memory is registered |
| Historical launchers, workspaces, and gates | H3C owns a single CLI, declarative suites, and one verifier contract |
| Generic forecast `None`-to-zero conversion | The old runtime silently applied it to every forecast field; H3C permits only the configured occupancy rule and fails closed for all other missing inputs |

## Migration rules

1. Copy behavior only when an equivalence fixture names the source and expected
   output.
2. Case differences belong in configuration, never in case-name control branches.
3. Missing observations are omitted as fields; placeholders are forbidden.
4. Causal-disabled runs remove causal data from prompts, schemas, memory,
   rejection feedback, validation, and manifests.
5. Generated run data belongs under `outputs/runs`; generated reports belong
   under `outputs/reports`.
