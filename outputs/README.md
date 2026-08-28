# Generated outputs

Generated artifacts are intentionally separated from source code and ignored by Git.

```text
outputs/
├── runs/<suite>/<case>/<run_id>/
├── reports/<suite_id>/
├── offline/<case>/<workflow_id>/
└── baselines/
    ├── identification/<case>/<run_id>/
    ├── runs/<suite>/<case>/<run_id>/
    └── reports/<report_id>/
```

## Online H3C runs

A completed online run publishes `completion.json` last, after its declared streams, metrics,
verification, and current-output secret scan. Model wire attempts are separate from logical Agent
calls so a recovered transient transport attempt does not look like another control decision.
See [the run-artifact contract](../docs/run_artifacts.md).

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

MPC identification directories contain:

- `resolved_config.json`, `manifest.json` and `identification_data.csv`;
- `model_coefficients.npz` and `fit_report.json`;
- native BOPTEST KPIs, verification and atomic final completion.

RBC, frozen-DRL and MPC evaluation directories contain:

- `resolved_config.json`, `manifest.json` and the conditioning trajectory;
- `performance.csv`, per-zone `actions.jsonl` and controller diagnostics;
- native BOPTEST KPIs, shared physical metrics, verification and atomic final completion.

DRL adds checkpoint identity, observations and policy-inference streams. MPC adds copied
identification identity, predictions and solver traces. Baselines never create fake Agent,
causal, program, budget or action-assurance evidence.

Reports contain Markdown, JSON and CSV comparisons plus per-run temperature, setpoint, PMV,
occupancy and power figures. A failed or degraded run is retained in place; it is not silently
rewritten as a clean result.
