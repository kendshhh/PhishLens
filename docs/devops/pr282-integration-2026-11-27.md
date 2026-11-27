# PR #282 integration record — 2026-11-27 10:30 UTC

## Current release integration

PR #268 merged to `main` at `88156d479d19eb0b8018ab76aa3170eb60079765`
with tree `89a3b3e0701629497c4f1f14e756f26ca98a10c7`. Its exact candidate tree
was accepted in protected staging run
[45966647832](https://github.com/kendshhh/PhishLens/actions/runs/45966647832).
PR #281 is closed unmerged; its relevant changes were integrated through #268.
The previous quota/runtime changes from PR #282 are also present in that merged
tree.

The open PR #282 is now a documentation-only follow-up. Before this correction,
head `77bd6065466b5218626218e7f3e2f3c8d215e66b` was based on current `main` and
changed only this integration record. It did not change application code, CI
workflows, dependencies, or database migrations. Its old description and this
file previously contained stale integration SHAs and DORA values; those old
values must not be treated as current.

## Checks and staging semantics

On the prior documentation head `77bd606`, CI run
[45978321101](https://github.com/kendshhh/PhishLens/actions/runs/45978321101),
CodeQL, deterministic AI evaluation, dependency security, workflow lint, and
trusted Neon preflight completed successfully. The Issue 90 package was skipped
by its path filter. `Secretary staging` reported explicit not-applicable success
because no runtime files changed. Main controller run
[45978972202](https://github.com/kendshhh/PhishLens/actions/runs/45978972202)
likewise skipped Neon validation, staging deployment, and product acceptance.
These N/A results are not hosted acceptance. This correction commit requires
fresh exact-head checks; no result from `77bd606` is carried forward.

The last authenticated product acceptance remains PR #268 run `45966647832` on
candidate `d77491d8fd91252190755714df8e5fa475e9c13b`, with extension ZIP
SHA-256 `495d9bb7d3a222b103a30de819f6a0e7c8d4c9844e9120c24b9d6f4a4b47bdb7`.
It passed isolated staging Auth, persistent saved-report CRUD, reload
persistence, account isolation, cleanup, and extension UX. The run recorded AI
quality blocked (`approval_not_provided`) and no backend image digest. The
current documentation follow-up does not repeat staging or change that evidence.

## Post-publication verification of this correction

The correction commit `e665fdde1fabba9906a7e9170b5d80c0e5d39916` completed
applicable CI in run
[45982767567](https://github.com/kendshhh/PhishLens/actions/runs/45982767567):
Backend, Extension, Staging integration, and migration source preflight passed;
the Issue 90 package was skipped by its path filter. CodeQL
([140450847115](https://github.com/kendshhh/PhishLens/runs/140450847115)),
deterministic AI evaluation
([45982767774](https://github.com/kendshhh/PhishLens/actions/runs/45982767774)),
dependency security
([45982767737](https://github.com/kendshhh/PhishLens/actions/runs/45982767737)),
workflow lint
([45982767583](https://github.com/kendshhh/PhishLens/actions/runs/45982767583)),
and the migration/preflight job passed. The separate `verify-neon` and Issue 90
jobs were skipped by their documented conditions. `Secretary staging` reported
success with explicit N/A: no application/runtime changes; required CI passed.
No Render staging deployment or authenticated acceptance was run on this
documentation-only PR head. The PR remains open with changes requested.

## Current DORA evidence

The reproducible 28-day snapshot refreshed at
`2026-11-27T10:11:12.795930Z` against main `88156d479d19eb0b8018ab76aa3170eb60079765`
reports a merge-to-live proxy median of 3.66 minutes (`60/143` merged PR SHAs
matched), 63 successful production deploy records, and main CI median of 66.50
seconds (`116/118` successful). Change failure rate, production failure recovery,
deployment rework, and a comparable end-to-end optimization remain unmeasured.
The DORA source and formulas are documented in
[`dora-report-2026-11-27.md`](dora-report-2026-11-27.md); earlier snapshots are
retained as dated evidence.

## Release decision

Issue #153 remains **NO-GO**. This record does not claim model-quality approval,
image-backed same-digest production promotion, production product acceptance,
current-compatible rollback, isolated restore with measured RTO/RPO, or tested
alert delivery. No production deployment, production data access, release tag,
or issue status change is part of this documentation update.
