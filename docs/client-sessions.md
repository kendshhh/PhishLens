# Saved-analysis client sessions

Optional client preparation for the agreed Bearer JWT contract. This does not implement Neon Auth,
token verification, user isolation, sign-in UI or sign-out UI. Those require the confirmed SDK/auth
configuration and Andrei's Vercel integration branch. No existing popup wiring is changed here.

## Interface

```js
const client = createAnalysisClient(apiOrigin, fetch, {
    getAccessToken: async () => sessionAdapter.getJwt(),
    requiredModel: modelSha
});
```

sessionAdapter.getJwt is an application-supplied adapter, not a Neon SDK method. It returns the
current signed JWT as a string, or null when signed out. Implement it using the agreed supported
SDK flow; do not supply an opaque session identifier or a string prefixed with Bearer.

The getter is called for each list, detail, create, update and delete request. The client attaches
Authorization: Bearer followed by the returned token. Existing model, content-type and idempotency
headers remain intact. Redirects are rejected. Tokens are never placed in URLs or request JSON.
The client neither stores tokens nor obtains/renews them. The existing HTTP deadline starts after
the getter returns; the session adapter must bound its own asynchronous work.

Omitting getAccessToken preserves existing unauthenticated behavior for current callers. Once the
backend requires authentication, the authenticated UI must inject the getter. Legacy getAnalyses
does not use this session interface; use the authenticated client's listAnalyses instead.

## Session errors

- A missing/invalid token rejects before fetch with status 401 and code authentication_required.
- An HTTP 401 rejects with the same status/code and a safe sign-in message. The client does not
  refresh the token or replay the failed request.
- A failed token lookup rejects with code session_unavailable and a generic message. It does not
  fall back to an anonymous request or expose the SDK error/token. This is not proof of expiry.
- Other HTTP errors retain their existing handling. A 403 does not initiate token refresh or retry.

The UI owns preservation of form drafts, the sign-in prompt, and clearing history/detail/pending
results on sign-out or account change. Create a fresh client instance for the new account and
invalidate outstanding UI operations; this component does not prevent a late response from a
previous session from being rendered by a caller. Never transfer one user's retry key to another
account. A saved POST with an uncertain response must be recovered using its original key within
the same verified user scope, without blind automatic retries. The helper preserves the caller's
input and attaches the request key to creation errors.

## Verification

Baseline: main a98b48a5086d0fc83b7d2419194a646ede1daead, November 6, 2026, plus this change.

```text
node --test extension/tests/client-session.test.mjs   11 passed
node --test extension/tests/*.test.mjs                231 passed, no failures/skips
```

ESLint passed for extension/js/ and the new test file using the installed executable. Tests use
synthetic tokens, injected fetch responses and one disposable loopback HTTP server. No real token,
Neon session, backend ownership check, external write or deployed/browser acceptance is claimed.
