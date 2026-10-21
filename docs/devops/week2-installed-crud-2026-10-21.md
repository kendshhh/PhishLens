# Issue #47 — installed-browser CRUD evidence

Date prepared: 2026-10-21 (Asia/Manila)  
Branch: `test/47-verify-installed-browser-crud`  
Owner: Andrei (`JupitraxNeptuna`)  
Review: pending `inaki3023` (backup `kendshhh`, subject to repository permissions)

## Evidence status

This file is a reproducible run sheet and local preparation record. It is not an installed-Chrome result, a real CRUD result, or instructor acceptance. Do not close #47 based on the local client fixture or package build alone.

| Evidence | Status | Recorded value |
|---|---|---|
| Local source revision used for package | Local | `f8691e6c5b4e16bea99982a8c9b466b13ddb5e17` |
| Package | Local staging package, not CI artifact | `output/staging/PhishLens-Staging-Extension.zip` |
| Package SHA-256 | Local rebuild 2026-10-22 | `a5e7cb6f82fc91750fb5b3e7f95eb47ea9efc5c4b9fa001d41b7ad88b77afff9` |
| Extension version | Local package manifest | `0.1.0` |
| Package target | Staging URL only | `https://phishlens-staging.onrender.com` |
| Archive inspection | Local | 10 assets; staging name and host permission; no test files |
| Backend `/version`, `/ready` | Deployed | `/version`: staging commit `9bb231a2cc1c701f6a8ce49d35bcdb7b81f56362`; `/ready`: `ready`, database `connected` |
| Staging DB confirmation | Confirmed per user reply | Confirmation supplied in this session; confirmer identity was not specified |
| Staging synthetic CRUD | Deployed API | Guarded real-client run passed; created and cleaned up only record `95e2169c-5e03-45ce-ab4d-8c870ce432ae` |
| Installed Chrome | Pending | Chrome extension management UI is unavailable to automation in this session; no screenshot or installed-package result captured |
| Public presentation arrangement | Pending | Kendra/instructor acceptance must be recorded; a ZIP or API URL alone is not a public working app |

## Local preparation performed

Command used to build the local staging-target package:

```powershell
$env:STAGING_BASE_URL = 'https://phishlens-staging.onrender.com'
python scripts/package_staging_extension.py
```

Actual result: `Built separate staging extension ZIP.` The ZIP inspection confirmed 10 runtime assets, manifest name `PhishLens Staging`, version `0.1.0`, host permission `https://phishlens-staging.onrender.com/*`, API base URL `https://phishlens-staging.onrender.com`, and no tests in the archive. This package is locally generated from the source revision above; use the exact current PR CI artifact for final Chrome acceptance after hosted checks pass.

Read-only staging identity/readiness probes initially timed out, then succeeded. The live staging identity was `9bb231a2cc1c701f6a8ce49d35bcdb7b81f56362`; readiness reported `ready` and `connected`. After the user confirmed the separate synthetic/demo database, the guarded runner below passed. No production endpoint was used.

The successful PowerShell probe was:

```powershell
$version = Invoke-RestMethod -Uri 'https://phishlens-staging.onrender.com/version' -TimeoutSec 60
$ready = Invoke-RestMethod -Uri 'https://phishlens-staging.onrender.com/ready' -TimeoutSec 60
```

The first probe attempt timed out; a later retry returned the staging identity and database readiness shown above.

Local commands/results on this source revision:

```text
npm test                               PASS — 125 tests
npm run lint                           PASS
npm run validate                       PASS — extension manifest/assets
node --check scripts/verify_crud.mjs   PASS
git diff --check                       PASS
```

The staging package was checked with `ZipFile.testzip()` and passed integrity validation. These are **local** checks; only the `/version`, `/ready`, and guarded CRUD results above are **deployed staging API** evidence.

## Gate before real API writes

The repository runbook `docs/crud-client.md` permits the real acceptance runner only after Trixia confirms that the approved staging origin is connected to a separate disposable/synthetic demo database. Kendra may confirm the environment mapping. Record the confirmation and backend deployment SHA here before running writes. Do not substitute production.

After confirmation and successful `/version` and `/ready`, the guarded runner was run with the exact deployed backend SHA:

```powershell
node scripts/verify_crud.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha <CONFIRMED_40_CHARACTER_BACKEND_SHA> --allow-writes
```

Actual result:

```json
{
  "result": "passed",
  "baseUrl": "https://phishlens-staging.onrender.com",
  "recordId": "95e2169c-5e03-45ce-ab4d-8c870ce432ae"
}
```

This is **deployed API evidence** through the real `extension/js/api.js` client. The runner confirmed list/detail reads, notes and feedback patch, read-after-write persistence, note clearing, delete, and a post-delete 404, then cleaned up only its own unique synthetic record. It is not Chrome UI evidence or a screenshot. No production endpoint was used.

