# Architecture

H3C is a cooling-only hierarchical control framework. Its public control surface
has three Agent roles and deterministic owners around them.

The paper uses **Policy Adapter** for the zone-level Agent. The code and retained
evidence use the historical identifier `Executor`; both names refer to the same role.

1. The Orchestrator runs once per hour and allocates a shared allowance for
   energy-intensive setpoint movement. Its rationale is audit-only. Policy Adapters
   receive only the structured allowance snapshot. Each rationale must be a
   nonempty string, has no method-level character limit, and is preserved in
   full in raw and parsed evidence. Character length is non-decisional telemetry:
   it cannot degrade the model contract or trigger a control fallback.
2. One Policy Adapter per zone runs once per hour. All zone calls are issued
   concurrently after Orchestrator completes, and all proposals use uncharged
   pre-settlement allowance snapshots. Only after every issued request finishes
   are proposals settled in validated Orchestrator priority order; independent
   mode settles in profile-zone order. Response arrival order never changes
   settlement. Policy Adapter rationale follows the same nonempty, full-preservation,
   no-length-decision contract before the normal program, causal, direction,
   and budget chain runs.
3. Each Policy Adapter sees the current complete executable program, current
   observations, the configured completed CAOL window, the last real rejection
   when one exists, and—when enabled—only resolved human-confirmed edge objects.
4. The deterministic admission chain applies `program_validation`,
   `causal_admissibility`, `consistent_program_direction_proof`, then
   `energy_budget_validation`. Disabled modules disappear instead of emitting
   empty placeholders.
5. The program interpreter runs every 15 minutes. Every resulting action passes
   through `comfort_recovery`, `setpoint_rate_limit`, then `actuator_bounds`.
6. The Reflector runs once after the four physical steps. Runtime first builds
   each zone's deterministic Context, Action, and Outcome. Reflector supplies
   only one concise Lesson per zone; runtime combines it with CAO to form the
   completed CAOL. A malformed Lesson is omitted while CAO remains usable.
   Reflector input contains no future weather. Its text is never an audit
   verdict, validator input, or direct control instruction.

The full accepted program-update ledger and 15-minute records remain internal and
are replayed from the initial program. Agent prompts expose only the current
executable program. CAOL is the sole Agent-visible working-memory owner. At
`k=1`, Orchestrator receives all zones' previous-hour CAOL records and each
Policy Adapter receives only its own previous-hour CAOL. An incomplete window is
omitted as a block. Future weather never enters CAOL.

Long-term experience is a separate optional module. Each zone has exactly three
initially empty slots: `unoccupied`, `occupancy_transition`, and
`steady_state_occupancy`. Stored values contain only regime, revision, and a
zone-wide experience. When enabled, Reflector may perform at most one
CAS-protected `add`, `replace`, `delete`, or `no_change` operation per zone and
only for a regime that occurred in the completed hour. Only the corresponding
zone Policy Adapter sees active experiences. Orchestrator never sees them, and
Policy Adapter references are audit-only. When disabled, the Prompt, schema, runtime
output, CRUD and reference surfaces are absent rather than empty placeholders.

Weather input consists of the next four raw 15-minute outdoor-temperature and
solar-irradiance points plus three deterministic one-hour summaries. The summary
field names are the weather-condition language available to executable rules:

- `outdoor_temp_change_next_1h_c`
- `solar_irr_max_next_1h_w_m2`
- `solar_irr_mean_next_1h_w_m2`

Case differences are declared in `configs/cases`. Production role, validation,
assurance, memory, and physical-loop code does not branch on testcase names.

The clean framework intentionally omits heating control, generic control domains,
direct-action program replacement, split gains, numeric lag/cooldown, PMV trend
inputs, comfort-triggered Executor scheduling, actuation-efficacy experiments,
unbounded or retrieval-based memory, and historical launch/gate machinery.

## Isolated offline onboarding

Onboarding a new case is outside the online control loop. `h3c.offline` uses
Microsoft Agent Framework to connect a Semantic Mapping Agent, a real human
Mapping review, deterministic standardized-variable extraction, a Causal
Discovery Agent, and a real human causal review. File checkpoints preserve each
pending review and completed stage across processes. Final confirmation reuses
the existing graph validator, stable edge ID algorithm, and `confirm_graph`.

Agent Framework and its OpenAI provider are optional dependencies and are
imported lazily only by the offline command. They never enter online control
modules. Mapping can fill only profile mapping fields; every physical protocol,
static control, occupancy rule, objective, comfort parameter, and testcase
remains human-authored configuration. Agent edge explanations and human feedback
live in a provenance sidecar rather than runtime edge identity.
