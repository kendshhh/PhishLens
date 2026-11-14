# Issue #136: accessible browser states and safe rendering on `main`

Audit recorded 2026-11-14 (Asia/Manila) for the code on `main` after #203 and
#204. Synthetic fixtures only; no real inbox, production API, account, or
database was used.

## Package and source identity

- Extension version: `0.1.0`.
- Source and tested Git revision: `eb8d74132c7fd637ae36d3db251e443d9e622a0f`
  (`main` at `ef9dec2` plus the keyboard checks added to the installed Chrome
  smoke in this PR).
- Generated archive: `PhishLens-Extension.zip`, SHA-256
  `342e24c25e95d0fa9d668e06d110e5448616b068c7832ae5e45b5865077025aa`.
  The identity sidecar marks `runtime_or_packaging_changes: false`:
  [installed-a11y-package-identity.json](installed-a11y-package-identity.json).
  Its `environment: production` is the package's configured API target; every
  browser request in this audit went to a local synthetic API or was intercepted.
- Installed browser: Google Chrome `157.0.8103.79` (Windows), with the unpacked
  extension loaded into a disposable profile. Packaged run: Microsoft Edge
  `157.0.4341.46`, because bundled Playwright Chromium was not installed.

## Observations

| Area | Expected | Observed | Result |
|---|---|---|---|
| Keyboard reach and focus, installed Chrome | Every control Tab reaches is visible, has an accessible name and shows a focus indicator | Full Tab cycles: Check email view (ready state) reached 4 controls; signed-out Saved reports reached 4, including “Sign in to view reports”. All visible, named and outlined. | Pass |
| Keyboard-only state change, installed Chrome | A check can be started and read without a mouse | Tab and Enter opened “Or paste email text”; typing a synthetic email and pressing Enter on “Check this email” produced a labeled result; Tab and Enter switched to Saved reports (`aria-pressed=true`). | Pass |
| Keyboard flows with reports, packaged run | Report open, edit cancel and delete cancel work by keyboard and restore focus | Tab cycles reached 11 controls (Check email, with a result) and 7 (Saved reports, test session). Report open, edit cancel and delete cancel returned focus to the trigger without changing the record. | Pass |
| Loading, empty, failed and uncertain states | States are readable; failure never looks safe | Ready, loading, result, “Unable to assess” (simulated failure), retry and Clear passed in installed Chrome. Without local LLM weights, results read “Uncertain — check before acting” ([screenshot](installed-a11y-chrome-157-scan.png)). Packaged run: empty history, history failure and provider failure keep input and show an error, not an empty or safe state. | Pass |
| No false safe verdict | No result is presented as safe or genuine | Keyboard-checked result labels matched Suspicious / No strong warning signs / Uncertain and never “safe”, “genuine” or “legitimate”. A `legitimate` prediction is displayed as “No strong warning signs”; the footer states “Below threshold does not mean genuine.” | Pass |
| Safe text rendering | Untrusted text is rendered as text | No `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `DOMParser`, `eval` or `new Function` in extension code (vendor excluded). Hostile subjects such as `Synthetic <script>alert(1)</script>` and `<img src=x>` rendered literally with no element created; installed Chrome found no inline script in the page. | Pass |
| Permission scope | No broad permissions | `contextMenus`, `sidePanel`, `activeTab`, `scripting`, `storage`, `offscreen`; host access only to `https://phishlens-api-ocvt.onrender.com/*`; no `<all_urls>`, `tabs` or web-request permission. `activeTab` and `scripting` read the right-clicked frame's selection. | Pass |
| No silent upload | Checking does not upload; saving needs sign-in and consent | Installed Chrome made 0 API requests across all checks; signed out, Save report and consent stayed disabled. | Pass |

## Evidence

- [Installed Chrome smoke](installed-a11y-chrome-157-smoke.json): 12 of 12 checks
  passed in Chrome `157.0.8103.79`, including both keyboard checks; runtime file
  hashes match the package identity; 0 API requests; temporary profile removed.
  The keyboard Tab orders are recorded under `keyboard_tab_order`.
- [Packaged browser acceptance](installed-a11y-packaged-browser-acceptance.json):
  the exact archive, checked against its SHA-256 sidecar, passed 18 of 18
  scenarios with a local synthetic API and a test-only session. A local path in
  the browser-fallback reason is redacted. One earlier run on the same revision
  failed one scenario: the history-refresh-failure check found the saved report's
  detail panel not yet visible. The same scenario passed in every other run,
  including two consecutive reruns, so it is recorded as an intermittent timing
  issue in the test, not a product defect.
- Repository checks on this revision: `npm test` (296 passed), `npm run lint`,
  `npm run validate`.

Reproduce from the repository root on a clean checkout:

```powershell
npm ci
npm run package
$env:PHISHLENS_PYTHON = (Get-Command python).Source
npm run test:browser
$env:PHISHLENS_CHROME = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$env:PHISHLENS_PLAYWRIGHT = (Resolve-Path node_modules/playwright/index.mjs).Path
node scripts/check_extension_browser.mjs
```

## Relation to other evidence

#203 restored focus after cancelled edits and deletes and added the packaged
keyboard checks. PR #202 records separate #136 evidence for the #156 integration
branch (source `6baaad1`); this record covers `main`. The two sets are kept apart
and do not share files.

## Remaining limits

This is automated keyboard verification in installed Chrome and a packaged
browser, not a screen-reader session or an independent accessibility audit.
Signed-in keyboard flows (saved reports in installed Chrome) need a live account,
which staging does not yet enable; they are covered by the packaged run's
test-only session. Colour contrast was not measured.
