# Issue #131: installed browser UX and install path audit

Audit recorded 2026-11-14 (Asia/Manila). Synthetic fixtures only; no real inbox,
production API, or database was used.

## Package and source identity

- Extension version: `0.1.0`.
- Source and tested Git revision: `70d1940f84472fcb1de533c2e87d38fd7007edc9`.
- The identity sidecar marks `runtime_or_packaging_changes: false` and records a
  SHA-256 for every package file; the archive digest below identifies the exact
  bytes that were exercised.
- Generated archive: `PhishLens-Extension.zip`, SHA-256
  `3480d67b642dc14deb11732f070682729dda950adbdca9134ef15a8272ff3eb4`.
- Sidecar: [package-identity.json](package-identity.json). The archive omits the
  optional LLM weights; they are about 1.1 GB and must be provisioned separately.
  The sidecar's `environment: production` describes the package's configured API
  target; browser requests in this audit were redirected to a local synthetic API.
  No production or staging service was contacted.

## Observations

| Area | Expected | Observed | Result |
|---|---|---|---|
| Initial/loading/result | Start ready; show progress; release a result only when the full review supports it | Ready and loading states rendered. Packaged Chromium rendered “Uncertain — full review not confirmed” because local LLM weights were absent. | Pass; uncertainty is explicit |
| Error and retry | An interrupted/failed local review must not appear safe | Chrome 157 synthetic failure rendered “Unable to assess”; retry returned to a result state and Clear returned to ready. | Pass |
| Safe text | Untrusted saved text is displayed as text | A synthetic subject containing `<script>alert(1)</script>` appeared literally; no script or image element was created. | Pass |
| Keyboard and labels | Controls are reachable and labeled, with visible focus | First Tab reached Clear and showed a focus outline. Form controls have associated labels; status regions use live/status semantics. | Pass for keyboard focus and markup; no screen-reader session was run |
| Permissions | Request only the browser/API access needed for the described flows | Manifest requests `contextMenus`, `sidePanel`, `storage`, and `offscreen`, plus only `https://phishlens-api-ocvt.onrender.com/*`. It has no broad page, tab, or web-request permission. | Pass; Chrome 116 minimum recorded for `sidePanel.open()` |
| Toolbar and selection entry | Toolbar opens panel; selected text opens the scan in the panel | Chrome 157 reported `openPanelOnActionClick: true`. The context-menu handler was unit-tested to open the clicked tab's panel and analyze its selection. | Pass in isolated Chrome software smoke and unit tests |
| Install route | Public page leads to clear, reproducible install steps | The landing-page source now points to the GitHub README. README describes repository ZIP, model setup, Developer mode, and Load unpacked. No Chrome Web Store listing exists; a deployed landing-page URL was not available to verify. | Source path documented; live deployment remains unverified |

## Evidence

- [Packaged browser acceptance](packaged-browser-acceptance.json): exact archive,
  SHA-256 sidecar verification, synthetic Chromium `156.0.8078.4`; all thirteen
  scenarios passed, including side-panel toolbar behavior, keyboard focus, safe
  rendering, local scan and synthetic saved-report flows. API requests were
  redirected to a local synthetic server. Screenshots are attached.
- [Chrome 157 smoke](chrome-157-browser-smoke.json): unpacked extension loaded in
  a disposable Chrome `157.0.8103.79` profile. Its source commit, version, archive
  digest, and each runtime file hash match the package identity sidecar. Local scan,
  upload consent, synthetic save/read/edit/delete, failure, retry, Clear, and
  side-panel behavior passed. Eight API requests were intercepted. Temporary
  profile was removed.
- Extension and package checks: `npm run validate`, `npm test` (253 passed),
  `npm run lint`, and `python -m unittest discover -s scripts/tests -p
  test_extension_assets.py` (6 passed).
- The four synthetic saved-report screenshots listed in the browser-acceptance
  evidence were captured from this packaged browser run.

## Defects fixed

1. **P1 — install instructions could not produce a complete local review.** The
   install guidance omitted the separately provisioned LLM weights. It now explains
   the 1.1 GB model setup and the WebGPU shader-f16 requirement; without those
   weights, the visible outcome is Uncertain.
2. **P1 — no clear route from the landing page.** The landing-page source now links
   directly to the GitHub install instructions. The project does not have a Web
   Store listing, and the live page was not available for deployment verification.
3. **P2 — stale product and popup guidance.** README referred to “VeriQo” and a
   toolbar popup. It now describes the PhishLens side panel and the supported
   Chrome 116+ install flow.
4. **P2 — extension UI validation expected a fixed-width popup.** The responsive
   side-panel expectation, Chrome minimum, and manifest target are now checked.
   The browser acceptance runner also opens the collapsed save disclosure before
   exercising its fields and uses a configurable Python interpreter.

## Remaining evidence limits

This is local software verification, not a production deployment, Web Store
publication, persistence test, AI accuracy study, or screen-reader audit. The
Chrome UI smoke loaded the unpacked source in a disposable profile; the packaged
archive was exercised separately in isolated Chromium. The live landing page and
Web Store publication remain unverified. The committed install path is the GitHub
repository ZIP and local unpacked install described above.
