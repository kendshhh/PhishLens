# S2-T2 PostgreSQL Test Handoff

## Scope and source state

Issue #43: prove saved-analysis CRUD persistence, validation, and failure behavior.

Branch: `test/43-crud-persistence`

Base commit: `edee25e1780d4fb28617fa04bf46d6e6624b6678`

The test results below were produced with four Issue #43 test files modified in
the working tree on top of that base commit. They are not yet represented by a
commit SHA. The WIP stash was restored, verified against its patch, and dropped.

The seeded-history test now creates its own synthetic users and records inside a
rollback-only transaction and requires a local database whose name ends in
`_test`. The seed-integrity check remains strictly gated by both
`RUN_DATABASE_TESTS=1` and `RUN_SEED_INTEGRITY_TESTS=1`; it still requires local
`phishlens_dev` and is skipped in the disposable-database suite.

## Results

- Ruff on the four changed PostgreSQL test files: passed.
- `git diff --check`: passed.
- Targeted PostgreSQL tests against the disposable local database
  `phishlens_s2_t1_test`: **33 passed, 1 skipped in 3.52s**. The skip is the
  deliberately gated seed-integrity check.
- Full backend suite with `RUN_DATABASE_TESTS=1` and the same disposable database:
  **218 passed, 1 skipped in 6.43s**. The skip is the seed-integrity check.
- Full backend suite with database-only tests disabled:
  **184 passed, 35 skipped in 3.94s**.

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
shared or hosted database to force a pass. The test changes and this handoff are
uncommitted; no Issue #43 commit SHA, PR CI run, or teammate review is available
yet. No Neon or hosted database was used, and this note contains no credentials.
