# Staging Neon Auth smoke failure and remediation — 2026-11-21

The code reviewed here is implementation commit
`a80b95e146cd03a96ffca156ccfe5721ac871b68` on
`codex/devops-staging-closeout-20261121`. The docs/evidence refresh is committed
separately on that branch. These PR #268 changes are not merged into `main`.
The separate Bearer-aware history correction from PR #263 is now in current
`main` at `06f89d7a0b5b9dec316dfa11f2846767a32086c5`.

## Summary

**The supplied hosted smoke did not pass.** Its log contains no response status
or body, so its underlying cause cannot be confirmed. A separate dated
read-only staging probe returned `401 Bearer`, making the expected anonymous
Auth boundary a plausible explanation. The earlier local patch recognized
that boundary, but it did not exercise authenticated saved-report CRUD or close
the hosted staging gate.

## Failure record

The user-provided Actions output (no run URL/ID or tested SHA supplied) was:

```text
STAGING_BASE_URL=https://phishlens-staging.onrender.com
STAGING_MIGRATION_REVISION=0004_neon_auth_subject
Error: Failed to load history
  at getAnalyses (.../extension/js/api.js:111:15)
  at .../scripts/staging_smoke.mjs:27:15
```

The extension API can throw that generic error when history returns an
unauthorized response, but the supplied log does not establish that this was
the response in that run. It did not include the full HTTP response, GitHub run link,
pull request, or checked-out commit, so those identifiers are intentionally
left unknown rather than inferred.

## Current read-only observations

The PhishLens Render workspace and Neon project were explicitly selected. The
following observations were made read-only on November 21:

| Target | Observation | Boundary |
|---|---|---|
| Staging Render | Service `srv-db92irlg1s2s739404i0`; latest observed live deploy `dep-dc0im3h7lnhs738pncng`; SHA `ba0b6c5475eb6a8f99c509c40384020d292e17e6`. | Render control-plane state only. The user log did not identify its source SHA. |
| Staging HTTP | `/version`, `/health`, `/ready`, `/model-info` each returned 200; version identified staging SHA above; readiness reported connected database; model mode was TF-IDF with SHA-256 `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`. | GETs only; no inference, Auth sign-in or database write. |
| Anonymous report history | `GET /api/analyses` returned HTTP 401 with `WWW-Authenticate: Bearer`. | This is the expected protected-resource boundary, not proof that authenticated history works. |
| Neon staging branch | Project `patient-bird-25428852`; branch `pr-58-staging` / `br-delicate-paper-b381z98i`; DB `phishlens_dev`; Auth DB `neondb`; migration head `0004_neon_auth_subject`. | Branch/Auth/SQL inspection was read-only. It does not prove Render's secret URL maps to this branch and role. |
| Auth policy | Trusted origin is the staging Render URL; email/password sign-up enabled; email verification required. | Config inspection only; no user was created and no sign-in flow was run. |
| Staging grants | Under role `phishlens_staging_app`, `public` CREATE is false; `users` SELECT/INSERT true, UPDATE/DELETE false; `analyzed_emails` SELECT/INSERT/UPDATE/DELETE true. | Read-only SQL against the named Neon branch/role. Render's actual runtime role mapping is not verified. |

Render control-plane service and deployment metadata were rechecked read-only
at 2026-11-21 07:31 UTC in the user-selected PhishLens workspace. Staging remains
Live on deploy `dep-dc0im3h7lnhs738pncng` / SHA
`ba0b6c5475eb6a8f99c509c40384020d292e17e6`; production remains Live on
`dep-dc07rs67bikc73fjgjq0` / SHA
`811980c2cbf70d9957146bf329627f0826a018f1`. Both services report branch
`main`, auto-deploy disabled, and trigger `off`. The production deploy record
still says `new_commit`, so the mismatch persists. An earlier direct workstation
probe timed out. At 08:15 UTC, the review-branch smoke script later completed
read-only GETs to `/health`, `/ready` and `/api/analyses`, passing health,
readiness and the expected anonymous `401 Bearer` boundary. It does not query
`/version`, confirm the deployed PR SHA or test authenticated CRUD.

## GitHub dependency-alert reconciliation

At 2026-11-21 07:46 UTC, a read-only GitHub Dependabot API query returned 15
open alerts: 12 high alerts for `pyasn1` (IDs 30-37 and 39-42; four GHSA
records across the root, backend runtime, and backend development requirements)
and three medium alerts for `opentelemetry-api` (IDs 43-45). The advisories
name `pyasn1` versions through 0.6.4 and `opentelemetry-api` versions through
1.45.1 as vulnerable; their first patched versions are 0.6.5 and 1.45.2.

