# BOPTEST status response compatibility preregistration

## Observed failure

The local BOPTEST service returns `GET /status/{testid}` as the top-level JSON string
`"Running"`.  The runtime currently rejects every top-level non-object before the
status owner can validate it, so a selected run stops before initialization or any
model call.  Current service documentation also permits the object envelope whose
`payload` is the status.

## Frozen mechanical change

- Only the BOPTEST status request may accept a top-level JSON string.
- Accepted status values are exactly `Running` and `Queued`.
- The documented object form remains accepted only when its `payload` is exactly one
  of those two strings.
- Every other endpoint continues to require a JSON object.
- Other strings, scalar values, arrays, missing payloads, nested/non-string payloads,
  and unknown status values fail closed.

This changes transport decoding only.  It does not change queue policy, initialization,
physical execution, model calls, prompts, or experiment methods.  No API or BOPTEST call
is authorized by this implementation task.

## Direct gates

Unit tests exercise both accepted wire forms, reject all other status forms, and prove
that the generic JSON request owner still rejects a top-level `"Running"` response.
