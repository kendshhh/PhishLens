# S3-T2 provider bounds and controlled failures

## Scope and source

This handoff covers Issue #96, “Bound provider inference and verify controlled
failures.” The implementation is present in the source baseline at
`b8015961b6f31bdeaea62820b313f339b587d5f1`; this branch records a focused
configuration regression test and current behavior notes. It does not claim a
new staging deployment or real-provider run.

## Persistent saved-create limits

For `POST /api/analyses`, the application uses one monotonic operation deadline:

- 15 seconds for inference, including worker admission and output validation.
- 20 seconds for the overall server operation, leaving the remainder for
  persistence. Database connection and SQL waits use the remaining budget.
- Gemini is configured for a 15,000 ms SDK timeout and one SDK attempt. The
  outer deadline remains necessary because SDK/HTTP transport timeouts alone do
  not bound every phase.
- A nonblocking process-local semaphore admits one inference per API process.
  This is not a deployment-global concurrency limit.
- Mock and Gemini inference run in a supervised worker process that is
  terminated/reaped on expiry. The worker cannot access the database. Local
  persistent inference returns 503 until supervised prewarming is supported.
- Only timely, validated results are persisted. A 201 is returned after commit
  acknowledgement. If commit outcome is ambiguous, clients must retry with the
  same `Idempotency-Key` to reconcile; retries without a key can duplicate.

Persistent-create failure mapping is 504 `analysis_timeout`, 503
`analysis_unavailable` (including provider/configuration unavailable), and 502
`analysis_failed` for invalid output or other inference failure. Database save
failure is controlled and does not produce a successful verdict. Ordinary
`POST /analyses` is a separate, unsaved path with its own 30-second Gemini SDK
timeout; do not report that setting as the persistent-create budget.

## Existing evidence in the source baseline

The repository already contains deterministic unit/process coverage in
`backend/tests/test_analysis_deadlines.py`, `test_analysis_execution.py`,
`test_analysis_execution_process.py`, `test_analysis_worker.py`,
`test_analysis_database.py`, `test_analysis_persistence.py`, and
`test_saved_create.py`. PostgreSQL acceptance coverage in
`test_saved_create_postgres.py` includes provider failure without a row, SQL
lock timeout, rollback and healthy follow-up, and idempotent replay after an
ambiguous commit acknowledgement. Tests use synthetic fixtures and do not call
the live provider.

This branch adds a focused SDK configuration test proving the persistent path’s
15-second timeout still has one SDK attempt. The S3-T2 PostgreSQL run below
includes the branch's allowlisted test-database guard. Verification used the
working tree based on source SHA `b8015961b6f31bdeaea62820b313f339b587d5f1`;
the changes were uncommitted during the run.

## Verification commands

Run from the repository root after activating the project virtual environment.
These commands are suitable for macOS/Linux and Windows shells when `python`
resolves to the project environment:

```sh
python -m ruff check backend/ai/gemini_provider.py backend/tests/test_ai_providers.py
python -m pytest backend/tests/test_ai_providers.py backend/tests/test_analysis_worker.py -q -p no:cacheprovider
```

PostgreSQL acceptance requires the explicitly disposable, migrated local test
database and `RUN_DATABASE_TESTS=1`; never use Neon production or a shared
development database for failure/rollback tests. This branch allows only the
named local test databases `phishlens_s2_t1_test` and `phishlens_s3_t2_test`.
To isolate this task from the older database whose migration state is not in
this branch, create a fresh local database and run:

```sh
createdb -h 127.0.0.1 -p 5432 -T template0 phishlens_s3_t2_test
DATABASE_URL='postgresql://127.0.0.1:5432/phishlens_s3_t2_test' python -m alembic -c backend/alembic.ini upgrade head
DATABASE_URL='postgresql://127.0.0.1:5432/phishlens_s3_t2_test' SAVED_CREATE_TEST_DATABASE=phishlens_s3_t2_test RUN_DATABASE_TESTS=1 python -m pytest backend/tests/test_saved_create_postgres.py -q -p no:cacheprovider
```

The corresponding tests and their database-target guards are defined in
`backend/tests/test_saved_create_postgres.py`.

### Actual local PostgreSQL run (November 2, 2026)

The preflight found the existing `phishlens_s2_t1_test` database recorded
`0004_neon_auth_subject`, which is absent from this branch. It was left
untouched. A fresh `phishlens_s3_t2_test` database was created locally from
`template0`, migrated from this branch, and used for acceptance. Alembic applied
`0001_initial_schema`, `0002_analysis_provenance`, and
`0003_saved_analysis_idempotency`.

On this Mac, the test command used the existing project virtual-environment
interpreter:

```sh
DATABASE_URL='postgresql://127.0.0.1:5432/phishlens_s3_t2_test' SAVED_CREATE_TEST_DATABASE=phishlens_s3_t2_test RUN_DATABASE_TESTS=1 /Users/trixia/Documents/PhishLens/.venv/bin/python -m pytest backend/tests/test_saved_create_postgres.py -q -p no:cacheprovider
```

Actual migration output:

```text
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001_initial_schema, Create users and analyzed_emails.
INFO  [alembic.runtime.migration] Running upgrade 0001_initial_schema -> 0002_analysis_provenance, Add analysis mode and provenance to saved analyses.
INFO  [alembic.runtime.migration] Running upgrade 0002_analysis_provenance -> 0003_saved_analysis_idempotency, Add per-demo-user idempotency keys for saved analysis creation.
```

Actual PostgreSQL acceptance command output:

```text
..............................                                           [100%]
30 passed in 8.50s
```

Final read-only migration/database identity check:

```text
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
0003_saved_analysis_idempotency (head)
   current_database
----------------------
 phishlens_s3_t2_test
(1 row)
```

Local PostgreSQL acceptance is **passed** for this working tree. No Neon
database or live AI provider was used; staging and real-provider evidence remain
pending.

## Remaining acceptance evidence

- Wilberr review/sign-off for the bounded provider behavior and failure mapping.
- Required CI on the reviewed branch.
- A bounded real-provider staging check only after DevOps confirms the current
  deployed SHA, matching extension artifact if client verification is included,
  database target, and explicit write authorization. No staging write has been
  performed or is authorized by this handoff.
- Record exact commands, result counts, source SHA, provider/model identity,
  failure shape, persistence outcome, reviewer, and any remaining limitations.

Evidence categories must stay distinct: mocked/unit and local PostgreSQL tests
are not real-provider or deployed staging evidence.