The observed `origin/main` snapshot at `811980c2cbf70d9957146bf329627f0826a018f1`
already pinned those first patched versions in the three requirements manifests.
Sample alert records 42 and 45 were last updated on their creation dates
(October 31 and November 14 respectively). The open API state conflicts with
the current pins; it does not prove that the current resolved environment is
vulnerable, and it is not proof that GitHub has closed or rescanned the alerts.
Reconcile the default-branch dependency graph and retain a fresh dependency
review result before marking this security gate complete. The alert list is
available at [GitHub Dependabot alerts](https://github.com/kendshhh/PhishLens/security/dependabot).

## Earlier repository correction

`scripts/staging_smoke.mjs` now makes a direct anonymous GET of `/api/analyses`
first. It accepts `401` only when the response includes a Bearer challenge and
reports that it verified anonymous authentication. If the endpoint returns
`200`, it continues to use the extension's `getAnalyses()` client and validates
the seeded synthetic history record and its expected fields. Any other status
or a 401 without the challenge still fails. This keeps the legacy demo-history
contract where it applies and avoids treating a secure Neon Auth response as a
public-history outage.

At that earlier snapshot the modified script was in a local worktree and had to
be integrated into the trusted workflow source before it could affect hosted
runs. Main subsequently merged PR #263; its current commit
`06f89d7a0b5b9dec316dfa11f2846767a32086c5` uses the Bearer-aware helper for the
legacy staging smoke. The workflow still checks out trusted default-branch
controller code for that smoke, then checks out the PR head for
`scripts/verify_crud.mjs --allow-writes`. The CRUD runner has no authenticated
session, so the anonymous preflight alone cannot make the whole hosted job pass.

The modified script was run locally on November 21 with
`STAGING_BASE_URL=https://phishlens-staging.onrender.com` and
`STAGING_MIGRATION_REVISION=0004_neon_auth_subject`:

```text
node scripts/staging_smoke.mjs
exit code: 0
Staging passed: health, database readiness, and anonymous saved-report authentication.
```

The tested file SHA-256 was
`1bee26a9cdaa9073345762e7784babf0c551ec8f463db507685d89b2c207ad9f`. This is
manual local verification of the dirty-worktree script against the live staging
URL. The script performed health/readiness and anonymous-history GETs only; it
does not check `/version` or query the migration table. The migration revision
was verified separately by read-only Neon SQL. The local run did not test hosted
CI, authentication, seeded history on this route, CRUD, write/cleanup behavior,
or the PR's exact deployed revision.

## Required remediation and acceptance

1. Mainline commit `06f89d7` now integrates the anonymous preflight correction
   into the trusted staging workflow. Keep its `200` seeded-history branch and
   strict `401 Bearer` assertion; verify the review branch's added diagnostics,
   bounded retry and fail-closed conditions in current CI before merge.
2. Update the hosted CRUD runner to sign in through the supported Neon Auth
   flow with a dedicated synthetic staging identity and least-privilege test
   credential. Send the real Bearer session on every saved-report request.
   Do not add an auth bypass, weaken endpoint policy, or put session tokens in
   logs/artifacts.
3. Run an exact-head staging job against an isolated approved staging target.
   Capture PR head SHA, merge/deployed SHA, migration revision, package hash,
   masked branch/role identity, run link, and redacted results.
4. Prove sign-in, create, list, read, update, delete, reload persistence,
   wrong-user isolation, unauthorized behavior, safe failure handling, and
   cleanup. Verify no test record remains. Keep the data in staging only.
5. Re-read `/version`, `/ready`, `/model-info` and anonymous `/api/analyses`
   after the run. Demonstrate that the tested backend/package pair still has
   the expected exact identities before uploading evidence.
6. Re-run the relevant CI job on the reviewed candidate. A local smoke run, a
   skipped hosted job, an unrelated successful check or an anonymous 401 test
   does not pass authenticated CRUD acceptance.

## Evidence limits and disposition

No hosted rerun, Auth signup/login, app-level write, inference, production call,
deployment, database mutation, or secret inspection was performed for the
original failure analysis. The service's staging state and Neon metadata were
inspected read-only. The original result was **supplied hosted smoke FAIL;
patched local anonymous preflight PASS; hosted authenticated acceptance OPEN**.
Keep the staging/release gate open until the full authenticated acceptance
above passes on one exact candidate.

## Review-branch correction and verification — 2026-11-21

The code and documentation closeout is prepared on
`codex/devops-staging-closeout-20261121`, based on
`3c858f7df51666e0545dea1a6dd5997574c16d43`. The original dirty checkout was
left untouched. The branch:

- accepts anonymous history only when the status is `401` and
  `WWW-Authenticate` starts with `Bearer`; retains the seeded-history
  assertions when the extension client receives `200`;
- retries transient HTTP/network failures only, with a 120-second overall
  deadline, 30-attempt ceiling and three-second delay; permanent authentication,
  HTTP and payload-contract errors fail without retry;
- includes final stage, endpoint, status and sanitized error in
  `GITHUB_STEP_SUMMARY`;
- monitors local server exit during readiness and uploads its log artifact even
  if startup or smoke fails;
- removes hosted job-level `always()`, retains explicit success predicates
  for staging, hosted preflight and backend, and applies these predicates again
  to the Render deployment step.

The linked workflow already had explicit dependency-success predicates alongside
`always()`; removing the status override is defense in depth. Code/test SHA
`d27eaa07a28173c485d19f44524a88e71515fc10` passed GitHub CI run
[44883590782](https://github.com/kendshhh/PhishLens/actions/runs/44883590782),
including local staging integration and deployment guard tests. In the 08:21
UTC pre-sync snapshot, PR #268's then-current documentation-only head was
`a2fb3f79e7857eeef20a2a2cf70f603906d86f31`; it passed CI run
[44884534992](https://github.com/kendshhh/PhishLens/actions/runs/44884534992),
workflow lint [44884534973](https://github.com/kendshhh/PhishLens/actions/runs/44884534973),
dependency security [44884535027](https://github.com/kendshhh/PhishLens/actions/runs/44884535027),
CodeQL [44884532294](https://github.com/kendshhh/PhishLens/actions/runs/44884532294),
and deterministic AI evaluation
[44884534978](https://github.com/kendshhh/PhishLens/actions/runs/44884534978).
Hosted staging and its preflight were skipped. The latest separate
[Secretary staging check](https://github.com/kendshhh/PhishLens/actions/runs/44884776725)
failed because the PR lacks `needs-hosted-staging` and exact-head hosted
verification. No Render deployment was started.

Earlier local checks on Node.js v24.20.0 (pre-mainline-sync snapshot):

| Check | Result | Limits |
|---|---|---|
| `npm test` | Exit 0; 315 tests passed, including six new smoke-runner cases. | Does not execute GitHub Actions or Render deployment. |
| Targeted workflow guard regression | `python -m unittest discover -s scripts/tests -p test_hosted_staging_gate.py -v`; exit 0, three checks passed. | Static regression for dependency and deploy-step gates, bounded local health probes, process monitoring and log upload; hosted execution remains outstanding. |
| `node --check` on smoke runner, smoke tests and API client | Exit 0. | Syntax only. |
| `npm run lint` | The local command could not find ESLint. GitHub Extension checks on PR head `d27eaa0` passed their configured JavaScript lint. | Local tool absence is not a CI lint failure; hosted staging remains skipped. |
| Markdown link and whitespace review | All 31 changed Markdown files checked; no missing local links. A broader scan of 141 repository Markdown files found 14 older local references to companion artifacts absent from three benchmark summaries (`english_real_v4_checkpoint_clean`, `real_email_v3`, and `real_readiness_v10`). `git diff --check` passed with CRLF-aware whitespace handling. | The 14 benchmark-artifact references are outside this DevOps change and remain an evidence-packaging gap; external URLs and GitHub-rendered layout were not validated. |
| Live read-only smoke request to staging | Exit 1; repeated `/health` requests timed out after 10 seconds. | Workstation connectivity failure; does not establish that Render is unhealthy. |
| `python -m unittest discover -s scripts/tests -v` | The earlier workstation attempt was incomplete under Python 3.10. On PR head `d27eaa0`, GitHub Staging integration ran all 226 deployment-guard tests successfully under Python 3.12. | The workstation failure is not a current CI failure; Hosted staging was skipped, so no hosted deployment is claimed. |
| GitHub Actions workflow lint / hosted workflow | Pinned actionlint v1.7.9 passed locally. Workflow lint [44884534973](https://github.com/kendshhh/PhishLens/actions/runs/44884534973) and CI [44884534992](https://github.com/kendshhh/PhishLens/actions/runs/44884534992) passed on pre-sync docs-only PR commit `a2fb3f7`; application/test SHA `d27eaa0` passed CI [44883590782](https://github.com/kendshhh/PhishLens/actions/runs/44883590782). | In that pre-sync snapshot, hosted staging and preflight were skipped and Secretary staging run [44884776725](https://github.com/kendshhh/PhishLens/actions/runs/44884776725) required the `needs-hosted-staging` label and exact-head hosted verification. |
| Direct live staging smoke | At 08:15 UTC, `node scripts/staging_smoke.mjs` passed health, database readiness and anonymous history authentication (`HTTP 401 Bearer`) against the configured staging URL. | GET-only workstation run; it does not verify the deployed PR SHA, migration table, Auth session, CRUD, or cleanup. |

The review-branch result at that snapshot was **focused Node regression tests
PASS; live workstation probe UNVERIFIED; hosted authenticated acceptance
OPEN**. The current follow-up evidence is recorded below.

## Mainline synchronization and repeat smoke — 2026-11-21

Current `origin/main` was fetched at
`06f89d7a0b5b9dec316dfa11f2846767a32086c5` (PR #263), which adds the tested
`scripts/staging_history.mjs` helper and accepts anonymous history only for a
Bearer challenge. PR #268 was synchronized with that main in merge commit
`14874d339bbb4042172df954f97596080aa303ee`; latest code/test commit
`83a0df1af1d64048b3b5fa3158f6509e83d71555` uses that helper while adding
bounded transient-only retries, endpoint/status/error summaries, and the
seeded-history contract. Permanent HTTP statuses fail without retry, even when
the response text mentions a timeout or network failure.
The CI workflow also monitors local API process exit, preserves its server log,
and repeats successful dependency gates at the hosted deployment step.

On 2026-11-21 at approximately 08:35 UTC, the synchronized worktree passed
`npm test` (321 tests) and `node scripts/staging_smoke.mjs` against
`https://phishlens-staging.onrender.com`. The smoke returned exit code 0 after
health, database readiness, and the expected anonymous `401 Bearer` result. It
performed GETs only. It does not prove the deployed PR revision, migration
table, authenticated CRUD, persistence, isolation, or cleanup. The live staging
service still reports the older deployed SHA in the environment map.

The latest code/test commit had not yet run GitHub CI when this snapshot was
written. Prior code CI [44883590782](https://github.com/kendshhh/PhishLens/actions/runs/44883590782)
and documentation CI [44884534992](https://github.com/kendshhh/PhishLens/actions/runs/44884534992)
passed on pre-sync commits. The prior hosted-staging check
[44884776725](https://github.com/kendshhh/PhishLens/actions/runs/44884776725)
required `needs-hosted-staging` and exact-head verification; no Render deploy
was started. Keep release **NO-GO** until synchronized-candidate CI, protected
hosted verification, and authenticated persistence/isolation/cleanup all pass.

## Exact-head CI refresh — 2026-11-21

After the preceding snapshot, PR #268 head
`d447b3c537bc24ec9b7c7ed0ba6f34b7316826d2` completed its GitHub checks. The
code/test content is commit `83a0df1af1d64048b3b5fa3158f6509e83d71555`; the
tested PR head adds the synchronized documentation. [CI run
44886742192](https://github.com/kendshhh/PhishLens/actions/runs/44886742192)
passed migration source preflight, backend checks, extension checks, and
Staging integration. Staging integration passed the hosted-history auth smoke,
local server/API integration, server-log preservation, and deployment guard
tests. [Workflow lint](https://github.com/kendshhh/PhishLens/actions/runs/44886742281),
[dependency security](https://github.com/kendshhh/PhishLens/actions/runs/44886742188),
[deterministic AI evaluation](https://github.com/kendshhh/PhishLens/actions/runs/44886742189),
and [CodeQL](https://github.com/kendshhh/PhishLens/actions/runs/44886738976)
also passed for this PR head. The automatic `label` workflow and Secretary
report workflow passed; the generic `label` status did not apply the required
`needs-hosted-staging` label.

The hosted staging preflight and hosted deployment jobs were **skipped** in
CI run 44886742192. Separately, GitHub reports the required `Secretary staging`
PR check as **failed**, with the reason that `needs-hosted-staging` and an
exact-head hosted staging verification are required ([check run
44886970872](https://github.com/kendshhh/PhishLens/actions/runs/44886970872)).
The controller's assessment job succeeded, but its preview job was skipped; the
status check therefore does not represent a hosted deployment or CRUD run. No
Render deployment, staging write, or authenticated hosted CRUD acceptance was
performed. PR #268 remains blocked and needs a fresh reviewer decision.

This result supersedes the pending-CI statement in the immediately preceding
snapshot. It does not establish that the original user-supplied failing run had
the same cause, that Render is running the PR revision, or that authenticated
history/CRUD, persistence, isolation, cleanup, effective branch protection, or
production acceptance has passed. Keep the release **NO-GO**.

## Documentation-head verification — 2026-11-21

The documentation refresh was pushed as commit
`bc9a6b0b742d1b75d9bdcbb6004f07d69e17ac47`. CI run
[44887660166](https://github.com/kendshhh/PhishLens/actions/runs/44887660166)
completed successfully on that exact PR head. Backend, extension, migration
source preflight and local staging integration passed; the local staging job
passed its history-auth smoke and server/deployment-guard tests. Workflow lint
[44887660108](https://github.com/kendshhh/PhishLens/actions/runs/44887660108),
dependency security [44887660090](https://github.com/kendshhh/PhishLens/actions/runs/44887660090),
deterministic evaluation [44887660089](https://github.com/kendshhh/PhishLens/actions/runs/44887660089),
and CodeQL [136796452132](https://github.com/kendshhh/PhishLens/runs/136796452132)
passed. The Secretary report and generic label checks passed as well.

Hosted preflight and hosted staging were skipped again. The PR's
`Secretary staging` context remains failed because the protected-run label and
exact-head hosted verification are missing ([check run
44887876370](https://github.com/kendshhh/PhishLens/actions/runs/44887876370)).
Its assessment job succeeded while the preview job was skipped. This confirms
the documentation-only push did not resolve hosted staging or authenticated
CRUD; no Render deploy or staging write occurred. The checks cover the code/test
commit `83a0df1af1d64048b3b5fa3158f6509e83d71555` unchanged in this docs-only
commit. Keep **NO-GO** and use the passing automated checks only as evidence for
their stated local/CI scope.

The PR branch later advanced to docs commit
`631b0ef21849e8abe877bb16b4676047f2aca86a`. On that exact head, CI
[44888140094](https://github.com/kendshhh/PhishLens/actions/runs/44888140094),
workflow lint [44888140104](https://github.com/kendshhh/PhishLens/actions/runs/44888140104),
dependency security [44888140135](https://github.com/kendshhh/PhishLens/actions/runs/44888140135),
and deterministic evaluation [44888140114](https://github.com/kendshhh/PhishLens/actions/runs/44888140114)
passed. The `Secretary staging` check failed because the protected hosted run
and exact-head verification were not requested ([run
44888369939](https://github.com/kendshhh/PhishLens/actions/runs/44888369939));
no hosted deployment or authenticated CRUD ran. The PR #265 documentation
reconciliation postdates those checks, so fresh checks are required on the
resulting candidate.

## PR #265 reconciliation check snapshot — 2026-11-21 09:22 UTC

GitHub reported remote PR #268 head
`7dbebfd060298a80e99a38a52663901e776935cb`, whose merge history includes PR
#265's shared readiness-document baseline. This exact SHA is a documentation
reconciliation head; the underlying code/test commit remains
`83a0df1af1d64048b3b5fa3158f6509e83d71555`.

- Backend checks, Extension checks and Migration source preflight passed in
  [run 44889070392](https://github.com/kendshhh/PhishLens/actions/runs/44889070392).
  Staging integration was `in_progress` when the check-runs API was read at
  09:22 UTC.
- [Workflow lint 44889070441](https://github.com/kendshhh/PhishLens/actions/runs/44889070441),
  [dependency security 44889070418](https://github.com/kendshhh/PhishLens/actions/runs/44889070418),
  and [deterministic evaluation 44889070455](https://github.com/kendshhh/PhishLens/actions/runs/44889070455)
  had succeeded. The separate `Dependency graph review (GitHub Advanced
  Security)` check in run 44889070418 had failed. CodeQL run
  [44889065082](https://github.com/kendshhh/PhishLens/actions/runs/44889065082)
  was `in_progress`.
- Secretary report [44889108682](https://github.com/kendshhh/PhishLens/actions/runs/44889108682)
  said **WAITING FOR CHECKS**. Hosted staging was not requested. No Render
  deployment, staging write or authenticated CRUD occurred.
- The present evidence reconciliation creates a newer PR head. Results above
  are not transferable to that SHA; read the new check run and report any failed,
  skipped, missing or pending gate explicitly.

## Settled check state — 2026-11-21 09:31 UTC

The remote PR still pointed to `7dbebfd060298a80e99a38a52663901e776935cb`.
Staging integration completed successfully in run 44889070392. Hosted staging
and preflight remained skipped. The three CodeQL language jobs in run 44889065082
completed with failure; GitHub annotations state that Actions installation API
rate limits prevented analysis. They contain no reported CodeQL findings. The
separate dependency graph review failed because GitHub says the repository's
Dependency graph is disabled (see [job log
136800698597](https://github.com/kendshhh/PhishLens/actions/runs/44889070418/job/136800698597)).
No hosted deployment or authenticated CRUD was performed. This later status
observation supersedes the 09:22 in-progress states above, but applies only to
the exact `7dbebfd` head. The current documentation reconciliation needs its
own checks.

The dependency review failure is an administrative prerequisite: have an
authorized repository administrator enable Dependency graph in GitHub Security
settings and then rerun dependency review. The CodeQL language job annotations
for [run 44889065082](https://github.com/kendshhh/PhishLens/actions/runs/44889065082)
attribute their failures to Actions installation API rate limits; rerun CodeQL
on a fresh exact head after the limit clears. The run does not establish a
CodeQL finding, but its failed status remains a failed gate until a successful
analysis is recorded.

## Current PR-head check snapshot — 2026-11-21 09:42 UTC

PR #265 merged into `main` at `95975cd47dceeac74ea36054610956f0a1db1fa9`.
That merged main revision passed CI [44889931821](https://github.com/kendshhh/PhishLens/actions/runs/44889931821)
and CodeQL [44889931096](https://github.com/kendshhh/PhishLens/actions/runs/44889931096).
The review branch now reports PR #268 head
`def5e9b3d925e94a9aa664a24f90c73b960c7f99`, still based on PR #265's merged
head `ca29235b42ac839f4cd7c4b417ef83d4c701c6a8`.

- [CI 44890690426](https://github.com/kendshhh/PhishLens/actions/runs/44890690426)
  passed Backend, Extension, migration source preflight and Staging integration.
  Hosted staging and hosted preflight were skipped; the job did not deploy to
  Render or run authenticated CRUD.
- [Workflow lint 44890690321](https://github.com/kendshhh/PhishLens/actions/runs/44890690321),
  [Dependency security and Dependency graph review 44890690295](https://github.com/kendshhh/PhishLens/actions/runs/44890690295),
  and [deterministic evaluation 44890690376](https://github.com/kendshhh/PhishLens/actions/runs/44890690376)
  passed. The repository's Dependency graph and vulnerability alerts were
  enabled after the 7dbebfd failure; 15 existing Dependabot alerts (12 high,
  3 moderate) remain open.
- No CodeQL check appeared on the `def5e9b` PR head. The retry commit did not
  supply a current PR CodeQL result. The prior CodeQL run on `7dbebfd` failed
  after GitHub Actions installation API rate limits; main's CodeQL pass does not
  substitute for the PR candidate's result.
- PR #268 remains open and still targets `codex/readiness-update-20261121`, now
  merged into main. Retarget the PR to `main` before merging. No CodeQL pass,
  authenticated staging CRUD, protected hosted deployment or exact deployed
  candidate has been established for this PR.

## Exact-head checks and hosted-job state — 2026-11-21 10:14 UTC

GitHub reported PR #268 head
`2e26327254c71b6cb7d655181cffb21e8dd1ee9b`, an empty commit requesting an
exact-head verification run. This SHA is the latest remote snapshot observed
before the documentation refresh; a later docs commit will need its own checks.

- Backend, Extension, migration source preflight, Staging integration, and
  Hosted staging preflight passed in [CI run 44891131201](https://github.com/kendshhh/PhishLens/actions/runs/44891131201).
  Hosted staging job [136807616481](https://github.com/kendshhh/PhishLens/actions/runs/44891131201/job/136807616481)
  completed with conclusion `success`, but the final freshness check reported `current=false` and classified the run as superseded after the request label
  was removed at 09:54 UTC. Render deployment, hosted API smoke, authenticated CRUD,
  evidence finalization and artifact steps were skipped; the job summary classifies
  this run as blocked, not hosted acceptance. No Render deployment or authenticated CRUD was observed.
- [Workflow lint 44891131261](https://github.com/kendshhh/PhishLens/actions/runs/44891131261),
  [Dependency security and Dependency graph review 44891131162](https://github.com/kendshhh/PhishLens/actions/runs/44891131162),
  and [deterministic evaluation 44891131190](https://github.com/kendshhh/PhishLens/actions/runs/44891131190)
  passed. Required `Secretary staging` failed because the request label and exact-head hosted verification were absent ([run 44892082807](https://github.com/kendshhh/PhishLens/actions/runs/44892082807)). No current PR CodeQL result appeared. The earlier `7dbebfd`
  CodeQL failure remains attributed by its annotations to Actions installation
  API rate limits, with no finding reported.
- The merged base PR #265 is now on `main` at `95975cd`, but PR #268 still has
  base `codex/readiness-update-20261121` at `ca29235`. Retarget it to `main`
  before merge. Fifteen Dependabot alerts (12 high, 3 moderate) remain open.

These check results are not a hosted deployment or release acceptance. The
branch remains unmerged, the authenticated staging CRUD path remains unresolved,
and all pending and skipped gates must remain visible in the closeout record.

## Latest documentation-head CI snapshot — 2026-11-21 11:08 UTC

The DevOps evidence reconciliation was pushed as PR #268 head
`a151585ff92d55f21e0364e9838287a9cf04a68d`. In [CI run 44897548076](https://github.com/kendshhh/PhishLens/actions/runs/44897548076),
Backend and migration source preflight passed, but `Extension checks` failed
in the packaged Chromium acceptance step. The assertion at
`scripts/browser_acceptance.mjs:700` reported “Saved reports view: Tab must
reach the popup controls.” This is a real failed required check on this SHA;
the earlier pass on `2e26327` does not override it. Workflow lint
[44897548088](https://github.com/kendshhh/PhishLens/actions/runs/44897548088),
dependency security and graph review
[44897548010](https://github.com/kendshhh/PhishLens/actions/runs/44897548010),
deterministic evaluation
[44897548070](https://github.com/kendshhh/PhishLens/actions/runs/44897548070),
and the Secretary report [44897544530](https://github.com/kendshhh/PhishLens/actions/runs/44897544530)
passed.

The same keyboard-focus assertion also failed on main SHA `06f89d7` in
[CI 44885148600](https://github.com/kendshhh/PhishLens/actions/runs/44885148600),
while the later merged-main run for `95975cd` passed in
[CI 44889931821](https://github.com/kendshhh/PhishLens/actions/runs/44889931821).
This shows a repeat failure and an intervening pass; it does not establish
whether the cause is intermittent browser behavior or a UI/test defect.

Staging integration, Hosted staging preflight and Hosted staging were skipped
after the Extension check failed. The separate required `Secretary staging`
status failed in [run 44897660167](https://github.com/kendshhh/PhishLens/actions/runs/44897660167),
whose assessment says application/runtime changes need the
`needs-hosted-staging` label and exact-head hosted verification. The label was
removed to preserve the read-only staging boundary. No Render deployment,
authenticated CRUD, or current PR CodeQL result was observed. PR #268 still
targets the merged PR #265 branch. Investigate the assertion, retarget to main,
and obtain fresh exact-head CI before requesting authorized hosted acceptance.

## Previous completed workflow snapshot — 2026-11-21 11:21 UTC

The documentation follow-up was pushed as head
`dffdc4c29338142f458350b51c8ce69e0f36e988`. Backend, Extension, migration
source preflight and Staging integration passed in [CI 44898467208](https://github.com/kendshhh/PhishLens/actions/runs/44898467208).
Workflow lint [44898467185](https://github.com/kendshhh/PhishLens/actions/runs/44898467185),
dependency security and graph review [44898467124](https://github.com/kendshhh/PhishLens/actions/runs/44898467124),
deterministic evaluation [44898467190](https://github.com/kendshhh/PhishLens/actions/runs/44898467190),
and the Secretary report [44898465856](https://github.com/kendshhh/PhishLens/actions/runs/44898465856)
passed. The keyboard focus assertion that failed on `a151585` did not recur
here, but its root cause remains undiagnosed; an older failure on `06f89d7`
and a passing merged-main run also exist.

Hosted staging preflight and Hosted staging were skipped. Required
`Secretary staging` failed because the request label and exact-head hosted
verification were absent ([run 44898698685](https://github.com/kendshhh/PhishLens/actions/runs/44898698685)).
No current PR CodeQL result, Render deployment or authenticated CRUD was
observed. The docs-only sync after this snapshot needs its own checks. PR #268
still targets the merged PR #265 branch and must be retargeted before merge.

## Latest completed workflow snapshot — 2026-11-21 11:31 UTC

Docs-only head `f79098cc075784563d2022cbca87d7abe8f0a635` passed Backend,
Extension, migration preflight and Staging integration in [CI
44899191736](https://github.com/kendshhh/PhishLens/actions/runs/44899191736).
Workflow lint [44899191771](https://github.com/kendshhh/PhishLens/actions/runs/44899191771),
dependency security/graph [44899191710](https://github.com/kendshhh/PhishLens/actions/runs/44899191710),
deterministic evaluation [44899191787](https://github.com/kendshhh/PhishLens/actions/runs/44899191787),
and the Secretary report [44899190365](https://github.com/kendshhh/PhishLens/actions/runs/44899190365)
passed. The keyboard-focus assertion that failed on `a151585` also passed on
this no-code-change follow-up; its root cause remains undiagnosed.

Hosted staging preflight and Hosted staging were skipped. Required
`Secretary staging` failed because the request label and exact-head hosted
verification were absent ([run 44899423134](https://github.com/kendshhh/PhishLens/actions/runs/44899423134)).
No current PR CodeQL result, Render deployment or authenticated CRUD was
observed. The docs-only sync following this snapshot needs its own checks. PR
#268 remains based on the merged PR #265 branch and must be retargeted before
merge.

## Follow-up exact-head PR CI — 2026-11-21 11:42 UTC

PR #268 head `e9451cc20928fefa7c0a6ded4803cebbad24ef42` completed its CI run
[44900115517](https://github.com/kendshhh/PhishLens/actions/runs/44900115517)
at 11:42 UTC. Backend, Extension, migration source preflight and Staging
integration passed. Workflow lint [44900115510](https://github.com/kendshhh/PhishLens/actions/runs/44900115510),
dependency security and graph review [44900115593](https://github.com/kendshhh/PhishLens/actions/runs/44900115593),
deterministic evaluation [44900115440](https://github.com/kendshhh/PhishLens/actions/runs/44900115440),
and the Secretary report [44900115513](https://github.com/kendshhh/PhishLens/actions/runs/44900115513)
also passed. The Issue 90 read-only package job, Hosted staging preflight and
Hosted staging were skipped. This is not hosted-service acceptance.

GitHub's commit-status API returned `failure` for the required `Secretary
staging` context attached to this PR head. Its status description says
application/runtime changes require the `needs-hosted-staging` label and an
exact-head hosted staging verification; the linked [Secretary preview workflow
run 44900357378](https://github.com/kendshhh/PhishLens/actions/runs/44900357378)
records that assessment. The request label remains absent. No Render deployment,
authenticated hosted CRUD, or current PR CodeQL result was observed. The check
run and status were inspected read-only; no staging write was requested or
performed.

PR #268 remains open and still targets `codex/readiness-update-20261121`, which
is already merged into `main` at `95975cd`. Retarget to `main` and obtain fresh
checks before merge. The 41/100 DevOps evidence-progress estimate is descriptive,
not a completion percentage; the release remains **NO-GO**. Do not claim 100% or
hosted acceptance from these results.

## Post-retarget exact-head snapshot — 2026-11-21 11:57 UTC

After reviewer feedback, PR #268 was retargeted from the already-merged
`codex/readiness-update-20261121` branch to `main`. The review branch merged the
current main history; the seven documentation conflicts retained the branch's
newer reconciled records. GitHub now reports PR #268 open, based on `main`, and
mergeable at `77c0ed00e607c5580cedffadd031fe40ad71771b`. The review decision is
still `CHANGES_REQUESTED`; collaborator re-review remains outstanding.

The exact-head CI run [44901297774](https://github.com/kendshhh/PhishLens/actions/runs/44901297774)
completed successfully at 11:56 UTC. Backend, Extension, migration source
preflight and Staging integration passed. Workflow lint
[44901297784](https://github.com/kendshhh/PhishLens/actions/runs/44901297784),
dependency security and graph review
[44901297782](https://github.com/kendshhh/PhishLens/actions/runs/44901297782),
deterministic evaluation
[44901297726](https://github.com/kendshhh/PhishLens/actions/runs/44901297726),
DevOps Secretary report
[44901295234](https://github.com/kendshhh/PhishLens/actions/runs/44901295234),
and CodeQL [136837678645](https://github.com/kendshhh/PhishLens/runs/136837678645)
passed. Hosted staging preflight, Hosted staging and the Issue 90 read-only
package were skipped.

GitHub's commit-status API reports failure for the required `Secretary staging`
context attached to this PR head. Its description requires the
`needs-hosted-staging` label and exact-head hosted verification; the linked
[Secretary preview assessment 44901487623](https://github.com/kendshhh/PhishLens/actions/runs/44901487623)
records that gate. No Render deployment or authenticated hosted CRUD occurred.
The label remains absent to preserve the read-only staging boundary. These
results do not authorize release acceptance. The scorecard remains 41/100
descriptive evidence progress and **NO-GO**; no 100% claim is supported.

## Exact-head CI after retarget — 2026-11-21 12:02 UTC

PR #268 head `1fa2e7827cfe84de425afcc7885743bd55b2a382`, based on `main`,
completed exact-head [CI run 44901642617](https://github.com/kendshhh/PhishLens/actions/runs/44901642617)
at 12:02 UTC. Backend, Extension, Staging integration and migration source
preflight passed. Workflow lint [44901642674](https://github.com/kendshhh/PhishLens/actions/runs/44901642674),
dependency security and graph review
[44901642615](https://github.com/kendshhh/PhishLens/actions/runs/44901642615),
deterministic evaluation
[44901642635](https://github.com/kendshhh/PhishLens/actions/runs/44901642635),
DevOps Secretary report
[44901640759](https://github.com/kendshhh/PhishLens/actions/runs/44901640759),
and CodeQL (Actions, JavaScript/TypeScript and Python; workflow
[44901639249](https://github.com/kendshhh/PhishLens/actions/runs/44901639249))
passed. Hosted staging preflight, Hosted staging and the Issue 90 read-only
package were skipped.

The commit status remains failed for required `Secretary staging`, because the
`needs-hosted-staging` label and exact-head hosted verification are absent. The
assessment is [Secretary preview run 44901931269](https://github.com/kendshhh/PhishLens/actions/runs/44901931269).
No Render deployment or authenticated hosted CRUD occurred. PR #268 is open,
based on `main`, and GitHub marks it mergeable; its review decision remains
`CHANGES_REQUESTED` while collaborator re-review is outstanding. Release status
is **NO-GO** and the descriptive DevOps evidence-progress value remains 41/100.

This is the latest completed workflow snapshot at the time of this record. The
following documentation-only commit must pass its own exact-head checks before
merge; no runtime or workflow code changed in this snapshot update.
