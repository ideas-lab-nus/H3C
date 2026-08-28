# Prompt contracts

`h3c.agents.prompts.PAIRED_PROMPT_UNITS` is the single bilingual owner for stable
role policy. `h3c.agents.dynamic_prompt` is the single owner for dynamic user
blocks, and output schemas are owned by `h3c.agents.contracts`.

The canonical enabled English system prompts are frozen by byte length and
SHA-256 in `tests/fixtures/oracle_equivalence.json` and checked directly by the
test suite:

- Orchestrator: 1,398 bytes/characters under the frozen ASCII contract,
  `26100a021584f8f9762593a2a9d257e9bf4acb03316552430d56549c03221c75`
- Executor: 2,465,
  `b8487fcdd9365c2097d8b06c8f6fa54880693880b00d0e02284e4929539c2440`
- Reflector: 971,
  `a8ed483ed6f8d0e00c5614bd777bda049eca1931e6ae1795fe1f9ae14bcba52e`

The paired English/Chinese Orchestrator and Executor Prompts require a rationale
but carry no `short string`, 240-character, or other method-level length
semantics. The output validators require a nonempty string and persist it in
full. Reflector's separate one-sentence insight contract is unchanged.

Unavailable dynamic blocks are omitted completely. The graph-disabled render is
checked for absence of graph vocabulary, edge IDs, graph fields, and related
schema fields. Independent coordination removes allowance language and the
Orchestrator itself. Executor input contains the current complete executable
program but never the accepted-update ledger. Reflector prose is audit-only and
does not return to Executor input.

The Orchestrator role builder adds the priority invariant to its dynamic
`ALLOCATION LIMITS`: priority contains every configured zone exactly once, even
when the site cap and all zone budgets are zero. This does not change the frozen
system Prompt or relax the deterministic allocation validator.

The complete representative dynamic user renders are also tracked as golden
fixtures and compared byte-for-byte for all three roles. Their frozen lengths
and SHA-256 values are:

- Orchestrator: 3,688,
  `7804488e02eaee21bae6c56b318fcd22b1757e966bf7dfac01f15220a3dd99b7`
- Executor: 8,034,
  `9113794906eeca9c8e72d503234d4c4c4788399b5fc3461fa77c1a3f539182db`
- Reflector: 1,251,
  `3640397c92a9d4e2f742b43753f894461fa68ef4bd459ebc7ec8a720f8aa98dc`

The fixture provenance binds the full read-only oracle commit, each exact legacy
source path and Git-blob SHA-256, the tracked representative-input file identity,
and every fixture hash. Standalone users need no historical tree: default pytest
checks the complete tracked provenance/input/fixture contract and requires the
new production renderer to remain byte-for-byte equal to the fixture.

Migration auditors separately run
`python tools/verify_legacy_prompt_oracle.py --legacy-repository <path>` with an
explicit read-only repository containing the recorded commit. This fail-closed,
zero-API gate materializes that Git tree in a temporary directory, calls the
three legacy builders with the frozen input, and compares their output directly
with the fixtures. It never silently skips, and the new renderer is never used
as the oracle.

The same tracked oracle fixture also binds the deterministic behavior surrounding
the prompts: program and patch results, direction proof, budget settlement,
action assurance, weather, KPI accumulation, case mappings, and full-ledger
replay identities.

## Offline onboarding Prompts

Offline Mapping and causal discovery have separate owners in
`h3c.offline.prompts`; they are not members of the online bilingual Prompt
registry. Both use the same provider identity: `reasoning_effort=low`, with
`temperature` and `top_p` absent from the final wire request. Mapping and causal
discovery differ only in role Prompt and output schema.

The migration baseline, deliberate current-schema differences, source hashes,
and legacy sampling retirement are recorded in
`docs/offline_prompt_migration.md`. Initial and reviewer-revision system/user
renders are frozen in `tests/fixtures/offline_prompts/golden_hashes.json`.
Human feedback is rendered only into the rejected stage's next offline user
Prompt and cannot enter the online Orchestrator, Executor, or Reflector Prompt.
