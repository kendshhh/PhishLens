# Release readiness scorecard — 2026-11-20

> Historical snapshot. Use the
> [November 21 scorecard](release-readiness-scorecard-2026-11-21.md) for the
> current release evidence and blockers. This draft's weights were not approved.

**Status: draft for team and instructor agreement. No completion percentage is
approved or calculated.** This is a project delivery readiness measure, not a
course grade. The weights and any non-binary scoring rule require agreement
before anyone reports a percentage.

This scorecard groups the seven final release requirements tracked by
[issue #153](https://github.com/kendshhh/PhishLens/issues/153). It maps the
issue checklist to evidence, owners and blockers; it does not create new
acceptance decisions.

## Draft seven-area evidence map

The owner names below follow the existing handoff; confirm assignments on
issue #153 before treating them as committed task ownership.

| Area | Weight | Proposed owners (confirm) | Pass evidence required | Evidence already recorded | Current state / blocker |
|---|---:|---|---|---|---|
| 1. Agreed product scope and acceptance ownership | Pending | Kendra (release owner), instructor, and team | Written agreement on the Chrome extension frontend requirement, release scope, named owners and acceptance criteria. | Issue #153 and the release docs now agree on Chrome MV3 + Render + Neon; PR #244's web experiment is marked abandoned. | **Open.** Instructor confirmation and team agreement are not recorded. |
| 2. Authenticated persistence and data isolation | Pending | Leyan and Andrei (extension flow), Trixia (backend/database), Kendra (coordination); confirm assignment | On the selected package/backend, demonstrate sign-in, create/list/read/update/delete, reload persistence, cross-user isolation, failure states, and cleanup using approved synthetic data. | PR #251 exact-head preflight reports Neon Auth mode and an anonymous `401 Bearer`. Seeded history was not checked. | **Open.** No installed-package live Auth journey, authenticated CRUD, isolation, writes or cleanup. |
| 3. AI behavior and release quality | Pending | Wilberr and team (evaluation); Kendra/Wilberr (provider and spend decision); confirm assignment | Approve source provenance, labels, split/overlap checks, intended model identity, quality thresholds, human explanation review, results and provider/spend limits. | Frozen English source-pair TF-IDF v12a result: 190/200 phishing recall (95%), 1/999 legitimate false positives (0.1%), 1,200 valid outputs; accepted only as advisory screening for that frozen cohort. The separate primary synthetic diagnostic detected 1/12. | **Open.** Contemporary-source qualification and human explanation ratings are missing; synthetic diagnostic remains weak; production provider status on the latest SHA needs probing. |
| 4. Failure handling and recoverability | Pending | Kendra (release lead); name the database restore operator and backup responder | Show controlled failure behavior; rehearse a compatible application rollback and Neon restore to an isolated branch; record measured RTO, RPO/data-loss window, and known-good app/config/schema identities. | Earlier staging-only recovery evidence is documented for a different SHA/environment. | **Open.** No current-production-compatible rollback or accepted isolated Neon restore; RTO/RPO not measured. |
| 5. Environment identity and security | Pending | Kendra (Render mapping), Trixia (database evidence); confirm service/database owner | Verify production/staging Render-to-Neon branch and role mapping, distinct targets, least-privilege grants, Auth/provider settings and GitHub secret scopes without exposing values. | PR #251 preflight names the staging Neon project/branch, report DB, runtime role, Auth DB and migration head. Render MCP confirms service identity but does not expose environment-variable values. | **Open.** Private Render connection-to-branch mapping, current production mapping, grants and secret access controls need owner verification before writes. |
| 6. Reviewed CI, exact candidate deployment and live behavior | Pending | Kendra (release owner); independent teammate reviewer to be named for the final candidate | One consolidated exact source/package/backend/model/Auth identity; effective required checks; independent approval; tagged source; automatic deploy of the same commit; exact-SHA health/readiness/provider and changed-feature smoke. | PR #255 was approved by EnviousCoal, its reported CI passed, it merged as `16f955321caf5dc368181be7ce5c00643750545d`, and Render deployed the same SHA via `new_commit`. Its hosted staging jobs were skipped. PR #251 staging package/backend is exact at `d6612c2`; PR #250 AI extension head is separate at `57fa2d5`. | **Open.** The PR #255 path proves same-SHA merge-to-deploy for a DevOps change, not product acceptance. No integrated candidate tuple; effective required-check list is not verified; exact-SHA feature smoke is missing; no version tag. |
| 7. Current documentation, metrics and real team records | Pending | Kendra (documentation), whole team (actual event records); confirm assignment | Keep setup/API/model/evaluation and release docs current; publish dated metrics with sample limits; capture actual Q&A, retrospective, standups and attendance; publish the release URL, tag and changelog for the verified release. | Issue #153, `PIPELINE.md`, environment map and release record were refreshed with current scope and deployment evidence. | **Open.** Documentation is partly current, but real participant records, instructor/team decisions, public release URL, tag and changelog are not evidenced. |

## Scoring rule to approve

1. Team and instructor confirm the category weights and whether criteria are
   binary or permit partial credit. The approved weights must sum to 100%.
2. Each area is `Pass` only when every required item in its pass-evidence column
   has a link or retained artifact tied to the same candidate identity. A plan,
   skipped job, unrelated green check, historical rehearsal or unverified
   endpoint is not a pass.
3. Calculate readiness as the sum of approved weights for passing areas divided
   by the total approved weights. Record the reviewer and date next to the
   result. Do not substitute issue closure counts or a course grade for this
   calculation.
4. Regardless of the percentage, keep release **NO-GO** while any required
   safety, identity, Auth/data-isolation, quality, deployment or recovery gate
   remains open.

## Current decision

No percentage is reported because the weights and scoring rule have not been
approved. The project is **not release-ready**: core acceptance areas 2–6 are
open. The exact staging Auth package/backend pair is a verification candidate,
not the consolidated final release candidate. See the
[current release record](release-record-2026-11-20.md) and
[environment map](environment-map-2026-11-20.md).
