# Pre-merge staging

> Current status — November 21, 2026: saved-report history requires a Bearer-authenticated session.
> The protected GitHub staging environment currently targets Neon project
> `hidden-shadow-38533062`, branch `br-broad-feather-b3261w7l` (`staging-root`),
> with Auth database `phishlens_dev`. The workflow reads the existing
> `PHISHLENS_STAGING_AUTH_DATABASE` variable and requires two distinct synthetic
> Auth accounts. The local startup guard still allows the older `patient-bird`
> project, and Render's actual app/migration URLs and roles remain unverified.
> The selected Auth configuration allows localhost and does not require email
> verification. Do not run authenticated CRUD or create accounts until an
> authorized staging owner resolves the target, role, and Auth-policy mismatches.
> The earlier anonymous-auth boundary failure is recorded in the
> [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md). No hosted
> Auth write acceptance or browser acceptance is claimed.
> The November 15 point-in-time staging deployment and CRUD acceptance are recorded in
> [the staging acceptance record](staging-acceptance-2026-11-15.md). That run predates
> PR #226's URL identity fix and does not establish that current `main` is deployed
> or verified in staging.

Delivery order: task branch → PR component checks → isolated staging integration
→ hosted staging → Chrome verification and teammate approval → merge to main
→ main CI → production Render deployment → production verification.

## Automated checks — November 22, 2026

`Staging integration` waits for `Backend checks` and `Extension checks`. It
starts an isolated PostgreSQL database, runs the FastAPI service and migration
chain, and exercises the API through the extension client. It uses no Render or
Neon credential and is not evidence of hosted Auth or persistence.

The remote `main` CI workflow still contains a PR-triggered `Hosted staging`
job with the Render deploy key in its protected environment. That job can run
PR-selected workflow/scripts with the credential and is not a safe trust
boundary. The local uncommitted change removes the PR-triggered deploy job.
Staging deployment is left to the separate `Secretary preview` `workflow_run`
controller, which checks out the default branch before using the protected
Render credential. This local correction is not active on GitHub until reviewed
and merged.

The trusted controller deploys an eligible PR source SHA after CI and staging
preflight. In Neon Auth mode, its current check verifies service identity,
health, readiness, version, and anonymous saved-report rejection only. It does
not perform A/B sign-in, authenticated create/list/read/update/delete, reload
persistence, cross-user denial, cleanup, or authenticated extension UX. No such
acceptance passed in this audit. Remote `main` can still report the required
`Secretary staging` status green while its detailed check says Auth acceptance
is pending. The local controller change fails the required status in that case;
it needs merge and a subsequent PR run to verify the installed workflow.

### Required gate and evidence

A green infrastructure preflight is not authenticated product acceptance. The
required status must remain failing until the exact candidate passes the
approved Auth/CRUD and extension journey, or the release record must keep that
criterion explicitly blocked. Do not promote or publish a release from health
checks, mock CRUD, seeded history, or browser-only evidence alone.

When implementing authenticated acceptance, use a confirmed isolated Neon
branch and synthetic identities. Keep credentials out of PR-controlled CI,
logs, artifacts, and extension packages. The trusted controller must validate
the current PR head, required CI attempt, service/database/Auth target, exact
migration revision, package identity, and cleanup before publishing evidence.
Until the authorized owner confirms the target and roles, do not run hosted
writes or create accounts.

> The remaining service, configuration, and dated verification sections below
> are historical runbook evidence and may describe older targets, check names,
> or workflow behavior. Use the November 22 audit section above for the current
> repository/workflow distinction; do not treat old checks or runtime results
> as current acceptance.

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
  The hosted workflow uses the Render API to deploy the selected PR merge SHA.

The current startup source allowlists Neon project `patient-bird-25428852`,
branch `pr-58-staging` (`br-delicate-paper-b381z98i`), application database
`phishlens_dev`, with the separate Auth database `neondb`. The protected
GitHub staging environment now names the different `hidden-shadow-38533062`
project and `staging-root` branch, with Auth database `phishlens_dev`.
Neither declaration proves which branch Render actually uses.

Read-only inspection on November 21 also found a second project,
`hidden-shadow-38533062`, branch `staging-root`
(`br-broad-feather-b3261w7l`), with only `phishlens_dev` and Auth configured
there. Its current Auth settings allow localhost and do not require email
verification. The older project's settings disable localhost and require
email verification. Neither project's connection mapping to Render has been
proven by the service read tool.

