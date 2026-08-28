# Architecture

H3C is a cooling-only hierarchical control framework. Its public control surface
has three Agent roles and deterministic owners around them.

1. The Orchestrator runs once per hour and allocates a shared allowance for
   energy-intensive setpoint movement. Its rationale is audit-only. Executors
   receive only the structured allowance snapshot. Each rationale must be a
   nonempty string, has no method-level character limit, and is preserved in
   full in raw and parsed evidence. Character length is non-decisional telemetry:
   it cannot degrade the model contract or trigger a control fallback.
2. One Executor per zone runs once per hour. Calls remain strictly serial in
   frozen profile-zone order, but all proposals are collected against the same
   pre-settlement allowance snapshot. Only after every proposal is collected
   are they settled in validated Orchestrator priority order; independent mode
   settles in profile-zone order. Executor rationale follows the same nonempty,
   full-preservation, no-length-decision contract before the normal program,
   causal, direction, and budget chain runs.
3. Each Executor sees the current complete executable program, current
   observations, the configured completed-history window, the last real
   rejection when one exists, and—when enabled—only resolved human-confirmed
   edge objects.
4. The deterministic admission chain applies `program_validation`,
   `causal_admissibility`, `consistent_program_direction_proof`, then
   `energy_budget_validation`. Disabled modules disappear instead of emitting
   empty placeholders.
5. The program interpreter runs every 15 minutes. Every resulting action passes
   through `comfort_recovery`, `setpoint_rate_limit`, then `actuator_bounds`.
6. The Reflector runs after the hour and summarizes observed results. Its input
   is explicitly projected to completed observations and excludes all future
   weather fields. Its prose is never an audit verdict, validator input, or
   downstream control input. Its one-sentence validator ignores a period only
   when that period has a digit on both sides, so decimal measurements do not
   masquerade as extra sentences; all real sentence terminators still share one
   fail-closed owner.

The full accepted program-update ledger is internal and replayed from the initial
program. Agent prompts expose only the current executable program. Working memory
contains exactly one, two, or three hours of completed proposal, admission,
program-identity, final-action, assurance, and physical-outcome frames. An
incomplete window is omitted as a block. Future weather never enters memory, and
this bounded projection is not long-term memory.

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
long-term memory, and historical launch/gate machinery.

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
