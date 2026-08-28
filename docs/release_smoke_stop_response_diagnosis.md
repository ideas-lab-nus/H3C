# Release-smoke stop-response diagnosis

Status: recorded after the single initialization-recovery run and before any
further physical attempt on 2026-08-27.

## Preserved second failure

The one allowed fresh recovery of release-smoke arm zero ran from
`40253479a32c5ab7d7809fe4d5e65f457eb90edc` in
`outputs/runs/release-6h/SZ_Air/20260827T054035464206Z-187648942a76`. It used one
fresh physical test, completed 672 vanilla-conditioning advances and all 24
six-hour evaluation steps, then exited without completion because the client
tried to JSON-decode the successful stop response.

The immutable failed manifest records one initialization, zero acknowledged
stops, one transport error, and zero retry, fallback, or secret-exposure counts.
The evidence contains 672 conditioning rows, 24 performance rows, 24 zone-step
rows, six hourly-decision rows, and zero model calls. Its pre-completion verifier
passes evaluation counts, action assurance, deterministic settlement, call
counts, causal omission, and coordination omission; it fails lifecycle, failure
counters, and final replay publication as expected. No later arm was started.

The dedicated heartbeat `h3c-release-smoke-arm-0` was paused immediately after
the process exit. The execution lock is absent. A targeted worker-log check
confirms that test `ab12797c-3e1a-4416-a6e8-14068ed7f114` received stop and is
complete, so no physical job remains active.

## Bounded code correction

The client already validates the HTTP status. BOPTEST's stop operation returns a
successful non-JSON body, while all state-bearing operations return JSON. The
bounded correction lets only the explicit stop call ignore a non-JSON success
body; JSON remains mandatory everywhere else. A direct unit test freezes this
exception. No method, Prompt, profile, timeline, model request, graph, memory,
settlement, assurance, metric, matrix, or acceptance rule changes.

The previous recovery registration allowed only one fresh physical recovery.
Therefore this code correction may be implemented and verified offline, but no
third arm-zero run or later arm is authorized by that registration. A new user
authorization is required before another fresh physical attempt.
