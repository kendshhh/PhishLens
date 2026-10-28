# Kendra — Week 1–4 DevOps closeout

Snapshot captured 2026-10-28 17:07 UTC (2026-10-29 01:07 GMT+8). This records
Kendra's work only against the official [CSP221A project guide](https://csp221a.vercel.app/),
the sprint workbook, repository evidence, and Kendra's GitHub issues. Week 4
remains a proposed sequence with no agreed dates or dedicated issues. This is
not team, instructor, release, or course acceptance.

## Current delivery evidence

- Main and production remain on `6414914dfa8eb8322839597c4cd6912145a442a0`.
  The recorded main CI and Workflow lint passed; Render production was Live on
  that SHA and its read-only version, health, and readiness checks passed on
  October 28. Production CRUD persistence is not established.
- PR [#86](https://github.com/kendshhh/PhishLens/pull/86) remains open at head
  `aa91511c7eb0c43b8d52eb3adc26ac607a537293`. Its component, isolated staging,
  migration/workflow preflights, CodeQL, Analyze, and Hosted staging checks
  passed. Dependency Review was skipped because the old workflow required an
  opt-in repository variable.
- Render staging deployment
  [`dep-dbh2cjnf3r2c73emoprg`](https://dashboard.render.com/web/srv-db92irlg1s2s739404i0/deploys/dep-dbh2cjnf3r2c73emoprg)
  is Live on exact merge SHA `d46cc09ecf7258a6bd10475f00cc8da035ef5e9a`.
  Read-only GETs at 17:07 UTC returned HTTP 200 for `/version`, `/health`, and
  `/ready`; version identified that SHA and `staging`, and readiness reported
  the database connected. This verifies the hosted gate, not write acceptance.
- The confirmed Neon target is `pr-58-staging/phishlens_dev`. A read-only check
  at 17:05 UTC still found `CREATE` on the `public` schema and write/delete
  privileges on `alembic_version`, `analyzed_emails`, and `users` for
  `phishlens_staging_app`. The role therefore exceeds the documented runtime
  minimum. No grants were changed and no staging or production CRUD write was
  run. The owner must remove excess grants and recheck before the guarded
  staging CRUD acceptance in the runbook.

## Kendra's task status

| Week | Kendra rows | Status | Verified Kendra work | What remains |
|---|---|---|---|---|
| 1 | W1-D1, W1-D2 | Verified | Repository/backlog foundation, CI and delivery path, runbook and evidence are recorded in merged work. | Later integrated product and real-model evidence belongs to component owners and carryover issues. |
| 1 | W1-D3 | In progress | Source-to-CI-to-production trace, dated metrics, risks, and recovery documentation are recorded. | Actual consultation/retrospective feedback and attendance must come from the real event; no record was supplied. |
| 2 | W2-D1, W2-D2 | Verified | Sprint ownership/contract audit and disposable PostgreSQL CI gate are merged; #38 is closed. | Keep API/UI/model owner decisions separate from DevOps evidence. |
| 2 | W2-D3 | In progress | Package identity and environment mapping are documented; PR #86's exact hosted staging candidate is live and healthy. | Environment owner removes excess grants; repeat the least-privilege read; install/verify exact package in Chrome; finish privacy/history classification. |
| 2 | W2-D4 | In progress | Exact-SHA staging delivery passed. Cache experiments were compared and removed because neither showed whole-job improvement. | A comparable end-to-end optimization and a complete safe recovery duration are not evidenced. Production persistence also remains unverified and requires an approved synthetic target. |
| 2 | W2-D5 | Complete for evidence preparation | Current status, risks, issue notes, and consultation preparation were refreshed. | Real standups, retrospective, rehearsal, attendance, and instructor feedback remain event-dependent. |
| 3 | W3-D1 | Verified | Carryover, current main/staging trace, and issue ownership were audited. | Product-side real report/evaluation work remains with its owners. |
| 3 | W3-D2 | In progress | Pinned, weight-free mock CI and deterministic checks pass. This PR now changes dependency review to run by default when the repository variable is unset. | Fresh PR checks must confirm the new advisory job. Runtime coordination and exact installed-Chrome acceptance remain open. |
| 3 | W3-D3 | In progress | Staging identity and model/production separation are documented. | Real-provider evaluation, frozen cases, and owner-supplied model revision/results are not available to Kendra to invent or sign off. |
| 3 | W3-D4 | In progress | Pipeline timing and cache comparisons are documented with sample sizes and limitations; the historical October 14 drill is retained. | No whole-pipeline gain is established; full recovery duration and a new compatible safe rehearsal remain open. Do not disrupt shared staging or production to fill a metric. |
| 3 | W3-D5 | In progress | Evidence pack is prepared. | Actual consultation, team decisions, attendance, and instructor feedback must be recorded after they occur. |
| 4 | W4-D1–D5 | Not started | A proposed sequence is present in the sheet. | The team must agree dates/scope and create or assign Week 4 issues. Kendra's release, gates, documentation, candidate, metrics, and closeout steps can start once those inputs and owner evidence exist. |

## Remaining Kendra-owned actions, in order

1. **Environment gate (#37):** have the environment owner remove unnecessary
   staging runtime grants and repeat the read-only verification. Then use the
   authorized exact-SHA guarded synthetic CRUD check, retaining cleanup
   evidence. Install the matching artifact in Chrome only when its package/SHA
   is identified and the browser session is available.
2. **Fresh CI/PR evidence:** push the advisory-by-default workflow adjustment
   in this PR and confirm the new-head `Dependency review (advisory)` result.
   Keep it advisory and read-only. Obtain current teammate review before merge;
   do not merge on automated checks alone.
3. **Delivery/recovery (#39/#40):** keep production read-only until an approved
   synthetic target exists. Record a comparable whole-pipeline improvement only
   if measurements support it; record recovery duration during the next
   necessary safe recovery or an owner-approved staging rehearsal.
4. **Coordination (#36/#41):** record actual owner acknowledgements, scope
   decisions, consultation, rehearsal, and feedback when participants provide
   them. Do not fabricate attendance, approvals, or meeting outcomes.
5. **Week 4:** agree dates/scope at kickoff, create/assign the release issues,
   then update the proposed day rows and execute release coordination,
   environment/gate review, documentation, exact-SHA candidate verification,
   and final metrics/retrospective against the official rubric.

## Evidence links

- [Kendra's backlog audit](backlog-audit-2026-10-28.md)
- [Staging gate and grant verification](staging.md)
- [Deployment/recovery runbook](runbook.md)
- [Pipeline metrics](metrics.md) and [optimization log](optimizations.md)
- [CI maintenance](ci-maintenance.md)
- [Weekly and Daily Sprint Task Plan](https://docs.google.com/spreadsheets/d/18ppxRcZEK6mBNyZMQkZwFTLlmMyS9WHnRRoUKiPCe58/edit?gid=774483955#gid=774483955)
