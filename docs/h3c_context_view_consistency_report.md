# H3C Context View Consistency Report

## Three views, one owner

Every request is compiled from one normalized typed context into:

1. `agent_view`: compact model input;
2. `human_view`: expanded JSON used by the English/Chinese complete-hour documentation;
3. `audit_view`: field manifest plus canonical and compact SHA-256 identities.

`ContextBuilder.build()` decodes every compact section before returning and fails unless the result equals the normalized canonical input exactly. `compile_working_memory()` independently performs the same round trip for reconstructed four-step records.

## Verified properties

- Zero, `false`, empty lists, Unicode, and delimiter-containing text survive normalization and decode.
- Missing values are omitted; they are not replaced by `null`, `N/A`, zero, or an empty table.
- Common extraction compares the same JSON pointer at the same structural depth. Numerically equal values under different semantic paths are never merged.
- Zone order, hour order, sample order, physical-step order, and occupancy-forecast order are stable.
- Conflicting repeated site cost or energy owners fail closed.
- Table cells are scalars. Nested proposal/rule objects remain compact JSON outside table cells.
- The Agent view's step-axis tables explicitly identify hour-start sample 0, post-action samples 1–4, the current sample, action timing, and 15/60-minute intervals.
- Model-facing audit-detail projection is reversible because the proof fields remain in `compact_view` and `audit_view`; it is not a source mutation.
- Memory-off prompts and schemas contain no experience slots, revisions, CRUD operations, or memory references.

## Machine gates

The dedicated compiler and contract tests cover common-row round trips, working-memory reconstruction, owner conflicts, input mutation isolation, single/multi-regime slot eligibility, multi-sentence Lessons, memory-off leakage, prompt goldens, documentation freshness, and all existing output parsers/validators.

This stage does not make a closed-loop behavior claim. Final status:

`DATA-LOSSLESS / CONTRACT-COMPATIBLE / BEHAVIOR-UNVERIFIED`
