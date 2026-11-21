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
FastAPI; the client never connects to Postgres. Authentication calls use the
API's HTTPS `/api/auth` proxy. It accepts only the release extension's pinned
Chrome origin, forwards to the configured Neon Auth URL with the API's trusted
HTTPS origin, and relays the session cookie back with `Path=/api/auth`,
`Secure`, and `SameSite=None`. The matching API HTTPS origin must be in Neon
Auth's trusted domains. Hosted staging checks that Render's
`NEON_AUTH_BASE_URL` exactly matches the isolated Auth URL used to package the
extension before it deploys.

## Backend rollout and ownership

REPORT_AUTH_MODE=demo preserves the current shared demo API during rollout
(also the local-development compatibility default). It is NOT personal storage
or a production authentication guarantee. On Render, set REPORT_AUTH_MODE
explicitly; if it is missing, saved-report routes fail closed with HTTP 503
instead of silently falling back to demo mode. The value must be set in the
Render service environment; a bundled `.env` file does not satisfy this
requirement. REPORT_AUTH_MODE=neon requires authentication for all five
/api/analyses operations: POST, list GET, detail
GET, PATCH and DELETE.
An unknown mode fails closed. Do not expose demo mode as a parallel fallback
on a personal-report deployment. Existing health/model endpoints stay public.

Configure NEON_AUTH_BASE_URL to the exact auth-enabled test branch's HTTPS Auth
URL. JWKS is loaded from that URL plus /.well-known/jwks.json; issuer and audience
must match its origin (not its full path). The server accepts EdDSA only, requires
subject, expiry, issued-at, issuer and audience, and requires
`emailVerified=true` and `banned=false`; missing or malformed account-status
claims fail closed. Tokens are not taken from request bodies or URLs. Missing,
invalid and expired tokens return 401; unverified/banned users return 403; key
service/configuration outages return 503. Neon documents these account-status
fields in its signed JWT payload and a fixed 15-minute access-token lifetime
(see [Neon's JWT guide](https://neon.com/docs/auth/guides/plugins/jwt)). The
backend therefore verifies the status snapshot carried by the token; it does
not perform a live account-status lookup. A status change after issuance may
not be reflected until that token expires. This is an inference from the
signed-token model and documented expiry, not a guarantee about Neon revocation
timing. The checked JWT guide documents JWKS signature verification, but not a
general introspection endpoint for these bearer JWTs. A direct lookup in the
Auth database would require a separate, narrowly scoped connection and a
stable supported query contract; neither is part of this draft. The initial
rollout accepts this bounded, up-to-15-minute account-status freshness window.
If immediate account disablement becomes a requirement, JWT-only verification
is insufficient and rollout must wait for a separately reviewed revocation or
live-status design. JWT logout/revocation is not immediate: an already-issued
token can remain valid until expiry. UI logout must clear the session and
account state; this draft does not implement server revocation.

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

Use the [backend acceptance and cleanup procedure](auth-backend-acceptance-runbook.md)
to prepare the private run record, bounded API steps and read-only cleanup preview.
The procedure is preparation only and requires separate live-write authorization.

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