An authorized staging owner must privately verify which project/branch Render's
app and migration URLs use, confirm the application and owner roles, and confirm
the Auth URL/database and security settings. Resolve the GitHub target versus
startup allowlist discrepancy with one reviewed source/environment change. Keep
the migration guard fail-closed until the same isolated candidate is verified.
The selected GitHub Auth configuration currently allows localhost and does not
require email verification; correct those settings or obtain a recorded staging
policy exception before authenticated acceptance.

Historical snapshot — October 28, 2026: the Render Environment page was privately
checked and `DATABASE_URL` mapped to `pr-58-staging/phishlens_dev`;
`STAGING_DATABASE_HOST` matched, with `APP_ENV=staging` and `AI_MODE=mock`.
This point-in-time check predates the second Neon project and does not verify
the current Render mapping. Do not copy any connection string into this runbook,
a PR comment, or an extension package.

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
backend was `2ce4051…`; those were not a paired client/backend check. For later
PRs, use the protected workflow's newly generated artifact only after `/version`,
its artifact source SHA, the Neon branch and database, and the Alembic revision
are recorded together.

Configure two credentials in this service's Render environment:

- `DATABASE_URL` uses the branch-scoped `phishlens_staging_app` role for API
  requests and synthetic seeding. This role must not create databases or roles,
  replicate, or bypass row-level security. Grant only `CONNECT`, schema `USAGE`,
  and the table/sequence operations the API requires.
- `STAGING_MIGRATION_DATABASE_URL` uses the `neondb_owner` role on this staging
  branch and is consumed only by the startup migration subprocess. The startup
  process removes it before seeding or launching Uvicorn.

The current startup source accepts only the legacy `pr-58-staging/phishlens_dev`
endpoint and checks the application and migration roles before migrations or
seeding. A URL's database name and host do not prove its Neon branch. Before any
hosted write, migrations, or seed operation, an authorized owner must privately
verify the Render host-to-branch mapping and role identities in Neon. If the
new project is selected, first revise the source allowlist and tests in a
reviewed change; changing Render variables alone is insufficient. Keep
`STAGING_APP_DATABASE_ROLE=phishlens_staging_app` and `APP_ENV=staging` aligned
with the approved candidate, and keep connection values out of logs and docs.

Hosted staging accepts only the `sslmode` and `channel_binding` query keys from
the configured URLs. Before DNS or migration, startup also checks the effective
psycopg/libpq role, database, host, and port, and rejects `hostaddr`, `options`,
`service`, and `servicefile`. IPv4 pinning adds its own `hostaddr` only after
these checks pass.
Never reuse the production connection or put either credential in an extension.
Before any new hosted CRUD acceptance, confirm the protected deployment SHA and
migration revision; the recorded exact-SHA result is below.

The Render runtime must reach Neon over IPv4. A failed deploy showed Render had no
route to the endpoint's IPv6 address. `start_staging.py` resolves the configured
hostname's IPv4 addresses at startup and passes them to libpq while retaining the
Neon hostname for TLS/SNI. Keep the hostname in `DATABASE_URL`; do not hard-code a
resolved IP, since Neon may change its address records.

Startup applies forward migrations through the staging-only migration URL and
repeatable synthetic seed through the restricted app URL. Failed migrations fail
startup; no rollback or production migration is performed by this workflow.

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

Hosted Auth acceptance additionally requires two protected staging environment variables:

- `STAGING_NEON_AUTH_URL` points to the owner-verified Auth endpoint; its path must be `/<database>/auth`.
- `PHISHLENS_STAGING_AUTH_DATABASE` names the same Auth database as the URL path.
- Secrets: `STAGING_AUTH_USER_A_EMAIL`/`PASSWORD` and `STAGING_AUTH_USER_B_EMAIL`/`PASSWORD`.

Keep both accounts synthetic, staging-only, distinct, and email-verified. The workflow
validates the URL shape and account distinctness; it cannot prove the selected Neon branch.

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
3. Extract and load the folder as an unpacked extension in Chrome. The PR #86
   artifact produced by run 40736903885 has manifest name `Veriqo STAGING PR 86`,
   version `0.1.0`, `contextMenus` and `storage` permissions, and only the
   `https://phishlens-staging.onrender.com/*` host permission. Verify those
   values in Chrome before testing. The production source configuration remains
   unchanged.
4. Open history and verify the synthetic account notice, phishing prediction,
   high risk, and 93% confidence. Check popup/error behavior affected by the PR.
5. Record the PR SHA, deployment link, browser result, and evidence in the PR.
   Obtain a teammate's approval before merging.

