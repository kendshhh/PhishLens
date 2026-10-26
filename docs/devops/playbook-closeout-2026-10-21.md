# DevOps playbook close-out — October 21, 2026

Local date: Asia/Shanghai. Linked Actions timestamps are UTC (October 20).
Current baseline: main `149808e3f76d9182688b5438153f57bd3cc03774`.
Work branch: `ci/37-40-delivery-verification`; PR #55. No production writes,
model calls, infrastructure changes, rollback or teammate sign-off performed.

## Correct source versions

- Week 1: original 39-page `PhishLens_Week_1_Team_Playbook.pdf` in Downloads;
  SHA-256 `e1b3686032cc0df39b700b8ad529e13c1f3bbc22005b3f0d8366a60ffc7b2365`.
  Its MySQL/Railway instructions are historical and superseded by the recorded
  PostgreSQL/Neon decision. Instructor notification remains unverified.
- Week 2: October 19 **verified independent-work** revision, 12 pages,
  `output/pdf/PhishLens_Week_2_Verified_Independent_Work_Playbook.pdf`;
  SHA-256 `52ad96fe35e7bcc3bd44c511319418958c528f5e96d907441e2c3ba23fe01507`.
  Kendra's instructions are on page 3. The October 19 original-format expansion
  (29 pages) repeats this independent assignment and supplies the daily sections.
  The older 36-page `PhishLens_Week_2_Team_Playbook.pdf` is not used as the current
  task allocation or implementation baseline.

The corrected Week 2 guide says to improve current CI, packaging, environment
configuration and delivery evidence independently, then add real backend CRUD
tests after their owner's merge. Fixtures and prepared artifacts do not establish
connected delivery. Review, actual team events and instructor acceptance stay
separate from automation.

## Week 1 carryover and Week 2 ownership

