# Migration compatibility and recovery verification — November 15, 2026

## Scope and source

This local evidence was collected from PhishLens source
`8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f` on macOS. It uses only throwaway
PostgreSQL databases and synthetic records. It does not verify a hosted environment,
staging or production recovery, or a deployment rollback.

Environment: Python 3.12.5, PostgreSQL 17.12, Alembic 1.20.1, SQLAlchemy 2.1.8,
psycopg 3.3.8, pytest 9.2.0. PostgreSQL 17 ran in a temporary local cluster on
port 55433 because a separate local process already occupied port 5432; that process
was left untouched. The repository's pinned development requirements were installed
in an isolated `.venv`. No `.env`, cloud credentials, or real email content was used.

## Clean and repeated migrations

On empty local `phishlens_dev` and `phishlens_s2_t1_test` databases, ran:

```sh
env DATABASE_URL=postgresql+psycopg://phishlens@127.0.0.1:55433/phishlens_dev \
  .venv/bin/python -m alembic -c backend/alembic.ini upgrade head
env DATABASE_URL=postgresql+psycopg://phishlens@127.0.0.1:55433/phishlens_dev \
  .venv/bin/python -m alembic -c backend/alembic.ini upgrade head
```

Expected: the first run applies the migration chain; the second leaves the database
unchanged. Observed: the first applied `0001_initial_schema` through
`0004_neon_auth_subject`; the repeat reported no upgrade. The same two-run sequence
on `phishlens_s2_t1_test` reached and remained at `0004_neon_auth_subject`.

The migration-source preflight passed and reported the same four-revision chain.
`python -m unittest scripts.tests.test_migration_lineage` passed both checks,
including the test that rejects a missing historically stamped `0004` file.

## Repeat seed and current CRUD/error regressions

Ran `scripts/seed_demo.py` twice on the disposable `phishlens_dev` database. Both
runs reported the fixed synthetic records present. A read-only query found one user,
one analysis, migration head `0004_neon_auth_subject`, the expected subject, and a
null Neon Auth subject for the demo identity.

On the separate migrated `phishlens_s2_t1_test` database, ran:

```sh
env DATABASE_URL=postgresql+psycopg://phishlens@localhost:55433/phishlens_s2_t1_test \
  RUN_DATABASE_TESTS=1 AI_MODE=mock \
  .venv/bin/python -m pytest backend/tests -q -p no:cacheprovider
```

Observed: **354 passed, 2 skipped**. This is local PostgreSQL integration and mock
provider evidence. The strict `scripts/ci_backend.py` wrapper was not used because it
requires port 5432; this direct pytest run used the isolated cluster on port 55433.

## Earlier backend compatibility with the newer schema

The pre-Neon-Auth backend source at
`270b7db2fb41334cd729f510a90000a0249b602a` has models and saved-report CRUD tests but
does not define `users.neon_auth_subject`. Against the disposable test database
migrated to current head `0004_neon_auth_subject`, its saved CRUD and saved-create
PostgreSQL tests passed: **11 passed**. This demonstrates compatibility for those
covered operations only; it is not a full old-version suite or a claim about deployed
runtime behavior.

The old backend snapshot was exported from that Git revision with
`git archive 270b7db2fb41334cd729f510a90000a0249b602a backend` and its two PostgreSQL
test files were run with `PYTHONPATH` set to the extracted snapshot.

The interpreter is the isolated `.venv` at the root of the current repository
checkout (`/private/tmp/phishlens-issue-134/.venv`), not inside the extracted old
snapshot (`/private/tmp/phishlens-issue134-old`). To recreate that environment from
the repository root, create it with Python 3.12 and install the pinned development
requirements:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
```

The extracted old source is placed on `PYTHONPATH`; the test runner and dependencies
come from the current checkout's `.venv`. The commands below recreate the snapshot
and rerun the 11 compatibility tests:

```sh
mkdir -p /private/tmp/phishlens-issue134-old
git archive --format=tar --output=/private/tmp/phishlens-issue134-old.tar \
  270b7db2fb41334cd729f510a90000a0249b602a backend
tar -xf /private/tmp/phishlens-issue134-old.tar \
  -C /private/tmp/phishlens-issue134-old

