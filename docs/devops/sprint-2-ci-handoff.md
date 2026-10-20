# Sprint 2 CI guard handoff

Related: #38. Baseline: main `c350131f51340bd01ba9f8719a40c44fb8838d4a`.

The backend job already applies migrations, seeds twice, and runs the whole API
suite with disposable PostgreSQL. The gap addressed here is evidence/enforcement:
pytest can report success when a required database test is skipped or removed.
The new runner checks explicit disposable configuration before migration, requires
the actual known database tests to pass, and uploads JUnit plus a revision-labeled
summary. It preserves the full existing suite and required job names.

`commit` identifies GitHub's tested revision (the generated merge revision on a
pull request); `source_commit` identifies the PR head or main push. Retain both
when connecting source to CI evidence.

## Commands

From the repository root, after installing the locked development requirements:

```sh
python -m unittest scripts.tests.test_ci_backend -v
python -m ruff check scripts/ci_backend.py scripts/tests/test_ci_backend.py
```

The normal CI workflow supplies the disposable PostgreSQL service configuration,
migration and seed. Do not point this runner at Neon or production. Regression
tests use synthetic XML and mocked process calls; they prove gate behavior, not
new database/API functionality. GitHub CI supplies the actual database execution.

## Recorded initial gate and intentional failure

- [Initial passing CI 39420500056](https://github.com/kendshhh/PhishLens/actions/runs/39420500056):
  Backend checks ran 72 tests, zero skipped; both required PostgreSQL tests passed.
  `Backend-Test-Evidence` artifact ID 12262598646 was uploaded.
- [Intentional failing CI 39420764116](https://github.com/kendshhh/PhishLens/actions/runs/39420764116):
  draft head `b8dfaaea11fb034a90ec0e9fb4ca2aa07f14916f` requires an intentionally
  nonexistent PostgreSQL test. Backend checks fails the evidence gate; dependent
  integration and Hosted staging are skipped. No broken revision reaches main.
- Repair removes that temporary requirement. Latest-head CI remains the authority
  for the repaired change; no merge or final CRUD acceptance is inferred.

## Backend-owner handoff

After reviewed #42/#43 provide persistent CRUD tests, register exact PostgreSQL
test IDs for create/read/update/delete, ownership and failure/rollback. Tests must
use real PostgreSQL and fail on absent API/schema. A client HTTP stub or mock AI
classification alone cannot establish saved-analysis CRUD. Keep #38 open until
that integration, required CI/review and meaningful failed/repaired run evidence
are recorded. Production delivery and installed-browser CRUD remain #39/#47.
