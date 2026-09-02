# H3C final framework release (2026-09-02)

## Release boundary

The user selected the generic H3C implementation at method source commit
`8b82bb967f583b64d1a885eb632659efe4485660` as the final framework. This release note and its
repository publication do not modify the Prompt, controller, causal method, Budget, Safety,
reward, model settings, working-memory behavior, or long-term-memory default.

The production defaults are:

- Baseten `deepseek-ai/DeepSeek-V4-Flash-0731` with provider-native strict JSON schema;
- `occupancy_routed` low thinking;
- one completed hour of structured per-zone working memory;
- long-term memory off, while retaining the optional CLI interface for reproducibility;
- causal, coordination, Budget, program validation, and action assurance enabled;
- bounded identical-payload retries for registered transient Provider errors;
- fresh-run/fresh-test physical replay recovery only for eligible control-neutral failures.

## First usable formal result

The MZ Hydro result is a real usable formal trajectory, not a diagnostic-only prefix:

- run: `outputs/runs/resume-run/MZ_Hydro/20260902T023130261026Z-3ac40543e425`;
- run identity: `3ac40543e425bf0d3095adc8a19ae483db6b5b61165f3d2c1f77636c211df0f0`;
- fresh BOPTEST test: `d95c75a3-b28f-4421-955c-9b415245ac27`;
- 120 formal hours, 480 physical advances, and 480 logical Agent calls;
- `trajectory_status=EXECUTION-HEALTHY`;
- `resume_replay_integrity=true`;
- `performance_status=REWARD-PMV-PASS`;
- `classification=EXECUTION-HEALTHY-MODEL-CONTRACT-DEGRADED`.

| Metric | H3C | Frozen eRBC | H3C minus eRBC |
|---|---:|---:|---:|
| reward (higher is better) | -170.475035 | -179.354184 | +8.879148 |
| cost | 110.047367 | 118.922079 | -8.874712 |
| energy (kWh) | 720.471351 | 778.326369 | -57.855018 |
| discomfort (zone-h) | 11.75 | 0.00 | +11.75 |
| discomfort (PMV-h) | 0.2875 | 0.0000 | +0.2875 |
| occupied peak absolute PMV | 0.59 | 0.47 | +0.12 |
| setpoint TV (C) | 114.60 | 100.60 | +14.00 |
| direction reversals | 129 | 20 | +109 |

The registered hard criteria pass: reward is strictly higher than frozen eRBC and occupied peak
absolute PMV is at most `0.70`. Zone-h and PMV-h are engineering diagnostics and do not need to
beat eRBC item by item. Stability remains weaker than eRBC and must be reported rather than hidden.

The model contract is degraded by one Orchestrator fallback, five schema/model-output rejections,
six length finishes, role-contract audit degradation, and incomplete usage evidence. Independent
verification nevertheless reports `execution_integrity=true` and `completion_eligible=true`.

## Generated evidence package

The complete 19-file terminal run was copied byte-for-byte, with SHA-256 equality checked, to:

```text
outputs/reports/final-framework-20260902/MZ_Hydro/evidence/
```

Generated evidence is ignored by Git under the repository output contract. It includes the raw
trajectory, Agent and transport evidence, program decisions, working memory, metrics,
verification, manifest, resolved configuration, and atomic completion marker. Failed source and
intermediate recovery directories remain preserved separately and are not presented as usable
formal results.

## Next confirmation arms

SZ Air and MZ Air must use the same generic framework and independent fresh tests. No case-specific
Prompt, parameter, rule, KPI, or acceptance change is permitted. Their terminal evidence must be
verified and reported from their own generated output directories.
