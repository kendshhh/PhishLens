# S2-T1 Persistent CRUD Backend Handoff

- Issue: #42
- Branch: `feat/42-persistent-crud`
- PR: [#58](https://github.com/kendshhh/PhishLens/pull/58)
- Status: Local implementation and earlier-candidate CI/hosted mock verification recorded; final-candidate review and acceptance remain pending.

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

## Original local verification: c162740

The results in this section apply to source committed as
`c162740d5aa4e9c87a697b395822cb36135ce744`.

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

## Kendra's CI and staging evidence: 9bb231a

Kendra's supplied `pr58-completion.md` identifies candidate
`9bb231a2cc1c701f6a8ce49d35bcdb7b81f56362`. The following summarizes her
reported verification; it is not a claim that Trixia reran those operations.

- [Seeded GitHub CI run](https://github.com/kendshhh/PhishLens/actions/runs/39618862893):
  192 passed, zero skipped, with all eleven mandatory PostgreSQL cases passed.
  This includes the two seeded checks excluded from the original local run.
  Migration and seed repeat checks, Extension checks and Staging integration passed.
- Isolated Neon branch `pr-58-staging` (`br-patient-thunder-b3oxgbb7`), database
  `phishlens_dev`: migration `0002_analysis_provenance` applied and repeat upgrade
  passed. Independent reads verified unchanged legacy data, nullable provenance
  and the mode constraint. See the [CI/staging runbook](s2-t1-ci-staging-runbook.md)
  for the recorded target and migration procedure.
- [Manual Render deployment](https://dashboard.render.com/web/srv-db92irlg1s2s739404i0/deploys/dep-dbcd1n4s728c73eoovl0):
  candidate SHA matched, inference was mock, and independent Neon reads confirmed
  writes reached the isolated branch. Create/list/detail, PATCH, clearing notes
  without clearing feedback, invalid input, DELETE and subsequent 404 passed.
  Temporary records were removed and the original row count restored.
- The existing extension API-client hosted CRUD verifier passed at the same SHA
  and cleaned up its record. This is not actual installed Chrome acceptance.
- One hosted mock create took 10.547 seconds. This observation does not establish
  a runtime bound or production performance guarantee.
- Hosted staging was skipped in that draft workflow. Manual hosted evidence does
  not satisfy the required Hosted staging workflow check.

Trixia subsequently read `/version` and `/ready`: they reported this exact full
SHA, `environment: staging`, and `database: connected`. Those reads establish
identity/readiness at that observation, not permanent target identity or new CRUD
acceptance. Recheck identity and the isolated target before further writes.

During initial staging validation, the previous development database received
the additive migration before a target mismatch was detected. Kendra reports
that its test row was removed and the final isolated configuration was independently
verified. Production was not deployed or configured. Any remaining development
database follow-up requires the operator's acknowledgement.

The supplied handoff references credential-free artifacts
`pr58-ci-evidence.json`, `pr58-neon-migration.json` and `pr58-hosted-crud.json`.
Accessible artifact links and the exact source SHA used to execute the migration
remain to be supplied by Kendra. The handoff's candidate SHA alone does not
establish the migration execution SHA. Do not publish connection strings or keys.

The temporary Neon branch's recorded expiry is October 22, 2026 at 22:19:27
Asia/Shanghai (the same local time in Manila). Availability beyond that time
requires explicit confirmation or extension; do not silently switch to production.

## Windows follow-up verification: ad47196

Runtime configuration follow-up source:
`ad4719691a2e2410edf7e712b7f920cd082fd904`.

- `./.venv/bin/python -m ruff check backend scripts/start_staging.py` passed.
- `env -u RUN_DATABASE_TESTS ./.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider`
  returned 184 passed, 12 skipped on macOS.
- `DATABASE_URL='postgresql://127.0.0.1:5432/phishlens_s2_t1_test' RUN_DATABASE_TESTS=1 ./.venv/bin/python -m pytest backend/tests/test_saved_create_postgres.py -q -p no:cacheprovider`
  returned 7 passed against disposable local PostgreSQL with mock inference.
- Four regression cases verify Windows loop selection and Uvicorn factory
  resolution with/without reload. Uvicorn factory inspection and whitespace
  checks also passed.

These are macOS checks, including simulated Windows selection; they do not
establish actual Windows/PostgreSQL acceptance. Earlier `9bb231a` hosted evidence
must not be represented as verification of `ad47196` or a later candidate.

## Client compatibility review

[Leyan's scoped review](https://github.com/kendshhh/PhishLens/pull/58#pullrequestreview-5602284448)
was against `9bb231a`: 137 JavaScript tests and 51 scoped backend tests passed
with database/inference substituted. Saved fields, nullable values,
evidence/provenance, PATCH, empty DELETE and 504 status/message handling were
compatible; no client code change was needed. This is not formal approval,
real-provider verification or installed Chrome acceptance.

## Remaining before completion

- Record the final candidate SHA and current CI/deployment/package links; pass
  all required checks, including Hosted staging, for that head. Eleven mandatory
  PostgreSQL cases are registered and earlier seeded CI passed; preserve the
  passing final-head report rather than relying on earlier results.
- Obtain Wilberr's actual Windows/PostgreSQL and normal single-process startup
  verification, and re-review of the event-loop fix.
- Obtain Kendra's accessible credential-free migration/hosted artifacts, exact
  migration execution SHA, and acknowledgement of development-database follow-up.
  The isolated Neon migration and earlier mock writes are already reported above;
  do not repeat migrations simply to fill an evidence gap.
- Coordinate the final deployed SHA and isolated database target with Kendra,
  including staging availability/expiry, before acceptance writes.
- Complete permitted real-provider/target-host verification with Wilberr and
  Kendra. Local persistent create remains unavailable (503); no production
  deadline guarantee is established.
- Complete actual connected-client/installed Chrome acceptance with Leyan and
  Andrei against the identified final deployed SHA and matching package.
- Obtain client-owner acknowledgement of uncertain commit outcomes and track
  idempotency/reconciliation separately if deferred. Do not blindly retry creates.
- Reconcile shared AI changes from still-open PR #50 on the final integration
  base and rerun relevant combined tests. PR #58 does not complete Week 1 acceptance.
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
