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

### Earlier PR #268 check snapshot — 2026-11-21 11:08 UTC

PR #268 head is `a151585ff92d55f21e0364e9838287a9cf04a68d`, the documentation
reconciliation commit. Backend and migration source preflight passed in
[CI 44897548076](https://github.com/kendshhh/PhishLens/actions/runs/44897548076);
workflow lint [44897548088](https://github.com/kendshhh/PhishLens/actions/runs/44897548088),
dependency security and graph review [44897548010](https://github.com/kendshhh/PhishLens/actions/runs/44897548010),
deterministic evaluation [44897548070](https://github.com/kendshhh/PhishLens/actions/runs/44897548070),
and the DevOps Secretary report [44897544530](https://github.com/kendshhh/PhishLens/actions/runs/44897544530)
passed. `Extension checks` failed at the keyboard Tab-order assertion in
`scripts/browser_acceptance.mjs:700`: “Saved reports view: Tab must reach the
popup controls.” Staging integration, Hosted staging preflight and Hosted
staging were skipped. Required `Secretary staging` failed because the request
label and exact-head hosted verification were absent
([run 44897660167](https://github.com/kendshhh/PhishLens/actions/runs/44897660167)).
No current PR CodeQL result appeared. No Render deployment or authenticated
CRUD occurred. PR #268 remains open and targets the merged
`codex/readiness-update-20261121` base; retargeting remains outstanding. The
full run was a failed/blocked candidate snapshot, not release acceptance.
The same keyboard-focus assertion also failed on `06f89d7` in [CI
44885148600](https://github.com/kendshhh/PhishLens/actions/runs/44885148600),
while the later merged-main snapshot `95975cd` passed in [CI
44889931821](https://github.com/kendshhh/PhishLens/actions/runs/44889931821).
The recurrence remains undiagnosed; the evidence does not distinguish a
browser timing issue from a UI or test defect.

### Previous completed PR #268 check snapshot — 2026-11-21 11:21 UTC

The 11:21 completed workflow results were for docs-only head
`dffdc4c29338142f458350b51c8ce69e0f36e988`; the later docs-only follow-up is
recorded below. Backend, Extension, migration preflight,
Staging integration passed in [CI 44898467208](https://github.com/kendshhh/PhishLens/actions/runs/44898467208).
Workflow lint [44898467185](https://github.com/kendshhh/PhishLens/actions/runs/44898467185),
dependency security and graph review [44898467124](https://github.com/kendshhh/PhishLens/actions/runs/44898467124),
deterministic evaluation [44898467190](https://github.com/kendshhh/PhishLens/actions/runs/44898467190),
and the DevOps Secretary report [44898465856](https://github.com/kendshhh/PhishLens/actions/runs/44898465856)
passed. Hosted staging preflight and Hosted staging were skipped. Required
`Secretary staging` failed because the request label and exact-head hosted
verification were absent ([run 44898698685](https://github.com/kendshhh/PhishLens/actions/runs/44898698685)).
No current PR CodeQL result appeared. No Render deployment or authenticated
CRUD occurred. PR #268 remains open and targets the merged
`codex/readiness-update-20261121` base; retargeting remains outstanding. The
candidate is not release accepted.

The keyboard-focus assertion failed on `a151585` and previously on `06f89d7`,
but passed on docs-only follow-up `dffdc4c` and merged main `95975cd`. This
pattern suggests intermittent behavior, but its root cause remains unverified;
do not label it a confirmed flake without reproducing and diagnosing it.

### Latest completed PR #268 check snapshot — 2026-11-21 11:31 UTC

The latest completed workflow results are for docs-only head
`f79098cc075784563d2022cbca87d7abe8f0a635`; the current docs-only sync needs
its own checks. Backend, Extension, migration preflight and Staging integration
passed in [CI 44899191736](https://github.com/kendshhh/PhishLens/actions/runs/44899191736).
Workflow lint [44899191771](https://github.com/kendshhh/PhishLens/actions/runs/44899191771),
dependency security and graph review [44899191710](https://github.com/kendshhh/PhishLens/actions/runs/44899191710),
deterministic evaluation [44899191787](https://github.com/kendshhh/PhishLens/actions/runs/44899191787),
and the DevOps Secretary report [44899190365](https://github.com/kendshhh/PhishLens/actions/runs/44899190365)
passed. Hosted staging preflight and Hosted staging were skipped. Required
`Secretary staging` failed because the request label and exact-head hosted
verification were absent ([run 44899423134](https://github.com/kendshhh/PhishLens/actions/runs/44899423134)).
No current PR CodeQL result appeared. No Render deployment or authenticated
CRUD occurred. PR #268 remains open and targets the merged
`codex/readiness-update-20261121` base; retargeting remains outstanding.

The Saved reports keyboard-focus assertion failed on `a151585`, then passed on
`dffdc4c` and `f79098c` without code changes. It also failed earlier on `06f89d7`
and passed on merged main `95975cd`. This is repeated intermittent behavior;
its cause has not been established.

| Component | Observed identity | Evidence and acceptance state |
|---|---|---|
| Review source | PR #268, branch `codex/devops-staging-closeout-20261121`; latest completed check head at 11:31 UTC is `f79098cc075784563d2022cbca87d7abe8f0a635`, followed by a docs-only sync. Code/test commit `83a0df1af1d64048b3b5fa3158f6509e83d71555` is synchronized with the Bearer-aware main code through merge commit `14874d339bbb4042172df954f97596080aa303ee`; shared docs from PR #265 are at `ca29235`. | On `f79098c`, Backend, Extension, migration preflight, Staging integration, workflow lint, dependency security/graph, deterministic evaluation and the Secretary report passed. Hosted staging/preflight were skipped; required `Secretary staging` failed ([CI 44899191736](https://github.com/kendshhh/PhishLens/actions/runs/44899191736), [Secretary staging 44899423134](https://github.com/kendshhh/PhishLens/actions/runs/44899423134)). No current PR CodeQL result, Render deployment or authenticated CRUD. PR #268 is still open and targets the old PR #265 branch, now merged into main at `95975cd`; retarget to `main` before merging. |
| Production API | Last observed at 07:31 UTC: Render deploy `dep-dc07rs67bikc73fjgjq0`, source SHA `811980c2cbf70d9957146bf329627f0826a018f1`. | Render reported live. Main later advanced first to `06f89d7` and then to merged main `95975cd47dceeac74ea36054610956f0a1db1fa9`; no later production deployment was verified. At the observed deploy, read-only `/version`, `/health`, `/ready` and `/model-info` returned HTTP 200. Model info said `analysis_enabled=false`, `provider_mode=disabled`, `supports_required_provider=false`, and `accepts_tfidf_reports=false`. No production inference or saved-report write was made; the production smoke workflow was not run. This is service-state evidence, not product acceptance. |
| Staging API | Render deploy `dep-dc0im3h7lnhs738pncng`, source SHA `ba0b6c5475eb6a8f99c509c40384020d292e17e6`. | Render reports live. Read-only `/version`, `/health`, `/ready` and `/model-info` returned HTTP 200; model info reports TF-IDF and model SHA-256 `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`. Anonymous `/api/analyses` returns `401` with `WWW-Authenticate: Bearer`. GET-only smokes at 08:15 and about 08:35 UTC passed health, readiness and the anonymous auth boundary; neither verified deployed PR identity. No authenticated CRUD acceptance is established. |
| Extension build | PhishLens-Extension artifact ID `14651606496` from [CI run 44779598624](https://github.com/kendshhh/PhishLens/actions/runs/44779598624), source SHA `811980c2cbf70d9957146bf329627f0826a018f1`; archive digest `sha256:8f07bf6fd9e5844ee541b4c13439cd32b57d231ca8c297bbd5513346bc17244d`, expires November 27. | This artifact is tied to the earlier `811980c` source, not current main `95975cd`. The digest is GitHub's artifact archive digest, not a separately verified ZIP SHA-256. No accepted extension/backend/model manifest is published. |
| Browser acceptance evidence | Extension-Browser-Acceptance artifact ID `14652195937` from CI run `44779598624`, source SHA `811980c2cbf70d9957146bf329627f0826a018f1`; digest `sha256:e953b567b84d99f70182b5a7fb22eedc4f3876b467a804f27cdcfe2e745b6c1b`, expires February 18, 2027. | Packaged browser checks ran for the earlier main source. The later main CI run for `06f89d7` failed at packaged-extension Chromium browser acceptance; see the current workflow evidence below. This artifact does not establish acceptance for current main or authenticated live staging. |
| Model/provider | Main's 40-case synthetic result recorded 65% accuracy, 18.75% phishing recall (3/16) and 6.25% legitimate false positives (1/16). Frozen English source-pair TF-IDF v12a evaluation recorded 190/200 phishing recall, 1/999 legitimate false positives and 1,200 valid outputs. | Both are advisory evidence only. A 12-case synthetic diagnostic detected 1/12. There is no approved broad release threshold, contemporary held-out cohort or human explanation review. Production's last observed model-info response reported `analysis_enabled=false` and `provider_mode=disabled`; production analysis remains unaccepted. |
| Staging Auth/database | Neon project `patient-bird-25428852`; staging branch `pr-58-staging` / `br-delicate-paper-b381z98i`; database `phishlens_dev`; Auth DB `neondb`; observed migration head `0004_neon_auth_subject`. | Read-only Neon Auth config and SQL/grant inspection are recorded in the evidence record. Runtime role can read/insert users and perform saved-report CRUD; public schema CREATE is false; users UPDATE/DELETE are false. This does not prove Render's private `DATABASE_URL` resolves to this exact branch/role. No SQL write was made. GitHub enabled Dependency graph and vulnerability alerts on November 21; Dependency graph review now passes on PR #268. There are still 15 open Dependabot alerts (12 high, 3 moderate), requiring review/remediation. |
| Staging smoke and hosted deploy guard | Latest code/test commit `83a0df1af1d64048b3b5fa3158f6509e83d71555`; latest completed PR head `f79098cc075784563d2022cbca87d7abe8f0a635`; mainline Bearer-aware correction is `06f89d7`, integrated in merge commit `14874d339bbb4042172df954f97596080aa303ee`. | Local Node tests passed (321), and a GET-only live staging smoke passed at about 08:35 UTC with health/readiness and anonymous `401 Bearer`. On `f79098c`, Backend, Extension, migration preflight and local Staging integration passed; see [CI 44899191736](https://github.com/kendshhh/PhishLens/actions/runs/44899191736). Hosted preflight/deployment were skipped, and required `Secretary staging` failed in [run 44899423134](https://github.com/kendshhh/PhishLens/actions/runs/44899423134). No Render deployment or authenticated CRUD occurred. |
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
These do not represent current main, which has advanced through `06f89d7` to
`95975cd`.

The CI failure at packaged-extension Chromium browser acceptance on `06f89d7`
in [run 44885148600](https://github.com/kendshhh/PhishLens/actions/runs/44885148600)
is historical. PR #265 merged to main at `95975cd47dceeac74ea36054610956f0a1db1fa9`;
the merged main snapshot passed [CI 44889931821](https://github.com/kendshhh/PhishLens/actions/runs/44889931821),
[CodeQL 44889931096](https://github.com/kendshhh/PhishLens/actions/runs/44889931096),
[workflow lint 44889931690](https://github.com/kendshhh/PhishLens/actions/runs/44889931690)
and [dependency security 44889931677](https://github.com/kendshhh/PhishLens/actions/runs/44889931677).

### PR #268 latest check snapshot — 2026-11-21 09:42 UTC

Remote head `def5e9b3d925e94a9aa664a24f90c73b960c7f99` passed Backend,
Extension, migration source preflight, Staging integration, workflow lint,
Dependency security, Dependency graph review and deterministic evaluation.
See [CI 44890690426](https://github.com/kendshhh/PhishLens/actions/runs/44890690426),
[workflow lint 44890690321](https://github.com/kendshhh/PhishLens/actions/runs/44890690321),
[dependency checks 44890690295](https://github.com/kendshhh/PhishLens/actions/runs/44890690295)
and [deterministic evaluation 44890690376](https://github.com/kendshhh/PhishLens/actions/runs/44890690376).
Hosted preflight and deployment were skipped. No CodeQL check was present on
this head; its preceding run on `7dbebfd` failed due to Actions installation API
rate limits. GitHub subsequently enabled Dependency graph, allowing its PR check
to pass. The repository still has 15 open Dependabot alerts (12 high, 3
moderate), documented in [CI maintenance](ci-maintenance.md) and the
[dependency audit](dependency-audits.md).

PR #268 remains open and its base is still `codex/readiness-update-20261121`
at `ca29235`, which has merged into main. Retarget the PR to `main` before
merging. The PR check results do not establish a hosted deployment or Auth CRUD.

### PR #268 exact-head check snapshot — 2026-11-21 10:14 UTC

PR #268 head `2e26327254c71b6cb7d655181cffb21e8dd1ee9b` passed Backend,
Extension, migration source preflight, Staging integration and hosted preflight
in [CI 44891131201](https://github.com/kendshhh/PhishLens/actions/runs/44891131201).
Workflow lint [44891131261](https://github.com/kendshhh/PhishLens/actions/runs/44891131261),
Dependency security and Dependency graph review
[44891131162](https://github.com/kendshhh/PhishLens/actions/runs/44891131162),
and deterministic evaluation
[44891131190](https://github.com/kendshhh/PhishLens/actions/runs/44891131190)
passed. Hosted staging job [136807616481](https://github.com/kendshhh/PhishLens/actions/runs/44891131201/job/136807616481)
completed with conclusion `success`, but its final pre-deployment recheck set
`current=false` and classified the run as superseded after the request label
was removed at 09:54 UTC. Render deployment, hosted API smoke, authenticated
CRUD, finalization and artifact steps were skipped. The job summary marks the
run **blocked**, not hosted acceptance. The separate required `Secretary
staging` status failed because the request label and exact-head hosted
verification were absent ([run 44892082807](https://github.com/kendshhh/PhishLens/actions/runs/44892082807)).
No current CodeQL check appeared. No Render deployment or authenticated CRUD
is verified. The head is an empty CI-trigger commit, so the pending docs update
needs its own fresh checks. PR #268 remains based on the
merged `codex/readiness-update-20261121` branch and must be retargeted to `main`
before merge. The 15 open Dependabot alerts (12 high, 3 moderate) remain open.

### PR #268 check snapshot — 2026-11-21 09:22 UTC

GitHub reported the remote PR head as
`7dbebfd060298a80e99a38a52663901e776935cb`, after the PR #265 documentation
reconciliation. Backend, Extension and migration source preflight passed in
[run 44889070392](https://github.com/kendshhh/PhishLens/actions/runs/44889070392);
Staging integration was still in progress. [Workflow lint
44889070441](https://github.com/kendshhh/PhishLens/actions/runs/44889070441),
[dependency security 44889070418](https://github.com/kendshhh/PhishLens/actions/runs/44889070418)
and [deterministic evaluation
44889070455](https://github.com/kendshhh/PhishLens/actions/runs/44889070455)
passed. The dependency graph review in run 44889070418 failed; CodeQL
[44889065082](https://github.com/kendshhh/PhishLens/actions/runs/44889065082)
was still in progress. Secretary report
[44889108682](https://github.com/kendshhh/PhishLens/actions/runs/44889108682)
said **WAITING FOR CHECKS**. Hosted staging was not requested, and no Render
deployment or authenticated CRUD occurred. These results are specific to
`7dbebfd`; the subsequent evidence-sync commit needs fresh checks. Do not count
the in-progress or failed contexts as passes.

### Settled check state — 2026-11-21 09:31 UTC

The same remote head `7dbebfd060298a80e99a38a52663901e776935cb` later showed
Staging integration **success**. Hosted staging and hosted preflight remained
**skipped**. The three CodeQL language-analysis jobs in run 44889065082
completed **failure**; their GitHub annotations attribute this to Actions
installation API rate limits, not a reported CodeQL finding. Dependency graph
review remained **failure** because GitHub says the repository Dependency graph
is disabled ([job log
136800698597](https://github.com/kendshhh/PhishLens/actions/runs/44889070418/job/136800698597)).
No hosted deploy or authenticated CRUD was run. These are statuses for the
prior head only; the subsequent docs commit must pass fresh required checks.

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
- [ ] Complete the protected exact-head Hosted staging run. The latest job's
  final pre-deployment freshness guard blocked execution after the request
  label was removed at 09:54 UTC; the required `Secretary staging` status
  failed. Do not re-request the deployment until an owner authorizes the
  staging write and authenticated CRUD scope.
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

### PR #268 follow-up — 2026-11-21 11:42 UTC

The next exact-head check on `e9451cc20928fefa7c0a6ded4803cebbad24ef42` passed Backend, Extension, migration preflight, Staging integration, workflow lint, dependency security/graph review, deterministic evaluation, and the Secretary report. Hosted staging preflight and Hosted staging were skipped. Required `Secretary staging` remains failed because the `needs-hosted-staging` label and exact-head hosted verification are absent. No current PR CodeQL result, Render deployment or authenticated CRUD was observed. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md) for run links. The release remains **NO-GO**; the descriptive DevOps evidence score remains 41/100.

### PR #268 retarget follow-up — 2026-11-21 11:57 UTC

PR #268 is now based on `main`; review branch head `77c0ed00e607c5580cedffadd031fe40ad71771b` includes the current `main` history. GitHub reports the PR open and mergeable, while the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. Exact-head CI passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security/graph review, deterministic evaluation, DevOps Secretary report and CodeQL. Hosted preflight/deployment were skipped; required `Secretary staging` remains failed because the hosted request label and exact-head hosted verification are absent. No Render deployment or authenticated hosted CRUD occurred. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md). Release remains **NO-GO** and the 41/100 descriptive evidence score is unchanged.
