# `revise2.txt` Disposition Matrix

This matrix records how the supplied Orchestrator review was handled. The source review remains outside the repository at `C:\Users\lenovo\Downloads\revise2.txt`; its content is paraphrased here rather than copied.

| Review point | Disposition | Production result |
|---|---|---|
| System and dynamic facts are correctly separated | Retained | Stable policies remain in system prompts; current state, forecasts, history and limits remain dynamic. |
| `common + rows` is effective | Retained and extended | Top-level scalar properties, common values and homogeneous rows are rendered without nested escaped JSON. |
| Time wording around “this/next hour” is ambiguous | Fixed with user override | The suggested `target_hour/target_steps` counters were deliberately not adopted. Inputs now use `current_time`, half-open intervals and explicit action/outcome `HH:MM` clocks. |
| `precool_residual_c=-5` is ambiguous | Fixed | Orchestrator sees `precool_offset_from_unoccupied_base_c=-5` and `resulting_precool_setpoint_c=25`. Executable program field names remain unchanged. |
| `warmer_c/cooler_c` lost their meaning | Fixed | Replaced by directional `temp_rise_to_warm_pmv_edge_c` and `temp_drop_to_cool_pmv_edge_c`. |
| Allocation contract lacks exact numeric/set constraints | Fixed | Shared `ALLOCATION_CONTRACT_SPEC` drives both compact prompt constraints and deterministic validation, including exact site cap, zone sets, finite bounds, sum, permutation, rationales and causal IDs. |
| Budget charge is mathematically ambiguous | Fixed | Prompt and code documentation use the maximum additional cooling displacement over the proof state space, explicitly excluding cumulative movement, power and precooling offset. |
| Zone state, occupancy, setpoint and prior Budget facts repeat across blocks | Fixed | Current facts, working history and previous Budget use have separate owners; the previous interval endpoint is not repeated as another current-state row. |
| Raw weather and derived summaries repeat information | Retained intentionally | Both remain because the summary reduces low-effort inference while the four-outcome path preserves trend shape; they have separate labels and are verified for completeness. |
| Previous allocation/utilisation arithmetic is unclear | Fixed | Reserved allowance, reserved consumption, initial unreserved pool, shared-pool consumption and remaining pool are separate fields generated from real ledger events. |
| New format should enter replay/A-B before production | Accepted | Current classification remains behavior-unverified; no API/BOPTEST run was started in this stage. |

The review's positive observations about typed structure, common-field lifting and system/user separation remain valid. The implementation does not claim that shorter or clearer context preserves model behavior until a separately approved real evaluation is completed.
