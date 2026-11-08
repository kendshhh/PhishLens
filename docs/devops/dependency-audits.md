# Dependency audits on private repositories

The GitHub dependency-review action relies on GitHub's dependency graph and is
supported for private repositories only when GitHub Advanced Security is
licensed. In the current private PhishLens setup, the action fails before it
can inspect dependency changes.

The `.github/workflows/dependency-review.yml` workflow therefore runs two
lockfile audits on every pull request and push to `main`:

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

The GitHub dependency-review action remains available as an optional additional
check. Set the repository Actions variable `DEPENDENCY_REVIEW_ENABLED` to the
string `true` only after the private repository has an enabled dependency graph
and GitHub Advanced Security license. When unset or set to `false`, that
GHAS-only job is skipped and the lockfile audits still run. A skipped
dependency-review job does not mean the dependencies have no vulnerabilities.
