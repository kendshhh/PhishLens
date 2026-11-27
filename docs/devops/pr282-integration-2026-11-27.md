# PR #282 integration record — 2026-11-27

## Current heads and integration order

- `main` is `88156d479d19eb0b8018ab76aa3170eb60079765`.
- PR #281 is at `27f4c3cd22138a78aa30b34284ef1c16230fb4a7`, based on that `main`.
  Its file tree is identical to `main` (`89a3b3e0701629497c4f1f14e756f26ca98a10c7`), so it contributes no remaining file changes.
- PR #282 is at `3131dae6f09c30b267ca4aa7b864694a44fd744c`, based on the older
  `main` commit `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0`.

Treat #281 as superseded and reconcile #282 directly with current `main`. The
resulting #282 merge commit has the previous #282 head as its first parent and
`88156d4` as its second parent. There is no reason to merge the empty #281 tree
as an additional integration layer.

## Merge checks and conflict resolution

On the exact heads above, `git merge-tree --write-tree --name-only` reports:

- `main` + #281: clean; merged tree equals current `main`.
- #281 + #282: seven conflict paths: `PIPELINE.md`, the two DORA evidence files,
  `docs/devops/metrics.md`, this integration record, and two staging test files.
- `main` + #282: ten conflict paths, including both workflow files and the
  release-promotion workflow test in addition to the overlapping evidence and
  staging gate test files.

The resolution keeps current `main`'s release workflows, CI workflow, and
workflow tests. The schema-only Neon identity inputs and module-based migration
invocation required by the release workflow are already present in that current
workflow. For the shared DORA records, it keeps the newer snapshot collected at
`2026-11-27T07:14:04.739580Z` rather than the older `05:58` snapshot from #282.
The historical pairwise-conflict narrative is replaced by this current merge
record. Non-conflicting #282 changes remain in the candidate.

No migration files or `backend/alembic.ini` are changed by this integration.
The merge-tree check is rerun against the resulting #282 head and current `main`
after the merge commit is created.

## Verification status

Local conflict-focused verification is recorded with the resulting candidate.
GitHub Actions must complete on that exact head before its CI or staging
acceptance is treated as current. Earlier checks and hosted runs on `3131dae`
or older SHAs do not transfer to the reconciled candidate.

The release remains **NO-GO**. No production deployment, production data
access, release tag, or production promotion is part of this integration.
