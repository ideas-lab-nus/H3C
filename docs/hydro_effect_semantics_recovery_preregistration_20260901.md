# Hydro effect-semantics recovery preregistration

Date: 2026-09-01

## Trigger and preserved evidence

The reward-feedback MZ Hydro arm from source
`47136464f9a6a1590edda023692ef303192b22b9`, run
`20260901T095051265311Z-4c71bc6e19bf`, and BOPTEST test
`effacef7-faca-4dad-8d18-adaa7af7b731` was stopped by explicit user decision
after 79 atomic completed hours. Its files are immutable
`USER-CANCELLED / ATTRIBUTABLE-METHOD-DEFECT / CENSORED-INCOMPLETE` evidence and
will not be resumed, overwritten, or presented as a completed result.

The attributable chain was:

1. an accepted `pmv_band_lo: 0.4 -> -0.5` patch reduced the match frequency of
   the positive-setpoint `pmv_raise` rule, despite a rationale claiming that the
   edit would save energy;
2. the full-program direction proof correctly derived `program_direction=down`
   and a power-increasing effect,
   but the next-hour Agent view removed that deterministic result as audit-only;
3. a later non-weather recovery patch was rejected because the causal
   weather-driver binding check
   check scanned unrelated weather rules in the whole executable program rather
   than only rules behaviorally affected by that patch;
4. hourly working-memory TV/reversal features omitted the boundary from the
   previous physical setpoint to the first action of the completed interval.

## One registered method correction

The fresh replacement may change only the following generic semantics:

- scope required weather-driver citations to the rule set behaviorally affected
  by the current operation (`add`, `replace`, `remove`, `move`, or parameter
  references for `set_param`);
- retain a compact deterministic program-effect summary in completed working
  memory after removing raw causal IDs and proof internals;
- calculate completed-interval setpoint TV and reversals over the previous
  physical setpoint followed by the four executed setpoints;
- add one role-neutral decision aid telling an Executor to trace comparator,
  rule-match frequency, and action direction before a parameter edit, and one
  Reflector evidence aid telling it to ground Lessons in observed reward
  components while distinguishing shared site energy from zone contributions.

These changes restore existing causal admissibility, full-program direction,
and feedback semantics. They do not add
an admission rule, reward veto, energy veto, cooldown, reversal prohibition,
PMV recovery rule, delayed-edge controller, case-specific parameter, direct
setpoint action, or new output field.

## Frozen method and acceptance

Provider/model, strict JSON schema, the uncompressed neutral Prompt under
`occupancy_routed` low thinking, one-hour
working memory, long-term memory off, the initial executable program,
`pmv_step_c=0.3`, ProgramCheck, causal admissibility, full-program direction
proof, Budget, actuator bounds followed by rate limiting and comfort recovery,
the reward formula, seven-day warm-up, 120-hour
evaluation and all MZ Hydro thresholds remain unchanged. The registered pass is
reward greater than `-179.35418363224142`, occupied peak absolute PMV at most
`0.70`, and healthy physical/source/run/test/timeline/secret/evidence identity.

## Offline gates before launch

- the historical bad threshold patch still produces full-program
  down/power-up evidence;
- an unrelated non-weather patch does not inherit weather-edge requirements;
- a genuinely affected weather rule still requires its visible weather edge;
- invalid, duplicate, irrelevant, or unavailable causal IDs remain rejected;
- Agent working memory exposes only the compact deterministic effect, not raw
  causal IDs, proof witnesses, or validation-stage internals;
- boundary TV/reversal values agree with the frozen step reward's action path;
- historical output JSON remains parseable and replayable;
- targeted tests, full pytest, Ruff, format, strict mypy, document freshness and
  staged secret scan pass from a clean commit.

## Fresh run discipline

After the gates, launch exactly one fresh MZ Hydro arm from the clean corrected
commit with a fresh run directory and fresh BOPTEST test identity. Do not reuse
or replay the cancelled test. Registered transient Provider failures may retry
at most twice (three requests total). Ordinary model-contract degradation or
poor KPI continues and does not trigger a lucky rerun. A dedicated 30-minute
heartbeat will report only atomic completed-hour evidence.
