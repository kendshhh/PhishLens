# PhishLens web app

A static web version of PhishLens. Paste an email's text, choose **Check this
email**, and the check runs in the browser tab. The text is not uploaded.

The web app reuses the extension's code rather than copying it:

- `extension/js/` provides the user interface, saved-report client and account screens;
- `extension/ai/` provides the local analysis workflow and model files;
- `extension/css/popup.css` provides the styles.

Only the browser runtime differs. [`runtime.js`](runtime.js) replaces the extension's
background service worker and `chrome.storage.session`:

- it runs the analysis in the page;
- it keeps the current check and draft in this tab's `sessionStorage`, which is
  cleared when the tab closes.

## Files

| File | Purpose |
|---|---|
| `index.html` | The page. It uses the same element IDs as `extension/popup.html`, with paste-first wording. |
| `app.js` | Entry point: connects the shared UI to the web runtime. |
| `runtime.js` | In-page replacement for the extension's background worker and session storage. |
| `css/web.css` | Full-width page layout on top of the shared stylesheet. |
| `favicon.svg` | Browser tab icon. |
| `tests/runtime.test.mjs` | Unit tests for the runtime (part of `npm test`). |
| `../scripts/build_web.mjs` | Copies the web files and shared modules into `web/dist`, and fails if an import or model file is missing. |
| `../scripts/serve_web.mjs` | Loopback preview of generated security headers and fixed API proxy routes. |
| `../scripts/web_build_config.mjs` | Strict public environment, API, Auth and backend-SHA pairing; generated CSP/routes. |
| `../vercel.json` | Build command; Vercel consumes generated `.vercel/output` (Build Output API v3). |

## Run locally

```sh
npm run web:build
npm run web:serve
```

Then open http://127.0.0.1:4173/. Rebuild after changing files in `web/` or `extension/`.

## Deploy on Vercel

Use the agreed project/account/domain and release gates in
[the web release guide](../docs/web-release.md). Keep **Root Directory** as the
repository root. `vercel.json` and the build output define:
   - **Build:** `node scripts/build_web.mjs`.
   - **Output:** `.vercel/output/static` with generated `.vercel/output/config.json`.
   - **No npm install:** the build uses only Node built-ins.
   - **Headers/routing:** CSP, other security headers and fixed API proxy routes.
   - **Identity:** public `build-info.json` with source SHA, dirty flag and file hashes.

The default local-scan-only build needs no variables or secrets. Accounts require
the verified public build settings listed in the release guide. Never supply
database credentials, passwords or tokens to this static build. A development
build supports loopback tests and emits no deployable Vercel output.

## Current limits

- **Highlight and right-click are on hold.** They remain extension-only while
  the team decides on them. The shared client changes retain extension compatibility;
  Chrome regression evidence remains separate from web acceptance.
- **The full local review needs model files a static site doesn't ship.** The LLM
  review needs about 1 GB of weights and WebGPU. The hosted app reports the
  reviewer as unavailable, so results read **Uncertain — check before acting**,
  never a safe verdict. That's the same outcome as the current extension release
  without weights.
- **Sign-in and saved reports are disabled by default.** The public build settings
  generate account configuration and CSP. The same-origin API proxy avoids a
  Render CORS change; Neon Auth still requires the exact trusted web origin and
  real browser-cookie acceptance. The compatible backend must enforce Neon report
  mode. Local substitute-provider evidence does not establish hosted acceptance.
