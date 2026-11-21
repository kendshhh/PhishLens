# Release readiness scorecard — 2026-11-21

**Decision: NO-GO. Score: NOT CALCULATED.** This is a delivery/release
scorecard, not a course grade. No completion percentage is valid until the team
and instructor approve the area weights and scoring rule. A criterion is a
full `Pass` only when its required evidence is complete and tied to one reviewed
candidate; partial evidence remains `Open`.

The seven areas continue the release gates in [issue #153](https://github.com/kendshhh/PhishLens/issues/153).
Owners listed below are proposed from prior handoffs and must be reconfirmed;
this document does not assign work by itself.

| Area | Pass evidence required | Evidence as of Nov 21 | Status / gap to close |
|---|---|---|---|
| 1. Product scope and acceptance ownership | Written team/instructor agreement on the Chrome MV3 release target, acceptance criteria and named owners. | Issue #153 and dated release records align on the extension + Render + Neon scope. | **Open (partial).** Instructor confirmation of the frontend requirement and team approval of final acceptance criteria are not recorded. |
| 2. Authenticated persistence and isolation | On the chosen package/backend, show sign-in, create/list/read/update/delete, reload persistence, cross-user isolation, failure behavior and cleanup with approved synthetic users. | GET-only staging smoke passed health, readiness and anonymous `401 Bearer` at about 08:35 UTC; 320 local Node tests pass for valid Bearer, wrong challenge, bounded transient history recovery, endpoint/status diagnostics and seeded-history validation. | **Open (partial).** No authenticated journey has run on the hosted candidate; the hosted CRUD runner still lacks an Auth session; isolation, persistence and cleanup remain unproven. The live smoke did not read or write reports. |
| 3. AI behavior and release quality | Approved evaluation cohort/provenance/labels/splits, pinned model identity, numeric thresholds, valid output and explanation review; safe provider/spend limits. | Frozen English source-pair TF-IDF v12a evaluation recorded 190/200 phishing recall (95%), 1/999 legitimate false positives (0.1%) and 1,200 valid outputs, accepted only as advisory screening on that cohort. A synthetic diagnostic detected 1/12. Production currently has analysis disabled. | **Open (partial).** Contemporary held-out evaluation, human explanation ratings and an approved broad release threshold are absent; production AI behavior is not enabled or accepted. |
| 4. Failure handling and recoverability | Compatible application rollback rehearsal and isolated Neon recovery; exact identities, measured end-to-end RTO and recoverable-point age/RPO, alert path and named primary/backup responders. | November 20 isolated restore verified schema and aggregate integrity for a small dataset; the temporary restored branch is distinct from production. | **Open (partial).** One-second provider branch-ready time is not service RTO; RPO is unmeasured; current app/config rollback compatibility, recovery responders and durable backup schedule remain unresolved. |
| 5. Environment identity and security | Privately verify staging and production Render-to-Neon project/branch/database/role mapping, distinct targets, Auth/provider settings, least privilege, dependency alerts and GitHub secret protections without exposing values. | Read-only Neon inspection confirms separate named staging/production branches, staging Auth origin, migration revision and grants. GitHub reports 15 open Dependabot alerts although observed `main` pins the first patched versions. | **Open (partial).** Reconcile the alert records against the default-branch dependency graph; private Render connection-to-branch mapping and secret scopes/permissions remain unverified. Render deploy trigger/config discrepancy is unresolved. |
| 6. CI, exact candidate deployment and live behavior | Effective required checks, independent review, one exact source/package/backend/model/Auth tuple, exact-SHA health/provider/feature smoke, browser acceptance, version tag and changelog. | Mainline Bearer-auth fix `06f89d7a0b5b9dec316dfa11f2846767a32086c5` is synchronized into candidate `14874d339bbb4042172df954f97596080aa303ee`. Local Node suite (320) and GET-only smoke passed. Pre-sync CI run 44883590782 and docs run 44884534992 passed. | **Open (partial).** GitHub CI for synchronized candidate `14874d339bbb4042172df954f97596080aa303ee` is pending. Hosted staging and preflight have not run; prior Secretary run 44884776725 required `needs-hosted-staging` and exact-head verification. No Render deployment or hosted Auth CRUD occurred; required-check settings remain unverified, as do integrated candidate, production observer, release tag and changelog. |
| 7. Current documentation, metrics and team records | Keep operations/API/model/release docs linked and current; provide bounded metric samples; retain actual dated team/instructor decisions, attendance, retrospective/Q&A and release records. | DevOps index, release record, environment map, failure evidence, runbook, metrics refresh, closeout prompt and linked project docs are reconciled on the review branch. Historical observations retain dates and sources. | **Open (partial).** Fourteen older references to absent benchmark companion artifacts in three summaries remain an evidence-packaging gap. Actual participant-sourced records, final instructor/team decisions, release tag and changelog are also absent. |

## Scoring rules to approve

1. The team and instructor approve area weights that sum to 100% and whether
   each area is binary or permits partial credit. Record the approvers and date.
2. Each criterion links a durable artifact or system record and names its exact
   candidate SHA/package/model/Auth/database identity. A plan, local patch,
   green unrelated check, skipped job, or old snapshot does not pass it.
3. Only then calculate the weighted result as passed weight divided by total
   approved weight. Identify the reviewer and evidence cutoff date.
4. Do not call the result `100%` unless every approved criterion passes. Keep
   the release **NO-GO** while any required safety, identity, Auth/isolation,
   quality, deployment or recovery gate is open, even if a future score is high.

At this audit cutoff, **0 of 7 areas meet their complete pass definition**; all
seven have partial artifacts or decisions still pending. This count is not a
percentage. See the [current release record](release-record-2026-11-21.md),
[environment map](environment-map-2026-11-21.md), and
[evidence index](README.md).
