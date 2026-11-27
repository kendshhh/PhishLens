# Neon session adapter: local integration draft

Based on account UI PR #164 at 1db7561a40a5663b66cb783a840a5dc09f62a907.
Work is on feat/neon-session-adapter; Leyan's branch is unchanged.

## SDK and supported mechanisms

Pinned auth-only package: @neon/auth 0.8.2. This is the current package name in
Neon's SDK reference; the older @neondatabase/auth package is not used. The
vanilla adapter matches our HTML/JavaScript extension and needs no React or
direct Data API/Postgres access. esbuild 0.28.2 bundles the browser SDK locally;
run `node scripts/build_neon_sdk.mjs` after an approved dependency update.
The extension never loads SDK JavaScript from a CDN. The build wrapper disables
the pinned SDK's default localStorage broadcast (which includes session data).
This uses Better Auth's exported broadcast-channel object; do not bypass this
wrapper. Cross-client detection uses cookie revalidation, not stored broadcasts.

The installed SDK uses credentialed HTTP-only-cookie sessions, gets JWTs from
the `set-auth-jwt` session response header, and exposes them as session.token.
Our adapter uses a forced session fetch before each report request so it sees
renewal and account changes rather than relying on cached identity. The
X-Force-Fetch header is consumed by SDK 0.8.2 and removed before network access;
this behavior is covered by an actual-SDK intercepted-HTTP test and must be
rechecked when updating the pinned SDK.

## HTTPS bridge for the Chrome extension

Neon's trusted-domain configuration rejected the extension's `chrome-extension://`
origin during staging preparation. The extension can use `transport: 'https-bridge'`
and `bridgeUrl: API_BASE_URL + '/auth/bridge'` with the existing `authUrl`,
`database`, and `apiOrigin` configuration. Its existing account screens and
session adapter call the same bundled Neon SDK through an HTTPS iframe served
by FastAPI. Neon receives the browser's HTTPS Origin from that iframe.

The HTTPS API origin must be a trusted Neon domain. For staging this is
`https://phishlens-staging.onrender.com`. Render provides `RENDER_EXTERNAL_URL`;
`AUTH_BRIDGE_ORIGIN` can explicitly select a custom HTTPS API origin. The bridge
requires `REPORT_AUTH_MODE=neon`, the configured Neon Auth URL, and a matching
request origin. Its CSP permits scripts from its own origin, connections to the
configured Auth host, and embedding by the fixed Chrome extension ID. Three
explicit GET routes serve the bridge document, host script, and existing SDK.

Both sides verify the message origin and source window. A random channel and
request ID bind responses to the initiating frame and operation. The frame
checks the configured Auth URL and a fixed list of SDK methods and input fields.
Passwords and codes cross this browser message boundary and then travel directly
to Neon. Render receives no credential POST. Tokens stay in memory, and the
existing persisted sign-out marker contains a boolean. Provider errors retain
their safe HTTP category and known verification codes while their messages are
discarded. Requests that time out before the frame loads are never submitted.

Chrome documents third-party cookie access in extension subframes. Session
restoration uses a new forced SDK session read when the popup reopens. Verify
this behavior against the actual managed Auth service and Chrome profile during
staging acceptance. The direct SDK transport remains available for callers that
already have a supported origin.

Sources checked November 19, 2026:

- https://neon.com/docs/auth/guides/configure-domains
- https://neon.com/docs/auth/guides/plugins/jwt
- https://developer.chrome.com/docs/extensions/develop/concepts/storage-and-cookies

Sources inspected November 8, 2026:

- https://neon.com/docs/reference/javascript-sdk
- https://neon.com/docs/auth/guides/plugins/jwt
- https://neon.com/docs/auth/guides/plugins/email-otp
- https://neon.com/docs/auth/guides/configure-domains
- https://developer.chrome.com/docs/extensions/develop/concepts/network-requests
- https://developer.chrome.com/docs/extensions/develop/concepts/storage-and-cookies

## Runtime behavior

- Signup uses signUp.email without a mandatory email-verification step. The
  selected provider branch must allow signup and sign-in without verified email.
  A returned session signs the user in; otherwise the UI offers email/password
  sign-in. The signup verification screen and resend action are removed.
- Sign-in uses signIn.email and confirms the provider session and expected email.
- Restoration requires a valid provider identity and future session expiry.
- The API token supplier rechecks the session, original account ID, JWT shape,
  subject and expiry. It does not verify JWT signatures; FastAPI does that.
  Null tokens block requests. Existing model/idempotency headers remain intact.
- Account state holds only public identity/expiry. No tokens, passwords or OTPs
  are written to Chrome storage, localStorage, logs, URLs or request payloads
  outside the Auth service. The SDK may cache its session in memory.
