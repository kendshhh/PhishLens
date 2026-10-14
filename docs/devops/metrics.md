# Pipeline Metrics

Record actual measurements before each consultation.
Do not invent results or treat individual observations as averages.

## Sprint 1 Observations

| Observation | Result | Evidence |
|---|---|---|
| Main CI after PR #11 merged | Passed; displayed duration 18 seconds | Commit 717334d |
| Initial Render deployment | Successful; 50.3 seconds | Commit 717334d |
| Runbook PR backend-check job | Passed; 11 seconds | CI run linked below |
| Automatic deployment after PR #12 merged | Successful; 44.9 seconds | Commit 8a8634e; trigger Auto-Deploy |
| Public /health after automatic deployment | Expected JSON returned | Public endpoint linked below |

Job duration, workflow duration, and deployment duration are
different measurements. Do not combine them into one average.

## Required Sprint Metrics

| Metric | Result |
|---|---|
| Measurement period | Runs started October 14, 2026, 00:15:46-12:56:04 GMT+8; snapshot through readiness merge 2a70ad3 |
| PR pipeline runs sampled | 16 completed, single-job runs |
| Average PR pipeline duration | Backend job execution: 25.94 seconds (0.43 minutes); queue/orchestration overhead excluded |
| Main pipeline duration | Average backend job execution: 32.14 seconds (0.54 minutes), 7 runs |
| Pipeline success rate | 20/23 = 86.96%, including 2 intentional drill failures; PR 13/16 = 81.25%, main 7/7 = 100% |
| Successful production deployments | Multiple dashboard-evidenced automatic, initial and manual deployments; full deduplicated Render inventory pending, so no aggregate count claimed |
| Merge-to-live lead time | Not measured |
| Failed production deployments | 1 observed restoration timeout; full Render history not directly accessible |
| Recovery time | Rollback operation: 35.7 seconds; complete restoration/outage recovery time not measured |

These values describe the recorded baseline, not necessarily
the latest state of every run or deployment.

## Measurement Method

- Record the measurement period and sample count.
- Use complete GitHub Actions run timings for pipeline duration.
- Keep individual job timings separate from workflow timings.
- Calculate success rate as successful completed runs divided
  by all successful and failed completed runs in the period.
- Record cancelled and in-progress runs separately.
- Include intentional CI drill failures in the overall success
  rate and identify them explicitly.
- Measure merge-to-live lead time from merge to verified live service.
- Measure recovery time from service failure to restored service.
- Include links supporting each result.

Deployment duration alone is not merge-to-live lead time.

## CI Failure-and-Repair Evidence

- [Intentional failing run](https://github.com/kendshhh/PhishLens/actions/runs/38430884810)
- [Repaired passing run](https://github.com/kendshhh/PhishLens/actions/runs/38431990720)

Failure introduced: the test expected HTTP 201 while /health
returned HTTP 200.

Repair: restored the expected status to HTTP 200.

This was an intentional PR CI drill, not a failed production deployment.

## Deployment Evidence

- [Runbook PR CI run](https://github.com/kendshhh/PhishLens/actions/runs/38501111554)
- [Backend scaffold PR #11](https://github.com/kendshhh/PhishLens/pull/11)
- [Runbook PR #12](https://github.com/kendshhh/PhishLens/pull/12)
- [Public health endpoint](https://phishlens-api-ocvt.onrender.com/health)

Verified health response:

    {"status":"ok","service":"phishlens-api"}

Render observations:
- Initial deployment: commit 717334d; 50.3 seconds.
- Subsequent deployment: commit 8a8634e; 44.9 seconds.
- Subsequent trigger: Auto-Deploy.
- Auto-Deploy setting: After CI Checks Pass.

## Measured CI snapshot

[CI run evidence](ci-run-evidence.csv) records exact job start/end timestamps,
conclusions, commits, and source URLs from the public GitHub API.
There were 23 completed backend jobs: 20 success, 3 failure, no cancellations.
Two failures were deliberate drills and one was database-PR lint.
Excluding only the two deliberate drills gives 20/21 = 95.24%; this secondary
rate does not replace the inclusive 86.96% result.

Each run currently has one backend job. The calculated values measure execution
from job started_at to completed_at, not the entire workflow wall-clock duration.
Do not substitute the API updated_at timestamp for workflow completion time.
Coverage changed during this period, so these averages are not optimization evidence.

Additional dashboard observations:
- Manual deployment of 67538f8: 56.2 seconds.
- Automatic deployment of PR #13, a6336de: 48.9 seconds.
- Environment-save redeployment of 3ae80c2: 45.3 seconds, manual trigger.
- Another displayed Live deployment of 3ae80c2: 58.1 seconds; trigger not
  shown on that screenshot, so do not infer it from the duration alone.

Direct main CI sources:
- [PR #14 main run](https://github.com/kendshhh/PhishLens/actions/runs/38510446866)
- [PR #15 main run](https://github.com/kendshhh/PhishLens/actions/runs/38512502699)
- [Readiness main run](https://github.com/kendshhh/PhishLens/actions/runs/38513965042)

Direct Render deployment record links remain to be collected.

The health endpoint verifies the backend process only.
Database connectivity is established separately by the public /ready endpoint,
which was independently checked and returned HTTP 200 with
{"status":"ready","database":"connected"}. This does not prove the full
schema, correct environment selection, frontend integration, or AI behavior.

## Optimization Log

| Change | Before | After | Evidence |
|---|---|---|---|
| No measured optimization verified | Not measured | Not measured | Pending |

The two deployment durations are baseline observations.
Their difference alone does not prove an optimization.

## Remaining Measurements

- Extend the recorded snapshot as new runs finish.
- Capture whole-workflow duration separately from job execution time.
- Record merge-to-live lead time.
- Audit failed production deployments.
- Collect restoration duration and attach rollback deployment links.
- Measure future optimizations using comparable before-and-after runs.
