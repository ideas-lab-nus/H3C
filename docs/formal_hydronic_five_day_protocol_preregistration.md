# Hydronic five-day formal protocol preregistration

Superseded for the new 2026-08-28 comparison by
`rationale_contract_and_mz_hydro_7day_preregistration.md`. This historical
preregistration and every result produced under it retain their original
five-day meaning and are not rewritten.

Status: frozen on 2026-08-27 after the user's protocol correction and before
changing the implementation or making another BOPTEST or model call.

## Decision and historical basis

MZ_Hydro formal evaluation starts at day 220 and lasts five consecutive days,
or 120 hours and 480 fifteen-minute steps. The other two cases retain seven-day
formal evaluation. The reason is part of the established case protocol:
MZ_Hydro is occupied on the five weekdays and fully unoccupied on the weekend.

This restores the preserved production protocol rather than introducing a new
performance window. Read-only owners independently record the same contract:

- `Revision1/Phase2.5_Step2.5_D1_Report.md` specifies 7/5/7 evaluation days and
  480 MZ_Hydro rows;
- `Revision1/Phase2.5_Step1_Baseline_Report.md` records 480 MZ_Hydro rows;
- `notes/2026-08-18_hydro_thinking_arms_preregistration.md` fixes MZ_Hydro at
  day 220 and 120 hours;
- `notes/PROJECT_DECISIONS.md` already records the earlier 120-hour/480-step
  evaluation-only decision.

The user's current correction supersedes the clean-framework assumption that
all three formal evaluations last seven days. It does not alter prior raw
evidence or silently rewrite earlier preregistrations.

## Single protocol change

Only `configs/cases/mz_hydro.json` changes its
`protocol.formal_evaluation_days` value from seven to five. All other registered
properties stay fixed:

- MZ_Hydro `evaluation_start_day` remains 220;
- server warm-up remains seven days;
- explicit vanilla conditioning remains seven days on the same test id;
- occupied/unoccupied vanilla setpoints remain 25/30 °C;
- `release-6h` still evaluates every case for six hours;
- SZ_Air and MZ_Air formal evaluation remain seven days;
- the documented hydronic occupancy missing-value policy is unchanged;
- model, Prompt, causal graph, program, memory, coordination, action assurance,
  API, BOPTEST assets, Python, and thermal-comfort package are unchanged.

The case configuration remains the behavior owner. Production code may validate
the declared supported duration but must not branch on a case name.

## Derived matrices and identities

The formal matrix remains three deterministic baselines and 24 unique Agent
identities. Its expected call total becomes 16,824. For MZ_Hydro, each
coordinated Agent arm expects 480 calls and the independent-coordination arm
expects 360; the MZ_Hydro baseline remains zero-call. The release matrix remains
three zero-model baselines, ten Agent arms, and 372 expected calls because its
evaluation duration is explicitly six hours.

Changing tracked configuration and source identity invalidates the earlier
release-smoke sequence as a single final-source release gate. The completed
SZ_Air and MZ_Hydro baselines and the interrupted MZ_Air directory remain
preserved as superseded evidence. After the new implementation is committed and
all offline gates pass, release smoke restarts at arm zero using fresh tests and
continues strictly serially through arm twelve. This is a declared
method-identity restart, not a retry of a failed outcome.

## Required offline gates

Before any new physical or model call:

1. profile loading must prove formal durations 7/5/7 and day 220 for MZ_Hydro;
2. formal dry planning must prove three baselines, 24 unique Agent identities,
   correct per-case evaluation hours, and 16,824 calls;
3. release dry planning must remain 13 runs and 372 calls;
4. verifier tests must prove 480 formal MZ_Hydro rows while keeping 672 vanilla
   conditioning advances and one initialize/one stop;
5. pytest, Ruff, strict mypy, config rejection, golden fixtures, identifier scan,
   secret scan, nested-repository scan, and Git whitespace checks must pass;
6. the same BOPTEST container, image, endpoint, and source identities must be
   rechecked before physical execution.

No formal suite is authorized by this correction. Release-smoke retry,
transport, fallback, and secret-exposure counts remain zero.
