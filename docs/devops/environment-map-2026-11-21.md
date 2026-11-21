# Environment and Secret Map — 2026-11-21

This map records current non-secret service identities and evidence boundaries.
It does not store credential values. Render environment-variable values were
not exposed in this audit, so live URLs/roles cannot be proven from a healthy
readiness response alone.
Render service and deployment metadata were rechecked read-only at
2026-11-21 07:31 UTC. A later direct GET-only staging smoke at 08:15 UTC passed
health, readiness, and the anonymous Bearer-auth boundary using the review
branch script. A follow-up smoke at about 08:35 UTC passed the same GET-only
checks after synchronizing the smoke helper with main. Neither run verified
`/version`, deployed PR identity, migration state, or authenticated CRUD.

## Environment map

| Environment | Service and data target | Runtime/configuration evidence | Status and open controls |
|---|---|---|---|
| Local development | Developer machine; `.env` is git-ignored. | `.env.example` supplies development/mock/demo defaults. | Repository configuration only. No local secret values were read. |
| CI / current main | Disposable PostgreSQL test database; synthetic credentials and mock AI. | Main is `95975cd47dceeac74ea36054610956f0a1db1fa9`, which merged PR #265. Its CI [44889931821](https://github.com/kendshhh/PhishLens/actions/runs/44889931821) and CodeQL [44889931096](https://github.com/kendshhh/PhishLens/actions/runs/44889931096) passed; workflow lint [44889931690](https://github.com/kendshhh/PhishLens/actions/runs/44889931690) and dependency security [44889931677](https://github.com/kendshhh/PhishLens/actions/runs/44889931677) passed. PR #268 code/test commit `83a0df1af1d64048b3b5fa3158f6509e83d71555` contains bounded retries, diagnostics, local server monitoring/log retention and fail-closed hosted deployment gates. The PR branch includes main code through `14874d3` and shared docs through `ca29235`. | Main's complete current check set passed for the merged snapshot. The previous main CI failure on `06f89d7` is historical. See the current PR-specific row for separate review status; CI credentials are not hosted credentials. |
| PR #268 current check snapshot | Head `a151585ff92d55f21e0364e9838287a9cf04a68d` observed at 11:08 UTC. PR #268 remains open and still targets `codex/readiness-update-20261121` at `ca29235`, now merged into main at `95975cd`. The 10:14 `2e26327` result is a historical snapshot. | Backend and migration source preflight passed in [CI 44897548076](https://github.com/kendshhh/PhishLens/actions/runs/44897548076); workflow lint [44897548088](https://github.com/kendshhh/PhishLens/actions/runs/44897548088), dependency security/graph [44897548010](https://github.com/kendshhh/PhishLens/actions/runs/44897548010), deterministic evaluation [44897548070](https://github.com/kendshhh/PhishLens/actions/runs/44897548070), and DevOps Secretary report [44897544530](https://github.com/kendshhh/PhishLens/actions/runs/44897544530) passed. | Extension checks failed the Saved reports view keyboard focus assertion in `scripts/browser_acceptance.mjs:700`. Staging integration, Hosted staging preflight and Hosted staging were skipped. Required `Secretary staging` failed because the request label and exact-head hosted verification were absent ([run 44897660167](https://github.com/kendshhh/PhishLens/actions/runs/44897660167)). No current PR CodeQL result, Render deployment or authenticated CRUD. Fifteen Dependabot alerts (12 high, 3 moderate) remain open; retarget PR #268 to `main` before merge. |
| Hosted staging | Render service `phishlens-staging`, ID `srv-db92irlg1s2s739404i0`, URL `https://phishlens-staging.onrender.com`; latest live deploy `dep-dc0im3h7lnhs738pncng`, SHA `ba0b6c5475eb6a8f99c509c40384020d292e17e6`. Render metadata rechecked at 07:31 UTC reports branch `main`, auto-deploy `no`, trigger `off`. | Earlier `/version`, `/health`, `/ready`, `/model-info` returned 200. GET-only smokes at 08:15 and about 08:35 UTC passed `/health`, `/ready`, and anonymous `/api/analyses` with `401 Bearer`. Neither checked deployed PR identity. | Neon project `patient-bird-25428852`, branch `pr-58-staging` (`br-delicate-paper-b381z98i`), database `phishlens_dev`, Auth DB `neondb`, migration revision `0004_neon_auth_subject` were independently inspected read-only. Render's actual connection URL to branch/role mapping remains unverified. No authenticated CRUD or app write acceptance. |
| Production | Render service `phishlens-api`, ID `srv-db7eap25b2lc73fkelpg`, URL `https://phishlens-api-ocvt.onrender.com`; latest live deploy `dep-dc07rs67bikc73fjgjq0`, SHA `811980c2cbf70d9957146bf329627f0826a018f1`. Render metadata rechecked at 07:31 UTC reports branch `main`, auto-deploy `no`, trigger `off`. | Earlier November 21 read-only `/version`, `/health`, `/ready`, `/model-info` returned 200. Model info: `provider_mode=disabled`, `analysis_enabled=false`, required-provider support false, TF-IDF reports false. | Exact Neon branch/role mapping, runtime Auth/provider values and secret access control are not verified. No inference or saved-report write was performed. The disabled state is not product acceptance. |
| Render deployment controls | Both services are configured for branch `main`; metadata at 07:31 UTC reports auto-deploy `no` and trigger `off`. | Production latest live deploy event reports trigger `new_commit`; staging latest live deploy trigger is `api`. | Production setting/event mismatch remains unresolved. Verify Dashboard controls and deployment audit trail before relying on auto-deploy semantics. Do not infer configuration from a single deploy event. |
| GitHub staging controller | Latest observed `main` workflow `.github/workflows/ci.yml` is on `95975cd` and includes the Bearer-aware history contract; PR #268 adds bounded retry diagnostics, local server monitoring, retained logs and explicit fail-closed hosted deployment gates. | On PR head `a151585`, [CI 44897548076](https://github.com/kendshhh/PhishLens/actions/runs/44897548076) failed in Extension checks; Staging integration and hosted preflight were skipped. | Hosted staging was skipped; required `Secretary staging` failed at [44897660167](https://github.com/kendshhh/PhishLens/actions/runs/44897660167) because the request label and exact-head hosted verification were absent. No Render deploy or authenticated CRUD occurred. The hosted CRUD runner still lacks an authenticated Neon Auth session. Last recorded Secretary preview variables on Nov 20 were false; live values were not re-read. PR #268's base remains the merged PR #265 branch and should be retargeted to `main` before merge. |
| GitHub production observer | `Production evidence` workflow is manual (`workflow_dispatch`) and read-only with respect to application data. | On `main`, the disabled-provider observer can report identity/health/readiness/disabled state without inference or database writes. | No current observer run was performed. Effective required checks and production-observer environment access scopes are not verified. |

