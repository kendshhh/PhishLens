# Release PR alignment — 2026-11-27 07:48 UTC

This snapshot compares the coordinated release PRs, not every unrelated open
repository PR. All three target `main` at
`11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0`; all are authored by `kendshhh`.
The linked Files changed pages contain each complete file list.

## Current dependency map

| PR | Head branch and SHA | Base | Changed files / migrations | Relationship and current evidence |
|---|---|---|---|---|
| [#281](https://github.com/kendshhh/PhishLens/pull/281/files) — Integrate staging readiness on the #251-based mainline | `codex/reconcile-staging-merge-order-20261122` @ `27859a31674f99f17a5e26454104b3e6719493a7` | `main` @ `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` | 59 files; no migration file or `alembic.ini` changes | Parent release-hardening work. Source/local CI passed. Exact-head protected Neon preflight run `45956687871` is waiting for `xxTrixia`; trusted controller run `45957149389` failed closed without a matching successful preflight attestation. No hosted Auth/CRUD pass on this SHA. |
| [#282](https://github.com/kendshhh/PhishLens/pull/282/files) — Add shared AI quota controls and refresh DevOps evidence | `codex/devops-evidence-go-20261123` @ `3131dae6f09c30b267ca4aa7b864694a44fd744c` | `main` @ `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` | 101 files; no migration file or `alembic.ini` changes | Intentionally stacked on an older #281 head (`5764974`), then reconciled against the older #268 head (`63b000e`). Current source/security CI and Neon preflight pass; no current exact-head Auth/CRUD acceptance is recorded. Review requests changes. |
| [#268](https://github.com/kendshhh/PhishLens/pull/268/files) — Codex/devops staging closeout 20261121 | `codex/devops-staging-closeout-20261121` @ `554fd223ec98852acb12ebca01812530a84fde2d` | `main` @ `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` | 107 files; no migration file or `alembic.ini` changes | Ordered integration branch: #281 current head `27859a3`, then #282 prior head `7551e40`, then #268 prior head `63b000e`. Current checks and Neon preflight pass; exact-head hosted acceptance is queued behind the protected #281 run. GitHub's review decision is APPROVED. |

## Pairwise merge-tree results

The checks use current remote PR refs fetched on November 27. Tree IDs below
are outputs from `git merge-tree --write-tree`; they are simulations, not
commits or evidence of a GitHub merge.

| Current pair | Merge base | Result | Interpretation |
|---|---|---|---|
| #281 `27859a3` + #268 `554fd22` | #281 head `27859a3` | Clean, tree `02471c3406b0d1dbee7d02b05d8362dae7a553d8` | #281 is already an ancestor of #268's ordered integration head. |
| #281 `27859a3` + #282 `3131dae` | `57649747fa6be401ca0310bc2a0ea1de6b0ab53f` | Clean, tree `33a2790ed3feec83c267f5fb884003cd18b78c5e` | #282 contains an older #281 integration; this check does not mean it contains current #281. |
| #268 `554fd22` + #282 `3131dae` | `57649747fa6be401ca0310bc2a0ea1de6b0ab53f` | Conflicts | The current #268 branch includes #282 `7551e40`, not #282's latest `3131dae`. |

Current conflicts between #268 and #282 are exactly:

- `.github/workflows/ci.yml`
- `docs/devops/metrics.md`
- `docs/devops/staging.md`
- `scripts/tests/staging_auth.test.mjs`

There are multiple merge bases for #268 and #282; Git selected `5764974` for
the pairwise merge-tree comparison. The merge tree did not identify migration
file conflicts.

## Migration alignment

None of the three current PR diffs changes `backend/migrations/` or
`backend/alembic.ini`. Their migration lineage therefore remains the lineage
in base `main`; no PR-specific revision, down-revision, or migration order is
introduced. Preserve the lineage guard and validate repeatable upgrades in the
existing disposable/staging checks. Do not stamp or modify a database to make
these PRs appear aligned.

## Recommended integration action

Keep the existing #268 integration sequence and its protected staging gate.
Before merging any of these PRs to `main`, integrate current #282 head
`3131dae6f09c30b267ca4aa7b864694a44fd744c` into the #268 ordered integration
branch and resolve the four listed conflicts while preserving the current
trusted staging controller, quota-ordering fix, latest evidence, and all
required check names. Then run all required CI/security checks and exact-head
protected staging on that resulting SHA. The previous Auth/CRUD passes on
`63b000e` and `7551e40` do not carry forward.

Do not retarget or rewrite the open PRs just to simplify their graph. Update
their descriptions to their current heads and this explicit integration plan.
Until current exact-head authenticated acceptance, approved model-quality
evidence, and the production artifact/recovery gates pass, keep issue #153
**NO-GO**.
