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

## PR #268 check snapshot — 2026-11-21 13:45 UTC

At 13:45 UTC, PR #268 head `9036132d8ff70cbf9ceae97175a7f59ba0b1e61d`
targeted `main` at `31e86c78523cbdcfb6da83f99d331c86409bf0fa`. PR #265 had
merged; GitHub reported the PR mergeable, with collaborator re-review pending.
Backend, Extension, Staging integration, migration preflight, workflow lint,
dependency security/graph review, deterministic evaluation, CodeQL and the
Secretary report passed on this exact head. Hosted staging preflight passed;
Hosted staging is waiting at the protected `staging` environment and has not
started. The source pin now targets `phishlens-staging`'s root endpoint. Exact-
head hosted verification remains pending, and this documentation refresh
triggers a new exact-head run. Service observations and older PR/CI rows below
remain dated snapshots.

## Environment map — dated service and CI snapshots

| Environment | Service and data target | Runtime/configuration evidence | Status and open controls |
|---|---|---|---|
| Local development | Developer machine; `.env` is git-ignored. | `.env.example` supplies development/mock/demo defaults. | Repository configuration only. No local secret values were read. |
| CI / current main | Disposable PostgreSQL test database; synthetic credentials and mock AI. | Main is `95975cd47dceeac74ea36054610956f0a1db1fa9`, which merged PR #265. Its CI [44889931821](https://github.com/kendshhh/PhishLens/actions/runs/44889931821) and CodeQL [44889931096](https://github.com/kendshhh/PhishLens/actions/runs/44889931096) passed; workflow lint [44889931690](https://github.com/kendshhh/PhishLens/actions/runs/44889931690) and dependency security [44889931677](https://github.com/kendshhh/PhishLens/actions/runs/44889931677) passed. PR #268 code/test commit `83a0df1af1d64048b3b5fa3158f6509e83d71555` contains bounded retries, diagnostics, local server monitoring/log retention and fail-closed hosted deployment gates. The PR branch includes main code through `14874d3` and shared docs through `ca29235`. | Main's complete current check set passed for the merged snapshot. The previous main CI failure on `06f89d7` is historical. See the current PR-specific row for separate review status; CI credentials are not hosted credentials. |
| PR #268 check snapshot | On head `9036132d8ff70cbf9ceae97175a7f59ba0b1e61d` at 13:45 UTC, Backend, Extension, Staging integration, migration preflight, workflow lint, dependency review/security, deterministic evaluation, CodeQL and Secretary report passed. Hosted preflight passed; Hosted staging is waiting at the protected `staging` environment. | The preceding head `943bbdb` failed before migrations on a stale endpoint pin. Head `9036132` updates it to the separate `phishlens-staging` root; no hosted deployment has started on this head. This documentation refresh requires a fresh exact-head run. | Collaborator re-review remains pending. No hosted smoke, CRUD, identity verification or package result is claimed. |
| Hosted staging | Render service `phishlens-staging`, ID `srv-db92irlg1s2s739404i0`, URL `https://phishlens-staging.onrender.com`; latest observed live deployment `dep-dc0pmu17lnhs739d14b0`, merge SHA `683eee44f9089b79b4d7b38163f7ab68bce89656` at 13:25 UTC. Render metadata at 13:25 reports branch `main`, auto-deploy `no`, trigger `off`. | Render logs show a different merge revision completed migrations and started the API. This was not PR #268's exact merge SHA. PR #268's previous deploy failed before migrations when its startup guard rejected the current staging endpoint. | Current source pin targets Neon project `phishlens-staging`, branch `staging-root`, endpoint `ep-long-fire-b31uvz7u`. This audit did not inspect private connection values or independently verify the current Render-to-Neon mapping. No PR #268 authenticated CRUD acceptance is established. |
| Production | Render service `phishlens-api`, ID `srv-db7eap25b2lc73fkelpg`, URL `https://phishlens-api-ocvt.onrender.com`; latest live deploy `dep-dc07rs67bikc73fjgjq0`, SHA `811980c2cbf70d9957146bf329627f0826a018f1`. Render metadata rechecked at 07:31 UTC reports branch `main`, auto-deploy `no`, trigger `off`. | Earlier November 21 read-only `/version`, `/health`, `/ready`, `/model-info` returned 200. Model info: `provider_mode=disabled`, `analysis_enabled=false`, required-provider support false, TF-IDF reports false. | Exact Neon branch/role mapping, runtime Auth/provider values and secret access control are not verified. No inference or saved-report write was performed. The disabled state is not product acceptance. |
| Render deployment controls | Both services are configured for branch `main`; metadata at 07:31 UTC reports auto-deploy `no` and trigger `off`. | Production latest live deploy event reports trigger `new_commit`; staging latest live deploy trigger is `api`. | Production setting/event mismatch remains unresolved. Verify Dashboard controls and deployment audit trail before relying on auto-deploy semantics. Do not infer configuration from a single deploy event. |
| GitHub staging controller | Main remains `31e86c7`; source commit `9036132` includes bounded retry diagnostics, local server monitoring, retained logs, fail-closed hosted deployment gates, and the endpoint pin fix. | Exact-head run [44909945177](https://github.com/kendshhh/PhishLens/actions/runs/44909945177) passed Backend, Extension, migration preflight, Staging integration, Hosted preflight and the Secretary report; lint, dependency, evaluation and CodeQL checks also passed. | Hosted staging is waiting at the protected environment and has not started. The prior `Secretary staging` failure is tied to the previous revision. No current-head hosted CRUD or exact-SHA package is claimed. |
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

### PR #268 follow-up — 2026-11-21 11:42 UTC

The next exact-head check on `e9451cc20928fefa7c0a6ded4803cebbad24ef42` passed Backend, Extension, migration preflight, Staging integration, workflow lint, dependency security/graph review, deterministic evaluation, and the Secretary report. Hosted staging preflight and Hosted staging were skipped. Required `Secretary staging` remains failed because the `needs-hosted-staging` label and exact-head hosted verification are absent. No current PR CodeQL result, Render deployment or authenticated CRUD was observed. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md) for run links. The release remains **NO-GO**; the descriptive DevOps evidence score remains 41/100.

