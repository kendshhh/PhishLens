# Issue #151: release demo of the install path and visible states

Recorded 2026-11-15 (Asia/Manila). This run sheet presents the release candidate's
install path and its loading, result, provenance, uncertainty, and controlled
failure and recovery states. It uses only the synthetic message below; no real
inbox, account, provider, staging or production data is involved.

## Release candidate shown

| Item | Value |
|---|---|
| Source revision | `8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f` (`main` after PR #215) |
| Package | `PhishLens-Extension.zip` from CI run [43610239369](https://github.com/kendshhh/PhishLens/actions/runs/43610239369), artifact `PhishLens-Extension` (retained until 2026-11-21) |
| Package SHA-256 | `4172f2aeab03d105e64192e75478cb410b1832295f3f29a5dfc25d26eb7903ba` |
| Package identity | [release-package-identity.json](release-package-identity.json) (48 per-file hashes, clean inputs) |
| Browser | Google Chrome `157.0.8103.79`, Windows |
| Model state | Local LLM weights not included; the expected local outcome is **Uncertain**, never a safe verdict |

This is a newer build than the [#141 demo guide](../issue-141/demo-guide.md)
(`e6d0fd0`); the install steps are the same.

## Install path

1. Use Google Chrome 127 or later.
2. Download the `PhishLens-Extension` artifact from the CI run above and extract
   it. Check that `evidence.json` names source `8c4795f` and that the ZIP's
   SHA-256 matches. Alternatively, clone the repository, check out `8c4795f`, and
   run `npm ci` then `npm run package`; compare the sidecar's per-file hashes,
   because ZIP timestamps change the archive hash.
3. Open `chrome://extensions`, enable **Developer mode**, choose **Load
   unpacked**, and select the extracted `extension` folder. Remove other PhishLens
   copies from the demo profile.
4. Pin PhishLens. The toolbar icon opens the side panel; the right-click menu
   opens the analysis popup for selected text. There is no Web Store listing.

## Presenter flow and observed screens

Synthetic message:

> Subject: Urgent account review
>
> Your account will be closed today. Review it at `https://example.invalid` and
> enter your password to keep access.

| Step | Expected | Observed (installed Chrome, release package) | Screen |
|---|---|---|---|
| Open PhishLens before checking | Ready state; checking does not upload | “Your email stays with you” | [01](01-ready.png) |
| Select the message, right-click, choose **Analyze selection with PhishLens** | The selected text appears and a loading state shows while the local check runs | “Checking your selection…” with the original text and **Cancel check** | [02](02-loading.png) |
| Wait for the result | A labeled result that states its limits; never “safe” | “Uncertain — check before acting”, because the local review cannot run without the weights | [03](03-result.png) |
| Controlled failure | A failed model run shows an error, keeps the text, and shows no verdict | “We couldn’t assess this email”, text retained, **Try again** offered | [04](04-controlled-failure.png) |
| Choose **Try again** | Recovery produces a labeled result | “Uncertain — check before acting” | [05](05-recovery.png) |
| Choose **Clear local scan** | Back to ready | Ready state shown | (recorded in [demo-states.json](demo-states.json)) |
| Saved-report provenance | A saved report shows how it was analyzed | “About this result”: automated analysis, Provider TF-IDF, Model TF-IDF v12a and its revision | [06](06-saved-report-provenance-test-session.png) |

How each screen was produced:

- **Screens 01–05** come from the release package's exact runtime files loaded into
  installed Chrome, with every file checked against the package identity and all
  network requests blocked. `scripts/capture_demo_states.mjs` produced them;
  [demo-states.json](demo-states.json) records each observed heading and screenshot
  SHA-256. The right-click step was driven through the same message the context
  menu sends, because automation cannot open Chrome's context menu.
- **Screen 04's failure is controlled**, triggered by the extension's built-in
  one-shot failure flag (`phishlensDebugFailNext` in session storage), not a real
  model fault. Present it as a controlled demonstration.
- **Screen 06 uses a test-only session.** Saving requires an account, and staging
  accounts are not enabled, so this screen comes from `npm run test:browser` on the
  same archive. That run injects a test-only session and uses a local synthetic API,
  as recorded in [packaged-browser-acceptance.json](packaged-browser-acceptance.json)
  (18 of 18 scenarios passed). The bar across the middle of this full-page capture
  is the fixed bottom navigation, not overlapping content.

During a live demo, stay signed out and do not use **Analyze and save on the
server** or real message content. A keyboard-only path is described in the #141
guide; keyboard checks for this release are recorded under
[`docs/frontend/issue-146/`](../issue-146/) when that evidence is merged.

## Reproduce the screens

1. Put the CI archive's `PhishLens-Extension.zip` and `evidence.json` in
   `output/extension/`.
2. Check out `8c4795f` (or this branch) with `core.autocrlf=false`, so the
   extension files match the Linux-built package, then run `npm ci`.
3. Set `PHISHLENS_CHROME` to the installed Chrome executable and
   `PHISHLENS_PLAYWRIGHT` to `node_modules/playwright/index.mjs`, then run
   `node scripts/capture_demo_states.mjs`. For screen 06, run
   `npm run test:browser` with `PHISHLENS_PYTHON` set.

## Limits

- Local LLM weights are absent, so the release shows Uncertain locally; a full
  local review needs separately provisioned weights and WebGPU `shader-f16`.
- No staging or production service, real provider, or live account is shown.
- The live presentation itself is done by the presenter using this run sheet.
