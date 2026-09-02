# Operator guide

## Prepare the repository

1. Clone the repository and enter its root.
2. Install the required extras with `uv sync`, or install the exported requirements followed by
   `pip install --no-deps -e .`.
3. Copy `.env.example` to an ignored local `.env` and configure only the required endpoints and
   credentials.
4. Confirm that the Git worktree is committed and clean. Physical execution fails closed when
   tracked or untracked files are present.
5. Run the relevant tests and resolve a dry plan before adding `--execute`.

## Online H3C

```console
h3c run --profile MZ_Air
h3c run --profile MZ_Air --execute
h3c run --profile MZ_Air --defer-full-verification --execute
h3c finalize outputs/runs/<suite>/<case>/<run_id>
h3c verify outputs/runs/<suite>/<case>/<run_id>
h3c report outputs/runs/<suite>
h3c resume outputs/runs/<suite>/<case>/<failed_run_id>
h3c resume outputs/runs/<suite>/<case>/<failed_run_id> --execute
h3c resume outputs/runs/<suite>/<case>/<failed_run_id> --defer-full-verification --execute
```

The registered physical profile initializes once at the evaluation start with a seven-day
BOPTEST internal warm-up and no explicit prefix. Air evaluations last seven days; MZ_Hydro lasts
five days. Only one physical process may hold `outputs/runs/.execution.lock`.

The deferred form releases that lock after a fast collection gate and publishes
`collection_complete.json`. The run is then `FULL-AUDIT-PENDING`, not yet a
valid result. Run `h3c finalize` from a single background audit worker; it makes
no API or BOPTEST calls and publishes verification/completion only after the
full audit succeeds.

The first `h3c resume` command is a network-free eligibility and prefix audit.
Execution is allowed only after the failed PID/test/lock are released. It always
uses a fresh run directory and BOPTEST test, replays every completed physical
step without recalling Agents, verifies the reconstructed state, then continues
at the next atomic hour. The original failure remains immutable.

## Offline onboarding

```console
h3c offline discover --spec configs/onboarding/example_spec.json
h3c offline discover --spec configs/onboarding/example_spec.json --reviewer <name> --execute
h3c offline resume outputs/offline/<case>/<workflow_id> --reviewer <name> --execute
h3c offline verify outputs/offline/<case>/<workflow_id>
```

Mapping and causal discovery pause for real human approval. Resume only the same checkpointed
workflow identity. Export accepts only a completed, verified workspace and refuses to overwrite
existing case or graph files.

## Baselines

```console
h3c-baseline models verify
h3c-baseline run --case SZ_Air --controller c-drl
h3c-baseline suite formal
h3c-baseline suite formal --execute
h3c-baseline verify outputs/baselines/runs/<suite>/<case>/<run_id>
h3c-baseline report outputs/baselines/runs/formal
```

The formal suite contains 11 strictly serial Basic RBC, P0/eRBC, C-DRL, and H-DRL arms. Each arm
uses a fresh BOPTEST test identity. A completed arm must pass production verification before the
next arm starts.

## Evidence handling

- Never overwrite, append to, splice, or silently delete a run directory. A
  registered `h3c resume` is a fresh lineage-bearing physical replay, not an
  in-place continuation.
- Treat `collection_complete.json` as collected-but-pending evidence and
  `completion.json` as the terminal fully audited success marker; a directory
  or manifest alone is neither.
- Compare only matching source, protocol, case, evaluation boundary, and model identities.
- Keep generated outputs ignored and store only reviewed summaries in tracked documentation.
- Do not expose endpoint secrets in commands, logs, reports, or commits.
