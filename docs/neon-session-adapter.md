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

Sources inspected November 8, 2026:

- https://neon.com/docs/reference/javascript-sdk
- https://neon.com/docs/auth/guides/plugins/jwt
- https://neon.com/docs/auth/guides/plugins/email-otp
- https://neon.com/docs/auth/guides/configure-domains
- https://developer.chrome.com/docs/extensions/develop/concepts/network-requests
- https://developer.chrome.com/docs/extensions/develop/concepts/storage-and-cookies

## Runtime behavior

- Signup uses signUp.email. Provider-managed signup OTP must be enabled; there
  is no automatic second OTP request. Resend explicitly calls
  emailOtp.sendVerificationOtp with type email-verification.
- Verification uses emailOtp.verifyEmail. If the provider does not establish a
  session, the UI sends the verified user to email/password sign-in.
- Sign-in uses signIn.email and confirms the provider session and expected email.
- Restoration requires a verified provider identity and future session expiry.
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
- Sign-out blocks local token access before requesting remote sign-out. Failed
  remote logout cannot restore this instance's access. A fresh popup can still
  restore a surviving cookie after failed remote logout; the UI limitation must
  not be represented as global revocation. Already-issued JWTs can survive to expiry.
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
If configuration or SDK initialization fails, the popup uses the unavailable
account adapter, keeps personal reports gated and shows a safe account message.
Local scanning still opens and accepts text; internal provider diagnostics are
not displayed. This fallback does not enable anonymous report requests.
Do not enable this by editing config alone: the production validator deliberately
restricts current host permissions; prepare/review a dedicated staging artifact
and its allowlist together after the environment pairing is confirmed.

Chrome permits credentialed cross-origin extension requests with exact host
permissions. Cookie restrictions can still interfere. Neon's trusted-domain
documentation does not explicitly guarantee chrome-extension origins. The exact
installed extension origin must be accepted by the provider and verified in
regular Chrome before calling this flow supported end to end. Do not forge an
Origin header or weaken provider checks to make it work. If direct extension
origins are rejected, review a supported web or OAuth/PKCE handoff separately.

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
npm run test:account-startup
BROWSER_CHANNEL=chrome npm run test:accounts
node scripts/test_neon_adapter_browser.mjs
python3 scripts/package_extension.py
npm run test:browser
```

Still required: provider origin/cookie acceptance, real email verification and
recovery, correct Auth/database pairing, staged migration/runtime grants, exact
candidate deployment, refresh/logout across actual clients and two-user API
denial. Use the combined acceptance checklist after staging is coordinated.

## Startup regression check — November 10, 2026

`npm run test:account-startup` runs the shipped popup entry in a local browser
with synthetic Chrome APIs. It checks disabled accounts, an invalid Auth URL,
missing host permission, an API-origin mismatch and SDK initialization failure.
Each case keeps reports gated and dispatches the original synthetic text to the
local scan boundary. Failure diagnostics are not exposed and no external
request is allowed. This check fails with the original popup entry.

All five cases passed in Edge 157.0.4341.42. The complete 273-test extension
suite, ESLint, account UI browser suite, intercepted-SDK browser suite and
manifest validation also passed locally. These are local regression results,
not installed-Chrome or live Neon acceptance. Machine-readable output is
written to `output/account-startup/results.json`.
