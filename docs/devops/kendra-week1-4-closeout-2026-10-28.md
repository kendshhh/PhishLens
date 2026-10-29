# Kendra — Week 1–4 DevOps closeout

Snapshot captured 2026-10-29 00:31 UTC (2026-10-29 08:31 GMT+8). This records
Kendra's work only against the official [CSP221A project guide](https://csp221a.vercel.app/),
the sprint workbook, repository evidence, and Kendra's GitHub issues. Week 4
remains a proposed sequence with no agreed dates or dedicated issues. This is
not team, instructor, release, or course acceptance.

## Pull-request checklist refresh — October 29, 2026

The repository had 2 open PRs and 59 closed PRs at the October 29 refresh. PR [#86](https://github.com/kendshhh/PhishLens/pull/86)
merged at 00:11 UTC on October 29. The open PRs are [#59](https://github.com/kendshhh/PhishLens/pull/59)
and [#61](https://github.com/kendshhh/PhishLens/pull/61). Use the
[current issue-to-PR checklist](week2-finish-checklist.md)
for linked issues and current open/merged states.

## Current delivery evidence — October 29, 2026 00:31 UTC

- PR [#86](https://github.com/kendshhh/PhishLens/pull/86) merged at 00:11 UTC
  as `1344fcb061272bac93ced5911f1ab8fbb3b6785d`. Production deploy
  [`dep-dbh8v6ivcj2c73fql7c0`](https://dashboard.render.com/web/srv-db7eap25b2lc73fkelpg/deploys/dep-dbh8v6ivcj2c73fql7c0)
  is Live on that commit. At 00:31 UTC, `/version`, `/health`, and `/ready`
  returned HTTP 200; the version matched production and the merge commit, and
  readiness reported the database connected. Production saved-record CRUD
  persistence is not established; no production write was made.
- Render staging deployment
  [`dep-dbh8s8942hec73bo7bt0`](https://dashboard.render.com/web/srv-db92irlg1s2s739404i0/deploys/dep-dbh8s8942hec73bo7bt0)
  is Live on candidate SHA `fc7db9bf5441af4cd68ec2efbcbc7ac8efdc20a2`. Read-only
  `/version`, `/health`, and `/ready` returned HTTP 200 and reported staging,
  that exact SHA, and a connected database. The target is Neon
  `pr-58-staging/phishlens_dev`.
- The staging runtime role was corrected on that branch: table ownership now
  belongs to `neondb_owner`; `phishlens_staging_app` has only CRUD privileges
  on `users` and `analyzed_emails`, schema `USAGE`, and database `CONNECT`. It
  cannot create objects in `public` or access `alembic_version`; extra table
  privileges were removed. The default `PUBLIC` TEMPORARY privilege remains
  unchanged for all logins on this isolated staging database.
- The already authorized exact-SHA guarded verifier passed against staging
  candidate `fc7db9b`. It created, listed, read, edited, cleared, deleted, and
  verified absence of a single synthetic record; cleanup completed. No
  production write was made. Full evidence is in [staging.md](staging.md).
- The matching `PhishLens-Staging-Extension` artifact is available from
  [workflow run 40736903885](https://github.com/kendshhh/PhishLens/actions/runs/40736903885)
  for PR head `3abad4309b2976e7390937c8f8f54e60aee8f6dc`. Its ZIP digest and
  embedded evidence were verified; the manifest is `Veriqo STAGING PR 86`
  version `0.1.0`, with only the staging host permission. Exact installed-Chrome
  behavior remains unverified.

## Kendra's task status

| Week | Kendra rows | Status | Verified Kendra work | What remains |
|---|---|---|---|---|
| 1 | W1-D1, W1-D2 | Verified | Repository/backlog foundation, CI and delivery path, runbook and evidence are recorded in merged work. | Later integrated product and real-model evidence belongs to component owners and carryover issues. |
| 1 | W1-D3 | In progress | Source-to-CI-to-production trace, dated metrics, risks, and recovery documentation are recorded. | Actual consultation/retrospective feedback and attendance must come from the real event; no record was supplied. |
| 2 | W2-D1, W2-D2 | Verified | Sprint ownership/contract audit and disposable PostgreSQL CI gate are merged; #38 is closed. | Keep API/UI/model owner decisions separate from DevOps evidence. |
| 2 | W2-D3 | In progress | PR #86's protected staging gate passed; the post-merge staging candidate is live and healthy; the Neon runtime grants now pass the read-only least-privilege check; exact-SHA synthetic staging CRUD passed with cleanup. | Install and verify the matching artifact in Chrome; finish the remaining privacy/history classification. |
| 2 | W2-D4 | In progress | Exact-SHA staging delivery passed. Cache experiments were compared and removed because neither showed whole-job improvement. | A comparable end-to-end optimization and a complete safe recovery duration are not evidenced. Production persistence also remains unverified and requires an approved synthetic target. |
| 2 | W2-D5 | Complete for evidence preparation | Current status, risks, issue notes, and consultation preparation were refreshed. | Real standups, retrospective, rehearsal, attendance, and instructor feedback remain event-dependent. |
| 3 | W3-D1 | Verified | Carryover, current main/staging trace, and issue ownership were audited. | Product-side real report/evaluation work remains with its owners. |
| 3 | W3-D2 | In progress | Pinned, weight-free mock CI and deterministic checks pass. PR #86's advisory Dependency Review passed; its protected staging gate and exact-SHA deployment also passed. | Runtime coordination and exact installed-Chrome acceptance remain open. |
| 3 | W3-D3 | In progress | Staging identity and model/production separation are documented. | Real-provider evaluation, frozen cases, and owner-supplied model revision/results are not available to Kendra to invent or sign off. |
| 3 | W3-D4 | In progress | Pipeline timing and cache comparisons are documented with sample sizes and limitations; the historical October 14 drill is retained. | No whole-pipeline gain is established; full recovery duration and a new compatible safe rehearsal remain open. Do not disrupt shared staging or production to fill a metric. |
| 3 | W3-D5 | In progress | Evidence pack is prepared. | Actual consultation, team decisions, attendance, and instructor feedback must be recorded after they occur. |
| 4 | W4-D1–D5 | Not started | A proposed sequence is present in the sheet. | The team must agree dates/scope and create or assign Week 4 issues. Kendra's release, gates, documentation, candidate, metrics, and closeout steps can start once those inputs and owner evidence exist. |

## Remaining Kendra-owned actions, in order

1. **Browser acceptance (#37):** install the matching artifact from workflow run
   40736903885 in Chrome and record the browser version, package/source SHA,
   staging host permissions, expected history behavior, errors, and result.
2. **Delivery/recovery (#39/#40):** keep production read-only. Verify saved-record
   persistence only after the integrated product owner provides an approved
   synthetic production target and explicitly authorizes a write. Record a
   comparable whole-pipeline improvement only if measurements support it; record
   recovery duration during the next necessary safe recovery or approved staging
   rehearsal.
3. **Coordination (#36/#41):** record actual owner acknowledgements, scope
   decisions, consultation, rehearsal, and feedback when participants provide
   them. Do not fabricate attendance, approvals, or meeting outcomes.
4. **Week 4:** agree dates/scope at kickoff, create/assign the release issues,
   then update the proposed day rows and execute release coordination,
   environment/gate review, documentation, exact-SHA candidate verification,
   and final metrics/retrospective against the official rubric.

## Previous planning sequence — October 28

The following actions were completed or superseded by the October 29 status:

- The environment owner gate, protected staging deployment, current branch
  mapping, and exact-SHA staging CRUD verification are complete.
- The former pending PR #86 CI and merge actions are complete; PR #86 is merged.

Remaining work is listed above; keep production read-only until an approved
synthetic target exists.

## Evidence links

- [Kendra's backlog audit](backlog-audit-2026-10-28.md)
- [Staging gate and grant verification](staging.md)
- [Deployment/recovery runbook](runbook.md)
- [Pipeline metrics](metrics.md) and [optimization log](optimizations.md)
- [CI maintenance](ci-maintenance.md)
- [Weekly and Daily Sprint Task Plan](https://docs.google.com/spreadsheets/d/18ppxRcZEK6mBNyZMQkZwFTLlmMyS9WHnRRoUKiPCe58/edit?gid=774483955#gid=774483955)
