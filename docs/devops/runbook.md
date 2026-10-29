# Deployment and Recovery Runbook

## Historical October 21 playbook handoff

See [October 21 close-out](playbook-closeout-2026-10-21.md) for current evidence,
the corrected Week 2 instructions and remaining integration gates. Production
evidence run 39449283551 passed for main `149808e`; this is dated observer evidence,
not a claim that every later independent endpoint probe succeeded.

## Current post-merge verification — October 29, 2026 00:31 UTC

PR #86 merged as `1344fcb061272bac93ced5911f1ab8fbb3b6785d`; production deploy
`dep-dbh8v6ivcj2c73fql7c0` is Live on that commit. Read-only `/version`,
`/health`, and `/ready` requests returned HTTP 200, with the expected production
identity and connected database. Staging deploy `dep-dbh8s8942hec73bo7bt0` is
Live on candidate `fc7db9bf5441af4cd68ec2efbcbc7ac8efdc20a2`; the same read-only
checks returned HTTP 200 and connected readiness.

The guarded synthetic CRUD verifier passed against that exact staging SHA after
the protected staging gate and the Neon `phishlens_staging_app` least-privilege
check passed. It cleaned up its synthetic record. Production remains read-only;
production persistence, installed-Chrome behavior, a comparable pipeline gain,
and complete recovery duration remain unverified.

## Recorded production and prior staging verification — October 28, 2026 17:07 UTC

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
PR #86 Hosted staging passed and deployment
[`dep-dbh2cjnf3r2c73emoprg`](https://dashboard.render.com/web/srv-db92irlg1s2s739404i0/deploys/dep-dbh2cjnf3r2c73emoprg)
is Live on exact merge SHA `d46cc09ecf7258a6bd10475f00cc8da035ef5e9a`.
Read-only `/version`, `/health`, and `/ready` GETs at 17:07 UTC returned HTTP
200; version matched the candidate and readiness reported the database connected.
The mapped Neon target is `pr-58-staging/phishlens_dev`. A read-only grant check
at 17:05 UTC still found public-schema `CREATE` and `INSERT`, `UPDATE`, and
`DELETE` on the migration and application tables for the runtime role. No grant
change or database write was made. The environment owner must remove the excess
privileges and repeat the read-only check before synthetic CRUD is run. The
historical guarded CRUD evidence on deactivated SHA `e3c6e37` does not verify this
candidate.

## Historical PR #86 staging gate — October 28, 2026 17:31 UTC

At this snapshot, current PR head `dcafd2f539a3dafdc6a3c50e62cc35ae71c24d86`
passed all automated checks except Hosted staging, pending at the protected
`staging` environment; connected diagnostics returned no steps or reason. The
Live staging candidate described above belongs to the previous PR code head and
does not establish this head's deployment or acceptance. The runtime role still
has excess grants, so staging CRUD remains blocked until the environment owner
cleans them up and a read-only recheck passes.

Production CRUD persistence across refresh/redeploy and installed-Chrome behavior
remain unverified. Production probes establish live version, process health, and
database readiness only. See [Kendra's Week 1–4 closeout](kendra-week1-4-closeout-2026-10-28.md)
for her per-week status and remaining owner-dependent acceptance.

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
