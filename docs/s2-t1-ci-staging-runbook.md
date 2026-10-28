# Saved CRUD: CI gate and isolated staging verification

## Scope and current state

Prepared from PR #58 source `c162740d5aa4e9c87a697b395822cb36135ce744`.
This change registers eleven mandatory PostgreSQL cases: the two existing seeded/history
checks and nine saved CRUD cases, including each inference-failure parameter, ownership,
rollback, database lock timeout, and the unsaved live-analysis boundary.
Missing, skipped, failed, or errored required cases reject the CI report.
A passing report establishes disposable local PostgreSQL plus mock inference only.
Hosted migration, real-provider performance, and Chrome acceptance require separate evidence.

## Reproduce seeded CI on a disposable local PostgreSQL service

Use PostgreSQL on localhost:5432 with disposable database `phishlens_dev`, user
`phishlens`, password `ci-only-password`. Do not reuse an existing development database
with valuable records. The exact target is enforced by the CI environment guard.
Set these process environment variables without committing credentials:

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://phishlens:ci-only-password@localhost:5432/phishlens_dev'
$env:RUN_DATABASE_TESTS = '1'
$env:AI_MODE = 'mock'
python scripts/ci_backend.py --check-environment
# Continue only if each command succeeds.
python -m alembic -c backend/alembic.ini upgrade head
python -m alembic -c backend/alembic.ini upgrade head
python scripts/seed_demo.py
python scripts/seed_demo.py
python scripts/ci_backend.py
```

Do not exclude test_seed_integrity.py or test_history_postgres.py. Preserve
`output/backend-ci/pytest.xml` and `summary.json`; require eleven mandatory cases,
pytest exit code zero, and no gate_error. The existing GitHub backend job already
uses this sequence and preserves its artifacts. Publishing/running the changed gate
in GitHub CI remains pending until these local edits are committed and pushed.

## Isolated Neon migration plan (not executed)

1. Record Neon project, branch ID/name, endpoint hostname, database, backend origin,
   migration operator/reviewer, and candidate full commit SHA. Confirm the branch
   and endpoint are isolated from production. A database named phishlens_dev alone
   does not establish isolation. Keep connection URLs and keys out of evidence.
2. Preserve the staging branch recovery point and capture current Alembic revision,
   analyzed_emails row count, and one existing synthetic row before upgrading.
   For legacy upgrade coverage use a branch at 0001 with synthetic data; an empty
   database alone cannot demonstrate preservation of existing records.
3. Review backend/migrations/versions/0002_analysis_provenance.py: additive nullable
   analysis_mode VARCHAR(20), nullable JSONB analysis_provenance, and mode check
   allowing NULL/mock/real/unknown. No backfill. The downgrade drops both columns
   and loses their data; use the recovery point if rollback is required.
4. Using the confirmed staging connection supplied through a secure environment,
   run `python -m alembic -c backend/alembic.ini current`, then `upgrade head` twice
   and `current` again. Require 0003_saved_analysis_idempotency (with historical
   0001 and 0002 revisions present), unchanged legacy records,
   NULL provenance on legacy rows, both columns, and the named mode constraint.
   Record duration and failures. Do not run the local CI runner/tests on Neon.
5. Deploy the reviewed candidate SHA using the approved staging process. Configure
   APP_ENV=staging and STAGING_DATABASE_HOST to the confirmed endpoint; verify
   /version reports the full expected SHA/environment and /ready is connected.
   Start with mock inference. Provision the synthetic demo user on this isolated
   target only; inspect seed_demo.py before use because its name guard alone does
   not verify a Neon branch. Real authentication is outside this shared demo scope.
6. On the approved staging origin, use the existing client verifier:

   ```text
   node scripts/verify_crud.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha FULL_DEPLOYED_SHA --allow-writes
   ```

   It validates target identity/readiness and creates, reads, lists, patches, clears
   notes, deletes, and verifies 404 for its synthetic record. It cleans up only that
   record. The verifier intentionally restricts origins; do not bypass this guard.
   Separately confirm acknowledged writes and deletion through independent DB reads.
   Ownership/failure injection is established in disposable CI, not by this smoke.
   If repeating these scenarios on Neon, design staging-only fixtures and controlled
   faults first; never lock or modify unrelated demo records.
7. Separately exercise Gemini with synthetic content, safe error mapping and measured
   deadlines. Local persistent inference is expected to return 503. Treat timeout
   during/after commit as an uncertain outcome; inspect before retrying because
   idempotency is absent. Never claim measured timing as a production guarantee.
8. Load the exact staging extension in Chrome, confirm it points to the expected
   origin, and exercise the saved history flow and safe error displays. Record
   package SHA, deployed SHA, migration revision, time, results, and residual limits.

## Verified migration evidence (2026-10-21)

The user created pr-58-staging in Neon project patient-bird-25428852.
Branch ID: br-patient-thunder-b3oxgbb7; parent: production.
Direct endpoint: ep-round-dew-b31w3ye7.c-4.ap-southeast-1.aws.neon.tech.
Database: phishlens_dev; existing owner role: phishlens_dev_app.
Branch expires 2026-10-22 22:19:27 Asia/Shanghai; it is temporary verification infrastructure.

Connected directly as the existing owner after confirming branch endpoint and database.
Applied the reviewed Alembic migration from 0001_initial_schema to
0002_analysis_provenance; a second upgrade head completed successfully.
Independent reads verified one legacy row retained unchanged, both new fields
nullable and NULL for the legacy row, and the mode constraint present. No
production migration, grants, ownership changes or password resets were performed.
Earlier SQL-editor attempts as neondb_owner were rolled back due to ownership errors.
The existing role password was subsequently retrieved through Neon and saved only
in the isolated checkout's Git-ignored .env; credentials are excluded from evidence.
Local credential-free evidence: output/pr58-neon-migration.json.

## CI and acceptance evidence

Ruff passed locally. The non-database run completed with 186 passed, 12 database
cases skipped, and 58 subtests passed. All eleven required IDs match actual JUnit
collection; the gate correctly rejected that real report because DB cases skipped.
Local artifact: output/crud-ci-local.xml.

For each published candidate require the GitHub Backend checks job, the full seeded
suite without exclusions, and a summary reporting all eleven required cases passed.
Store the workflow/run URL and exact candidate SHA in the handoff evidence. Passing
mock/disposable CI alone does not establish hosted or real-provider acceptance.
Use the isolated Neon target above for hosted acceptance and record the backend's
exact deployed SHA before and after synthetic CRUD. Follow the staged plan above;
record real-provider/deadline and frontend/Chrome results separately.
