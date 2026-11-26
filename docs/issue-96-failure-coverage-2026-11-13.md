# Issue 96: local provider failure and PostgreSQL recovery evidence

Source: `fix/issue-96-main-reconcile`, based on local reconciliation
`bc7f09ffabd3b996a7dbb6c7b816c8e2e24113ec` (PR #107 head `9bbb4d3`
and main `0ad7eb4`). The accompanying test commit adds the cases below.

Four parametrized cases in
`test_gemini_failure_has_no_row_and_same_key_can_recover` exercise saved-create
HTTP handling, the actual Gemini adapter, worker error classification, parent
result decoding, and PostgreSQL persistence. Synthetic SDK responses inject
HTTP 429 rate limiting, daily quota exhaustion, malformed JSON, and an
unsupported verdict. Quota failures return `503 analysis_unavailable`; invalid
output returns `502 analysis_failed`. Responses contain only fixed public
messages. Each failed request leaves zero rows for its isolated test user.
The next healthy request with the same idempotency key returns 201, leaves one
legitimate record, and can be read through the API. Each request makes one SDK
call, uses the 15,000 ms timeout and single-attempt configuration, and closes
the provider client.

The worker executes inline to make SDK fault injection portable across macOS
and Windows. These cases do not test process spawning or termination; existing
execution tests cover that boundary. No Gemini network request was made.

## Local verification, November 13, 2026

An isolated PostgreSQL cluster on localhost port 55496 used database
`phishlens_s3_t2_test`, migrated through `0004_neon_auth_subject`. No hosted
database or service was used. Run from the checkout root with the project
virtual environment active:

```sh
DATABASE_URL=postgresql+psycopg://127.0.0.1:55496/phishlens_s3_t2_test python -m alembic -c backend/alembic.ini upgrade head
DATABASE_URL=postgresql+psycopg://127.0.0.1:55496/phishlens_s3_t2_test SAVED_CREATE_TEST_DATABASE=phishlens_s3_t2_test RUN_DATABASE_TESTS=1 python -m pytest backend/tests/test_saved_create_postgres.py -q -p no:cacheprovider
python -m pytest backend/tests/test_ai_providers.py backend/tests/test_analysis_worker.py backend/tests/test_analysis_execution.py backend/tests/test_saved_create.py -q -p no:cacheprovider
python -m ruff check --no-cache backend/tests/test_saved_create_postgres.py
git diff --check
```

Results: migrations passed; PostgreSQL suite **35 passed**; focused provider,
worker, execution and API regressions **78 passed**; Ruff and diff check passed.
The database fixture deletes each synthetic user and its rows after each case.

This fills the previously documented quota and raw malformed-provider-output
API/PostgreSQL coverage gaps. CI for the new commit, formal reviewer acceptance,
and an authorized bounded hosted failure drill remain pending. Historical
staging success does not verify these failures on a live service. Issue #96
should remain open pending its remaining acceptance criteria.
