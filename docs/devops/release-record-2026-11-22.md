# Staging reliability and release checklist — 2026-11-22

## Decision and current state

The authorized staging owner selected Neon project `hidden-shadow-38533062`
(`phishlens-staging`), branch `br-broad-feather-b3261w7l` (`staging-root`),
application database `phishlens_dev`, and Auth database `phishlens_dev` on
2026-11-22 (Asia/Manila) in this Codex conversation. The selection is recorded in
`.github/secretary.json` and pinned by the staging release guards.

The selected #268 base at `d31a76b` changes the database endpoint pin to
`ep-winter-wind-a1y2r1db`, superseding the earlier database host recorded from
the metadata check. The Auth host remains the host from that owner mapping.
Privately verify both still resolve to this project/branch and that Render's
runtime and migration URLs use the updated database endpoint before any hosted
run. Until that check is complete, the target mapping is code-pinned but not
accepted for deployment or writes.

Read-only Neon metadata identified one ready compute endpoint on that branch and
the branch Auth endpoint at `/phishlens_dev/auth`. The branch is an independent
root and was marked default in the metadata read. Its PG and Auth hostnames are
pinned in `.github/secretary.json`; this record intentionally does not reproduce
connection strings or credential values. Neon Auth's trusted-origin settings
included `https://phishlens-staging.onrender.com` during the metadata read.

**Release status: NO-GO.** These checks identify the target but do not prove that
Render currently connects to it. No Render secret values were inspected in this
work session. No staging deployment, migration, account creation, or Auth/CRUD
write was run. The Render runtime and migration server-side identities remain
unverified, as do the protected schema-only and no-production-rows attestations,
and the registration/verification state of both synthetic Auth accounts.

## Evidence currently available

| Area | Recorded evidence | Status |
| --- | --- | --- |
| Owner target selection | Authorized owner selected `hidden-shadow-38533062` / `br-broad-feather-b3261w7l`, `phishlens_dev` for app and Auth | Confirmed in conversation; record the signed/owned change reference if the team's release system requires one |
| Neon metadata | Branch ready/root; one compute endpoint; database `phishlens_dev` owned by `neondb_owner`; Auth path `/phishlens_dev/auth`; staging API origin trusted | Read-only metadata checked; schema-only initialization and row isolation still need attestation |
| Render runtime | Expected DB `phishlens_dev`, role `phishlens_staging_app`, approved branch host | Current `DATABASE_URL` server identity not verified |
| Render migration | Expected DB `phishlens_dev`, role `neondb_owner`, same approved branch host | Current migration server identity not verified |
| Auth accounts | Two synthetic accounts are required; CI does not create accounts | A/B existence, distinct subjects, and verified-email state remain unverified |
| Candidate | PR #266 was based on head `85ddf64661530c88b103df8dcabaabd482198439`; this reliability patch is to be reviewed on the updated PR head | Do not reuse a run or approval from the earlier head |
| Prior staging attempts | Run #449301 reached Auth sign-in and timed out for account A; run #449337 stopped on staging host/name mismatch | Historical failure evidence only; neither establishes current mapping |
| Release approval | Issue #153 remains NO-GO; independent reviewer approval and complete release scorecard evidence are outstanding | Do not merge around required protection or mark release ready |

## Code changes in this candidate

- Pin the selected Neon project, branch, database endpoint host, and Auth host in
  `.github/secretary.json`; compare the protected workflow variables and Render
  environment mapping against that target.
- Keep `scripts/start_staging.py` fail-closed if Render startup sees a different
  project, branch, database host, Auth host/path, or non-Neon report mode. This
  guard does not change or relax its allowlist.
- Require GitHub's packaged Auth URL and Render's `NEON_AUTH_BASE_URL` to match the
  approved host and `/phishlens_dev/auth` path before the deploy controller runs.
- Add a non-mutating `OPTIONS` CORS preflight to the email sign-in route. It checks
  DNS/TLS reachability and that the staging API origin, POST method, content type,
  and credentialed browser flow are allowed. Redirects fail closed.
- Require two different, pre-registered synthetic accounts and both protected
  credentials before the staging deploy step; CI never creates them.
- Sign in both accounts and obtain distinct JWT subject hashes before any report
  CRUD. The extension's account layer rejects sessions unless `emailVerified` is
  true. Acceptance artifacts record only subject hashes, safe status categories,
  and cleanup evidence; they do not record emails, passwords, cookies, or tokens.
- Use bounded and sanitized Auth failure categories, clean up acceptance reports,
  and sign out the active synthetic account during final cleanup.

All changes remain code-only until an independent review and required branch
protections pass. The workflow's staging step must still be reviewed against the
exact candidate SHA before any protected environment approval.

## Owner checklist before any protected staging run

