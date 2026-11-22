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
| 2. Authenticated persistence and isolation | On the chosen package/backend, show sign-in, create/list/read/update/delete, reload persistence, cross-user isolation, failure behavior and cleanup with approved synthetic users. | Staging `/api/analyses` correctly returns `401 Bearer` anonymously. The workspace runner now implements two-account Auth and cross-user isolation; the local Auth database variable matches the existing GitHub variable name. | **Open (partial).** A reported hosted candidate failed sign-in and downstream CRUD/persistence/isolation/cleanup checks. The local correction is unmerged and has not passed hosted or browser acceptance. |
| 3. AI behavior and release quality | Approved evaluation cohort/provenance/labels/splits, pinned model identity, numeric thresholds, valid output and explanation review; safe provider/spend limits. | Frozen English source-pair TF-IDF v12a evaluation recorded 190/200 phishing recall (95%), 1/999 legitimate false positives (0.1%) and 1,200 valid outputs, accepted only as advisory screening on that cohort. A synthetic diagnostic detected 1/12. Production currently has analysis disabled. | **Open (partial).** Contemporary held-out evaluation, human explanation ratings and an approved broad release threshold are absent; production AI behavior is not enabled or accepted. |
| 4. Failure handling and recoverability | Compatible application rollback rehearsal and isolated Neon recovery; exact identities, measured end-to-end RTO and recoverable-point age/RPO, alert path and named primary/backup responders. | November 20 isolated restore verified schema and aggregate integrity for a small dataset; the temporary restored branch is distinct from production. | **Open (partial).** One-second provider branch-ready time is not service RTO; RPO is unmeasured; current app/config rollback compatibility, recovery responders and durable backup schedule remain unresolved. |
| 5. Environment identity and security | Privately verify staging and production Render-to-Neon project/branch/database/role mapping, distinct targets, Auth/provider settings, least privilege and GitHub secret protections without exposing values. | Read-only Neon inspection confirms separate named staging/production branches, staging Auth origin, migration revision and grants. Render service metadata and health probes identify the services. | **Open (partial).** Private Render connection-to-branch mapping and current secret scopes/permissions have not been verified. Render deploy trigger/config discrepancy is unresolved. |
| 6. CI, exact candidate deployment and live behavior | Effective required checks, independent review, one exact source/package/backend/model/Auth tuple, exact-SHA health/provider/feature smoke, browser acceptance, version tag and changelog. | Production is live at `811980c`; staging's last recorded deploy is `ba0b6c5`; checksums/identities are documented. A later reported hosted product candidate at `279b0a514620c1d7839da3cbb4bd57f2c58f670d` on `br-broad-feather-b3261w7l` failed sign-in and downstream product checks. | **Open (partial).** Current effective required checks and a fresh integrated candidate run are unverified; the local correction is unmerged, the candidate failed, and no installed browser acceptance or tag exists. |
| 7. Current documentation, metrics and team records | Keep operations/API/model/release docs linked and current; provide bounded metric samples; retain actual dated team/instructor decisions, attendance, retrospective/Q&A and release records. | Current DevOps index, release record, environment map, failure evidence, runbook, metrics refresh and prompt are prepared in the workspace. Historical records are marked as snapshots. | **Open (partial).** This refresh is uncommitted workspace evidence; no actual participant-sourced records, final instructor/team decisions, release tag or changelog are evidenced. |

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