Node smoke checks verify API/client integration, not Chrome DOM rendering,
extension permission enforcement, real email analysis, or AI inference. Those
claims require separate evidence. The API supports persistent saved-analysis
CRUD, and PR #58 records a successful synthetic API CRUD check on staging.
Hosted staging smoke checks saved-history reads; separate synthetic CRUD checks
passed on staging for PR #58 and for PR #83's exact deployed merge SHA, as
recorded below. The PR #86 exact-SHA guarded CRUD verifier also passed against
its live staging candidate, as recorded in the current verification section.
Production persistence and installed-Chrome acceptance remain separate evidence
items. Real-provider/AI verification remains separate. The Neon Auth CRUD
prototype is separate, local-only, and not yet exercised.

## Verification status

### Post-merge staging and CRUD verification — October 29, 2026 00:31 UTC

PR [#86](https://github.com/kendshhh/PhishLens/pull/86) merged at 00:11 UTC
with merge commit `1344fcb061272bac93ced5911f1ab8fbb3b6785d`. Render staging
deployment [`dep-dbh8s8942hec73bo7bt0`](https://dashboard.render.com/web/srv-db92irlg1s2s739404i0/deploys/dep-dbh8s8942hec73bo7bt0)
is Live on candidate SHA `fc7db9bf5441af4cd68ec2efbcbc7ac8efdc20a2`. At 00:31 UTC,
read-only `/version`, `/health`, and `/ready` requests returned HTTP 200;
`/version` matched that SHA and `staging`, and `/ready` reported the database
connected.

On Neon branch `pr-58-staging` (`br-delicate-paper-b381z98i`), database
`phishlens_dev`, table ownership was transferred from `phishlens_staging_app`
to the migration owner `neondb_owner`. The runtime role has `CONNECT`, schema
`USAGE`, and only `SELECT`, `INSERT`, `UPDATE`, and `DELETE` on `users` and
`analyzed_emails`. It has no schema `CREATE`, no privileges on `alembic_version`,
and no `TRUNCATE`, `REFERENCES`, `TRIGGER`, or `MAINTAIN` access. No sequences
exist in `public`. The role cannot create roles or databases, replicate, or
bypass RLS. PostgreSQL's database default still gives `TEMPORARY` to `PUBLIC`;
that default was not changed because it applies to every login role in this
staging database, and no temporary tables were present.

The already authorized guarded verifier passed against the exact live candidate:

```text
node scripts/verify_crud.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha fc7db9bf5441af4cd68ec2efbcbc7ac8efdc20a2 --allow-writes
```

It created, read, listed, edited, cleared, and deleted one synthetic record
(`9dceae92-cd9e-4046-b0fa-f667b3b87d1d`); the final absent-record check passed.
The verifier removes its created row in cleanup. No production write was made.
Installed-Chrome acceptance remains separate.

The PR #86 workflow artifact ID is `12861842602`, created from head
`3abad4309b2976e7390937c8f8f54e60aee8f6dc`. Its outer ZIP SHA-256 is
`c718b8a19fbbce2f5a823513330836ee34098fffd6c0e056bd6aba6fbbbaed15`; embedded
evidence identifies deployed candidate `fc7db9bf5441af4cd68ec2efbcbc7ac8efdc20a2`,
migration revision `0003_saved_analysis_idempotency`, and reports
`chrome_manual_test: not performed`. The extension artifact's manifest and
host permission were inspected; actual installed-Chrome behavior remains open.

### Current PR #86 gate — October 28, 2026 17:31 UTC

At this snapshot, PR head `dcafd2f539a3dafdc6a3c50e62cc35ae71c24d86` passed all
automated checks except Hosted staging, which is pending at the protected
`staging` environment; diagnostics returned no steps or reason. No deployment
for this head is claimed. The Live deployment below is from the previous code
head and is historical current-service evidence only. The Neon mapping and
excess runtime grants remain as recorded below; no grant change or write was made.

### Previous live candidate snapshot — October 28, 2026 17:07 UTC

PR #86 Hosted staging passed. Render service `phishlens-staging` is Live on
deployment [`dep-dbh2cjnf3r2c73emoprg`](https://dashboard.render.com/web/srv-db92irlg1s2s739404i0/deploys/dep-dbh2cjnf3r2c73emoprg),
exact merge SHA `d46cc09ecf7258a6bd10475f00cc8da035ef5e9a`. Read-only GETs at
17:07 UTC returned HTTP 200 for `/version`, `/health`, and `/ready`; `/version`
reported the exact SHA and `staging`, and `/ready` reported the database
connected. The staging Neon mapping is `pr-58-staging/phishlens_dev`.

A read-only grant check at 17:05 UTC still found `CREATE` on `public` and
`INSERT`, `UPDATE`, and `DELETE` on `alembic_version`, `analyzed_emails`, and
`users` for `phishlens_staging_app`. No role change or CRUD write was made.
The environment owner must remove excess grants and repeat the read-only check
before Kendra runs the already authorized guarded synthetic staging CRUD check.
Production remains read-only. Current Chrome acceptance, production persistence,
real-model evaluation, complete recovery timing, and event/sign-off evidence are
still open. See the [Kendra Week 1–4 closeout](kendra-week1-4-closeout-2026-10-28.md).

### Earlier October 28 snapshot — 15:43 UTC (superseded)

- The dedicated staging database target is Neon branch `pr-58-staging`, database
  `phishlens_dev`. A read-only Neon check found Alembic revision
  `0003_saved_analysis_idempotency` on that branch. The shared `development`
  branch is at `0002_analysis_provenance`.
- At 2026-10-28 16:08 UTC, a read-only Neon check on `pr-58-staging/phishlens_dev`
  found the `phishlens_staging_app` role. It can log in, is not superuser, and
  cannot create databases or roles. However, it has `CREATE` on the `public`
  schema and `DELETE`, `INSERT`, `REFERENCES`, `SELECT`, `TRIGGER`, `TRUNCATE`,
  and `UPDATE` on `alembic_version`, `analyzed_emails`, and `users`. The schema
  and table grants exceed the documented minimum app role. No privilege change
  was made. The environment owner should remove unnecessary grants, confirm the
  migration table is not writable by the runtime role, and repeat this read-only
  inspection before staging CRUD acceptance.
- Render service metadata reports source branch `main`, auto-deploy off, and
  service `phishlens-staging`. A later read at 2026-10-28 15:43 UTC found the
  live deployment `dep-dbh14vbl550s738ddfc0`, API-triggered at 15:19:25 UTC and
  finished at 15:20:52 UTC, on SHA
  `57da457be77fcf7a132e3a5e2f0d704c676040d6`. `/version`, `/health`, and `/ready`
  all returned HTTP 200; version identified `staging` and readiness reported a
  connected database. A GitHub comparison with current main
  `6414914dfa8eb8322839597c4cd6912145a442a0` found this deployment diverged from
  main (13 commits ahead, one behind; merge base `79aef1a`). It is not current
  main or PR #86 head `3fa617c1f53a44dcddd68de4468e6f3b6acc705f`, so its healthy
  endpoints do not verify either exact candidate. The 14:59 observation at
  `ec6d58c60659da940771873bec5d389b372b1f45` was superseded as the latest deploy.
- PR #83's earlier deployment `dep-dbgo3v49v7es73b02igg` at SHA
  `e3c6e37fd6661aeb582bd000507ef8cac677c23f` was subsequently deactivated.
  At that SHA, `/version` reported the commit and `staging`; `/ready` returned
  HTTP 200 with database connected. The exact-SHA guarded CRUD verifier passed
  against that staging origin: it created a synthetic analysis, read/listed it,
  edited and cleared notes, then deleted it and confirmed a 404. No production
  write was made. Command:
  `node scripts/verify_crud.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha e3c6e37fd6661aeb582bd000507ef8cac677c23f --allow-writes`.
- The `PhishLens-Staging-Extension` artifact and hosted smoke were produced by
  PR #83 run [40635217771](https://github.com/kendshhh/PhishLens/actions/runs/40635217771).
  Package identity and API integration passed. Installed-Chrome acceptance is
  still pending.
- An earlier staging snapshot identified source branch `ci/staging-validation`
  and deployed SHA `91b964d3bdb91b114a654065db184153a25403e0`. Its artifact record
  for workflow run `40542904034` points to source commit
  `d15a5b109a6170599a943213f22219ee1069f100` (artifact `12779275763`, expires
  November 3, 2026). That record describes its own deployment candidate; it does
  not identify the current live deployment or verify the later candidate above.
- Production and staging branch names are distinct in Neon. The Render service
  API does not expose database connection values, so the exact configured host
  mapping and staging app-role privileges still require an owner-side check in
  Render/Neon before claiming least privilege.
- The exact-SHA synthetic CRUD run above belongs to the deactivated PR #83 SHA
  `e3c6e37`; it does not establish CRUD behavior for current staging SHA
  `57da457` or current PR #86 head. PR #86's Hosted staging job is pending its
  protected gate. Do not run a new staging write until the approved target and
  exact candidate SHA are confirmed and the runtime role's excess grants are
  reviewed.

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
