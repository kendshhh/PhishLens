# Issue #47 — installed-browser CRUD evidence

Date updated: 2026-11-03 (Asia/Manila)
Branch: `test/47-verify-installed-browser-crud`
PR: [#61](https://github.com/kendshhh/PhishLens/pull/61)
Owner: Andrei (`JupitraxNeptuna`)

## Evidence status

The local/package checks and staging API run documented below are historical snapshots from source `23e2973dcc4f4030cc9f58e894116179cb992365`; the older 2026-10-22 PR screenshots came from source `f8691e6c5b4e16bea99982a8c9b466b13ddb5e17`. The reviewed PR head at the time was `5c217fad69067574894e844c5e0ed4ef8d1aafc`, followed by popup code-fix commit `454754c`. The four screenshots supplied on 2026-11-02 and embedded below replace those older images in the PR presentation. Their source/package identity is not visible and is not inferred. They show visible UI states only; they do not establish persistence or deletion after reopening the popup.

| Evidence | Status | Recorded value |
|---|---|---|
| Source revision for recorded local/package checks | Historical snapshot | `23e2973dcc4f4030cc9f58e894116179cb992365` |
| Production archive recorded for that snapshot | Rebuilt locally at that snapshot | `PhishLens-Extension.zip`; SHA-256 `41ca3b82650d2dcf1e93dc4bc37552b5a62c3e71b1a28f2806bb11d12da46d9e`; includes `extension/js/api.js`, `extension/background.js`, CRUD popup assets, and result-view assets |
| Staging package recorded for that snapshot | Local temporary package | Built from source `23e2973dcc4f4030cc9f58e894116179cb992365` for `https://phishlens-staging.onrender.com`; SHA-256 `c52a2d020db71613cefe84ff56ee1f6a14ceff06f5d11e18fe977c38ec3dae78`; 10 runtime files, staging manifest/host, no tests |
| Earlier PR screenshots | Superseded in PR description | Historical 2026-10-22 set; source/package provenance is retained in the prior evidence record, not used for current acceptance |
| Screenshots supplied 2026-11-02 | Visible UI states only; source/package identity unverified | Context-menu mock result, saved-analysis detail, edit form, delete success and empty list; files below |
| UI states shown in those screenshots | Completed on earlier revision | Create/list and detail view; edit notes/feedback form; delete confirmation and visible delete-success state |
| Selected-text analysis in Chrome | Pending current revision | No browser result/error view captured against the current PR head/package |
| CRUD flow in Chrome using current packaged extension | Pending | Current exact-head package has not completed a browser run against staging |
| Notes/feedback persistence after popup reopen | Pending | Not established by existing screenshots or API runner |
| Deletion absent after popup reopen | Pending | Not established by existing screenshots or API runner |
| DevTools Network evidence | Pending | No current-head Network capture/HAR |
| Staging API observed during the historical run | Deployed API verified at that time | `/version` SHA `57da457be77fcf7a132e3a5e2f0d704c676040d6`; `/ready` ready, database connected |
| Staging synthetic CRUD recorded for that run | Passed against deployed API at that time | Guarded client run created and cleaned up synthetic record `854787a0-b7d9-41d6-94a8-1f8fff8cff34` |

### Screenshots replacing the earlier PR images

The following four user-supplied screenshots, dated 2026-11-02, replace the older 2026-10-22 images in the PR description. They show these visible states:

1. Context-menu analysis result with selected text and mock-mode notice.
2. Saved-analysis detail view.
3. Edit notes and feedback form.
4. Delete-success message and empty saved-analysis list.

The screenshots do not visibly identify the source commit, installed package checksum, or Chrome version. They are recorded as supplied visual evidence; they do not establish which package produced them. They show UI states, not a complete create-to-delete run. In particular, they do not demonstrate notes/feedback persistence after closing and reopening the popup, deleted-record absence after reopening, or Network request/response details.

![Context-menu analysis result](evidence/issue-47-chrome-2026-11-02/01-selected-text-analysis.png)

![Saved-analysis detail view](evidence/issue-47-chrome-2026-11-02/04-analysis-details.png)

![Edit notes and feedback form](evidence/issue-47-chrome-2026-11-02/02-edit-notes-feedback.png)

![Delete success and empty saved-analysis list](evidence/issue-47-chrome-2026-11-02/03-delete-success-empty-list.png)

These images supersede the earlier-revision screenshots in the PR presentation. Their provenance is not inferred from their appearance.

## Implementation and local verification at the recorded snapshot

At source snapshot `23e2973dcc4f4030cc9f58e894116179cb992365`, the popup aligned notes with the API's 2,000-character maximum, preserved null feedback during notes-only edits, ignored stale detail responses, and retained the context-menu selected-text result/error view and Clear control alongside CRUD. Production used the five-method API client; the test-only in-memory client was excluded from packaged assets.

The source commit for these checks is `23e2973dcc4f4030cc9f58e894116179cb992365`, not reviewed PR head `5c217fad69067574894e844c5e0ed4ef8d1aafc` or subsequent popup code-fix commit `454754c`. The regenerated production ZIP from that snapshot was configured for the production API; the separately built staging ZIP was configured for staging. Do not install the production ZIP for synthetic staging writes.

Local verification on this source revision:

```text
npm test          PASS — 132 tests
npm run lint      PASS
npm run package   PASS — package and manifest/assets validation
git diff --check  PASS (rerun before commit)
```

The root ZIP was inspected and contains both `extension/js/api.js` and `extension/background.js`, plus the CRUD and context-result UI assets. Packaging evidence in `output/extension/evidence.json` records source/tested commit `23e2973dcc4f4030cc9f58e894116179cb992365`; packaging explicitly does not claim Chrome acceptance.

## Deployed staging API verification

The staging identity observed during this historical run was `57da457be77fcf7a132e3a5e2f0d704c676040d6`; readiness reported `ready` and database `connected` at that time. The guarded runner passed using the real `extension/js/api.js` client from the recorded source snapshot:

```powershell
node scripts/verify_crud.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha 57da457be77fcf7a132e3a5e2f0d704c676040d6 --allow-writes
```

It verified create/list/detail, notes and feedback patching including null feedback, read-after-write, delete, and post-delete 404, then cleaned up only its own synthetic record `854787a0-b7d9-41d6-94a8-1f8fff8cff34`. This is deployed **API** evidence. It is not a packaged-extension browser run and does not satisfy the persistence-after-reopen or deletion-after-reopen browser checks.

## Historical staging and browser screenshot evidence

The staging run recorded here tested PR code revision `40f67d720270d05cb64d9f616fc3d16400ffc960`, which was the PR head when run 41424692539 executed. This is historical evidence for that revision; it does not identify the current PR head. Later documentation and screenshot updates do not change which code revision the run tested.

The four screenshots supplied on 2026-11-02 are included above and replace the older images in the PR description. They show selected-text result content in mock mode, a saved-analysis detail, the edit form, and delete success with an empty list. The images do not expose package identity or Chrome version, so their exact installed-package provenance is unverified.

The PR's Hosted staging run [41424692539](https://github.com/kendshhh/PhishLens/actions/runs/41424692539) passed for code revision `40f67d720270d05cb64d9f616fc3d16400ffc960`; it deployed merge candidate `8b5f292bfb318bf41a3c41fdafa113198facf67e` and produced a staging artifact. This automated deployment evidence does not tie the supplied screenshots to that artifact or establish an installed-Chrome run.

Still pending:

- Verify create, view, edit-save, and delete with the current staging package in Chrome.
- Confirm saved notes and feedback persist after closing and reopening the popup.
- Confirm a deleted record remains absent after closing and reopening the popup.
- Capture redacted Network evidence with request methods, paths, statuses, and response envelopes. Exclude cookies, authorization values, tokens, and personal data.
- Record the exact package SHA-256, Chrome version, and package-to-source identity for the browser run.

The earlier 2026-10-22 screenshots have been superseded in the PR description. The new images are useful visual evidence, but they do not satisfy the pending persistence or Network checks.

## Run record / handoff

| Field | Result |
|---|---|
| Historical evidence source SHA / PR | `23e2973dcc4f4030cc9f58e894116179cb992365` / [PR #61](https://github.com/kendshhh/PhishLens/pull/61); not the reviewed or later PR head |
| Historical local tests/lint/package | Passed for the recorded snapshot as listed above |
| Historical deployed staging API | Passed on staging SHA `57da457be77fcf7a132e3a5e2f0d704c676040d6` at that time |
| Chrome current-head selected-text and CRUD | Pending; extension was not loaded in the attempted session |
| Persistence after popup reopen | Pending |
| Deletion absence after popup reopen | Pending |
| Network evidence | Pending |
| Existing PR screenshots | Earlier revision; links and scope recorded above |
| Public presentation arrangement | Pending Kendra/instructor confirmation |
| Reviewer / required checks / board update | Pending; no merge or deployment claim |

Do not claim #47 fully accepted until current-head packaged-extension browser verification, the three pending evidence items, review, and required checks are complete.
