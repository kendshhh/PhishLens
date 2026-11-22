# PhishLens staging acceptance

**Selected base:** PR #268 commit `d31a76b`, descended from `main@0338ad1`.
The staging merge sequence is #268 → #251 → #276 → #270 → #267 → #266 → #258.
This branch preserves the staging endpoint pin and mapping. No live Hosted Auth or
CRUD acceptance is claimed for this integrated candidate; issue #153 remains
**NO-GO** until exact-head checks and protected acceptance pass.

## PR-required Hosted staging

The stable `Hosted staging` job runs for a same-repository, non-draft runtime PR
with the `needs-hosted-staging` label and `SECRETARY_PREVIEW_ENABLED=true`. It
retains the existing check name. Its eligibility and prerequisite logic is
fail-closed: if backend checks, isolated integration, or exact-head preflight
fails, the job fails rather than being treated as a successful skipped job.

Before any deployment or product-data write, the job:

- confirms the PR is still open at the queued exact head and still labeled;
- requires staging and production Neon project IDs to differ;
- verifies the configured staging branch is a root branch, differs from the
  production branch, has the expected endpoint, and has a protected schema-only
  attestation;
- requires the staging Render runtime mapping to match that endpoint and
  requires enabled Neon Auth;
- refuses a changed or superseded PR head immediately before deployment.

Do not enable this run against `pr-58-staging` (`br-delicate-paper-b381z98i`),
any production-derived branch, or the restored production snapshot. A root branch
in the production project is not sufficient isolation: use a separate Neon
project. The current workflow intentionally blocks until that project, branch,
Auth configuration, runtime mapping, and attestations are ready.

After preflight, CI packages the extension from the exact PR merge candidate,
checks its archive digest and Auth/API origins, deploys that exact candidate to
the allowlisted Render staging service, and installs the package in Chromium.
Two dedicated synthetic users exercise sign-in, saved-report create/list/read/
update/delete, persistence after reload, user isolation, ownership checks,
cleanup, anonymous-history rejection, and loading/success/auth/API/timeout UI
states. The test blocks production API/Auth and unexpected external requests.
Persistent acceptance uses the live staging API and Neon Auth; mock results do
not satisfy it. The workflow captures sanitized evidence bound to the extension
ZIP, backend SHA, project/branch, and service identity.

The model gate is reported separately. Product CRUD evidence may identify
`model_quality=blocked`, but that cannot authorize release. Release staging and
production promotion require an approved representative held-out evaluation,
an AI/model-owner-approved numeric policy, immutable model/provider identity,
and the exact accepted model in staging. The checked-in policy remains pending
approval. A missing, disabled, unavailable, mocked, or unapproved model leaves
the release NO-GO.

## Secretary staging status

`Secretary staging` remains the stable required context. The new trusted
`workflow_run` bridge checks out default-branch code only and mirrors success for
a runtime PR only after the same latest CI run has passed Backend checks,
Extension checks, Staging integration, and Hosted staging. It does not deploy or
receive Render/Neon credentials. Missing, skipped, failed, stale, or pending
Hosted staging produces a non-green status. Documentation-only changes can be
marked not applicable only after ordinary CI succeeds.

GitHub executes `workflow_run` definitions from the default branch. Until a
reviewed bridge is on `main`, the branch cannot activate this new status logic.
Do not manually write a green status to bypass that boundary. Hosted staging
remains a direct required check and no live acceptance is claimed by this PR.

## Release promotion and production

`.github/workflows/release-promotion.yml` is manual-only. It builds one backend
image and one extension ZIP, records their immutable digests, tests those same
artifacts in a protected staging environment, and requires a distinct protected
production approval before promotion. It verifies the production SHA, provider,
health, readiness, exact image digest, manifest, version tag, and changelog
before publishing. Production is never deployed by PR acceptance.

Render production `srv-db7eap25b2lc73fkelpg` is Git-backed with auto-deploy off;
staging `srv-db92irlg1s2s739404i0` is also Git-backed. That read-only metadata
was checked on 2026-11-21. The release workflow refuses Git-backed targets, so
no digest promotion is possible yet. Changing Render's backing source triggers
a deploy; an administrator must schedule and approve a safe transition or
provision an image-backed replacement. No production setting was changed and no
production deployment was triggered by this work.

## Verified Neon and Render mapping

- Staging Neon project: `phishlens-staging`; root branch: `staging-root`;
  database: `phishlens_dev`.
- The startup pin is endpoint `ep-winter-wind-a1y2r1db` in
  `ap-southeast-1`; its direct and pooler hostnames are the accepted staging
  targets. `STAGING_DATABASE_HOST` and `STAGING_NEON_EXPECTED_HOST` must map
  to this endpoint.
- Render runtime `DATABASE_URL` uses the `phishlens_staging_app` role.
  `STAGING_MIGRATION_DATABASE_URL` uses a separate owner credential against
  the same staging database and endpoint. Keep both values in protected Render
  settings.
- Protected staging and production Neon project IDs and branch IDs remain
  distinct. The staging root requires an explicit schema-only attestation and
  an empty-parent attestation; production rows must be absent.
- Render staging service `srv-db92irlg1s2s739404i0` and production service
  `srv-db7eap25b2lc73fkelpg` were observed as Git-backed on 2026-11-21.
  The release workflow blocks digest promotion to Git-backed targets. Keep the
  Render-to-Neon/Auth mapping and repository source branch privately verified
  before deployment.

## Required external setup

