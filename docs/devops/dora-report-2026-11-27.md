# PhishLens DORA delivery report — 2026-11-27

**Snapshot:** `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0`<br>
**Window:** 2026-10-30 05:58 UTC through 2026-11-27 05:58 UTC (28.00 days)<br>
**Collected:** 2026-11-27T05:58:53.745515Z

This report contains the four DORA delivery metrics and the current fifth metric,
deployment rework rate. It also reports CI wall time as an internal pipeline
measure. DORA metric names and definitions follow the [current DORA guide](https://dora.dev/guides/dora-metrics/);
the course's “time to restore” is represented by failed-deployment recovery time.

| Metric | Result | Denominator and method |
|---|---|---|
| Change lead time | median 3.66 min; p90 8.61 min; range 2.26–19.81 min (n=60) | 60 unique merged PR SHAs matched exactly to the first successful Render deployment after merge, out of 142 merged PRs in the window. Uses merge-to-live as a reproducible proxy for commit-to-production; records without an exact SHA match are excluded. |
| Deployment frequency | 63 successful Render deploy records; 2.25/day (15.75/week) | 63 records with `live` or `deactivated` status divided by 28.00 days. This is the complete set assembled from the retained Nov 14 inventory and the current Render inventory. |
| Change fail rate | **Not measured** | Current source does not link production incidents or failed changes to the corresponding release SHA. Diagnostic only: 0/63 failed Render deployment attempts; this deploy-attempt proxy is not the DORA change fail rate. |
| Failed-deployment recovery time | not measured (no qualifying production recovery records) | Recovery requires timestamps from production failure detection to verified service restoration. The available source contains no qualifying production recovery event; this is not zero. |
| Deployment rework rate | not measured (deployments lack reviewed planned/unplanned classifications) | Requires each successful production deployment to be classified as planned or unplanned rework. No reviewed classification ledger is available; this is not zero. |
| CI workflow wall time (supplemental) | median 66.00 s; p90 91.00 s; range 46.00–423.00 s (n=117) | 117 timed main-push CI runs; outcomes across 117 completed runs: 115 success, 2 failure, 0 cancelled; successful-run share 98.29%. From run start to completion, excluding queue before start and environment wait outside the workflow run. |

## Optimization result

No current like-for-like before/after pipeline optimization is established. The
latest reusable comparison remains the October 21 staging-cache trial: two
samples per condition; the whole staging job averaged 40.5 seconds before and
44.0 seconds with cache. That experiment did not demonstrate an end-to-end gain.
The October 28 extension-cache trial also did not show a job-time improvement.
See [optimization evidence](optimizations.md). Keep this criterion open until a
specific workflow change is compared with the same event, checks, runner, and
queue/approval treatment over adequate samples.

## Sources and limits

- GitHub main CI runs: [https://api.github.com/repos/kendshhh/PhishLens/actions/workflows/ci.yml/runs?branch=main&per_page=100](https://api.github.com/repos/kendshhh/PhishLens/actions/workflows/ci.yml/runs?branch=main&per_page=100)
- Merged PR metadata: [https://api.github.com/repos/kendshhh/PhishLens/pulls?state=closed&per_page=100](https://api.github.com/repos/kendshhh/PhishLens/pulls?state=closed&per_page=100)
- Render production deploy inventory: [https://dashboard.render.com/web/srv-db7eap25b2lc73fkelpg/deploys](https://dashboard.render.com/web/srv-db7eap25b2lc73fkelpg/deploys)
- Retained Render inventory through Nov 14: `docs/devops/evidence/production-deploys-2026-11-14.csv`
- DORA definitions: [DORA software delivery metrics](https://dora.dev/guides/dora-metrics/)

Render deployments with `deactivated` status were previously live and later
superseded. Deployment frequency counts successful deploy records, including
repeat deploys of the same SHA; change lead time deduplicates by merged SHA.
Render's latest deploy record marked `live` is
`811980c2cbf70d9957146bf329627f0826a018f1`. This is
deployment metadata, not a successful HTTP version or user-flow check, and does
not imply that the current main commit has been released. No production user
data or inference telemetry is included.
