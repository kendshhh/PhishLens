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