## Read-only Neon details

The connected Neon project is `patient-bird-25428852` (`phishlens`, AWS
`ap-southeast-1`). The staging branch is `pr-58-staging` and the production
branch is `production` (`br-orange-sky-b3zzzyqc`); they are separate branches
and both were reported ready. The staging Auth configuration has trusted origin
`https://phishlens-staging.onrender.com`; email/password sign-up is enabled and
email verification is required. The staging database migration revision is
`0004_neon_auth_subject`.

Read-only SQL under the staging application role showed `public` schema CREATE
false; `users` SELECT/INSERT true and UPDATE/DELETE false; and
`analyzed_emails` SELECT/INSERT/UPDATE/DELETE true. These grants and Auth
settings describe the inspected Neon branch and role. They do not prove that
Render's private connection setting uses that role or branch. No row contents,
credential values or SQL writes were used for this check.

## Secret names and safe review

Repository/workflow configuration references names including `DATABASE_URL`,
`REPORT_AUTH_MODE`, `NEON_AUTH_BASE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`,
`RENDER_STAGING_API_KEY`, `RENDER_STAGING_SERVICE_ID`, `STAGING_BASE_URL`,
`SECRETARY_PREVIEW_ENABLED`, `SECRETARY_STAGING_DB_HOST`,
`SECRETARY_PRODUCTION_DB_HOST`, and `RENDER_OBSERVER_API_KEY`. This list is not
proof that a secret is present, correct, least-privileged or assigned to the
intended environment.

Before release, an authorized owner should inspect Render and GitHub settings
privately and record only: variable/secret name, environment, masked target
identity, required reviewer/scope, verifier, date, and pass/fail. Confirm the
Render-to-Neon project, branch, database and role mapping independently for
both services; verify least privilege and protected-environment review; do not
paste values into the repository, issue, logs or artifacts. Until those checks
are recorded, environment identity and secret-control acceptance remains open.
