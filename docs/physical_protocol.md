# Physical protocol

Every registered arm uses a fresh BOPTEST selection and runs strictly serially.

The lifecycle is fixed:

1. Select the configured testcase and obtain one test identity.
2. Configure dynamic electricity price and a 900-second step.
3. Initialize once at the case evaluation start while requesting a seven-day BOPTEST internal
   warm-up.
4. Apply no explicit conditioning or prefix control advances.
5. Start the controller from its declared initial state and evaluate for seven days in SZ_Air and
   MZ_Air or five days in MZ_Hydro.
6. Stop the same test identity exactly once.

`physical_conditioning.jsonl` is empty under this protocol. The conditioning-prefix identity is
the deterministic identity of an empty stream. Only evaluation rows contribute to
`performance.csv` and `metrics.json`. The verifier checks the initialization time and warm-up,
zero conditioning advances, case-specific evaluation count, continuous test identity, and one
stop.

SZ_Air and MZ_Hydro use raw occupancy for control and public KPIs. MZ_Air uses effective official
occupancy, `[06:00,19:00) AND raw > 0`. Frozen MZ_Air DRL policies receive their registered
raw-binary occupancy input, which is logged separately from public occupancy.

MZ_Hydro declares a source-specific missing occupancy policy from the testcase documentation. An
explicit occupancy JSON `null` in a documented non-occupancy interval resolves to zero; one in a
documented occupied interval resolves to the immediately preceding finite value in the same
forecast series. Each resolution is recorded and independently reclassified by the verifier.
Missing weather, price, time, state, or undeclared occupancy inputs fail closed.

BOPTEST requests remain single-attempt. Only an OpenAI-compatible model request may use the
registered bounded transient-connection recovery, and no physical advance or action occurs
between identical wire attempts. Initialization, advance, test identity, source, secret, artifact
corruption, terminal model transport, or an incomplete lifecycle is `RUN-INVALID` and must not
publish `completion.json`.

A syntactically invalid model response is recorded without retry and deterministically contained.
If the full physical lifecycle and every execution-integrity check remain healthy, the run may
publish an `EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED` completion; that class is not a clean
`RELEASE-PASS`.
