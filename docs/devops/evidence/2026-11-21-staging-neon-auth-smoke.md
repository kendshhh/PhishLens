# Staging Neon Auth smoke failure and remediation — 2026-11-21

## Summary

**The supplied hosted smoke did not pass.** The failure is consistent with the
current staging security contract: anonymous saved-report history requires a
Bearer session. The legacy smoke interprets that expected `401` as a generic
history failure. A local change now validates this anonymous auth boundary, and
a read-only run of that modified script passed against staging on November 21.
The change is not on `main`, does not exercise authenticated saved-report CRUD,
and does not close the hosted staging gate.

## Failure record

The user-provided Actions output (no run URL/ID or tested SHA supplied) was:

```text
STAGING_BASE_URL=https://phishlens-staging.onrender.com
STAGING_MIGRATION_REVISION=0004_neon_auth_subject
Error: Failed to load history
  at getAnalyses (.../extension/js/api.js:111:15)
  at .../scripts/staging_smoke.mjs:27:15
```

The deployed extension API throws that error when the history request is
unauthorized. The log did not include the full HTTP response, GitHub run link,
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

## Repository correction in the workspace

`scripts/staging_smoke.mjs` now makes a direct anonymous GET of `/api/analyses`
first. It accepts `401` only when the response includes a Bearer challenge and
reports that it verified anonymous authentication. If the endpoint returns
`200`, it continues to use the extension's `getAnalyses()` client and validates
the seeded synthetic history record and its expected fields. Any other status
or a 401 without the challenge still fails. This keeps the legacy demo-history
contract where it applies and avoids treating a secure Neon Auth response as a
public-history outage.

The modified script is in the local worktree and must be integrated into the
trusted workflow source before it affects hosted runs. The latest observed
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
The current result is **supplied hosted smoke FAIL; patched local anonymous
preflight PASS; hosted authenticated acceptance OPEN**. Keep the staging/release
gate open until the full authenticated acceptance above passes on one exact
candidate.
