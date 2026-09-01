# Working-memory release and long-term-experience decision

## Post-result decision

On 2026-09-01, after reviewing the matched MZ Air prefixes, the user selected the
Context–Action–Outcome–Lesson working-memory architecture without three-regime long-term
experience as the repository default. The current and subsequent formal H3C campaigns do not
enable long-term experience.

The `--long-term-memory` command-line option remains implemented for reproducibility and a future
explicitly authorized ablation. Its absence remains the default and removes the experience,
CRUD, revision and reference surfaces from the model contract and runtime evidence.

This is a post-result engineering decision. It does not erase or relabel the adverse memory-arm
evidence and does not claim that the incomplete comparison is a completed causal ablation.

## Cancelled MZ Air arm

The registered Baseten MZ Air three-regime arm from source
`d62057a49341016814d6726fb03ab25c1512aef3` was cancelled at the user's request after 54 complete
hours (216 physical advances):

- run identity: `24d62822014d74ccccbd1fe625a15ea211f1ca4db3856721a36e6486abd5ca30`;
- BOPTEST test identity: `2b06f164-4d1a-4e64-9d9e-821cce6e0b97`;
- terminal classification: `USER-CANCELLED / CENSORED-INCOMPLETE`;
- the BOPTEST test, runtime PID and execution lock are released;
- no `completion.json` exists and the trajectory must not be presented as a complete formal arm.

The external stop removed the BOPTEST test before the runtime's own final stop call. That second
stop returned HTTP 400, so the old runtime did not publish `failure.json` and left its last atomic
dispatch state at `Running`. The immutable checkpoint, trajectory and terminal supervision stderr
are retained as the authoritative cancellation evidence. The surviving working-memory-only MZ Air
arm was not interrupted.

## Release boundary

The repository release keeps the frozen control method and API contract from `d62057a`: Baseten
strict structured output is the default provider path, `occupancy_routed` low thinking remains in
force, and CAOL working memory is the only memory surface used by default. No Prompt, controller,
causal, Budget, Safety, reward, KPI or action-mapping rule is changed by this decision record.
