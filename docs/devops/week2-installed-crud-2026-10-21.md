# Issue #47 — installed-browser CRUD evidence

Date updated: 2026-10-29 (Asia/Manila)
Branch: `test/47-verify-installed-browser-crud`
PR: [#61](https://github.com/kendshhh/PhishLens/pull/61)
Owner: Andrei (`JupitraxNeptuna`)

## Evidence status

This record separates screenshots from the earlier PR revision, current local/package checks, deployed staging API checks, and installed Chrome checks. The screenshots below document visible UI states only; they do not establish persistence or deletion after reopening the popup.

| Evidence | Status | Recorded value |
|---|---|---|
| Current source revision | Local branch | `23e2973dcc4f4030cc9f58e894116179cb992365` |
| Current production archive | Rebuilt locally | `PhishLens-Extension.zip`; SHA-256 `41ca3b82650d2dcf1e93dc4bc37552b5a62c3e71b1a28f2806bb11d12da46d9e`; includes `extension/js/api.js`, `extension/background.js`, CRUD popup assets, and result-view assets |
| Current staging package | Local temporary package | Built from current source for `https://phishlens-staging.onrender.com`; SHA-256 `c52a2d020db71613cefe84ff56ee1f6a14ceff06f5d11e18fe977c38ec3dae78`; 10 runtime files, staging manifest/host, no tests |
| Existing PR screenshots | Earlier revision only | Source `f8691e6c5b4e16bea99982a8c9b466b13ddb5e17`; package SHA `a5e7cb6f82fc91750fb5b3e7f95eb47ea9efc5c4b9fa001d41b7ad88b77afff9`; Chrome `153.0.8010.55`; see links below |
| UI states shown in those screenshots | Completed on earlier revision | Create/list and detail view; edit notes/feedback form; delete confirmation and visible delete-success state |
| Selected-text analysis in Chrome | Pending current revision | No browser result/error view captured against the current PR head/package |
| CRUD flow in Chrome using current packaged extension | Pending | Current exact-head package has not completed a browser run against staging |
| Notes/feedback persistence after popup reopen | Pending | Not established by existing screenshots or API runner |
| Deletion absent after popup reopen | Pending | Not established by existing screenshots or API runner |
| DevTools Network evidence | Pending | No current-head Network capture/HAR |
| Current staging API | Deployed API verified | `/version` SHA `57da457be77fcf7a132e3a5e2f0d704c676040d6`; `/ready` ready, database connected |
| Current staging synthetic CRUD | Passed against deployed API | Guarded client run created and cleaned up synthetic record `854787a0-b7d9-41d6-94a8-1f8fff8cff34` |

### Screenshots attached to PR #61

These are linked from the PR description and have the older source/package provenance listed above:

- [Create and view](https://github.com/user-attachments/assets/45d3376e-33aa-4a32-b7c8-349db08835a9)
- [Edit notes and feedback](https://github.com/user-attachments/assets/d803b6e9-bddf-4202-b566-7dbe64985113)
- [Delete confirmation](https://github.com/user-attachments/assets/d7ce9c60-a0d0-429b-9b4d-cf346676a0d7)
- [Delete success](https://github.com/user-attachments/assets/973f06ad-e3e3-4a1b-9914-3b7335cf5225)

They show those screens were reached on the earlier revision. They do not prove the current PR head, successful persistence through reopening, absence after reopening, selected-text analysis, or Network request/response statuses. The PR narrative’s claim of screenshot completion is retained with that scope.

## Current implementation and local verification

The current popup aligns notes with the API’s 2,000-character maximum, preserves null feedback during notes-only edits, ignores stale detail responses, and retains the context-menu selected-text result/error view and Clear control alongside CRUD. Production uses the five-method API client; the test-only in-memory client is excluded from packaged assets.

The source commit is `23e2973dcc4f4030cc9f58e894116179cb992365`. The regenerated production ZIP is configured for the production API; the separately built staging ZIP is configured for staging. Do not install the production ZIP for synthetic staging writes.

Local verification on this source revision:

```text
npm test          PASS — 132 tests
npm run lint      PASS
npm run package   PASS — package and manifest/assets validation
git diff --check  PASS (rerun before commit)
```

The root ZIP was inspected and contains both `extension/js/api.js` and `extension/background.js`, plus the CRUD and context-result UI assets. Packaging evidence in `output/extension/evidence.json` records source/tested commit `23e2973dcc4f4030cc9f58e894116179cb992365`; packaging explicitly does not claim Chrome acceptance.

## Deployed staging API verification

The latest staging identity observed during this run was `57da457be77fcf7a132e3a5e2f0d704c676040d6`; readiness reported `ready` and database `connected`. The guarded runner passed using the real `extension/js/api.js` client:

```powershell
node scripts/verify_crud.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha 57da457be77fcf7a132e3a5e2f0d704c676040d6 --allow-writes
```

It verified create/list/detail, notes and feedback patching including null feedback, read-after-write, delete, and post-delete 404, then cleaned up only its own synthetic record `854787a0-b7d9-41d6-94a8-1f8fff8cff34`. This is deployed **API** evidence. It is not a packaged-extension browser run and does not satisfy the persistence-after-reopen or deletion-after-reopen browser checks.

## Browser verification still required

The current PR head/package still needs installation in a fresh Chrome profile, with the staging-target package. Record Chrome version, source SHA, package SHA-256, `/version` identity, and the exact artifact used. Verify selected-text analysis result and error rendering, then create, view, edit notes/feedback, and delete a synthetic record through the packaged extension against staging. Capture screenshots and a redacted Network record showing request methods, paths, statuses, and response envelope. Do not include cookies, authorization values, tokens, or personal data.

Keep these acceptance items pending until captured against the current PR head:

- Notes and feedback still present after closing and reopening the popup.
- Deleted record remains absent after closing and reopening the popup.
- DevTools Network evidence for the full flow.

The PR screenshots linked above are useful evidence for visible earlier-revision states, but do not substitute for this current-head run. The current Chrome attempt did not load the extension: Chrome ignored the command-line unpacked-extension switches and the `chrome://extensions` Load unpacked action did not produce a folder picker. No PhishLens action was performed in that browser session, so no Chrome acceptance is claimed.

## Run record / handoff

| Field | Result |
|---|---|
| Source SHA / PR | `23e2973dcc4f4030cc9f58e894116179cb992365` / [PR #61](https://github.com/kendshhh/PhishLens/pull/61) |
| Local tests/lint/package | Passed as listed above |
| Deployed staging API | Passed on staging SHA `57da457be77fcf7a132e3a5e2f0d704c676040d6` |
| Chrome current-head selected-text and CRUD | Pending; extension was not loaded in the attempted session |
| Persistence after popup reopen | Pending |
| Deletion absence after popup reopen | Pending |
| Network evidence | Pending |
| Existing PR screenshots | Earlier revision; links and scope recorded above |
| Public presentation arrangement | Pending Kendra/instructor confirmation |
| Reviewer / required checks / board update | Pending; no merge or deployment claim |

Do not claim #47 fully accepted until current-head packaged-extension browser verification, the three pending evidence items, review, and required checks are complete.
