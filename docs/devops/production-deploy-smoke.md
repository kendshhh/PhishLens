# Production deployment smoke

## What the check verifies

[`production-deploy-smoke.yml`](../../.github/workflows/production-deploy-smoke.yml)
and `scripts/production_deploy_smoke.py` take a full deployment SHA, wait for
production `/version` to report that exact SHA, then check `/health`, `/ready`,
the configured provider/model identity, and two fixed synthetic analysis cases.
The preflight also requires `/model-info` to advertise
`supports_required_provider=true`. Each analysis request sends
`X-Require-Provider: tfidf` to `/analyses/revision/{expected_sha}`. The API
checks its own source revision and active provider before inference, then echoes
the serving revision in `X-PhishLens-Revision`. An older instance without the
revision-scoped route returns before inference; a mismatched revision is
rejected before provider lookup. The smoke verifies the response revision for
every analysis request. The behavior checks run only when the live provider is
TF-IDF. They make no saved-report/database write and no paid provider request.
A failed identity or provider preflight stops before analysis.

## Workflow trust boundary

The workflow is `workflow_dispatch` only, and its job runs only when the
selected ref is `main`. It checks out that run's `github.sha` with persisted
credentials disabled. Its `GITHUB_TOKEN` permission is limited to
`contents: read`; the workflow does not reference repository secrets, write
repository contents, or modify branch protection or required checks. Artifact
upload is the only retained output.

The workflow is currently manual. Run it from Actions after a production
deployment and supply the full SHA reported by Render. It uploads a redacted
summary artifact. Do not treat a successful `/ready` response alone as feature
acceptance.

## Why it is not automatically deploy-triggered yet

The production Render service is on the Free plan with `autoDeploy=checksPass`.
The connected GitHub deployment inventory for the current production SHA has
staging records but no production deployment event. Render workspace webhooks,
which can emit a `deploy_ended` event, require a Pro plan or higher. A
`workflow_run` check on the same default-branch commit could also become a
pending check while Render is waiting for checks to deploy that commit, so this
workflow does not register that trigger and risk a check/deploy cycle.

Therefore the repository has the verification code, but **it does not yet run
automatically after every production deployment**. To close the gap, either:

1. use a Render `deploy_ended` webhook on a plan that supports it, validate the
   signed event, and dispatch this workflow with the exact deployed SHA; or
2. move production deployment into a GitHub-controlled release workflow that
   deploys after CI, waits for the exact SHA to become live, then runs the
   smoke. That changes the current `checksPass` auto-deploy path and needs an
   owner-approved Render API credential and deployment configuration.

Until one of those paths is configured and verified, the manual run is a
runbook action, not automatic deployment evidence.

## Current production result

On 2026-11-14 the production SHA advanced to
`76551f68ff7dc02971cf127fa82f1f35e79cc2ab` after PR #197. A fresh exact-SHA
manual run failed closed because `/model-info` returned
`provider_mode=unavailable`. The script sent zero analysis requests, made zero
database writes, and made zero paid provider calls. Production health and
readiness passed, but AI feature acceptance did not. A prior run on
`2c293f3739fc712fa4622906cc4df2846c880029` failed for the same reason. See
[reliability-acceptance-2026-11-14.md](reliability-acceptance-2026-11-14.md).
