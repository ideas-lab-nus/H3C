# Generated outputs

Generated artifacts are intentionally separated from source code and ignored by Git.

```text
outputs/
├── runs/<suite>/<case>/<run_id>/
├── reports/<suite_id>/
├── offline/<case>/<workflow_id>/
└── baselines/
    ├── runs/<suite>/<case>/<run_id>/
    └── reports/<report_id>/
```

## Online H3C runs

A completed online run publishes `completion.json` last, after its declared streams, metrics,
verification, and current-output secret scan. Model wire attempts are separate from logical Agent
calls so a recovered transient transport attempt does not look like another control decision.
See [the run-artifact contract](../docs/run_artifacts.md).

Batch runs may first publish `collection_complete.json` after the stopped physical
lifecycle passes the fast collection gate. This means
`COLLECTION-COMPLETE / FULL-AUDIT-PENDING`, releases the physical lock, and
freezes runtime evidence; it is not a valid-result marker. The zero-network
`h3c finalize` command later runs one full audit and publishes
`verification.json` and `completion.json`.

An evidence-consistent physical lifecycle may be classified
`EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED` when control execution is healthy but one or more model
outputs violate their registered contract. `RUN-INVALID` means execution integrity is not
established and must not publish `completion.json`.

After a terminal model-transport failure, the finalization path performs the real secret scan,
freezes the available counters, and writes partial `metrics.json` and fail-closed
`verification.json`. No `completion.json` is published.

## Offline onboarding

Offline workspaces hold mapping/causal proposals, real human review events, checkpoints,
provenance and the final confirmed graph. Interrupted workspaces intentionally remain incomplete
and may resume only under the same workflow identity. They are never physical-run evidence.

## Independent baselines

RBC and frozen-DRL evaluation directories contain:

- `resolved_config.json`, `manifest.json`, `forecast_inputs.json` and an empty conditioning stream;
- `performance.csv`, per-zone `actions.jsonl` and controller diagnostics;
- native BOPTEST KPIs, shared physical metrics, verification and atomic final completion.

DRL adds checkpoint identity, observations and policy-inference streams. Baselines never create
fake Agent, causal, program, budget or action-assurance evidence.

Reports contain Markdown, JSON and CSV comparisons plus per-run temperature, setpoint, PMV,
occupancy and power figures. A failed or degraded run is retained in place; it is not silently
rewritten as a clean result.
