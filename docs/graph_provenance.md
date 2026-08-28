# Human-confirmed graph provenance

All canonical graphs use schema `confirmed_causal_graph`, version 1. Each stores
the confirmer role, confirmation date, source list, nodes, qualitative signed
edges, zone topology, and stable edge identities derived from complete edge
content. Timing is qualitative (`Immediate` or `Delayed`); no numeric lag or
cooldown is inferred.

## sz_air

- Profile: `SZ_Air`
- Confirmation: project owner, 2026-08-05
- Sources: the frozen project causal-rule artifact; BOPTEST BESTEST air testcase
  documentation; the project topology review consolidated before migration.

## mz_hydro

- Profile: `MZ_Hydro`
- Confirmation: project owner, 2026-08-05
- Sources: the frozen project causal-rule artifact; BOPTEST simple hydronic office
  testcase documentation; the project topology review consolidated before
  migration.
- Canonical fact relevant to sensitivity planning: the
  `solar_irr → zone_temp` edge is already tagged `Delayed`.

## mz_air

- Profile: `MZ_Air`
- Confirmation: project owner, 2026-08-05
- Sources: the frozen project causal-rule artifact; BOPTEST simple air office
  testcase documentation; the project topology review consolidated before
  migration.

The graph CLI separates preparation, proposal, validation, human confirmation,
and declared single-difference derivation. Preparation is only a machine
candidate: a human or authorized external process must edit/review the structured
graph before proposal and explicitly approve it before confirmation. Merely
running the commands is not human review. Missing edges cannot be cited. A timing
tag change changes the stable edge identity. Derived graphs embed the exact
mutation alongside the unchanged human confirmation and sources.

The registered timing sensitivity preserves each canonical graph and changes one
qualitative tag in the direction available for that profile. SZ_Air and MZ_Air
derive Immediate to Delayed; MZ_Hydro derives Delayed to Immediate. The profile
selection is declarative in the suite contract rather than a case-name branch in
control code.
