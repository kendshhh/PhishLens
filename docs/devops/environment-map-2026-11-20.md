# Environment and Secret Map — 2026-11-20

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
| Hosted staging | Render `phishlens-staging`; current observed backend SHA `d6612c258f289b3a45d8229e4a4803cac75a91ee`; auto-deploy is off. | `/version` identifies staging; `/ready` reports database connected; `/model-info` reports TF-IDF. Auth mode and exact database branch are not established by these endpoints. | GitHub `staging` environment is intended to hold the deploy credential; Render service variables are expected to hold database, Auth and optional provider configuration. Expected selector names are documented in `.env.example` and `docs/devops/staging.md`. | Service identity, branch and auto-deploy setting were verified read-only. Exact Render-to-Neon branch mapping, current variable presence, secret permissions, and Authenticated CRUD are **NOT VERIFIED**. Nov. 8 configuration history is historical and must be rechecked. |
| Production | Render `phishlens-api`; live deploy `dep-dbvt8r0u01pc73b4siig` on SHA `60641f32353c61a5b1f0dcfca1e0f5912afb76b3`; auto-deploy is `checksPass` on `main`. | `/version` identifies production; `/health` and `/ready` return 200 with database connected; `/model-info` reports provider unavailable and `accepts_tfidf_reports=false`. | The application requires database and provider settings in Render. Their presence, values and access policy are not exposed by the connected service metadata. Do not copy credential values to GitHub, docs, logs, or artifacts. `REPORT_AUTH_MODE` must be explicit for an accepted release. | Service identity, branch, health path, auto-deploy trigger and endpoint behavior are verified read-only. Exact Neon branch mapping, runtime Auth mode, provider variable presence/access and secret permissions are **NOT VERIFIED**. Provider behavior is currently unusable for the target release. |
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
