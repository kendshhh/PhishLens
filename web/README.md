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
| `../scripts/serve_web.mjs` | Local preview server that applies the same headers as `vercel.json`. |
| `../vercel.json` | Vercel build, output and security-header settings. |

## Run locally

```sh
npm run web:build
npm run web:serve
```

Then open http://127.0.0.1:4173/. Rebuild after changing files in `web/` or `extension/`.

## Deploy on Vercel

1. In Vercel, choose **Add New → Project** and import the PhishLens repository.
2. Keep **Root Directory** as the repository root. `vercel.json` sets everything
   else:
   - **Build:** `node scripts/build_web.mjs`.
   - **Output:** `web/dist`.
   - **No npm install:** the build uses only Node built-ins.
   - **Headers:** a Content-Security-Policy and other security headers.
3. Deploy. Pull requests get preview deployments; the production branch is set in
   **Project Settings → Git**.

No environment variables or secrets are needed.

## Current limits

- **Highlight and right-click are on hold.** They remain extension-only while
  the team decides on them, and the extension in `extension/` is unchanged.
- **The full local review needs model files a static site doesn't ship.** The LLM
  review needs about 1 GB of weights and WebGPU. The hosted app reports the
  reviewer as unavailable, so results read **Uncertain — check before acting**,
  never a safe verdict. That's the same outcome as the current extension release
  without weights.
- **Sign-in and saved reports stay disabled** until `AUTH_CONFIG` is set. Enabling
  them needs:
  - the backend to allow the deployed web origin through CORS (it currently sends
    no CORS headers);
  - the Neon Auth origin added to `connect-src` in `vercel.json`;
  - the web origin added as a trusted origin in Neon Auth.
