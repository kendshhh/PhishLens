# Dependency security policy

As of 2026-11-14, the GitHub repository is public. The owner has stated that
public visibility is intended. Older November 8 and 13 notes describe an
unresolved or attempted private-visibility change; they are historical and are
superseded by
[repository-process-status-2026-11-14.md](repository-process-status-2026-11-14.md).

GitHub's dependency-review action uses the repository dependency graph. The
repository is public, and the current workflow runs the review for every pull
request without an opt-in variable.

The `.github/workflows/dependency-review.yml` workflow runs two lockfile
audits for pull requests and pushes to `main`, and GitHub's dependency graph
review for every pull request. The enforced thresholds are high-or-critical
for npm and GitHub graph findings, and any reported vulnerability for Python:

- `npm audit --audit-level=high --package-lock-only` checks the complete npm
  lockfile and fails for high or critical findings.
- Pinned `pip-audit` scans the fully pinned Python runtime and development
  requirements without resolving a different dependency set. It fails on any
  known Python vulnerability; low and moderate Python findings are therefore
  blocking under the current implementation.
- GitHub dependency graph review fails on high and critical findings via
  `fail-on-severity: high`.

These audits use the npm and PyPI advisory services and do not need repository
secrets. They scan the locked dependency trees; they do not replace GitHub's
before/after dependency graph review or license policy checks. Both the
`Dependency security` lockfile audit and
`Dependency graph review (GitHub Advanced Security)` are required main-branch
checks after their workflow names are observed on the PR.

Historical note: an earlier audit found `pyasn1==0.6.4` with CVEs
`CVE-2026-119194`, `CVE-2026-119195`, `CVE-2026-119196`, and
`CVE-2026-119197`; the lockfile was updated to `0.6.5`. The current dependency
workflow re-audits the full locks on each PR and main push.

## November 14 refresh

The pinned Python scan found `opentelemetry-api==1.45.1` affected by
`CVE-2026-126360`; the advisory listed `1.45.2` as the fixed version. The
source requirement now constrains `opentelemetry-api>=1.45.2,<2`, and both
runtime and development locks were regenerated with `1.45.2`. The post-fix
local checks passed: `pip-audit --no-deps -r backend/requirements-dev.txt`
reported no known vulnerabilities, and `npm audit --audit-level=high
--package-lock-only` reported zero vulnerabilities. The CI workflow repeats
these scans for the PR and main push.
