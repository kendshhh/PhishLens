# S2-T2 PostgreSQL Test Handoff

## Scope and source state

Issue #43: prove saved-analysis CRUD persistence, validation, and failure behavior.

Branch: `codex/issue-43-postgres-tests`

Base commit: `b3a7588811e77edc48b29b07763152f66172a331` (`origin/main`, including merged PR #58).

Test-change commit: `7ced698` (based on the current `main` commit above). The
test changes were transplanted from the earlier local `test/43-crud-persistence`
branch so this PR contains only the Issue #43 test and handoff files. The WIP
stash was restored, verified against its patch, and dropped.

The seeded-history test now creates its own synthetic users and records inside a
rollback-only transaction and requires a local database whose name ends in
`_test`. The seed-integrity check remains strictly gated by both
`RUN_DATABASE_TESTS=1` and `RUN_SEED_INTEGRITY_TESTS=1`; it still requires local
`phishlens_dev` and is skipped in the disposable-database suite.

## Results

- Ruff on the four changed PostgreSQL test files: passed.
- `git diff --check`: passed.
- Targeted PostgreSQL tests against the disposable local database
  `phishlens_s2_t1_test`: **35 passed, 1 skipped in 8.62s**. The skip is the
  deliberately gated seed-integrity check.
- Full backend suite with `RUN_DATABASE_TESTS=1` and the same disposable database:
  **252 passed, 1 skipped in 11.77s**. The skip is the seed-integrity check.
- Full backend suite with database-only tests disabled:
  **216 passed, 37 skipped in 3.84s**.

## Commands

```sh
./.venv/bin/python -m ruff check backend/tests/test_history_postgres.py backend/tests/test_seed_integrity.py backend/tests/test_saved_create_postgres.py backend/tests/test_saved_crud_postgres.py

DATABASE_URL='postgresql://127.0.0.1:5432/phishlens_s2_t1_test' RUN_DATABASE_TESTS=1 ./.venv/bin/python -m pytest backend/tests/test_history_postgres.py backend/tests/test_seed_integrity.py backend/tests/test_saved_create_postgres.py backend/tests/test_saved_crud_postgres.py -q -p no:cacheprovider

DATABASE_URL='postgresql://127.0.0.1:5432/phishlens_s2_t1_test' RUN_DATABASE_TESTS=1 ./.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider

env -u RUN_DATABASE_TESTS -u RUN_SEED_INTEGRITY_TESTS ./.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider
```

The previous full PostgreSQL run failed because two legacy tests required seeded
`phishlens_dev`. The history test is now independent of seed data; seed integrity
remains separately gated and was intentionally skipped. Do not point it at a
shared or hosted database to force a pass. These results were rerun on the
current-main-based test commit `7ced698`; PR CI and teammate review are tracked
separately. No Neon or hosted database was used, and this note contains no
credentials.