### PR #268 retarget follow-up — 2026-11-21 11:57 UTC

PR #268 is now based on `main`; review branch head `77c0ed00e607c5580cedffadd031fe40ad71771b` includes the current `main` history. GitHub reports the PR open and mergeable, while the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. Exact-head CI passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security/graph review, deterministic evaluation, DevOps Secretary report and CodeQL. Hosted preflight/deployment were skipped; required `Secretary staging` remains failed because the hosted request label and exact-head hosted verification are absent. No Render deployment or authenticated hosted CRUD occurred. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md). Release remains **NO-GO** and the 41/100 descriptive evidence score is unchanged.

### PR #268 exact-head snapshot — 2026-11-21 12:02 UTC

Retargeted PR #268 head `1fa2e7827cfe84de425afcc7885743bd55b2a382` passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security and graph review, deterministic evaluation, DevOps Secretary report, and all three CodeQL analyses. [CI run 44901642617](https://github.com/kendshhh/PhishLens/actions/runs/44901642617) completed at 12:02 UTC. Hosted staging preflight and Hosted staging were skipped. The required `Secretary staging` status failed because the `needs-hosted-staging` label and exact-head hosted verification were absent ([assessment 44901931269](https://github.com/kendshhh/PhishLens/actions/runs/44901931269)); no Render deployment or authenticated hosted CRUD occurred. GitHub reports the PR open and mergeable on `main`; the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. The release remains **NO-GO**, and 41/100 is a descriptive evidence-progress score only. This documentation-only evidence update requires fresh exact-head CI before merge. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).

### PR #268 main-sync snapshot — 2026-11-21 12:14 UTC

PR #268 now includes current `main` through `31e86c7` in merge head `aee49fe5a11da37ed441464c80ad9a09e0b9dda8`. Exact-head CI run [44902645800](https://github.com/kendshhh/PhishLens/actions/runs/44902645800) passed Backend, Extension, Staging integration and migration preflight. Workflow lint [44902645811](https://github.com/kendshhh/PhishLens/actions/runs/44902645811), dependency security/graph [44902645851](https://github.com/kendshhh/PhishLens/actions/runs/44902645851), deterministic evaluation [44902645832](https://github.com/kendshhh/PhishLens/actions/runs/44902645832), and CodeQL [44902643383](https://github.com/kendshhh/PhishLens/actions/runs/44902643383) passed. The exact-head DevOps Secretary report was cancelled during the branch sync ([44902644757](https://github.com/kendshhh/PhishLens/actions/runs/44902644757)); the Secretary preview assessment reports required `Secretary staging` failure because the `needs-hosted-staging` label and exact-head hosted verification are absent ([44902874550](https://github.com/kendshhh/PhishLens/actions/runs/44902874550)). Hosted preflight/deployment were skipped; no Render deploy or authenticated CRUD occurred. GitHub shows PR #268 open, mergeable on `main`, with review decision `CHANGES_REQUESTED`. Release remains **NO-GO**; 41/100 is descriptive evidence progress, not completion. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).
