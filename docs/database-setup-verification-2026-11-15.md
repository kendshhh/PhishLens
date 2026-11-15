# Database setup verification — November 15, 2026

This is local disposable-database evidence for the setup and schema documentation in
PhishLens source revision `8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f`. It does not
represent hosted staging or production verification.

## Environment

- macOS, Python 3.12.5
- PostgreSQL 17.12, initialized as a temporary local cluster and bound to loopback
  port 55432
- Alembic 1.20.1, SQLAlchemy 2.1.8, psycopg 3.3.8 from the repository's pinned
  `requirements.txt`
- Database: empty disposable `phishlens_dev`; local trust authentication only
- No `.env`, Neon credentials, staging services, or production services were used

## Procedure and results

1. Created a Python 3.12 virtual environment and installed the pinned requirements:

   ```sh
   python3.12 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   ```

   Expected: dependency installation completes. Observed: all pinned requirements
   installed successfully.

2. Applied the migrations twice to the empty disposable database:

   ```sh
   env DATABASE_URL=postgresql+psycopg://phishlens@127.0.0.1:55432/phishlens_dev \
     .venv/bin/python -m alembic -c backend/alembic.ini upgrade head
   ```

   Expected: the first run creates the schema through `0004_neon_auth_subject`; the
   second run reports no pending migration. Observed: the first run applied revisions
   `0001_initial_schema` through `0004_neon_auth_subject`; the second run completed
   without an upgrade.

3. Ran the documented synthetic seeder twice:

   ```sh
   env DATABASE_URL=postgresql+psycopg://phishlens@127.0.0.1:55432/phishlens_dev \
     .venv/bin/python scripts/seed_demo.py
   ```

   Expected: both runs report the demo user and analysis present, with no duplicate
   rows. Observed: both runs printed the expected success message. A final read-only
   query found migration head `0004_neon_auth_subject`, one user, one analysis, and
   the expected synthetic subject `Synthetic account notice`; the demo subject mapping
   was null.

4. Changed only the fixed synthetic analysis subject in this disposable database,
   reran the seeder, and queried the row again.

   Expected: the seeder restores `Synthetic account notice`. Observed: it did, and the
   database still contained one user and one analysis at migration head
   `0004_neon_auth_subject`.

## Limits

This verifies local Python/PostgreSQL setup, migration application and repeatability,
the synthetic seed's repeatability, and its fixed-subject repair behavior. The Docker
command in the setup guide was not used; a temporary Homebrew PostgreSQL 17.12 cluster
was used instead. No complete backend test suite, hosted database, startup script,
database grants, deployment, Auth flow, or browser journey was tested here.
