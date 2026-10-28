# Saved report client integration

Week 3 task: W3-D2-Leyan. This module composes the injectable API client without owning HTTP requests or popup rendering.

## Usage

```js
import { createAnalysisClient } from "./api.js";
import { saveAnalysisAndRefresh } from "./report-client.js";

const client = createAnalysisClient(baseUrl);
const result = await saveAnalysisAndRefresh(client, {
    subject: "",
    body: "Synthetic demonstration message"
});
```

Creation must succeed before refresh begins. The helper reads detail using the ID returned by the server and refreshes history. It returns:

- `saved`: the confirmed creation response.
- `detail` and `history`: successful refresh values, or null when that refresh failed.
- `refreshErrors`: entries with `operation` ("detail" or "history") and the original error.

An empty history array is a successful response; null indicates a failed refresh. A refresh failure does not discard the confirmed saved record or trigger another POST. The caller should show the saved result and a refresh warning.

A creation failure rejects with the original error. The helper does not change the submitted input, retry requests, invent a verdict, or turn errors into empty history. The UI owns retaining input and choosing when a user may retry.

## Retry and response contract

The existing API client generates and retains an idempotency key for uncertain creates. Keep that client instance for an explicit retry. If recreating the client, forward the original error's `idempotencyKey`:

```js
await saveAnalysisAndRefresh(client, input, {
    idempotencyKey: previousError.idempotencyKey
});
```

The helper forwards options unchanged to `createAnalysis`. It performs one create call per invocation and never retries automatically. This relies on the API client's and backend's idempotency implementation; it does not guarantee provider processing deadlines.

The API client continues to validate saved records. Labels, nullable confidence/feedback, evidence quotes, analysis mode and provenance pass through without conversion. Saved CRUD uses `/api/analyses`; the unsaved `POST /analyses` is separate.

## Verification and remaining work

Tested against main source `e4ea032615a6663d787a5b44714b5fc982fc6355`:

```text
node --test extension/tests/*.test.mjs
142 passed, 0 failed, 0 skipped
```

The new tests include 12 injected-client tests and three local HTTP tests using the actual API client. The local server is a synthetic in-memory substitute. It covers successful create/read/list, a failed history refresh after a confirmed save, and a lost POST response followed by an explicit retry with one stored record.

Pending: Andrei's popup/history integration, real backend/database and model behavior, controlled failure cases through that backend, and verification in the exact deployed extension/environment. These tests do not establish those results.
