# Issue #131: installed browser UX and install path audit

Audit refreshed 2026-11-14 (Asia/Manila) for the split entry flow agreed with
PR #156. Synthetic fixtures only; no real inbox, production API, or database was
used. The earlier audit of the side-panel-only build `70d1940` is superseded by
this record.

## Entry flow audited

- **Primary:** highlight email text, right-click, and choose **Analyze selection
  with PhishLens**. The background worker reads the source-frame selection, stores
  the loading state, sets `popup.html?surface=popup` as the popup for that tab
  only, calls `chrome.action.openPopup()`, then clears the tab's popup.
- **Secondary:** the toolbar button opens the same page in the side panel. The
  manifest defines no `action.default_popup`, because Chrome gives a configured
  popup priority over `sidePanel.setPanelBehavior({ openPanelOnActionClick: true })`.
- Chrome 127 or newer is required for `chrome.action.openPopup()`.

## Package and source identity

- Extension version: `0.1.0`.
- Source and tested Git revision: `7301b953c678ab9c8657cad323ac1eecc65f62fe`.
- The identity sidecar marks `runtime_or_packaging_changes: false` and records a
  SHA-256 for every package file.
- Generated archive: `PhishLens-Extension.zip`, SHA-256
  `68cdbe2c66352310f581dd43c8d6fb38d871dc98ca55d3b631c95cfa91721eb1`.
- Sidecar: [package-identity.json](package-identity.json). The archive omits the
  optional LLM weights (about 1.1 GB), which must be provisioned separately. The
  sidecar's `environment: production` describes the package's configured API
  target; browser requests in this audit were redirected to a local synthetic API
  or intercepted. No production or staging service was contacted.

## Observations

| Area | Expected | Observed | Result |
|---|---|---|---|
| Right-click entry | Selected text opens the scan in the action popup | The context-menu handler opened the real action popup at `/popup.html?surface=popup` with the selected text; the popup used its fixed 380px layout. | Pass in the packaged browser run |
| Toolbar entry | Toolbar button opens the side panel, not the popup | After the right-click popup opened, the source tab and the global action had no popup configured, and `openPanelOnActionClick` was `true`. Chrome 157 also reported no global popup and `openPanelOnActionClick: true`. In the manual installed-Chrome run, clicking the toolbar button opened the side panel and no popup appeared. | Pass (automated configuration check and manual click) |
| Initial/loading/result | Start ready; show progress; release a result only when the full review supports it | Ready and loading states rendered. Without local LLM weights, the packaged run showed “Uncertain — check before acting”. | Pass; uncertainty is explicit |
| Error and retry | An interrupted or failed local review must not appear safe | Chrome 157 synthetic failure rendered “Unable to assess”; retry returned to a result and Clear returned to ready. | Pass |
| Safe text | Untrusted text is displayed as text | The seeded history title `Synthetic <script>alert(1)</script>` and the subject `Synthetic provider fixture <img src=x>` rendered literally; no script or image element was created. Chrome 157 found no inline script in the rendered page. | Pass |
| Keyboard and labels | Controls are reachable and labeled, with visible focus | Keyboard-only Tab cycles reached 11 controls in Check email and 7 in Saved reports, each visible, named and outlined. A keyboard-only report open, edit cancel and delete cancel returned focus without changing the record. | Pass for keyboard and markup; no screen-reader session was run |
| Permissions | Request only the access needed for the described flows | `contextMenus`, `sidePanel`, `activeTab`, `scripting`, `storage`, `offscreen`, and only `https://phishlens-api-ocvt.onrender.com/*`. `activeTab` and `scripting` read the clicked frame's selection; no broad host or web-request permission. | Pass |
| Signed-out saving | No upload without an account and consent | In Chrome 157 without a session, Save report and consent stayed disabled and no API request was made. | Pass |
| Install route | Public page leads to clear, reproducible install steps | The landing-page source links to the GitHub README, which covers the repository ZIP, model setup, Developer mode, Load unpacked, right-click use and the optional pinned side panel. No Chrome Web Store listing exists; a deployed landing-page URL was not available to verify. | Source path documented; live deployment unverified |

## Evidence

- [Packaged browser acceptance](packaged-browser-acceptance.json): exact archive
  checked against its SHA-256 sidecar; 18 of 18 scenarios passed, including the
  right-click popup, toolbar side-panel configuration, keyboard checks, safe
  rendering, local scan, cancel/retry and synthetic saved-report CRUD. Bundled
  Playwright Chromium was not installed, so the runner used installed Microsoft
  Edge `157.0.4341.46`. The local path in its fallback reason is redacted. API
  requests went to a local synthetic server.
