# Reproducing the paper

This guide maps the experiments in *Causality-Constrained Hierarchical LLM Agents for
Online Rule Adaptation in Building HVAC Control* to the public research artifacts. It
distinguishes configuration reproduction, fresh physical reruns, and verification of the
reported processed results.

## Artifact versions

Use the release commit or tag associated with this guide. The H3C Git history intentionally retains every
source commit recorded by the 81 completed Agent trajectories:

| Completed trajectories | Recorded source commit |
|---:|---|
| 3 | `1058f958438e40e23bbbdcd85a2d4603ce652a1d` |
| 1 | `8becfad87d0acf6f91a687879c3da7eff5847a45` |
| 36 | `35b382bac6b7cfc3a8eb6b3f043a101b490fcf8c` |
| 5 | `bd6701e13724948c3a0c37d74cd443dd1f7d68cb` |
| 36 | `f4b272f055e3daae296e8c1b7d5c180ef34af23f` |

The five source commits record the exact code identities used by the completed trajectories.
Several later commits contain control-neutral transport or runtime-state publication fixes, but
the release does not infer method equivalence from commit ancestry alone. Each released row
therefore retains its actual `source_commit`; directory names from the original campaign are not
used as source identity.

Companion artifacts own the two trained baselines:

- [h3c-drl-training](https://github.com/wlxin-nus/h3c-drl-training) owns PPO/MAPPO training and
  formal DRL evaluation;
- [building-mpc-training](https://github.com/wlxin-nus/building-mpc-training) owns ARX
  identification, hierarchical MPC validation, and the frozen MPC models used in the paper.

## Exact Agent matrix

One repetition contains nine configurations for each of `SZ_Air`, `MZ_Hydro`, and `MZ_Air`.
`h3c suite paper-agent` returns these 27 Agent plans in case-major order. It contains no RBC,
DRL, or MPC baseline arms.

| Offset within each case | Paper label | Change from the standard configuration |
|---:|---|---|
| 0 | `STANDARD` | `k=1`, confirmed graph, causal layer on, coordination on, occupancy-routed thinking |
| 1 | `B1_WM0` | no completed-hour memory (`k=0`) |
| 2 | `B2_WM2` | retain two completed-hour records (`k=2`) |
| 3 | `B3_WM3` | retain three completed-hour records (`k=3`) |
| 4 | `B4_CausalOff` | remove Agent-visible causal context and causal proof |
| 5 | `B5_MissingSolarZoneEdge` | remove the confirmed solar-irradiance-to-zone-temperature edge |
| 6 | `B6_EdgeTiming` | change that edge from immediate to delayed in the air cases and from delayed to immediate in `MZ_Hydro` |
| 7 | `B7_CoordOff` | remove the Orchestrator and shared Budget |
| 8 | `B8_NoThinking` | disable thinking for every Agent call and use temperature zero |

The paper reports three independent repetitions (`R01`, `R02`, and `R03`) of every plan, giving
81 completed Agent trajectories. The repeat label is analysis metadata rather than part of the
method identity, so repeated executions of the same plan intentionally share the same deterministic
configuration identity.

Preview the exact matrix without external calls:

```console
h3c suite paper-agent
h3c suite paper-agent --arm-index 0
h3c suite paper-agent --arm-index 26
```

The case-major arm ranges are 0--8 for `SZ_Air`, 9--17 for `MZ_Hydro`, and 18--26 for
`MZ_Air`. Commands are dry plans unless `--execute` is supplied.

## Frozen physical and model contract

| Item | Paper contract |
|---|---|
| Control interval | 900 s |
| Forecast horizon | four 15-minute steps |
| Internal BOPTEST warm-up | seven days |
| Original BOPTEST deployment | exact container-image and FMU identities are not included in this processed release |
| `SZ_Air` evaluation | day 203, 168 h, 672 steps |
| `MZ_Hydro` evaluation | day 220, 120 h, 480 steps |
| `MZ_Air` evaluation | day 199, 168 h, 672 steps |
| Online model | `deepseek-ai/DeepSeek-V4-Flash-0731` through the registered Baseten provider |
| Structured output | strict JSON Schema |
| Occupied or occupied within one hour | low reasoning effort; temperature and `top_p` omitted |
| Otherwise | thinking disabled; temperature `0`; `top_p=1` |
| Transient model retry | at most two retries after the initial request, with 1 s and 2 s backoff |

The exact values remain machine-readable in `configs/cases`,
`configs/experiments/runtime.json`, `configs/experiments/suites.json`, and
`configs/graphs/mutations.json`.

## Fresh physical reruns

Fresh execution requires an independently deployed BOPTEST service and an authorized model
endpoint. Follow the [official BOPTEST deployment guide](https://ibpsa.github.io/project1-boptest/docs-userguide/getting_started.html)
for the simulator service. The paper matrix uses the default `baseten-deepseek` provider, so set
`H3C_BOPTEST_ENDPOINT` and `BASETEN_API_KEY` in the ignored local `.env`. The `H3C_MODEL_ENDPOINT`
and `H3C_MODEL_API_KEY` variables apply only when selecting the alternate `deepseek-official`
provider. Inspect the dry plan, and execute one independently supervised arm at a time:

```console
h3c suite paper-agent --arm-index <0-26> --execute
```

Every physical arm must use a fresh BOPTEST test identity and a fresh output directory. Do not
combine partial runs or rerun a completed arm selectively because of its performance. Model calls
can incur external charges. No command in CI uses `--execute`.

The processed release does not contain enough deployment metadata to recreate the original
BOPTEST service bit for bit. Exact floating-point trajectories are therefore not guaranteed across
BOPTEST deployments, provider service conditions, or future model revisions. Record the repository
commit, resolved plan, BOPTEST version/image, model endpoint identity, and completion evidence for
every new run.

## Verify the released results

Use a full-history Git clone because the verifier confirms that all five recorded run-source
commits are reachable from the release. For a shallow clone, run `git fetch --unshallow` before
verification; a GitHub-generated source archive does not contain the required Git history.

The paper-result package is under `reference_results/paper_2026`. Verify its byte identities, row
counts, and recorded source history with:

```console
python tools/verify_paper_reference_results.py
```

The released CSV files contain the 81 Agent-run metrics, their 27 group summaries, main
cross-method statistics, and the source data for the temporal rule-adaptation figure. The verifier
recomputes the published summaries and accounting relationships from these processed tables. They
are not substitutes for the raw model messages or simulator trajectories, so they do not support
an independent recomputation of physical metrics from raw trajectories. See
[Data availability](data_availability.md) for the exact boundary.

## Reproduce the cross-method comparison

1. Verify or rerun the H3C Agent matrix using this repository.
2. Train and evaluate seeds `42`, `1337`, and `2026` for the five PPO/MAPPO tasks using the DRL
   repository.
3. Verify the frozen MPC suite or run a new identification campaign using the MPC repository.
4. Compare only complete trajectories with the same case, evaluation window, physical input
   boundary, reward definition, occupancy interpretation, and cooling-setpoint bounds.
5. Report the deterministic RBC and eRBC references as single trajectories. The paper evaluates
   MPC three times; its deterministic repetitions are identical and therefore have zero sample
   standard deviation. Report Agent, PPO, and MAPPO results as the mean and sample standard
   deviation over three runs.
