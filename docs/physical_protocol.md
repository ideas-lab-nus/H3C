# Physical protocol

Every registered arm uses a fresh BOPTEST selection and is executed strictly
serially.

The lifecycle is fixed:

1. Select the configured testcase and obtain one test id.
2. Configure dynamic electricity price and a 900-second step.
3. Initialize once at seven days before the evaluation boundary while requesting
   a seven-day server warm-up.
4. Advance the same test id for seven explicit vanilla-conditioning days. The
   occupied cooling setpoint is 25°C and the unoccupied setpoint is 30°C. No Agent
   is constructed or called in this phase.
5. Carry the physical boundary state into evaluation while starting the Agent at
   the initial program, version zero, an empty accepted ledger, and empty working
   memory.
6. Evaluate for the case-declared formal duration: seven days for SZ_Air and
   MZ_Air, five occupied weekdays for MZ_Hydro, or six hours for every
   `release-6h` arm.
7. Stop the same test id exactly once.

Only evaluation rows contribute to `performance.csv` and `metrics.json`.
Conditioning has its own complete `physical_conditioning.jsonl` stream. The
verifier checks one initialize, 672 conditioning advances, a continuous test id,
the method-derived evaluation row counts, and one stop.

MZ_Hydro keeps evaluation day 220 and declares one source-specific missing
occupancy policy from the testcase documentation. An explicit occupancy JSON
`null` in a documented non-occupancy interval resolves to zero; one in a
documented occupied interval resolves to the immediately preceding finite value
in the same forecast series. Raw and resolved conditioning occupancy are logged
separately. Every resolution is recorded in `timing.jsonl`, counted in the
manifest, and independently reclassified by the verifier. Missing weather,
price, time, state, or undeclared occupancy values still fail closed.

The release recovery uses the same localhost BOPTEST web and worker containers
and image identities as the preserved old day-220 run. The old runtime's broad
forecast `None`-to-zero conversion is not migrated; only the declared occupancy
rule above is permitted.

BOPTEST requests remain single-attempt. Only an OpenAI-compatible model request
may use the registered bounded transient-connection recovery, and no physical
advance or action occurs between its identical wire attempts. Initialization,
advance, test-id, source, secret, artifact corruption, terminal model transport,
or an incomplete lifecycle is `RUN-INVALID` and must not publish
`completion.json`. A syntactically invalid model response is recorded without a
retry and deterministically contained. If the full physical lifecycle and every
execution-integrity check remain healthy, the run may atomically publish an
`EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED` completion; that class is never a
clean `RELEASE-PASS`.