- While a live-adapter popup is open, focus and 60-second checks revalidate the
  provider session. A change/expiry clears report access and stale responses;
  the user signs in again for a changed account. Provider changes in other
  clients are not claimed to appear instantly; checks do not run after popup
  closure. Each new popup restores from the provider.
- Sign-out clears report access in the current popup. A boolean saved in
  extension storage blocks restoration of a surviving provider session on
  reopen until explicit sign-in confirms the expected account. If the storage
  write and provider sign-out both fail, the popup shows that sign-out is
  unconfirmed and offers a retry. A fresh popup can still restore the active
  provider session in that case. A successful provider sign-out completes the
  operation even when the storage write fails. Password reset also blocks
  restoration of the previous session. Already-issued JWTs can survive to expiry.
- Password recovery uses the documented forgetPassword.emailOtp and
  emailOtp.resetPassword methods. Live delivery and branch configuration are
  unverified; no six-digit example code is accepted as live acceptance evidence.
- SDK requests include credentials, reject redirects, have a 10-second transport
  deadline and no automatic retries. The adapter bounds calls to 12 seconds and
  sanitizes upstream errors. Missing sessions, 403 and 429 remain distinguishable.

## Activation is intentionally blocked by default

js/auth-config.js exports null. Importing the normal product entry point makes
no live Auth request. Neither the known mismatched neondb Auth URL nor a guessed
phishlens_dev URL is configured. Shared Neon/Render settings and backend auth
mode are unchanged. Production manifest permissions remain unchanged.

For an approved integration build, set enabled, authUrl, database and apiOrigin
in an environment-specific configuration. The API origin must match that build,
the provisioned Auth path must match its database, and an exact Auth host
permission must be declared. The factory rejects mismatches before initialization.
Do not enable this by editing config alone: the production validator deliberately
restricts current host permissions; prepare/review a dedicated staging artifact
and its allowlist together after the environment pairing is confirmed.

For the HTTPS bridge, use `--auth-transport https-bridge` when preparing the
staging package. Register the staging HTTPS API origin with Neon, and check the
installed Chrome origin against the bridge's frame policy. The package evidence
records its bridge URL and required Neon trusted domain. The existing direct
transport needs separate provider-origin acceptance. Hosted acceptance must
verify the selected transport, cookie behavior, and backend/package revisions.

## Verification and remaining acceptance

Run `node --test extension/tests/neon-accounts.test.mjs`, the complete extension
suite, account browser suite, lint and packaging checks. SDK HTTP tests inject
responses locally and prohibit unexpected origins; no real credentials, email,
Neon users or backend records are used. Fixtures are excluded from the package.

Local verification on November 8, 2026, with uncommitted adapter changes:

- Full extension tests: 273 passed, none skipped.
- Eight adapter/session tests include actual bundled SDK intercepted HTTP,
  renewed JWT attachment, opaque/mismatched/expired token denial, bounded safe
  errors, late sign-out restoration, renewal and stale account-response denial.
- `node scripts/test_neon_adapter_browser.mjs`: passed in regular Google Chrome
  156.0.8078.80 with intercepted synthetic Auth/API responses; no page errors,
  unexpected origins or localStorage/sessionStorage entries.
- Account UI browser suite: passed in regular Google Chrome with mocked accounts.
- Packaged extension browser suite: nine checks passed in disposable Chromium
  156.0.8078.4. This does not establish live Auth or complete local LLM accuracy.
- ESLint, extension validation and packaging: passed. Packaging-related Python
  tests: 33 passed with the SDK and license inventory included.

Reproduce after installing locked dependencies:

```sh
node scripts/build_neon_sdk.mjs
node --test extension/tests/neon-accounts.test.mjs
npm test
npm run lint
BROWSER_CHANNEL=chrome npm run test:accounts
node scripts/test_neon_adapter_browser.mjs
python3 scripts/package_extension.py
npm run test:browser
```

The bridge integration test needs a freshly migrated disposable PostgreSQL 17
database on loopback, named `phishlens_auth_test_*`, and installed Google Chrome.
Set `PHISHLENS_AUTH_TEST_DATABASE_URL` and `PHISHLENS_PYTHON`, then run
`node scripts/test_neon_bridge_browser.mjs`. It loads the actual extension,
serves the actual FastAPI bridge, checks the bundled SDK's HTTPS Origin, and
uses locally signed JWTs against the real backend, TF-IDF and PostgreSQL.
Managed Auth responses, code delivery and the signing key source are synthetic.
All browser HTTP traffic is intercepted, with backend traffic forwarded to the
disposable loopback server. Hosted delivery and Neon settings need live acceptance.

Still required: provider origin/cookie acceptance, real email verification and
recovery, correct Auth/database pairing, staged migration/runtime grants, exact
candidate deployment, refresh/logout across actual clients and two-user API
denial. Use the combined acceptance checklist after staging is coordinated.
