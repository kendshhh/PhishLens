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

Evidence includes the latest checks retrieved on November 21, 2026. GitHub main
is `95975cd47dceeac74ea36054610956f0a1db1fa9` after PR #265 merged. Production
remains on deploy `dep-dc07rs67bikc73fjgjq0` / SHA
`811980c2cbf70d9957146bf329627f0826a018f1`; staging remains on deploy
`dep-dc0im3h7lnhs738pncng` / SHA
`ba0b6c5475eb6a8f99c509c40384020d292e17e6`. Neither deployment is evidence of
an accepted release candidate. Scope and checklist links are in
the [release record](release-record-2026-11-21.md), [environment map](environment-map-2026-11-21.md),
[demo-day matrix](demo-day-readiness-2026-11-21.md), [metrics](metrics.md),
[smoke runbook](production-deploy-smoke.md), and
[recovery drill](recovery-drill-2026-11-20.md).

At 09:42 UTC, PR #268 head `def5e9b3d925e94a9aa664a24f90c73b960c7f99` had
Backend, Extension, migration source preflight, Staging integration, workflow
lint, dependency security, Dependency graph review and deterministic evaluation
passed. Hosted staging was skipped, and no CodeQL check appeared on this head.
The merged main snapshot passed CI and CodeQL. The repository Dependency graph
is now enabled, but 15 existing Dependabot alerts (12 high, 3 moderate) remain
open. These results do not resolve the live authenticated acceptance gaps or
change any scorecard criterion to PASS; see the
[release record](release-record-2026-11-21.md).

