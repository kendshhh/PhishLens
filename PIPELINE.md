# PhishLens Pipeline

## Status

This pipeline is planned.

Automated application checks and deployment are not configured
or verified yet. Review enforcement has been verified on setup PR #2.

## Delivery Flow

Task branch → Pull request → Automated checks → Teammate approval
→ Merge to main → Automated checks → Automatic deployment
→ Deployed verification

## Pull Request Checks

| Stage | Purpose | Implementation dependency |
|---|---|---|
| Install | Install reproducible dependencies | Committed dependency files |
| Lint | Detect source problems | Python and JavaScript lint configuration |
| Build | Validate and package runnable components | Verified backend and extension build commands |

Checks must run automatically on every pull request.

Exact commands will be recorded after application owners implement
and verify them. Checks must fail when the checked component is broken.
Missing components or suppressed errors must not produce misleading
successful runs.

Regular AI tests will use mocked inference without model downloads.
A successful actual-model call will be recorded separately.

## Deployment

Every merge to main must deploy automatically after successful checks.

- Proposed backend host: Render.
- Database host: Neon.
- Service creation: pending runnable backend.
- Build, start, and migration commands: pending verification.
- Automatic deployment: not configured.
- Public application URL: pending.

A successful build alone does not prove deployment succeeded.
Verify the deployed version and the frontend-to-database connection.

## Merge Protections

Main must require:

- A pull request.
- At least one teammate approval.
- Passing required CI checks.
- Resolved review conversations.

Review enforcement was verified on setup PR #2:
GitHub requires approval and blocks merging while review is pending.

Required CI status checks remain pending the first working workflow.
The complete merge gate is therefore not finished.

## Database Connections

The database is PostgreSQL hosted on Neon.

- Production branch: production.
- Development branch: development.
- Region: AWS Asia Pacific 1 (Singapore).
- Database: neondb.
- DATABASE_URL: pooled connection for application queries.
- MIGRATION_DATABASE_URL: direct connection for migrations.

Both connection URLs must target the intended database branch.
The backend and migration configuration must explicitly read their
respective variables using the selected PostgreSQL driver.

Routine CI database checks will use an isolated test database.
Ordinary PR checks must not use production Neon credentials.

Neon branches are provisioned.
Application connection testing and migrations remain pending.

## Secrets

Local secrets belong in ignored .env files.
.env.example contains configuration placeholders only.

Deployment secrets belong in the host or CI secret store,
with separate configuration for development and production.

Database credentials and backend secrets must never be included
in the Chrome extension.

## Verification and Evidence

Record:

- Pull request and check-run links.
- Evidence that a broken change fails CI and the repaired change passes.
- Deployed commit and public URL.
- Frontend → backend → database verification.
- Confirmation that database records survive redeployment.
- Pipeline duration and deployment failures.

Update docs/devops/metrics.md with actual measurements,
sample counts, and supporting links.

Application checks, deployment, and measurements remain pending.