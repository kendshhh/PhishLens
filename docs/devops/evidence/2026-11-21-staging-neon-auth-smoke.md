# Staging Neon Auth smoke failure and remediation — 2026-11-21

The code reviewed here is implementation commit
`a80b95e146cd03a96ffca156ccfe5721ac871b68` on
`codex/devops-staging-closeout-20261121`. The docs/evidence refresh is committed
separately on that branch. Neither commit is merged into `main`.

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
still says `new_commit`, so the mismatch persists. A direct workstation HTTP
probe timed out; control-plane Live status does not substitute for endpoint
health verification.

## Earlier repository correction

`scripts/staging_smoke.mjs` now makes a direct anonymous GET of `/api/analyses`
first. It accepts `401` only when the response includes a Bearer challenge and
reports that it verified anonymous authentication. If the endpoint returns
`200`, it continues to use the extension's `getAnalyses()` client and validates
the seeded synthetic history record and its expected fields. Any other status
or a 401 without the challenge still fails. This keeps the legacy demo-history
contract where it applies and avoids treating a secure Neon Auth response as a
public-history outage.

The modified script was in a local worktree and had to be integrated into the
trusted workflow source before it could affect hosted runs. The latest observed
`origin/main` is `811980c2cbf70d9957146bf329627f0826a018f1`; its CI workflow checks
out trusted default-branch controller code for the legacy staging smoke, then
checks out the PR head for `scripts/verify_crud.mjs --allow-writes`. The latter
is a separate test path and currently has no authenticated session. A correct
anonymous preflight alone therefore cannot make the whole job pass.

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

1. Integrate the anonymous preflight correction into the trusted branch
   workflow actually used by hosted staging. Keep the `200` seeded-history
   branch and the strict `401 Bearer` assertion.
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
deployment, database mutation, or secret inspection was performed for this
record. The service's staging state and Neon metadata were inspected read-only.
The earlier result was **supplied hosted smoke FAIL; patched local anonymous
preflight PASS; hosted authenticated acceptance OPEN**. Keep the staging/release
gate open until the full authenticated acceptance above passes on one exact
candidate.

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
`always()`; removing the status override is defense in depth. No hosted
deployment or GitHub workflow run was started by this closeout.

Local code checks on Node.js v24.20.0:

| Check | Result | Limits |
|---|---|---|
| `npm test` | Exit 0; 315 tests passed, including six new smoke-runner cases. | Does not execute GitHub Actions or Render deployment. |
| Targeted workflow guard regression | `python -m unittest discover -s scripts/tests -p test_hosted_staging_gate.py -v`; exit 0, three checks passed. | Static regression for dependency and deploy-step gates, bounded local health probes, process monitoring and log upload; hosted execution remains outstanding. |
| `node --check` on smoke runner, smoke tests and API client | Exit 0. | Syntax only. |
| `npm run lint` | Exit 1; the `eslint` executable is not installed in this workstation environment. | No lint pass is claimed; run in the normal CI dependency environment. |
| Markdown link and whitespace review | All 31 changed Markdown files checked; no missing local links. A broader scan of 141 repository Markdown files found 14 older local references to companion artifacts absent from three benchmark summaries (`english_real_v4_checkpoint_clean`, `real_email_v3`, and `real_readiness_v10`). `git diff --check` passed with CRLF-aware whitespace handling. | The 14 benchmark-artifact references are outside this DevOps change and remain an evidence-packaging gap; external URLs and GitHub-rendered layout were not validated. |
| Live read-only smoke request to staging | Exit 1; repeated `/health` requests timed out after 10 seconds. | Workstation connectivity failure; does not establish that Render is unhealthy. |
| `python -m unittest discover -s scripts/tests -v` | Earlier attempt, before adding the three static gate regressions: exit 1; 201 discovered, 11 failures and 28 errors. | Not a valid CI reproduction: workstation Python is 3.10 rather than workflow Python 3.12; SQLAlchemy is absent; Git config environment values are incomplete; package-identity cases inspect this intentionally dirty review worktree. |
| GitHub Actions workflow lint / hosted workflow | Pinned actionlint v1.7.9 exited 0 on `.github/workflows/ci.yml`. | Static lint only; no GitHub Actions run or hosted staging deployment was started. |

The review-branch result is **focused Node regression tests PASS; live
workstation probe UNVERIFIED; hosted authenticated acceptance OPEN**. The
release remains **NO-GO** until the current CI, exact-SHA hosted run, and
authenticated persistence/isolation/cleanup journey pass on one candidate.
