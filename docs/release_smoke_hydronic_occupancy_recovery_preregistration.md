# Hydronic occupancy-forecast recovery preregistration

Status: frozen on 2026-08-27 after the failed hydronic deterministic baseline
and before implementation or fresh physical execution.

Post-freeze protocol correction: MZ_Hydro formal evaluation is five days, not
seven. The occupancy rule and six-hour release-smoke acceptance contract below
are unchanged. The later duration ruling and its exact matrix consequences are
frozen in `formal_hydronic_five_day_protocol_preregistration.md`.

## User ruling and invariant

MZ_Hydro keeps `evaluation_start_day: 220`. The user rejected changing its
calendar window and authorized this deterministic rule for an explicit JSON
`null` in a configured occupancy forecast:

- during a documented non-occupancy interval, resolve the value to zero;
- during a documented occupancy interval, use the immediately preceding
  finite value from the same forecast series.

SZ_Air and MZ_Air are unchanged. No weather, price, time, state, or other
forecast field may use this rule.

## Corrected legacy and server facts

The earlier hard-stop note inferred that the old physical service had returned
a finite zero. Read-only inspection corrects that inference. The preserved old
runtime requested the complete forecast and then replaced every returned
`None` with `0.0` before using it. Its physical client itself returned the
server payload unchanged. Therefore the old successful day-220 run does not
prove that the server response was finite; it proves that the old runtime
silently resolved the missing value to zero.

The physical-service environment has not changed between that old run and the
current smoke attempt:

- both used `http://127.0.0.1:80`;
- the active web and three worker containers were created on 2026-08-15 and
  started on 2026-08-20, before the old run on 2026-08-21;
- the same containers and image identities remained active for the current
  attempt;
- the web image is
  `sha256:018f01011e001214012c7cd6e247d982bbc7271174eed4619107ec70153e4eeb`;
- the worker image is
  `sha256:d8cbd03d033965756e8366131f491b4c6ae3124d7d60a56efffc99185f0a45aa`;
- the local BOPTEST source checkout is clean at
  `e818a1c41412c73f35f7d5c12e8a7eae1e9dd8f4`.

Python and thermal-comfort package versions are not part of this recovery
change, by explicit user ruling. H3C keeps its existing application environment.
The old client's multi-attempt transport behavior is also not restored: the
release protocol remains one request attempt with zero retries.

## Documented classification

The BOPTEST testcase documentation defines occupied HVAC time as weekdays from
07:00 through 19:00, with the end excluded, and defines weekends and listed
Belgian bank holidays as unoccupied. The registered conditioning, release-smoke
evaluation, and formal-evaluation union contains these source nulls for both
configured zones:

| Time (s) | Calendar time | Documented class | Deterministic result |
|---:|---|---|---:|
| 18429300 | 2021-08-02 07:15 | occupied | previous value, 50 |
| 19031400 | 2021-08-09 06:30 | unoccupied | 0 |
| 19163700 | 2021-08-10 19:15 | unoccupied | 0 |
| 19377000 | 2021-08-13 06:30 | unoccupied | 0 |
| 19597500 | 2021-08-15 19:45 | unoccupied | 0 |

The old 24-hour day-220 run covered only the second row and resolved it to zero,
which is exactly the new rule for that timestamp. It did not include the new
seven-day common conditioning period and therefore supplies no historical
answer for the first row; the user's occupied-time rule owns that case.

## Bounded implementation

The owner is the MZ_Hydro case configuration, not a case-name branch. The
configuration records the calendar origin, occupied weekdays, half-open daily
window, holiday dates, source, and the two resolution rules. The physical
client preserves an explicit occupancy `null` long enough for that configured
resolver to classify it. All ordinary forecast values remain unchanged.

Resolution fails closed when:

- a missing value belongs to any non-occupancy forecast field;
- an occupancy point has no declared policy;
- an occupied missing value has no finite preceding value in the same series;
- the timestamp cannot be classified by the declared calendar;
- any value is boolean, non-numeric, NaN, or infinite.

Every applied resolution is logged with the source point, forecast phase,
index, absolute time, documented occupancy class, rule, preceding value when
applicable, replacement value, and documentation source. Raw and resolved
occupancy are distinct in conditioning evidence. This creates no Prompt,
causal, coordination, memory, program, budget, or action-assurance channel.
The BOPTEST checkout, FMU, historical run, and failed smoke directory remain
unchanged.

## Frozen gates and continuation

Before another physical call, tests must prove all five timestamps, the
occupied previous-value branch, the unoccupied-zero branch even when the prior
value is nonzero, and fail-closed behavior for every excluded input. A fake
hydronic run must exercise the two release-window nulls, retain raw nulls,
record exactly six zone-level resolution events, complete one initialize,
continuous conditioning and evaluation, one stop, and pass the production
verifier. Corrupting a resolution event must make verification fail.

The full pytest, Ruff, strict mypy, configuration, golden-fixture, matrix,
repository-identifier, secret, nested-repository, and whitespace gates must be
green. The BOPTEST endpoint, live container identities, image identities, and
clean source checkout listed above must then be checked again.

Only after those gates and a clean commit may arm one be restarted in a new
directory. It receives one fresh attempt under the user's existing
release-smoke authorization. If its completion and production verification are
green, continue arms two through twelve strictly serially under the original
matrix and per-arm heartbeat contract. Formal seven-day execution remains
outside scope.
