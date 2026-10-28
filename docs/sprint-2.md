# Sprint 2 — independent work

October 20 Kendra implementation update: see the
[work/evidence and interface audit](devops/sprint-2-work-2026-10-20.md).
PR #52 is now merged through main; the CI guard and remote failure/repair drill
are delivered. PR #58 has since merged the persistent CRUD backend, and its
description records successful current-head Hosted staging and authorized
synthetic API CRUD verification. Issue #43's PostgreSQL acceptance tests are
now in a focused PR; local PostgreSQL evidence is recorded in
[the S2-T2 test handoff](s2-t2-test-handoff.md). That PR's CI and teammate
review remain pending. No issue, board card, or delivery gate is marked complete
by local results alone.

October 28 Trixia S2-T2 update: test changes are based on `main`
`b3a7588811e77edc48b29b07763152f66172a331` and committed as
`7ced6984ba5cdc962a756afd2ec642fbf274ec4d`. Against the disposable local
PostgreSQL database, targeted CRUD tests passed (35 passed, 1 intentionally
skipped), and the full DB-enabled backend suite passed (252 passed, 1 skipped).
The ordinary backend suite passed (216 passed, 37 skipped); Ruff and whitespace
checks passed. The skip is the separately gated seed-integrity test, which
requires local `phishlens_dev`. These are local results, not the new PR's CI.
Issue #43 remains open pending required review, CI, and checklist/board
reconciliation. The test-only change has not been deployed; deployed API CRUD
evidence is recorded separately under merged PR #58.

October 21 continuation: [playbook close-out and remaining gates](devops/playbook-closeout-2026-10-21.md).
PR #55 adds strict production-package permissions, reproducible artifact identity
and a measured staging download-cache experiment. Existing production evidence
is at main `149808e`; fresh public endpoint probes timed out, so current reachability
is not inferred from that historical observer run.

Planning updated October 19, 2026. Sprint: October 16–22; consultation October 22, time unconfirmed.

Project: [PhishLens — Sprint 2](https://github.com/users/kendshhh/projects/4)

## Assigned backlog

| Code | Owner | Issue |
| --- | --- | --- |
| S2-K1 | kendshhh | [#36: Audit carryover, prioritize Sprint 2 and record the shared contract](https://github.com/kendshhh/PhishLens/issues/36) |
| S2-K2 | kendshhh | [#37: Verify isolated environments and the extension delivery package](https://github.com/kendshhh/PhishLens/issues/37) |
| S2-K3 | kendshhh | [#38: Gate CRUD API tests on disposable PostgreSQL in CI](https://github.com/kendshhh/PhishLens/issues/38) |
| S2-K4 | kendshhh | [#39: Verify automatic main-to-production CRUD delivery](https://github.com/kendshhh/PhishLens/issues/39) |
| S2-K5 | kendshhh | [#40: Measure a pipeline improvement and verify recovery](https://github.com/kendshhh/PhishLens/issues/40) |
| S2-K6 | kendshhh | [#41: Prepare Consultation 2 evidence, sprint logs and requirements audit](https://github.com/kendshhh/PhishLens/issues/41) |
| S2-T1 | xxTrixia | [#42: Implement persistent CRUD endpoints and compatible schema](https://github.com/kendshhh/PhishLens/issues/42) |
| S2-T2 | xxTrixia | [#43: Prove CRUD persistence, validation and failure behavior](https://github.com/kendshhh/PhishLens/issues/43) |
| S2-L1 | inaki3023 | [#44: Build the complete injectable CRUD API client](https://github.com/kendshhh/PhishLens/issues/44) |
| S2-L2 | inaki3023 | [#45: Deliver replayable HTTP CRUD acceptance and real client integration](https://github.com/kendshhh/PhishLens/issues/45) |
| S2-A1 | JupitraxNeptuna | [#46: Build create, view, edit and delete screens independently](https://github.com/kendshhh/PhishLens/issues/46) |
| S2-A2 | JupitraxNeptuna | [#47: Verify installed-browser CRUD and public presentation acceptance](https://github.com/kendshhh/PhishLens/issues/47) |
| S2-W1 | EnviousCoal | [#48: Keep real/mock AI adapters compatible with CRUD and failure tests](https://github.com/kendshhh/PhishLens/issues/48) |
| S2-W2 | EnviousCoal | [#49: Document model suitability, backend smoke and Sprint 3 evaluation plan](https://github.com/kendshhh/PhishLens/issues/49) |

## Sprint 1 carryover

Existing issues are also on the Sprint 2 board; their previous evidence/state is retained.

- Leyan: [#7](https://github.com/kendshhh/PhishLens/issues/7), [#23](https://github.com/kendshhh/PhishLens/issues/23): contract, changed-record/browser-state and review evidence.
- Trixia: [#20](https://github.com/kendshhh/PhishLens/issues/20): contract acknowledgement and review.
- Wilberr: [#8](https://github.com/kendshhh/PhishLens/issues/8), [#21](https://github.com/kendshhh/PhishLens/issues/21): coordination/review and explicit model limitations.
- Closed Week 1 browser evidence gaps are checked in S2-A2; closed DevOps evidence gaps in S2-K2/K4/K6. Administrative closure is not proof of verification.

## Requirements coverage

| Instructor Sprint 2 requirement | Issues |
| --- | --- |
| All CRUD endpoints and request validation | #42, #43 |
| Related tables used in real features | #42, #43 |
| Create/view/edit/delete screens and real client | #44, #45, #46, #47 |
| Automated API tests in pipeline | #38, #43, #45 |
| Separate environments taking shape | #37 |
| Every main merge automatically deploys | #39 |
| Process, roles, standups, retro, consultation | #36, #41 |
| Metrics, measured optimization and recovery | #40 |
| AI contracts, controlled failures and eval preparation | #48, #49 |

## Working agreement

Kendra owns delivery infrastructure; Trixia owns backend CRUD/models/migrations/main.py; Leyan owns api.js and HTTP acceptance; Andrei owns popup/history rendering; Wilberr owns AI modules. Build/test against declared local substitutes immediately. After 30 minutes blocked, record missing boundary/owner and continue unaffected work. No substitute proves real PostgreSQL or deployed UI success.

Each issue lists acceptance criteria, exact file scope, reviewer/backup, independent start and evidence requirements. Independently ready is reviewable component work; integrated requires real neighboring components; delivered requires reviewed main, passing CI, automatic deployment and real verification. Board Todo does not claim anyone has started.

## Next sprint backlog

Sprint 3: real AI end-to-end and hosting suitability; held-out evaluation/results with source/license/leakage controls; model/preprocessing or prompt-change eval automation; scheduled guarded real smoke and failure simulation.

Sprint 4/final: resilience/security hardening; complete setup/API/schema/architecture/AI documentation; tagged release and changelog/public URL; demonstrated rollback; metrics trend/optimization evidence; slides and live deploy challenge rehearsal. All seven final requirements and product/docs/process/DevOps deliverables remain in S2-K1/K6 planning scope. Final items are not incorrectly declared Week 2 implementation gates.

## Evidence to collect

- [ ] Two or three real async standups: done, next, blocked.
- [ ] Retrospective: went well, did not, one next change.
- [ ] Real deployed create/read/update/delete, persistence, relationship and failure checks.
- [ ] Actual API tests in CI and main-SHA-to-live evidence.
- [ ] Updated metrics, optimization, runbook, incident and scope logs.
- [ ] Whole-team consultation; each member explains their own work and architecture.

Planning/board setup alone completes none of these delivery checkboxes. Authority: [CSP221A guide](https://csp221a.vercel.app/). API defaults and target dates are team recommendations.

