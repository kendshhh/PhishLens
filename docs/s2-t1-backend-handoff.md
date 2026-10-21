# S2-T1 Persistent CRUD Backend Handoff

- Issue: #42
- Branch: `feat/42-persistent-crud`
- Status: Implemented and tested locally; review, CI and deployed verification pending.

## Endpoint boundaries

- `POST /analyses` returns an unsaved live result.
- `POST /api/analyses` runs inference, validates output and commits a saved record.
- The server selects the synthetic demo user. This is not real-user authentication.
- Browser-supplied ownership, prediction, confidence and provenance fields are rejected.

## Saved CRUD contract

| Operation | Endpoint | Success |
|---|---|---|
| Create | POST `/api/analyses` | 201, saved detail |
| List | GET `/api/analyses` | 200, `{"items": [...]}` |
| Detail | GET `/api/analyses/{id}` | 200, saved detail |
| Update | PATCH `/api/analyses/{id}` | 200, saved detail |
| Delete | DELETE `/api/analyses/{id}` | 204, empty body |

Unknown or out-of-scope record IDs return 404. Invalid UUID paths return 422.
Queries use the server-selected demo user.

### Create

```json
{"body": "Synthetic email body"}
```

`subject` may be omitted or empty and defaults to `""`; maximum 320 characters.
`body` is required, nonblank and at most 30,000 characters.
Extra fields are rejected.

The following is an illustrative mock response, not a captured deployment result:

```json
{
  "id": "29d80c39-ec0d-4db8-a6e5-87444ba2600c",
  "subject": "",
  "body": "Synthetic email body",
  "prediction": "spam",
  "confidence": null,
  "risk_level": "medium",
  "threat_indicators": [],
  "explanation": "Tactics: Mock analysis: AI_MODE=mock\nRecommendations: Set AI_MODE=gemini and configure Gemini credentials for AI analysis.",
  "notes": null,
  "feedback": null,
  "analysis_mode": "mock",
  "analysis_provenance": {
    "provider_mode": "mock",
    "model": null,
    "model_revision": null,
    "prompt_version": null,
    "explanation_source": null,
    "input_truncated": null,
    "windows_processed": null
  },
  "created_at": "2026-10-21T04:00:00Z"
}
```

List responses retain the existing summary fields; detail and create responses
add body, notes, feedback, mode and provenance.

### Update

```json
{"notes": "Reviewed synthetic email", "feedback": "false_positive"}
```

Only notes and feedback are accepted. At least one must be supplied.
Notes allow up to 2,000 characters. Feedback accepts `none`,
`false_positive`, `false_negative`, or null.
Omitted fields remain unchanged; explicit null clears the supplied field.
PATCH never reruns inference.

```json
{"notes": null}
```

### Delete

DELETE returns HTTP 204 without a response body.
A subsequent detail request returns:

```json
{"detail": "Analysis not found"}
```

## Output mapping and legacy compatibility

- Saved `prediction` preserves `legitimate`, `spam`, or `phishing`.
- New risk mapping is legitimate → low, spam → medium, phishing → high.
- Missing confidence remains null; no score is invented.
- Evidence becomes `{type: "evidence", quote: text, detail: reason}`.
- Explanation formats tactics and recommendations as readable text.
- Mock results use mode `mock`; Gemini results use mode `real`.
- Provenance preserves provider mode, model/revision, prompt version,
  explanation source, truncation and window metadata without invented values.
- Migration `0002_analysis_provenance` adds nullable mode and JSONB provenance.
- Legacy rows may retain null mode/provenance and nullable result fields.
  Existing indicators without quotes remain readable; absent quotes are omitted.

## Persistent create errors

These responses use the saved CRUD `detail` format, separately from the
unsaved endpoint's structured `error` envelope.

| HTTP | Code |
|---|---|
| 422 | invalid_input |
| 502 | analysis_failed |
| 503 | analysis_unavailable or storage_unavailable |
| 504 | analysis_timeout |
| 500 | internal_error |