env PYTHONPATH=/private/tmp/phishlens-issue134-old \
  DATABASE_URL=postgresql+psycopg://phishlens@localhost:55433/phishlens_s2_t1_test \
  RUN_DATABASE_TESTS=1 AI_MODE=mock \
  /private/tmp/phishlens-issue-134/.venv/bin/python -m pytest \
  /private/tmp/phishlens-issue134-old/backend/tests/test_saved_crud_postgres.py \
  /private/tmp/phishlens-issue134-old/backend/tests/test_saved_create_postgres.py \
  -q -p no:cacheprovider
```

Observed: **11 passed**.

Data preservation across migration `0003` → `0004` was checked separately. At `0003`,
one synthetic legacy user and report were inserted. A fingerprint over the report's
ID, owner, subject, body, prediction, confidence, risk, notes, feedback, analysis
mode, and idempotency key was `4b12a7e3229a1082443db7d1b468269b`. After upgrading to
`0004`, the fingerprint was unchanged, the row count remained one, and the new Auth
subject column was null for the legacy user.

Reproduction outline (the database was disposable and had no other records):

```sh
env DATABASE_URL=postgresql+psycopg://phishlens@127.0.0.1:55433/phishlens_legacy_test \
  .venv/bin/python -m alembic -c backend/alembic.ini upgrade 0003_saved_analysis_idempotency

psql -h 127.0.0.1 -p 55433 -U phishlens -d phishlens_legacy_test -c \
  "INSERT INTO users (id, email) VALUES ('11111111-1111-4111-8111-111111111111', 'legacy@example.test');
   INSERT INTO analyzed_emails
     (id, user_id, subject, body, prediction, confidence, risk_level, indicators,
      explanation, notes, feedback, analysis_mode, analysis_provenance, idempotency_key)
   VALUES
     ('22222222-2222-4222-8222-222222222222', '11111111-1111-4111-8111-111111111111',
      'Legacy synthetic notice', 'Synthetic compatibility fixture', 'legitimate', 0.4200,
      'low', '[]'::jsonb, 'Synthetic pre-upgrade fixture', 'preserve me', 'none',
      'mock', '{\"provider_mode\":\"mock\"}'::jsonb, 'legacy-key-1');"

env DATABASE_URL=postgresql+psycopg://phishlens@127.0.0.1:55433/phishlens_legacy_test \
  .venv/bin/python -m alembic -c backend/alembic.ini upgrade head
```

The before/after report fingerprint query is:

```sql
SELECT md5(string_agg(
  id::text || '|' || user_id::text || '|' || subject || '|' || body || '|' ||
  prediction || '|' || confidence::text || '|' || risk_level || '|' || notes || '|' ||
  feedback || '|' || analysis_mode || '|' || idempotency_key,
  ',' ORDER BY id
))
FROM analyzed_emails;
```

It returned the same digest before and after the upgrade.

## Disposable backup and restore

Created a PostgreSQL custom-format backup of the synthetic-only `phishlens_dev`
database, restored it with `pg_restore --exit-on-error --no-owner` into a new empty
`phishlens_restore_test` database, and queried the restored state. Expected: migration
head and synthetic rows match the source. Observed: head `0004_neon_auth_subject`, one
user, one analysis, and the expected synthetic subject. This verifies one local dump
and restore path; it does not establish role/grant restoration, backup scheduling,
point-in-time recovery, restore-time objectives, or hosted recovery.

Commands used for the backup and restore:

```sh
pg_dump -h 127.0.0.1 -p 55433 -U phishlens --format=custom \
  --file=/private/tmp/phishlens-issue134-dev.backup phishlens_dev
createdb -h 127.0.0.1 -p 55433 -U phishlens phishlens_restore_test
pg_restore -h 127.0.0.1 -p 55433 -U phishlens --exit-on-error --no-owner \
  --dbname=phishlens_restore_test /private/tmp/phishlens-issue134-dev.backup
```

## Recovery limits

The changes after the initial schema are additive, but their downgrade functions discard data:
`0002` drops analysis mode/provenance, `0003` drops idempotency keys, and `0004` drops
the Neon Auth subject mapping. Do not use downgrades to recover data. Prefer a verified
backup restore into an isolated database or a reviewed forward repair. Application
rollback alone does not reverse a database migration. No downgrade was run here, and
no shared or hosted database was changed.
