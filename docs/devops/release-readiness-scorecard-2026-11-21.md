# DevOps release-readiness scorecard — 2026-11-21

**Current release: NO-GO. Estimated DevOps evidence progress: 41/100.**

This estimate uses the 16 criteria below as equally weighted checklist items:
PASS = 1, PARTIAL = 0.5, FAIL or NOT VERIFIED = 0. The current evidence has
13 PARTIAL, 3 FAIL, 0 PASS: 13 × 0.5 ÷ 16 = 40.625%, rounded to 41%.
This is a transparent progress estimate, not the official CSP221A score. The
PDF does not provide a complete 100-point weighting scheme for these criteria.
It does not mean the product is 41% operational or release-ready. This fixed
16-item indicator is separate from the seven-area release gate: 0 of 7 areas
meet their full pass definition, and no weighted seven-area score or overall
project-completion percentage is calculated because those weights and rules are
not approved.

Evidence includes the latest read-only checks retrieved on November 21, 2026.
GitHub main is `06f89d7a0b5b9dec316dfa11f2846767a32086c5` (PR #263). Production
remains on deploy `dep-dc07rs67bikc73fjgjq0` / SHA
`811980c2cbf70d9957146bf329627f0826a018f1`; staging remains on deploy
`dep-dc0im3h7lnhs738pncng` / SHA
`ba0b6c5475eb6a8f99c509c40384020d292e17e6`. Neither deployment is evidence of
an accepted release candidate. Scope and checklist links are in
the [release record](release-record-2026-11-21.md), [environment map](environment-map-2026-11-21.md),
[demo-day matrix](demo-day-readiness-2026-11-21.md), [metrics](metrics.md),
[smoke runbook](production-deploy-smoke.md), and
[recovery drill](recovery-drill-2026-11-20.md).

At 09:31 UTC, PR #268 head `7dbebfd060298a80e99a38a52663901e776935cb` had
Backend, Extension, migration source preflight, Staging integration, workflow
lint, dependency security and deterministic evaluation passed. Dependency
graph review failed because GitHub reports the repository Dependency graph is
disabled; CodeQL failed all three language jobs on Actions installation API
rate limits. Hosted staging was skipped. These checks do not resolve the live
authenticated acceptance gaps or change any scorecard criterion to PASS; see
the [release record](release-record-2026-11-21.md).

| PDF reference | Criterion | Status | Current evidence and gap |
|---|---|---|---|
| p. 3 and p. 49 | One defined real-data product path with working CRUD, backend-owned AI/data and user-facing error states | **FAIL** | Issue #153 states Chrome extension + Render API + Neon and retires the Vercel experiment, but authenticated Auth/CRUD and an accepted extension/backend/model journey are not proven. The last verified production analysis setting was disabled on November 20, but it was not reread in this refresh; no approved production model/provider is evidenced. |
| pp. 33, 42 | Separate environments and protected secrets | **PARTIAL** | Local, CI, staging and production scopes are documented; no secret values were read. Current Render-to-Neon branch/role mapping, live Auth/provider settings and complete secret access controls are not verified. |
| pp. 38–41 | PR checks, required gates and branch protection | **PARTIAL** | The visible CI ruleset requires Backend checks, Extension checks, Staging integration and Secretary staging, with strict checking off; the approval ruleset requires one approval but not latest-push approval. Classic protection returned 403; the earlier eight-context read is stale. Main CI for `06f89d7` (run 44885148600) failed at packaged-extension Chromium browser acceptance while Backend passed. No current failure-blocking PR demonstration. |
| pp. 39–40, p. 127 | Traceable artifact and same candidate through staging and production | **PARTIAL** | The PhishLens-Extension and browser-acceptance artifacts are tied to SHA 811980c, which is still the production SHA; staging now serves `ba0b6c5`, and main has advanced to `06f89d7`. No accepted package/backend/model/Auth manifest or same-candidate production promotion exists. |
| p. 43 | Expand/contract migrations and application rollback compatibility | **PARTIAL** | Disposable PostgreSQL evidence covers migrations through schema 0004 and 11 saved-report CRUD tests from an older backend revision. Current production predecessor/config/schema compatibility is untested. |
| pp. 44–46 | Current metrics and comparable optimization | **PARTIAL** | Four successful main-push CI runs through SHA 811980c had median 1.30 min, nearest-rank p90 1.90 min and range 1.10–1.90 min; this is a dated sample, not the current check result. Main later advanced to `06f89d7`, whose CI failed in browser acceptance. Twenty production deploys through Nov 20 had median 74.15 sec and p90 93.14 sec. No comparable before/after end-to-end or user-flow result exists. |
| p. 47, pp. 91–104 | AI evaluation in CI with an enforced release threshold | **PARTIAL** | Deterministic AI evaluation is recorded on the earlier 811980c source; the current main check set for `06f89d7` does not establish an approved numeric model-quality threshold. The visible four-context ruleset does not include the AI evaluation context. |
| pp. 92–104 | Representative model quality and release decision | **FAIL** | The 40-case synthetic result remains 65% accuracy, 18.75% phishing recall (3/16), and 6.25% legitimate false positives (1/16), with all eight spam cases labelled legitimate. Frozen English source-pair TF-IDF v12a achieved 190/200 phishing recall and 1/999 legitimate false positives but is advisory only; a 12-case synthetic diagnostic detected 1/12. No contemporary broad holdout or human explanation review establishes release quality. |
| p. 115 | Input, rate, quota, output and spend controls | **PARTIAL** | Input/output bounds, per-request cost cap and evaluation-run limits exist. A shared durable production daily/monthly budget, per-user quota/rate control and cross-instance enforcement are not evidenced. |
| pp. 106, 118–123 | Observability, SLOs and tested alert response | **PARTIAL** | Request IDs and structured allowlisted metadata exist. Scheduled drift checks source SHA, health and readiness. No approved extension-journey SLO, tested alert delivery/acknowledgement or current hosted-log evidence. |
| pp. 127–130 | Approved versioned release, rollout control, kill switch and changelog | **FAIL** | Issue #153 remains NO-GO. Render metadata reports auto-deploy off, while the latest production deploy record says `new_commit`; this discrepancy is unresolved. No GitHub Release or v1.0.0 tag exists; a disabled-aware smoke is available but has not been shown as automatic post-deploy release acceptance. |
| p. 131 | Current-release application rollback rehearsal | **PARTIAL** | Runbook and an older staging drill exist. No exact compatible production rollback SHA/config/schema combination has been identified and rehearsed. |
| p. 132 | Exact-SHA post-deploy smoke and monitoring | **PARTIAL** | Main supports a disabled-aware zero-inference manual smoke. The scheduled drift check is limited to SHA/health/readiness; no exact-SHA feature smoke runs automatically after each production deploy. A GET-only staging smoke at about 08:35 UTC validated health, readiness and the anonymous `401 Bearer` boundary, not deployed PR identity or authenticated CRUD. |
| pp. 48, 133 | Incident detection, escalation and recovery | **PARTIAL** | Incident/runbook procedures and a primary release owner are documented. Backup responder, alert recipient/channel, tested delivery and measured response are not evidenced. |
| p. 135 | Backups, restore and measured RTO/RPO | **PARTIAL** | Nov 20 manual snapshot restored to an isolated Neon branch; schema and aggregate counts matched. Free plan blocks production branch protection and scheduled snapshots; full-service RTO/RPO remain unmeasured. |
| pp. 136, 140 | Current handover and readiness evidence | **PARTIAL** | Current main/deploy identities, workflow gates and open checklist are documented. Team explanation and full product/model/auth/recovery evidence remain incomplete; the ten-question matrix is not all PASS. |

## Release stop conditions

Keep NO-GO until authenticated staging CRUD/isolation passes on the exact
extension/backend pair; a reviewed model cohort meets approved thresholds;
current GitHub required-status and review behavior is demonstrated; production
promotion and exact-SHA smoke are gated; current application rollback and
isolated database recovery are rehearsed; and alert ownership, RTO/RPO and
handover evidence are complete. Do not count a successful process-health check
or a skipped job as product acceptance.
