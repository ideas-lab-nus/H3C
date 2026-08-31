# Executor output-envelope recovery result

## Outcome

The dominant Executor schema regression is fixed. The correction restores the
historical H3C wire envelope explicitly in the English Prompt:

```json
{"patch":[{...}]}
```

The parser, operation shape contract, causal evidence requirement, program
validator, Budget, Safety and interpreter were not relaxed.

Classification:

`FORMAT-RECOVERED / BASETEN-WIRE-COMPATIBLE /
MODEL-CONTRACT-MINOR-DEGRADATION / PHYSICAL-BEHAVIOR-UNTESTED`

## Root cause

Across the completed Official and Baseten MZ Air 06:00--12:00 diagnostics, the
60 Executor responses used these root spellings:

- 24 flat operation objects;
- 29 `patch` objects whose `patch` value was an object rather than a list;
- 3 correct singleton-list envelopes;
- 1 truncated non-JSON response.

The compact English Prompt said only that `patch` contained one operation,
whereas both the current production parser and the earlier H3C parser require
the exact singleton-list envelope. The Chinese Prompt still showed that
envelope. This was therefore a Prompt/wire mismatch, not evidence that the
executable safety checks were too strict.

An audit-only envelope normalization, with no operation-field repair, produced:

| Historical Executor responses | Count |
|---|---:|
| Total | 60 |
| Parseable JSON | 59 |
| Passed unchanged operation-shape owner after envelope normalization | 58 |
| Missing required causal citation | 1 |
| Truncated invalid JSON | 1 |

## Correction and offline gates

Source commit used for the external probe:
`366c4ab4d79ee75fede4108655b32b6f2400c259`.

The correction adds the exact root object to the shared model-visible operation
contract and adds positive and negative tests that bind the Prompt to the
existing parser. Flat operations, `patch` objects, empty lists and
multiple-operation lists remain rejected.

- Full pytest: `488 passed`.
- Ruff lint: passed.
- Ruff format check: passed for 211 files.
- Strict mypy: passed for 80 source modules.
- Generated English and Chinese complete-hour documents: fresh.
- Git whitespace and staged-file secret scans: passed.
- Prompt bundle:
  `sha256:6a5b1fe1a65b6d723560fd35a4dfa33cdab0afdc435ca4d9e37beec1156d96ee`.

## Baseten production-client probe

The preregistered probe reused byte-for-byte user inputs from all five MZ Air
zones at evaluation hours 0 and 5 of Official run
`20260831T163209086500Z-769b0b802f70`. Only the corrected English Executor
system Prompt changed. Ten independent calls used the production HTTP client,
model `deepseek-ai/DeepSeek-V4-Flash-0731`, thinking enabled,
`reasoning_effort=low`, no `temperature` or `top_p`, and zero retries. BOPTEST
was not called.

Evidence directory:
`outputs/diagnostics/executor-envelope-baseten-20260831T175319135750Z-366c4ab`.

| Check | Result |
|---|---:|
| Transport responses | 10/10 |
| `finish_reason=stop` | 10/10 |
| Exact response model | 10/10 |
| Correct low-thinking raw request | 10/10 |
| Bare JSON | 10/10 |
| Exact singleton-list envelope | 10/10 |
| Unchanged production shape resolver | 9/10 |
| Secret absent from evidence | yes |

Operation distribution was three `no_change`, three `remove_rule`, three
`replace_rule` and one `set_param`. All six modifying operations that supplied
causal IDs used unique IDs visible in their exact user input. One additional
`remove_rule` omitted `causal_edge_ids`; it was correctly rejected by the
unchanged resolver. This requirement predates the current context revision and
is necessary to bind a modifying operation to supplied causal evidence, so it
is not removed as an unnecessary runtime check.

Latency per call was 16.50--63.33 seconds, with a 26.06-second median and a
63.33-second nearest-rank p95. Aggregate usage was 22,690 prompt tokens, 32,913
reasoning tokens and 33,899 completion tokens (56,589 total tokens under the
provider's normalized usage fields). No request was retried.

## Interpretation and limit

The real Provider test confirms that explicitly restoring the old wire example
solves the widespread root-format failure: the exact-envelope rate changed from
3/60 in the earlier mixed diagnostics to 10/10 in this frozen probe. The one
remaining rejection is an ordinary model omission of an already explicit,
method-relevant causal field, not a root-format regression and not evidence for
removing causal validation.

This was an API-only contract probe. It did not settle proposals, modify a
program, advance BOPTEST or measure control KPIs. No replacement call, physical
run, paper edit or push was performed.