## Chrome manual run — exact CI artifact only

Prerequisites: the current PR head has passing required checks; hosted staging reports that same source SHA live; its `evidence.json` identifies the SHA and staging URL; the synthetic database confirmation above is recorded. Download `PhishLens-Staging-Extension` from that PR workflow run. Do not use the production ZIP or an older artifact.

1. Record Chrome version from `chrome://version/`, PR/source SHA, artifact workflow URL, artifact SHA-256, package manifest version, and target `/version` response.
2. Extract the artifact. Open `chrome://extensions/`, enable Developer mode, select **Load unpacked**, and choose the extracted extension folder. Confirm the extension is named **PhishLens Staging** and inspect its service worker for startup/runtime errors.
3. Open the extension popup. In DevTools Network, preserve the log and filter to `/api/analyses`. Record the initial `GET` status, envelope shape, and displayed list. Capture screenshots of the list and detail view; use only synthetic data.
4. Create one record with a unique subject such as `Issue 47 synthetic <timestamp>` and a clearly synthetic body. Record the `POST` status and returned ID. Open its detail and verify subject, body, explanation/result fields, and provenance are rendered as text. If using markup-like strings, confirm they appear literally and do not execute.
5. Edit notes and feedback. Record the `PATCH` status. Close the popup, reopen it, and read the record again. Confirm the notes and feedback persist; record the follow-up `GET` status and screenshot.
6. Open edit and cancel after changing an unsaved field; verify the saved value remains. Open delete confirmation and cancel; verify the record remains. Capture those cancellation states.
7. Confirm deletion for only the record created in step 4. Record the `DELETE` status and confirm a later detail read returns 404 and the item is absent after closing/reopening the popup. Capture the absent state. Never delete preseeded/shared records to manufacture an empty list.
8. Verify field validation, unavailable-network handling, malformed-response handling, and loading/empty views using an isolated staging test account or controlled local overrides. Keep these marked as **stub/override** where the response was intercepted; do not describe them as deployed API evidence. For malformed-response coverage, the local UI tests already exercise a `SyntaxError`; record the browser method and exact captured response if run manually.
9. Save screenshots and a redacted DevTools Network export under the PR artifacts/evidence. Exclude cookies, auth headers, tokens, personal content, and unrelated requests. Record expected versus actual behavior for every failed step.

For an empty state, use a separate disposable account/database. The shared seeded staging account may contain records; do not clear it.

## Fresh-browser carryover: issues #6 and #22

Carry the fresh-browser gaps linked to [#6](https://github.com/kendshhh/PhishLens/issues/6) and [#22](https://github.com/kendshhh/PhishLens/issues/22) into this run: use a fresh Chrome profile or freshly loaded exact artifact, record browser and package versions, reload/close/reopen as above, and retain screenshots/network evidence for the changed behavior. Check both issue records for their current wording/status before the test and link the evidence there. An issue being administratively closed is not browser evidence and does not satisfy either issue's acceptance.

## Public presentation arrangement with Kendra

**Pending discussion/acceptance.** Record the instructor-accepted arrangement here after Kendra confirms it, including the public production URL (if applicable), how a reviewer reaches the working experience, extension installation/distribution steps, production API target, and what is demonstrated in Chrome. A ZIP is an installation artifact, not a public web application. Do not invent instructor acceptance or present the staging URL as production.

## Run record / handoff

| Field | Result |
|---|---|
| Source SHA / PR | Local preparation only: `f8691e6c5b4e16bea99982a8c9b466b13ddb5e17`; PR not yet recorded |
| CI / hosted deployment | Pending |
| Staging DB confirmation (Trixia/Kendra) | Confirmed in user reply; confirmer identity not specified |
| `/version` / `/ready` actual result | `/version` staging SHA `9bb231a2cc1c701f6a8ce49d35bcdb7b81f56362`; `/ready` ready, database connected |
| Real HTTP CRUD command / output | Passed; record `95e2169c-5e03-45ce-ab4d-8c870ce432ae` cleaned up |
| Chrome version / artifact ID / SHA-256 | Pending |
| Screenshots / Network evidence | Not captured; pending installed Chrome run |
| Public presentation acceptance (Kendra/instructor) | Pending |
| Component defect links | None identified during local prep; report API/client failures to Leyan/Trixia with request/response and record ID |
| Reviewer / required checks | Pending `inaki3023` or authorized backup; no merge/deploy claim |
| Board / sprint log | Pending owner update with this evidence and blockers |

The extension UI implementation is inherited from #46; this branch adds verification preparation. Do not claim #47 integrated or delivered until the real API, exact-package Chrome test, review, CI, and handoff evidence are complete.
