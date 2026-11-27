# DevOps rubric readiness — 2026-11-27 11:04 UTC

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
| Pipeline design and coverage | 15 | **Not Excellent.** PR #268 head `d77491d8fd91252190755714df8e5fa475e9c13b` passed Backend, Extension, Staging integration, migration preflight, Workflow lint, Dependency security, deterministic AI evaluation, CodeQL, trusted Neon preflight, and post-acceptance Secretary status. PR #268 merged as `88156d4`; the main tree is identical to the accepted candidate tree. | Main-push controller run `45974461494` reported no runtime changes and skipped deploy/acceptance; it is not product evidence. Production remains Git-backed; same-digest promotion and exact-SHA production acceptance have not run. |
| Automation and quality gates | 10 | **Not Excellent.** At 10:11 UTC, classic protection and active ruleset #27733591 required the same eight strict contexts. Main requires one approval, latest-push approval, stale-review dismissal, and admin enforcement. At 10:12 UTC, self-review was prevented for all three protected staging environments while preserving `main`-only refs and reviewer lists. | No deliberately failing required-check experiment proves merge blocking. Current #282 is docs-only: all applicable checks passed, Secretary staging reports explicit N/A, and hosted staging was not triggered. |
| Optimization with measured results | 20 | **Partial.** The reproducible 28-day report, refreshed 11:04 UTC, records a 3.66-minute merge-to-live proxy median (`60/143` matched), 63 successful deploy records, and CI median 66.50 seconds (`116/118` successful). PR #119 measured and merged one Backend job improvement: cached pinned uv median 50.92 s versus cached pip 61.52 s (`n=2` per side, 17.2% lower); current `main` retains this approach. | This small job-level result is not an end-to-end improvement or a multi-optimization trend. Other cache trials were neutral/slower; change failure rate, failed-deployment restore time, and deployment rework are not measured. |
| Environments and secrets | 10 | **Partial overall; exact staging acceptance passed.** Exact-head staging acceptance verified the isolated Neon project/branch, Auth bridge, migration revision, and staging service identity; the evidence records zero production requests or writes. Staging environment self-review is now prevented. | Current Render runtime/migration/Auth mapping is not re-attested. Both services remain Git-backed; the production Render environment is marked unprotected; required release/migration secret names and production promotion variables are absent. |
| AI-aware pipeline practices | 10 | **Partial.** Deterministic AI regression checks pass in CI, and the hosted acceptance gate records model quality as blocked when approval is absent. | No AI-owner-approved representative holdout report or threshold is bound to the candidate model. Current model acceptance and scheduled live inference smoke are blocked; historical English evidence is advisory only. |
| Release and rollback | 10 | **Partial / below Excellent.** Versioned manifest validation, gated workflow, staging artifacts, and rollback documentation exist in the candidate. Production Auto Deploy is off. | Render is not image-backed; backend image digest is `null`, so identical-digest promotion is unproven. No production tag/release/changelog or current-schema-compatible rollback rehearsal exists. |
| Reliability and incident handling | 10 | **Partial.** Exact-candidate staging sign-in, persistent CRUD, account isolation, cleanup, and extension UX passed. | Current alert delivery, named backup responder, alert-to-recovery drill, application rollback, database restore, and measured RTO/RPO are not proven. Staging acceptance is not production availability. |
| Metrics, documentation, and reporting | 10 | **Partial.** A dated reproducible DORA report, refreshed cross-PR evidence, and redacted current staging proof are published. | Change failure rate, failed-deployment recovery time, deployment rework, a comparable end-to-end optimization, and a full current sprint metric log remain unmeasured. |
| Live performance | 5 | **Partial overall; staging demonstration evidence only.** The protected controller deployed and accepted the exact extension/backend candidate on isolated staging. | No production release/demo was performed; AI acceptance is blocked and the rubric's live verbal walkthrough cannot be established from repository evidence. |

## Current exact-head evidence — PR inventory 2026-11-27 11:00 UTC; checks 10:48 UTC; control plane 10:12 UTC; DORA 11:04 UTC

PR #268 merged at 08:44 UTC as main commit
`88156d479d19eb0b8018ab76aa3170eb60079765`. Git confirms its tree
`89a3b3e0701629497c4f1f14e756f26ca98a10c7` exactly matches the staging-tested
PR candidate tree for `d77491d8fd91252190755714df8e5fa475e9c13b`. The merge did
not change application source or migration graph. PR #281 is now closed
unmerged. PR #282 remains open at head
`27118fc610f2c01fd11a472e0939f6dc74cbe130` against current `main`; its only
changed file is a DevOps integration note. Backend, Extension, Staging
integration, migration source preflight, CodeQL, dependency security, AI
evaluation, dependency graph review, and workflow lint passed. Neon and hosted
acceptance are skipped for this docs-only diff, and Secretary staging explicitly
reports N/A. No product acceptance ran on #282.
The earlier runtime changes are already in #268/main; these checks do not
represent hosted product acceptance.

The post-merge trusted controller run
[45968192019](https://github.com/kendshhh/PhishLens/actions/runs/45968192019)
skipped all jobs. Later run [45974461494](https://github.com/kendshhh/PhishLens/actions/runs/45974461494)
inspected main and reported no runtime changes; deployment and acceptance were
skipped. Neither run is post-merge product acceptance. A subsequent read-only
staging `/version` request timed out. The last positive live staging identity remains
the authenticated exact-PR run below; no production check was performed.

PR #282's current documentation-only head is
`27118fc610f2c01fd11a472e0939f6dc74cbe130`. Exact-head Backend, Extension,
Staging integration, migration source preflight, Workflow lint, Dependency
security, deterministic AI evaluation, CodeQL, and dependency graph review
passed. The `verify-neon` and Issue 90 jobs were skipped by their documented
conditions; `Secretary staging` reported explicit N/A because there are no
runtime changes. No hosted deployment or product acceptance ran. The previous
main controller run `45978972202` also skipped Neon validation, deployment, and
product acceptance; neither is a second product acceptance or production
release.

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
APPROVED on this exact SHA and the PR was subsequently merged. The Issue 90 package job was skipped by its explicit
path filter; it is not a substitute for the required checks.

During the acceptance run, staging `/version` and backend source both reported `d77491d`; a later read-only `/version` probe timed out, so current staging identity is not freshly verified.
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
[PR alignment record](pr-alignment-2026-11-27.md), refreshed against all 16 open
PRs at 11:00 UTC.

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
