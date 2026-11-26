# Demo-day readiness matrix — 2026-11-21

This maps the ten checks in *Engineering AI-Native Products*, p. 140,
“end-term · demo day readiness,” to repository and service evidence current on
November 21, 2026. Statuses describe demonstrated evidence, not planned work.
N/A is used only for the conditional agent question because PhishLens has no
autonomous agent.

Current source is GitHub main 811980c2cbf70d9957146bf329627f0826a018f1 (PR
#264). Render production and manually deployed staging both run this SHA.
Production drift checked exact SHA, health and readiness; that is not a product
journey test. The release decision remains **NO-GO**.

| # / module | PDF question (paraphrased) | Status | Current evidence | Remaining proof |
|---|---|---|---|---|
| 1 / M1 | Can every member explain the product's core terms? | **NOT VERIFIED** | Architecture, API and AI docs define product terms. | Record a dated explanation/review by each member; repository docs do not prove individual understanding. |
| 2 / M2 | Are the architecture diagram and ADR committed? | **PASS** | Architecture document contains component/environment diagrams and ADR-0001 records the decision. | Keep them aligned with implementation; team/instructor sign-off is not evidenced. |
| 3 / M3 | Is main protected, with both pipelines green? | **PARTIAL** | Main CI, AI evaluation, workflow lint, dependency security, CodeQL and drift checks passed. Active CI ruleset #27733591 requires four contexts with strict checking disabled; one-approval ruleset is active. Classic protection could not be read (403), and no failing-check block was demonstrated on a current runtime PR. | Reconcile and verify effective status settings, latest-push review behavior, label/skip semantics and a deliberately failing required status. |
| 4 / M4 | Does the backend validate AI output before acting on it? | **PASS** | Gemini output is validated by the strict AIAnalysisPayload schema; backend tests cover invalid output and safe failure. | Keep these checks required for applicable backend/AI changes. This is code/test evidence, not provider acceptance. |
| 5 / M5 | If the product has an agent, does it have step limits, budgets and traces? | **N/A** | Current architecture has one-shot inference and persistence, not an autonomous agent/tool loop. | Reassess only if an agent loop is added. |
| 6 / M6 | Do mocked tests run on PR/main changes, and evaluations run on AI changes? | **PARTIAL** | CI and deterministic AI evaluation passed on current main. Visible active ruleset does not require the AI evaluation context, and current classic status settings could not be rechecked. | Demonstrate current runtime-PR behavior and make AI evaluation enforcement unambiguous. |
| 7 / M7 | Are input size, rate, quota, output-token and spend limits in place? | **PARTIAL** | Input/output bounds and per-request cost checks exist; evaluation has request and run caps. | Shared durable daily quota, per-user rate/daily limits and cross-instance spend budget are not evidenced. Keep paid inference disabled. |
| 8 / M7 | Do logs carry request IDs and AI metadata? | **PARTIAL** | PR #256 added request IDs and structured allowlisted AI metadata. The scheduled observer checks SHA, health and readiness. | Verify hosted redacted log ingestion/retention/access and an alert path; no extension-journey SLI/SLO is measured. |
| 9 / M8 | Is v1.0.0 tagged, is there a failure switch, and has rollback been rehearsed? | **PARTIAL** | No release/tag exists. PR #256 added the analysis kill switch; PR #257 added a disabled-aware zero-inference smoke path. The smoke remains manual, and current production rollback is not rehearsed. | Verify the current disabled model state, rehearse a schema/config-compatible rollback, and tag only after GO. |
| 10 / M8 | Is there a written plan for models, keys and backups? | **PARTIAL** | Provider smoke plan, current environment map and runbook are linked. A Nov 20 manual snapshot restored to an isolated branch with schema and aggregate counts matching. | Current key/access scopes, model quality and Auth are unresolved; Neon free plan blocks production branch protection and scheduled snapshots; approved ≤30-minute RTO / ≤1-hour RPO are unmeasured. |

## Decision

The ten-question checklist is not ready for ten “yes” answers. Q1 is not
verified; Q3 and Q6–Q10 are partial; Q2 and Q4 pass; Q5 is not applicable.
Keep the release at **NO-GO** until authenticated exact-SHA product acceptance,
model-quality thresholds, effective merge protection, deployment smoke and
current application/data recovery evidence pass.

Use [the current release scorecard](release-readiness-scorecard-2026-11-21.md),
[release record](release-record-2026-11-21.md),
[environment map](environment-map-2026-11-21.md), and
[recovery drill](recovery-drill-2026-11-20.md) for the linked evidence.