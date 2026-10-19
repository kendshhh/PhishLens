# Pre-merge staging

Delivery order: task branch → PR component checks → isolated staging integration
→ hosted staging → Chrome verification and teammate approval → merge to main
→ main CI → production Render deployment → production verification.

## Automated checks

`Staging integration` waits for `Backend checks` and `Extension checks`. It starts
an isolated PostgreSQL 17 database and the real FastAPI process, applies migrations,
seeds synthetic records, then requests health, readiness, and seeded history using
the extension's actual `getAnalyses` client over HTTP. No Neon or Render secrets
are used in this job. Its database is discarded after the job.

`Hosted staging` runs on PRs after isolated staging succeeds. It deploys the exact
PR head SHA using the Render API, waits for that deployment to be live, verifies
Render's reported commit SHA, and repeats the HTTP/client smoke checks. Missing
configuration fails the job. A shared concurrency group prevents two workflow
jobs from deploying or testing the staging service at once. GitHub can replace
older pending jobs when several PRs queue; rerun the intended PR if necessary.

The PR merge candidate is tested by component and isolated integration jobs;
hosted staging tests the PR head. Require an up-to-date branch before merging.
New commits require fresh checks and review. Another PR may later replace the
shared staging deployment; confirm the live SHA before manual Chrome testing.

## Hosted service

- Workspace: PhishLens.
- Service: `phishlens-staging` (`srv-db92irlg1s2s739404i0`).
- URL: https://phishlens-staging.onrender.com
- Dashboard: https://dashboard.render.com/web/srv-db92irlg1s2s739404i0
- Region and plan: Singapore, Free.
- Runtime: Python 3.12.10.
- Build: `python -m pip install -r backend/requirements.txt`.
- Start: `python scripts/start_staging.py`.
- Auto-deploy: off; the PR workflow selects the exact commit.
- Bootstrap branch: `ci/staging-validation`. After this PR merges, change the
  service's connected branch to `main`, keeping auto-deploy off. Keep the bootstrap
  branch until this setting has been updated.

Configure `DATABASE_URL` directly in this service's Render environment. It must
refer to the separate Neon development branch and database `phishlens_dev`.
The startup script refuses other database names before migrations or seed run.
The name guard cannot distinguish Neon branches: verify the host/branch privately
in Neon. Never reuse the production connection or put it in an extension.

Startup applies forward migrations and repeatable synthetic seed only to staging.
The database role must permit migrations. Failed migrations fail startup; no
rollback or production migration is performed by this workflow.

## GitHub configuration

Repository Actions variables:

| Name | Value |
|---|---|
| `RENDER_STAGING_SERVICE_ID` | `srv-db92irlg1s2s739404i0` |
| `STAGING_BASE_URL` | `https://phishlens-staging.onrender.com` |

Repository Actions secret: `RENDER_STAGING_API_KEY`, configured privately by the
owner. This key is exposed only to the deploy step. Treat same-repository PRs that
can edit workflows as trusted deployment code; review access accordingly. Fork PRs
do not receive repository secrets and cannot pass hosted staging automatically.
Bring reviewed fork changes into a trusted repository branch for staging. Never
use `pull_request_target` to execute untrusted PR code with deployment credentials.

Required checks on `main`: `Backend checks`, `Extension checks`,
`Staging integration`, `Hosted staging`. Preserve teammate approval, stale-review
dismissal, conversation resolution, up-to-date branches, and no administrator
bypass. Existing PR branches need this workflow from current main after rollout.

## Chrome verification before approval

1. Confirm all four checks passed for the latest PR commit and verify its live
   SHA in the staging Render dashboard.
2. Download `PhishLens-Staging-Extension` from that PR's workflow artifacts.
3. Extract and load the folder as an unpacked extension in Chrome. Its display
   name is `PhishLens Staging`; its configuration and host permission point only
   to staging. The production source configuration remains unchanged.
4. Open history and verify the synthetic account notice, phishing prediction,
   high risk, and 93% confidence. Check popup/error behavior affected by the PR.
5. Record the PR SHA, deployment link, browser result, and evidence in the PR.
   Obtain a teammate's approval before merging.

Node smoke checks verify API/client integration, not Chrome DOM rendering,
extension permission enforcement, real email analysis, or AI inference. Those
claims require separate evidence. Staging currently covers the saved-history
walking skeleton, not unfinished AI or CRUD features.

## Verification status

### October 19 follow-up

The source worker now imports the same API origin as history. Its manifest uses
a module service worker. The staging packager therefore redirects both requests
using `js/config.js`, with staging-only host permission. The source package uses
production; local development requires changing the shared origin and permission
as described in README.

Local checks: 18 extension tests passed, configured ESLint passed, worker syntax
and manifest validation passed. Production packaging passed; the staging archive
passed integrity, shared configuration, module worker, and host-permission checks.
Packages are generated under `output/` and excluded from version control.

Render's deployment API reported deployment `dep-dbaehj5g1s2s73bqcs80` live for
commit `fc0741a100c15b898ca18d2a6ede169c367fe9da` (finished
2026-10-18 15:43:25 UTC). This identifies the existing hosted code, not the local
URL fix. A synthetic `POST /analyses` returned HTTP 200 in 3.44 seconds with
`mode: mock` and instructions to configure Gemini. Real AI acceptance remains
pending. Initial `/health` and `/ready` probes timed out; no readiness success is
claimed from this verification. Warm retries also timed out for both endpoints;
`GET /api/analyses` returned HTTP 200 with one item.

Installed-Chrome verification remains pending. Chrome is connected, but its
`chrome://extensions/` tab cannot be claimed by browser automation, and native
app control is disabled in this session. No installed-package result is claimed.
Teammate approval, current remote CI, deployment of the URL fix, and production
acceptance are still outstanding. The earlier provisioning snapshot below is
historical; its pending setup statements do not describe the latest live deploy.

The service and workflow are provisioned in [PR #31](https://github.com/kendshhh/PhishLens/pull/31).
[Initial CI run](https://github.com/kendshhh/PhishLens/actions/runs/38909864740)
passed Backend checks, Extension checks, and Staging integration. Hosted staging
failed at configuration validation before deployment because the URL variable was
not yet configured. The service ID and URL repository variables were subsequently
configured. The owner still needs to configure the development database and
deployment secret, then rerun hosted verification. Creation of a Render service
is not deployment success.

The main protection editor has all four checks selected, but saving redirected to
GitHub's email identity verification. Enforcement of the additional checks is
pending that verification and confirmation that the rule was saved. Do not treat
the selected form values as an applied rule.

Local verification: 11 backend tests passed, 2 database tests skipped locally;
all 5 deployment guard tests passed; new scripts passed Python lint and JavaScript
syntax checks. The staging ZIP's name, staging-only permission/configuration and
archive integrity were checked. Startup rejected a non-development database name
before attempting database access. Real PostgreSQL integration passed in CI.

Production remains the existing `phishlens-api` service following `main` after CI
checks pass. Post-merge CI repeats isolated staging; the hosted PR job is skipped
on pushes. Verify production health, readiness, live SHA, and changed behavior
after deployment as described in the runbook.
