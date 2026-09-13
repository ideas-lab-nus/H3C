# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately to the repository maintainers through GitHub's private
security-reporting channel. Do not include credentials, private endpoints, model-service payloads,
or building-management-system data in a public issue.

## Operational boundary

H3C reads model and BOPTEST credentials from environment variables. Never commit `.env` files or
embed tokens in configuration, prompts, logs, screenshots, or result packages. Review generated
artifacts before sharing them because external services can return deployment identifiers and
diagnostic metadata.

The LLM roles propose structured RBC updates; they do not execute generated code. Deterministic
parsing, program validation, causal proof, cooling-allowance checks, and action constraints remain
part of the trusted boundary. Operators must still isolate the runtime from safety-critical plant
controls, enforce local actuator limits, and preserve a controller that can continue operating when
the model service is unavailable.
