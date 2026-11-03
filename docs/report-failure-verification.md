# Saved-report failure checks

Related tasks: #98 and #105. Date: November 2, 2026.

These checks run the actual API client and saveAnalysisAndRefresh helper against a disposable local
HTTP server. The server substitutes the backend, database and inference provider. No staging or
production records are changed. These results do not complete deployed-provider or Chrome acceptance.

## Run

From the repository root:

```powershell
node --test extension/tests/report-failures-http.test.mjs
node --test extension/tests/*.test.mjs
npm.cmd run lint
```

## Observed results

Tested source: PR #106 head 899b14a9b9ccd7ab61ea5ada344e0158969ea5d1 plus the new test file.

- Seven new HTTP checks passed; the full extension suite passed 169 tests with no failures or skips.
- ESLint passed for extension/js/ and the new test file using the installed ESLint executable.
- HTTP 422, 502, 503 and 504 preserve status and readable messages, reject creation, retain input
  and the request key, and issue one POST with no refresh calls or automatic retries.
- Invalid JSON after HTTP 201 rejects with the original parsing error and request key. The client
  does not treat uncertain creation as successful empty history.
- A partially transmitted POST response exceeds a 200 ms local deadline and aborts before refresh.
  The request key remains available for recovery; no second POST is sent.
- A confirmed save followed by malformed detail and HTTP 503 history preserves the saved record,
  returns both original refresh errors, and leaves history null rather than claiming an empty list.

The local endpoint's 503 storage message is a substitute; it does not prove a real database outage
or rollback. The local timeout checks client cancellation, not termination of provider processing.
Ambiguous creation must be recovered with the original request/key against the backend contract.

## Remaining connected checks

After the intended staging SHA, isolated database and matching browser package are confirmed,
coordinate backend-controlled timeout, unavailable, invalid-output and storage failures with Trixia.
Verify the resulting UI states with Andrei, record the actual request statuses and identities,
and confirm cleanup of any created synthetic records. Keep those acceptance items pending until run.
