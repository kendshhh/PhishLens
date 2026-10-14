# PhishLens Pipeline

## Status

Backend scaffold CI and automatic deployment are implemented
and verified.

GitHub Actions installs dependencies, checks compatibility,
lints Python, tests /health, and checks Python compilation.

Render deploys main automatically after CI checks pass.
Automatic deployment was verified for commit 8a8634e,
followed by a successful public /health check.

Extension checks, PostgreSQL integration checks, and AI tests
remain pending. Compilation is basic validation, not the
complete application build stage.

## Delivery Flow

Task branch → Pull request → Automated checks → Teammate approval
→ Merge to main → Automated checks → Automatic deployment
→ Deployed verification

## Workflow Triggers

Workflow file: .github/workflows/ci.yml

- Every pull request triggers backend checks.
- Every push to main, including a merged PR, triggers backend checks.
- Render deploys changes to main after CI checks pass.

The workflow uses Python 3.12 on an Ubuntu runner.
Render is configured to use Python 3.12.10.

## Implemented Backend Checks

| Stage | Purpose | Command |
|---|---|---|
| Install runtime dependencies | Install pinned application packages | python -m pip install -r backend/requirements.txt |
| Install development dependencies | Install pinned checking tools | python -m pip install -r backend/requirements-dev.txt |
| Dependency compatibility | Detect incompatible installed dependencies | python -m pip check |
| Lint | Check backend Python code | python -m ruff check backend |
| API test | Verify the health endpoint's status and response | python -m pytest backend/tests -q -p no:cacheprovider |
| Compilation | Check Python source compilation | python -m compileall -q backend/app |

Commands run from the repository root.

Disabling pytest's cache avoids a local cache-permission issue.
It does not disable tests or suppress test failures.

A failed command fails the job. Errors must not be suppressed
to produce a misleading successful run.

## Coverage Still Needed

- Chrome extension linting, validation, and packaging.
- PostgreSQL migration and integration checks.
- Database-backed API and frontend verification.
- Mocked AI tests when the inference adapter is available.

Regular AI tests should use mocked inference without model downloads.
Successful actual-model calls must be recorded separately.

## Deployment

- Backend host: Render.
- Instance plan: Free.
- Service: phishlens-api.
- Deployment branch: main.
- Root directory: repository root; the field is blank.
- Python version: 3.12.10.
- Auto-Deploy: After CI Checks Pass.
- Public URL: https://phishlens-api-ocvt.onrender.com
- Health check path: /health.

Build command:

    python -m pip install -r backend/requirements.txt

Start command:

    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT

Render supplies PORT at runtime.

Automatic deployment was verified after PR #12 merged:
commit 8a8634e became Live without a manual deployment trigger.

Public /health returned:

    {"status":"ok","service":"phishlens-api"}

This verifies the API process only.
It does not establish database, frontend, or AI integration.

## Merge Protections

Main is configured to require:

- A pull request.
- At least one teammate approval.
- Passing Backend checks from GitHub Actions.
- Resolved review conversations.

Stale approvals are dismissed after new commits.
Administrator bypass, force pushes, and branch deletion are disabled.

Review enforcement was observed on setup PR #2.
The required backend check and teammate approval were verified
on PR #11 before merging.

## Database Connections

The selected database is PostgreSQL hosted on Neon.

- Production branch: production.
- Development branch: development.
- Region: AWS Asia Pacific 1 (Singapore).
- Database: neondb.
- DATABASE_URL: pooled connection for application queries.
- MIGRATION_DATABASE_URL: direct connection for migrations.

Both URLs must target the intended database branch.
Backend and migration code must explicitly read their respective
variables using the selected PostgreSQL driver.

Routine CI database checks will use an isolated test database.
Ordinary PR checks must not use production Neon credentials.

Neon branches are provisioned.
Application connection testing and migrations remain unverified
in this recorded baseline.

## Secrets

- Local credentials belong in ignored .env files.
- .env.example contains configuration placeholders only.
- Deployment secrets belong in the host or CI secret store.
- Development and production use separate configuration.
- Database credentials and backend secrets must never be
  included in the Chrome extension.
- Private emails and datasets must not enter Git.

## Verified Evidence

- [Backend scaffold PR #11](https://github.com/kendshhh/PhishLens/pull/11)
- [Runbook PR #12](https://github.com/kendshhh/PhishLens/pull/12)
- [Intentional failing CI run](https://github.com/kendshhh/PhishLens/actions/runs/38430884810)
- [Repaired passing CI run](https://github.com/kendshhh/PhishLens/actions/runs/38431990720)
- [Runbook PR CI run](https://github.com/kendshhh/PhishLens/actions/runs/38501111554)
- [Public health endpoint](https://phishlens-api-ocvt.onrender.com/health)

The intentional failure changed the expected HTTP status from
200 to 201. Restoring 200 produced passing CI.

Recorded deployment observations:
- First deployment: commit 717334d; 50.3 seconds.
- Automatic deployment: commit 8a8634e; 44.9 seconds.
- Public health response verified after automatic deployment.

Deployment duration is not complete merge-to-live lead time.
These observations do not prove an optimization trend.

## Documentation and Remaining Verification

Update docs/devops/metrics.md with actual measurements,
sample counts, and supporting links.

Use docs/devops/runbook.md for deployment and recovery procedures.

Still required:
- Database-backed frontend verification.
- Confirmation that records persist across redeployments.
- Complete pipeline averages and success-rate measurements.
- Merge-to-live lead time.
- Tested rollback and recovery evidence.
- Measured before-and-after optimization results.

Backend scaffold CI, automatic deployment, and public health
verification are complete. Full application integration,
aggregate metrics, and rollback verification remain pending.