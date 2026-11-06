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

Local PostgreSQL acceptance was **passed** for the November 2 working tree
described above. No Neon database or live AI provider was used; staging and
real-provider evidence remain pending.

### Reconciled branch verification (November 5, 2026)

After merging the latest `origin/main`, the Issue #96 worktree is at
`4bfbf4d9564f7d987fe1b6746400825471f9dbe0` on
`feat/96-bounded-inference`. The merge completed without conflicts. The auth
prototype worktree was not touched.

The following checks were run from the reconciled worktree using the project
virtual environment at `/Users/trixia/Documents/PhishLens/.venv`:

```sh
/Users/trixia/Documents/PhishLens/.venv/bin/python -m ruff check --no-cache backend/ai/gemini_provider.py backend/app/analysis_deadlines.py backend/app/analysis_execution.py backend/app/analysis_service.py backend/app/routers/saved_create.py backend/tests/test_ai_providers.py backend/tests/test_analysis_deadlines.py backend/tests/test_analysis_execution.py backend/tests/test_analysis_execution_process.py backend/tests/test_analysis_worker.py backend/tests/test_analysis_persistence.py backend/tests/test_saved_create.py backend/tests/test_saved_create_postgres.py backend/tests/test_tfidf_provider.py
env -u RUN_DATABASE_TESTS /Users/trixia/Documents/PhishLens/.venv/bin/python -m pytest backend/tests/test_ai_providers.py backend/tests/test_analysis_deadlines.py backend/tests/test_analysis_execution.py backend/tests/test_analysis_execution_process.py backend/tests/test_analysis_worker.py backend/tests/test_analysis_persistence.py backend/tests/test_saved_create.py backend/tests/test_saved_create_postgres.py backend/tests/test_tfidf_provider.py -q -p no:cacheprovider
pg_isready -h 127.0.0.1 -p 5432
```

Actual results:

```text
Ruff: All checks passed!
Pytest: 110 passed, 31 skipped in 3.61s
pg_isready: 127.0.0.1:5432 - no response (exit 2)
```

The 31 skipped cases require PostgreSQL; this run deliberately unset
`RUN_DATABASE_TESTS`. PostgreSQL was started locally, and the current-SHA
database check reported `0003_saved_analysis_idempotency (head)` for
`phishlens_s3_t2_test`. After pushing the reconciled code, PR #107 head
`724953f9ecc501c97197fdbbe7580b1adc708589` was tested again against this
disposable database. The guarded acceptance command and actual result were:

```sh
DATABASE_URL='postgresql://127.0.0.1:5432/phishlens_s3_t2_test' SAVED_CREATE_TEST_DATABASE=phishlens_s3_t2_test RUN_DATABASE_TESTS=1 /Users/trixia/Documents/PhishLens/.venv/bin/python -m pytest backend/tests/test_saved_create_postgres.py -q -p no:cacheprovider
```

```text
31 passed in 9.12s
```

The earlier 30-pass PostgreSQL run remains historical evidence for its
November 2 working tree; the 31-pass result above is for the updated PR head.
The implementation and deterministic coverage reviewed here include TF-IDF
as the primary saved path, the retained Gemini timeout/one-attempt regression,
single-process inference admission, 15/20-second budgets, controlled failures,
no-save-on invalid inference, healthy follow-up, and idempotent ambiguous-commit
replay.

### Hosted/provider verification (reported November 6, 2026)

Kendra reported the approved PR #107 head
`dca326fa3d051be106c6b4ed8012d4a733a98c00` live on staging, with `/ready`
connected and `/model-info` reporting TF-IDF, model
`word_plus_char_wb_C1p0`, SHA-256
`a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`, and
`accepts_tfidf_reports: true`. The confirmed Neon target was
`pr-58-staging` / `phishlens_dev`, revision
`0003_saved_analysis_idempotency`.

Kendra then reported the explicitly authorized synthetic TF-IDF saved-analysis
lifecycle succeeded: create 201, list/detail 200, detail provenance matched
TF-IDF and the model SHA, delete 204, follow-up detail 404, and the list
returned to its pre-run count of two. Record ID:
`6df7bd80-5f44-42d9-aa8f-b3b6f0071aaf`. This is reported hosted success-path
evidence; it does not establish failure-path behavior, model accuracy, or
browser acceptance. Evidence was recorded on Issues #90 and #96. No extension
artifact was required for this server-side check.

## Remaining acceptance evidence

- Wilberr approved PR #107 head `dca326fa3d051be106c6b4ed8012d4a733a98c00` on November 5. In a later PR comment, he requested one additional regression for a TF-IDF model-hash mismatch before storage or idempotency replay. That follow-up is implemented locally below, but is not yet included in the PR; it still needs to be pushed, checked by CI, and re-reviewed.
- Required checks passed on the current PR head: CI run #556 (`42004387427`), plus the current lint and dependency-review runs. The earlier CI run #555 is historical evidence.
- Kendra's reported hosted TF-IDF lifecycle satisfies the successful save/read/delete/cleanup path for the reported dca326 deployment. Keep it distinct from deterministic failure-path tests and provider/model evaluation sign-off.
- Wilberr's later requested wrong-model-hash regression is implemented locally below but still needs to be pushed, checked by CI, and reviewed on the new head. Obtain any additional provider/model evaluation sign-off he requires separately; the prior approval was for the earlier head.
- Keep mocked/unit, local PostgreSQL, and deployed evidence distinct. A matching extension artifact is only needed for client/browser acceptance, not this API-only lifecycle.

Issue #96 should remain open until the follow-up regression is integrated and reviewed, required CI passes on that head, and provider/model evaluation sign-off and all other acceptance evidence are reconciled.

### Follow-up regression for Wilberr (November 6, 2026)

Added locally in `backend/tests/test_saved_create.py`:
`test_tfidf_saved_create_rejects_wrong_model_before_storage_or_replay`.
With TF-IDF configured and a deliberately mismatched 64-character model hash,
the test expects HTTP 503 `analysis_unavailable` and asserts that database
configuration, idempotency lookup/replay, and saved-analysis service invocation
do not occur. Existing coverage continues to allow a missing model header for
generic saved creation.

Focused command and actual result:

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/trixia/Documents/PhishLens/.venv/bin/python -m pytest backend/tests/test_saved_create.py::test_tfidf_saved_create_rejects_wrong_model_before_storage_or_replay -q -p no:cacheprovider
```

```text
1 passed in 0.91s
```

This is local, uncommitted evidence on `feat/96-bounded-inference`; it is not
part of PR #107's remote head and does not replace required CI or Wilberr's
follow-up review. It does not change the separate pending hosted-provider
verification.
