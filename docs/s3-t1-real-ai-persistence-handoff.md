# S3-T1 Real AI Persistence Handoff

- Issue: #90, “verify real AI inference through the saved-analysis API”
- Branch: `feat/90-real-ai-persistence`
- Current base SHA: `98dd0dc13136f16c1159a9aedee870a84be066a3` (`origin/main`)
- Status: deterministic Gemini and TF-IDF saved-provider contract coverage is present locally; the TF-IDF saved-create PostgreSQL acceptance passed against the disposable local database. Staging real-provider acceptance remains pending.

## Local deterministic coverage

`backend/tests/test_saved_provider_pipeline.py` contains two complementary
contract tests:

- The Gemini test parses a synthetic provider response and validates evidence
  with `AIService`, then checks the saved API mapping and commit using a fake
  database connection. It stubs the saved inference entry point, so it is not
  evidence of a live Gemini call or PostgreSQL persistence.
- The TF-IDF test posts synthetic content through `POST /api/analyses` with the
  frozen model hash. It exercises the bundled TF-IDF model in the supervised
  worker and checks that prediction, risk, evidence quotes, explanation,
  confidence, provider/model provenance, score metadata, and commit match the
  saved response. Its database connection is fake, so it is not PostgreSQL or
  deployed acceptance evidence.

These tests complement the existing separate tests for TF-IDF model parity,
worker limits, failure mapping, persistence transactions, and PostgreSQL CRUD.
This handoff does not claim that those suites were rerun here.

From the Issue #90 worktree, with the repository virtual environment:

```sh
/Users/trixia/Documents/PhishLens/.venv/bin/python -m ruff check backend/tests/test_saved_provider_pipeline.py
/Users/trixia/Documents/PhishLens/.venv/bin/python -m pytest backend/tests/test_saved_provider_pipeline.py -q -p no:cacheprovider
```

Actual results after the TF-IDF test was added:

```text
All checks passed!
2 passed in 1.53s
```

The commands ran while the worktree was based at `98dd0dc13136f16c1159a9aedee870a84be066a3`; the added test and this handoff are uncommitted local work, so this result does not yet identify a commit containing them.

The following PostgreSQL acceptance test exercised the real TF-IDF worker and
saved-analysis API against the disposable local PostgreSQL database
`phishlens_s2_t1_test`. The test creates synthetic content, verifies a fresh
session read, then deletes the record and verifies the missing-record response.
The test fixture also enforces a localhost database host and the exact
disposable database name. No staging or production database was used.

```sh
DATABASE_URL='postgresql://127.0.0.1:5432/phishlens_s2_t1_test' \
RUN_DATABASE_TESTS=1 \
/Users/trixia/Documents/PhishLens/.venv/bin/python -m pytest \
  backend/tests/test_saved_create_postgres.py::test_local_review_saved_fresh_session_read_delete \
  -q -p no:cacheprovider
```

Actual result on branch `feat/90-real-ai-persistence`, base SHA
`98dd0dc13136f16c1159a9aedee870a84be066a3`:

```text
1 passed in 2.04s
```

This is local TF-IDF plus PostgreSQL evidence. It is not a live Gemini/provider
call, deployed staging result, or proof of the current Render database target.

## Remaining acceptance

- Confirm current staging identity and matching build evidence with Kendra.
- Wait for explicit authorization before writing any provider-backed synthetic
  saved record to staging.
- On the authorized isolated target, use the selected TF-IDF v12a saved path
  with synthetic email content; record the provider/model hash, exact backend
  SHA, API response, and subsequent saved detail/history read.
- Confirm the saved prediction, indicators, explanation, and provenance against
  the agreed contract; record cleanup and limitations.
- Obtain required review and CI, and distinguish mock, local, deterministic
  model, PostgreSQL, and deployed real-provider evidence.

Do not run the staging write until DevOps confirms the current deployment,
matching model/build identity, Neon target, and explicit authorization. Earlier
CRUD-write authorization does not by itself authorize a provider-backed test.
