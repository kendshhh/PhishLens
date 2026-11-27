# PhishLens DORA delivery report — 2026-11-27

**Snapshot:** `88156d479d19eb0b8018ab76aa3170eb60079765`<br>
**Window:** 2026-10-30 11:04 UTC through 2026-11-27 11:04 UTC (28.00 days)<br>
**Collected:** 2026-11-27T11:04:33.245272Z

This report contains the four DORA delivery metrics and the current fifth metric,
deployment rework rate. It also reports CI wall time as an internal pipeline
measure. DORA metric names and definitions follow the [current DORA guide](https://dora.dev/guides/dora-metrics/);
the course's “time to restore” is represented by failed-deployment recovery time.

| Metric | Result | Denominator and method |
|---|---|---|
| Change lead time | median 3.66 min; p90 8.61 min; range 2.26–19.81 min (n=60) | 60 unique merged PR SHAs matched exactly to the first successful Render deployment after merge, out of 143 merged PRs in the window. Uses merge-to-live as a reproducible proxy for commit-to-production; records without an exact SHA match are excluded. |
| Deployment frequency | 63 successful Render deploy records; 2.25/day (15.75/week) | 63 records with `live` or `deactivated` status divided by 28.00 days. This is the complete set assembled from the retained Nov 14 inventory and the current Render inventory. |
| Change fail rate | **Not measured** | Current source does not link production incidents or failed changes to the corresponding release SHA. Diagnostic only: 0/63 failed Render deployment attempts; this deploy-attempt proxy is not the DORA change fail rate. |
| Failed-deployment recovery time | not measured (no qualifying production recovery records) | Recovery requires timestamps from production failure detection to verified service restoration. The available source contains no qualifying production recovery event; this is not zero. |
| Deployment rework rate | not measured (deployments lack reviewed planned/unplanned classifications) | Requires each successful production deployment to be classified as planned or unplanned rework. No reviewed classification ledger is available; this is not zero. |
| CI workflow wall time (supplemental) | median 66.50 s; p90 91.00 s; range 46.00–423.00 s (n=118) | 118 timed main-push CI runs; outcomes across 118 completed runs: 116 success, 2 failure, 0 cancelled; successful-run share 98.31%. From run start to completion, excluding queue before start and environment wait outside the workflow run. |

## Optimization result

One implemented, measured job-level improvement is documented in PR [#119](https://github.com/kendshhh/PhishLens/pull/119), merged on November 4 as
`98dd0dc13136f16c1159a9aedee870a84be066a3`: the cached, pinned-uv Backend
checks job median was 50.92 s versus 61.52 s for the pip baseline (`n=2` per
condition), 10.61 s or 17.2% lower. The samples used the same Backend checks
and passed; current `main` still uses pinned uv with caching, with the setup
action later updated in PR #283. This measures one backend job, not end-to-end
PR/main delivery, and the small sample does not establish a sustained trend or
a failure-rate improvement.

Other measured trials were not wins: the October 21 staging-cache trial's
whole-job median rose from 40.5 s to 44.0 s, and the October 28 extension-cache
trial did not improve whole-job time. See [optimization evidence](optimizations.md)
and the detailed [backend-job comparison](metrics.md#november-4-cached-uv-backend-job-comparison).
The rubric's requirement for multiple optimizations with a downward end-to-end
pipeline-time and failure-rate trend therefore remains open.

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
