# PhishLens environment map — 2026-11-23

Evidence cutoff: **2026-11-23 13:14 UTC**. Public staging/production GET probes were read-only; candidate `48ead208487408b04f3eed9f8643631454d6cc83` ran through GitHub CI and the protected staging deploy attempt. The staging deploy failed `update_failed`; no production deployment or paid AI call occurred. The workflow’s synthetic CRUD phase was skipped because deploy failed.

## Current repository and candidate

- GitHub `main`: `0338ad163a4892987a6a682aed29b95c22c322da`.
- PR #282 candidate: `48ead208487408b04f3eed9f8643631454d6cc83`; open, merge blocked, `REVIEW_REQUIRED`.
- Exact-head checks on `48ead20` completed: Backend, Extension, Migration source preflight, disposable Staging integration, Workflow lint, Dependency security/Gitleaks, Deterministic AI Evaluation, CodeQL, and Secretary report/label passed. Hosted staging preflight passed. The user-approved Render deployment failed `update_failed`; `Secretary staging` then failed because the CI workflow did not succeed. PR review remains required.
- Prior PR #282 head `89227b35f050e17d2b2fa2cc004f438462861290` passed ordinary
  checks but Hosted staging failed with Render status `update_failed`
  ([run 45167906325](https://github.com/kendshhh/PhishLens/actions/runs/45167906325));
  Secretary staging then failed because staging was not deployed
  ([run 45168581284](https://github.com/kendshhh/PhishLens/actions/runs/45168581284)).
  A connected-account diagnostics tool was unavailable, and the workflow log
  exposed no Render build/start root cause.

## Environment map

| Environment | Known setup | Fresh evidence | Open verification |
|---|---|---|---|
| Local development | `.env` ignored; `.env.example` provides local/mock defaults. | Local Python suites on candidate `48ead20`: 597 passed, 45 skipped, 199 subtests; focused AI gate: 113 passed; no paid provider calls. | Skipped PostgreSQL tests need hosted CI; teammate setup/key hygiene not independently accepted. |
| CI | Disposable PostgreSQL test DB, synthetic credentials, mocked AI. | Exact-head Backend, Extension, Migration source preflight, disposable staging integration, Workflow lint, Dependency security/Gitleaks, AI eval and CodeQL all passed. Hosted deployment did not. | The shared hosted staging deployment failed `update_failed`; exact candidate application acceptance is not established. |
| Hosted staging | Render `phishlens-staging`, `https://phishlens-staging.onrender.com`; separate Neon staging branch documented as `pr-58-staging`. | Preflight validated exact PR head, migration head, staging service and private target. Render deploy `dep-dc23il5g1s2s73er61ig` for `48ead20` failed `update_failed`. Afterward `/version`, `/health`, `/ready`, `/model-info` returned 200 for old SHA `05bd559744ab96357b74a96404a4d4c8a6d070eb`; provider remains TF-IDF. | Candidate did not deploy; authenticated CRUD, migration application, and candidate product flow were skipped. Render build/start/deploy event logs are needed to identify root cause. |
| Production | Render `phishlens-api`, `https://phishlens-api-ocvt.onrender.com`; production Neon branch previously recorded separately. | Fresh read-only probe at 13:12 UTC timed out/failed for `/version`, `/health`, `/ready`, and `/model-info`. Last successful identity was SHA `811980c2cbf70d9957146bf329627f0826a018f1`; last successful model-info at 12:24 UTC said `analysis_enabled=false`, `provider_mode=disabled`. | Service is currently unreachable from this probe; current release identity, live product behavior, auto-deploy merge-to-live, provider settings and Render-to-Neon role mapping are unverified. |
| GitHub controls | Main protection has eight required contexts, one approval, latest-push review, stale-review dismissal, admin enforcement, and force-push/deletion blocked. | PR #282 exact head `48ead20`: all normal checks pass; `Hosted staging` and `Secretary staging` fail due deployment failure; review required. Push reports 15 open Dependabot alerts. | Resolve Render staging update failure, reconcile alert state and obtain reviewer approval. |

## Secret handling and separation

The branch adds a checksum-pinned Gitleaks scan inside the existing required
`Dependency security` job and uses 13 exact line fingerprints for reviewed
false positives. The exact candidate job passed in run `45178590663`. A prior local
scan found zero unallowlisted findings and detected a generated synthetic canary.
Main still does not contain this unmerged gate until PR #282 is reviewed and merged.

No hosted secret values or topology settings were changed. The exact-head staging preflight validated the configured service and private database target; no database topology change was made. Private service-to-database target/role mappings,
least-privilege scopes, protected environment reviewers, separate AI keys and
per-environment spend caps still require an authorized owner verification.
