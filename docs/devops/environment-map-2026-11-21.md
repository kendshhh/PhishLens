# Environment and Secret Map — 2026-11-21

This map records scopes and verification status without secret values. The
current refresh did not read hosted secret values. A live deployment or
successful readiness check does not prove a correct database mapping, Auth
mode, provider configuration or access policy.
Render service/deploy metadata was refreshed read-only at 07:31 UTC on November
21. Production was Live on SHA `811980c2cbf70d9957146bf329627f0826a018f1`;
staging had advanced to SHA `ba0b6c5475eb6a8f99c509c40384020d292e17e6`.
GitHub main later advanced through PR #263 to
`06f89d7a0b5b9dec316dfa11f2846767a32086c5`; neither service was verified on
that SHA in this refresh.

## Environment map

| Environment | Current service identity | Runtime purpose and non-secret state | Secret/data boundary and open verification |
|---|---|---|---|
| Local development | Developer machine; .env is git-ignored | .env.example defaults to development, mock AI and demo Auth. Local DATABASE_URL must target a local or dedicated development database. | Keep hosted credentials out of local files. Repository controls were reviewed; no local secret values were read. |
| CI | GitHub Actions disposable PostgreSQL and synthetic credentials | CI uses mock AI and runs migrations against the disposable test database. | CI credentials are not production credentials. Workflow source is checked in. |
| Hosted staging | Render `phishlens-staging`; latest observed live deploy at 07:31 UTC `dep-dc0im3h7lnhs738pncng` on SHA `ba0b6c5475eb6a8f99c509c40384020d292e17e6`; URL `https://phishlens-staging.onrender.com`. The Nov 20 deploy `dep-dc07s1cipgvc73dh0150` on `811980c` is historical. | Render metadata reports branch `main`, auto-deploy `no`, trigger `off`. `/version`, `/health`, `/ready`, `/model-info` returned HTTP 200 at the refresh. GET-only smokes at 08:15 and about 08:35 passed health/readiness plus anonymous history `401 Bearer`; neither verified PR SHA or authenticated CRUD. | Neon `pr-58-staging` migration `0004_neon_auth_subject` and grants were inspected read-only, but Render's runtime connection target/role is unverified. No authenticated CRUD/write acceptance. |
| Production | Render `phishlens-api`; latest observed live deploy at 07:31 UTC `dep-dc07rs67bikc73fjgjq0` on SHA `811980c2cbf70d9957146bf329627f0826a018f1`; URL `https://phishlens-api-ocvt.onrender.com`. | Read-only `/version`, `/health`, `/ready`, `/model-info` returned HTTP 200. The November 20 observer run 44812619162 passed exact-SHA/health/readiness for this SHA; it did not test model, Auth, CRUD or extension behavior. | Render metadata at 07:31 reports auto-deploy `no` and trigger `off`; a November 20 record says auto-deploy `checksPass`, and the latest deploy record says `new_commit`. Preserve this unresolved setting/event discrepancy. Analysis was verified disabled Nov 20 but not reread at 07:31. Auth mode and Neon mapping are unverified. |
| PR #268 CI candidate | Code/test source `83a0df1af1d64048b3b5fa3158f6509e83d71555`; latest recorded fully checked docs-only revision `631b0ef21849e8abe877bb16b4676047f2aca86a`. | CI run 44888140094, workflow lint 44888140104, dependency security 44888140135, deterministic evaluation 44888140114 and CodeQL 136797921015 passed for that source/head. | Hosted staging/preflight were skipped; PR check `Secretary staging` failed because the protected run label/exact-head verification were absent (44888369939). No Render deploy or hosted Auth CRUD. Later docs-only branch merges require their own live checks. |
| Secretary staging controller | Trusted default-branch controller; PR #257 requires explicit Neon Auth mode and fails closed while Auth acceptance is pending; PR #262 corrects the backend-only staging skip. | At PR #268 check run 44888369939, the controller assessment passed and preview job was skipped; GitHub reports the `Secretary staging` context failed with the missing `needs-hosted-staging`/exact-head verification message. | Protected staging secret values remain private. This did not deploy or write to staging. CRUD still lacks an authenticated Neon Auth session. |
| Production observer | Scheduled GitHub Production drift workflow | Current run checks source SHA, /health and /ready only; it does not deploy, roll back or test model/provider/Auth/extension behavior. | Workflow secret scopes and alert routing were not reread. No external alert delivery/acknowledgement is evidenced. |

## GitHub enforcement snapshot

The active ruleset #27733591 applies to main and codex/*-live-* and visibly
requires four contexts: Backend checks, Extension checks, Staging integration
and Secretary staging. Strict status checking is disabled. The active approval
ruleset #26782191 requires one approval, stale-review dismissal and thread
resolution; latest-push approval is disabled. The classic branch-protection API
returned 403 on Nov 21, so the prior Nov 20 observation of eight required
contexts and classic settings is historical, not fresh verification. The
effective combined protection contract remains unresolved.

## Neon backup state

The Nov 20 read-only check found the production branch unprotected, no scheduled
snapshot and six-hour history retention. The manual snapshot and isolated
restore branch from the Nov 20 drill expire Nov 27. The free plan rejected
production branch protection and does not offer scheduled snapshots. That
restore matched schema and aggregate counts but did not measure end-to-end RTO
or RPO.

## Configuration verification before GO

Verify privately that production and staging map to distinct intended Neon
branches and least-privilege roles; confirm the effective Auth and AI settings;
review GitHub environment scopes and required reviewers; and record setting
names, scope, reviewer/owner, verification time and pass/fail only. Never paste
secret values into this repository. These items remain open.
