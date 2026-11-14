# PhishLens clean install and presenter demo

This run sheet installs the identified extension package in a clean Chrome
profile and demonstrates the local, uncertainty-safe analysis path. It uses only
the synthetic message below. It does not sign in, save a report, contact the
configured API, or claim staging or production acceptance.

## Exact demo candidate

| Item | Value |
|---|---|
| Source revision used to build the package | `e6d0fd01fb7e74587c20bc420e16c453ad5f7ef8` |
| Extension version | `0.1.0` |
| Package | `PhishLens-Extension.zip` |
| Package SHA-256 | `db8f2cbdf2b9c340a76123b13515f6de06a3ea3da3e930e01d4555b1e5c560de` |
| Package identity and per-file hashes | [demo-package-identity.json](demo-package-identity.json) |
| Browser used for the attached installed-flow captures | Google Chrome `157.0.8103.79`, Windows 11 |
| Environment | Local Chrome, extension loaded unpacked, signed out; no API requests in the capture |
| Model state in attached capture | Local LLM weights absent; expected visible outcome is **Uncertain**, never a safe verdict |

The archive was built from the public repository revision above. It omits about
1.1 GB of optional local LLM weights. The archive SHA identifies the exact local
build exercised here; ZIP timestamps can make a rebuild's archive SHA differ, so
compare the per-file hashes in the sidecar. The screenshots are from the matching
extension runtime files; this is recorded in [demo-evidence.json](demo-evidence.json).
After this PR's Extension checks pass, presenters can download the
`PhishLens-Extension` artifact from its Actions run and compare its sidecar file
hashes with [the package identity](demo-package-identity.json). That CI artifact
is retained for seven days. No Web Store listing or hosted extension preview is
available. The Vercel site is a separate information page, not an extension host.

## Prepare a clean install

1. Install Google Chrome 127 or later. The screenshots use Chrome 157.0.8103.79.
2. Download and extract the `PhishLens-Extension` ZIP from the successful
   Extension job on this PR's GitHub Actions run. Keep the extracted folder in
   place. Confirm its `evidence.json` names the PR's source commit and compare
   the listed extension file hashes to
   [the recorded package identity](demo-package-identity.json). Alternatively,
   clone the repository, check out source revision
   `e6d0fd01fb7e74587c20bc420e16c453ad5f7ef8`, then run `npm ci` and
   `npm run package`. The archive SHA is timestamp-sensitive; the sidecar's
   per-file hashes are the build identity.
3. For the attached no-weights demo, do not run the model download command. If a
   full local review is intended instead, run
   `npm run phishlens -- setup-models --download` before packaging. It downloads
   and verifies roughly 1.1 GB; full review also requires WebGPU `shader-f16`.
   That produces a different package identity and must be recorded separately.
4. Open `chrome://extensions`, enable **Developer mode**, select **Load
   unpacked**, and choose the package's extracted `extension` directory. Remove
   other PhishLens copies from this demo profile to avoid opening the wrong build.
5. Pin PhishLens. Its toolbar action opens the side panel. The right-click action
   opens the analysis popup for the selected text.

## Presenter run sheet

Use a blank tab or a local text file containing only this synthetic message:

> Subject: Urgent account review
> Your account will be closed today. Review it at `https://example.invalid` and
> enter your password to keep access.

1. Select the synthetic message and open the context menu. Choose **Analyze
   selection with PhishLens**. The original text appears in the action popup and
   local analysis begins. The right-click menu is the primary flow.
2. Explain that analysis runs in Chrome. In this identified package the local
   LLM weights are intentionally absent, so the expected result is **Uncertain**;
   the extension does not present that as safe. This is a limitation-state demo,
   not a claim about model accuracy.
3. Click the pinned toolbar icon to show the persistent side panel. Point out
   that the toolbar and right-click entry have different surfaces: toolbar opens
   the side panel, while right-click opens the action popup.
4. Use **Clear local scan** before ending. Stay signed out and do not use
   **Analyze and save on the server**, refresh shared reports, or enter real
   message content. Those are separate API interactions and are outside this
   local-only demo.

### Keyboard-accessible alternative

1. Open the pinned toolbar action and move through the side-panel controls with
   **Tab** / **Shift+Tab**; use **Enter** or **Space** to activate controls.
2. Expand **Or paste email text**, focus the labeled **Email text** field, and
   paste the same synthetic message. Tab to **Check this email** and press
   **Enter**.
3. Review the announced result/status. Focus indicators remain visible. Use
   **Clear local scan** when finished. The same explicit **Uncertain** state is
   expected while weights are absent.

No screen-reader result is claimed. Labels, focus order, and visible focus were
checked in Chrome; see the linked audit and evidence for scope.

## Actual screenshots and evidence

The screenshots are actual Chrome captures, rather than website mockups. They
were captured from revision `7301b953`; their extension runtime files match the
identified package's file hashes. The only file-level difference is the
manifest's line endings; its parsed permissions, version, and behavior settings
match the package:

| Step | Expected | Observed |
|---|---|---|
| [Toolbar opens side panel](../issue-131/manual-chrome-157/01-toolbar-opens-side-panel.png) | Pinned toolbar action opens PhishLens in the side panel | Side panel opened in its ready state; no popup appeared. |
| [Right-click action](../issue-131/manual-chrome-157/02-right-click-analyze-selection-menu.png) | Selected text offers the PhishLens analysis action | Chrome context menu showed **Analyze selection with PhishLens**. |
| [Local result](../issue-131/manual-chrome-157/03-right-click-result-uncertain.png) | Incomplete review is visibly uncertain | The selected synthetic message appeared with **Uncertain — check before acting** because weights were absent. |

For captured screenshot hashes, exact source/package identity, permissions,
expected-versus-observed details, and automated clean-profile checks, see
[demo-evidence.json](demo-evidence.json), [the package identity](demo-package-identity.json),
and [the installed-browser audit](../issue-131/audit.md). The automated checks
used synthetic fixtures; their results are separate from this manual Chrome
capture.

## Environment and model labels

- **Attached run:** local Chrome extension, production API origin configured in
  the package but not contacted; no authenticated account; no remote requests;
  model weights absent; uncertainty shown.
- **Optional full local run:** local Chrome extension plus verified downloaded
  model assets and WebGPU `shader-f16`; still local analysis. Do not describe this
  as staging or hosted-model analysis.
- **Staging or production:** not part of this guide or its attached evidence.
  Use only a separately approved candidate, demo identity, and target for any
  hosted demonstration.
- The browser cannot validate sender identity or whether links/attachments are
  safe. Treat the assessment as a second opinion, not a guarantee.
