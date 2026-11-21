# CI runtime and package-cache maintenance

> This page includes historical October maintenance notes. Current deployment
> state is summarized in the [November 21 release record](release-record-2026-11-21.md)
> and [environment map](environment-map-2026-11-21.md); older deployment notes
> below are dated snapshots.

## Current pinned Actions — 2026-11-15

The checked-in workflows currently pin `actions/checkout` v7 to
`3d3c42e5aac5ba805825da76410c181273ba90b1` and `actions/setup-python` v7 to
`6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`. The older setup-python hash in the
historical note below is no longer used.

## Historical October 14 action update

GitHub reported a Node.js 20 deprecation warning for checkout v4 and
setup-python v5. This change uses the official v7 implementations, pinned to
the commit IDs resolved from their public v7 tags on October 14, 2026.

- checkout: 3d3c42e5aac5ba805825da76410c181273ba90b1
- setup-python: 5fda3b95a4ea91299a34e894583c3862153e4b97

Official sources: https://github.com/actions/checkout and
https://github.com/actions/setup-python . The newer runtime requires a current
runner; this workflow uses GitHub-hosted ubuntu-latest.

Checkout credentials are not persisted because the check job does not push code.
The required job name, triggers, read-only permissions and tests are retained.

## Cache behavior

setup-python caches pip downloads using both pinned dependency files. Changed
pins invalidate the key. Runtime/development installation and every quality
check still execute; a cache hit does not count as test success.

The October 21 comparison found lower install time but no end-to-end staging-job
improvement; see [optimization evidence](optimizations.md). Compare cold and warm
runs with the same database/test coverage, recording setup/install/job durations.
The first run may cost more time to save the cache.

## Dependency security gates on current main

The `Dependency security` workflow runs on pull requests and pushes to `main`.
It rejects high-severity npm findings and audits the pinned Python runtime and
development requirements with `pip-audit`. The optional CPU inference lock is
also audited with strict OSV collection. The main ruleset requires this context.

The PR-only `Dependency graph review (GitHub Advanced Security)` job runs on
every pull request with read-only `contents` and `pull-requests` permissions.
It fails on introduced high or critical findings, and the main ruleset separately
requires this context. The obsolete `DEPENDENCY_REVIEW_ENABLED` variable was
removed; neither current job uses `warn-only` or an opt-in gate. Check the Actions
result on every PR rather than treating a skipped job as a clean scan.

On 2026-11-21, the repository's dependency graph and vulnerability alerts were
enabled after Dependency Review reported that the graph was unavailable. The
rerun of PR #268's Dependency graph review passed on
[`0d3818e`](https://github.com/kendshhh/PhishLens/commit/0d3818e95715cdd1dba2d4a3b6572a029c6fc1c),
`def5e9b` ([run 44890690295](https://github.com/kendshhh/PhishLens/actions/runs/44890690295)),
and PR head `a151585` ([run 44897548010](https://github.com/kendshhh/PhishLens/actions/runs/44897548010)).
GitHub reported 15 existing Dependabot alerts on the default branch (12 high,
3 moderate); these are tracked in [the dependency audit record](dependency-audits.md)
and were not dismissed. They remain open security work.

## Validation and review

- Local backend lint and tests must pass before publishing.
- Only a GitHub run can validate the upgraded Action runtime and cache behavior.
- Use the latest JUnit/JSON report, not a fixed historical test count. Required
  PostgreSQL tests must pass without skipping in CI; backend and extension suites
  grow as reviewed feature tests land.
- Required Backend checks and teammate approval remain necessary before merge.
- The original runtime/cache update did not change application features,
  hosting plan, secrets or branch protection.
