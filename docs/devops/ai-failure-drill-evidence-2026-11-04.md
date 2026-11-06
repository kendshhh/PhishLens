# AI failure and recovery evidence - November 4, 2026

Status: deterministic CI failure evidence is verified. The AI-specific protected-staging failure drill is still pending owner approval and execution. This record does not close issue #95.

## Verified deterministic run

- Workflow: [CI run 41216421988](https://github.com/kendshhh/PhishLens/actions/runs/41216421988)
- Related change: [PR #104](https://github.com/kendshhh/PhishLens/pull/104), merged November 3, 2026.
- Tested source SHA: `cd5687e7884a13e86d0f7c7a96d48163c6dac316`.
- Run: October 31, 2026, 15:46:11-15:48:41 UTC (150 seconds total).
- Backend job: 66 seconds. This is CI job duration, not failure detection or service recovery time.
- Deterministic AI contract/failure checks: 87 passed, 0 failed, 0 skipped.
- Required PostgreSQL cases: 12 passed using synthetic test data.
- Provider requests: 0. Production writes: 0.
- Model revision: not applicable; this run used deterministic mock/failure injection, not model inference.
- Hosted staging jobs: skipped because the PR was still a draft. No staging deployment or live AI drill is claimed.
- Artifact: `Backend-Test-Evidence`, created October 31, 15:47:41 UTC. GitHub retention currently expires it November 7, 15:47:40 UTC; archive the redacted artifact before expiry if it is needed for the November 11 consultation.

The simulated checks cover the supported unavailable, timeout, quota, malformed-output, database-save-failure, no-partial-record, and later-healthy-request paths. They prove deterministic contract behavior in CI. They do not measure a live outage or recovery.

## Timings and limitations

| Measure | Result |
|---|---|
| CI workflow elapsed time | 150 seconds |
| Backend test job | 66 seconds |
| AI failure detection time | Not measured; failures were injected in tests |
| AI service recovery time | Not measured; no live service outage was induced |
| Provider/model response latency | Not applicable; no live inference was sent |
| Production impact | None; no production writes or configuration changes |

A separate staging-only deployment rollback and restore rehearsal is recorded in the [deployment and recovery runbook](runbook.md). It restored the staging service in 200.753 seconds, with independent verification at 233.408 seconds. That was an infrastructure recovery rehearsal, not an AI-provider failure drill; do not combine the timings.

## Repeatable local UI demonstration

The [AI failure demo guide](../ai-failure-demo.md) describes how to run the backend with Gemini mode selected but credentials intentionally unset. The expected result is a controlled `503 analysis_unavailable` response and the extension's unavailable state, before any provider network call. It uses the analysis-only endpoint and does not persist a saved report. The demo has not been represented here as a completed browser run.

## Stop and recovery steps

1. Before dispatching a real provider smoke, confirm the protected staging target, exact deployed SHA, approved provider/model, one-request cap, owner-approved per-run cost limit, provider-side quota, and required environment review.
2. If those controls are not approved, do not dispatch. Disable future eligibility by setting `AI_PROVIDER_SMOKE_ENABLED=false` or removing the approved staging variables. The workflow is manual-only and unscheduled.
3. If a live smoke request has started, do not retry it. The workflow allows at most one fixed synthetic request and stops on identity, timeout, quota, or response failures.
4. If a staging deployment needs rollback, follow the staging procedure in the [deployment and recovery runbook](runbook.md): identify the known-good app SHA and schema revision, restore the verified staging SHA, then check `/version`, `/health`, `/ready`, and migration head. Coordinate database recovery with Trixia. Do not run this procedure against production to satisfy an evidence checkbox.

## Remaining owners and evidence

- **Kendra:** preserve the CI artifact before expiration, keep the smoke disabled until approvals are present, and record run identities and limits.
- **Trixia:** confirm the backend failure contract and safe saved-analysis persistence behavior.
- **Wilberr:** review failure expectations alongside model output and evaluation thresholds.
- **Staging owner:** confirm target identity, protected-environment approval, quota/cost limit, and whether an AI-specific staging failure injection is supported.

To complete the AI-specific drill, record its exact source, backend deployment and model revisions; identify each live or simulated failure; record sample count and measured detection/recovery times where an actual staging event occurs; and keep unavailable timings marked as not measured. Obtain the required review before marking issue #95 complete.



## Artifact archive confirmed - November 5, 2026

The unexpired GitHub artifact was downloaded and preserved at
`evidence/ai-regression-41216421988.zip` (7,527 bytes). Its local SHA-256
`e072f470a8ce243f30df7a6d1705f3330255e25f531d75d2f0d40dc8458cb1d4`
matches GitHub's artifact digest, so the archived ZIP is byte-for-byte identical
to artifact 13048790616. It contains `ai-regression.json`, `summary.json`,
and `pytest.xml`.

The preserved report records 87/87 selected deterministic AI checks passed
with 0 failures and 0 skips; 12/12 required PostgreSQL cases passed; and 253
total API/PostgreSQL tests with 1 skip. Its simulated failure harness took
1.957 seconds. That is test-harness runtime only, not live provider detection
or service recovery time.