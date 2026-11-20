# Environment and Secret Map — 2026-11-20

This map names configuration and its intended scope without storing secret
values. It distinguishes checked-in configuration from live values: the
connected evidence does not expose Render environment-variable values or
prove their access controls. A green health endpoint is not proof of a correct
database branch, Auth mode, or AI provider configuration.

## Environment map

| Environment | Service and data target | Non-secret runtime settings | Secret/configuration boundary | Current evidence and status |
|---|---|---|---|---|
| Local development | Developer machine; .env is git-ignored. DATABASE_URL must target a local/dedicated development database. | .env.example defaults to APP_ENV=development, AI_MODE=mock, REPORT_AUTH_MODE=demo; GEMINI_MODEL and NEON_AUTH_BASE_URL are blank. | Local .env only. Never copy hosted credentials into it. Gemini requires GEMINI_API_KEY, model, matching model-specific rates, and a per-request cap before inference. | Repository controls verified. No local secret values read. |
| CI | Disposable PostgreSQL service and test database; workflows use mock AI and synthetic credentials. | RUN_DATABASE_TESTS=1, AI_MODE=mock; migration checks target the disposable test database. | GitHub Actions job environment; CI-only credentials are not production credentials. | Workflow source verified in .github/workflows/ci.yml. |
| Hosted staging | Render phishlens-staging; live deploy dep-dc018hlg1s2s73dtalng on backend SHA d6612c258f289b3a45d8229e4a4803cac75a91ee; auto-deploy is off. | /version identifies staging; /ready reports database connected; /model-info reports TF-IDF. Auth mode and exact service-to-branch mapping are not established by the public endpoints. | The GitHub staging environment contains the `RENDER_STAGING_API_KEY` secret name and has one required reviewer with self-review prevented. Repo variable `SECRETARY_PREVIEW_ENABLED=false`; `SECRETARY_REPLACES_LEGACY_STAGING=false`. Secret values and Render service variables are never recorded here. | Neon branch `pr-58-staging` / database `phishlens_dev` was inspected read-only: `phishlens_staging_app` has no `public` schema CREATE, SELECT/INSERT on `users`, and CRUD on `analyzed_emails`; UPDATE/DELETE on `users` were revoked and rechecked on 2026-11-20. This verifies that branch's effective grants, not that Render currently connects to it. Exact Render-to-Neon mapping, Auth mode, GitHub DB-host variable values and authenticated CRUD remain NOT VERIFIED. |
| Production | Render phishlens-api; main SHA `0c382dda175db3570e6bb7122841122254ba131d`; env-config deploy `dep-dc04t5dg1s2s73e5pc00` is Live on the same SHA since 13:44:56 UTC. Auto-deploy is checksPass on main. | Prior endpoint responses at 12:18 UTC were for SHA `16f955321caf5dc368181be7ce5c00643750545d`. Post-deploy direct GETs to `/version`, `/health`, `/ready` and `/model-info` from this client returned HTTP 403; effective application response is not yet verified. | `AI_ANALYSIS_ENABLED=false` is set on Render production per owner instruction. No provider key or budget has been added. Do not expose values in docs/logs. `REPORT_AUTH_MODE` must be explicit for an accepted release. | Render metadata confirms the SHA and completed deploy; the disabled-aware zero-inference smoke fix is on the review branch, not yet in main. Exact Neon branch mapping, runtime Auth mode, provider variable access and secret permissions are NOT VERIFIED. Keep AI disabled pending endpoint confirmation and an approved shared budget. |
| GitHub hosted-staging controller | Secretary preview runs from trusted default-branch code after CI completes; it does not execute PR code with the staging key. | Current repo settings keep previews disabled. The legacy CI hosted-staging path has not been retired. | `RENDER_STAGING_API_KEY` exists in the protected staging environment; one required reviewer and `prevent_self_review=true` were verified. | PR #255's missing-label fail-closed change is in main. The main controller can still publish a green required status after a Neon Auth preflight while authenticated CRUD is pending. The local review-branch follow-up makes that state fail closed and requires explicit `REPORT_AUTH_MODE=neon`; it is not merged. No current runtime-PR acceptance demonstration exists. |
| GitHub production observer | Production evidence is a manual observer and does not deploy or roll back. | Workflow is workflow_dispatch only. | RENDER_OBSERVER_API_KEY is intended to be scoped to production-observer. | Workflow source is verified; current secret access policy and current observer run are not verified. |

As of November 20, strict classic protection for main requires eight statuses:
Backend checks, Extension checks, Staging integration, CodeQL, Secretary
staging, Deterministic AI Evaluation, Dependency security, and Workflow lint.
One approval, latest-push approval, stale-review dismissal and admin enforcement
are enabled; force-push and branch deletion are disabled. Active ruleset
#26782191 has an approval rule but no status rules. A current runtime PR must
still demonstrate the expected status behavior and failing-check merge block.
Required GitHub checks are not a substitute for product acceptance.

The Neon production branch is currently unprotected. Enabling protection failed
because the active free plan allows no protected branches. No scheduled backup
exists; Neon’s documented automatic snapshot schedules require a paid plan. A
manual snapshot and isolated restore were completed on November 20; both the
snapshot and the unprotected recovery branch expire after seven days. See the
[drill record](recovery-drill-2026-11-20.md). No subscription change was made.

## Configuration names (values omitted)

- Backend runtime: `DATABASE_URL`, `APP_ENV`, `AI_MODE`,
  `AI_ANALYSIS_ENABLED`, `REPORT_AUTH_MODE`,
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
