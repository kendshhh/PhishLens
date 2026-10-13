# PhishLens Pipeline

## Status

This pipeline is planned. No automated checks or deployments
have been verified yet.

## Delivery Flow

Task branch → Pull request → Automated checks → Teammate approval
→ Merge to main → Automated checks → Automatic deployment
→ Deployed verification

## Pull Request Checks

| Stage | Purpose | Implementation dependency |
|---|---|---|
| Install | Install reproducible dependencies | Committed dependency files |
| Lint | Detect source problems | Python and JavaScript lint configuration |
| Build | Validate and package runnable components | Backend and extension build commands |

Commands will be recorded after the application owners implement
and verify them. Checks must fail when the application is broken.

## Deployment

Every merge to main must deploy automatically after successful checks.

Hosting provider and deployment configuration are not finalized.
A successful build alone does not prove deployment succeeded.

## Merge Protections

Main must require:
- A pull request.
- At least one teammate approval.
- Passing required checks.

Protection settings are not verified yet.

## Secrets

Local secrets belong in ignored .env files.
Deployment secrets belong in the host or CI secret store.
Production credentials must not be exposed to pull request checks
or included in the Chrome extension.

## Verification and Evidence

Record:
- Pull request and check-run links.
- Deployed commit and public URL.
- Deployed verification results.
- Pipeline duration and deployment failures.

Application checks, deployment, and measurements remain pending.