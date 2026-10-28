# Week 2 audit and professor reporting script

Prepared October 21, 2026, Asia/Shanghai. Week 2 planning period: October 16–22.
Consultation target: October 22; actual time remains unconfirmed. This document
prepares a report; it is not evidence of attendance, rehearsal or acceptance.

## Audit conclusion

DevOps has a merged database-test evidence gate and two tested follow-up PRs.
The team's full persistent API/UI CRUD increment is not yet verified. Report
implementation, integration and production delivery separately. Passing component
checks does not establish hosted staging, installed Chrome or formal review.

Fresh GitHub snapshot:

| Area | Actual status | What to tell the professor |
|---|---|---|
| #36 sprint/contract coordination | Ownership and interface audit recorded; issue open | Planning exists; component-owner agreement and acceptance still need evidence |
| #37 package/environment | #55 open at 040bfdb; three automatic checks passed; hosted staging pending | Package identity/restricted hosts are tested; browser and private environment acceptance remain incomplete |
| #38 PostgreSQL CI gate | #52 merged; #38 still open | Gate is delivered; it requires known real database tests, not just a successful pytest exit. Full CRUD test registration follows backend integration |
| #39 production CRUD delivery | Retained main 149808e delivery trace; issue open | Automatic delivery has recorded evidence; new full CRUD delivery is not yet demonstrated |
| #40 optimization/recovery | Cache measurements retained; #57 draft; issue open | Report the measurements honestly. No established whole-job speedup or new recovery-time claim |
| #41 consultation/process | #56 open; #57 supports reporting; issue open | Preparation exists; actual standups, retro, rehearsal and instructor feedback require participants |
| Backend CRUD #42/#43 | Issues open; no verified integrated CRUD result in this audit | Trixia owns API/schema/persistence acceptance |
| Client #44/#45 | Issues open; earlier #51 client merge retained in consultation notes | Leyan owns client and actual HTTP acceptance; a merged client alone does not establish deployed CRUD |
| UI/browser #46/#47 | Issues open; full installed-browser CRUD evidence unavailable | Andrei owns screens and browser acceptance |
| AI #48/#49 | Issues open; #50 backend boundary PR also open | Wilberr/Trixia own compatible processing and failure contracts; do not claim real AI quality from mocks |

Open issues are not proof that no work exists. This audit identifies acceptance
evidence, not a judgment about a teammate's effort. No grades are predicted.

## Work timeline to show

Dates below are local dates, not invented meeting/standup records.

| Date | Development/evidence milestone | Status |
|---|---|---|
| Before Week 2 | Existing production backend, database readiness and October 14 rollback drill | Reused foundation; do not count the drill as newly performed this week |
| October 19 | Revised independent-work playbook sets component ownership and no-wait work | Planning baseline |
| October 20 | CI gate failure/repair exercised; #52 merged at 22:59 local | Merged DevOps work; missing required DB tests cannot silently pass |
| October 21 | #55 follow-up verifies source/tested revisions, exact package contents and hashes before artifact upload | Head 040bfdb; automatic checks pass; hosted staging/review pending |
| October 21 | #56 prepares Consultation 2 evidence and requirements audit | Open, not delivered through main |
| October 21 | #57 adds offline metrics-to-report command independently of #55 | Head f67a8a3; automatic checks pass; draft |
| Before consultation | Team reviews, exact-SHA hosted testing, installed Chrome, actual process records and joint rehearsal | Planned next actions; not yet completed |
| After reviewed feature integration | Register actual CRUD tests; verify synthetic create/list/detail/update/delete and persistence; trace main to production | Dependency-based follow-up; do not promise completion without owner agreement |

## Evidence tabs to open

1. #52: https://github.com/kendshhh/PhishLens/pull/52
2. Intentional CI gate failure: https://github.com/kendshhh/PhishLens/actions/runs/39420764116
3. Repaired run: https://github.com/kendshhh/PhishLens/actions/runs/39421062979
4. #55: https://github.com/kendshhh/PhishLens/pull/55
5. #55 current CI: https://github.com/kendshhh/PhishLens/actions/runs/39521541137
6. #56: https://github.com/kendshhh/PhishLens/pull/56
7. #57: https://github.com/kendshhh/PhishLens/pull/57
8. #57 CI: https://github.com/kendshhh/PhishLens/actions/runs/39522153467
9. Recorded main CI: https://github.com/kendshhh/PhishLens/actions/runs/39449001340
10. Recorded production observer: https://github.com/kendshhh/PhishLens/actions/runs/39449283551

#55's current run passed 72 backend tests and 67 deployment-script tests; extension
checks verified the 10-file production package. Hosted staging is pending.
#57 passed backend, extension and isolated staging, with 58 deployment-script
tests. Hosted staging was skipped because it is draft. These counts belong to
different branches and must not be added together as unique test coverage.

Keep the source JSON and matching SHA/run visible. Production identity and shared
staging identity must be refreshed immediately before a live demonstration.

## Suggested fifteen-minute team consultation

