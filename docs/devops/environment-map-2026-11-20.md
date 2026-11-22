# Environment and Secret Map — 2026-11-20

> Historical snapshot. The November 21
> [environment map](environment-map-2026-11-21.md) refreshes live service and
> Neon evidence. Keep this dated record as history; do not copy its deployment
> identities or auto-deploy claim into current release decisions.

This map names configuration and its intended scope without storing secret
values. It distinguishes checked-in configuration from live values: the
connected evidence does not expose Render environment-variable values or
prove their access controls. A green health endpoint is not proof of a correct
database branch, Auth mode, or AI provider configuration.

## Environment map

| Environment | Service and data target | Non-secret runtime settings | Secret/configuration boundary | Current evidence and status |
|---|---|---|---|---|
| Local development | Developer machine; `.env` is git-ignored. `DATABASE_URL` must target a local/dedicated development database. | `.env.example` defaults to `APP_ENV=development`, `AI_MODE=mock`, `REPORT_AUTH_MODE=demo`; `GEMINI_MODEL` and `NEON_AUTH_BASE_URL` are blank. | Local `.env` only. Never copy hosted credentials into it. Gemini requires `GEMINI_API_KEY`, model, matching model-specific rates, and a per-request cap before inference. | Repository controls verified. No local secret values read. |
| CI | Disposable PostgreSQL service and test database; workflows use mock AI and synthetic credentials. | `RUN_DATABASE_TESTS=1`, `AI_MODE=mock`; migration checks target the disposable test database. | GitHub Actions job environment; CI-only credentials are not production credentials. | Workflow source verified in `.github/workflows/ci.yml`. |
| Hosted staging | Render `phishlens-staging`; live deploy `dep-dc018hlg1s2s73dtalng` on backend SHA `d6612c258f289b3a45d8229e4a4803cac75a91ee`; auto-deploy is off. | Exact-head preflight run #1231 reports `/version` as staging, `/ready` connected, `/model-info` TF-IDF, `REPORT_AUTH_MODE=neon`, and anonymous saved-report `401 Bearer`. | GitHub `staging` environment is intended to hold the deploy credential; Render service variables are expected to hold database, Auth and provider configuration. Never copy credential values into docs or artifacts. | Bounded preflight records Neon project `patient-bird-25428852`, branch `pr-58-staging` (`br-delicate-paper-b381z98i`), DB `phishlens_dev`, role `phishlens_staging_app`, Auth DB `neondb`, and migration head `0004_neon_auth_subject`. The exact private Render connection-to-branch/role mapping, runtime grants, secret permissions, seeded history, installed Chrome, and authenticated CRUD remain **NOT VERIFIED**. No staging write was made. |
| Production | Render `phishlens-api`; Render reports live deploy `dep-dc03j4sipgvc738ueieg` on SHA `16f955321caf5dc368181be7ce5c00643750545d`; auto-deploy is `checksPass` on `main`. | Current `/version`, health/readiness, Auth and model endpoints were not independently verified because the direct endpoint returned a Cloudflare challenge. The prior SHA `60641f3` reported provider unavailable and `accepts_tfidf_reports=false`; do not silently carry that result forward as a current probe. | The application requires database, Auth and provider settings in Render. Their presence, values and access policy are not exposed by connected service metadata. Do not copy credential values to GitHub, docs, logs, or artifacts. | Service identity, live deployment SHA and auto-deploy trigger are verified read-only. Exact Neon branch mapping, runtime Auth/provider modes, secret access controls and current feature behavior are **NOT VERIFIED**. Run the exact-SHA observer before any release decision. |
| GitHub hosted-staging controller | `Secretary preview` runs from trusted default-branch controller code; `CI` only invokes the hosted deploy for eligible same-repository PRs. | Workflow code reads preview controls and separate staging/production database-host identifiers; workflow names are in `.github/workflows/secretary-preview.yml` and `ci.yml`. | `RENDER_STAGING_API_KEY` is intended to be scoped to the protected `staging` GitHub environment. | Workflow code is verified. Current secret existence, value, permissions and host-to-branch mapping were not re-verified in the connected control plane. |
| GitHub production observer | `Production evidence` is a manual observer and does not deploy or roll back. | Workflow is `workflow_dispatch` only. | `RENDER_OBSERVER_API_KEY` is intended to be scoped to `production-observer`. | Workflow source is verified; current secret access policy and current observer run are not verified. |

## Configuration names (values omitted)

- Backend runtime: `DATABASE_URL`, `APP_ENV`, `AI_MODE`, `REPORT_AUTH_MODE`,
  `NEON_AUTH_BASE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`,
  `GEMINI_INPUT_USD_PER_MILLION_TOKENS`,
  `GEMINI_OUTPUT_USD_PER_MILLION_TOKENS`, `GEMINI_COST_MODEL_ID`, and
  `GEMINI_PER_REQUEST_COST_CAP_USD`.
- Hosted-staging safety: `STAGING_DATABASE_HOST`,
  `STAGING_APP_DATABASE_ROLE`, and `STAGING_MIGRATION_DATABASE_URL`.
- GitHub deploy/observer: `RENDER_STAGING_API_KEY`,
  `RENDER_STAGING_SERVICE_ID`, `STAGING_BASE_URL`, `RENDER_OBSERVER_API_KEY`,
  `SECRETARY_PREVIEW_ENABLED`, `SECRETARY_STAGING_DB_HOST`, and
  `SECRETARY_PRODUCTION_DB_HOST`.
- Evaluation-only bounds: `GEMINI_PER_RUN_COST_CAP_USD` and
  `GEMINI_MAX_REQUESTS`. These do not create a shared durable production daily
  or monthly budget.

## Required control-plane verification before GO

The release/platform owner must verify the exact Render service-to-Neon branch
and role mapping privately; confirm production and staging are distinct; confirm
the effective `REPORT_AUTH_MODE` and provider configuration without displaying
values; verify least-privilege runtime database grants; and review GitHub
environment secret scopes and required reviewers. Record only setting names,
scope, reviewer/owner, verification time, and pass/fail. Do not paste secret
values into this repository. These checks are outstanding, so this document
improves the map but does not convert the environment/secrets criterion to
PASS.
