# AI CI and protected staging smoke

## Ordinary pull request checks

Backend checks continue to run with `AI_MODE=mock` against disposable PostgreSQL.
They make no live provider calls and download no model weights. The backend
evidence artifact now also contains `ai-regression.json`, generated from the
current JUnit report and tied to the PR source SHA. It records the frozen
development case-set version and hash, class inventory, selected deterministic
contract-test counts, failing test IDs, and the simulated failure-path test IDs.
The report does not score model predictions or claim an accuracy result. AI
quality thresholds remain pending agreement with the AI owner in #49/#92; the
held-out set must stay separate from this development gate.

The existing PostgreSQL CI gate also requires the constraint-failure recovery
case and invalid-evidence/no-save/follow-up-success case. They use simulated
failures and synthetic data. `offline_failure_drill` explicitly reports zero
provider requests, zero production writes, and no live service-recovery time.
This automated evidence is not a substitute for a protected staging rehearsal.

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

### Owner setup and stop path

Before anyone dispatches a live request, the AI and staging owners must agree on
the provider, model, per-run cost cap and provider-side quota/budget control. In
GitHub Settings → Environments → `staging`, keep required reviewers enabled and
set these non-secret variables only after that review:

| Variable | Required value |
|---|---|
| `STAGING_BASE_URL` | The exact origin in `.github/secretary.json` |
| `AI_PROVIDER_SMOKE_ENABLED` | `true` only while the owner-approved smoke is allowed |
| `AI_PROVIDER_SMOKE_PROVIDER` | `gemini` |
| `AI_PROVIDER_SMOKE_MODEL` | The owner-approved configured model name |
| `AI_PROVIDER_SMOKE_MAX_REQUESTS` | `1` |
| `AI_PROVIDER_SMOKE_COST_CAP_USD` | The owner-approved positive per-run cap |
| `AI_PROVIDER_SMOKE_PROVIDER_BUDGET_ENFORCED` | `true` only after an owner confirms the provider-side budget/quota limit is active |

Do not place provider credentials in workflow variables or artifacts. Runtime
credentials remain configured on the staging service, not exposed to this
workflow. GitHub's protected-environment approval is an additional gate; it does
not replace the provider owner's budget control. The API response does not expose
provider billing, so this workflow cannot independently confirm incurred cost.

To run after the owner setup: Actions → AI provider staging smoke → Run workflow
on `main`; set `enable_live_provider_request` to `true`, and paste the exact SHA
currently reported by staging `/version`. Approve the protected `staging`
environment only after reviewing those values. If any check fails, the workflow
stops without retrying the provider request.

To stop future runs, set `AI_PROVIDER_SMOKE_ENABLED=false` or remove the owner
variables, and keep the workflow manual-only. No live request has been run as
part of preparing this workflow. Until the owners configure and approve the
provider budget, dispatches are blocked before any provider call.

