# Saved-analysis API reference

Supports API documentation and client resilience tasks #140 and #135.
Source rechecked against main: `ea00e2411d065d78e9a2efae47dcb555b67a21b5` (November 24, 2026). The review covered the saved-create router, saved-analysis deadline and worker, Auth owner resolution, and the extension API client.
This is a source contract reference, not a live release sign-off.

## Client setup

```js
import { createAnalysisClient } from './api.js';

const client = createAnalysisClient(baseUrl);
const saved = await client.createAnalysis({
    subject: '',
    body: 'Synthetic account notice. Verify with the sender.'
});
const detail = await client.getAnalysis(saved.id);
const history = await client.listAnalyses();
await client.updateAnalysis(saved.id, { notes: 'Reviewed synthetic example', feedback: null });
await client.deleteAnalysis(saved.id);
```

Andrei injects this five-method object into the UI. Inject fetch as the second factory argument for tests;
the third argument accepts createTimeoutMs (default 25000), requiredModel and getAccessToken.
Reads/PATCH/DELETE use 10000 milliseconds. requiredModel sends X-PhishLens-Model on create;
getAccessToken is called for each CRUD request when a caller supplies it; the client then sends that token as Bearer. This hook does not establish that Auth is enabled in a hosted service or packaged extension. See [session contract](client-sessions.md).
The standalone `getAnalyses(baseUrl, { fetchImpl, timeoutMs = 10000, retries = 2, retryDelayMs = 250 } = {})` helper returns the history array and sends `Cache-Control: no-cache`. It uses a timeout per attempt and retries network errors, timeouts, and HTTP 408, 425, 429, and 5xx responses. The delay grows linearly with the attempt number. On failure it throws a structured error with fields such as `code`, `category`, `origin`, and `status`. This helper is separate from the authenticated client's `listAnalyses()`.

## Saved-create availability guard

Before persistent creation, the backend checks `AI_ANALYSIS_ENABLED`. If analysis is disabled, it returns `503 analysis_unavailable` without creating a report. When `X-PhishLens-Model` or `local_review` is supplied, the backend requires the configured provider to be TF-IDF, the requested model hash (when supplied) to match, and the model artifact to load; otherwise it returns `503 analysis_unavailable`. This is a runtime availability guard, not evidence of model quality or hosted acceptance.

## Saved CRUD

| Client method | HTTP route | Success body |
|---|---|---|
| listAnalyses() | GET /api/analyses | 200, JSON {items: [...]} on the wire; client returns the array |
| getAnalysis(id) | GET /api/analyses/{id} | 200, detail object |
| createAnalysis(input, options) | POST /api/analyses | 201, detail object |
| updateAnalysis(id, patch) | PATCH /api/analyses/{id} | 200, detail object; does not rerun inference |
| deleteAnalysis(id) | DELETE /api/analyses/{id} | 204, no body; client does not parse JSON |

IDs are UUID strings. History returns at most 100 records for the server-selected owner, ordered newest first with ID tie-breaker. In demo mode that owner is the shared synthetic demo user; in Neon mode it is the verified token's mapped application user.
A failed or malformed response rejects; it is never converted to successful empty history.
All client requests reject redirects, including 307/308 POST redirects; use the final configured API origin.

## Input

| Field | Contract |
|---|---|
| create.body | Required nonblank string, at most 30000 characters |
| create.subject | Optional string, at most 320; omitted becomes empty string on the server |
| patch.notes | String at most 2000 characters, or null to clear |
| patch.feedback | none / false_positive / false_negative, or null |
| omitted patch field | Leave unchanged |

An empty patch or unknown request fields is invalid. Do not send user IDs, owner, prediction,
confidence, evidence or provenance. Do not save a UI '(No subject)' placeholder as the actual subject.
The browser does not choose ownership or a verdict.

