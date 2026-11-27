# Staging reliability and release checklist — updated 2026-11-27

## Integration decision — 2026-11-27

**Selected proposal: the #251 staging target, carried forward by PR #266.**
The release owner previously recorded the #251 integration as the accepted
base. Current `main` is `46f0298d8e3299afa74e02882081be56c1de4933`; it includes
#251's merge at `28f136894ac0c220fc370feb926da335472b283d`. The current PR #266
branch is `251d7b83d6dc58324539be5668bbdd3aea8083dc`, 42 commits ahead of and
zero behind that `main` base.

The Nov. 25 recheck of #266 at `18fa7c8` found a clean standalone integration.
That SHA is no longer the branch head. Use the current branch head and its own
checks for any next step.

PR #268's `phishlens-staging` / `staging-root` target is a separate, unselected
proposal. PR #281's `9e778d5` integration proposal is also unselected; its
described order is not actual ancestry because #281 was based on `main`, not
#268. Do not merge either branch wholesale into this selected path. If specific
changes are later chosen, rebase them onto the selected base, preserve the
#251 target, and verify the resulting exact SHA before staging.

These docs record the integration choice only. They do not authorize production
promotion.

## Selected staging target

The selected #251-based target uses Neon project `ancient-brook-17208049`,
branch `br-rough-sea-a1l6ehi1`, PostgreSQL endpoint
`ep-winter-wind-a1y2r1db.ap-southeast-1.aws.neon.tech`, application/migration
database `phishlens_dev`, and Auth database `neondb` at `/neondb/auth`. The
non-secret identities are pinned in `.github/secretary.json`; connection
strings and credentials are intentionally omitted. Recheck runtime and
migration identities privately for every new candidate.

## Current candidate status before this documentation update

PR #266's pre-edit head was `251d7b83d6dc58324539be5668bbdd3aea8083dc`. The
latest Secretary report, [run 45930182262](https://github.com/kendshhh/PhishLens/actions/runs/45930182262),
reported Extension checks passing, Backend checks in progress, and Staging
integration missing. The reported preview deployment SHA was
`01153fd81ea7301acb565c4f5ac47e0d0afc3dac`, not the exact PR head. This is not
current-head hosted staging acceptance.

## Historical exact-head acceptance

- PR #266 head `18fa7c8` passed its recorded [CI run 45525200065](https://github.com/kendshhh/PhishLens/actions/runs/45525200065)
  and [Trusted staging Neon check 45525195574](https://github.com/kendshhh/PhishLens/actions/runs/45525195574),
  including hosted acceptance. This evidence applies only to `18fa7c8`.
- Earlier head `44ddb46` passed [Hosted staging run 45521263702](https://github.com/kendshhh/PhishLens/actions/runs/45521263702).
  It is also historical and does not establish acceptance of a later head.
- PR #268's alternate target and PR #281's proposed integration remain
  separate from this evidence and from the selected #251 target.

## Evidence summary

| Area | Current record | Boundary |
| --- | --- | --- |
| Integration base | `main` at `46f0298`; #266 pre-edit head `251d7b8` was 42 ahead and 0 behind | New documentation commits require fresh exact-head checks |
| Staging target | #251 target: `ancient-brook-17208049` / `br-rough-sea-a1l6ehi1` | Non-secret identities only; recheck runtime and migration mapping privately |
| Current checks | Latest report on `251d7b8`: Extension passed, Backend in progress, Staging integration missing | No current-head hosted acceptance is established |
| Prior staging runs | #266 heads `18fa7c8` and `44ddb46` passed their recorded hosted checks | SHA-bound historical evidence only |
| Production release | **NO-GO** | No production deployment or approval is claimed |
## Changes retained in #266

After reconciliation against #251, this PR's distinct changes are the non-secret
staging identity mapping, the architecture/runbook updates, and the bounded Auth
endpoint/provider-error diagnostics helper with its tests. Shared CI, Auth,
startup, package, and release implementations remain those accepted in #251.
The changes do not add a migration or grant the PR workflow a staging Neon key.

## Owner checklist for a later candidate

1. Recheck the current PR head and protected staging target before a new run.
2. Privately verify Render's runtime and migration URLs resolve to the approved
   project, branch, database, and least-privilege roles. Do not copy URLs,
   passwords, or secret values into a commit or chat.
3. Confirm the protected branch remains isolated, schema-only as required, and
   contains no production rows before any staging write workflow.
4. Use two distinct pre-registered synthetic accounts with verified email and
   credentials stored only in protected GitHub secrets. CI must not create
   accounts or use personal accounts.
5. Require the exact-head migration, target, Auth, package, and authenticated
   acceptance gates. A skipped step, missing artifact, timeout, or stale SHA is
   not a pass.
6. Keep AI-quality approval and production release review separate from staging
   acceptance. The project remains NO-GO until every required release gate passes.

## Protected variable contract

The workflow expects the protected GitHub variables to describe this same
candidate target, including `STAGING_NEON_PROJECT_ID`,
`STAGING_NEON_BRANCH_ID`, `STAGING_NEON_EXPECTED_HOST`,
`SECRETARY_STAGING_DB_HOST`, `PHISHLENS_STAGING_AUTH_URL`,
`PHISHLENS_STAGING_AUTH_DATABASE`, `STAGING_BASE_URL`,
`STAGING_NEON_SCHEMA_ONLY_ATTESTATION`,
`STAGING_NEON_PRODUCTION_ROWS_PRESENT`, and
`STAGING_RENDER_DATABASE_CONFIG_ATTESTATION`. Render's runtime and migration
settings must keep their separate roles. Record names and masked identities
only; never write secret values here.

## Verification boundary

This documentation reconciliation does not rerun tests or staging. It advances
PR #266 beyond the previously checked code heads, so all existing CI and hosted
acceptance results remain bound to their recorded SHAs. Require current-head CI
and the protected staging gate before treating a later candidate as accepted.
Production remains NO-GO; no production deployment or approval is claimed.