1. **Confirm current Render runtime identity privately.** Verify the current
   `DATABASE_URL` resolves to the approved branch and that a read-only connection
   reports `current_database() = phishlens_dev` and
   `current_user = phishlens_staging_app`. Do not send the URL, password, or full
   host string in chat or commit it to the repository.
2. **Confirm current migration identity privately.** Verify
   `STAGING_MIGRATION_DATABASE_URL` maps to the same approved host/database and
   reports `current_user = neondb_owner`; keep it separate from the runtime role.
3. **Confirm current Auth mapping privately.** Render `NEON_AUTH_BASE_URL` must
   match the approved Neon Auth host and `/phishlens_dev/auth` path, and GitHub
   `PHISHLENS_STAGING_AUTH_URL` plus `PHISHLENS_STAGING_AUTH_DATABASE` must match
   the same branch/database. Keep the staging origin at
   `https://phishlens-staging.onrender.com`.
4. **Attest data isolation.** Confirm the branch was initialized schema-only and
   contains no production rows; keep it a root branch separate from production.
   The current workflow requires `STAGING_NEON_SCHEMA_ONLY_ATTESTATION=true`,
   `STAGING_NEON_PRODUCTION_ROWS_PRESENT=false`, and a current
   `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION`.
5. **Prepare two accounts outside CI.** Register synthetic accounts A and B on
   the approved Auth branch, verify each account's email, confirm the accounts
   are distinct, and store their credentials only in the protected GitHub secrets
   `STAGING_AUTH_USER_A_EMAIL`, `STAGING_AUTH_USER_A_PASSWORD`,
   `STAGING_AUTH_USER_B_EMAIL`, and `STAGING_AUTH_USER_B_PASSWORD`. Do not use
   personal accounts or create accounts from the workflow.
6. **Run the exact candidate gates in order.** Require the current PR head,
   migration preflight, isolated Neon metadata check, Render DB/Auth mapping,
   no-write Auth CORS preflight, exact extension package, and the two-account
   browser acceptance. A skipped step, missing artifact, timeout, or stale SHA is
   not a pass.
7. **Record and review the same candidate.** Record PR head SHA, deployed merge
   SHA, migration revision, model/provider identity, extension ZIP checksum,
   workflow run, and cleanup outcome. Require independent reviewer approval and
   the required GitHub branch protection before merging.
8. **Keep NO-GO until every release area passes.** Obtain Wilberr's AI policy and
   representative holdout approval; complete environment identity, rollback and
   recovery measurements, scope/acceptance decisions, and the scorecard for this
   same candidate. Do not treat target selection or a green non-hosted CI run as
   release approval.

## Protected variable contract

The workflow expects these existing GitHub variables to describe the same
approved target: `STAGING_NEON_PROJECT_ID`, `STAGING_NEON_BRANCH_ID`,
`STAGING_NEON_EXPECTED_HOST`, `SECRETARY_STAGING_DB_HOST`,
`PHISHLENS_STAGING_AUTH_URL`, `PHISHLENS_STAGING_AUTH_DATABASE`,
`STAGING_BASE_URL`, `STAGING_AUTH_TRUSTED_CHROME_ORIGIN`,
`STAGING_NEON_SCHEMA_ONLY_ATTESTATION`,
`STAGING_NEON_PRODUCTION_ROWS_PRESENT`, and
`STAGING_RENDER_DATABASE_CONFIG_ATTESTATION`. The Render service must use
`DATABASE_URL`, `STAGING_MIGRATION_DATABASE_URL`,
`STAGING_APP_DATABASE_ROLE`, `STAGING_DATABASE_HOST`,
`STAGING_NEON_EXPECTED_HOST`, `STAGING_NEON_PROJECT_ID`,
`STAGING_NEON_BRANCH_ID`, `NEON_AUTH_BASE_URL`, and
`REPORT_AUTH_MODE=neon`. Verify names and masked identities privately; do not
copy values into this record.

## Local verification and merge boundary

The code proposal is based on PR #266's exact source branch, not the dirty local
checkout. The current targeted offline release/deployment suites passed (109
tests and 33 subtests); Ruff, the staging runner's Node syntax check, embedded
workflow Python syntax, and `git diff --check` passed. A full `scripts/tests` run
passed 284 tests but two package identity checks failed on this Windows checkout
because Git's CRLF working-tree conversion changed the packaged `config.js`
bytes. Running the package identity tests with the index's canonical LF bytes
passed all six tests; no source change to `extension/js/config.js` was made. The
later targeted run includes an additional Neon CLI target-pin regression test.

Do not run hosted staging, migrations, account creation, or CRUD as part of local
verification. Push only the reviewed code proposal to PR #266; merge only after
the independent review and required checks approve the updated head. If those
protections are unavailable, leave the PR open and retain NO-GO.