- Screenshots from that run:
  [provider-backed report](01-synthetic-provider-backed-saved-report.png),
  [after popup reopen](02-synthetic-provider-report-after-popup-reopen.png),
  [provider failure keeps input](03-synthetic-provider-failure-preserves-input.png),
  [history refresh failure keeps the report](04-synthetic-history-refresh-failure-keeps-saved-report.png).
  These full-page captures show the fixed bottom navigation partway down the image.
- [Chrome 157 smoke](chrome-157-browser-smoke.json): the unpacked extension from
  the same clean revision loaded in a disposable Chrome `157.0.8103.79` profile;
  its runtime file hashes match the sidecar. 10 of 10 checks passed with 0 API
  requests, and the temporary profile was removed. This smoke runs signed out;
  saved-report CRUD is covered by the packaged run's test session.
- Extension and package checks on this revision: `npm test` (296 passed),
  `npm run lint`, `npm run validate`, and `python -m unittest discover -s
  scripts/tests` (164 passed).

## Manual installed-Chrome check

Recorded 2026-11-14 by Andrei in installed Google Chrome `157.0.8103.79` on
Windows, with the extension loaded unpacked from the repository's `extension`
folder. The 48 packaged runtime files in that folder matched the
[package identity](package-identity.json) for `7301b95`; `manifest.json` differed
only in line endings (LF locally, CRLF in the identity checkout). The selected text
was a synthetic phishing sample with `example.com` addresses shown in a web page,
not a real inbox. No account was signed in to PhishLens and no report was saved.

| Step | Expected | Observed | Result |
|---|---|---|---|
| [Click the pinned toolbar button](manual-chrome-157/01-toolbar-opens-side-panel.png) | The side panel opens in its ready state | The side panel opened with “Highlight. Right-click. Check.” and “Your email stays with you”; no popup appeared. | Pass |
| [Select text and right-click](manual-chrome-157/02-right-click-analyze-selection-menu.png) | The context menu offers “Analyze selection with PhishLens” | The menu showed “Analyze selection with PhishLens”. | Pass |
| [Choose Analyze selection](manual-chrome-157/03-right-click-result-uncertain.png) | The selected text is analyzed locally and shown with an explicit result | The open side panel showed the analyzed text and “Uncertain — check before acting”, because the local LLM review could not run in this install. No safe verdict was shown. | Pass; uncertainty is explicit |

The side panel was already open during the right-click step, and the toolbar is
outside the captured area, so these screenshots do not show whether the action
popup also opened. The popup opening is evidenced by the automated packaged run
above.

| Screenshot | SHA-256 |
|---|---|
| `manual-chrome-157/01-toolbar-opens-side-panel.png` | `38b856cce392da4c4ac7eeb74ddd4c64a19340fce90c46c4443638d2cc03c8d8` |
| `manual-chrome-157/02-right-click-analyze-selection-menu.png` | `1535f2ed99adab0aacb0d06e1d119ddad81ce86b343f5784bf4afe07d6fb9968` |
| `manual-chrome-157/03-right-click-result-uncertain.png` | `0380bc1d2cae98c396c2d19359badd17a71d44e95e0a9c004c95931e87e72d17` |

## Open defects

1. **P3 — paragraph breaks lost for this page's selection.** In the manual run, the
   analyzed text shows the selection's paragraphs joined by spaces. The worker
   therefore used Chrome's flattened `selectionText` instead of the source-frame
   selection, which it does when the page selection cannot be read or does not
   match the menu text word for word. Classification is unaffected, but the
   displayed text loses its layout. Next step: reproduce on this page and log
   whether `scripting.executeScript` fails or the word comparison rejects the
   page selection.

## Defects fixed

1. **P1 — install instructions could not produce a complete local review.** The
   install guidance now explains the 1.1 GB model setup and the WebGPU
   shader-f16 requirement; without those weights, the visible outcome is Uncertain.
2. **P1 — no clear route from the landing page.** The landing-page source links
   directly to the GitHub install instructions.
3. **P1 — the toolbar could not open the side panel while a popup was declared.**
   A manifest `default_popup` takes priority over `openPanelOnActionClick`. The
   popup is now set only for the right-clicked tab and cleared after it opens.
4. **P2 — stale product and entry guidance.** README now describes PhishLens,
   right-click analysis in the popup, the optional toolbar side panel and Chrome 127+.
5. **P2 — layout assumed one surface.** The shared page keeps a fixed popup size
   for `?surface=popup` and a fluid layout in the side panel.

## Remaining evidence limits

This is local software verification, not a production deployment, Web Store
publication, persistence test, AI accuracy study, or screen-reader audit. The
manual run used an install without the local LLM weights, so it shows the
Uncertain path rather than a released local verdict. The right-click popup was
observed only in the automated packaged run, not in the manual screenshots. The
live landing page and Web Store publication remain unverified.
