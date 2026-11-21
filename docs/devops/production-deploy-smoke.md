# Production deployment smoke

> Current state — November 21, 2026: production is Live on SHA
> 811980c2cbf70d9957146bf329627f0826a018f1 in deploy
> dep-dc07rs67bikc73fjgjq0. The scheduled Production drift run passed source
> SHA, health and readiness checks only. Staging was manually deployed to the
> same SHA in dep-dc07s1cipgvc73dh0150; no authenticated product acceptance is
> inferred. The current model-info state was not checked in this refresh. The
> smoke supports a disabled-aware zero-inference check, but remains manual-only.
> See the [current release record](release-record-2026-11-21.md). The November
> 14 production result below is historical.

## What the check verifies

[`production-deploy-smoke.yml`](../../.github/workflows/production-deploy-smoke.yml)
and `scripts/production_deploy_smoke.py` take a full deployment SHA, wait for
production `/version` to report that exact SHA, then check `/health`, `/ready`,
and `/model-info`. On the current `main` implementation, the smoke also
requires a non-paid TF-IDF provider and checks two fixed synthetic analysis
cases. The preflight requires `/model-info` to advertise
`supports_required_provider=true`. Each analysis request sends
`X-Require-Provider: tfidf` to `/analyses/revision/{expected_sha}`. The API
checks its own source revision and active provider before inference, then echoes
the serving revision in `X-PhishLens-Revision`. An older instance without the
revision-scoped route returns before inference; a mismatched revision is
rejected before provider lookup. The smoke verifies the response revision for
every analysis request. The TF-IDF behavior checks make no saved-report/database
write and no paid provider request. A failed identity or provider preflight
stops before analysis.

PR #257 merged the disabled-mode path into main. When model-info returns
analysis_enabled=false and provider_mode=disabled, the smoke rechecks exact
deployment identity and reports health/readiness/model state without sending
an inference request. This verifies the disabled state only; it is not product
or model acceptance. No current successful manual run of this path is recorded.

## Workflow trust boundary

The workflow is `workflow_dispatch` only, and its job runs only when the
selected ref is `main`. It checks out that run's `github.sha` with persisted
credentials disabled. Its `GITHUB_TOKEN` permission is limited to
`contents: read`; the workflow does not reference repository secrets, write
repository contents, or modify branch protection or required checks. Artifact
upload is the only retained output.

The workflow remains manual. Run it from Actions after a production
deployment and supply the full SHA reported by Render. It uploads a redacted
summary artifact. Do not treat a successful readiness response alone as feature
acceptance. The current SHA has not passed this smoke. When analysis is
disabled, the smoke must confirm the disabled response and send zero inference
requests; do not attempt AI behavior while the owner has asked to keep AI off.

## Why it is not automatically deploy-triggered yet

The production Render service auto-deploys from main when checks pass. The
latest production deploy dep-dc07rs67bikc73fjgjq0 is Live on
811980c2cbf70d9957146bf329627f0826a018f1. The production smoke workflow is
still workflow_dispatch-only; no deploy-ended webhook or automatic smoke
trigger is configured or verified. The read-only workspace metadata does not
expose the current plan. A workflow_run check on the same default-branch commit
could remain pending while Render waits for checks to deploy that commit, so
that trigger could create a deploy/check cycle.

To automate post-deploy acceptance, either:

1. use a Render deploy_ended webhook on a plan that supports it, validate the
   signed event, and dispatch this workflow with the exact deployed SHA; or
2. move production deployment into a GitHub-controlled release workflow that
   deploys after CI, waits for the exact SHA to become live, then runs the
   smoke. That changes the current auto-deploy path and needs an approved
   Render API credential and deployment configuration.

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
