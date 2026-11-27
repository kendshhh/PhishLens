# Production deployment smoke

> Last observed live state — November 21, 2026 07:31 UTC: production deploy
> `dep-dc07rs67bikc73fjgjq0` serves SHA
> `811980c2cbf70d9957146bf329627f0826a018f1`. GitHub `main` later advanced
> through PR #263 and merged PR #265 to `95975cd47dceeac74ea36054610956f0a1db1fa9`;
> no later production deployment
> was verified. Read-only `/version`, `/health`,
> `/ready` and `/model-info` return 200; model info reports
> `analysis_enabled=false` and `provider_mode=disabled`. The disabled-aware
> observer in `main` can report identity/health/readiness/disablement with zero
> inference, paid calls and database writes, but the workflow was not run in
> this audit. This is not product acceptance. The workflow remains manual-only.
> See [PIPELINE.md](../../PIPELINE.md). The November 14 result below is historical.

## What the check verifies

[`production-deploy-smoke.yml`](../../.github/workflows/production-deploy-smoke.yml)
and `scripts/production_deploy_smoke.py` take a full deployment SHA, wait for
production `/version` to report that exact SHA, then check `/health`, `/ready`,
and `/model-info`. On current `main`, analysis disabled is accepted only when
`analysis_enabled=false`, `provider_mode=disabled`, and required-provider
support is false; the observer exits with zero inference requests, paid calls
and database writes. When analysis is enabled, the smoke requires a non-paid
TF-IDF provider and checks two fixed synthetic analysis cases. The enabled-path
preflight requires `/model-info` to advertise `supports_required_provider=true`.
Each analysis request sends
`X-Require-Provider: tfidf` to `/analyses/revision/{expected_sha}`. The API
checks its own source revision and active provider before inference, then echoes
the serving revision in `X-PhishLens-Revision`. An older instance without the
revision-scoped route returns before inference; a mismatched revision is
rejected before provider lookup. The smoke verifies the response revision for
every analysis request. The TF-IDF behavior checks make no saved-report/database
write and no paid provider request. A failed identity or provider preflight
stops before analysis.

The disabled-mode observer verifies the kill switch and service identity only;
it is not product or model acceptance. No production smoke workflow run was
performed in this audit.

## Workflow trust boundary

The workflow is `workflow_dispatch` only, and its job runs only when the
selected ref is `main`. It checks out that run's `github.sha` with persisted
credentials disabled. Its `GITHUB_TOKEN` permission is limited to
`contents: read`; the workflow does not reference repository secrets, write
repository contents, or modify branch protection or required checks. Artifact
upload is the only retained output.

The workflow is currently manual. Run it from Actions after a production
deployment and supply the full SHA reported by Render. It uploads a redacted
summary artifact. Do not treat `/ready` or the disabled-mode observer as feature
acceptance. No workflow run for current production SHA
`811980c2cbf70d9957146bf329627f0826a018f1` was performed in this audit.

## Why it is not automatically deploy-triggered yet

Render service metadata currently reports production auto-deploy off, while its
latest deployment record is triggered by `new_commit`. Treat this as an
unresolved configuration/evidence discrepancy and verify the Dashboard before
relying on automatic deployment.
No deploy-ended webhook or automatic smoke trigger is configured or verified.
Render documents workspace webhooks, which can emit a `deploy_ended` event, as a Pro-or-higher feature
([Render Webhooks](https://render.com/docs/webhooks)). The connected read-only
workspace metadata does not expose the current workspace plan. A
`workflow_run` check on the same default-branch commit could also become a
pending check while Render is waiting for checks to deploy that commit, so this
workflow does not register that trigger and risk a check/deploy cycle.

Therefore the repository has the verification code, but **it does not yet run
automatically after every production deployment**. To close the gap, either:

1. use a Render `deploy_ended` webhook on a plan that supports it, validate the
   signed event, and dispatch this workflow with the exact deployed SHA; or
2. move production deployment into a GitHub-controlled release workflow that
   deploys after CI, waits for the exact SHA to become live, then runs the
   smoke. This requires owner-approved Render deployment configuration and
   reconciliation with the currently reported auto-deploy-off setting.

Until one of those paths is configured and verified, the manual run is a
runbook action, not automatic deployment evidence.

## Production result — 2026-11-14 snapshot

On 2026-11-14 the production SHA advanced to
`76551f68ff7dc02971cf127fa82f1f35e79cc2ab` after PR #197. A fresh exact-SHA
manual run failed closed because `/model-info` returned
`provider_mode=unavailable`. The script sent zero analysis requests, made zero
database writes, and made zero paid provider calls. Production health and
readiness passed, but AI feature acceptance did not. A prior run on
`2c293f3739fc712fa4622906cc4df2846c880029` failed for the same reason. See
[reliability-acceptance-2026-11-14.md](reliability-acceptance-2026-11-14.md).
