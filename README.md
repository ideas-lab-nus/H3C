# Hierarchical Causal-Constrained Control (H3C)

H3C is a reproducible, cooling-only framework for hierarchical building control. It combines
LLM-based coordination, zone-level executable programs, human-confirmed causal constraints,
and a deterministic action-assurance chain. The repository also contains two independent
research surfaces: human-in-the-loop case onboarding and conventional RBC/DRL/MPC baselines.

> **Project status.** The online H3C implementation and the offline onboarding workflow are
> established. Frozen DRL policies and a common short-data linear MPC baseline are included for
> the three BOPTEST cases. Physical commands are dry plans unless `--execute` is explicit.

![Paper-level H3C concept](docs/assets/Figure1_Overview_Framework.jpg)

*This is the paper's conceptual overview. It is not a literal software component diagram and may
contain research concepts that are outside the current release implementation.*

## Three reproducible workflows

| Workflow | Purpose | Entry point |
|---|---|---|
| Online H3C | Orchestrator, zone Executors, Reflector, confirmed graph, budget and action assurance | `h3c run`, `h3c suite` |
| Offline onboarding | Mapping Agent, causal-discovery Agent and real human approval/checkpointing | `h3c offline` |
| Independent baselines | basic RBC, enhanced RBC, frozen PPO/MAPPO and short-data linear MPC | `h3c-baseline` |

Online control uses H3C's deterministic runtime. Microsoft Agent Framework is optional and used
only by offline onboarding. Baselines do not fabricate Agent, causal, program, budget, or
action-assurance logs.

## Installation

Python 3.11 or newer is required. `pyproject.toml` and `uv.lock` are the dependency owners.

```console
# Online H3C and development checks
uv sync --extra dev

# Mapping and human-in-the-loop causal discovery
uv sync --extra offline

# Frozen DRL policies, ARX identification, MPC and figures
uv sync --extra baselines

# Everything needed by contributors
uv sync --extra dev --extra offline --extra baselines
```

Pip users can install from the generated compatibility exports:

```console
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pip install -r requirements-offline.txt
.venv\Scripts\python -m pip install -r requirements-baselines.txt
```

Never place API keys in repository files. Copy `.env.example` only as a local template and keep
the real `.env` ignored.

## Quick start

All planning commands below are read-only until `--execute` is added.

```console
# Resolve one H3C run and the registered H3C suites
h3c run --profile MZ_Air
h3c suite main

# Verify the five frozen inference checkpoints on CPU
h3c-baseline models verify

# Resolve one independent baseline and the full registered benchmark
h3c-baseline run --case MZ_Hydro --controller h-drl
h3c-baseline suite formal-7d

# Verify or report completed baseline artifacts
h3c-baseline verify outputs/baselines/runs/<suite>/<case>/<run_id>
h3c-baseline report outputs/baselines/runs/formal-7d
```

Offline onboarding has two genuine human review pauses and can resume from a checkpoint:

```console
h3c offline discover --spec configs/onboarding/example_spec.json
h3c offline discover --spec configs/onboarding/example_spec.json --reviewer <name> --execute
h3c offline resume outputs/offline/<case>/<workflow_id> --reviewer <name> --execute
h3c offline verify outputs/offline/<case>/<workflow_id>
```

See [offline onboarding](docs/offline_onboarding.md) and the
[operator guide](docs/operator_guide.md) for the full interaction and export contracts.

## Baseline benchmark

Every formal evaluation uses a fresh BOPTEST test identity:

```text
7-day server warm-up
→ same-test-id 7-day vanilla RBC prefix (occupied 25 °C, otherwise 30 °C)
→ 7-day formal evaluation
```

| Case | basic RBC | enhanced RBC | C-DRL | H-DRL | linear MPC |
|---|:---:|:---:|:---:|:---:|:---:|
| SZ_Air | ✓ | ✓ | 1-policy PPO | — | ✓ |
| MZ_Hydro | ✓ | ✓ | 1-policy PPO | 2-actor MAPPO | ✓ |
| MZ_Air | ✓ | ✓ | 1-policy PPO | 5-actor MAPPO | ✓ |

This gives 14 fresh evaluation arms. MPC additionally uses one independent, pre-evaluation eRBC
identification trajectory per case: 7 days for SZ_Air, 5 days for MZ_Hydro, and 7 days for
MZ_Air. Evaluation data never enter identification or model selection.

