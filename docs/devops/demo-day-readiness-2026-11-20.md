# Demo-day readiness matrix — 2026-11-20

> Historical snapshot — superseded by [the November 21 readiness matrix](demo-day-readiness-2026-11-21.md).

This maps the ten checks in *Engineering AI-Native Products*, p. 140,
“end-term · demo day readiness,” to evidence available on November 20, 2026.
Statuses describe evidence, not planned work. `N/A` is used only for the
conditional agent question because PhishLens does not implement an autonomous
agent.

Current source identity: GitHub `main` at
[`0c382dda175db3570e6bb7122841122254ba131d`](https://github.com/kendshhh/PhishLens/commit/0c382dda175db3570e6bb7122841122254ba131d), merged by PR #256.
Render deployed this SHA; the owner-requested `AI_ANALYSIS_ENABLED=false`
configuration deploy is pending final endpoint verification. The release
decision remains **NO-GO** because authenticated product acceptance, a reviewed
model-quality pass and recovery evidence against approved objectives remain
open.

| # / module | PDF question (paraphrased) | Status | Dated evidence | Remaining proof or action |
|---|---|---|---|---|
| 1 / M1 | Can every member explain the product's core terms? | **NOT VERIFIED** | The repository defines the extension, API, saved-report, provider and evaluation boundaries in [architecture](../architecture.md), [API reference](../api-reference.md) and [AI docs](../ai.md). No dated team-by-team explanation or review record was found. | Ask each member to explain the core terms and record their name, date and review result. Repository documentation alone cannot establish individual understanding. |
| 2 / M2 | Are the architecture diagram and ADR committed? | **PASS** | The committed [architecture document](../architecture.md) contains the component and environment diagrams; [ADR-0001](../adr/0001-application-and-deployment-architecture.md) records the decision and tradeoffs. | Keep the architecture and ADR aligned with the chosen release scope; the ADR itself notes team/instructor sign-off is not evidenced. |
| 3 / M3 | Is `main` protected, with both pipelines green? | **PARTIAL** | Strict classic protection requires eight statuses, one approval, latest-push approval and admin enforcement; stale reviews are dismissed. Main SHA `0c382dd` passed Backend, Extension, Dependency security, Workflow lint, Deterministic AI Evaluation and CodeQL. Staging integration and hosted staging were skipped. Active ruleset #26782191 has an approval rule but no required-status rules; statuses are required by classic protection. | Test expected label/skip behavior on a current runtime PR, verify an independent approval, and show a deliberately failing required check blocks merge. Skipped staging remains no product acceptance. |
| 4 / M4 | Does the backend validate AI output before acting on it? | **PASS** | [Gemini output](../../backend/ai/gemini_provider.py) is parsed by the strict `AIAnalysisPayload` schema; response fields, enum values, lengths and numeric bounds are constrained in [AI schemas](../../backend/ai/schemas.py). Backend AI/provider tests exercise invalid output and safe failure handling. | Keep these contract tests required for AI/backend changes; production provider acceptance is tracked separately. |
| 5 / M5 | If the product has an agent, does it have step limits, budgets and traces? | **N/A** | The [architecture](../architecture.md) describes one-shot local/server inference and persistence. No autonomous tool-using agent or agent loop is part of the product. | Reassess if an agent workflow is added. Do not count ordinary inference as an agent trace. |
| 6 / M6 | Do mocked tests run on PR/main changes, and do evaluations run on AI changes? | **PARTIAL** | [`CI`](../../.github/workflows/ci.yml) runs on pull requests and `main` pushes with `AI_MODE=mock`. [`Deterministic AI evaluation`](../../.github/workflows/ai-evaluation.yml) runs on pull requests and `main` pushes, and evaluates AI-related paths. PR #256 CI and AI evaluation passed; both contexts are in the eight required classic-protection statuses. | Show current runtime-PR behavior for labels, skips and a deliberately failing AI check. Unsubmitted branch commits do not run automatically. |
| 7 / M7 | Are input size, rate, quota, output-token and spend limits in place? | **PARTIAL** | [API schemas](../../backend/ai/schemas.py) cap text at 30,000 characters; [`GeminiProvider`](../../backend/ai/gemini_provider.py) caps output at 2,048 tokens; [`GeminiSpendPolicy`](../../backend/ai/spend_limit.py) blocks requests above a configured per-request upper-bound cost. Evaluation runs have exact request-count and per-run caps. Provider daily-quota responses are handled. | No application-level rate limiter, per-user daily quota or shared durable cross-instance/restart budget is evidenced. The request caps do not prove a production account-wide ceiling. Add and verify approved shared quotas before enabling paid inference. |
| 8 / M7 | Do logs carry request IDs and AI metadata? | **PARTIAL** | PR #256 merged server-generated `X-Request-ID` correlation and structured, allowlisted AI metadata for stateless inference and saved-analysis requests in [`observability.py`](../../backend/app/observability.py). CI passed on exact main SHA `0c382dd`; deployment is live. Hosted log ingestion, retention and access were not verified. | Verify redacted request events in hosted logs and confirm retention/access. Keep email content, credentials and user identifiers out of operational records. |
| 9 / M8 | Is `v1.0.0` tagged, is there a failure switch, and has rollback been rehearsed? | **PARTIAL** | No current `v1.0.0` tag or approved release exists. PR #256 merged `AI_ANALYSIS_ENABLED=false` as a backend inference kill switch for both analysis routes; the owner set it on Render and the matching-SHA configuration deployment is Live. Direct endpoint GETs from this audit client returned HTTP 403, so the effective /model-info response remains unverified. Local disposable-PostgreSQL evidence includes 11 prior-backend saved-report CRUD tests against schema `0004`; this does not establish rollback compatibility for the current production configuration. See [migration evidence](../migration-compatibility-recovery-2026-11-15.md). | Verify the deployed switch through a trusted read-only smoke; keep AI off pending an approved shared budget. Record a compatible app/config/schema target and rehearse current-release rollback before tagging. |
| 10 / M8 | Is there a written plan for models, keys and backups? | **PARTIAL** | The [provider smoke plan](ai-provider-smoke.md), [environment/secret map](environment-map-2026-11-20.md), [release record](release-record-2026-11-20.md) and [recovery runbook](runbook.md) document model/provider setup, secret boundaries and separate data recovery. On November 20 a manual Neon snapshot was restored to an isolated branch and schema/aggregate integrity matched; see the [drill record](recovery-drill-2026-11-20.md). | Model quality/provider budget and hosted key scopes remain unverified. The Neon free plan blocks production branch protection and scheduled snapshots; six-hour history is not a daily backup. The restore sample does not prove the approved RTO ≤30 minutes or RPO ≤1 hour. |

## Decision

The ten-question checklist is **not ready for ten “yes” answers**: Q1 is not
verified; Q3 and Q6–Q10 are partial. Q2 and Q4 pass, and Q5 is not applicable
to the current architecture. Keep the release **NO-GO** until exact-SHA product
acceptance, model quality and recovery gates pass. Update this matrix only when
dated evidence supports a status change.
