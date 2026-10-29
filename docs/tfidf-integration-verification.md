# Integration verification — 29 October 2026

This page records the initial TF-IDF-only integration at `dacd777`. The later
full teacher workflow has [separate implementation checks](ai/live-workflow-verification.md).

See the machine-readable evidence in `docs/evidence/tfidf-integration-20261029/`.
The integration is based on main `1344fcb061272bac93ced5911f1ab8fbb3b6785d`.

| Check | Recorded result |
|---|---|
| Extension JavaScript tests | 133 passed |
| Backend and repository Python tests | 349 passed; 37 skipped; 82 passing subtests |
| ESLint | Passed, including extension entry points and frozen AI modules |
| Installed extension | Loaded in isolated Chrome 156.0.8078.73 on Windows 10.0.26300 |
| Browser workflow | Local scan, checked English insights, consent, create/detail/history, notes/feedback, delete, failure, retry and Clear passed |
| Browser API access | Seven requests intercepted; none sent to the real API |
| Prepared development parity | All 52 decisions/scores matched frozen fixtures; max margin difference 2.14e-14 |
| Visible-text browser/server parity | All 52 matched; max margin difference 2.67e-15 |
| Historical archive | 108 files, 11,400,867 bytes, source SHA-256 verified |
| Model and frozen kernel hashes | Matched original v12a handoff |
| Runtime packaging | Allowlisted assets include the model and contributor report helper |

The Python check used bundled Python 3.12.14 with the existing local dependency
directory, inside the sandbox. Its first run found package inventory/origin
assumptions that were corrected, plus a pytest temporary-directory permission
problem resolved with a new workspace-local temporary directory. The final suite
passed; two existing Alembic configuration deprecation warnings remain.
The exact library versions are recorded in `verification.json`; the local
environment's FastAPI/SQLAlchemy versions differ from main's pinned requirements.
This is local verification, not a claim that hosted CI on the pinned environment
has run for this branch.

The parity check distinguishes benchmark-prepared text from original visible
input. One prepared fixture changes if cleaned again. Production prepares visible
text once; it does not apply benchmark cleaning twice. The actual selected model,
mapping and alert cutoff are unchanged. The browser additionally drops word
attribution quotes whose tokens no longer match after Unicode case expansion.

The source benchmark's Python 3.12.10 timing/accuracy record is preserved as
historical evidence, not overwritten with this verification runtime's version.

## Explicit limits

- The Chrome save/read/update/delete responses were intercepted fixtures. This
  validates UI and API contracts, **not PostgreSQL persistence**. Database tests
  were disabled and pointed at an unreachable local test URL. No existing Neon,
  development, staging or production database was contacted or modified.
- No hosted configuration was changed or deployed. The currently hosted server
  must implement matching `AI_MODE=tfidf` before the new extension permits saves.
- The current shared demo history has no new per-user authentication/isolation.
  Saving original selected text requires explicit consent and authorized content.
- No new accuracy benchmark or held-out rescoring occurred. Original missing
  OOD/adversarial, fresh authenticated bank/OTP and human explanation evidence
  remains missing. No macOS test or whole-machine performance claim is added.

The temporary Chrome profile was removed. Test data stayed in local software
fixtures; no test record was created on an external service. The original dirty
benchmark checkout under `D:\Phishlens\PhishLens` was left intact.
