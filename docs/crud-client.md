# Week 2 CRUD client

Owner: Leyan. Primary reviewer: Trixia. Backup: Kendra.

## Usage

```javascript
import { createAnalysisClient } from './api.js';

const client = createAnalysisClient(baseUrl);
const records = await client.listAnalyses();
const created = await client.createAnalysis({
    subject: 'Synthetic notice',
    body: 'Synthetic email body'
});
const detail = await client.getAnalysis(created.id);
await client.updateAnalysis(created.id, {
    notes: 'Reviewed',
    feedback: 'false_positive'
});
await client.deleteAnalysis(created.id);
```

Andrei can inject this object into his UI. Fetch can be injected as the second constructor argument for tests. The existing getAnalyses(baseUrl) export remains unchanged for Week 1 callers.

## Proposed saved CRUD interface

Input limits and saved labels are aligned with Trixia's Week 2 CRUD proposal. Other integration decisions below remain pending. It is separate from the unsaved AI analysis endpoint.

| Method | Path | Success |
| --- | --- | --- |
| GET | /api/analyses | 200, returns items array to the caller |
| GET | /api/analyses/{id} | 200, returns detail |
| POST | /api/analyses | 201, returns detail |
| PATCH | /api/analyses/{id} | 200, returns detail |
| DELETE | /api/analyses/{id} | 204, no JSON parsing |

Records use the saved-history fields, UUID IDs, UTC timestamps, nullable phishing/legitimate/spam prediction, confidence 0–1, and saved risk levels. Detail also includes body, notes, feedback, and analysis_mode. Legacy unknown/null mode is accepted without treating it as real inference.

Create input: subject and body. Aligned server limits: optional subject up to 320 characters, including an empty string; required nonblank body up to 30,000. The client forwards omitted subjects unchanged; the backend stores an empty string for omitted subjects. A UI placeholder such as (No subject) must not be saved. Patch input: notes up to 2,000 characters or null, feedback none/false_positive/false_negative. Detail responses may contain null feedback; the client preserves it. Omitted fields stay unchanged. The backend owns input validation, rejects unknown fields and empty patches, and chooses the demo owner. Never send credentials or ownership IDs from the extension.

Failures reject with Error. HTTP failures include error.status and use readable detail when available. Non-JSON error bodies and FastAPI detail arrays retain an HTTP status message. Network, timeout, malformed JSON, and invalid records reject instead of returning an empty list. Reads, patch, and delete retain a 10-second timeout. Create uses a configurable 25-second client cancellation deadline. The saved-create backend uses one monotonic 20-second operation budget, including inference, validation, and persistence, with a 15-second inference budget. These are enforced application deadlines, not a guarantee that a client timeout means no commit occurred: the commit may have succeeded while its acknowledgement was lost.

Every `createAnalysis` call sends an `Idempotency-Key`. The client generates one for a new create and keeps it for retries with the same subject/body on that client instance. A successful response clears the pending key so a later intentional create gets a fresh key. If the client must be recreated after a failed/uncertain request, save `error.idempotencyKey` and pass it back as `createAnalysis(input, { idempotencyKey })`; reuse it only with the identical input. The backend returns the original record for a matching retry and `409 idempotency_conflict` if the same key is used with different content. Do not retry a create using a new key when the result is uncertain.

## Local verification

```powershell
node --test extension/tests/*.test.mjs
npm.cmd run lint
```

The CRUD unit tests use injected fetch responses. crud-http.test.mjs runs the standalone acceptance function against an in-memory local HTTP server. These checks do not prove PostgreSQL persistence or deployed integration.

## Real HTTP acceptance

Only run after Trixia confirms that the URL points to a disposable or synthetic demo database. This command creates, reads, lists, patches, rereads, clears notes, deletes, and confirms 404 for one uniquely named synthetic record. Cleanup targets only that created record.

```powershell
node scripts/verify_crud.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha CONFIRMED_FULL_BACKEND_SHA --allow-writes
```

Replace the SHA placeholder with the confirmed full 40-character backend commit. The exported verifyCrud(baseUrl, { environment, expectedSha, allowWrites }) function applies the same guard as the CLI, before creating a client or writing records. It permits only the exact HTTPS staging origin above with environment staging, or loopback origins with environment demo/disposable. It verifies /version environment and commit, then /ready. All redirects, including writes and cleanup, are refused. Arbitrary hosts and the known production origin are rejected. This uses the backend’s deployment identity; it cannot independently inspect database credentials. Trixia/Kendra must still confirm staging is wired to its separate demo database. Record the source SHA, confirmed environment, command, and actual output when run. No real backend or database acceptance has been performed for this work yet.

## Remaining integration

Trixia reviews endpoint envelopes, field defaults, error format, and server limits. Once the backend is available, run the HTTP acceptance command there. Then coordinate one check with Andrei using the real client in his UI. Backend routes, models, migrations, main.py, UI files, and CI are outside this change.

## PR #35 overlap

The saved-history helpers and getAnalyses implementation preserve PR #35 commit 413e8de, with Week 2 extensions for spam predictions and optional evidence quotes. UUID, UTC timestamp, confidence, indicator and nullable-field checks remain intact. Its API and popup regression tests are retained. The new CRUD factory follows that implementation instead of replacing its checks. PR #35 is included as a second parent of the review-fix commit, with the api.js overlap resolved by preserving its complete implementation before the CRUD factory. Recheck if either PR changes before merging. No main branch changes were made.

Review-fix local verification: 89 extension tests passed; ESLint passed. Later contract-alignment verification: 109 extension tests passed; ESLint passed. Target-guard tests use local HTTP substitutes, including identity mismatch and redirects. No deployed database writes were performed.

## Evidence and provenance proposal — Issue #42

The client can read the shapes proposed by Trixia and Wilberr:
- New evidence indicators: { type: "evidence", quote: text, detail: reason }. quote must be a string when present. Existing type/detail indicators without quote remain readable.
- explanation: formatted tactics/recommendations as a string, or null for legacy records.
- analysis_mode: mock or real for new results (Gemini/local are real); unknown or null for legacy records.
- Optional analysis_provenance: an object or null; absent remains readable for legacy responses. Model, revision, prompt version, explanation source, truncation and window metadata are preserved as supplied, without fabricated defaults. Exact JSON keys remain backend-owned; the client does not rename or discard them.

These are proposed backend storage decisions, not evidence of implemented migrations or successful real inference. Trixia owns the forward migration for analysis_mode and nullable analysis_provenance JSONB and the actual evidence/explanation conversion. The browser supplies subject/body, not owner, verdict, evidence or provenance. PATCH notes/feedback must not rerun inference.

Saved labels preserve legitimate, spam and phishing (legacy null allowed). New results map to low, medium and high respectively; the client displays supplied values rather than recalculating old records. Confidence remains 0–1 or null, including absent Gemini scores represented as null in saved records.

GET /api/analyses retains the items envelope. Saved POST returns 201 detail, detail GET/PATCH return 200 and DELETE returns empty 204. POST /analyses remains unsaved and separate. The standalone acceptance runner writes only to a confirmed guarded test target.

Contract-alignment checks use fixtures and a local HTTP substitute. No new backend, database, production UI, or deployment changes are included.
