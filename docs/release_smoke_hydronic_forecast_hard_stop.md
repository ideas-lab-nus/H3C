# Hydronic release-smoke forecast hard stop

Status: diagnosed after the failed MZ_Hydro deterministic baseline on
2026-08-27. No subsequent release-smoke run is active or authorized by this
record.

Post-diagnosis correction: MZ_Hydro formal evaluation is five days. References
below to a seven-day formal forecast describe the broader diagnostic scan, not
the current case protocol. See
`formal_hydronic_five_day_protocol_preregistration.md`.

## Preserved execution facts

The deterministic baseline started from source commit
`d935b89562d50685827f53038c607a4f722056b1` in the fresh output directory
`outputs/runs/release-6h/MZ_Hydro/20260827T055730263944Z-816decc18a2f`.
The process exited without `completion.json`; no model request was made and no
later arm started. Its dedicated heartbeat is paused and the serial execution
lock is absent.

The BOPTEST worker log binds this run to test
`8653c66a-66e8-4f72-a41f-deabec565c8b`. The worker initialized the test at
`18403200` seconds with a `604800` second server warm-up, served the forecast,
accepted stop, and marked the test complete. The output manifest says
`initialize_count: 0` because the runtime previously recorded initialization
only after forecast validation. That manifest is preserved as failed evidence;
it must not be edited to match the later diagnosis.

## Root cause

The registered forecast spans `18403200` through `19094400` seconds at
900-second intervals. Both the local BOPTEST source asset and the copy embedded
in `multizone_office_simple_hydronic.fmu` contain empty values for both
`Occupancy[nZ]` and `Occupancy[sZ]` at these in-window timestamps:

| Timestamp (s) | Forecast index | Source row |
|---:|---:|---|
| 18429300 | 29 | `18429300,,` |
| 19031400 | 698 | `19031400,,` |

BOPTEST returns these missing values as JSON `null`. The H3C client attempted a
bare `float(null)` conversion and raised an unlabelled `TypeError`. The profile
mapping, forecast point names, start day, server warm-up, conditioning length,
and interval match the registered configuration; this is not a case-name
routing error.

H3C must not coerce these values to zero, forward-fill them, or silently omit
occupancy. The first missing point is directly inside vanilla conditioning, and
the second is also inside the following evaluation-day forecast. Either
substitution would change the physical input and occupancy routing contract.

The installed BOPTEST checkout is clean for this file. Both missing rows are
tracked at `HEAD`, and `git blame` attributes them to upstream commit
`2cb00caea8aa3f899265b0cc587a7fd7051778db` (`Corrected occupancy profile`).
The official BOPTEST release notes describe that update as a corrected occupancy
count file that changes the occupancy forecast. Replacing its blanks with values
from the parent commit would therefore create a local test-case fork, not restore
an accidentally dirty checkout.

## Bounded diagnostic correction

The client now validates every returned forecast value and raises a
single-attempt `TransportError` naming the exact point and index. The physical
protocol validator gives the same location for fake or alternative physical
clients. The runtime also records a successful initialize immediately after the
validated initialize response, before requesting the forecast, so a later
forecast hard stop retains truthful initialize/stop lifecycle counts.

Direct unit and fake-service integration tests cover the exact missing-value
location, one successful initialize, one stop, zero conditioning advances, one
transport error, no completion marker, and strict serial hard stop. These
changes improve failure evidence only. They do not repair or reinterpret the
external BOPTEST data and therefore do not make another physical attempt viable.

## Decision boundary

Continuing MZ_Hydro requires a new framework or physical-data decision, such as
changing the external test-case asset, selecting a different registered
physical window, or declaring a missing-occupancy policy. None is authorized by
the earlier fresh arm-zero recovery approval. The preserved run must not be
resumed or retried, and the remaining release-smoke sequence stays stopped until
the user chooses an input contract.

An exhaustive read-only scan of the installed annual occupancy asset found that
only evaluation start days 172 and 173 have a fully finite union of the required
seven-day conditioning forecast and seven-day formal-evaluation forecast,
including their forecast tails. Day 173 is the stronger configuration-only
candidate: its evaluation week has outdoor temperature mean `18.86 °C` and
maximum `28.11 °C`, compared with `16.51 °C` and `22.80 °C` for the registered
day 220 week. It preserves raw official occupancy without imputation and remains
a cooling-relevant window, but it changes the frozen case identity and golden
fixture. It therefore requires explicit user approval, a transparent
preregistration amendment, new run identities, and fresh execution.

The recommended choice is to change only the MZ_Hydro evaluation start day from
220 to 173. Declaring an imputation policy or patching the official test-case
asset is not recommended because either would invent occupancy values that can
alter both vanilla conditioning and Agent routing.

## Subsequent correction and superseding user decision

The recommendation above is preserved as the decision boundary before the
user's later ruling; it is no longer current. Read-only inspection subsequently
found that the old successful day-220 runtime replaced every forecast `None`
with `0.0` after the client returned the server payload. The old run therefore
does not prove that the server returned a finite value. It proves that the
missing value at 06:30 was silently resolved to zero.

Docker inspection also proves that the old run and current smoke attempt used
the same localhost service, live containers, and image identities. The issue is
not a changed BOPTEST server. The user has kept day 220 and authorized a narrower
occupancy-only contract: documented non-occupancy nulls resolve to zero, while
documented occupied nulls use the immediately preceding finite value in the same
series. The frozen owner, evidence, gates, and continuation boundary are in
`release_smoke_hydronic_occupancy_recovery_preregistration.md`.
