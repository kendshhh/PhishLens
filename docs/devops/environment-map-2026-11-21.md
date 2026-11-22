# Environment and Secret Map — 2026-11-21

This map records current non-secret service identities and evidence boundaries.
It does not store credential values. Render environment-variable values were
not exposed in this audit, so live URLs/roles cannot be proven from a healthy
readiness response alone.

## Environment map

| Environment | Service and data target | Runtime/configuration evidence | Status and open controls |
|---|---|---|---|
| Local development | Developer machine; `.env` is git-ignored. | `.env.example` supplies development/mock/demo defaults. | Repository configuration only. No local secret values were read. |
| CI | Disposable PostgreSQL test database; synthetic credentials and mock AI. | Workflow source on latest observed `main` is `811980c2cbf70d9957146bf329627f0826a018f1`. | Workflow configuration is inspectable; no current full CI run was established in this refresh. CI credentials are not hosted credentials. |
| Hosted staging | Render service `phishlens-staging`, ID `srv-db92irlg1s2s739404i0`, URL `https://phishlens-staging.onrender.com`; latest recorded deploy must be rechecked before a candidate run. | GitHub `staging` environment explicitly targets Neon project `hidden-shadow-38533062`, branch `br-broad-feather-b3261w7l` (`staging-root`), Auth DB `phishlens_dev`. The local startup guard still pins legacy `patient-bird-25428852` / `pr-58-staging`. | Render actual app/migration URLs and role mapping remain unverified. The selected Auth config allows localhost and does not require email verification. The latest reported hosted product-acceptance attempt failed at sign-in and downstream checks. No complete authenticated CRUD or browser pass is established. |
| Production | Render service `phishlens-api`, ID `srv-db7eap25b2lc73fkelpg`, URL `https://phishlens-api-ocvt.onrender.com`; deploy `dep-dc07rs67bikc73fjgjq0`, SHA `811980c2cbf70d9957146bf329627f0826a018f1`. | Read-only `/version`, `/health`, `/ready`, `/model-info` returned 200. Model info: `provider_mode=disabled`, `analysis_enabled=false`, required-provider support false, TF-IDF reports false. | Exact Neon branch/role mapping, runtime Auth/provider values and secret access control are not verified. No inference or saved-report write was performed. The disabled state is not product acceptance. |
| Render deployment controls | Both services are configured for branch `main`; service metadata says auto-deploy off. | Production latest deploy event reports trigger `new_commit`; staging latest trigger is `api`. | Production setting/event mismatch remains unresolved. Verify actual Dashboard controls and deployment audit trail before relying on auto-deploy semantics. Do not infer service configuration from a single deploy event. |
| GitHub staging controller | Local change to `.github/workflows/ci.yml` preflights two distinct Auth test accounts and matches the Auth URL path to the existing `PHISHLENS_STAGING_AUTH_DATABASE` variable, then runs the exact-head `verify_crud.mjs --authenticate` path. The browser package/test identity now uses the exact PR merge candidate SHA, and the browser evidence artifact is mandatory. | Protected environment inspection found `STAGING_NEON_AUTH_URL`, `PHISHLENS_STAGING_AUTH_DATABASE`, and four A/B account secrets; old single-account secrets also remain. The local workflow still requires reconciliation with current `origin/main` before hosted use. | Keep the existing variable names; do not create a parallel `STAGING_NEON_AUTH_DATABASE`. A separate nested acceptance candidate expects `PHISHLENS_STAGING_AUTH_URL`, which does not match the observed URL variable. Confirm the target and policy before rerunning hosted acceptance. No authenticated CRUD result is established. Last recorded Secretary rollout values were from Nov 20 and need a fresh read. |
| GitHub production observer | `Production evidence` workflow is manual (`workflow_dispatch`) and read-only with respect to application data. | On `main`, the disabled-provider observer can report identity/health/readiness/disabled state without inference or database writes. | No current observer run was performed. Effective required checks and production-observer environment access scopes are not verified. |

## Read-only Neon details

The existing Neon project `patient-bird-25428852` (`phishlens`, AWS
`ap-southeast-1`) has staging branch `pr-58-staging` and production branch
`production` (`br-orange-sky-b3zzzyqc`). A second project,
`hidden-shadow-38533062` (`phishlens-staging`), has branch `staging-root`.
Read-only Auth inspection on Nov 21 found the existing project's Auth database
is `neondb`, with localhost disabled and email verification required. The new
project's Auth database is `phishlens_dev`, with localhost enabled and email
verification not required. Both list the staging Render origin. GitHub's
protected staging environment explicitly points Auth at the new project/branch,
but Render's actual branch and role mapping remains unknown. The old project's
recorded migration revision is `0004_neon_auth_subject`.

## Secret names and safe review

Repository/workflow configuration references names including `DATABASE_URL`,
`REPORT_AUTH_MODE`, `NEON_AUTH_BASE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`,
`RENDER_STAGING_API_KEY`, `RENDER_STAGING_SERVICE_ID`, `STAGING_BASE_URL`,
`STAGING_NEON_AUTH_URL`, `PHISHLENS_STAGING_AUTH_DATABASE`, `STAGING_AUTH_USER_A_EMAIL`,
`STAGING_AUTH_USER_A_PASSWORD`, `STAGING_AUTH_USER_B_EMAIL`, `STAGING_AUTH_USER_B_PASSWORD`, `SECRETARY_PREVIEW_ENABLED`, `SECRETARY_STAGING_DB_HOST`,
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
