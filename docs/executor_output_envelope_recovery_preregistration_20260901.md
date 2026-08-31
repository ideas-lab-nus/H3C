# Executor output-envelope recovery preregistration

Status: frozen before the Prompt correction and before any new Baseten request.

## Observed failure

The completed Official and Baseten MZ Air 06:00--12:00 diagnostics contain 60
Executor responses. All 60 preserve their raw evidence. Fifty-nine are parseable
JSON. After an audit-only normalization of the three observed envelope spellings,
58 operations pass the existing H3C patch-shape contract; one edit lacks required
causal IDs and one response is truncated with `finish_reason=length`.

The dominant regression is an English Prompt/wire mismatch introduced while
compacting the operation contract. Runtime still requires the historical H3C
wire `{"patch":[{...}]}`, but the current English Prompt only says that “patch
contains exactly one operation.” The two providers consequently returned:

- 24 flat operation objects;
- 32 `patch` objects, of which 29 use an object instead of a singleton list;
- 3 correct singleton-list envelopes;
- 1 truncated non-JSON response.

This is not evidence that the executable-program validator is too strict. The
legacy production owner also required the exact singleton-list envelope before
validating the operation.

## Authorized correction

Change only the English model-visible output contract so that it explicitly says
and shows:

```json
{"patch":[{...}]}
```

The list contains exactly one operation. Keep the current operation names,
required fields, causal IDs, rule/value types, parser, program validator, causal
proof, Budget, Safety, interpreter, Prompt context, thinking route, provider, KPI,
and acceptance criteria unchanged. Do not add compatibility normalization for
flat operations or `{"patch":{...}}`; accepting those would create a new wire
contract rather than restore the previous H3C contract.

Update the production-generated English/Chinese hour documents and Prompt bundle
identity. Add positive and negative tests proving the renderer and parser share
the exact envelope owner.

## Offline gates

Before any API request:

1. the 58 audit-normalized historical operations already known to be complete
   still pass the unchanged production shape owner; the separate
   missing-causal-ID sample and truncated sample remain rejected;
2. exact singleton-list envelope parses;
3. flat operation, `patch` object, empty list, multi-operation list, unknown
   fields, missing required fields and invalid JSON remain rejected;
4. memory-off and memory-on Prompts both show their exact root object;
5. historical accepted singleton-list output is unchanged and replays;
6. targeted tests, full pytest, Ruff, format, strict mypy, generated-document
   freshness, Git whitespace and secret scan pass;
7. the source is committed cleanly before external requests.

## Baseten regression probe

After the offline gates, send exactly ten independent production Executor calls
to Baseten from frozen real MZ Air inputs: all five zones at evaluation hours 0
and 5 of Official run `20260831T163209086500Z-769b0b802f70`. Only the corrected
English system Prompt changes; every user payload is reused byte-for-byte.

- model: `deepseek-ai/DeepSeek-V4-Flash-0731`;
- thinking: enabled with `reasoning_effort=low`;
- `temperature` and `top_p`: absent;
- retry count: zero for this diagnostic;
- calls may run concurrently because they are independent and do not touch
  BOPTEST or shared mutable controller state;
- API key is read only from the registered external `.env`, never printed or
  written to evidence;
- evidence is written under a fresh ignored diagnostics directory.

The probe passes only if all ten responses have `finish_reason=stop`, parse as
bare JSON, use the exact singleton-list envelope, and pass the unchanged
production Executor shape resolver. Program/causal/Budget admission is reported
separately and is not silently relabeled as a schema failure. No retry or lucky
replacement is allowed. This probe does not call BOPTEST and does not authorize
the seven-day MZ Air experiment.