```json
{"detail": "Email analysis timed out", "code": "analysis_timeout"}
```

Client responses exclude private input, credentials and exception details.

## Runtime and transaction limits

Persistent create uses one monotonic deadline with a 15-second inference budget
and a 20-second operation target. Mock and Gemini inference run in a supervised
process with bounded admission per API process. Gemini uses one SDK attempt
and a 15,000 ms configured HTTP timeout.

Local persistent create currently returns 503 because supervised prewarming
has not been implemented.

Inference workers never save records. Persistence begins only after timely,
validated inference. Database connection and SQL waits use the remaining
operation budget. A 201 response requires commit acknowledgement.

Cancellation and process/database cleanup still require target-host testing;
these settings do not establish a production wall-clock guarantee.
A timeout during or after commit can leave a saved row. Idempotency and
outcome reconciliation are not implemented; clients must not assume every
timeout means no record exists.

## Local verification

Ruff and `git diff --check` passed.

Without database opt-in:

```bash
env -u RUN_DATABASE_TESTS ./.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider
```

Result: 180 passed, 12 skipped.

Against disposable local PostgreSQL:

```bash
DATABASE_URL='postgresql://127.0.0.1:5432/phishlens_s2_t1_test' RUN_DATABASE_TESTS=1 ./.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider --ignore=backend/tests/test_history_postgres.py --ignore=backend/tests/test_seed_integrity.py
```

Result: 190 passed. The excluded tests explicitly require seeded
`phishlens_dev`; they were not verified by this command.

The new `test_saved_create_postgres.py` file passed all 7 cases:
complete HTTP CRUD, three inference-failure cases, rollback after INSERT,
database lock timeout, and the unsaved live-analysis boundary.

Evidence uses real local PostgreSQL with mock inference. It does not prove
real-provider availability, hosted operation or connected frontend acceptance.

## Remaining before completion

- Record the final source SHA and PR/CI links.
- Reconcile current shared AI changes and review the final combined diff.
- Publish and review the contract with Leyan and Wilberr, including 504 handling,
  provenance keys, runtime limits and uncertain commit outcomes.
- Coordinate mandatory PostgreSQL test registration with Kendra.
- Pass required CI, including the seeded database tests.
- Coordinate the forward migration and configuration on the approved hosted
  database; no Neon migration or hosted write is claimed here.
- Verify CRUD through the connected client against the identified deployed SHA.
- Obtain teammate review and update issue #42, the sprint log and board.

## Windows async persistence follow-up

The supported Python 3.12 startup command explicitly selects the event-loop
factory required by async Psycopg on Windows:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --loop backend.core.event_loop:new_event_loop
```

Optional `--reload` uses the same factory. The staging startup script also
selects it explicitly. Bare Uvicorn startup without this option is not the
documented Windows configuration.

`backend/tests/conftest.py` selects WindowsSelectorEventLoopPolicy for the
Windows pytest process, covering asyncio.run and TestClient-based tests.
Mac and Linux retain their existing test policy.

For an already migrated, disposable local database named
phishlens_s2_t1_test, run:

```powershell
$env:DATABASE_URL = 'postgresql://127.0.0.1:5432/phishlens_s2_t1_test'
$env:RUN_DATABASE_TESTS = '1'
$env:AI_MODE = 'mock'
.\.venv\Scripts\python.exe -m pytest backend/tests/test_saved_create_postgres.py -q -p no:cacheprovider
```

This uses real local PostgreSQL and synthetic mock inference. It is not a
command for Neon or production. The separate full CI gate still requires
its seeded disposable phishlens_dev target and all mandatory database cases.

Mac verification of factory selection and focused tests does not establish
Windows acceptance. Wilberr must verify the updated candidate on Windows,
including actual saved create against disposable PostgreSQL and normal
single-process API startup without reload. Record source SHA, Python/Uvicorn/
Psycopg versions, commands, results and cleanup.
