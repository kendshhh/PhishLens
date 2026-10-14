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
| Measurement period | Not finalized |
| PR pipeline runs sampled | Not calculated |
| Average PR pipeline duration | Not calculated |
| Main pipeline duration | One observed run: 18 seconds; complete sample pending |
| Pipeline success rate | Not calculated |
| Successful production deployments | 2 observed through commit 8a8634e |
| Merge-to-live lead time | Not measured |
| Failed production deployments | Not audited |
| Recovery time | Not measured |

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

Direct main CI run and Render deployment record links remain
to be collected.

The health endpoint verifies the backend process only.
Database, extension, and AI integration are not established
by this response.

## Optimization Log

| Change | Before | After | Evidence |
|---|---|---|---|
| No measured optimization verified | Not measured | Not measured | Pending |

The two deployment durations are baseline observations.
Their difference alone does not prove an optimization.

## Remaining Measurements

- Finalize the measurement period.
- Collect all relevant pipeline runs and calculate averages.
- Calculate pipeline success rate with drill failures identified.
- Record merge-to-live lead time.
- Audit failed production deployments.
- Verify rollback and record recovery time.
- Measure future optimizations using comparable before-and-after runs.