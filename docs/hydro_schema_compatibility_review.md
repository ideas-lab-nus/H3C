# MZ_Hydro seven-day schema compatibility review

Date: 2026-08-28

This is a post-result engineering review of the completed MZ_Hydro runs under source `8cbf352f48536969f401d8f76cf394fcd580dc5f`. It does not rewrite their manifests, raw model output, verification files, or physical trajectory.

## Finding

The physical run is complete and auditable: 672 evaluation steps, 1,344 zone-step records, 168 hourly decisions, 672 logical model calls, a single initialization and stop, matching conditioning-prefix and evaluation-boundary identities, no terminal transport failure, and no secret exposure.

The original inline verifier reported `RUN-INVALID`. Two distinct issues were combined in that label:

1. A verifier implementation defect compared the public model patch with a settled patch after the deterministic validation chain had added `expected_effects` and `consistent_program_direction_proof`. All 32 accepted edits therefore failed an exact-object rationale comparison even though their public fields and rationale were preserved. The correct engineering classification for the original trajectory is execution-healthy with a degraded model contract, not corrupt execution.
2. The model produced 78 narrow structural deviations: one Orchestrator `allocation_contract` wrapper and 77 Executor deviations. The Executor set comprised 69 extra root-level audit rationales, two duplicate `root.patch` wrappers equal to the canonical patch, and six redundant `replace_rule.id` values equal to `rule.id`.

The runtime now normalizes only these unambiguous forms and then applies the unchanged strict allocation, program, causal, direction, and budget validators. Conflicting duplicate patches, mismatched rule identifiers, unknown fields, invalid JSON, and invalid control content still fail closed. Raw model I/O remains complete.

## Result interpretation

Relative to the deterministic baseline, the historical Agent trajectory reduced cost by 8.8906% and energy by 9.1922%, while discomfort increased from 0 to 4.75 zone-hours and from 0 to 0.165 PMV-hours; occupied peak absolute PMV rose from 0.47 to 0.59, setpoint total variation increased by 31.1%, and reversals increased from 20 to 80. It is useful evidence of an energy-comfort tradeoff and does not establish G1.

## Reuse boundary

- The baseline run can be reused unchanged.
- The Agent run is retained as a complete historical/adverse trajectory of source `8cbf352f`; it must keep that source identity and its original machine artifacts.
- The compatibility change can admit 19 candidate edits that the historical runtime converted to deterministic no-change. Consequently the old Agent trajectory cannot be presented as a formal result of the integrated post-fix source and cannot remove the need for a future final-source Hydro run if that exact result is required.
- No rerun or physical/API call was made for this review.

The original result report and machine summary remain in `docs/rationale_contract_and_mz_hydro_7day_result.md` and `docs/rationale_contract_and_mz_hydro_7day_summary.json`. The copied raw directories, when present locally, remain ignored under `outputs/runs/main/MZ_Hydro/`.
