# H3C batch collection and remaining-ablation preregistration

Date: 2026-09-02

## Purpose

This preregistration freezes two control-neutral execution changes for the remaining first-pass
campaign from source `8becfad87d0acf6f91a687879c3da7eff5847a45`:

1. add a true zero-hour working-memory ablation; and
2. separate fast terminal data collection from the existing expensive full run audit.

Neither change alters the canonical Prompt text, P0 program, interpreter, causal admission,
Budget, action assurance, reward, case profile, Provider request contract, or the established
one-, two-, and three-hour working-memory views.

## Zero-hour working memory

`--working-memory-hours 0` is an Agent ablation. Completed-hour evidence, Reflector calls, and
internal records are still produced, but no prior working-memory block is injected into any of
the three Agent roles. Long-term memory remains off. Existing `k=1/2/3` rendering and behavior
must remain unchanged.

## Two-level terminal state

Batch runs use `--defer-full-verification`. After BOPTEST has stopped, a lightweight collection
gate checks the registered identity, final checkpoint, expected row/call counts, readable core
artifacts, deterministic KPI recomputation, stopped lifecycle, and zero secret exposure. Passing
runs atomically publish `collection_complete.json` with
`COLLECTION-COMPLETE / FULL-AUDIT-PENDING`, release the execution lock, and may no longer mutate
runtime evidence.

`python -m h3c.cli finalize <run-directory>` later performs exactly one full zero-call audit and
atomically publishes the existing `verification.json` and `completion.json`. Full audit is not a
barrier for launching the next independent batch. Execution-integrity failure may pause the
campaign at the next batch boundary; ordinary model-contract degradation and poor KPI do not.

The legacy synchronous mode remains supported. Its duplicate pre-completion verifier call is
removed; one full verification is sufficient before atomic completion publication.

## Registered first-pass matrix

Each factor is run once for `SZ_Air`, `MZ_Hydro`, and `MZ_Air`, with at most three independent
physical arms in parallel. The eight factors are:

1. zero-hour working memory;
2. two-hour working memory;
3. three-hour working memory;
4. causal module off;
5. missing solar-to-zone causal edge;
6. solar-edge timing mutation (Air immediate to delayed; Hydro delayed to immediate);
7. coordination off, including Orchestrator and shared Budget; and
8. all-role no-thinking.

The matrix contains 24 arms, 3,648 evaluation hours, 14,592 physical advances, and 16,824
logical Agent calls. All use Baseten `deepseek-ai/DeepSeek-V4-Flash-0731`, the registered formal
case windows, one fresh BOPTEST test per arm, long-term memory off, and the same final source.

## Recovery and reporting

Every active arm has its own worktree, PID, lock, run directory, test identity, and 30-minute
heartbeat. Heartbeats use only atomic completed prefixes and report reward, cost, energy,
zone-hours, PMV-hours, occupied peak absolute PMV, total variation, reversals, schema, fallback,
and retry counts against the same-length final H3C and frozen eRBC references.

Only registered control-neutral infrastructure failures may use the public fresh-test physical
replay path. Completed Agent calls are not repeated, failed directories remain immutable, and
poor KPI or ordinary model-contract degradation never triggers recovery or a lucky rerun.

## Acceptance and exclusions

Implementation must pass targeted zero-memory, collection/finalization, resume, one/two/five-zone,
Prompt-identity, pytest, Ruff, format, strict-mypy, and staged-secret gates. No DeepSeek or BOPTEST
call is made during implementation gates. The campaign starts only from a clean committed source.

This work does not enable long-term memory, change paper text, LaTeX, Figure 3, or create a
case-specific method. It is not pushed without a separate explicit push instruction.