Complete through protected GitHub/Render/Neon settings, not committed secrets:

1. Provision a Neon project separate from production, with a schema-only root
   branch, current migrations, Neon Auth, and no production rows.
2. Privately verify the Render staging service's runtime and migration URLs,
   database, branch, Auth mode, and separate least-privilege roles. Record the
   project IDs, branch IDs, endpoint hosts, and attestations in protected GitHub
   variables. Use a separate owner credential for migrations and an app role for
   runtime.
3. Create two empty synthetic Auth accounts and trust the extension ID as the
   Chrome origin. Configure protected `staging` reviewers and prevent self-review.
4. Set `SECRETARY_PREVIEW_ENABLED=true` only once all isolation and mapping
   checks are current. Keep production database URLs and credentials out of the
   staging environment.
5. Configure `release-staging` and `production` protected environments. The
   production approval must be independent of the source author.
6. Have the AI/model owner approve the quality-policy thresholds and a reviewed
   held-out report. Do not invent the approval or turn on production analysis to
   make the check green.
7. Schedule the Render Git-to-image source transition or a replacement service;
   switching the existing source can deploy, so it requires an approved
   maintenance/release window.

See [controlled release](controlled-release.md) for exact variables, gates, and
manifest contents. Never store secret values in source or evidence artifacts.

## Local and CI verification

Offline checks validate the workflow decision and evidence parsers; they do not
prove hosted Auth, persistent CRUD, provider quality, or production promotion.
Use the latest exact-head Actions run and its sanitized artifact for hosted
evidence. A previous PR's artifact or a different backend SHA cannot satisfy the
current candidate.

The older point-in-time records in this directory document their own historical
SHA and environment. They must not be described as acceptance for current main,
PR #266, or a later release unless the exact identity matches and the run is
repeated.

## Historical verification snapshots

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

### PR #268 follow-up — 2026-11-21 11:42 UTC

The next exact-head check on `e9451cc20928fefa7c0a6ded4803cebbad24ef42` passed Backend, Extension, migration preflight, Staging integration, workflow lint, dependency security/graph review, deterministic evaluation, and the Secretary report. Hosted staging preflight and Hosted staging were skipped. Required `Secretary staging` remains failed because the `needs-hosted-staging` label and exact-head hosted verification are absent. No current PR CodeQL result, Render deployment or authenticated CRUD was observed. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md) for run links. The release remains **NO-GO**; the descriptive DevOps evidence score remains 41/100.

### PR #268 retarget follow-up — 2026-11-21 11:57 UTC

PR #268 is now based on `main`; review branch head `77c0ed00e607c5580cedffadd031fe40ad71771b` includes the current `main` history. GitHub reports the PR open and mergeable, while the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. Exact-head CI passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security/graph review, deterministic evaluation, DevOps Secretary report and CodeQL. Hosted preflight/deployment were skipped; required `Secretary staging` remains failed because the hosted request label and exact-head hosted verification are absent. No Render deployment or authenticated hosted CRUD occurred. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md). Release remains **NO-GO** and the 41/100 descriptive evidence score is unchanged.

### PR #268 exact-head snapshot — 2026-11-21 12:02 UTC

Retargeted PR #268 head `1fa2e7827cfe84de425afcc7885743bd55b2a382` passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security and graph review, deterministic evaluation, DevOps Secretary report, and all three CodeQL analyses. [CI run 44901642617](https://github.com/kendshhh/PhishLens/actions/runs/44901642617) completed at 12:02 UTC. Hosted staging preflight and Hosted staging were skipped. The required `Secretary staging` status failed because the `needs-hosted-staging` label and exact-head hosted verification were absent ([assessment 44901931269](https://github.com/kendshhh/PhishLens/actions/runs/44901931269)); no Render deployment or authenticated hosted CRUD occurred. GitHub reports the PR open and mergeable on `main`; the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. The release remains **NO-GO**, and 41/100 is a descriptive evidence-progress score only. This documentation-only evidence update requires fresh exact-head CI before merge. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).

### PR #268 main-sync snapshot — 2026-11-21 12:14 UTC

PR #268 now includes current `main` through `31e86c7` in merge head `aee49fe5a11da37ed441464c80ad9a09e0b9dda8`. Exact-head CI run [44902645800](https://github.com/kendshhh/PhishLens/actions/runs/44902645800) passed Backend, Extension, Staging integration and migration preflight. Workflow lint [44902645811](https://github.com/kendshhh/PhishLens/actions/runs/44902645811), dependency security/graph [44902645851](https://github.com/kendshhh/PhishLens/actions/runs/44902645851), deterministic evaluation [44902645832](https://github.com/kendshhh/PhishLens/actions/runs/44902645832), and CodeQL [44902643383](https://github.com/kendshhh/PhishLens/actions/runs/44902643383) passed. The exact-head DevOps Secretary report was cancelled during the branch sync ([44902644757](https://github.com/kendshhh/PhishLens/actions/runs/44902644757)); the Secretary preview assessment reports required `Secretary staging` failure because the `needs-hosted-staging` label and exact-head hosted verification are absent ([44902874550](https://github.com/kendshhh/PhishLens/actions/runs/44902874550)). Hosted preflight/deployment were skipped; no Render deploy or authenticated CRUD occurred. GitHub shows PR #268 open, mergeable on `main`, with review decision `CHANGES_REQUESTED`. Release remains **NO-GO**; 41/100 is descriptive evidence progress, not completion. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).