At 10:14 UTC, PR #268 head `2e26327254c71b6cb7d655181cffb21e8dd1ee9b` passed
Backend, Extension, migration preflight, Staging integration, hosted preflight,
workflow lint, dependency security, Dependency graph review and deterministic
evaluation. Hosted staging job 136807616481 ended with conclusion success, but
its final freshness guard marked the request superseded after the label was
removed; deployment, smoke, CRUD and artifact steps were skipped. Its summary
classifies the run as blocked, not hosted acceptance. The separate required
`Secretary staging` status failed in [run 44892082807](https://github.com/kendshhh/PhishLens/actions/runs/44892082807).
No current PR CodeQL result appeared. This was an empty CI-trigger commit, and
the pending documentation commit requires a fresh exact-head check. PR #268 remains based
on the merged PR #265 branch and must be retargeted to `main`.

At 11:08 UTC, PR #268 head `a151585ff92d55f21e0364e9838287a9cf04a68d`
passed Backend, migration source preflight, workflow lint, dependency checks,
deterministic evaluation and the Secretary report. `Extension checks` failed
the packaged Saved reports view keyboard-focus assertion in
`scripts/browser_acceptance.mjs:700` ([CI
44897548076](https://github.com/kendshhh/PhishLens/actions/runs/44897548076)).
Staging integration and hosted staging/preflight were skipped. Required
`Secretary staging` failed in [run 44897660167](https://github.com/kendshhh/PhishLens/actions/runs/44897660167).
No current PR CodeQL, hosted deployment or authenticated CRUD evidence exists.
The 10:14 check snapshot above is historical for the previous head. These
latest statuses do not close a scorecard criterion or raise the checklist
estimate; the release remains NO-GO.

The previous completed snapshot, at 11:21 UTC on `dffdc4c29338142f458350b51c8ce69e0f36e988`,
passed Backend, Extension, migration preflight, Staging integration, workflow
lint, dependency review/security, deterministic evaluation and the Secretary
report. Hosted staging/preflight were skipped, and required `Secretary staging`
failed ([CI 44898467208](https://github.com/kendshhh/PhishLens/actions/runs/44898467208),
[Secretary staging 44898698685](https://github.com/kendshhh/PhishLens/actions/runs/44898698685)).
No hosted deployment, authenticated CRUD or current PR CodeQL result exists.
The docs-only sync after this snapshot needs its own checks.

The latest completed snapshot at 11:31 UTC, on `f79098cc075784563d2022cbca87d7abe8f0a635`,
also passed Backend, Extension, migration preflight, Staging integration,
workflow lint, dependency review/security, deterministic evaluation and the
Secretary report. Hosted staging/preflight were skipped; required `Secretary
staging` failed in [run 44899423134](https://github.com/kendshhh/PhishLens/actions/runs/44899423134).
No hosted deployment, authenticated CRUD or current PR CodeQL result exists.
The current docs-only sync needs its own exact-head checks.

| PDF reference | Criterion | Status | Current evidence and gap |
|---|---|---|---|
| p. 3 and p. 49 | One defined real-data product path with working CRUD, backend-owned AI/data and user-facing error states | **FAIL** | Issue #153 states Chrome extension + Render API + Neon and retires the Vercel experiment, but authenticated Auth/CRUD and an accepted extension/backend/model journey are not proven. The last verified production analysis setting was disabled on November 20, but it was not reread in this refresh; no approved production model/provider is evidenced. |
| pp. 33, 42 | Separate environments and protected secrets | **PARTIAL** | Local, CI, staging and production scopes are documented; no secret values were read. GitHub Dependency graph is enabled and the current PR dependency-review check passes, but 15 Dependabot alerts (12 high, 3 moderate) remain open. Current Render-to-Neon branch/role mapping, live Auth/provider settings and complete secret access controls are not verified. |
| pp. 38–41 | PR checks, required gates and branch protection | **PARTIAL** | Main `95975cd` CI and CodeQL passed. Latest completed PR #268 snapshot `f79098c` passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency review/security and deterministic evaluation. Hosted staging/preflight were skipped; required `Secretary staging` failed in run 44899423134. No current PR CodeQL, hosted acceptance or authenticated CRUD evidence exists. The keyboard-focus assertion failed on `a151585` but passed on docs-only follow-ups `dffdc4c` and `f79098c`; root cause remains unknown. Earlier `2e26327` hosted staging was blocked by its freshness guard after the request label was removed. The CI ruleset requires Backend, Extension, Staging integration and Secretary staging, with strict checking off; the approval ruleset requires one approval but not latest-push approval. Classic protection returned 403; no current failure-blocking PR demonstration. PR #268 still targets the merged #265 branch. |
| pp. 39–40, p. 127 | Traceable artifact and same candidate through staging and production | **PARTIAL** | The PhishLens-Extension and browser-acceptance artifacts are tied to SHA 811980c, which is still the production SHA; staging serves `ba0b6c5`, and main is `95975cd`. No accepted package/backend/model/Auth manifest or same-candidate production promotion exists. |
| p. 43 | Expand/contract migrations and application rollback compatibility | **PARTIAL** | Disposable PostgreSQL evidence covers migrations through schema 0004 and 11 saved-report CRUD tests from an older backend revision. Current production predecessor/config/schema compatibility is untested. |
| pp. 44–46 | Current metrics and comparable optimization | **PARTIAL** | Four successful main-push CI runs through SHA 811980c had median 1.30 min, nearest-rank p90 1.90 min and range 1.10–1.90 min; this is a dated sample. Main `95975cd` CI passes but is not a comparable performance sample. Twenty production deploys through Nov 20 had median 74.15 sec and p90 93.14 sec. No comparable before/after end-to-end or user-flow result exists. |
| p. 47, pp. 91–104 | AI evaluation in CI with an enforced release threshold | **PARTIAL** | Deterministic AI evaluation passed on merged main `95975cd` and latest completed PR #268 head `f79098c` (also on `dffdc4c`, `a151585` and `2e26327`), but no approved numeric model-quality threshold exists. The visible four-context ruleset does not include the AI evaluation context. |
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

### PR #268 follow-up — 2026-11-21 11:42 UTC

The next exact-head check on `e9451cc20928fefa7c0a6ded4803cebbad24ef42` passed Backend, Extension, migration preflight, Staging integration, workflow lint, dependency security/graph review, deterministic evaluation, and the Secretary report. Hosted staging preflight and Hosted staging were skipped. Required `Secretary staging` remains failed because the `needs-hosted-staging` label and exact-head hosted verification are absent. No current PR CodeQL result, Render deployment or authenticated CRUD was observed. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md) for run links. The release remains **NO-GO**; the descriptive DevOps evidence score remains 41/100.

### PR #268 retarget follow-up — 2026-11-21 11:57 UTC

PR #268 is now based on `main`; review branch head `77c0ed00e607c5580cedffadd031fe40ad71771b` includes the current `main` history. GitHub reports the PR open and mergeable, while the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. Exact-head CI passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security/graph review, deterministic evaluation, DevOps Secretary report and CodeQL. Hosted preflight/deployment were skipped; required `Secretary staging` remains failed because the hosted request label and exact-head hosted verification are absent. No Render deployment or authenticated hosted CRUD occurred. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md). Release remains **NO-GO** and the 41/100 descriptive evidence score is unchanged.

### PR #268 exact-head snapshot — 2026-11-21 12:02 UTC

Retargeted PR #268 head `1fa2e7827cfe84de425afcc7885743bd55b2a382` passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security and graph review, deterministic evaluation, DevOps Secretary report, and all three CodeQL analyses. [CI run 44901642617](https://github.com/kendshhh/PhishLens/actions/runs/44901642617) completed at 12:02 UTC. Hosted staging preflight and Hosted staging were skipped. The required `Secretary staging` status failed because the `needs-hosted-staging` label and exact-head hosted verification were absent ([assessment 44901931269](https://github.com/kendshhh/PhishLens/actions/runs/44901931269)); no Render deployment or authenticated hosted CRUD occurred. GitHub reports the PR open and mergeable on `main`; the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. The release remains **NO-GO**, and 41/100 is a descriptive evidence-progress score only. This documentation-only evidence update requires fresh exact-head CI before merge. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).

### PR #268 main-sync snapshot — 2026-11-21 12:14 UTC

PR #268 now includes current `main` through `31e86c7` in merge head `aee49fe5a11da37ed441464c80ad9a09e0b9dda8`. Exact-head CI run [44902645800](https://github.com/kendshhh/PhishLens/actions/runs/44902645800) passed Backend, Extension, Staging integration and migration preflight. Workflow lint [44902645811](https://github.com/kendshhh/PhishLens/actions/runs/44902645811), dependency security/graph [44902645851](https://github.com/kendshhh/PhishLens/actions/runs/44902645851), deterministic evaluation [44902645832](https://github.com/kendshhh/PhishLens/actions/runs/44902645832), and CodeQL [44902643383](https://github.com/kendshhh/PhishLens/actions/runs/44902643383) passed. The exact-head DevOps Secretary report was cancelled during the branch sync ([44902644757](https://github.com/kendshhh/PhishLens/actions/runs/44902644757)); the Secretary preview assessment reports required `Secretary staging` failure because the `needs-hosted-staging` label and exact-head hosted verification are absent ([44902874550](https://github.com/kendshhh/PhishLens/actions/runs/44902874550)). Hosted preflight/deployment were skipped; no Render deploy or authenticated CRUD occurred. GitHub shows PR #268 open, mergeable on `main`, with review decision `CHANGES_REQUESTED`. Release remains **NO-GO**; 41/100 is descriptive evidence progress, not completion. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).
