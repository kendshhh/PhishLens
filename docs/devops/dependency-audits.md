# Dependency audits while repository visibility change is pending

As of 2026-11-08, GitHub reports PhishLens as public. The owner-approved
change to private is paused for sudo reauthentication, so the repository should
not be described as private until GitHub confirms the change. See
[kendra-release-readiness-2026-11-08.md](kendra-release-readiness-2026-11-08.md)
for the point-in-time status.

GitHub's dependency-review action uses the repository dependency graph. It can
be used on public repositories; private repositories require GitHub Advanced
Security licensing. The current workflow keeps that action opt-in through the
`DEPENDENCY_REVIEW_ENABLED` Actions variable. A skipped job reflects that
workflow setting; it does not mean the repository is currently private or that
the dependencies have no vulnerabilities.

The `.github/workflows/dependency-review.yml` workflow runs two lockfile
audits for pull requests and pushes to `main`:

- `npm audit --audit-level=high --package-lock-only` checks the complete npm
  lockfile and fails for high or critical findings.
- Pinned `pip-audit` scans the fully pinned Python runtime and development
  requirements without resolving a different dependency set. It fails for a
  known vulnerability in those pins.

These audits use the npm and PyPI advisory services and do not need repository
secrets. They scan the locked dependency trees; they do not reproduce GitHub's
before/after dependency graph review or license policy checks.

The initial audit found `pyasn1==0.6.4` with CVEs `CVE-2026-119194`,
`CVE-2026-119195`, `CVE-2026-119196`, and `CVE-2026-119197`. This PR constrains
and locks `pyasn1` at `0.6.5`, the fixed version reported by the audit. The
updated lockfile audit must pass before the change is ready to merge.

November 14, 2026: PR #168's audit flagged `opentelemetry-api==1.45.1`
for `CVE-2026-126360` / `GHSA-mf5v-w3w3-f6cg`. The
[upstream advisory](https://github.com/open-telemetry/opentelemetry-python/security/advisories/GHSA-mf5v-w3w3-f6cg)
identifies `1.45.2` as patched. The runtime input now requires
`opentelemetry-api>=1.45.2,<2`; runtime and development locks were regenerated
for Python 3.12/Linux using uv 0.13.8. Only that package's pinned version changed.

Local verification used a fresh Python 3.12.5 environment installed from the
updated development lock. `pip check` passed; the backend suite reported
293 passed and 45 skipped. Both Python locks passed `pip-audit==2.10.1`, and
the npm lock audit reported zero vulnerabilities. These are local results;
PostgreSQL-specific CI and hosted Auth acceptance remain separate. No audit
exception, workflow bypass, or shared-environment change was introduced.

To run the optional GitHub dependency-review job, set
`DEPENDENCY_REVIEW_ENABLED` to the string `true` after confirming dependency
graph access for the repository's current visibility. If the pending private
visibility change completes, confirm GitHub Advanced Security licensing first.
When the variable is unset or `false`, the job is skipped while the lockfile
audits still run.
