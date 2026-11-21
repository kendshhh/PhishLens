# Release record — 2026-11-21

## Decision

**NO-GO.** This dated record reconciles the latest available repository,
Render, Neon and user-supplied CI evidence. It does not authorize deployment or
claim product acceptance. The Chrome Manifest V3 extension backed by the
Render API and Neon remains the intended release scope. Instructor confirmation
of the frontend requirement remains outstanding.

## Candidate and deployment identities

| Component | Observed identity | Evidence and acceptance state |
|---|---|---|
| Review source | PR #268, branch `codex/devops-staging-closeout-20261121`, current head `a2fb3f79e7857eeef20a2a2cf70f603906d86f31` (docs-only); latest code/test SHA `d27eaa07a28173c485d19f44524a88e71515fc10`; implementation commit `a80b95e146cd03a96ffca156ccfe5721ac871b68`, based on `3c858f7df51666e0545dea1a6dd5997574c16d43`, a descendant of observed `main` `811980c2cbf70d9957146bf329627f0826a018f1`. | Prepared in a clean isolated worktree. The original developer checkout at `16f955321caf5dc368181be7ce5c00643750545d` and its existing edits remain untouched. PR #268 is open and not merged into `main`. |
| Production API | Render deploy `dep-dc07rs67bikc73fjgjq0`, source SHA `811980c2cbf70d9957146bf329627f0826a018f1`. | Render reports live. Read-only `/version`, `/health`, `/ready` and `/model-info` returned HTTP 200. Model info says `analysis_enabled=false`, `provider_mode=disabled`, `supports_required_provider=false`, and `accepts_tfidf_reports=false`. No production inference or saved-report write was made; the production smoke workflow was not run. This is service-state evidence, not product acceptance. |
| Staging API | Render deploy `dep-dc0im3h7lnhs738pncng`, source SHA `ba0b6c5475eb6a8f99c509c40384020d292e17e6`. | Render reports live. Read-only `/version`, `/health`, `/ready` and `/model-info` returned HTTP 200; model info reports TF-IDF and model SHA-256 `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`. Anonymous `/api/analyses` returns `401` with `WWW-Authenticate: Bearer`. No authenticated CRUD acceptance is established. |
| Staging Auth/database | Neon project `patient-bird-25428852`; staging branch `pr-58-staging` / `br-delicate-paper-b381z98i`; database `phishlens_dev`; Auth DB `neondb`; observed migration head `0004_neon_auth_subject`. | Read-only Neon Auth config and SQL/grant inspection are recorded in the evidence record. Runtime role can read/insert users and perform saved-report CRUD; public schema CREATE is false; users UPDATE/DELETE are false. This does not prove Render's private `DATABASE_URL` resolves to this exact branch/role. No SQL write was made. GitHub reports 15 open Dependabot alerts despite observed `main` pinning first-patched versions; reconciliation is pending. |
| Staging smoke and hosted deploy guard | Implementation commit `a80b95e146cd03a96ffca156ccfe5721ac871b68`; code/test SHA `d27eaa07a28173c485d19f44524a88e71515fc10`; current docs-only PR head `a2fb3f79e7857eeef20a2a2cf70f603906d86f31`. | CI run [44883590782](https://github.com/kendshhh/PhishLens/actions/runs/44883590782) passed local staging and deployment-guard tests; docs-only head passed [44884534992](https://github.com/kendshhh/PhishLens/actions/runs/44884534992). A separate direct GET-only staging smoke passed at 08:15 UTC. Hosted staging and its preflight were skipped. Secretary staging run [44884776725](https://github.com/kendshhh/PhishLens/actions/runs/44884776725) requires `needs-hosted-staging` and exact-head hosted verification. No Render deployment was made. |
| Hosted CRUD runner | `origin/main` `.github/workflows/ci.yml` invokes `scripts/verify_crud.mjs --allow-writes` after the legacy smoke. | The current observed code path has no authenticated session for Neon Auth. It is a separate blocker that the anonymous smoke adjustment does not resolve. Fix the runner to obtain an approved synthetic test session and authenticate all operations; retain cleanup and least privilege. Do not disable auth or use a database bypass. |
| Production smoke | `origin/main` contains the disabled-provider observer path. | Source inspection shows it can report a bounded observer pass for disabled mode with zero inference, paid provider calls and database writes. No workflow execution was run, and this result cannot pass product/AI acceptance. |
| Recovery evidence | Isolated Neon restore drill, November 20, on upstream `main`. | The drill checked revision, schema shape and aggregate counts on an isolated restored branch. RTO/RPO remain unmeasured; service-to-branch mapping and compatible application rollback remain open. [Read the source record](https://github.com/kendshhh/PhishLens/blob/811980c2cbf70d9957146bf329627f0826a018f1/docs/devops/recovery-drill-2026-11-20.md). |

## Failure record and cause

The user-supplied job output shows `STAGING_MIGRATION_REVISION` set to
`0004_neon_auth_subject` and `node scripts/staging_smoke.mjs` failing at the
history request with `Error: Failed to load history` from
`extension/js/api.js:111`, called at `scripts/staging_smoke.mjs:27`. The log
also sets `STAGING_BASE_URL` to the staging service, but it did not include a
GitHub Actions run URL/ID, tested commit SHA, or full HTTP response. The
migration head was independently checked on Neon; the smoke script does not
verify it.
In a separate dated read-only staging observation, anonymous history returned
the expected authentication challenge (`401 Bearer`) because saved reports
require sign-in. No run ID or tested SHA establishes that it was the same
deployment/run as the supplied failure, so this is a plausible cause, not a
confirmed diagnosis. The legacy smoke assumed anonymous history was readable
and treated that boundary as a failure. An earlier workstation probe timed
out; a later GET-only run at 08:15 UTC passed health, readiness and the expected
`401 Bearer` boundary, but did not confirm the original run's response or
deployed source SHA. See the
[dated failure analysis](evidence/2026-11-21-staging-neon-auth-smoke.md).

The fix has two separate parts:

1. **Anonymous preflight and CI safety:** recognize and assert `401 Bearer` when
   no session is supplied; retain seeded demo-history checks only for legacy
   unauthenticated `200` mode. Bound transient retries, report failure details,
   detect an exited local service promptly, retain its log, and make hosted
   deploy depend explicitly on all successful gates. The implementation is on
   the review branch and is not yet in `main`.
2. **Authenticated acceptance:** teach `verify_crud.mjs` to use a dedicated
   synthetic staging identity and valid Auth session, then prove sign-in,
   create/list/read/update/delete, reload persistence, ownership isolation,
   failure cases and cleanup. The current unauthenticated runner is still a
   blocker. Never weaken authorization to make CI green.

## Remaining release gates

- [ ] Review and land the exact review-branch source through the trusted
  controller path; select one extension/backend/model/Auth candidate and retain
  package and source hashes.
- [ ] Run the protected hosted workflow on a current PR head and make the
  authenticated CRUD job work with a least-privilege synthetic test user.
- [ ] Complete the protected exact-head Hosted staging run; the current PR's
  Hosted staging jobs are skipped until `needs-hosted-staging` is present.
- [ ] Pass hosted staging smoke plus authenticated CRUD, persistence,
  ownership/isolation, failure and cleanup checks; install and accept the exact
  extension package in Chrome.
- [ ] Privately verify Render-to-Neon project/branch/database/role mapping for
  staging and production, current Auth/provider settings, GitHub environment
  scope and reviewer controls.
- [ ] Reconcile the 15 open GitHub Dependabot alert records with the pinned and
  resolved default-branch dependencies; preserve a fresh dependency-review
  result before calling the security gate clear.
- [ ] Reconcile Render's auto-deploy-off metadata with production's observed
  `new_commit` deploy trigger. Verify settings in the Render dashboard.
- [ ] Verify the effective GitHub required-check contract and independent
  review on the final candidate.
- [ ] Approve broad model-quality criteria and contemporary held-out evidence;
  the existing frozen English source-pair result remains advisory-only.
- [ ] Record a schema/config-compatible application rollback, isolated data
  restore, measured service RTO/RPO, recovery responders and alert path.
- [ ] Obtain actual team/instructor decisions and participant records; publish
  the release tag and changelog only after all gates pass.

No completion percentage is reported. The scoring weights and rule are not
approved; do not call the project 100% ready or convert partial artifacts into
full passes. Keep release issue #153 at **NO-GO** until the release owner and
reviewers accept evidence tied to the same final candidate.
