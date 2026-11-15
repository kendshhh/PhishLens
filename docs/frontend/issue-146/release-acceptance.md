# Issue #146: Chrome release package acceptance

Recorded 2026-11-15 (Asia/Manila). Synthetic fixtures only; no real inbox,
account, provider, staging or production data was used.

## Release candidate

The candidate is the extension package that CI built on the push of `main` at
`8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f` (PR #215 merge).

| Item | Value |
|---|---|
| Source and tested revision | `8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f` |
| Package | `PhishLens-Extension.zip`, artifact `PhishLens-Extension` of CI run [43610239369](https://github.com/kendshhh/PhishLens/actions/runs/43610239369) (retained until 2026-11-21) |
| Package SHA-256 | `4172f2aeab03d105e64192e75478cb410b1832295f3f29a5dfc25d26eb7903ba` |
| Package identity | [release-package-identity.json](release-package-identity.json): `runtime_or_packaging_changes: false`, 48 per-file hashes |
| Configured API | `https://phishlens-api-ocvt.onrender.com` (production host permission only) |
| Extension version | `0.1.0` |
| Browsers | Installed Google Chrome `157.0.8103.79` (Windows); packaged run in Microsoft Edge `157.0.4341.46` because bundled Playwright Chromium was not installed |

The CI archive was downloaded and checked against its sidecar before use. For the
installed Chrome run, the repository's `extension` folder was checked out at the
same revision without line-ending conversion, and all 48 runtime files matched
the package's per-file hashes before loading.

## Expected versus observed

| Check | Expected | Observed | Result |
|---|---|---|---|
| Package identity | The archive matches its sidecar and was built from clean inputs | SHA-256 matched; `runtime_or_packaging_changes: false`; source and tested revision `8c4795f` | Pass |
| Permissions in installed Chrome | Chrome grants exactly what the manifest requests | `activeTab`, `contextMenus`, `offscreen`, `scripting`, `sidePanel`, `storage`, and only `https://phishlens-api-ocvt.onrender.com/*` | Pass |
| Console in installed Chrome | No console errors, permission warnings or uncaught errors | None recorded across the full smoke | Pass |
| Entry points | Toolbar opens the side panel; no toolbar popup is configured | `openPanelOnActionClick: true`; no global popup | Pass |
| Opening without a scan | Ready state, no API or upload request | Ready state; 0 API requests | Pass |
| Local scan | Labeled result; never a safe verdict | Without local LLM weights the result reads “Uncertain — check before acting” ([screenshot](release-chrome-157-scan.png)) | Pass; limitation visible |
| Error state | A failed model run shows an error, not a verdict | Simulated failure showed “Unable to assess” with no result | Pass |
| Recovery | Retry produces a result; Clear returns to ready | Both worked | Pass |
| Signed-out saving | No upload without an account and consent | Save report and consent disabled; 0 API requests | Pass |
| Keyboard | Controls reachable, named and visibly focused; a check can be run by keyboard | Tab cycles passed in both views; keyboard-only paste and check produced a labeled result | Pass |
| Empty and error history, saved-report journey (packaged run) | Empty history and history failure render clearly; create, read, edit, delete and reopen work | 18 of 18 scenarios passed with a local synthetic API and a test-only session | Pass |
| Provider and history failures (packaged run) | Input kept, no false verdict; confirmed save kept with a warning | Both passed ([provider failure](release-packaged-03-synthetic-provider-failure-preserves-input.png), [history failure](release-packaged-04-synthetic-history-refresh-failure-keeps-saved-report.png)) | Pass |

## Evidence

- [Installed Chrome smoke](release-chrome-157-smoke.json): 14 of 14 checks,
  including the console and permission checks added for this issue; 0 API requests;
  temporary profile removed.
- [Packaged browser acceptance](release-packaged-browser-acceptance.json): the exact
  CI archive, checked against its sidecar, passed 18 of 18 scenarios. A local path in
  its browser-fallback reason is redacted. Its four screenshots are stored here with
  a `release-packaged-` prefix; their SHA-256 values are listed in the JSON.

## Reproduce

1. Download the `PhishLens-Extension` artifact from CI run 43610239369 and place
   `PhishLens-Extension.zip` and `evidence.json` in `output/extension/`.
2. Check out `8c4795f` (or this branch) with `core.autocrlf=false` so the
   extension files match the Linux-built package byte for byte, then run `npm ci`.
3. Run `npm run test:browser` with `PHISHLENS_PYTHON` set, then
   `node scripts/check_extension_browser.mjs` with `PHISHLENS_CHROME` and
   `PHISHLENS_PLAYWRIGHT` set as described in `docs/frontend/issue-136/installed-a11y-audit.md`.

## Limits

- This accepts the production-configured package with intercepted or synthetic
  API traffic. It is not a staging or production connection test, a Web Store
  release, or an AI accuracy study.
- Local LLM weights are not in the package, so the visible local outcome is
  Uncertain; a full local review requires separately provisioned weights.
- The right-click context menu cannot be triggered by automation; the menu's
  handler is covered by unit tests and the #131 manual check.
- The issue's “visible-change deployment challenge, if part of the rubric” is not
  prepared here: it depends on the course rubric and a deployment, which the team
  has not authorized.
