# DevOps rubric readiness — 2026-11-27 08:45 UTC

## Decision

**A 10/10 (100/100) is not supported. Release remains NO-GO.** This crosswalk
uses the 100-point rubric supplied by the project owner. It records current
evidence and gaps; it does not convert qualitative bands into invented partial
points. The rubric gives criterion maxima and broad bands, but does not define
how to score the gaps between bands or how to award partial points within a
criterion.

## Criterion crosswalk

| Rubric criterion | Max | Current evidence | Gap to Excellent |
|---|---:|---|---|
| Pipeline design and coverage | 15 | **Strong, not Excellent.** On PR #268 head `d77491d8fd91252190755714df8e5fa475e9c13b`, Backend, Extension, Staging integration, migration preflight, Workflow lint, Dependency security, deterministic AI evaluation, CodeQL, trusted Neon preflight, and post-acceptance Secretary status all passed. | Production remains Git-backed; same-digest production promotion and exact-SHA production acceptance have not run. |
| Automation and quality gates | 10 | **Strong, not Excellent.** The exact-head required checks and protected staging controller passed; PR review is approved on `d77491d`; unrelated Issue 90 staging job was explicitly skipped by its path filter. | A deliberately failing required check has not been shown to block merge. This documentation follow-up will create a new head and require fresh exact-head review/checks. |
| Optimization with measured results | 20 | **Partial.** The reproducible 28-day report records a 3.66-minute merge-to-live proxy median (`60/142` matched), 63 successful deploy records, and CI median 66 seconds (`115/117` successful). | No comparable before/after result establishes a downward trend in end-to-end pipeline time and failure rate. Change failure rate, failed-deployment restore time, and deployment rework are not measured. |
| Environments and secrets | 10 | **Strong for staging; partial overall.** Exact-head staging acceptance verified the isolated Neon project/branch, Auth bridge, migration revision, and staging service identity; the evidence records zero production requests or writes. | Production service/environment mapping is not privately re-attested; both Render services are Git-backed, and same-digest promotion is absent. |
| AI-aware pipeline practices | 10 | **Partial.** Deterministic AI regression checks pass in CI, and the hosted acceptance gate records model quality as blocked when approval is absent. | No AI-owner-approved representative holdout report or threshold is bound to the candidate model. Current model acceptance and scheduled live inference smoke are blocked; historical English evidence is advisory only. |
| Release and rollback | 10 | **Partial / below Excellent.** Versioned manifest validation, gated workflow, staging artifacts, and rollback documentation exist in the candidate. Production Auto Deploy is off. | Render is not image-backed; backend image digest is `null`, so identical-digest promotion is unproven. No production tag/release/changelog or current-schema-compatible rollback rehearsal exists. |
| Reliability and incident handling | 10 | **Partial.** Exact-candidate staging sign-in, persistent CRUD, account isolation, cleanup, and extension UX passed. | Current alert delivery, named backup responder, alert-to-recovery drill, application rollback, database restore, and measured RTO/RPO are not proven. Staging acceptance is not production availability. |
| Metrics, documentation, and reporting | 10 | **Partial.** A dated reproducible DORA report, refreshed cross-PR evidence, and redacted current staging proof are published. | Change failure rate, failed-deployment recovery time, deployment rework, a comparable end-to-end optimization, and a full current sprint metric log remain unmeasured. |
| Live performance | 5 | **Strong staging demonstration; not full Excellent evidence.** The protected controller deployed and accepted the exact extension/backend candidate on isolated staging. | No production release/demo was performed; AI acceptance is blocked and the rubric's live verbal walkthrough cannot be established from repository evidence. |

## Current exact-head evidence — 2026-11-27 08:45 UTC

PR #268 head `d77491d8fd91252190755714df8e5fa475e9c13b` passed exact-head CI
run [45966131065](https://github.com/kendshhh/PhishLens/actions/runs/45966131065),
Workflow lint [45966130957](https://github.com/kendshhh/PhishLens/actions/runs/45966130957),
Dependency security [45966131061](https://github.com/kendshhh/PhishLens/actions/runs/45966131061),
Deterministic AI Evaluation [45966131179](https://github.com/kendshhh/PhishLens/actions/runs/45966131179),
CodeQL [45966123755](https://github.com/kendshhh/PhishLens/actions/runs/45966123755),
and trusted Neon preflight [45966125445](https://github.com/kendshhh/PhishLens/actions/runs/45966125445).
The trusted hosted controller [45966647832](https://github.com/kendshhh/PhishLens/actions/runs/45966647832)
passed exact-PR inspection, Neon isolation, controlled staging deployment,
authenticated acceptance, and `Secretary staging`. The PR review decision is
APPROVED on this exact SHA. The Issue 90 package job was skipped by its explicit
path filter; it is not a substitute for the required checks.

The live staging `/version` SHA and backend source SHA both equal `d77491d`.
The candidate extension ZIP SHA-256 is
`495d9bb7d3a222b103a30de819f6a0e7c8d4c9844e9120c24b9d6f4a4b47bdb7`.
On isolated Neon project `ancient-brook-17208049`, branch
`br-rough-sea-a1l6ehi1`, migration revision `0005_ai_request_quota`, the run
passed sign-in, persistent create/list/read/update/delete, reload persistence,
ownership, two-account isolation, cleanup, and loading/success/auth/API/timeout
UX checks. It records zero production requests, writes, or Auth requests.
The redacted JSON and review record are in
[`evidence/2026-11-27-staging-acceptance-d77491d.md`](evidence/2026-11-27-staging-acceptance-d77491d.md).

AI quality remains **BLOCKED** (`approval_not_provided`) for TF-IDF revision
`a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`;
`backend_image_digest` is `null`; `release_decision` is `no-go`. This successful
staging product acceptance does not constitute AI-quality acceptance or
production release evidence.

The current dependency and merge-tree evidence is in the
[PR alignment record](pr-alignment-2026-11-27.md).

## Required closure evidence

1. Obtain the AI/model owner's reviewed policy decision and a representative,
   permissioned, independently labeled holdout report bound to the exact model
   revision. Require its numeric threshold status before enabling inference or
   production release. Wilbert's historical English result remains advisory.
2. Move Render to an approved immutable-image path, retaining one backend image
   digest and extension ZIP across staging and production. Supply the missing
   protected release configuration and require exact-SHA production smoke.
   Do not enable production promotion until the image service, credentials,
   mappings, independent reviewer, and deployment controls are verified.
3. Rehearse rollback to a schema/config-compatible application artifact and
   restore a fresh backup into an isolated Neon branch. Record measured RTO,
   RPO, recovery-point age, operator, and integrity checks; verify alert
   delivery and name the backup responder.
4. Complete the five-metric DORA dataset: reconcile the production deployment
   denominator, classify failed changes, record failed-deployment recovery,
   and identify deployment rework. Run a like-for-like before/after optimization
   study with adequate samples and publish calculations. Keep unknowns as
   unknown rather than scoring them as zero.
5. Demonstrate that a deliberately failing required check blocks merge. The
   exact candidate's checks and staging acceptance passed, but no negative
   merge-gate experiment is recorded.
6. This evidence update is documentation-only; after it is pushed, obtain a
   fresh exact-head review and required checks. Do not merge or publish a
   release while the AI, image-promotion, production smoke, and recovery gates
   above remain unresolved.

The full current metrics and source methodology are in
[the DORA report](dora-report-2026-11-27.md); current service observations are
in [metrics.md](metrics.md); release workflow state is in
[controlled-release.md](controlled-release.md).
