# Environment and Secret Map — 2026-11-21

This map records scopes and verification status without secret values. The
current refresh did not read hosted secret values. A live deployment or
successful readiness check does not prove a correct database mapping, Auth
mode, provider configuration or access policy.

## Environment map

| Environment | Current service identity | Runtime purpose and non-secret state | Secret/data boundary and open verification |
|---|---|---|---|
| Local development | Developer machine; .env is git-ignored | .env.example defaults to development, mock AI and demo Auth. Local DATABASE_URL must target a local or dedicated development database. | Keep hosted credentials out of local files. Repository controls were reviewed; no local secret values were read. |
| CI | GitHub Actions disposable PostgreSQL and synthetic credentials | CI uses mock AI and runs migrations against the disposable test database. | CI credentials are not production credentials. Workflow source is checked in. |
| Hosted staging | Render phishlens-staging; live deploy dep-dc07s1cipgvc73dh0150 on SHA 811980c2cbf70d9957146bf329627f0826a018f1; manual deployment; auto-deploy off | Same source SHA as current production. This deployment identity alone is not Auth or CRUD acceptance. | Current Auth mode and Render-to-Neon branch/database/role mapping are not verified. The Neon pr-58-staging grants were inspected on Nov 20; that did not prove this service connects to that branch. |
| Production | Render phishlens-api; live deploy dep-dc07rs67bikc73fjgjq0 on SHA 811980c2cbf70d9957146bf329627f0826a018f1; auto-deploy checksPass from main | Scheduled Production drift run 44812619162 passed exact SHA, health and readiness. The run does not query model-info or exercise product behavior. Production auto-deploy can publish main while issue #153 remains NO-GO. | AI_ANALYSIS_ENABLED=false was verified in Render on Nov 20, but not reread in this refresh. Current effective model state, Auth mode, secret access controls and exact Neon mapping are unverified. Do not record secret values. |
| Secretary staging controller | Trusted default-branch controller; previews currently disabled by repository configuration | PR #257 requires explicit Neon Auth mode and reports Auth-pending acceptance as a failing required status; PR #262 avoids requiring hosted staging for backend-only changes. | Protected staging secret values remain private. A current runtime PR has not demonstrated the full label, skip and failure behavior. |
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