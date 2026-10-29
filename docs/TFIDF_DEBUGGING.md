# Use and debug the TF-IDF extension

A dedicated CLI application is **not required**. Chrome provides the extension
debuggers. The repository adds a small `npm run phishlens -- …` helper so common
checks are easy to remember. It is for developers; users only need Chrome.

## Start here

From this branch's repository folder:

```powershell
npm run phishlens -- doctor
npm test
npm run lint
npm run phishlens -- records-check
```

Use Node 24+ and the repository's locked npm dependencies (`npm ci`). The helper
uses no API keys and does not scan an inbox or upload any text.

1. Open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**
   and select this checkout's `extension` folder.
2. Highlight the visible email body and right-click **Analyze selection with
   PhishLens**. Open the extension icon to see its assessment and checked quotes.
3. A scan runs locally and needs no API or database. Opening the popup also makes
   no API call. **Load / refresh history** explicitly contacts the API.
4. Optional **Save report** requires the upload checkbox. It uploads the original
   selected text, including anything you have not redacted, to shared demo
   storage. Only use authorized material. The backend must independently run the
   same TF-IDF model. This is not personal authenticated multi-user storage.
5. After editing extension code, click **Reload** at `chrome://extensions` and
   reopen the popup. Existing pages need no content-script reload because this
   version uses Chrome's visible selection, not an injected content script.

## Where to look when something fails

| Symptom | Tool / next step |
|---|---|
| Context menu absent or scan cannot start | Extension card → service worker **Inspect** → Console; reload the extension |
| Popup display problem | Right-click the popup → **Inspect** → Console / Elements |
| Model hash or load failure | `npm run model:check`; replace altered files with a verified package |
| Wrong-looking verdict | `npm run phishlens -- scan --file message.txt`; inspect margin and threshold, then add a regression case |
| Saved history unavailable | Popup's history error and DevTools Network; local scanning continues |
| Save disabled | Backend `/model-info` must return matching `tfidf` capability; do not switch silently to Gemini or mock |
| Save timed out | Retry the unchanged report. Its request key is retained in session storage even if the popup closes |
| Saved but refresh failed | Use **Load / refresh history**. Do not create another report to fix a failed refresh |

The diagnostic scan accepts **visible plain text**, not `.eml` MIME source or raw
HTML. It omits the message and quoted evidence from terminal output. Its timing
is a local Node diagnostic, not Chrome benchmark speed or new accuracy evidence.

## Understand or change behavior

| File | Responsibility |
|---|---|
| `extension/background.js` | Selection requests, latest-request/Clear protection, session state and badge |
| `extension/ai/local-analyzer.mjs` | Packaged model loading, SHA-256 checks, cache, invalid-input failure |
| `extension/ai/core.mjs` and `observations.mjs` | Frozen scoring/preprocessing and complete English wording observations |
| `extension/ai/contract.json` | Frozen score mapping and raw-margin alert cutoff |
| `extension/js/popup.js` | Safe rendering, explicit upload consent, history/detail/notes/feedback/delete |
| `extension/js/report-client.js` | Contributors' confirmed-create + independent refresh handling |
| `extension/js/api.js` | Validated CRUD API, timeout and idempotency behavior |
| `backend/ai/tfidf_provider.py` | Server-owned body-only scoring for explicitly saved reports |
| `benchmark-records/index.html` | Preserved historical results and limitations |

The **raw margin ≥ 0** cutoff corresponds to **88.71%** on the fitted display
mapping. Do not replace it with 50%, change weights or adjust the mapping while
claiming the existing v12a results. A changed model/policy needs a separately
planned validation and untouched test cohort. Notes/feedback do not retrain it.

Observations and word-feature contributions are different kinds of explanation.
The former describe checked wording; the latter are partial statistical effects.
Neither authenticates a sender. Below threshold does not mean safe or genuine.
Quote highlights refer to normalized/redacted model input, not original webpage
DOM offsets. Hidden link targets, attachments and authentication headers are not
captured or checked. The UI does not claim they are.

The integration checks replay both already-prepared development fixtures and the
public visible-text adapter separately. Do not clean prepared benchmark inputs
again: one fixture changes under a second cleaning pass. Production browser and
server paths each prepare original visible input once and agree in that replay.
Unsupported word-feature quotes caused by Unicode case expansion are dropped;
this guard does not change classifier scores or thresholds.

## Test a failure for the demo

In the extension's **service-worker Console**:

```javascript
await chrome.storage.session.set({ phishlensDebugFailNext: true });
```

Scan again. The popup must show **Unable to assess** and no confident verdict.
The flag is consumed once; another scan retries normally. To clear the local
scan, use the popup button. It does not delete previously uploaded reports.

## Optional server-owned saved reports

Use the existing backend setup/migration instructions and a **disposable local
database** for testing. Set `AI_MODE=tfidf` in your local environment and start
the API. Existing `mock`, `gemini` and legacy `local` modes remain explicit.
No cloud API key, new database migration or ML library is required for TF-IDF.
The server reads the same tracked model under `extension/ai/`; include that
folder when deploying the API. No hosted environment was changed by this branch.

The production extension's API origin remains the contributor-controlled origin
in `extension/js/config.js`. Use the existing staging package tooling for an
authorized staging target; do not repoint staging to production. For a disposable
localhost integration check use a separate temporary build/profile. Never put
database credentials or raw private messages in Git or bug reports.

`/model-info` checks capability without receiving mail. `X-PhishLens-Model` on
saved creation prevents an extension request from silently using another
provider. The API still rejects client-owned verdict fields. The legacy stored
label `legitimate` means below the cutoff for this binary model, not authenticated.
Saved explanations deliberately contain only original-body word-feature quotes;
the browser also supplies richer deterministic wording observations. Neither is
an LLM-generated explanation, and no new human quality pass is claimed.

## Package

```powershell
python scripts/validate_extension.py
npm run phishlens -- package
```

If `python` is not on PATH, set `PHISHLENS_PYTHON` to your interpreter's full path
for the helper. The ZIP and hash sidecar appear under `output/extension/`.
They contain runtime assets and attribution, not benchmark mail or review cards.
A modified/uncommitted build is recorded as such; packaging is not a production
deployment or proof of a clean release. Run installed-extension acceptance and
disposable database checks before promoting a tagged release.
