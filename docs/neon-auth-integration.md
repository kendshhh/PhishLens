# Neon Auth integration contract — November 8, 2026

Status: backend draft; not deployed or accepted for production. The older PDF
and isolated prototype are reference material, not the current implementation.

## Client and session boundary

The Chrome extension is the first client. Local email scanning remains available
without an account. Personal saved reports require an authenticated account.
The web/Vercel client is deferred. Frontend contributions use inaki3023; backend
contributions use xxTrixia. Never merge into main automatically.

Use the current supported Neon Auth client flow for email/password signup,
email-verification OTP, password sign-in, session restoration/renewal and logout.
Returning sign-in must not request OTP on every login. Password recovery and
verification resend need UI handling. The prototype's raw cookie fetches are not
proof of supported extension sessions. Confirm trusted extension origin, cookie
behavior and the installed SDK version in regular Chrome before wiring the UI.

Neon's current JWT documentation recommends obtaining the JWT through the SDK's
getSession result. The adapter must return the signed JWT, not assume an opaque
cookie/session token is a JWT. Do not persist passwords, OTPs or raw tokens in
logs, URLs or localStorage. See https://neon.com/docs/auth/guides/plugins/jwt.

The existing createAnalysisClient getAccessToken hook obtains a current token
for each CRUD operation and sends Authorization: Bearer <JWT>. Model identity
and idempotency headers stay intact. No owner ID is sent. Backend requests go to
FastAPI; the client never connects to Postgres. Authentication calls go to the
configured Neon Auth service, not to a database connection URL.

## Backend rollout and ownership

REPORT_AUTH_MODE=demo preserves the current shared demo API during rollout
(also the compatibility default). It is NOT personal storage or a production
authentication guarantee. REPORT_AUTH_MODE=neon requires authentication for all
five /api/analyses operations: POST, list GET, detail GET, PATCH and DELETE.
An unknown mode fails closed. Do not expose demo mode as a parallel fallback
on a personal-report deployment. Existing health/model endpoints stay public.

Configure NEON_AUTH_BASE_URL to the exact auth-enabled test branch's HTTPS Auth
URL. JWKS is loaded from that URL plus /.well-known/jwks.json; issuer and audience
must match its origin (not its full path). The server accepts EdDSA only, requires
subject, expiry, issued-at, issuer and audience, and checks emailVerified and
banned status. Tokens are not taken from request bodies or URLs. Missing,
invalid and expired tokens return 401; unverified/banned users return 403; key
service/configuration outages return 503. JWT logout/revocation is not immediate:
an already-issued token can remain valid until expiry. UI logout must clear the
session and account state; this draft does not implement server revocation.

Migration 0004 adds a unique nullable neon_auth_subject to application users.
The verified subject resolves to an internal UUID. First access creates the
mapping; existing email collisions require review (409), never automatic linking.
Demo rows remain unlinked. Each database deployment is bound to one Auth issuer;
do not switch it to a different Auth project while retaining mappings.

All report access filters by that UUID. Create and idempotency lookup carry the
same owner through inference/persistence; retry keys are unique per user. Another
user's report appears as 404. Request schemas reject owner IDs. Account changes
must create a fresh frontend client, invalidate pending reads, clear visible
reports/drafts containing private history, and never reuse another account's
pending save key. Do not automatically replay uncertain POSTs after login.

## Acceptance before rollout

1. Review offline signed-token and API ownership tests, plus existing regressions.
2. Apply migration using migration credentials only on the confirmed isolated
   auth-enabled test database; runtime credentials must have only needed grants.
3. Confirm a real supported SDK session and JWT refresh in regular Chrome.
4. Test signup, verification/resend, sign-in/out, restoration/expiry, all CRUD,
   two accounts, demo separation, cross-account IDs and idempotent retries.
5. Record frontend/backend SHAs, Neon branch, migration revision and cleanup.
6. Review staging results and CI, then plan production configuration/migration
   and rollback separately. RLS and pooled-connection isolation are follow-up
   defense in depth, not implemented or claimed by this patch.

No live migration, Auth signup/email, database grant change, deployment, or
production acceptance is implied by passing offline tests.
