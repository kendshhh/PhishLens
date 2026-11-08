# Account UI preview

This branch starts from PR #156 at f2b5edbf57b8d009edc68168a8cbba058b21cf2e.
It adds account screens for local review. It does not connect Neon Auth, change the
database, implement backend authorization, or replace PR #157.

Right-click analysis remains the first flow. Local checking and its draft do not
require an account. The extension entry point gates personal saved-report actions
behind a session boundary. Until a live adapter is agreed and connected, account
actions show an unavailable message and do not send credentials or report requests.
Existing shared-demo endpoints are unchanged; hiding them in the UI does not secure
the backend. Do not use this branch for real personal reports yet.

## Review locally

From the repository root, run `python scripts/preview_accounts.py`, then open
http://127.0.0.1:8766/account-preview. Use fictional data only.

- Sign in as `ada@example.test` or `bea@example.test`, password `Demo-only-123!`.
- Create a new `@example.test` account with a name and a password of at least eight
  characters. The mock verification and recovery code is `123456`.
- Try an invalid verification code, resend, then verify. Password/code fields are
  cleared after requests; errors keep the current form available for retry.
- If you close verification before finishing, reopen Account and choose Verify email.
  Verification and recovery also provide Back to sign in; signing in with an
  unverified demo account cannot grant report access.
- Account headings scroll below the sticky navigation when changing screens.
  Browser checks assert the heading is unobscured at 380px and 320px popup widths.
- Closing or leaving a form clears password/OTP fields. Resend checks that the email
  field is present and valid before invoking the adapter; email addresses remain
  available when resuming verification.
- Open Saved reports, sign out, and sign in as the other demo account. The old
  report list, details, notes, search, save marker and confirmation are cleared.
- Reload the preview to restore its synthetic session. Demo sessions expire after
  ten minutes. New demo accounts, password changes and report edits are in-memory
  fixtures; they are not persistent backend data.

The preview uses a separate mock adapter and in-memory report clients. It sends no
email, creates no Neon account, stores no password/token in browser storage, and
does not call the shared API. Only a synthetic user/expiry and existing local scan
state are retained in the preview's browser session. The preview runtime stub does
not execute the real local model; packaged scanner regression tests remain separate.

## Adapter handoff

`initializeAccountPopup` accepts an adapter and a `createClient(session)` factory.
The default adapter is unavailable. Mock code lives under `preview/`, is excluded
from the extension archive, and is never imported by the product entry point.

The adapter exposes `restore`, `signUp`, `verifyEmail`, `resend`, `signIn`, `signOut`,
`recover` and `resetPassword`. Sign-in, verification and restoration return either
null or `{user: {id, name, email, emailVerified: true}, expiresAt}` with an epoch
millisecond expiry. The live adapter must derive this from the supported SDK's
verified session, not from form values. It owns refresh, revocation, safe error
messages and storage decisions. A future account-state subscription must propagate
provider logout/account changes between open clients.

The backend must still verify the Bearer JWT and derive record ownership itself.
No owner ID is added to saved-analysis payloads. Once the SDK/version, database
pairing and intended client branch are confirmed, connect the existing API client's
token supplier to that adapter and test real verification, expiry and cross-user
denial with PR #157. Six-digit verification/recovery codes are mock UX decisions,
not a claim about Neon's supported recovery transport. Adjust the screen handoff to
the confirmed SDK; do not invent an endpoint or put Neon credentials in the client.

Report operations capture the active account generation. A late response from a
previous account is rejected and cannot repopulate its reports. Sign-out clears
local access before requesting remote sign-out; a failure leaves a clear limitation.
A previously submitted write may still finish on the server. There is no automatic
POST retry; check the same account's reports before explicitly saving again after
an interrupted session. This branch does not claim cross-session exactly-once saves.

## Verification — November 8, 2026

- `node --test extension/tests/*.test.mjs`: 265 passed, no failures/skips. Includes
  ten account/session tests for signed-out CRUD denial, restoration, expiry, 401 vs
  403, sign-out failure, account switching and stale read/write rejection.
- `npm run lint`: passed using the installed ESLint over `extension/`.
- `npm run test:accounts`: passed in Edge 157.0.4341.42 with a disposable profile.
  Covers guest gate, sign-up, OTP error/resend/retry, safe name rendering, restoration,
  sign-out cleanup, account switch, recovery, changed-password sign-in and expired-session UI. No page
  errors or external requests. Set `PYTHON` if needed and `BROWSER_CHANNEL=msedge`
  when bundled Playwright Chromium is unavailable.
- `python scripts/package_extension.py`: passed validation and archive checks.
  The three account modules are included in production/staging package inventories;
  preview fixtures are excluded. Package identity is a local uncommitted snapshot,
  not an accepted source SHA or deployed artifact.
- `node scripts/browser_acceptance.mjs`: all nine existing packaged local/synthetic
  scanner and CRUD checks passed in Edge 157.0.4341.42. The disposable test copy
  explicitly injects a verified mock session against its loopback API; this is not
  real sign-in or cross-user backend evidence. The real model returned uncertainty,
  which is not a completed local-LLM verdict.
- 65 Python packaging/secretary tests passed, including staging account assets.
- Ruff passed for changed Python files after import ordering fixes.

Screenshots/results are generated under ignored `output/account-ui/` and
`output/extension/`. CI, teammate design review, live SDK integration, real email
delivery/recovery, deployed authorization and final candidate acceptance are pending.
Nothing has been merged into main or changed in a shared environment by this work.
