# Current PR #281 → #282 → #268 integration — 2026-11-27

This record documents the actual coordinated integration on PR #268. The
branches remain open against `main`; no PR was merged to `main`, no production
deployment occurred, and no production data was accessed.

## Exact branch heads and merge order

At the integration check, `main` was `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0`.
The current release branches were:

- PR #281: `0c48cbf240b963a35b5e4669417e118d5ea6573b`.
- PR #282: `3131dae6f09c30b267ca4aa7b864694a44fd744c`.
- PR #268's prior head: `554fd223ec98852acb12ebca01812530a84fde2d`.

The combined #268 history is in this order:

1. Merge current #281 into the integration base: `1002b20`.
2. Merge current #282: `e8016db`.
3. Carry prior #268 work last: `9039d1a490d283cc7bcca9243aa02b705036a7dd`.

This preserves the intentional #282-on-#281 history and the #268 integration
branch. The child PRs were not retargeted, rebased, or closed to simplify the
graph.

## Conflict and migration results

The shared CI and staging tests and the current DORA/DevOps records overlapped.
Resolution retained the current trusted staging controller, #282 quota/staging
changes, #281's later November 27 DORA snapshot, and the stable required check
names. The old pairwise conflicts are resolved in actual merge commits; they
are not pending merge-tree simulations. No PR in this set changes
`backend/migrations/` or `backend/alembic.ini`, so no migration revision or
down-revision was duplicated or reordered.

The #268 exact-head CI run found that
`scripts/tests/test_hosted_staging_gate.py` referenced an undefined `ROOT`.
The path definition is corrected in the current PR update. Focused tests pass,
and the repository Python 3.12 suite passes 347 tests with 9 expected skips.
GitHub must still rerun every required check on the new exact head.

## Exact-head status and staging evidence

On integrated SHA `9039d1a`:

- Trusted Neon preflight passed in run
  [45963430015](https://github.com/kendshhh/PhishLens/actions/runs/45963430015).
- Backend, Extension, migration source preflight, Workflow lint, CodeQL,
  dependency security, and deterministic AI evaluation passed.
- Staging integration failed on the test import defect in run
  [45963431013](https://github.com/kendshhh/PhishLens/actions/runs/45963431013),
  so `Secretary staging` correctly failed. Protected authenticated acceptance
  did not run for this SHA.

Prior exact-head protected staging run
[45958860400](https://github.com/kendshhh/PhishLens/actions/runs/45958860400)
passed for old SHA `554fd223` and its extension ZIP SHA-256
`7d7082e1e1bc5f3c0fd0c89d8e1d85bb4ec0b3180cd19602cd87d322b955dccd`. It
verified Auth sign-in, persistent saved-report CRUD, reload persistence,
ownership/isolation, cleanup, and extension UX. Its AI status was blocked and
backend image digest was absent. This evidence does not transfer to `9039d1a`
or the corrected successor. The next head requires fresh CI, protected Neon
preflight, independent reviewer approval, and authenticated acceptance.

## DORA snapshot and release state

The retained main report uses source collected at
`2026-11-27T07:14:04.739580Z`: median merge-to-live proxy 3.66 minutes
(`60/142` matched merged PRs), 63 successful deploy records, and CI median 66
seconds (`115/117` passed). Change failure rate, failed-deployment recovery,
deployment rework, and comparable end-to-end optimization remain unmeasured.

Issue #153 remains **NO-GO**. The historical staging pass is not AI-quality
approval, same-image promotion, production smoke, rollback/restore rehearsal,
measured RTO/RPO, or alert delivery evidence.