### Frozen DRL identity

Only inference assets are distributed; training loops, notebooks, optimizers and experiment
trackers are intentionally excluded. Checkpoints were selected from training records, never from
the new formal evaluation.

| Case / method | Checkpoint | Training steps | SHA-256 prefix |
|---|---:|---:|---|
| SZ_Air C-DRL | PPO epoch 297 | 798,336 | `abd5d1adb751` |
| MZ_Hydro C-DRL | PPO epoch 650 | 1,248,000 | `beba50eb178a` |
| MZ_Hydro H-DRL | MAPPO epoch 700 | 1,344,000 | `3644b477c4e0` |
| MZ_Air C-DRL | PPO epoch 281 | 755,328 | `7385e6d9e055` |
| MZ_Air H-DRL | MAPPO epoch 298 | 801,024 | `2b6b1c2c83f4` |

Each load verifies the full SHA-256 and byte count from `models/registry.json`, then performs
deterministic CPU inference under the model's original observation order, normalization,
history/cold-start, residual base and action mapping. The extended Hydro checkpoints are the
user-designated final models, but their original convergence criteria were not fully satisfied;
that limitation is preserved in their model cards.

### Short-data linear MPC

All three cases use the same four-lag, four-step vector ARX structure:

```text
y(k+1) = c + Σ A_j y(k-j) + Σ B_j u(k-j) + E d(k)
```

`y` contains zone temperatures and total power, `u` contains zone cooling setpoints, and `d`
contains outdoor temperature, solar irradiance, occupancy and time encoding. A frozen ridge grid
and chronological validation select one model; SLSQP optimizes a one-hour horizon and applies only
the first action. The objective reuses H3C's cost/energy, occupied-PMV and setpoint-smoothness
terms. Solver failure uses enhanced RBC and marks the arm `METHOD-DEGRADED`.

The identification data are deliberately short and generated by an unexcited eRBC trajectory.
This is a transparent, reproducible reviewer baseline—not a claim of well-tuned MPC. See
[baseline methods and frozen contracts](docs/baselines.md). The first complete registered result
is preserved in the [seven-day baseline result](docs/baseline_formal_7d_result_20260828.md).

## Outputs and metrics

Generated data are ignored under:

```text
outputs/runs/                         # online H3C
outputs/offline/                      # onboarding workspaces
outputs/baselines/identification/     # ARX training/validation and coefficients
outputs/baselines/runs/               # RBC, DRL and MPC trajectories
outputs/baselines/reports/            # tables and time-series figures
```

Baseline runs report cost, energy, reward, discomfort zone-hours, PMV·h, occupied peak PMV,
setpoint total variation, reversals, comfort-band crossings, per-zone trajectories and native
BOPTEST KPIs. These physical metrics use the same calculation owner as H3C. See
[run artifacts](docs/run_artifacts.md) and [`outputs/README.md`](outputs/README.md).

## Repository map

```text
src/h3c/                 online control, assurance, causal graph, runtime and offline onboarding
src/h3c_baselines/       independent RBC, frozen-policy and linear-MPC evaluation
configs/                 cases, experiments, graphs, programs, onboarding and baselines
models/                  frozen DRL checkpoints, registry and model cards
tests/                   unit, integration, contract and golden inference fixtures
docs/                    methods, protocols, migration and operator documentation
outputs/                 ignored generated runs and reports
```

The parser accepts only named, unambiguous, control-neutral wrappers observed in real model
outputs. Every normalized control object still passes the same strict validators; conflicting or
unknown fields fail closed. Rationale text is audit-only, retained in full, and never changes a
control decision solely because it is long.

## Reproducibility, citation and license

- Verify a resolved configuration, source commit, case, controller and model identity before
  comparing runs.
- Do not mix trajectories from different implementation commits or physical prefixes.
- Preserve poor KPI, rejected model output and degraded MPC results; new evidence supersedes
  historical paper tables when protocols differ.
- Cite the accompanying paper, *Causal-augmented Hierarchical LLM Agents for Building Control*,
  when using this research code. Formal bibliographic metadata will be added after publication.

Released code is under the [MIT License](LICENSE). BOPTEST test cases, pretrained checkpoints and
third-party packages remain subject to their respective upstream terms.
