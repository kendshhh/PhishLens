# PhishLens DevOps compliance audit — 2026-11-23

## Decision

**Release status: NO-GO.** The repository has meaningful CI, security, AI evaluation,
and recovery controls, and this branch closes a few local implementation gaps.
The evidence still does not prove the course requirements are all met for one
reviewed release candidate. Production is behind `main` and analysis is disabled;
PR #281 has requested changes and failed required staging checks; hosted secret
scopes, migration target, full AI acceptance, DORA reconciliation, alert delivery,
and production recovery remain open. Do not report 100% compliance or a GO score.

This audit distinguishes implementation in Git from hosted behavior and human
acceptance. A passing local test proves only the local code contract.

## Scope and evidence cut

Requirements were gathered from *Engineering AI-Native Products.pdf*, Modules 3,
6, 7, and 8, and the course [DevOps track](https://csp221a.vercel.app/#devops)
and [rubric](https://csp221a.vercel.app/#rubrics). The project’s current
mainline and records were reviewed read-only. No deployment, merge, hosted
setting change, database migration, production inference, or production write
was made.

| Evidence | State at audit cutoff |
|---|---|
| GitHub `main` | `0338ad163a4892987a6a682aed29b95c22c322da`; latest recorded CI run [45019688558](https://github.com/kendshhh/PhishLens/actions/runs/45019688558) passed. |
| Main protection | Eight required contexts; one approval; latest-push approval; stale approvals dismissed; admin enforcement on; force-push and deletion blocked. Rechecked through GitHub settings API. |
| PR #281 | [Open and blocked](https://github.com/kendshhh/PhishLens/pull/281), changes requested. Hosted staging and Secretary staging required checks failed; ordinary checks passed. |
| Production | `https://phishlens-api-ocvt.onrender.com`; GET `/version`, `/health`, `/ready`, `/model-info` returned 200. Live SHA `811980c2cbf70d9957146bf329627f0826a018f1`, behind main; analysis disabled. |
| Staging | GET identity/health/readiness/model-info returned 200 for `b8feb7b472018da981e945717ff80d1278f34219`; these GETs do not clear PR #281’s failed hosted checks or prove authenticated acceptance. |
| Security alerts | 0 open secret-scanning alerts; 0 code-scanning alerts; 15 Dependabot alerts. Secret scanning is not among the eight required branch contexts. |
| Branch under review | `codex/devops-evidence-go-20261123`, implementation commit `1e5f20490f44c7e2dc30b2cdcff147e04fdf6857`, based directly on current main. Not merged or deployed. |

“Pass” means the specific evidence named in the row meets the requirement.
“Partial” means some implementation or evidence exists but a material proof or
control is missing. “Gap” means required control/evidence is absent. “Unverified”
means the available evidence cannot establish the state.

## Module 3 — CI/CD and DevOps

| Requirement | Status | Evidence | What closes it |
|---|---|---|---|
| PR pipeline runs install, lint/format, type checks where used, mocked unit tests, build, integration, security checks, staging/preview, and smoke tests in a fast-to-slow sequence. | **Partial** | `.github/workflows/ci.yml` has backend and extension checks, disposable PostgreSQL integration, CodeQL, dependency security, deterministic AI evaluation, workflow lint, and protected hosted staging. Local branch adds npm caching and concurrency control. Complete fail-fast ordering and all secret-scan gates are not proven; the local test suite does not execute GitHub’s workflow. | Run the exact updated workflow on a reviewed PR; retain required status for each stage, secret-scan gate, path coverage, and clear failure summaries. |
| Main merge automatically deploys the accepted code and verifies the live result. | **Gap** | Main CI passed, but production serves `811980c…` while main is `0338ad…`. Render metadata and deploy triggers have historically disagreed; the current live GETs do not prove auto-deploy or exact SHA after merge. | Reconcile Render’s current trigger setting; deploy an approved merge automatically; verify SHA, product flow, health, and notification from post-deploy automation. |
| Main is protected by required checks and review; force push and deletion are blocked. | **Pass** | Current GitHub rules require eight checks and review, latest-push approval, stale-review dismissal, admin enforcement, and disallow force push/deletion. | Recheck after any protection change; keep the rule configuration evidence in the release record. |
| Fresh runners, stale-run cancellation, caching, parallel jobs, and fail-fast behavior are used without cancelling protected staging unsafely. | **Partial** | GitHub-hosted jobs and backend uv cache exist. This branch adds npm dependency caching and ref/PR concurrency; labeled protected staging runs are allowed to finish. Broader fail-fast/path-filter behavior and current hosted execution are not verified. | Confirm updated Workflow lint and CI; measure queue and runner time separately; prove stale pending work is superseded and protected deployment remains serialized. |
| Local, preview, staging, and production are separated; secrets are environment-scoped, least-privilege, masked, and AI keys/spend limits are distinct per environment. | **Unverified / Partial** | Separate Render environments and GitHub staging environment are documented. Private Render-to-Neon targets, effective variable scopes, production secret permissions, and separately capped AI keys were not independently confirmed. This branch documents required quota variable names but does not provision their values. | Verify environment names, reviewer rules, Render service-to-database mapping, role grants, separate key identities and caps without recording secret values. Keep paid AI disabled until verified. |
| Secret scanning is a required gate and alerts are resolved. | **Gap** | GitHub currently reports zero open secret alerts, but no secret-scanning required context appears in the protected check list. There are 15 open Dependabot alerts. | Make an explicit secret scan a required check, verify it on a PR, and triage the 15 dependency alerts with documented dispositions. |
| Database migrations run through CI and schema changes use backward-compatible expand/dual-write/backfill/read-switch/contract sequencing; destructive changes have a backup. | **Partial** | Existing pipeline runs migrations against disposable PostgreSQL and checks lineage. This branch adds additive migration `0005_ai_request_quota`. The full suite’s database-dependent tests were skipped locally; this migration has not been applied to any hosted database. The live target mapping, full expand/contract history, and backup-before-destructive-change proof are not complete. | Run migration against an isolated disposable database and the exact hosted staging target after ownership/mapping approval; test old/new app compatibility and rollback before any destructive contract step. |
| Track deployment frequency, merge-to-live lead time, change failure rate, and time to restore. | **Partial / Gap** | See the DORA section below. Frequency and lead time are partial historical samples; change failure rate and time to restore are unknown. | Reconcile deploys to successful releases and merged SHAs; link incidents, rollbacks, and hotfixes; record incident start and service-restored timestamps on a regular window. |
| Measure an optimization baseline, change one lever at a time, and report comparable before/after results. | **Partial** | `docs/devops/optimizations.md` records small experiments. Cached uv Backend median was 50.92 s versus 61.52 s baseline (n=2 per side); staging cache whole-job median increased 3.5 s. These do not establish sustained end-to-end improvement. | Repeat on the same workflow/check set with a larger sample and publish runner time, wait time, variability, and before/after results. Keep all checks. |
| Maintain a pipeline diagram, stage/trigger documentation, metrics log, optimization record, and per-consult metrics update. | **Partial** | `PIPELINE.md`, workflow diagrams, `docs/devops/metrics.md`, and `docs/devops/optimizations.md` exist. This branch refreshes metrics as of Nov 23 while preserving dated source samples. Course consultation updates are human evidence and were not verified. | Refresh the same metrics log before each consultation and record the actual report/meeting evidence. |

### DORA measurement status

The latest complete source window remains **2026-10-17 00:00 UTC to
2026-11-14 03:12 UTC**. The Nov 23 audit did not build a new reconciled 28-day
sample, so these are the latest defensible historical figures, not current
Nov 23 values.

| DORA measure | Existing result | Status and limitation |
|---|---|---|
| Deployment frequency | 69 Render production deploy records in 28 days; raw inventory ratio 2.46 records/day. | **Partial.** Records are not deduplicated/reconciled to unique successful code releases delivered to users. 2.46 is not an accepted DORA frequency. |
| Lead time for changes | 64 matched merged PR SHAs: mean 4.40 min, median 3.42 min, p90 5.47 min. 31 of 95 merged PR SHAs unmatched; five deploy records unmatched. | **Partial.** Incomplete match coverage and stale window. |
| Change failure rate | Zero failed deploy statuses in 69 records. | **Unknown / Gap.** Deploy status is not incident/rollback/hotfix linkage. Do not report CFR as zero. |
| Time to restore service | No measured production restoration sample; n=0. | **Unknown / Gap.** Do not report zero minutes. |

The 28-day CI sample records 682 PR workflow attempts (515 pass, 112 fail,
55 cancelled), and 86 completed main-push runs (all passed). These are pipeline
health figures, not DORA measures. The later Nov 20 timing refresh had only four
main runs and does not refresh the four DORA measures.

## Module 6 — AI-aware testing in CI

| Requirement | Status | Evidence | What closes it |
|---|---|---|---|
| Ordinary unit/API CI mocks the AI client and does not make paid model calls. | **Pass** | Mocked/provider contract tests and deterministic AI evaluation are in the repository; ordinary CI does not need a live provider. The project has a bounded, separate provider smoke workflow. | Keep live provider credentials absent from ordinary CI and verify PR runs show zero provider calls. |
| Test eight unhappy paths: timeout, rate limit, provider failure, invalid JSON, wrong shape, business-rule failure, empty retrieval, and oversized input; assert properties rather than wording. | **Partial** | Provider timeout/rate/error contracts, malformed-output checks, business evidence validation, and size checks exist. The repository does not yet provide one explicit passing-test map for all eight cases; empty/no-retrieval coverage and property assertions need candidate-bound confirmation. | Add/maintain a named test-to-requirement crosswalk and show each path passing for the selected candidate. |
| Commit a 20–50 case evaluation set covering normal, edge, adversarial, and regression examples. | **Pass for development set** | The committed synthetic set has 40 cases. It is not a held-out release-quality set. | Keep the development set and create a separate representative, held-out acceptance set with owner-approved data handling. |
| Run evaluations on AI/prompt changes, compare against previous scores, and attach results to PR; unrelated changes must not invoke paid providers. | **Partial** | `docs/devops/ai-regression-policy.md` and the deterministic AI workflow run on relevant changes and report not-applicable for unrelated changes. The workflow passes contract/development validity, not quality acceptance. | Verify the exact new workflow/status on a PR and attach before/after quality scores and accepted threshold result. |
| Assert structured output and semantic properties, not exact wording; define numeric quality thresholds. | **Partial / Gap** | Schema and business-rule validation exists. The 40-case synthetic result reports 18.75% phishing recall and 6.25% legitimate false-positive rate; no numeric model-quality cutoff is approved. Historical English cohort results are scoped to that cohort and do not prove broad release quality. | Approve a representative held-out threshold and fail the release gate when recall, false positives, output validity, or another agreed measure misses it. |
| Run a bounded live smoke on a schedule and a full evaluation plus human spot-check before release. | **Gap** | `docs/devops/ai-provider-smoke.md` describes a safe bounded workflow, but it is manual-only and unscheduled. A current-candidate full evaluation and human review are not complete. | Configure an owner-approved schedule/key/budget in the staging environment; capture a full pre-release evaluation and reviewer sign-off. |
| Maintain an experiment log and promote real failures to regression cases. | **Partial** | Evaluation records and policy exist; a complete experiment log/review trail and failure-to-regression linkage are not established. | Record each model/prompt experiment, data/cohort, model version, metrics, reviewer decision, cost, and new regression cases. |

## Module 7 — Production readiness

| Requirement | Status | Evidence | What closes it |
|---|---|---|---|
| Hold a threat-model session covering trust boundaries, access control, injection, cost abuse, and secret exposure. | **Gap** | No completed, dated session record with attendees, decisions, and follow-up owners was found. | Hold and record the session; link tracked follow-up actions and acceptance. |
| Check ownership on every endpoint/data query; parameterize SQL; use HTTPS, restricted CORS, secure sessions, dependency audit, and secret scanning. | **Partial** | Auth/ownership tests and parameterized database operations exist; CodeQL and dependency checks are required. Hosted authenticated CRUD/isolation on the current candidate did not pass, full endpoint/query coverage and current CORS/session config are not proven, and secret scanning is not a required gate. | Produce an endpoint/query ownership inventory, pass cross-user isolation acceptance on exact staging SHA, verify effective HTTPS/CORS/session policy, require secret scan, and disposition dependency alerts. |
| Defend against prompt injection; use least-privilege tools; validate model output/tool arguments; render output safely; never send secrets in prompts; include adversarial evals. | **Partial** | The prompt treats email as untrusted input; output schemas and evidence-source validation reject invalid results; extension rendering is covered by tests. No tool execution path is evidenced. Candidate-bound hosted adversarial/safe-render acceptance and a secrets-in-prompt audit remain open. | Pass candidate-bound injection/adversarial, rendering and data-flow checks; retain an explicit no-tools/no-secret prompt policy or validate every tool boundary. |
| Enforce all five cost gates: input limit, per-user/IP rate limit, per-user daily quota, maximum output tokens, and spend cap plus alerts. | **Partial** | Existing 30,000-character input cap and 2,048 output-token cap remain. Commit `1e5f204` adds HMAC-hashed fixed-window IP limits, per-user daily limit for authenticated saved-analysis requests, and a shared conservative daily spend reservation. The unauthenticated `/analyses` route has IP limits but no authenticated per-user identity. Threshold crossing currently emits a warning log, not a tested alert delivery. Config values are examples only; migration and settings are not deployed. | Require identity or explicitly constrain anonymous paid inference; provision per-environment limits after owner approval; apply migration to isolated staging; test concurrent cap behavior and actual alert delivery/acknowledgement. |
| Timeouts, retries with backoff/jitter, circuit breakers, bulkheads, readiness/health, and graceful degradation. | **Partial** | Provider and database timeouts, health/readiness routes, safe unavailable responses, and a bounded saved-analysis worker exist. Gemini SDK retry attempts are one; a circuit breaker and production alert response are not evidenced. | Select and document retry policy; add/test circuit breaking where needed; verify bulkheads cover all paid routes and exercise live failure recovery without paid unbounded tests. |
| Structured logs, metrics, and traces share a request ID; AI metadata includes model/prompt version, tokens, latency, cost, validation, retries, and fallback. | **Partial** | Request IDs and privacy-safe structured access logs exist. Commit `1e5f204` adds provider token counts and a configured-rate `estimated_cost_usd` field (not provider invoice cost); success logs include validation/retry/fallback fields. Production log ingestion, cross-service metric/trace correlation and actual-cost reconciliation are not shown. | Verify hosted redacted log retention/access and joined metrics/traces; label estimates vs billed costs and reconcile them with provider usage. |
| Provide dashboard for latency, traffic, errors, saturation, AI cost, invalid output, fallback, and retrieval quality. | **Gap** | No current dashboard with these panels was evidenced. | Publish and verify the dashboard, including owners, data source, refresh/retention, and alert links. |
| Write and approve an SLI/SLO and error budget; provide health/readiness. | **Partial** | `/health` and `/ready` return 200 for the current production GET probe. `docs/devops/reliability-acceptance-2026-11-14.md` records proposed targets, not a team-approved measured SLO/error budget; production identity is behind main. | Approve user-journey SLI/SLO, error-budget policy, measurement window and owner; run it on the exact release. |

## Module 8 — Deployment, operations, and maintenance

| Requirement | Status | Evidence | What closes it |
|---|---|---|---|
| Separate deployment from release with runtime flags; build one immutable artifact for staging and production; use zero-downtime rollout where feasible. | **Partial / Unverified** | Runtime `AI_ANALYSIS_ENABLED` kill switch exists. Production/staging use managed Git deployments; identical immutable artifact promotion and zero-downtime behavior are not proven. | Record artifact/package digest and promote the same tested artifact; verify rollback-safe runtime flag and traffic strategy. |
| Tag a versioned release and changelog; pin model versions. | **Gap / Partial** | No approved `v1.0.0` release/tag was found. Model identity is recorded and provider controls require configured model ID; owner-approved release model and upgrade evaluation are not established. | Select exact reviewed candidate, record changelog, create approved tag, pin model ID/revision, and attach acceptance report. |
| Provide runtime AI kill switch. | **Partial** | `AI_ANALYSIS_ENABLED=false` exists and production currently reports analysis disabled in `/model-info`. It has not been tested as a release-time operator switch for the current candidate. | Test switch off/on behavior on staging, prove no provider call when disabled, assign owner and include operational instructions. |
| Write rollback runbook and practice it so another teammate can perform it; include compatible app/schema restoration and health checks. | **Partial** | `docs/devops/runbook.md` exists. Nov 8 staging rollback/redeploy took 40.352/86.593 seconds and health checks passed; it was not a teammate-led production/schema-compatible drill. Nov 20 isolated database restore checked schema/aggregates, not service RTO/RPO. | Rehearse with a second operator against the approved staging candidate; verify app/config/schema compatibility and record timing, health, smoke, and artifacts. |
| Run post-deploy smoke; maintain uptime monitor, actionable alerts, and owned notification channel. | **Partial / Gap** | Health/readiness routes and a scheduled production drift observer exist; exact-candidate product smoke is manual-only. No tested monitor/alert delivery and backup recipient are evidenced. | Automatically run exact-SHA product smoke after deploy; configure uptime monitor, actionable threshold, primary/backup channel and an acknowledged alert drill. |
| Record incident detection/recovery times, severity, and blameless postmortems. | **Partial** | `docs/devops/incidents.md` contains historical incidents and drill records; incident-to-deploy linkages, measured detection/recovery for production, and a complete postmortem process are incomplete. | For each incident, log severity, affected release, detect/declare/restore timestamps, impact, blameless analysis, and owned follow-up. |
| Maintain models, dependencies, keys, tested backups, approved RTO/RPO, and weekly cost/free-tier review. | **Partial** | Model/evaluation and recovery runbooks exist. Nov 20 isolated restore checked schema and aggregate counts; full-service RTO/RPO and recoverable-point age remain unmeasured. Neon free plan has no scheduled snapshots/protected branch; backup responders are not confirmed. Weekly cost/free-tier review and key rotation evidence are not complete. | Assign data/key owners, test backup schedule and restore path, measure approved RTO≤30m/RPO≤1h, rotate credentials, and log weekly spend/free-tier review. |
| Commit a handover kit: setup, architecture/ADRs, runbooks, `.env.example`, seed steps, API/AI docs, pinned-model/eval instructions. | **Partial** | `PIPELINE.md`, runbooks, environment maps, `.env.example`, seed/migration instructions and AI evaluation docs exist. The kit lacks confirmed backup contacts, complete secret/key procedures, and current exact release evidence. | Publish a single indexed kit and have a teammate follow setup, runbook, model/eval and recovery steps. |
| Demo day: freeze changes, tag release, rehearse rollback and AI-failure drill, check health/demo data, and pass live deploy challenge. | **Gap** | No approved release/tag, current-candidate drill, human acceptance, or completed live challenge is evidenced. | Complete the freeze checklist and rehearsals against the exact tagged candidate; attach live challenge results and sign-off. |

## DORA and optimization closeout actions

1. Establish a dated release ledger with deploy ID, source SHA, merged PR, success,
   and whether it caused an incident, rollback, or hotfix.
2. Define the reporting window and successful-release rule before computing
   deployment frequency. Reconcile all merge-to-live matches and show unmatched
   count/coverage with lead time.
3. Record incident declaration and service-restored timestamps to compute change
   failure rate and time to restore. Unknown remains unknown; never turn missing
   observations into zero.
4. Run one controlled optimization at a time on an identical event/check set,
   with enough samples to show median, p90, sample size, runner duration, queue
   delay, and failure rate before/after.
5. Update `docs/devops/metrics.md` weekly and before each course consultation.

## Course CI/CD rubric

The course rubric categories total 100 possible points, but this review does not
assign a numeric score because the grading rule/evidence acceptance is not
established. Status is the evidence status for each area.

| Rubric area | Weight | Status | Main open proof |
|---|---:|---|---|
| Pipeline design and coverage | 15 | **Partial** | Current candidate workflow result and complete gated stage coverage. |
| Automation and quality gates | 10 | **Partial** | PR #281 required staging checks are failing; no exact release candidate is accepted. |
| Optimization with measured results | 20 | **Partial** | Small n=2 job sample; no reliable end-to-end improvement. |
| Environments and secrets | 10 | **Partial / Unverified** | Private target mapping, least privilege, distinct AI key/cap scopes. |
| AI-aware pipeline practices | 10 | **Partial** | Approved quality threshold, eight-path crosswalk, scheduled smoke, human release eval. |
| Release and rollback | 10 | **Partial** | Tag/changelog and second-operator compatible production recovery drill. |
| Reliability and incidents | 10 | **Partial** | Approved SLO/error budget, alert delivery, measured production recovery. |
| Metrics, docs, and reporting | 10 | **Partial** | Reconciled current DORA ledger and recurring consultation records. |
| Live performance | 5 | **Open** | Exact release product-journey performance and acceptance evidence. |

Course-process evidence also needs the declared DevOps role, consultation report
and metrics update, reviewed main changes, and sprint planning/review/retrospective
records. These are human/course artifacts, not repository code, and were not
verified as complete in this audit.

## Local verification of implementation commit

At implementation commit `1e5f20490f44c7e2dc30b2cdcff147e04fdf6857`:

- Backend and script suites: **596 passed, 45 skipped, 199 subtests passed**.
  Database-dependent/opt-in tests were skipped; no hosted migration was run.
- Extension Node suite: **300 passed**.
- Ruff (`backend`, `scripts/secretary`): passed.
- ESLint and extension manifest validation: passed after `npm ci`.
- `git -c core.whitespace=cr-at-eol diff --cached --check`: passed for the
  repository’s CRLF workflow file.
- The local `actionlint` binary and YAML parser were unavailable. GitHub’s
  required Workflow lint check must validate the workflow after PR creation; no
  PR was created in this task.

## Sources

- *Engineering AI-Native Products.pdf*, Modules 3, 6, 7, 8 (user-provided PDF).
- [CSP221A DevOps requirements](https://csp221a.vercel.app/#devops) and
  [CI/CD rubric](https://csp221a.vercel.app/#rubrics).
- Repository evidence: [`PIPELINE.md`](../../PIPELINE.md),
  [`metrics.md`](metrics.md), [`optimizations.md`](optimizations.md),
  [`ai-regression-policy.md`](ai-regression-policy.md),
  [`ai-provider-smoke.md`](ai-provider-smoke.md), [`runbook.md`](runbook.md),
  [`recovery-drill-2026-11-20.md`](recovery-drill-2026-11-20.md),
  [`incidents.md`](incidents.md), and
  [`reliability-acceptance-2026-11-14.md`](reliability-acceptance-2026-11-14.md).
