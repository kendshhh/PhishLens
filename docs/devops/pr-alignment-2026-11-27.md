# Coordinated release PR alignment — November 27, 2026 08:45 UTC

This snapshot covers the coordinated release PR set, not every unrelated open
PR. All three target `main` at `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` and
are authored by `kendshhh`. Current GitHub PR metadata was refreshed before the
integration check. Full file inventories remain linked from each PR.

## Current dependency map

| PR | Branch and current head | Base | Files / migrations | Relationship, verification, and action |
|---|---|---|---|---|
| [#281](https://github.com/kendshhh/PhishLens/pull/281/files) | `codex/reconcile-staging-merge-order-20261122` @ `0c48cbf240b963a35b5e4669417e118d5ea6573b` | `main` @ `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` | 59 files in the captured PR diff; no migration files or `backend/alembic.ini` | Release-hardening parent. Exact current head is merged into the #268 integration branch by `1002b20`; its own review remains changes requested. Do not assume PR status transfers from the integration run. |
| [#282](https://github.com/kendshhh/PhishLens/pull/282/files) | `codex/devops-evidence-go-20261123` @ `3131dae6f09c30b267ca4aa7b864694a44fd744c` | `main` @ `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` | 101 files in the captured PR diff; no migration files or `backend/alembic.ini` | Intentionally built on an older #281 head and reconciled with #268. Current #282 head is integrated after #281 by `e8016db`; review remains changes requested. Do not retarget or rewrite the stack merely to simplify the graph. |
| [#268](https://github.com/kendshhh/PhishLens/pull/268/files) | `codex/devops-staging-closeout-20261121` @ `d77491d8fd91252190755714df8e5fa475e9c13b` | `main` @ `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` | 114 files in captured integration review plus correction/evidence docs; no migration files or `backend/alembic.ini` | Integration branch. It contains current #281, then current #282, then its prior #268 base. Exact-head CI, trusted staging acceptance, and PR review passed on `d77491d`. The PR remains open and unmerged; this evidence update will be a docs-only descendant and needs fresh required checks/review. |

## Actual ordered integration

The current #268 tree records these parent relationships:

1. Current #281 head `0c48cbf240b963a35b5e4669417e118d5ea6573b` was integrated
   first by merge `1002b20`.
2. Current #282 head `3131dae6f09c30b267ca4aa7b864694a44fd744c` was integrated
   second by merge `e8016db`.
3. Prior #268 head `554fd223ec98852acb12ebca01812530a84fde2d` was integrated last
   by merge `9039d1a490d283cc7bcca9243aa02b705036a7dd`.

This preserves the intended stack while making #268 the combined review
candidate. The current merge is real Git history, not a simulated merge tree.
The current #268 commit is still a candidate only; it has not been merged to
`main`.

## Migration and overlap audit

The three PR diffs do not modify `backend/migrations/` or
`backend/alembic.ini`; no child introduces a new revision or down-revision and
there is no PR-set migration ordering dependency. The actual combined diff
retains the existing migration-lineage guard. Protected staging acceptance on
exact #268 SHA `d77491d` reported revision `0005_ai_request_quota`; the
candidate introduces no new migration revision, and both migration-graph and
live staging revision checks passed.

The shared workflow and DevOps evidence files overlap. The integration keeps
the trusted staging controller, current quota-ordering changes, current DORA
source/report, and the existing stable required check names. The undefined
`ROOT` in `scripts/tests/test_hosted_staging_gate.py` was fixed; exact-head
Staging integration now passes. No duplicated migration work or
dependency-update conflict was found in this set.

## Latest exact-head CI and acceptance

PR #268 exact head `d77491d8fd91252190755714df8e5fa475e9c13b` passed CI
[45966131065](https://github.com/kendshhh/PhishLens/actions/runs/45966131065),
Workflow lint [45966130957](https://github.com/kendshhh/PhishLens/actions/runs/45966130957),
Dependency security [45966131061](https://github.com/kendshhh/PhishLens/actions/runs/45966131061),
Deterministic AI Evaluation [45966131179](https://github.com/kendshhh/PhishLens/actions/runs/45966131179),
CodeQL [45966123755](https://github.com/kendshhh/PhishLens/actions/runs/45966123755),
and Trusted staging Neon [45966125445](https://github.com/kendshhh/PhishLens/actions/runs/45966125445).
Backend, Extension, Staging integration, and migration source preflight passed;
the unrelated Issue 90 package job was skipped by its exact path filter.

Trusted hosted run
[45966647832](https://github.com/kendshhh/PhishLens/actions/runs/45966647832)
passed exact PR inspection, isolated Neon verification, controlled Render
staging deployment, exact-package authenticated acceptance, and the required
`Secretary staging` status. PR review was APPROVED on this SHA. Live staging
and backend source SHA matched. The run reported migration revision
`0005_ai_request_quota` and extension ZIP SHA-256
`495d9bb7d3a222b103a30de819f6a0e7c8d4c9844e9120c24b9d6f4a4b47bdb7`.
Sign-in, persistent CRUD, reload persistence, ownership, two-account isolation,
cleanup, and extension loading/success/auth/API/timeout behavior passed. The
record shows zero production requests or writes. See the
[redacted evidence record](evidence/2026-11-27-staging-acceptance-d77491d.md).

The run explicitly reports AI quality **BLOCKED** (`approval_not_provided`)
and backend image digest `null`; it is not production promotion. The earlier
`9039d1a` test failure was fixed and the current Staging integration check
passes. The full local Python 3.12 `scripts/tests` suite passed after the fix:
347 passed and 9 expected skips.

## DORA and release decision

The latest published main-snapshot DORA report is based on source collected at
`2026-11-27T07:14:04.739580Z`: merge-to-live proxy median 3.66 minutes (`60/142`
merged PR SHAs matched), 63 successful deploy records, and main-CI median 66
seconds (`115/117` runs passed). Change failure rate, failed-deployment
recovery, deployment rework, and like-for-like end-to-end optimization remain
unmeasured. A staging acceptance run is not a production deployment and does
not alter those production denominators.

Issue #153 remains **NO-GO**. No current-model approved holdout, image-backed
same-digest production promotion, production post-deploy acceptance, compatible
rollback rehearsal, measured data restore/RTO/RPO, or tested alert-to-response
evidence has been established by this integration.
