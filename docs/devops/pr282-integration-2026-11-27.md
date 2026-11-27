# PR #282 integration record — 2026-11-27

## Ordered branch integration

PR #281’s current head was 57649747fa6be401ca0310bc2a0ea1de6b0ab53f. It was merged first into PR #282’s pre-integration head 7551e4077e4f71f2768a3d090b7ce437d727eb60. The merge commit is 006fbf29cf8b1c5a4c0c5ddbb74aabafda50e55e; its first parent is the PR #282 candidate and its second parent is the PR #281 head.

The merge resolved overlaps in the shared CI workflow, pipeline and DevOps notes. It keeps PR #281’s trusted staging workflow changes, the #282 current-main quota and staging-host changes, and the historical evidence from both branches. The authenticated-staging helper was unchanged in substance; its conflict was a trailing blank-line difference.

## Pairwise compatibility with PR #268

The current PR #268 head used for comparison is 63b000e17631f9514d8763c4c88d054cbcfc2e24, based on main at 11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0. The initial pairwise merge-tree check after the #281 merge identified overlaps in PIPELINE.md, the DevOps metrics and staging notes, extension/js/api.js, and three staging tests.

The follow-up reconciliation retains the newer #282 evidence in this integration record, aligns shared historical documentation with the #268 snapshots, keeps the equivalent bearer-token validation, and splits the trusted-controller tests from the Issue 90 workflow tests. The final pairwise merge-tree result is recorded after this updated head is checked.

## Checks

Before integration, PR #282 head 7551e4077e4f71f2768a3d090b7ce437d727eb60 had successful required checks and trusted hosted staging acceptance, as confirmed in the latest reviewer diagnostics. The hosted run is [45949708542](https://github.com/kendshhh/PhishLens/actions/runs/45949708542). The Issue 90 package job was skipped by its exact-branch filter.

These results belong to the pre-integration SHA. Exact-head checks and protected hosted acceptance must be evaluated again on the final integrated head; no status from 7551e407 is carried forward. The final exact-head results are recorded in the refreshed PR description.

## Current DORA evidence and release status

The November 27 report and redacted source snapshot are in [dora-report-2026-11-27.md](dora-report-2026-11-27.md) and [dora-source-2026-11-27.json](evidence/dora-source-2026-11-27.json). Against the 11f72ad main snapshot, the 28-day report records a 3.66-minute median merge-to-live lead-time proxy for 60 of 142 merged PRs, 63 successful deploy records, and 117 main CI runs (115 success, 2 failure; median 66 seconds, p90 91 seconds). Change failure rate, failed-deployment recovery time, deployment rework, and a comparable end-to-end optimization gain remain unmeasured.

No production deployment or production data access occurred. The release remains NO-GO.