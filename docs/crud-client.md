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

This follows the Week 2 playbook defaults, pending confirmation against Trixia's implementation. It is separate from the unsaved AI analysis endpoint.

| Method | Path | Success |
| --- | --- | --- |
| GET | /api/analyses | 200, returns items array to the caller |
| GET | /api/analyses/{id} | 200, returns detail |
| POST | /api/analyses | 201, returns detail |
| PATCH | /api/analyses/{id} | 200, returns detail |
| DELETE | /api/analyses/{id} | 204, no JSON parsing |

Records use the saved-history fields, UUID IDs, UTC timestamps, nullable phishing/legitimate prediction, confidence 0–1, and saved risk levels. Detail also includes body, notes, feedback, and analysis_mode. Legacy unknown/null mode is accepted without treating it as real inference.

Create input: subject and body. Proposed server limits: trimmed subject 1–250 characters; nonblank body up to 20,000. Patch input: notes up to 2,000 characters or null, feedback none/false_positive/false_negative. Omitted fields stay unchanged. The backend owns input validation, rejects unknown fields and empty patches, and chooses the demo owner. Never send credentials or ownership IDs from the extension.

Failures reject with Error. HTTP failures include error.status and use readable detail when available. Non-JSON error bodies and FastAPI detail arrays retain an HTTP status message. Network, timeout, malformed JSON, and invalid records reject instead of returning an empty list. Requests have a 10-second timeout.

## Local verification

```powershell
node --test extension/tests/*.test.mjs
npm.cmd run lint
```

The CRUD unit tests use injected fetch responses. crud-http.test.mjs runs the standalone acceptance function against an in-memory local HTTP server. These checks do not prove PostgreSQL persistence or deployed integration.

## Real HTTP acceptance

Only run after Trixia confirms that the URL points to a disposable or synthetic demo database. This command creates, reads, lists, patches, rereads, clears notes, deletes, and confirms 404 for one uniquely named synthetic record. Cleanup targets only that created record.

```powershell
node scripts/verify_crud.mjs --base-url https://CONFIRMED-TEST-HOST --environment demo --allow-writes
```

Replace the placeholder with the confirmed test URL. Both environment and write opt-in flags are required. Do not use the production backend. Record the source SHA, confirmed environment, command, and actual output when run. No real backend or database acceptance has been performed for this work yet.

## Remaining integration

Trixia reviews endpoint envelopes, field defaults, error format, and server limits. Once the backend is available, run the HTTP acceptance command there. Then coordinate one check with Andrei using the real client in his UI. Backend routes, models, migrations, main.py, UI files, and CI are outside this change.
