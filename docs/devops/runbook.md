# Deployment and Recovery Runbook

## Historical October 21 playbook handoff

See [October 21 close-out](playbook-closeout-2026-10-21.md) for current evidence,
the corrected Week 2 instructions and remaining integration gates. Production
evidence run 39449283551 passed for main `149808e`; this is dated observer evidence,
not a claim that every later independent endpoint probe succeeded.

## Current verification — October 28, 2026

Production service `phishlens-api` is configured on `main` with Render auto-deploy
trigger `checksPass`. At 2026-10-28 15:39 UTC, main was
`6414914dfa8eb8322839597c4cd6912145a442a0`. Main CI run
[40715810349](https://github.com/kendshhh/PhishLens/actions/runs/40715810349)
passed Backend and Extension; Workflow lint
[40715810515](https://github.com/kendshhh/PhishLens/actions/runs/40715810515)
passed. Render deployment
[`dep-dbh18p6i0phs73d1mtag`](https://dashboard.render.com/web/srv-db7eap25b2lc73fkelpg/deploys/dep-dbh18p6i0phs73d1mtag)
is Live on that exact SHA. `/version`, `/health`, and `/ready` returned HTTP 200;
version reported production and the matching SHA, and readiness reported the
database connected. See [metrics.md](metrics.md) for the 73.525-second deployment
duration; merge-to-live time for this SHA is not measured.

Staging service `phishlens-staging` is configured on `main` with auto-deploy off.
At 15:43 UTC, its latest Live deployment was
[`dep-dbh14vbl550s738ddfc0`](https://dashboard.render.com/web/srv-db92irlg1s2s739404i0/deploys/dep-dbh14vbl550s738ddfc0)
on SHA `57da457be77fcf7a132e3a5e2f0d704c676040d6`; `/version`, `/health`, and
`/ready` returned HTTP 200 and identified staging/database readiness. That SHA
diverges from current main and PR #86 head, so it is not exact-candidate evidence.
The earlier guarded synthetic CRUD result was on deactivated SHA `e3c6e37`; no
new staging or production CRUD write was made. The exact Neon host mapping and
staging app-role grants still need private owner verification.

Production CRUD persistence across refresh/redeploy, installed-Chrome behavior,
and exact-current-candidate staging behavior remain unverified. The production
probes establish live version, process health, and database readiness only.

For each deployment, retain main SHA, successful main CI, reviewer approval,
Render deploy ID/trigger/live timestamp, and the live `/version`/health/readiness
observations. Archive package `evidence.json` alongside the ZIP before expiry;
compare its source/tested SHA and ZIP hash before installing. Packaging does not
establish browser execution or database isolation.

Before a rollback, record both app revisions and their expected schema revisions.
Current source has migration `0001_initial_schema`; compare migration trees and
coordinate with Trixia if either revision introduces schema changes. Do not run
reverse migrations or a production failure drill to fill an evidence checkbox.
Reuse the verified October 14 drill; its complete recovery time remains unknown.
For the next necessary recovery, record incident start, action start, live result,
independent restored `/version`/health/readiness time, and actual affected behavior.

The [Secretary pilot operator guide](secretary.md) adds exact-SHA preview and
production observation. Its observer produces `metrics.json` and, on failure, an
incident draft under the Actions artifact `Veriqo-Production-Evidence`. Inspect
the exact failed deployment in Render before deciding recovery. The pilot never
deploys production, changes secrets, applies production migrations, or executes
rollback. The existing human recovery procedure below remains authoritative.

## Historical initial scaffold status

The FastAPI backend scaffold is publicly deployed on Render.

- Public /health endpoint verified.
- Auto-Deploy configured as After CI Checks Pass.
- Automatic deployment verified after PR #12 merged.
- Historical automatic-deployment baseline: 8a8634e. Later deployments are
  recorded in metrics.md; confirm the current Live SHA in Render for each release.
- Public /ready independently returned HTTP 200 and database connected.

Database connectivity is verified; schema-backed frontend and AI integration
remain pending. Rollback and restoration were exercised, including one failed
restoration attempt. See incidents.md for the evidence and limitations.

## Service Configuration

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

Before merging, follow [pre-merge staging](staging.md): all four required checks,
the exact PR commit live on staging, Chrome verification with the staging package,
and teammate approval. Missing staging settings must be fixed before merge.

1. Open a focused PR.
2. Pass required checks and obtain teammate approval.
3. Merge into main.
4. Confirm main CI passes.
5. Confirm Render deploys that commit automatically.
6. From GitHub Actions, manually run **Production evidence** on `main` after the
   exact commit is live. Retain its metrics artifact and confirm the exact SHA.
7. Verify /health and the behavior affected by the change.
8. Record merge-to-live time and evidence.

The observer is manual and post-deploy so Render's **After CI Checks Pass** gate
does not wait on a check that itself waits for the deployment. It never deploys
or rolls back production.

For database-dependent changes, also request /ready and expect HTTP 200 with
{"status":"ready","database":"connected"}. Keep /health as the process
health check. Readiness currently executes SELECT 1; it does not verify tables
or records. Confirm DATABASE_URL's intended Neon branch privately in the host.
The base URL / has no homepage and may correctly return 404.

## Deployment Failure

1. Open Render deployment logs.
2. Identify the first meaningful error.
3. Check dependency installation, Python version, start command
   and environment configuration.
4. Prepare a focused repair PR and repeat the normal review process.
5. Record the incident, impact, repair and recovery time.

Never paste secrets into issues or logs shared with teammates.

## Rollback Plan

Rollback to 717334d was successful in 35.7 seconds. Restoration to 8a8634e
succeeded on retry after an initial health-check/port-detection timeout.
Full restoration duration remains unmeasured. This was a planned drill.

After at least two successful deployments:
1. Identify the last known-good deployment and its commit.
2. Use Render's available rollback control.
3. Verify /health and affected application behavior.
4. Check the Auto-Deploy setting after rollback.
5. Coordinate a reviewed correction before resuming normal deployment.
6. Record the result and recovery time.

Dashboard rollback automatically disables Auto-Deploy. Deploying a specific
commit also disables it. Restore After CI Checks Pass only after verifying the
intended version and reviewing any newer main changes.

To restore a known-good version during a drill, use Manual Deploy > Deploy a
specific commit and select its verified SHA. Confirm the Live SHA and /health,
then restore Auto-Deploy. A health response alone cannot identify a version.

If replacement deployment times out, inspect that deployment's own logs.
General service logs can come from the still-running older instance. Preserve
the health check; do not change ports or suppress errors without evidence.

Rolling back application code does not automatically reverse
database migrations. Coordinate database recovery with Trixia.

## Evidence

- Public URL: https://phishlens-api-ocvt.onrender.com
- Health endpoint: https://phishlens-api-ocvt.onrender.com/health
- First deployment: commit 717334d; duration 50.3 seconds.
- Verified automatic deployment: PR #12, commit 8a8634e.
- Automatic deployment duration: 44.9 seconds.
- Post-deployment health response:
  {"status":"ok","service":"phishlens-api"}
- Rollback verification: successful operation; see incidents.md.
- Database readiness: public /ready returned HTTP 200 and database connected.

Deployment duration is not the full merge-to-live lead time.
