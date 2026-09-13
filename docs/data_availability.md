# Data availability

## Included in this repository

- H3C source code, case profiles, prompts, confirmed causal graphs, and deterministic validation
  contracts;
- offline semantic-mapping and human-in-the-loop causal-graph workflows;
- frozen legacy inference assets retained as compatibility fixtures for the baseline runtime;
- unit, integration, contract, and offline verification tests;
- processed paper-result tables under `reference_results/paper_2026`.

The processed result package contains no credentials, private model endpoints, raw natural-language
model messages, BOPTEST test identifiers, machine-local paths, or unpublished reviewer material.

## Companion repositories

- [h3c-drl-training](https://github.com/wlxin-nus/h3c-drl-training) provides PPO/MAPPO training,
  evaluation, and DRL reference results;
- [building-mpc-training](https://github.com/wlxin-nus/building-mpc-training) provides ARX model
  identification, hierarchical MPC validation, and the frozen MPC model suite.

The companion repositories, rather than the legacy compatibility fixtures bundled here, own the
paper's DRL and MPC training artifacts.

## External dependencies

BOPTEST test cases, weather files, and simulator services are governed by the BOPTEST project and
are not redistributed here. The online Agent experiments also require access to the model named in
the paper protocol. Provider availability, endpoint behavior, and pricing can change independently
of this repository. The exact container-image and FMU identities of the original BOPTEST
deployment are not included in the processed release, so a fresh run is a protocol reproduction
rather than a bit-for-bit replay of the published trajectories.

## Not included

Raw model-service request/response records, private endpoints, credentials, machine-local logs, and
the complete raw simulator trajectory archive are not committed. They may contain operational or
service metadata that cannot be published safely. Subject to institutional and provider
restrictions, additional research records can be requested from the corresponding author.

The released processed tables support audit of the paper values and regeneration of the reported
summaries. A fresh end-to-end rerun requires the external services and versioned environments
described in [Reproducing the paper](paper_reproduction.md).
