# S3-T2 provider bounds and controlled failures

## Scope and source

This handoff covers Issue #96, “Bound provider inference and verify controlled
failures.” The implementation is present in the source baseline at
`b8015961b6f31bdeaea62820b313f339b587d5f1`; later commits add tests and update
the evidence below. It does not claim a new staging deployment or real-provider
run.

## Reviewed source and CI evidence before this handoff update (November 14, 2026)

Before this documentation-only update, PR #107's code head was
`9eedb67f57980995a7e37a246ab831aa4cfca672`. PR #205 merged that reconciliation
into `feat/96-bounded-inference`; it includes main at
`51357447ef77de436fa43f2bd1d092417a04d1e2`, preserves the
`0004_neon_auth_subject` migration-lineage assertion, and has no merge conflict.

Code head `9eedb67` contains the TF-IDF wrong-model-hash regression at
[`backend/tests/test_saved_create.py::test_tfidf_saved_create_rejects_wrong_model_before_storage_or_replay`](https://github.com/kendshhh/PhishLens/blob/9eedb67f57980995a7e37a246ab831aa4cfca672/backend/tests/test_saved_create.py#L223),
committed in `9b54c5adb1c9c6718ccca7bb28364bf1e4390642`. It rejects with
503 `analysis_unavailable` before database setup, idempotency lookup, or saving.
The exact-head [CI run](https://github.com/kendshhh/PhishLens/actions/runs/43581813221)
and [PR #107 checks](https://github.com/kendshhh/PhishLens/actions/runs/43581726243)
passed for code head `9eedb67`. PR #205 records Backend, Extension, Staging integration, Migration
source preflight, Workflow lint, Dependency security, Dependency graph review,
and CodeQL passing on this same SHA. Hosted staging was skipped/not requested;
no current hosted deployment or write is claimed.

This update changes only this handoff. Its resulting PR head and checks must be
refreshed after the document change is pushed. The re-review of the updated PR
head is pending. Earlier local, CI, and staging results below are historical and
remain tied to the source revisions explicitly stated in their sections.

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

The focused Gemini SDK configuration test is committed in
`8fd1fa32338bbd12208cbbfc5b28abaef0b60bc1` at
[`backend/tests/test_ai_providers.py::test_saved_create_gemini_timeout_keeps_single_sdk_attempt`](https://github.com/kendshhh/PhishLens/blob/9eedb67f57980995a7e37a246ab831aa4cfca672/backend/tests/test_ai_providers.py#L68).
Its original November 2 local run used an uncommitted working-tree snapshot
based on `b8015961b6f31bdeaea62820b313f339b587d5f1`; the test was subsequently
committed in `8fd1fa3`. That run is historical evidence for the pre-commit
snapshot only. Both the Gemini timeout test and the separate TF-IDF
wrong-model-hash regression are committed, respectively, in `8fd1fa3` and
`9b54c5a`. The S3-T2 PostgreSQL run below includes the branch's allowlisted
test-database guard.

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

## Historical review and verification snapshot (November 7, 2026)

The audited PR #107 head was
`4c6d548b3999cc37ebc121ac89747deccb716c1a`. Its final commit changed
only this handoff. At that time, the TF-IDF wrong-model-hash regression was pushed in code
commit `9b54c5adb1c9c6718ccca7bb28364bf1e4390642`, and Wilberr confirmed
the test on that revision. [CI run #42213225007](https://github.com/kendshhh/PhishLens/actions/runs/42213225007)
passed for the code commit. At that historical point, Wilberr's formal review
was `CHANGES_REQUESTED`; that status and the earlier dismissed approvals refer
to the revisions reviewed then, not the current `9eedb67` head. The current
re-review status is recorded above.

[CI run #42252109389](https://github.com/kendshhh/PhishLens/actions/runs/42252109389)
passed for source head `4c6d548b3999cc37ebc121ac89747deccb716c1a`.
Its backend job reported 281 passed and 1 skipped, including 13 required
disposable-PostgreSQL cases. Workflow lint #42252109380 and dependency review
#42252109281 also passed. Ordinary backend CI used `AI_MODE=mock`; the tests
simulate provider failures and do not make live Gemini calls.

The regression is
`backend/tests/test_saved_create.py::test_tfidf_saved_create_rejects_wrong_model_before_storage_or_replay`.
It sends a valid synthetic request with `AI_MODE=tfidf`, a valid
`Idempotency-Key`, and a deliberately different 64-character hexadecimal
`X-PhishLens-Model`. It expects HTTP 503 with:

```json
{"detail":"The matching TF-IDF save service is unavailable","code":"analysis_unavailable"}
```

The test asserts that `get_database_url`,
`find_idempotent_saved_analysis`, and `create_saved_analysis` are never
called. The mismatch guard therefore rejects before database setup,
idempotency replay lookup, inference, or persistence. Header omission remains
compatible for generic saved creation; the model comparison runs when the
header is supplied. An overlong header remains a request-validation 422 case.

This check supplements rather than replaces the existing Gemini persistent
create regression: Gemini remains an optional provider and must retain its
15,000 ms SDK timeout and one-attempt behavior for saved creation. The
unsaved route keeps its separate 30,000 ms SDK timeout.

## Earlier evidence (kept tied to its original SHA)

- The November 5 deterministic/local PostgreSQL results and the November 6
  hosted TF-IDF success-path lifecycle above belong to their explicitly stated
  earlier SHAs. They are historical evidence and are not presented as tests
  performed on the current head.
- The hosted lifecycle was the successful TF-IDF path (create/read/delete and
  cleanup). It does not establish this wrong-hash failure path, browser
  acceptance, or model-accuracy sign-off.
- Exact-head CI evidence for the focused wrong-hash regression and the broader
  deterministic suite is run #42252109389. Wilberr's discussion confirmation
  and run #42213225007 apply to code head `9b54c5a`. Keep mock/unit, CI
  disposable PostgreSQL, and deployed evidence labeled separately.

## Failure-case coverage at audited head `4c6d548`

- Unavailable configuration/provider: `test_bad_ai_configuration_never_calls_service`,
  `test_provider_initialization_failure_is_safe`, and
  `test_failed_inference_does_not_save` cover safe API/worker behavior and no
  PostgreSQL row. The wrong-model-hash regression rejects before database
  setup and idempotency replay lookup.
- Timeout and bounds: `test_busy_worker_rejects_new_request`,
  `test_timeout_terminates_worker`,
  `test_timeout_kills_worker_if_termination_is_insufficient`,
  `test_late_result_is_rejected`, and
  `test_database_lock_timeout_does_not_save` cover admission, cleanup,
  deadline, and no-row behavior. The saved-create Gemini test checks a
  15,000 ms SDK timeout and one attempt.
- Quota: `test_daily_quota_is_distinct_from_a_temporary_rate_limit` and
  `test_provider_errors_return_only_safe_status` cover provider and worker
  mapping. There is no single saved-create API plus PostgreSQL test that
  injects a quota response and asserts the response and zero rows; generic
  unavailable-error tests cover the later persistence boundary.
- Malformed/unsupported output: `test_bad_google_output_is_not_a_safe_verdict`,
  `test_invalid_provider_result_is_rejected`, and
  `test_invalid_evidence_does_not_save_and_next_request_succeeds` cover
  validation, no row, and recovery across layers. A raw malformed Gemini
  response is not carried through one saved-create/PostgreSQL test.
- Database-save failure: `test_invalid_saved_response_rolls_back_insert`,
  `test_create_recovers_after_database_constraint_failure`, and
  `test_database_lock_timeout_does_not_save` use disposable PostgreSQL to
  confirm controlled errors, no partial successful row, and recovery.

The CI hosted-staging job checked a synthetic saved-report lifecycle on its
merge candidate, but this handoff does not contain a bounded hosted failure
drill for each scenario. It also does not prove what is deployed now. Any new
staging write requires a freshly confirmed target and explicit authorization.

## Remaining Issue #96 work

The requested regression and exact-head CI are complete for the audited
revision. Formal re-review and the remaining Issue #96 acceptance evidence
are pending, including the bounded hosted failure drill and any separate
provider/model evaluation sign-off. Keep Issue #96 open until those results
are recorded against their tested revisions.
Do not treat the earlier successful staging lifecycle as proof of those
separate checks.
