# AI CI and protected staging smoke

## Ordinary pull request checks

Backend checks continue to run with `AI_MODE=mock` against disposable PostgreSQL.
They make no live provider calls and download no model weights. The backend
evidence artifact now also contains `ai-regression.json`, generated from the
current JUnit report and tied to the PR source SHA. It records the frozen
development case-set version and hash, class inventory, selected deterministic
contract-test counts, failing test IDs, and the simulated failure-path test IDs.
Required AI and failure-path test cases and expected parameter counts are explicit
in `scripts/ai_ci_report.py`; missing or skipped cases fail Backend checks.
The report does not score model predictions or claim an accuracy result. AI
quality thresholds remain pending agreement with the AI owner in #49/#92; the
held-out set must stay separate from this development gate.

The existing PostgreSQL CI gate also requires the constraint-failure recovery
case and invalid-evidence/no-save/follow-up-success case. They use simulated
failures and synthetic data. `offline_failure_drill` explicitly reports zero
provider requests, zero production writes, and no live service-recovery time.
This automated evidence is not a substitute for a protected staging rehearsal.

## Deterministic AI evaluation

`.github/workflows/ai-evaluation.yml` runs on pull requests and main pushes that
change AI code, prompt/schema/model assets, or the evaluation harness. It runs
AI contract tests with mocked providers and one deterministic TF-IDF pass over
the 40-case development cohort. It makes zero Gemini requests and downloads no
model weights. The artifact records the evaluated source, model revision,
cohort hash, and development metrics. This cohort is not a held-out accuracy
claim; quality thresholds still require approval from the AI owner.

## Manual-only staging provider smoke

`.github/workflows/ai-provider-smoke.yml` has only a `workflow_dispatch` trigger.
The job runs only when dispatched from `main`, requires the protected `staging`
environment, and has no schedule. Ordinary PR CI cannot invoke it. It reads the
trusted staging origin from `.github/secretary.json`, checks `/version` against
the supplied full 40-character deployment SHA and requires
`environment=staging`, then checks `/ready` and database connectivity before any
provider request.

The request is fixed synthetic text to the non-persisting `POST /analyses`
endpoint. The script sends it once, uses no retry or redirect, limits the run to
one inference attempt, and stops on any preflight, identity, timeout, quota, or
response failure. The Gemini client is configured for one attempt. It does not
print or retain the request/response bodies, credentials, or provider error
details. The redacted
`AI-Provider-Smoke-Evidence` artifact contains run/source/deployment identity,
provider/model/prompt identity, one analysis-request attempt count, observed
provider-call count (or unknown if the service failed before returning mode),
outcome and limitations. A successful response produces no database write.

### Runtime spend guard and owner setup

Gemini inference is blocked unless the service has valid values for
`GEMINI_PER_REQUEST_COST_CAP_USD`, `GEMINI_INPUT_USD_PER_MILLION_TOKENS`,
`GEMINI_OUTPUT_USD_PER_MILLION_TOKENS`, and `GEMINI_COST_MODEL_ID` matching
`GEMINI_MODEL`. Before each request,
`backend/ai/spend_limit.py` reserves a conservative token-cost upper bound from
the UTF-8 byte count of the input, system instruction, and response schema, plus
1,024 bytes of overhead and the maximum of 2,048 output tokens. It blocks the
request when this estimate exceeds the configured cap. The workflow compares
its approved cap to the deployed runtime cap before sending its single
synthetic request.

The local `scripts/ai_smoke.py` and `scripts/benchmark_ai.py` use the same
estimator with `GEMINI_PER_RUN_COST_CAP_USD` and an exact `GEMINI_MAX_REQUESTS`
limit. The three-case smoke requires `3`; the full benchmark requires `41`
(one cold-start inference plus 40 development cases). Each request reserves its
cost before inference.

The input/output rates must match the selected model's current paid pricing and
must be updated when either the provider price or model changes. The exact
`GEMINI_COST_MODEL_ID` check blocks a model switch that leaves old rates in
place. This is a code-enforced pre-call estimate, not a provider invoice or an
account-level quota.
These requests do not use tools, grounding, or cached-input discounts. A
provider-side quota remains useful defense in depth but is not claimed as
evidence by this repository.

Before anyone dispatches a live request, the AI and staging owners must agree on
the provider, model, rates, and cap. In GitHub Settings → Environments →
`staging`, keep required reviewers enabled and set these non-secret variables
only after that review:

| Variable | Required value |
|---|---|
| `STAGING_BASE_URL` | The exact origin in `.github/secretary.json` |
| `AI_PROVIDER_SMOKE_ENABLED` | `true` only while the owner-approved smoke is allowed |
| `AI_PROVIDER_SMOKE_PROVIDER` | `gemini` |
| `AI_PROVIDER_SMOKE_MODEL` | The owner-approved configured model name |
| `AI_PROVIDER_SMOKE_MAX_REQUESTS` | `1` |
| `AI_PROVIDER_SMOKE_COST_CAP_USD` | Must equal the deployed `GEMINI_PER_REQUEST_COST_CAP_USD` |

On the protected Render staging service, set the matching `GEMINI_MODEL`,
`GEMINI_COST_MODEL_ID`, `GEMINI_PER_REQUEST_COST_CAP_USD`, and two model-specific rate variables. Keep
the Gemini API key on Render only. The workflow reads public model/cap identity
and refuses the request unless both match the approved values. The API response
does not expose provider billing, so this workflow cannot independently confirm
incurred cost.

To run after the owner setup: Actions → AI provider staging smoke → Run workflow
on `main`; set `enable_live_provider_request` to `true`, and paste the exact SHA
currently reported by staging `/version`. Approve the protected `staging`
environment only after reviewing those values. If any check fails, the workflow
stops without retrying the provider request.

To stop future runs, set `AI_PROVIDER_SMOKE_ENABLED=false` or remove the owner
variables, and keep the workflow manual-only. No live Gemini request has been
run as part of this work. Spend-guard tests verify that an over-cap request is
blocked before `generate_content`; paid provider evidence remains pending an
owner-approved configuration and manual dispatch.

