# Coordinated release PR alignment — November 27, 2026 08:22 UTC

This snapshot covers the coordinated release PR set, not every unrelated open
PR. All three target `main` at `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` and
are authored by `kendshhh`. Current GitHub PR metadata was refreshed before the
integration check. Full file inventories remain linked from each PR.

## Current dependency map

| PR | Branch and current head | Base | Files / migrations | Relationship, verification, and action |
|---|---|---|---|---|
| [#281](https://github.com/kendshhh/PhishLens/pull/281/files) | `codex/reconcile-staging-merge-order-20261122` @ `0c48cbf240b963a35b5e4669417e118d5ea6573b` | `main` @ `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` | 59 files in the captured PR diff; no migration files or `backend/alembic.ini` | Release-hardening parent. Exact current head is merged into the #268 integration branch by `1002b20`; its own review remains changes requested. Do not assume PR status transfers from the integration run. |
| [#282](https://github.com/kendshhh/PhishLens/pull/282/files) | `codex/devops-evidence-go-20261123` @ `3131dae6f09c30b267ca4aa7b864694a44fd744c` | `main` @ `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` | 101 files in the captured PR diff; no migration files or `backend/alembic.ini` | Intentionally built on an older #281 head and reconciled with #268. Current #282 head is integrated after #281 by `e8016db`; review remains changes requested. Do not retarget or rewrite the stack merely to simplify the graph. |
| [#268](https://github.com/kendshhh/PhishLens/pull/268/files) | `codex/devops-staging-closeout-20261121` @ `9039d1a490d283cc7bcca9243aa02b705036a7dd` (last remotely verified) | `main` @ `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` | 114 files in the captured PR review; no migration files or `backend/alembic.ini` | Integration branch. It contains current #281, then current #282, then its prior #268 base. The exact-head run failed a Python test import; see checks below. A focused correction is being prepared. Keep this PR open and unmerged until fresh required checks, independent review, and current-head staging pass. |

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
retains the existing migration-lineage guard. The protected staging acceptance
on old SHA `554fd223` reported revision `0005_ai_request_quota`; this does not
prove the integrated candidate's migration result, which must be checked again
after its CI and staging run.

The shared workflow and DevOps evidence files overlap. The integration keeps
the trusted staging controller, current quota-ordering changes, current DORA
source/report, and the existing stable required check names. The only exact-head
runtime failure found so far is the undefined `ROOT` in
`scripts/tests/test_hosted_staging_gate.py`; it is fixed in this PR update and
covered by the focused tests. No duplicated migration work or dependency-update
conflict was found in this set.

## Checks and evidence identity

For last remotely verified integrated SHA `9039d1a`:

- CI [run 45963431013](https://github.com/kendshhh/PhishLens/actions/runs/45963431013)
  passed Backend, Extension, and migration preflight but failed Staging
  integration because `CI_WORKFLOW = ROOT / ...` referenced an undefined
  `ROOT`. This made required `Secretary staging` fail closed. The Issue 90
  package job was skipped by its exact-branch filter.
- Trusted Neon preflight [run 45963430015](https://github.com/kendshhh/PhishLens/actions/runs/45963430015)
  passed. Workflow lint [45963431058](https://github.com/kendshhh/PhishLens/actions/runs/45963431058),
  Deterministic AI Evaluation [45963430986](https://github.com/kendshhh/PhishLens/actions/runs/45963430986),
  Dependency security [45963431195](https://github.com/kendshhh/PhishLens/actions/runs/45963431195),
  and CodeQL analysis [140386566053](https://github.com/kendshhh/PhishLens/runs/140386566053)
  passed.
- Authenticated staging acceptance passed earlier on exact SHA
  `554fd223` only: trusted run
  [45958860400](https://github.com/kendshhh/PhishLens/actions/runs/45958860400).
  It passed sign-in, CRUD, persistence, ownership/isolation, cleanup and
  extension UX; ZIP SHA-256 was
  `7d7082e1e1bc5f3c0fd0c89d8e1d85bb4ec0b3180cd19602cd87d322b955dccd`. It
  reported AI quality blocked and no backend image digest. Do not treat it as
  evidence for `9039d1a` or a successor.
- The full local `scripts/tests` suite passed after the path correction under
  the repo Python 3.12 virtual environment: 347 tests passed, 9 expected skips.
  The focused hosted-gate tests also passed. These local results do not replace
  fresh required GitHub checks.

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
