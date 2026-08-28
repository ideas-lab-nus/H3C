# Dynamic Prompt, fallback, and run-classification recovery preregistration

Status: frozen on 2026-08-27 after the user approved the proposed recovery and
before any production-code change or further model/BOPTEST call.

## Preserved evidence and reason for recovery

Source `1255afa829fc20577143bd327bef9fefd5cd6bab` produced five accepted release
arms, two completed but failed MZ_Air Agent arms, and one interrupted MZ_Air
Agent arm. The completed main and memory-two arms each made 42 model calls. Both
repeatedly exposed an hour-zero Orchestrator allocation whose zone budgets
exceeded its site cap; each also contained one Executor response with an
unknown root field. Their physical lifecycles and identity evidence are intact,
but their JSON-schema, coordination, or deterministic-settlement checks failed,
so neither counts as passing smoke.

The memory-three arm was stopped when the migration audit arrived. It made 38
model calls before interruption, has no completion marker, and its BOPTEST test
was explicitly stopped. All three directories remain immutable failed or
interrupted evidence. Together with the earlier 18-call failed arm, actual
DeepSeek use before this recovery is 182 calls. This number is separate from the
372-call plan for a future source-consistent release sequence and from the
16,824-call formal plan, which remains unexecuted and unauthorized.

The audit proved that the existing golden contract covered the three stable
system Prompts but not their dynamic user inputs. The historical cooling
production owner rendered materially different data, section names, ordering,
and formatting from H3C. The most consequential Orchestrator differences were:

- allocation limits were the resolved ordered `zones`, `site_cap_c`, and
  `per_zone_cap_c`, rather than maximum-field names plus a new priority object;
- cross-zone state contained each zone's setpoint, PMV, occupancy, program
  temperature targets, and available measured headroom/utilisation fields,
  rather than adjacency alone;
- only graph edges reaching the site surface were sent to the Orchestrator;
- the legacy compact Markdown/JSON rendering and combined previous-allocation
  section were not preserved.

The same renderer drift exists for Executor and Reflector user inputs. System
Prompt hash equality therefore did not prove the registered byte-equivalence
claim.

## Dynamic Prompt recovery boundary

The recovery restores the final cooling production dynamic Prompt contract for
all three roles while preserving the clean-framework omissions:

1. use the historical compact section renderer, titles, ordering, omission
   rules, tables, and JSON bytes for every retained cooling block;
2. restore the historical Orchestrator resolved limit object, detailed
   cross-zone projection, and site-edge-only causal projection;
3. restore the historical Executor current-program, observation, allowance,
   limits, relevant-edge, memory, outcome-summary, and rejection projections;
4. restore the historical Reflector current-results and working-memory
   projections; Reflector remains summary-only;
5. render `CONTROL DOMAIN` as a fixed cooling-only compatibility view with the
   historical cooling bytes. Do not restore a generic domain abstraction,
   Heating, domain switching, or case-name branches;
6. keep long-term memory absent, keep Orchestrator rationale audit-only, and
   keep only the current executable program visible to Executor.

The stable system Prompt bytes, output schemas, program language, causal
admission, direction proof, budget charging, action assurance, physical
protocol, request parameters, and suite matrix do not change.

## Deterministic fallback boundary

Restore deterministic Orchestrator fallback through the same allocation
validator. A previous valid allocation is reused when available; otherwise the
resolved site cap is split evenly in configured zone order. The raw rejection,
fallback reason, validated fallback allocation, and final ledger are recorded.
Fallback never accepts or clips an invalid allocation and never retries a model
call.

Executor keeps its exact root schema. An extra root field such as `rationale`
remains invalid and is not removed. API, parse, or schema rejection produces an
explicit deterministic unchanged-program outcome with the original rejection
evidence. It does not retry and does not synthesize an executable edit.

## Orthogonal run classification

Verification owns two independent results:

- `execution_integrity`: identity, continuous lifecycle, physical counts,
  evidence completeness, serialization, replay, action assurance, secret scan,
  retry, and transport integrity;
- `model_contract_clean`: raw role schemas, zero fallback, coordination
  contract, causal surface, thinking route, and complete deterministic
  settlement.

The final classification is exactly one of:

- `RELEASE-PASS`: execution integrity and model contract are both clean;
- `EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED`: execution integrity is clean but
  one or more safe model-contract checks failed;
- `RUN-INVALID`: execution identity, lifecycle, secret, transport, retry, or
  evidence integrity failed, or the verifier cannot establish a complete safe
  trajectory.

After a complete lifecycle, full verification, and secret scan, completion is
written atomically and carries the classification. A degraded completion is
evidence that a trajectory completed; it is not release acceptance and must
never be reported as clean. Interrupted or invalid runs do not receive a
completion marker. Release smoke still requires `RELEASE-PASS` for its highest
acceptance result.

## Required gates before any real call

1. tracked golden fixtures contain exact dynamic user bytes for Orchestrator,
   Executor, and Reflector, produced from representative production inputs;
2. production builders reproduce those bytes exactly, including block order,
   compact serialization, omission, site-only versus zone-relevant edges, and
   the resolved allocation-limit object;
3. reverse tests fail on maximum-field aliases, adjacency-only coupling,
   all-edge Orchestrator exposure, unknown root fields, and missing retained
   blocks;
4. fixed cooling compatibility projection is present while no Heating or
   generic domain switch exists;
5. causal-off removes causal data, glossary terms, output fields, validation,
   and evidence surfaces without placeholders;
6. invalid first-hour and later Orchestrator outputs select the registered
   deterministic fallback, validate it through the production validator, and
   preserve complete explicit audit evidence;
7. fake physical execution proves fallback maintains one continuous physical
   trajectory and produces a degraded completion, not `RELEASE-PASS`;
8. fake strict Executor schema rejection proves the unknown field is preserved
   as rejection evidence and results in an unchanged program;
9. fake valid execution proves zero fallback, clean model contract, and
   `RELEASE-PASS` completion;
10. corruption tests independently force `RUN-INVALID` for identity, lifecycle,
    secret, transport, retry, or evidence damage;
11. all pytest, Ruff, production strict mypy, configuration, matrix, Prompt,
    repository, secret, public-identifier, nested-repository, and whitespace
    gates pass;
12. the BOPTEST endpoint, container/image identities, and source checkout match
    the preserved server before a fresh release sequence begins.

Tracked source identity will change. Every earlier passing baseline and Agent
arm remains preserved but is superseded for final source-consistent smoke. The
next real sequence must restart at fresh arm zero and run strictly serially,
only after the review Session completes a read-only full-repository audit and
explicitly releases the hold. No formal suite or push is authorized.
