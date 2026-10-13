# Deployment and Recovery Runbook

## Current Status

Render configuration is prepared.
Public deployment and rollback have not been verified.

## Planned Service Configuration

- Repository: kendshhh/PhishLens
- Branch: main
- Runtime: Python 3
- Python version: 3.12.10
- Instance plan: Free
- Root directory: repository root; leave the field blank
- Health check path: /health
- Auto-deploy: After CI Checks Pass

Build command:

    python -m pip install -r backend/requirements.txt

Start command:

    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT

## Initial Deployment

1. Confirm the backend PR is reviewed and merged.
2. Confirm CI passes on the merged main commit.
3. Verify the Render settings above.
4. Create the service and inspect deployment logs.
5. Confirm Auto-Deploy is set to After CI Checks Pass.
6. Open the service's public URL followed by /health.
7. Expect HTTP 200 and:
   {"status":"ok","service":"phishlens-api"}
8. Record the deployed commit, URL, deployment result and timings.

The health endpoint verifies the API process only.
It does not verify database access, AI inference or extension integration.

## Subsequent Deployments

1. Open a focused PR.
2. Pass required checks and obtain teammate approval.
3. Merge into main.
4. Confirm main CI passes.
5. Confirm Render deploys that commit automatically.
6. Verify /health and the behavior affected by the change.
7. Record merge-to-live time and evidence.

## Deployment Failure

1. Open Render deployment logs.
2. Identify the first meaningful error.
3. Check dependency installation, Python version, start command
   and environment configuration.
4. Prepare a focused repair PR and repeat the normal review process.
5. Record the incident, impact, repair and recovery time.

Never paste secrets into issues or logs shared with teammates.

## Rollback Plan

Rollback is untested.

After at least two successful deployments:
1. Identify the last known-good deployment and its commit.
2. Use Render's available rollback control.
3. Verify /health and affected application behavior.
4. Check the Auto-Deploy setting after rollback.
5. Coordinate a reviewed correction before resuming normal deployment.
6. Record the result and recovery time.

Rolling back application code does not automatically reverse
database migrations. Coordinate database recovery with Trixia.

## Evidence

- Public URL: pending
- First successful deployment: pending
- Automatic deployment after a later merge: pending
- Rollback verification: pending