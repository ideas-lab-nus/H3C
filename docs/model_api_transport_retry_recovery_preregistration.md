# Model API transport retry recovery preregistration

Status: registered after the final-source release arm-five transport hard stop
and before any retry implementation, API call, or physical recovery run on
2026-08-27.

## Preserved failure and public decision

Source `660b6c927cd1849e8823353bc5b91318fcef1490` release arm five stopped after
36 confirmed model responses when an Executor request lost the TLS response
stream with `ConnectionResetError` on Windows. The run completed one physical
initialization, the registered conditioning prefix, and one stop, but it did not
publish metrics, verification, or completion. It remains immutable
`RUN-INVALID` evidence and must not be resumed, rewritten, deleted, or counted as
a completed release arm.

The user subsequently decided: “如果是连接问题，就重跑。另外需要补充api请求重试，
这是很关键的一个逻辑”. This is a post-result recovery decision that publicly
replaces the previous zero-retry transport rule. It does not revise the original
failure classification or erase the original hard stop.

## Single permitted implementation variable

Only the OpenAI-compatible model transport may retry. BOPTEST selection,
initialization, advance, observation, forecast, KPI, and stop requests remain
single-attempt and fail closed.

One logical model request may make at most three wire attempts: the initial
attempt plus two retries. The deterministic waits before retry attempts are one
second and two seconds. A retry is permitted only for a transient connection
failure while resolving, connecting, writing, or reading the model request:

- connection reset, aborted connection, broken pipe, truncated HTTP response,
  or clean/abrupt TLS EOF;
- network timeout;
- DNS resolution failure.

HTTP responses of any status, authentication or authorization failures, rate
limits, provider server responses, invalid response JSON, model-output schema
failures, role-contract failures, and deterministic control rejection are not
transport retries. They retain their existing owners and classifications. This
bounded list deliberately answers the observed connection failure without
introducing a general provider-response retry policy.

Every attempt for a logical request must use the identical endpoint, model,
thinking mode, sampling values, messages, response format, and serialized
request body. The API key must never enter an identity hash or artifact. No
parallel attempt, hedged request, resume, or recursive retry is permitted.

## Evidence and accounting contract

Every wire attempt must be appended to a dedicated attempt stream, including a
secret-free request identity, logical-call identity, attempt number, maximum
attempts, outcome, retryability, whether another attempt will be made, error
type, provider-charge status, and elapsed time. A confirmed successful response
links to its recorded provider usage. A connection failure after outbound send
is explicitly marked as having unknown provider-side charge status; retrying it
must not silently assume that only the later response can be billed. A recovered
logical call still produces exactly one
`agent_calls.jsonl` row and one `raw_model_io.jsonl` row. A terminal transport
failure produces no synthetic model response.

The registered release matrix remains 13 arms and 372 successful logical model
responses; the formal plan remains 27 arms and 16,824 successful logical model
responses. Retry attempts are reported separately and must never be counted as
additional logical responses. The manifest, metrics, and production verifier
must independently recompute actual retries, recovered calls, terminal transport
failures, attempt ordering, immutable request identity, and one-to-one logical
response alignment.

A safely recovered transient connection failure may retain healthy execution
integrity if the complete physical lifecycle and all other evidence checks pass.
Retry exhaustion or any non-retryable transport failure remains `RUN-INVALID`.
Model-contract degradation keeps its existing orthogonal classification; retry
does not make an invalid model output acceptable.

## Fresh recovery and release boundary

The implementation must add focused positive and tamper-negative tests, then
pass the complete offline pytest, Ruff, strict mypy, lock, Prompt oracle, dry
matrix, secret, repository, and standalone gates from a clean committed HEAD.
No API or BOPTEST execution is allowed while implementing or validating this
change.

Because the model client, runtime configuration, artifacts, metrics, manifest,
and verifier identities change, no result from source `660b6c9` may be combined
with the replacement release matrix. After an exact-HEAD read-only audit and
explicit release, the complete 13-arm release matrix must restart fresh at arm
zero. Each arm remains single-run at the logical experiment level: the bounded
wire retries above occur inside one logical call and do not authorize resuming a
failed workspace or a lucky arm rerun. Formal experiments remain prohibited.