| Area | Evidence / work completed | Remaining gate and owner |
|---|---|---|
| W1 K1–K4 setup, workflow, reproducibility | Existing reviewed repository foundation, locks and PR workflow retained; current .env.example distinguishes active/proposed variables | Own-account access attestations and shared-contract acknowledgement belong to actual owners |
| W1 K5/K7 hosting, protection, delivery | Existing production, four-check protection history and automatic observer reused; current main reports protected; #51 has Trixia approval on its final reviewed head | Current protection-settings API returns 403; private settings are not inferred from passing CI |
| W1 K6 / W2 CI (#38) | #52 merged; required real PostgreSQL test IDs, preflight, reports and intentional failed/repaired remote runs exist | Register actual persistent CRUD test IDs once #42/#43 merge; existing history tests are not full CRUD |
| W1 K8 / W2 inventory (#36/#41) | Sprint ownership, requirements map, carryover, interfaces and gaps documented | Real standups, retrospective, team rehearsal and instructor acceptance cannot be reconstructed |
| W2 packaging/environments (#37) | Strict production hosts, verified ZIP identity, 52 script/123 extension tests; bounded history scan triaged below; ignore checks confirmed | Review/latest CI, private DB branch/role separation and hosting secrets remain pending |
| W2 deployment (#39) | Main CI 39449001340 and production observer 39449283551 succeeded for 149808e | New independent version probes timed out; real persisted CRUD and browser workflow depend on backend/UI owners |
| W2 measurement/recovery (#40) | Comparable cache experiment and schema-aware recovery runbook retained | No established whole-pipeline improvement; historical recovery duration remains unknown |

## Interfaces and requirements (#36/#41)

Goal: persistent create/list/detail/update notes-feedback/delete through Chrome
and PostgreSQL, actual DB API tests in CI, automatic reviewed-main deployment,
and documented environment separation. Consultation is planned for October 22,
time unconfirmed. Kendra's product-owner duty remains proposed, not instructor
acceptance. Existing formal roles/owners are retained in docs/sprint-2.md.

Current main: GET /api/analyses returns `{items: [...]}` for a server-selected
synthetic demo account; POST /analyses classifies without saving. Text input is
nonblank, at most 30,000 chars; optional subject/sender at most 320. Proposed
saved CRUD under /api/analyses belongs to #42/#43. The merged #51 client now
preserves spam, nullable feedback, evidence and provenance, with tests for agreed
input/timeout handling. The older work log's claim that it rejects spam is stale.
Do not replace reviewed limits with older playbook defaults silently.

Top risk: the database-backed CRUD API and UI are still unfinished; delivery
automation cannot substitute for them. Trixia owns API/schema/tests (#42/#43),
Leyan real HTTP client composition (#44/#45), Andrei UI/browser (#46/#47), Wilberr
AI output contracts (#48/#49); Kendra wires their actual tests and traces delivery.
The exact saved-record serializer/error/provenance choices need owner agreement.

Sprint 2 mapping: CRUD/validation/related tables → #42/#43; real UI/client →
#44–#47; actual API tests → #38/#43/#45; environments → #37; automatic deployment
→ #39; process/consultation → #36/#41; metrics/recovery → #40. Sprint 3 retains
real AI/provider/capacity and held-out evaluation; Sprint 4 retains resilience,
security, complete API/schema/architecture/AI/setup docs, tagged release/changelog,
public demonstration, slides, metrics trends and rollback evidence.

## Package evidence and installation (#37)

Run `npm ci`, `npm run lint`, `npm test`, `npm run validate`, `npm run package`.
Use `npm.cmd` on Windows if PowerShell blocks npm.ps1. No global policy change is
required. CI artifact `PhishLens-Extension` now contains the inner extension ZIP
and sidecar `evidence.json`; the sidecar does not enter the installable package.

Compare `source_commit` (PR head/main source), `tested_commit` (GitHub merge
revision on PRs), `archive_sha256`, version and per-file hashes. Local modified
runtime/packaging inputs are explicitly identified. Extract the inner ZIP to a
folder whose root contains manifest.json; Chrome Load unpacked selects that
folder. Never select `output/pdf`. Close/reopen and reload the extension; record
browser version, exact artifact/backend identity and observed errors/states.
An old 0.1.0 installation is not fresh acceptance of PR #55.

## Environment boundary (#37)

| Target | Public endpoint | Configuration / verification |
|---|---|---|
| Local/CI | localhost | Explicit disposable PostgreSQL 17 and mock AI; no cloud fallback |
| Staging | https://phishlens-staging.onrender.com | Protected staging environment, RENDER_STAGING_API_KEY, STAGING_BASE_URL, RENDER_STAGING_SERVICE_ID; private development DATABASE_URL / STAGING_DATABASE_HOST |
| Production | https://phishlens-api-ocvt.onrender.com | Runtime DATABASE_URL; observed main-to-production automation; secrets remain backend-only |

Read-only inspection of the PhishLens Render workspace verified different staging
and production database endpoints, with `sslmode=require` on both. The role names
are identical and owner-style; distinct endpoints do not prove least privilege or
separate Neon role policies. No role/secret configuration was changed. A browser
snapshot exposed a connection value during inspection; it is excluded from these
files and GitHub updates. Subsequent comparison returned sanitized booleans only.
See [fresh hosted evidence](evidence/2026-10-21-hosted-verification.json).

Bounded [remote-history audit](evidence/2026-10-21-history-audit.json): all 298
unique text blobs reachable from fetched origin refs were scanned; no binary or
oversized blobs were skipped. No private .env path or recognized model-weight
extension was found. Three credential-pattern matches were triaged: two synthetic
test URLs targeting invalid/example hosts, and one bracketed password placeholder
in a historical .env.example. Matching values were never logged. This pattern
scan does not guarantee absence of every credential/private email and does not
audit host-side secrets or unfetched/deleted remote history.

## Actual delivery evidence and limitations (#39/#40)

[Main CI](https://github.com/kendshhh/PhishLens/actions/runs/39449001340) and
[production observer](https://github.com/kendshhh/PhishLens/actions/runs/39449283551)
succeeded for main 149808e. The observer verifies exact SHA, health/readiness and
records deploy identity/timing; artifact `Veriqo-Production-Evidence` ID 12276999746
was published. #51's final reviewed head e538a1c has Trixia approval
[5587131601](https://github.com/kendshhh/PhishLens/pull/51#pullrequestreview-5587131601).
That proves this PR's review, not universal review compliance.

Earlier shell probes timed out. Fresh browser reads subsequently returned the
production version `149808e3f76d9182688b5438153f57bd3cc03774`, healthy service,
ready/connected database and saved synthetic history. These are response-body
observations, not captured HTTP status assertions or full CRUD acceptance.
Render confirms automatic `new_commit` deployment `dep-dbbois67bikc73b06fpg`
for the same SHA, live at 2026-10-20T15:33:17.294784Z. Relative to the merge commit
timestamp 15:30:13Z, this sample's merge-to-live time is 184.294784 seconds.
No CRUD operation was performed against either hosted database. Run guarded real
HTTP acceptance after backend merge and confirm safe persistence/restart evidence.

No new rollback is necessary for a CI/package-only PR. Reuse the October 14
drill; see runbook/incidents. A rollback does not reverse schema or external writes.
The current source has only 0001_initial_schema; private live revision remains a
separate check. Unknown recovery/failed-deployment counts are not zero.

PR #55 is now ready for review. Source head a316653 passed Backend checks,
Extension checks and Staging integration in run 39454875889; Hosted staging is
pending. Required staging environment approval and exact-head acceptance remain
human gates. Latest-head checks after documentation updates remain authoritative.

## Human evidence still required (#41)

Collect two or three real done/next/blocked standups, a retrospective, owner
contract acknowledgements, required PR review, whole-team 15-minute rehearsal and
instructor approval of scope/extension presentation. The issue bodies and records
may be updated with supplied evidence; these activities are not marked complete
from code, package hashes, fixtures or administrative closure.
