# H3C Three-Case Terminal Audit and Fix Items

## Scope

This audit covers the completed Baseten working-memory-only trajectories for MZ
Air, SZ Air and MZ Hydro. Their original `failure.json` and `verification.json`
files remain immutable. The corrections below only permit append-only,
zero-call recertification.

## What physically happened

All three trajectories completed their registered physical evaluation windows.
The runtime continued through ordinary model degradation by applying the
registered deterministic fallbacks. The adverse model events were:

| Case | Observed model-contract events |
|---|---|
| MZ Air | Empty length-terminated Executor output at hours 63 (WES) and 162 (COR); Orchestrator fallback at hour 15 for missing causal IDs and hour 116 for allocation above the registered cap |
| SZ Air | Empty length-terminated Executor output at hour 136; invalid Reflector lessons at hours 44 and 126; Orchestrator fallback at hour 6 for cap mismatch and hour 87 for missing causal IDs |
| MZ Hydro | Empty length-terminated SZ Executor output at hours 13, 80 and 108; Orchestrator fallback at hours 40, 66 and 89 for missing causal IDs |

Those events are genuine model-contract degradation. They are not evidence of a
broken physical trajectory: Executor empty output becomes deterministic
`no_change`, Orchestrator invalid output uses the registered validated allocation
fallback, and invalid Reflector output omits the lesson.

## Why the old terminal classifier said invalid

The old verifier also produced false execution failures:

1. It compared clock strings directly across midnight rather than modulo 24 h.
2. It reconstructed Baseten strict `json_schema` request identity from a stale
   generic schema instead of the actual wire schema.
3. It treated the runtime's deterministic addition of the mandatory visible
   site-power causal edge as raw-model patch tampering.
4. It used exact float equality for Budget values.
5. One SZ Air hour was recomputed with a default site cap instead of the cap
   embedded in that run's allocation contract.

These are verifier defects, not new acceptance relaxations. The correction
replays the same evidence using the original embedded runtime contract and
separates trajectory, model-contract and performance status.

## Fix items

| ID | Change | Runtime behavior impact |
|---|---|---|
| V1 | Verify working-memory clocks modulo 24 h | None |
| V2 | Rebuild request identity from the provider-native wire schema | None |
| V3 | Verify deterministic site-power edge completion as a bounded append-only transform | None |
| V4 | Use one registered absolute tolerance for Budget values | None |
| V5 | Share the exact dynamic cap owner with renderer, runtime and verifier | None |
| V6 | Report `trajectory_status`, `model_contract_status` and `performance_status` independently | None |
| V7 | Append zero-call recertification with source/terminal hashes; never overwrite old artifacts | None |
| R1 | Add exact completed-step reward decomposition to the next working-memory interval | Information channel only; no new gate or safety rule |

## Release discipline

The old trajectories remain historical evidence. The new MZ Hydro candidate is
a fresh, preregistered one-attempt run whose only method change is R1. It must
beat the frozen eRBC reward and remain within occupied peak `|PMV| <= 0.70`
before the same commit is evaluated on SZ Air and MZ Air.
