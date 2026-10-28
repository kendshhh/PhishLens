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

`Hosted staging` runs on PRs after isolated staging succeeds. It deploys the
GitHub pull-request merge-ref SHA (`github.sha`) through the Render API, records
the PR head SHA separately, verifies the deployed SHA through `/version`, and
repeats the HTTP/client smoke checks. Missing configuration fails the job. A
shared concurrency group prevents two workflow jobs from deploying or testing
the staging service at once. GitHub can replace older pending jobs when several
PRs queue; rerun the intended PR if necessary.

Backend checks verify the Alembic graph on the exact merge commit and export its
head as deployment evidence. Before deployment, the trusted controller checks
the Render service, verifies that its connected source branch is `main`, confirms
auto-deploy is off, and privately validates the configured Neon host/database
against the staging allowlist. The merge SHA and verified migration head are
passed into the protected deployment step; failed preflight stops before Render
is called.

The PR merge candidate is tested by component and isolated integration jobs.
Hosted staging deploys that merge-ref SHA. Require an up-to-date branch before
merging. New commits require fresh checks and review. Another PR may later
replace the shared staging deployment; confirm the live SHA before manual Chrome
testing.

### Required gate and deployment evidence

Every eligible same-repository, non-draft PR runs the real `Hosted staging` job
after isolated integration. Tooling-only changes are not an exemption. A green
check requires Render to report the requested merge-ref SHA live, the real
extension client smoke to pass, and `/version` to report that same SHA in
`staging`.
Missing synthetic history, unhealthy/unready responses, changed PR heads, and
failed deployments fail acceptance.

The trusted default-branch controller packages extension assets from that exact
deployed merge-ref SHA. The `PhishLens-Staging-Extension` artifact contains a
staging-only ZIP with a visible PR/SHA banner, `preview-info.json`, and
`evidence.json`; the evidence records both PR head and deployed commit. This
binds the automated client package to the backend SHA. The artifact does not
claim installed-Chrome acceptance; that remains a separate human test.

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
- Required connected branch: `main`; auto-deploy remains off. On 2026-10-28,
  Render service settings were changed from stale bootstrap branch
  `ci/staging-validation` to `main`. Build and start commands remain unchanged.
  The change updates the service source setting; it does not deploy a new commit.

The selected staging target is Neon branch `pr-58-staging`, database
`phishlens_dev`. Keep development on the `development` branch and production on
`production`; never point staging at either one. On 2026-10-28, the Render
Environment page was privately checked: `DATABASE_URL` resolves to the host and
database for `pr-58-staging/phishlens_dev`, and `STAGING_DATABASE_HOST` matches
that host; `APP_ENV=staging` and `AI_MODE=mock`. Only the branch/database result
is recorded here. Do not copy the connection string into this runbook, a PR
comment, or an extension package. A current `main` deployment is now live as
commit `2ce4051…`.

On 2026-10-28, Save and Deploy retried stale commit `35b68ba…` and failed with
the missing-revision error. Render then used **Manual Deploy → Deploy latest
commit** from the connected `main` branch. Commit `2ce4051…` is live as deploy
`dep-dbgkc267bikc73aefsgg`; `/health` and `/ready` return 200 and `/version`
reports `2ce4051b320ce96069f4cc29dcf32724e1b7dfca` in `staging`. A read-only
Neon query confirms `0003_saved_analysis_idempotency` on
`pr-58-staging/phishlens_dev`. No CRUD acceptance request was run.

The earlier failure log `Can't locate revision identified by
'0003_saved_analysis_idempotency'` came from stale source commit `35b68ba…`,
which did not include
`backend/migrations/versions/0003_saved_analysis_idempotency.py`. The live
database already had that revision; the current source commit did not. Do not
stamp, edit, or reset `alembic_version` to repair a source/database mismatch.
The protected deployment workflow now preflights the exact merge commit's
Alembic graph, the allowlisted Render service and `main` source branch, and the
staging database host/name before it requests a deployment. It then deploys the
same merge SHA and records the migration head with the staging evidence.

The previous PR #68 staging artifact was built from `520779…`, while the live
backend was `2ce4051…`; those were not a paired client/backend check. After this
guard change merges, rerun the protected workflow and use its newly generated
artifact only after `/version`, its artifact source SHA, the Neon branch and
database, and the Alembic revision are recorded together.

Set `APP_ENV=staging` and `STAGING_DATABASE_HOST` to the exact hostname in
`DATABASE_URL`. Startup refuses other database names or a missing/mismatched host
before migrations or seed run. The name guard cannot distinguish Neon branches:
verify the host/branch privately in Neon. Never reuse the production connection
or put it in an extension. Until a current protected deployment is live and its
commit and migration revision are recorded, do not perform hosted staging CRUD
acceptance.

The Render runtime must reach Neon over IPv4. A failed deploy showed Render had no
route to the endpoint's IPv6 address. `start_staging.py` resolves the configured
hostname's IPv4 addresses at startup and passes them to libpq while retaining the
Neon hostname for TLS/SNI. Keep the hostname in `DATABASE_URL`; do not hard-code a
resolved IP, since Neon may change its address records.

Startup applies forward migrations and repeatable synthetic seed only to staging.
The database role must permit migrations. Failed migrations fail startup; no
rollback or production migration is performed by this workflow.

## GitHub configuration

Repository Actions variables:

| Name | Value |
|---|---|
| `RENDER_STAGING_SERVICE_ID` | `srv-db92irlg1s2s739404i0` |
| `STAGING_BASE_URL` | `https://phishlens-staging.onrender.com` |

Protected `staging` environment variables used by the trusted deployment
preflight:

| Name | Value |
|---|---|
| `SECRETARY_STAGING_DB_HOST` | Exact hostname for Neon `pr-58-staging` |
| `SECRETARY_PRODUCTION_DB_HOST` | Production Neon hostname, distinct from staging |

Keep host values private to the GitHub environment configuration. Do not put
them in workflow logs or evidence. `SECRETARY_PREVIEW_ENABLED` and
`SECRETARY_REPLACES_LEGACY_STAGING` are separate rollout switches; follow the
staging controller cutover steps in `secretary.md` before enabling them.

Protected `staging` environment secret: `RENDER_STAGING_API_KEY`, configured
privately by the owner. This key is exposed only to the deploy step, after
environment approval. Treat same-repository PRs that can edit workflows as trusted
deployment code; review access accordingly. Fork PRs
do not receive repository secrets and cannot pass hosted staging automatically.
Bring reviewed fork changes into a trusted repository branch for staging. Never
use `pull_request_target` to execute untrusted PR code with deployment credentials.

GitHub evaluates deployment branch rules against the workflow's event ref, even
when checkout reads `main`. A `pull_request` workflow uses `refs/pull/N/merge`.
Allowing only `main` therefore rejects this job before any runner steps execute.
The proposed staging branch allowlist is `main` plus `refs/pull/*/merge`; this
setting requires explicit owner confirmation before it is applied. Keep required
reviewer `xxTrixia`, prevent self-review, and disallow administrator bypass.
The environment approval authorizes deployment and is separate from PR approval.
Do not remove `environment: staging`, move its secret back to repository scope,
or replace deployment with a successful not-applicable check to work around it.

GitHub documents the PR merge-ref pattern in
[deployment branch restrictions](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

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
claims require separate evidence. Hosted staging currently covers saved-history
read behavior; CRUD acceptance remains gated. The Neon Auth CRUD prototype is
separate, local-only, and not yet exercised.

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
