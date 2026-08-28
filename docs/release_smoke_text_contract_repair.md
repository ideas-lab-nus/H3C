# Release-smoke text-contract repair

Superseded for new sources on 2026-08-28 by
`rationale_contract_and_mz_hydro_7day_preregistration.md`. This file remains the
old-source explanation; its 240-character normalization must not be applied to
or used to reclassify new runs.

Status: approved mechanical repair after the source `614019b` release arms and
before any further physical or model arm.

## Preserved evidence

The completed SZ_Air, MZ_Hydro, and MZ_Air Agent arms remain immutable evidence.
All six Reflector calls in each completed arm returned structurally plausible
zone summaries but failed the one-sentence validator whenever ordinary decimal
measurements such as `1.0125` or `0.0` appeared. The validator had been copied
byte-for-byte from the historical memory owner and counted every ASCII period as
a sentence terminator, including periods between digits.

The SZ_Air arm also exposed one Orchestrator allocation whose only invalid field
was an audit rationale longer than 240 characters. The historical production
Orchestrator did not replace that otherwise-valid allocation with a fallback: it
revalidated while allowing only the overlong audit text, truncated the text to
240 characters, recorded a `non_execution_text` deviation, and used the fully
validated allocation. H3C had omitted that compatibility path.

The MZ_Air arm contained one Executor rejection at hour 5 for zone `wes`. Its
root and patch shapes were exact, but its patch rationale exceeded the existing
short-string bound. The historical Executor also rejected this condition and
had no Orchestrator-style text-normalization exception. It is therefore retained
as an ordinary model-contract deviation; the Executor Prompt, schema, and
validator do not change.

## Mechanical repair boundary

1. The Reflector sentence owner ignores an ASCII period only when digits occur
   immediately on both sides. That same filtered terminator sequence owns both
   the sentence count and the check for text after a terminal mark. Multiple
   real sentences, line breaks, invalid zones, and invalid pair schemas remain
   rejected.
2. Orchestrator rationale normalization is available only when the exact root,
   zones, rationale types and non-empty strings are present, at least one
   rationale is overlong, and the allocation, graph references, and budget are
   otherwise strictly valid. The normalized allocation passes the same
   production validator again before use.
3. Telemetry records the raw rejection, non-execution-text category, strategy,
   character limit, original and normalized lengths, final validation, and that
   no fallback occurred. An accepted or text-normalized allocation always emits
   the exact fallback object `{used: false, reason: null, source: null,
   validated: false}`; its raw rejection is confined to `raw_contract` and
   `text_normalization`.
4. Raw schema and role-contract checks continue to reject the original overlong
   response. Such a run is model-contract degraded and cannot be
   `RELEASE-PASS`. Any other Orchestrator error still uses the existing validated
   previous-allocation or equal-split fallback without retry.
5. Canonical system Prompts, dynamic user Prompt golden bytes, output schemas,
   control laws, model request identity, release thresholds, and historical run
   directories do not change.

The production verifier resolves each raw Orchestrator response through the same
model-output owner as execution. For a true fallback, it then walks hours in
order and calls the same `validated_fallback_allocation` owner with the prior
expected resolved allocation. The expected allocation, source, rejection reason,
and complete fallback object must all match the artifact. A different valid
allocation or any fallback-field corruption therefore fails execution integrity;
the verifier does not accept a self-consistent rewritten allocation and budget.

Because production and verifier code change, every run under source `614019b`
is superseded for the final comparable release matrix. After a new stable HEAD,
all offline gates, and an explicit root-audit release, the thirteen-arm matrix
must restart at fresh arm zero. No current run may be resumed, retried, rewritten,
or combined with runs from the new source identity.
