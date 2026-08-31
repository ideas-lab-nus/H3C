# H3C Context View Consistency Report

## One fact owner, three views

Every request is compiled from one normalized typed context into:

1. `agent_view`: clocked, compact model input;
2. `human_view`: the same semantic rendering used by the bilingual complete-interval documents;
3. `audit_view`: hashes, field manifest, internal call coordinates and all canonical temporal-coordinate paths.

`ContextBuilder.build()` decodes every compact section and fails unless it equals the normalized canonical input. `compile_working_memory()` independently reconstructs the original four-action records and applies the same equality gate.

## Verified properties

- Zero, `false`, empty lists, Unicode and delimiter-containing text survive normalization and decode.
- Missing values are omitted rather than replaced by `null`, `N/A`, zero or an empty table.
- Common extraction compares identical JSON pointers at identical structural depth; coincidentally equal values under different owners are never merged.
- Zone order, interval order and all internal sequence orders remain stable.
- Internal hour/step/sample counters appear in audit data, not in Agent input.
- Action and outcome clocks are paired at exactly 15-minute offsets; crossing midnight uses `next day HH:MM` without a date or year.
- The raw forecast and its deterministic summary both remain available under separate labels.
- A current-state value that conflicts with the previous completed-interval endpoint fails closed.
- Repeated site cost/energy or Budget owners that disagree fail closed.
- Table cells are scalar; nested programs and patches remain structured objects outside table cells.
- Memory-off prompts, input and output contracts contain no long-term slot, revision, CRUD operation or memory reference.
- `values_shared_by_all_rows` and `values_constant_within_each_zone` are self-describing; stale `common`, `constant_by_zone` and `common_when` labels are absent.
- Orchestrator model input excludes previous natural-language rationale while the canonical/audit view retains it.
- Reflector receives only completed-action-time outdoor temperature, irradiance, price and comfort-headroom history; no future or cross-zone evidence is introduced.
- Documentation Lesson pointers resolve against canonical completed-interval records and are not part of the model wire.
- The dynamic reserved cap and causal allocation rule are shared by renderer and validator owners.

## Boundary

No API or physical simulation was run. Final status:

`DATA-LOSSLESS / CONTRACT-ALIGNED / TIME-EXPLICIT / SEMANTICALLY-EXPLICIT / EVIDENCE-CLOSED / BEHAVIOR-UNVERIFIED`
