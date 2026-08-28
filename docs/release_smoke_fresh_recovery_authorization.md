# Release-smoke fresh-recovery authorization

Post-freeze protocol correction: MZ_Hydro formal evaluation is five days while
this release smoke remains six hours. The source-consistent sequence restarts
under `formal_hydronic_five_day_protocol_preregistration.md`.

Status: frozen before the newly authorized physical attempt on 2026-08-27.

After reviewing the two preserved arm-zero failures and the bounded stop-response
correction in commit `6c4935068d1684b19a33951e8cbd7a1b8f73792c`, the user
answered “授权” to the explicit question of whether to run one more fresh arm zero
and, if it completes and verifies, continue the preregistered arms one through
twelve.

This authorization does not change the release matrix, method, Prompt, model,
physical timeline, call budget, acceptance gates, or stop rules. The two existing
failed directories remain immutable and are neither resumed nor reused. The new
arm zero must use a new physical test and output directory. It is one fresh
infrastructure recovery, not an HTTP retry.

If the new arm zero publishes atomic completion and passes production
verification, continue arms one through twelve strictly serially under the
original preregistration. If it fails a hard-stop condition, stop the sequence
and preserve its evidence. Every executed arm retains its independent process,
exact completion path, and dedicated ten-minute heartbeat. The formal seven-day
suite remains outside authorization.