The optional local_review field carries a validated local review report, not ownership or an
authoritative server verdict. Its nested schema is defined in backend/app/analysis_schemas.py.
See the [saved-create availability guard](#saved-create-availability-guard) for the TF-IDF model checks. Keep the model header when handling an availability error.

## Response fields

The replayable synthetic requests, list/detail responses and errors are in
[examples/saved-api.json](examples/saved-api.json). The API reference tests pass these fixtures
through the actual client; they do not establish a live database or model result.

| Field | Summary and detail |
|---|---|
| id / subject | UUID / string (possibly empty) |
| prediction | legitimate, spam, phishing; null is permitted for legacy records |
| confidence | Finite score from 0 to 1, or null; do not invent a score |
| risk_level | low, medium, high, critical or null for existing records |
| threat_indicators | Array of {type, detail}, optionally a string quote |
| explanation | String or null |
| created_at | UTC ISO 8601; Z and +00:00 represent UTC |

Detail adds body, notes, feedback, analysis_mode and analysis_provenance.
Mode is mock or real for new server results; unknown/null is accepted for legacy detail reads.
Provenance is an object or null; omitted provenance remains readable by the client for legacy data.
The backend currently records provider_mode, model, model_revision, prompt_version,
explanation_source, input_truncated and windows_processed. The client preserves those supplied values.
List summaries do not include the detail-only mode/provenance fields.
Summary and detail may include review_status: released, uncertain or null. Preserve uncertainty;
an uncertain report must not be presented as a confirmed safe verdict.

New server results map legitimate -> low, spam -> medium and phishing -> high.
Generic reads retain legacy nullable fields. Final acceptance of a new saved result additionally
requires a concrete label and appropriate mode/provenance; legacy compatibility does not prove new inference.

## Error responses

Saved create errors use {detail: "readable message", code: "machine_code"}:

| Status | Saved-create code(s) |
|---|---|
| 409 | idempotency_conflict |
| 422 | invalid_input |
| 500 | internal_error |
| 502 | analysis_failed |
| 503 | analysis_unavailable or storage_unavailable |
| 504 | analysis_timeout |

History/detail/PATCH/DELETE use readable detail; missing record is 404 and unavailable storage is 503.
FastAPI validation errors for these routes may return a detail array (422).
The client exposes error.status for HTTP failures and a nonblank detail when present.
Empty/whitespace detail, non-JSON bodies and detail arrays fall back to 'Request failed (HTTP N)'.
The client does not expose saved-route machine codes separately. Its own session errors do expose
authentication_required or session_unavailable; see the session contract for their handling.
Network, timeout, redirect, malformed JSON and invalid fields reject; do not display a successful verdict.

## Timeouts and retry safety

At the reviewed backend source, saved creation has one 20-second operation budget and a 15-second
inference budget; the route accepts configured mock, Gemini or TF-IDF mode. This is not proof that every
provider/cold start succeeds within that budget. Local provider suitability remains backend/AI-owned.

A client timeout does not mean the server failed to commit. Saved creation does not retry automatically.
An uncertain create retains its Idempotency-Key; explicitly retry the identical input with that key.
Retain the same client instance, or keep error.idempotencyKey and pass it to a recreated client:

```js
await client.createAnalysis(originalInput, { idempotencyKey: originalError.idempotencyKey });
```

Do not generate a fresh key for an uncertain retry, or reuse the old key with different content.
Successful creation clears the client's pending key for a later intentional create.
Reads never create records. A failed refresh after a confirmed save should show the saved record
plus the refresh error; it must not trigger another inference/POST.

## Analyze versus save

POST /analyses is the separate unsaved analysis route: selected text maps to text, not body.
POST /api/analyses is persistent: selected text maps to body; omit subject if unavailable.
The persistent route runs inference and saves once. Do not call unsaved inference then persistent
create assuming that avoids a second inference. Separate 'Analyze' / 'Analyze and save' UI choices
remain subject to the agreed UI contract. This reference does not implement or approve that UI.

## Synthetic identity and authentication

The backend selects report ownership; the client never sends an owner ID.

- With `REPORT_AUTH_MODE=demo` (the compatibility default), all CRUD uses the shared synthetic
  `demo@phishlens.test` user. This is not personal storage or authenticated isolation.
- With `REPORT_AUTH_MODE=neon`, all five saved CRUD operations require
  `Authorization: Bearer <JWT>`. The backend validates an EdDSA token's signature, issuer,
  audience, expiry, issued-at time, subject and email; `emailVerified` must be `true` and
  `banned` must be `false`. It maps the verified subject to an internal user ID and scopes
  list/detail/create/update/delete and idempotency lookup to that owner. Legacy demo records
  are not linked by email.
- Missing, malformed, invalid or expired Bearer tokens return 401; missing, malformed or
  negative verified/active account claims return 403; invalid Auth configuration or JWKS
  availability failures return 503. An unknown auth mode also fails closed with 503.
- Another user's report is returned as 404. Idempotency keys are scoped per owner: replaying
  the same key and payload returns the original save; reusing that owner's key with changed
  content conflicts, while a different owner may use the same key independently.
- Authentication configuration and JWKS are backend settings. The extension sends the current
  token through `getAccessToken`; it never connects to Postgres or receives database credentials.

These are implementation contracts from the cited source, not proof that any hosted service has
Auth enabled. `REPORT_AUTH_MODE=demo` remains the current compatibility default in code.
The [Neon Auth integration contract](neon-auth-integration.md) records the bounded account-status
freshness limitation: a JWT reflects claims at issuance, and backend token verification does not
provide immediate account/session revocation.


## Verification limits

For an actual FastAPI-to-JavaScript error-contract replay without an external database or provider,
activate the backend development environment and run `python -m scripts.verify_client_errors`.
Node must be on PATH, or supplied through NODE_BINARY. This starts only a disposable loopback
server, substitutes inference/persistence, and checks HTTP 409/422/500/502/503/504, safe messages,
retained input/idempotency keys, explicit retry-key reuse and absence of automatic POST retries
or detail/history refresh after failure. See [acceptance status](client-acceptance-status.md).

The local client/HTTP tests and documented examples are preparation.
On November 10 the six-status FastAPI/client replay passed against source snapshot
fa9a23fbb5d1d60c45d0fc06333c50415d04d57e, along with 81 focused client/HTTP tests
and schema validation of all four JSON examples. That run applies to the November 10 source snapshot. Inference and database faults were controlled substitutes; no
external record was written. See the acceptance status for remaining live checks.
October 31 API evidence on #103 is dated mock-mode evidence for its exact earlier SHA, not the
current release. PR #103 is merged. The November 7 evidence audit records later TF-IDF staging
CRUD and separate synthetic browser coverage. Installed Chrome against the deployed backend, refresh/redeploy
persistence, controlled real-backend failures and real-provider evidence require identified candidate runs.

See [current evidence audit](client-integration-audit.md) for exact revisions, scope and remaining work.