| Minute | Speaker and activity |
|---|---|
| 0–4 | Component owners demonstrate the actual deployed increment. Attempt full synthetic CRUD only if verified. Otherwise show working behavior and explicitly state the missing acceptance |
| 4–7 | Sprint coordinator shows planned/done/slipped items, evidence, owners and replanned scope. Kendra's product-owner duty remains proposed unless the team confirms it |
| 7–10 | Kendra presents the pipeline, one gate failure/repair, measurements and recovery limits |
| 10–12 | Owners explain the top integration risk, mitigation and next increment |
| 12–15 | Questions and actual instructor feedback; record resulting actions/owners |

This agenda follows the retained verified playbook. The course website could not
be refreshed in this audit; confirm any instructor-announced changes directly.

## Kendra's approximately three-minute script

**0:00–0:30 — scope and result**

“My role is DevOps. This week I focused on making our database checks enforceable,
our extension packages traceable, and our delivery evidence reproducible. The
database evidence gate is merged through PR 52. The package work in PR 55 and
the reporting tool in draft PR 57 have passed their automatic checks, but they
have not been merged. Full product CRUD acceptance remains pending.”

**0:30–1:15 — show the real database gate**

Open #52 and its failure/repair runs.

“CI starts a disposable PostgreSQL database, applies migrations and repeats the
seed. It runs the API suite and checks that specific real database tests actually
passed. This matters because pytest can succeed while a required database test
is skipped or disappears. I demonstrated that failure condition and repaired it.
Normal CI uses mocked AI so it does not depend on provider availability or spend
provider quota. Once the reviewed CRUD tests land, I will register their actual
test IDs rather than presenting the current tests as complete CRUD coverage.”

**1:15–1:50 — show package and delivery identity**

Open #55's CI and package verification step.

“The package includes a separate evidence file containing the source commit,
tested commit, extension version and hashes. The new check rejects a stale source,
unexpected files or permissions, and altered archive contents before upload.
This proves consistency with the CI evidence; it does not prove Chrome behavior.
Hosted staging and manual Chrome verification are still pending, followed by
formal teammate review. I have kept those gates in place.”

**1:50–2:25 — report the measurements honestly**

“The cache experiment has two before and two after samples. Average installation
time went from nine to seven seconds, but whole staging jobs went from 40.5 to
44 seconds. I therefore cannot claim an overall pipeline speedup. The retained
production evidence includes one merge-to-live sample of about 3.07 minutes.
That is one delivery observation, not an optimization comparison. PR 57 makes
the existing observer metrics easier to report while keeping unknown values
explicit.”

**2:25–3:00 — explain the gap and next action**

“Our main remaining integration gap is persistent CRUD through the API and
installed extension. Trixia owns persistence/API tests, Leyan the real HTTP/client
integration, and Andrei the UI/browser flow. My next step is to connect their
reviewed tests to CI, verify the intended synthetic target, and trace the reviewed
main commit through automatic deployment and changed behavior. Private database
privileges and secret scope also need verification. I am reporting these as open
acceptance items rather than completed work.”

## Questions to rehearse

**Why use a disposable database?**
It exercises migrations, queries and persistence without modifying hosted data;
each CI run starts with an isolated target.

**Why can source and tested SHA differ?**
GitHub may run component tests on a generated PR merge revision. The source SHA
identifies the submitted head; the tested SHA identifies what CI executed.

**Does a green pipeline prove the application works?**
It proves the configured checks passed. Hosted identity, real HTTP integration,
installed Chrome and persistent CRUD need their own evidence.

**Why are PRs still open?**
“Automatic checks are ready, but the required human review and hosted acceptance
are not complete. I continued independent metrics work while retaining the gates.”
Avoid blaming unavailable teammates or saying their approval is unnecessary.

**What improved?**
The enforced DB-test evidence and package traceability improved verification.
Installation was lower in a small sample; a whole-pipeline speed gain is unproven.

**What if a deployment fails?**
Inspect the exact failed deployment, confirm the known-good app/schema pair,
use the reviewed recovery procedure, and verify live SHA, health and affected
behavior. Application rollback does not undo database migrations. The retained
October 14 rollback drill succeeded, but full restoration duration is unknown.

**Did AI assistance do this?**
“I used Codex assistance to prepare implementation and evidence. I remain
responsible for understanding the changes and explaining what the tests prove.”
Use this wording only if you can actually explain and reproduce the work.

## Before/after the meeting

Before: confirm the actual consultation time; review the script with the team;
refresh CI and live SHAs; prepare a synthetic-only demo; attach actual standups,
retro and board updates; record a real timed rehearsal. The Week 1 report replay
is historical, so do not label its 87.88% success rate as fresh Week 2 metrics.

After: record date, attendance, actual demonstrated SHA, instructor feedback,
scope decisions, follow-up owner and agreed target. Confirm the PostgreSQL scope
change, useful AI feature and public extension-demo format if still unresolved.
Do not turn a proposed plan into an instructor-approved decision.
