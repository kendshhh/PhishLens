# Kendra DevOps task status — 2026-11-04

This snapshot covers only work assigned to Kendra (`kendshhh`) in PhishLens.
GitHub’s live issue query found #36, #37, #40, #41, #93, #94, and #95 open;
#39 is closed. The repository’s current `main` is
[`6b0e97f`](https://github.com/kendshhh/PhishLens/commit/6b0e97f6c2b88a469614b0ce3aaf6773a501fd7a).
PR [#104](https://github.com/kendshhh/PhishLens/pull/104), which implements
the deterministic AI evidence gate and guarded manual staging smoke, merged on
November 3 as `af1f90981cb18ae7802a2a363b56c30fb2d02488`. The merged implementation
advances the tasks; it does not satisfy the remaining external acceptance gates.

| Issue | Kendra work recorded | Remaining acceptance |
|---|---|---|
| [#36](https://github.com/kendshhh/PhishLens/issues/36) — shared contract and carryover | Contract proposals, owner map, and sprint requirements are documented. | API/client/AI owner acknowledgement, instructor scope decision, integrated demonstration, and board/sprint-log update. Keep proposals labelled until accepted. |
| [#37](https://github.com/kendshhh/PhishLens/issues/37) — environments and package | The exact PR #99 staging artifact was installed in Chrome 156.0.8078.79 on October 31; staging-only site access, popup, and context-menu entry were checked. Later bounded package/history scans are recorded in the issue. | Browser save/history CRUD and privacy/history classification remain incomplete. The production app role still has excess privileges; the approved grant change needs an owner-managed database connection with sufficient rights. Hosted secret and credential scopes also need owner review. |
| [#39](https://github.com/kendshhh/PhishLens/issues/39) — automatic production delivery | Closed October 31. | No open Kendra action is recorded for this issue. |
| [#40](https://github.com/kendshhh/PhishLens/issues/40) — optimization and recovery | The October 31 staging-only rollback/restore took 200.753 seconds to return Live and 233.408 seconds to independent verification. The `n=2` cache comparison showed no whole-job gain. | A comparable end-to-end optimization is not demonstrated. Production and schema/model rollback compatibility remain unmeasured; do not induce a production failure to fill this gap. |
| [#41](https://github.com/kendshhh/PhishLens/issues/41) — consultation and team evidence | Consultation materials and technical evidence are prepared. | Later standups, retrospective, whole-team rehearsal, consultation attendance, instructor decisions, and resulting follow-ups need records from the actual events. |
| [#93](https://github.com/kendshhh/PhishLens/issues/93) — deterministic AI regression gate | PR #104 is merged. Ordinary CI remains mock-only; its revision-linked report checks required deterministic AI and failure-path coverage and does not claim model accuracy. | Agree the regression baseline and any blocking thresholds with the AI owner; keep held-out quality evaluation separate. No model-quality claim is established. |
| [#94](https://github.com/kendshhh/PhishLens/issues/94) — guarded real-provider smoke | PR #104 is merged. The manual-only workflow checks the staging revision and readiness before one fixed synthetic, non-persisting analysis request. It has no schedule and fails closed without owner configuration. | AI/staging owners must confirm provider, model, cost/quota guard, staging identity, and approval path. The November 2 settings review found no required reviewers or wait timer on `staging`, with administrator bypass enabled; the owner must confirm or correct that gate before dispatch. Then an authorized bounded staging run can produce live evidence. No live provider call is claimed. |
| [#95](https://github.com/kendshhh/PhishLens/issues/95) — AI failure drill | PR #104 is merged with deterministic simulated failure evidence and required PostgreSQL save/no-save/recovery cases. The October rollback timings in #40 cover an app-deploy rehearsal, not an AI failure. | An owner-approved AI failure matrix and bounded protected-staging drill, with exact revisions and recovery evidence, remain pending. Production was not used for a failure drill. |

Week 4 dates, scope, and issue assignments still need team agreement. Do not
infer final release or demo acceptance from this status record.

## Next Kendra actions

1. Keep the manual provider workflow unconfigured until the AI and staging owners
   confirm its provider, model, budget guard, target, and reviewer path, and the
   staging environment has its approved gate. After approval, dispatch it from
   `main` against the exact SHA reported by staging.
2. Update #37 only after the database administrator, secret-scope owner, and
   browser acceptance evidence are available; do not change production access
   from the current limited SQL role.
3. Record future optimization and recovery samples with comparable coverage,
   sample sizes, full timing boundaries, and compatibility details. Do not call
   the existing cache experiment a speedup.
4. Refresh #36 and #41 from actual owner decisions and team events. Do not infer
   acceptance or backfill meeting records.
5. Keep #93–#95 open until their remaining owner and live-evidence criteria are
   met; PR #104 being merged alone does not complete those issues.

## Evidence references

- [Pipeline gates and AI evidence](../../PIPELINE.md)
- [Manual staging smoke operator guide](ai-provider-smoke.md)
- [Metrics and recovery record](metrics.md)
- [Deployment and recovery runbook](runbook.md)
- [Staging record](staging.md)
- [Consultation 2 preparation](consultation-2.md)

