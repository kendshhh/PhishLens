# Staging reliability and release checklist — 2026-11-22

## Decision and current state

The protected staging mapping uses Neon project `ancient-brook-17208049`, branch
`br-rough-sea-a1l6ehi1`, PostgreSQL endpoint
`ep-winter-wind-a1y2r1db.ap-southeast-1.aws.neon.tech`, and separate Auth database
`neondb` at `/neondb/auth`. Application and migration URLs remain pinned to
`phishlens_dev` and their separate runtime/owner roles. The non-secret target
identities are recorded in `.github/secretary.json`; connection strings and
credentials are intentionally omitted. The selected integration path targets `main` at
`d2057e1c747efd97b7232c82e18d5445b49a9307`, which contains the #251-based mainline.
PR #281 is not based on PR #268. Earlier pairwise merge simulations against #266 and
#268 each produced conflicts, so those branch heads are not treated as part of this
candidate. PR #281 code revision `c9346913605c459e79734152b9b4dc09d8253345` is the
revision verified by CI.

**Release status: NO-GO.** Historical hosted run `45040106942` passed the
protected Neon, Render, and Auth mapping preflights and deployed candidate
`4e4481d6279a7404d35b21d4a32ef5d0c280311b`. The staging service reported healthy
and ready at migration revision `0004_neon_auth_subject`. Acceptance stopped
during account A sign-in with HTTP 401, before report CRUD; the sanitized evidence
records zero production requests and writes. This was PR #266 candidate evidence,
not a deployment or acceptance result for PR #281. No Render secret values were
inspected and CI did not create Auth accounts. Confirm that both synthetic
accounts exist and are verified on the protected `neondb` Auth target, and that
the protected secret pair matches, before another hosted acceptance run. Schema
and production-row attestations remain separate release gates.

## Evidence currently available

| Area | Recorded evidence | Status |
| --- | --- | --- |
| Protected target mapping | Project `ancient-brook-17208049` / branch `br-rough-sea-a1l6ehi1`; PostgreSQL endpoint `ep-winter-wind-a1y2r1db`; app/migration DB `phishlens_dev`; Auth DB `neondb` | Non-secret protected identities checked read-only; Render URL identities and data isolation still require private verification/attestation |
| Neon/Auth readiness | Auth path `/neondb/auth`; staging API origin configured | No current Auth/CRUD acceptance; schema-only initialization and row isolation still need attestation |
| Render runtime | Expected DB `phishlens_dev`, role `phishlens_staging_app`, approved branch host | Current `DATABASE_URL` server identity not verified |
| Render migration | Expected DB `phishlens_dev`, role `neondb_owner`, same approved branch host | Current migration server identity not verified |
| Auth accounts | CI does not create accounts; hosted run `45040106942` received HTTP 401 for account A | Verify A/B registration, verified-email state, and protected secret mapping on the current Auth target |
| Candidate | PR #281 verified code revision `c9346913605c459e79734152b9b4dc09d8253345` against `main` at `d2057e1c747efd97b7232c82e18d5445b49a9307` | CI run `45943315598` passed; no hosted deployment was performed |
| Earlier hosted candidate | PR #266 candidate `4e4481d6279a7404d35b21d4a32ef5d0c280311b` | Run `45040106942` is historical and does not verify PR #281 |
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
  approved Auth host and `/neondb/auth` path before the deploy controller runs.
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
   match the approved Neon Auth host and `/neondb/auth` path, and GitHub
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

## Current PR verification and merge boundary

PR #281 targets `main` at `d2057e1c747efd97b7232c82e18d5445b49a9307`, the
selected #251-based mainline. Its verified code revision is
`c9346913605c459e79734152b9b4dc09d8253345`; the PR is mergeable with no conflict.
The #268-based title and stale verification summary have been corrected.

[CI run 45943315598](https://github.com/kendshhh/PhishLens/actions/runs/45943315598)
passed for that code revision. The staging integration job passed all 335 tests,
including staging extension package verification. The synthetic Auth bridge
browser acceptance passed against a local disposable PostgreSQL database; it
covers the fixed generated-config parsing and registration/sign-out/sign-in
sequence. Extension package identity verification and isolated Chromium
acceptance also passed.

This CI run did not deploy to protected hosted staging, create real Auth
accounts, run a hosted migration, or touch production. Keep release status NO-GO
until the protected-target attestations, hosted authenticated acceptance, and
independent release approvals are complete.
