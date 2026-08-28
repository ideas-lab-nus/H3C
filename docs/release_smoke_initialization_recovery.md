# Release-smoke initialization recovery

Status: registered after the failed initialization attempt and before any fresh
recovery attempt on 2026-08-27.

## Preserved failure

Release-smoke arm zero was invoked once from source commit
`18990ca14a5c29630e54c6c52e731d800f7c2429`. It created the fresh directory
`outputs/runs/release-6h/SZ_Air/20260827T053539357924Z-e71562cff4b2` and exited
before initialization. The directory has no completion marker. Its manifest
records zero model calls expected, one transport error, zero successful
initializations, and zero stops. The execution lock is absent after exit. No
later arm was started.

The process returned in about three seconds, before a run heartbeat could be
created. It did not obtain a physical test identifier and did not send a model
request. This directory is immutable failed evidence and must never be resumed,
deleted, or reused.

## Root cause and bounded repair

Read-only service checks showed that `bestest_air` is registered and all six
BOPTEST containers are running. The BOPTEST web log tied the failed select to an
empty-body JSON parse error. The client sent `Content-Type: application/json` on
requests with no payload, including testcase selection and stop, even though the
body was absent.

The only permitted repair is request framing: omit the JSON content-type header
when payload is absent, while retaining JSON encoding and content type for every
request that has a payload. A direct request-shape test must fail if an empty-body
request again claims to contain JSON. No profile, physical timeline, controller,
Prompt, model contract, graph, memory, validation, assurance, metric, matrix, or
acceptance rule may change.

## Fresh recovery boundary

Commit the bounded repair and this recovery registration, rerun the complete
offline gates from a clean HEAD, and repeat arm zero once in a new directory. The
recovery is a fresh infrastructure run, not an HTTP retry and not a continuation
of the failed workspace. If initialization fails again, stop without another
attempt. If arm zero completes and verifies, resume the original preregistered
sequence at arm one. All original strict-serialization, heartbeat, evidence,
inspection, continuation, and hard-stop rules remain unchanged.
