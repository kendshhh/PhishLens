# CI runtime and package-cache maintenance

> This page includes historical October maintenance notes. Current deployment
> and security state is summarized in the [November 15 DevOps status](kendra-devops-status-2026-11-15.md).

## Current pinned tools — 2026-11-21

The checked-in workflows pin Actions to full commit SHAs and record the
corresponding release beside each pin. Current versions include:

| Tool | Pinned version | Full commit / runtime pin |
|---|---|---|
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-node` | v7.1.0 | `949feb2413d6458794dcd2491c4babbbce0c15c1` |
| `actions/setup-python` | v7.1.0 | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` |
| `actions/upload-artifact` | v7.0.2 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |
| `actions/dependency-review-action` | v5.0.1 | `bbc44d14a204704ccc493733616cd1e93a0321ec` |
| `astral-sh/setup-uv` | v10.4.0 | `1db35dd8eee11c5894872e0b383ae6c406cf738d` |
| uv | 0.13.9 | Verified checksum required by the setup action |

The Node.js 24 and Python 3.12 runtime pins are shared across workflows and
match the repository's current package and Python lock configuration.
Dependabot checks GitHub Actions, npm, and pip weekly; review its PRs and rerun
the affected required checks before updating this table.

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

## Validation and review

- Local backend lint and tests must pass before publishing.
- Only a GitHub run can validate the upgraded Action runtime and cache behavior.
- Use the latest JUnit/JSON report, not a fixed historical test count. Required
  PostgreSQL tests must pass without skipping in CI; backend and extension suites
  grow as reviewed feature tests land.
- Required Backend checks and teammate approval remain necessary before merge.
- The original runtime/cache update did not change application features,
  hosting plan, secrets or branch protection.
