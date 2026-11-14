# Issue #136 browser acceptance

This evidence is for source commit `6baaad17a03387f6ac9e22f7cb47de8107ac511d` on the Issue #136 integration branch. The packaged extension was tested from the exact archive identified in `package-evidence.json` (SHA-256 `1d452808a00a46c56d0280bd31734a21d9b47a278b97ca353a3f10102a3d1a2d`).

## Results

- `npm run test:browser` passed 15 packaged-extension scenarios in installed Microsoft Edge `157.0.4341.46` using a disposable browser profile and synthetic API. Playwright's bundled Chromium was unavailable, so the runner used its documented headed Edge fallback.
- Keyboard-only checks traversed both the Check email and Saved reports views. Every reached control was visible, named and showed a focus indicator. The report flow used Tab, Shift+Tab, Enter and Space to open a report, cancel an edit and cancel a delete; focus returned to the initiating controls and the synthetic record stayed unchanged. Recorded order is in `browser-acceptance.json`.
- The packaged browser run also checked local scan outcomes, uncertain wording, empty/loading/failed states, safe text rendering, stale-result clearing, synthetic saved-report CRUD and provider provenance. No live provider, real inbox content or production data was used.
- `package-evidence.json` records the package source SHA, ZIP hash, production API host permission and exact file hashes. The browser run intercepted requests at a local synthetic server; its API activity is test-fixture traffic, not production.

## Reproduce

From the repository root, run:

```powershell
npm run package
$env:PHISHLENS_PYTHON = (Get-Command python).Source
npm run test:browser
```

The browser result and screenshots are emitted under `output/extension/`. The committed copies here are the results from the recorded source commit. Screenshot hashes and scenario results are in `browser-acceptance.json`.

## Scope

The permission list is limited to `activeTab`, `contextMenus`, `offscreen`, `scripting` and `storage`; host access is limited to the PhishLens API origin. User-supplied email text is rendered as text, not HTML. Below-threshold output remains explicitly uncertain and does not claim that a message is genuine. The package and browser evidence are separate artifacts; these tests do not claim hosted staging or production acceptance.
