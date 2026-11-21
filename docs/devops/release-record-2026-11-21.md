# Release record — 2026-11-21

## Decision

**NO-GO.** This dated record reconciles the latest available repository,
Render, Neon and user-supplied CI evidence. It does not authorize deployment or
claim product acceptance. The Chrome Manifest V3 extension backed by the
Render API and Neon remains the intended release scope. Instructor confirmation
of the frontend requirement remains outstanding. The [scorecard](release-readiness-scorecard-2026-11-21.md)
reports a descriptive 41/100 result for its fixed 16-item evidence checklist;
this is not a course grade or project-completion percentage. None of the seven
release areas meets its full pass definition, and no weighted seven-area score
is calculated because the weights are not approved.

## Candidate and deployment identities

| Component | Observed identity | Evidence and acceptance state |
|---|---|---|
| Review source | PR #268, branch `codex/devops-staging-closeout-20261121`; at the 08:53 UTC audit cutoff its head was `d447b3c537bc24ec9b7c7ed0ba6f34b7316826d2`, a documentation sync. Latest code/test commit `83a0df1af1d64048b3b5fa3158f6509e83d71555` is synchronized with `main` `06f89d7a0b5b9dec316dfa11f2846767a32086c5` through merge commit `14874d339bbb4042172df954f97596080aa303ee`. Earlier implementation commit `a80b95e146cd03a96ffca156ccfe5721ac871b68` and staging-history base `3c858f7df51666e0545dea1a6dd5997574c16d43` remain in its history. | That observed PR #268 head passed Backend, Extension and Staging integration in [run 44886742192](https://github.com/kendshhh/PhishLens/actions/runs/44886742192); hosted staging was skipped. PR #268 is open and its changes are not merged into `main`. |
| Production API | Last observed at 07:31 UTC: Render deploy `dep-dc07rs67bikc73fjgjq0`, source SHA `811980c2cbf70d9957146bf329627f0826a018f1`. | Render reported live. Main later advanced to `06f89d7a0b5b9dec316dfa11f2846767a32086c5`; no later production deployment was verified. At the observed deploy, read-only `/version`, `/health`, `/ready` and `/model-info` returned HTTP 200. Model info said `analysis_enabled=false`, `provider_mode=disabled`, `supports_required_provider=false`, and `accepts_tfidf_reports=false`. No production inference or saved-report write was made; the production smoke workflow was not run. This is service-state evidence, not product acceptance. |
| Staging API | Render deploy `dep-dc0im3h7lnhs738pncng`, source SHA `ba0b6c5475eb6a8f99c509c40384020d292e17e6`. | Render reports live. Read-only `/version`, `/health`, `/ready` and `/model-info` returned HTTP 200; model info reports TF-IDF and model SHA-256 `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`. Anonymous `/api/analyses` returns `401` with `WWW-Authenticate: Bearer`. GET-only smokes at 08:15 and about 08:35 UTC passed health, readiness and the anonymous auth boundary; neither verified deployed PR identity. No authenticated CRUD acceptance is established. |
| Extension build | PhishLens-Extension artifact ID `14651606496` from [CI run 44779598624](https://github.com/kendshhh/PhishLens/actions/runs/44779598624), source SHA `811980c2cbf70d9957146bf329627f0826a018f1`; archive digest `sha256:8f07bf6fd9e5844ee541b4c13439cd32b57d231ca8c297bbd5513346bc17244d`, expires November 27. | This artifact is tied to the earlier `811980c` source, not current main `06f89d7`. The digest is GitHub's artifact archive digest, not a separately verified ZIP SHA-256. No accepted extension/backend/model manifest is published. |
| Browser acceptance evidence | Extension-Browser-Acceptance artifact ID `14652195937` from CI run `44779598624`, source SHA `811980c2cbf70d9957146bf329627f0826a018f1`; digest `sha256:e953b567b84d99f70182b5a7fb22eedc4f3876b467a804f27cdcfe2e745b6c1b`, expires February 18, 2027. | Packaged browser checks ran for the earlier main source. The later main CI run for `06f89d7` failed at packaged-extension Chromium browser acceptance; see the current workflow evidence below. This artifact does not establish acceptance for current main or authenticated live staging. |
| Model/provider | Main's 40-case synthetic result recorded 65% accuracy, 18.75% phishing recall (3/16) and 6.25% legitimate false positives (1/16). Frozen English source-pair TF-IDF v12a evaluation recorded 190/200 phishing recall, 1/999 legitimate false positives and 1,200 valid outputs. | Both are advisory evidence only. A 12-case synthetic diagnostic detected 1/12. There is no approved broad release threshold, contemporary held-out cohort or human explanation review. Production's last observed model-info response reported `analysis_enabled=false` and `provider_mode=disabled`; production analysis remains unaccepted. |
| Staging Auth/database | Neon project `patient-bird-25428852`; staging branch `pr-58-staging` / `br-delicate-paper-b381z98i`; database `phishlens_dev`; Auth DB `neondb`; observed migration head `0004_neon_auth_subject`. | Read-only Neon Auth config and SQL/grant inspection are recorded in the evidence record. Runtime role can read/insert users and perform saved-report CRUD; public schema CREATE is false; users UPDATE/DELETE are false. This does not prove Render's private `DATABASE_URL` resolves to this exact branch/role. No SQL write was made. GitHub reports 15 open Dependabot alerts despite observed `main` pinning first-patched versions; reconciliation is pending. |
| Staging smoke and hosted deploy guard | Latest code/test commit `83a0df1af1d64048b3b5fa3158f6509e83d71555`; PR #268 head observed at 08:53 UTC was `d447b3c537bc24ec9b7c7ed0ba6f34b7316826d2`; merge commit `14874d339bbb4042172df954f97596080aa303ee` integrates mainline Bearer-aware correction `06f89d7a0b5b9dec316dfa11f2846767a32086c5`. | Local Node tests passed (321), and the GET-only live staging smoke passed at about 08:35 UTC with health/readiness and anonymous `401 Bearer`. That observed PR head's run [44886742192](https://github.com/kendshhh/PhishLens/actions/runs/44886742192) passed Backend, Extension and Staging integration; hosted staging was skipped. Earlier pre-sync CI runs [44883590782](https://github.com/kendshhh/PhishLens/actions/runs/44883590782) and [44884534992](https://github.com/kendshhh/PhishLens/actions/runs/44884534992) are historical. The previous Secretary check [44884776725](https://github.com/kendshhh/PhishLens/actions/runs/44884776725) required `needs-hosted-staging` and exact-head verification. No Render deployment was made. |
| Hosted CRUD runner | `origin/main` `.github/workflows/ci.yml` invokes `scripts/verify_crud.mjs --allow-writes` after the legacy smoke. | The current observed code path has no authenticated session for Neon Auth. It is a separate blocker that the anonymous smoke adjustment does not resolve. Fix the runner to obtain an approved synthetic test session and authenticate all operations; retain cleanup and least privilege. Do not disable auth or use a database bypass. |
| Production smoke | `origin/main` contains the disabled-provider observer path. | Source inspection shows it can report a bounded observer pass for disabled mode with zero inference, paid provider calls and database writes. No workflow execution was run, and this result cannot pass product/AI acceptance. |
| Recovery evidence | Isolated Neon restore drill, November 20, on upstream `main`. | The drill checked revision, schema shape and aggregate counts on an isolated restored branch. RTO/RPO remain unmeasured; service-to-branch mapping and compatible application rollback remain open. [Read the source record](https://github.com/kendshhh/PhishLens/blob/811980c2cbf70d9957146bf329627f0826a018f1/docs/devops/recovery-drill-2026-11-20.md). |

## Current workflow evidence

The following runs for the earlier main SHA `811980c2cbf70d9957146bf329627f0826a018f1`
passed: [CI 44779598624](https://github.com/kendshhh/PhishLens/actions/runs/44779598624),
[deterministic AI evaluation 44779598647](https://github.com/kendshhh/PhishLens/actions/runs/44779598647),
[workflow lint 44779598943](https://github.com/kendshhh/PhishLens/actions/runs/44779598943),
[dependency security 44779598600](https://github.com/kendshhh/PhishLens/actions/runs/44779598600),
and [CodeQL 44779598763](https://github.com/kendshhh/PhishLens/actions/runs/44779598763).
These do not represent current main, which has advanced to `06f89d7`.

Current main CI [44885148600](https://github.com/kendshhh/PhishLens/actions/runs/44885148600)
failed at packaged-extension Chromium browser acceptance; Backend checks passed.
[Workflow lint 44885148613](https://github.com/kendshhh/PhishLens/actions/runs/44885148613)
and [dependency security 44885148629](https://github.com/kendshhh/PhishLens/actions/runs/44885148629)
passed. PR #268's current head `d447b3c537bc24ec9b7c7ed0ba6f34b7316826d2`
passed Backend, Extension and Staging integration in
[run 44886742192](https://github.com/kendshhh/PhishLens/actions/runs/44886742192);
hosted staging was skipped. These are different refs, so the PR pass does not
clear the mainline browser-acceptance failure.

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
out; later GET-only runs at 08:15 and about 08:35 UTC passed health, readiness
and the expected `401 Bearer` boundary, but did not confirm the original run's response or
deployed source SHA. The environment map and production smoke notes retain the
current service identities and the limits of the GET-only checks.

The fix has two separate parts:

1. **Anonymous preflight and CI safety:** recognize and assert `401 Bearer` when
   no session is supplied; retain seeded demo-history checks only for legacy
   unauthenticated `200` mode. Bound transient retries, report failure details,
   detect an exited local service promptly, retain its log, and make hosted
   deploy depend explicitly on all successful gates. Mainline commit `06f89d7`
   already contains the strict Bearer-aware history correction; the review
   branch adds bounded retries, detailed diagnostics, local server monitoring,
   retained logs and fail-closed deployment conditions. Those additional
   changes remain under review and are not merged.
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

The scorecard's 41/100 value is a descriptive, equally weighted 16-item DevOps
evidence-progress indicator; it is not a course grade or project-completion
percentage. The separate seven-area weighted release score is not calculated
because its weights and rule are not approved. Do not call the project 100% ready
or convert partial artifacts into full passes. Keep release issue #153 at
**NO-GO** until the release owner and reviewers accept evidence tied to the same
final candidate.
