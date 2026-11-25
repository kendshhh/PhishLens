# Staging reliability and release checklist — updated 2026-11-25

## Agreed integration base

- PR #251 is merged into `main` at `28f136894ac0c220fc370feb926da335472b283d`. Use that accepted tree as the integration starting point.
- PR #266 at `44ddb461308c29ac3014f9e0ce0b41db267e9d84` merges current `main` with the prior #266 head; it keeps #251's shared workflow, Auth, staging, and release implementations.
- PR #268 and #281 are separate branches based on the older `54ce4af` main. PR #281 is not actually based on #268 despite its title; do not treat its proposed order as Git ancestry. Bring only agreed changes into a #251-based integration candidate.
- The `phishlens-staging` / `staging-root` target documented on the parallel #268 branch is not the target used by the accepted #251-based staging run. Preserve the current target below when reconciling their docs.
- #266 adds no database migration. Keep the single `0005_ai_request_quota` revision from #251, with `0004_neon_auth_subject` as its parent.

## Current staging target

The #251-based candidate uses Neon project `ancient-brook-17208049`, branch
`br-rough-sea-a1l6ehi1`, PostgreSQL endpoint
`ep-winter-wind-a1y2r1db.ap-southeast-1.aws.neon.tech`, application/migration
database `phishlens_dev`, and Auth database `neondb` at `/neondb/auth`.
The non-secret identities are pinned in `.github/secretary.json`; connection
strings and credentials are intentionally omitted. Runtime and migration
credentials remain separate and are verified privately by the protected staging
workflow.

## Current evidence and decision

**Production release status: NO-GO.** Hosted staging run [45521263702](https://github.com/kendshhh/PhishLens/actions/runs/45521263702) completed on exact PR #266 head `44ddb461308c29ac3014f9e0ce0b41db267e9d84`. The trusted Neon check, migration-source preflight, backend checks, extension checks, staging integration, dependency/security checks, workflow lint, and Hosted staging passed on that head.

Hosted staging verified the isolated Neon and Render mapping, confirmed migration head `0005_ai_request_quota`, deployed the exact PR head, completed authenticated extension saved-report acceptance and cleanup, and uploaded the staging extension/evidence artifact. This is evidence for `44ddb46` only. Do not reuse it as exact-head evidence after the PR advances.

The earlier hosted attempts—including run `45040106942` with an HTTP 401 for account A, and runs that stopped on a Render update failure—are historical and superseded for `44ddb46`. They do not establish results for a later commit.

The staging product path passed on that SHA. AI-quality approval and production promotion remain separate gates; CI and hosted staging success do not make the release GO. No production deployment is claimed.

## Evidence summary

| Area | Evidence on `44ddb46` | Boundary |
| --- | --- | --- |
| Protected target | Project, branch, PostgreSQL host, and Auth mapping matched the approved candidate target | No secret values are recorded here |
| Render runtime and migration | Protected preflight passed for the staging service and the separate database roles | Recheck privately for a later candidate |
| Migration lineage | Preflight passed through `0005_ai_request_quota` | Keep only one copy of the migration |
| Auth and saved reports | Exact-head authenticated extension acceptance and saved-report CRUD/cleanup passed | Evidence is SHA-bound to `44ddb46` |
| Browser package | Exact-head staging extension artifact and browser acceptance were preserved | Do not treat an artifact for another SHA as current |
| AI quality | Not approved by the hosted staging check | Representative holdout review remains required |
| Production release | NO-GO | No production deployment or approval is claimed |

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

The successful hosted run is for exact head `44ddb46`, before this documentation
reconciliation. No local tests or staging actions were run for this documentation
change. The next commit must use its own current-head CI and any required
protected staging approval. Keep production status NO-GO until independent
AI-quality approval and the separate promotion controls pass.
