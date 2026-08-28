# Offline Prompt migration record

## Read-only legacy sources

The migration used these sources only as read-only semantic oracles:

| Role | Legacy source | Source identity |
|---|---|---|
| Semantic Mapping | `Causal_augmented_Hierarchical_Control/agents/agent_a_mapper.py` | nested repository `941e6afbc540c5fb588829ed74a87b6e6a869830`; file SHA-256 `a8d83ffc3bb860cd00ef37447f78a0e1d3ba156d9f3e1463eb135e8bdade615d` |
| Initial causal discovery | `Causal_augmented_Hierarchical_Control/phase0_causal_discovery.py` | nested repository `941e6afbc540c5fb588829ed74a87b6e6a869830`; file SHA-256 `d1e5cc25ec41abf1555f52f00eeab3a2af8fb39b97296da3d63cdf519c0e28b6` |
| Later causal HITL discipline | `Revision1/Phase1.5_Scripts/hitl_rewalk.py` | file SHA-256 `70d34c8fa7a3718ea620869d4a31aee7fd795c42c60a803f0e08f17118990255` |

No legacy file was modified or imported by the new runtime.

## Preserved semantics

The Mapping system Prompt retains the legacy text exactly, including the
“Master Systems Integrator for Smart Buildings” role, Unified Control Layer,
specific BMS points, standardized internal schema, and extract-only scope. Its
dynamic Prompt keeps positive observation/control requirements, all power
meters, `_u`/`_y` naming heuristics, source documentation, and exact point IDs.

The causal Prompt retains the “Building Physics & Thermodynamics Expert” role,
standardized physical names, the prohibition on BMS IDs, setpoint/temperature/
power and occupancy/weather analysis, and previous-proposal plus exact-human-
critique revision semantics.

## Deliberate minimum differences

| Change | Reason |
|---|---|
| Free-form mapping JSON became the strict current mapping schema. | Deterministic membership, role-conflict, and template-merge validation. |
| Free-text arrow parsing became structured graph proposal JSON. | Reuse H3C's graph validator and stable edge ID owner. |
| `Threshold` and unsupported labels were removed. | They are absent from the current runtime graph schema and control chain. |
| Each edge cites only declared source IDs. | Prevent invented provenance; explanations live outside edge identity. |
| Human `input()` loop became Agent Framework `request_info` plus checkpoint/resume. | Real pausable human review with durable pending requests. |
| Mapping `temperature=0.0` and causal `temperature=0.2` were retired. | Both roles now use `reasoning_effort=low`; `temperature` and `top_p` are absent. |
| Framework/SDK automatic retry is disabled. | A network interruption remains an explicit audited resume decision. |

The runtime graph remains `confirmed_causal_graph` schema version 1. Agent
explanations, human feedback, evidence source IDs, and confirmation round are
stored separately in `causal_provenance.json`, so provenance cannot alter a
stable edge ID. Provenance is joined to each edge by that stable ID, never by
proposal list position.

## Golden identity

`tests/fixtures/offline_prompts/golden_hashes.json` freezes initial and revised
system/user render byte counts and SHA-256 identities. The tracked example
document, inventory, Mapping proposal, causal proposal, source texts, and exact
review feedback are the sole representative inputs. Tests render through the
production owners; they do not call a provider or import the legacy runtime.
