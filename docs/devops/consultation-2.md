# Consultation 2 preparation

Issue: [#41](https://github.com/kendshhh/PhishLens/issues/41). Prepared October 21,
2026, Asia/Shanghai; consultation target October 22, time unconfirmed.
Source: [CSP221A course guide](https://csp221a.vercel.app/), read October 21.
This is a preparation record, not an attendance, rehearsal or acceptance record.
Code baseline: main `149808e3f76d9182688b5438153f57bd3cc03774`.

## Open before the consultation

- Production API: https://phishlens-api-ocvt.onrender.com/docs and `/version`.
- Installed extension: record package SHA, version, browser version and API target.
- [Sprint board](https://github.com/users/kendshhh/projects/4) and the sprint log
  proposed in [PR #55](https://github.com/kendshhh/PhishLens/pull/55).
- [Sprint PRs](https://github.com/kendshhh/PhishLens/pulls), [metrics](metrics.md),
  [optimization log](optimizations.md), [runbook](runbook.md), [incidents](incidents.md).
- [Pipeline stages and diagram](../../PIPELINE.md).

Wake the public API before presenting. Check the live SHA again immediately
before the demo. Shared staging may contain another PR: verify its exact SHA
before using it. Open only synthetic data; keep dashboards and secret fields
closed when screen sharing.

## Fifteen-minute agenda

| Time | Presenter / material | Observable result |
|---|---|---|
| 0–4 min | Backend, client and UI owners: deployed increment | Create synthetic record, list/detail, edit notes/feedback, refresh, delete and confirm absence; show relationship use. If unavailable, state the gap and show only actual deployed behavior |
| 4–7 min | Product-owner duty, proposed Kendra: board and sprint PRs | Planned/done/slipped, linked evidence, responsible owner and replan; distinguish open PRs from delivered work |
| 7–10 min | Kendra: pipeline, metrics, recovery | Source SHA → CI → automatic deploy → live version; explain DB-test gate, environment boundary and measured-cache limits |
| 10–12 min | Each affected owner: top risk and next sprint | API/client/UI compatibility risk, concrete mitigation and next increment |
| 12–15 min | Whole team: questions | Each person explains their own changes and architectural boundaries |

## Sprint 2 build and consultation audit

| Required build item | Owners / issues | Current evidence and remaining gate |
|---|---|---|
| All core CRUD endpoints and validation | Trixia #42/#43 | Current history API and non-saving analysis exist; full saved CRUD remains pending |
| Related tables used by real features | Trixia #42/#43; Andrei #46/#47 | Schema/seed relationship tests exist; demonstrate meaningful live feature use |
| Create/view/edit/delete screens | Leyan #44/#45; Andrei #46/#47 | Reviewed client #51 merged; installed-browser full CRUD remains pending |
| API tests in pipeline | Kendra #38; Trixia #43; Leyan #45 | #52 merged; 72 backend tests including actual PostgreSQL tests passed; register real CRUD IDs after owner merge |
| Separate environments taking shape | Kendra #37 | Production/staging and distinct DB endpoints verified; TLS required; privileges/Neon branch identity unverified |

The three consultation checks are API **and UI** CRUD (pending), API tests in CI
(existing tests demonstrated; CRUD coverage pending), and automatic deployment
(one exact-main delivery traced; do not infer every historical merge from one).

## Evidence available and slips to carry

| Evidence / slip | Identity or reason | Owner and replan |
|---|---|---|
| Main delivery | CI [39449001340](https://github.com/kendshhh/PhishLens/actions/runs/39449001340), observer [39449283551](https://github.com/kendshhh/PhishLens/actions/runs/39449283551), live SHA 149808e | Kendra: refresh against actual main before presenting |
| CI gate failure/repair | #52; intentional [39420764116](https://github.com/kendshhh/PhishLens/actions/runs/39420764116), repaired [39421062979](https://github.com/kendshhh/PhishLens/actions/runs/39421062979) | Kendra: explain missing required test fails even when pytest passes |
| Package/environment work | Open [#55](https://github.com/kendshhh/PhishLens/pull/55), head 18c60d3 at this snapshot | Kendra: finish latest-head checks, hosted acceptance and teammate review; not delivered yet |
| Full CRUD | Backend and UI integration not yet established on baseline | Trixia/Leyan/Andrei: complete #42–#47; Kendra then wires exact tests and delivery evidence |
| Cache improvement | n=2 before/after; install lower, whole-job average higher | Kendra #40: retain raw observations; collect a meaningful comparable improvement, no gain claim yet |
| Standups/retro/rehearsal | No actual team records supplied here | Actual participants: append dated evidence; never backfill invented events |

Next-sprint risk: AI/provider or serialization changes can break saved-record UI
while isolated tests pass. Mitigation: owners agree one real response/error
contract, exercise it through real HTTP and PostgreSQL, then installed Chrome;
keep provider calls mocked in normal CI and plan guarded real-AI evaluation.

## Actual process records to append

Retain two or three actual async standups with timestamp, author, original
message/permalink, done, next and blocked. A code commit is not evidence that a
standup happened. No standup entries are claimed by this document.

Retro, after the team holds it: date/participants, what went well, what did not,
and **one** agreed change with owner and next-sprint check. Pending.

Rehearsal, after it occurs: date, whole-team attendance, actual elapsed time,
tested source/package/deploy identity, steps/results, failed steps and owner for
each repair. Pending. Kendra should explain why CI uses disposable PostgreSQL,
why source/tested SHAs differ, why fixtures are insufficient, how stale staging
is detected, and why app rollback does not reverse schema/data writes.

Instructor record, after consultation: date, attendees, exact feedback, accepted
scope versus requested changes, follow-up issue/owner/date. Pending decisions:
PostgreSQL proposal change, useful AI feature scope and public extension demo
format. Do not label any of these instructor-approved without actual evidence.

## Remaining-sprint requirements backlog

These are proposed responsibilities and review gates, not completed work or new
instructor deadlines. Keep existing issue ownership; create further issues during
Sprint 3/4 planning once scope is agreed.

| Final requirement | Responsible owners | Remaining evidence / planned sprint |
|---|---|---|
| R1 persistent real-database CRUD | Trixia, Leyan, Andrei; Kendra delivery | #42–#47/#38/#39; refresh/redeploy persistence on confirmed synthetic target, Sprint 2 carryover |
| R2 useful AI with backend processing | Wilberr, Trixia | #48/#49; real end-to-end feature, validated/transformed/stored output, measured held-out evaluation, Sprint 3 |
| R3 backend-owned API/data/AI | Trixia, Wilberr, Leyan | Document real contracts and show frontend never calls DB/provider directly, Sprint 2–3 |
| R4 real backend data and UI states | Leyan, Andrei | #44–#47; real HTTP plus loading/empty/error and installed-browser results, Sprint 2–4 |
| R5 meaningful related entities | Trixia, Andrei | Relationship used by product, not just table count; live proof, Sprint 2 carryover |
| R6 environments and secrets | Kendra; each configuration owner | Complete .env.example, scoped host secrets, privilege/history audit and cost guards; close remaining gaps by Sprint 4 |
| R7 controlled malformed input/AI failure | Trixia, Wilberr, Leyan, Andrei | Mocked regression tests and safe replayable failure demonstration, Sprint 3–4 |

| Final submission group | Items that must remain on the backlog | Proposed coordinating owner |
|---|---|---|
| Product | Public tagged production URL; frontend/backend/migrations; complete value-free .env.example; local seed/setup | Kendra release; component owners supply sources/setup |
| Documentation | README with roles/stack/setup; architecture; schema; API reference; AI write-up/evaluation; release changelog | Component owners; Kendra checks inventory |
| Process | Board with sprint history; four plans and retros plus actual standups; scope log; slide deck; AI-failure simulation | Product-owner duty; all participants; Wilberr failure scenario |
| DevOps | Workflow config; PIPELINE.md/diagram; completed weekly metrics; measured optimization log; deploy/rollback runbook; incident postmortems | Kendra |
| Demo Day | 20-minute presentation plus 10-minute Q&A; production CRUD/AI, failure handling, reviewed visible-change deploy challenge and safe rollback readiness | Whole team; Kendra narrates delivery |

Before closing #41, attach actual process/rehearsal/consultation evidence, bring
the board current, pass required PR review/checks, and refresh this snapshot.
