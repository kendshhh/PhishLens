# Offline Auth readiness review — November 14, 2026

Reviewed PR #168 source `352438926da6b9f4c1e2c47be414bc046511cdb7` in
a separate local worktree. No runtime, deployment, database, package overlay or
Auth configuration changes were made. This record does not establish live Auth
acceptance or authorize any hosted operations.

## Backend preparation completed

Added 20 HTTP boundary cases to `backend/tests/test_report_auth.py`: malformed
and expired bearers return 401; unverified and banned credentials return 403,
across POST, list GET, detail GET, PATCH and DELETE. The cases require that subject
mapping is never invoked, use a storage dependency that cannot access a database,
and assert that the response does not disclose the supplied token or fixture email.
Missing-bearer and direct signature/issuer/audience checks remain in the existing
suite. Synthetic signing keys and in-memory SQLite are used; no Neon keys or
accounts were used.

## Session and package review

The pinned `@neon/auth` 0.8.2 Vanilla adapter injects the `set-auth-jwt` response
header into `session.token`. The extension reads that injected JWT, rejects opaque,
expired or wrong-subject tokens, and obtains a current token for each report
request. This behavior was checked against the actual bundled code and its
synthetic SDK test, rather than assuming APIs from another SDK version.

Existing account-generation guards clear prior reports and reject late responses
after sign-out/account switching. The tracked `AUTH_CONFIG` remains null. The
manifest validator and package inventory checks passed; no final Auth-enabled
Chrome package was produced or installed in this review. Leyan owns that handoff.

## Actual local results

- Focused backend Auth/model-migration tests: **48 passed**, including 20 new cases.
- Extension regression suite: **279 passed**. The SDK test intercepts all HTTP;
  some other tests use local loopback HTTP fixtures.
- Package/asset/evidence checks: **39 passed, 8 subtests passed**.
- Extension manifest validation, Ruff for the changed Python test and whitespace
  checks passed.

The reused Python environment has SQLAlchemy 2.1.8, psycopg 3.3.6 and pytest 9.1.1;
it is not a fresh install of the PR's complete dependency lock. The PostgreSQL
Auth integration suite and full backend suite were not rerun in this review.
Earlier CI/PostgreSQL evidence remains tied to its recorded source and run.

## Remaining live gates

1. Kendra/credential owner confirms rotation, active Render update, exact shared
   staging branch/database pairing, production separation, approved deployed SHA,
   migration/grants, Auth mode, issuer/audience/JWKS and named operators.
2. Leyan supplies the accepted source/ZIP SHA-256, installed Chrome ID, exact
   backend/Auth host permissions and matching trusted Chrome origin. Previously
   identified packages/origins do not establish this pairing.
3. Agree on the current window, tester pause, two-account/two-report budget,
   mapping creation, optional updates/denial attempts, cleanup and rollback.
   Deployment/startup and Auth settings need their own explicit authorization.
4. After authorization, run real signup/OTP/verification, sign-in, restoration,
   renewal when observable, logout, bearer/isolation/retry checks and scoped cleanup.
   Record pending cases rather than extrapolating from the offline tests.

No deployed rate-limit rule was verified. Existing 429 UI handling does not prove
server-side throttling; rate-limit probing remains excluded from this Auth run.
Issued JWTs may survive sign-out/session revocation until expiry; cleanup must
stop clients and account for token expiry before final mapping deletion checks.

Use the separately reviewed backend acceptance procedure for exact bounded live
requests. #48's demo-mode TF-IDF lifecycle is a different acceptance task. The
local RLS spike is separate and has not changed the Auth implementation.
