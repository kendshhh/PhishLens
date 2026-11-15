# Dependency security policy

As of 2026-11-14, the GitHub repository is public. The owner has stated that
public visibility is intended. Older November 8 and 13 notes describe an
unresolved or attempted private-visibility change; they are historical and are
superseded by
[repository-process-status-2026-11-14.md](repository-process-status-2026-11-14.md).

GitHub's dependency-review action uses the repository dependency graph. The
repository is public, and the current workflow runs the review for every pull
request without an opt-in variable.

The `.github/workflows/dependency-review.yml` workflow runs three lockfile
audits for pull requests and pushes to `main`, and GitHub's dependency graph
review for every pull request. The enforced thresholds are high-or-critical
for npm and GitHub graph findings, and any reported vulnerability for Python:

- `npm audit --audit-level=high --package-lock-only` checks the complete npm
  lockfile and fails for high or critical findings.
- Pinned `pip-audit` scans the fully pinned Python runtime and development
  requirements without resolving a different dependency set. It fails on any
  known Python vulnerability; low and moderate Python findings are therefore
  blocking under the current implementation.
- The optional CPU inference lock, `backend/requirements-ai.txt`, is audited
  against OSV with `--strict`. Its pinned `torch==2.15.0+cpu` build is not
  published on PyPI, so the default PyPI audit reports that package as
  unauditable. OSV covers the lock while strict collection makes a skipped
  dependency fail the check instead of looking like a clean result.
- GitHub dependency graph review fails on high and critical findings via
  `fail-on-severity: high`.

These audits use npm, PyPI, and OSV advisory data and do not need repository
secrets. They scan the locked dependency trees; they do not replace GitHub's
before/after dependency graph review or license policy checks. Both the
`Dependency security` lockfile audit and
`Dependency graph review (GitHub Advanced Security)` are required main-branch
checks after their workflow names are observed on the PR.

Historical note: an earlier audit found `pyasn1==0.6.4` with CVEs
`CVE-2026-119194`, `CVE-2026-119195`, `CVE-2026-119196`, and
`CVE-2026-119197`; the lockfile was updated to `0.6.5`. The current dependency
workflow re-audits the full locks on each PR and main push.

November 14, 2026: PR #168's audit flagged `opentelemetry-api==1.45.1`
for `CVE-2026-126360` / `GHSA-mf5v-w3w3-f6cg`. The
[upstream advisory](https://github.com/open-telemetry/opentelemetry-python/security/advisories/GHSA-mf5v-w3w3-f6cg)
identifies `1.45.2` as patched. The runtime input now requires
`opentelemetry-api>=1.45.2,<2`; runtime and development locks were regenerated
for Python 3.12/Linux using uv 0.13.8. Only that package's pinned version changed.

The optional AI lock was also scanned locally on November 14 with
`pip-audit==2.10.1 --no-deps --strict --vulnerability-service osv`; it reported
no known vulnerabilities and collected every pinned dependency. The default
PyPI service had skipped the CPU-specific Torch build, which is why CI now uses
OSV for this lock.

GitHub's Dependabot API still reports 15 open alerts even though the current
default-branch locks contain the patched versions: 12 high `pyasn1` alerts
refer to `=0.6.4` (fixed in `0.6.5`) and three medium `opentelemetry-api`
alerts refer to `=1.45.1` (fixed in `1.45.2`). The latest lockfile audit passes.
These alert records appear stale; keep them open until GitHub reconciles the
dependency graph, and do not dismiss them to clear the dashboard.

Local verification used a fresh Python 3.12.5 environment installed from the
updated development lock. `pip check` passed; the backend suite reported
293 passed and 45 skipped. Both Python locks passed `pip-audit==2.10.1`, and
the npm lock audit reported zero vulnerabilities. These are local results;
PostgreSQL-specific CI and hosted Auth acceptance remain separate. No audit
exception, workflow bypass, or shared-environment change was introduced.

As of November 14, the repository is public and GitHub dependency graph review
runs for every pull request without an opt-in variable. The previously configured
`DEPENDENCY_REVIEW_ENABLED` variable had no current workflow consumer and was
removed; do not reintroduce an opt-in gate without updating branch protection.
