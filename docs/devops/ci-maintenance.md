# CI runtime and package-cache maintenance

## Problem and change

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

No measured performance improvement is claimed yet. Compare cold and warm runs
with the same database/test coverage, recording setup/install/job durations.
The first run may cost more time to save the cache.

## Validation and review

- Local backend lint and tests must pass before publishing.
- Only a GitHub run can validate the upgraded Action runtime and cache behavior.
- Use the latest JUnit/JSON report, not a fixed historical test count. Required
  PostgreSQL tests must pass without skipping in CI; backend and extension suites
  grow as reviewed feature tests land.
- Required Backend checks and teammate approval remain necessary before merge.
- No changes to application features, hosting plan, secrets or branch protection.
