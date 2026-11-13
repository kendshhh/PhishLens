# Issue #91 — saved real-AI browser acceptance

Task: S3-A2 / W3-D3-Andrei and W3-D5-Andrei  
Owner: Andrei (`JupitraxNeptuna`)  
Reviewer: Leyan (`inaki3023`); backup: Kendra (`kendshhh`)

## Local packaged-browser evidence

From the repository root, package the current checkout and run the packaged
browser acceptance:

```powershell
npm run package
npm run test:browser
```

The test unpacks the exact ZIP into a disposable browser profile, verifies the
package identity, and redirects only the temporary unpacked copy to a local
synthetic HTTP server. It creates no staging records and sends no text to a
provider. The result is written to `output/extension/browser-acceptance.json`;
screenshots are written to `output/extension/browser-evidence/` and uploaded
with the `Extension-Browser-Acceptance` CI artifact:

| Screenshot | Demonstrates |
|---|---|
| `01-synthetic-provider-backed-saved-report.png` | Returned classification, explanation, provider/model provenance and safe text rendering |
| `02-synthetic-provider-report-after-popup-reopen.png` | Returned report ID is present in server history and can be opened after reopening the popup |
| `03-synthetic-provider-failure-preserves-input.png` | Controlled HTTP 503 keeps the synthetic input, shows an error, and renders no verdict |
| `04-synthetic-history-refresh-failure-keeps-saved-report.png` | A confirmed create remains visible with truthful provider details while history refresh shows an error, not an empty state |

The evidence JSON records the source/package/browser identity, synthetic
record IDs, screenshot SHA-256 values and a redacted API method/path/status
summary. These browser fixtures use a synthetic provider-backed response and
controlled failures. They demonstrate the UI and client contract only; they do
not establish a real provider call, staging persistence, or independent review.

## Protected staging run

Do not start until Kendra or the environment owner confirms that the protected
staging service points to the isolated synthetic database and that the intended
real provider is configured. `/ready` alone does not confirm either item. Then
record the full package source SHA, extension version, inner ZIP SHA-256, Chrome
version, deployment identifier, staging `/version` SHA, and timestamp. Require
the ZIP source SHA and `/version` SHA to match; stop on mismatch or unhealthy
readiness. Record `/model-info` and the actual saved response provenance, but do
not infer a real provider from a healthy endpoint or a `real` label alone.

Using only a synthetic email, run the installed staging package through its
provider-backed analysis/save action. Confirm that the displayed classification
and explanation match the server response, then capture the returned report ID.
Reopen the popup (or reload the extension), refresh history, and open that same
ID. Capture redacted Network methods, paths, statuses and response fields; omit
credentials, cookies, authorization headers, personal data and email content.
Delete only the synthetic record created by this run, then verify a fresh detail
request returns 404 and refreshed history no longer contains it. Record cleanup
evidence separately from the saved-result evidence.

For controlled provider and history failures, arrange a test-only failure with
the backend owner or use the synthetic browser fixtures above. Do not alter a
shared provider key or turn off a shared staging provider. Keep any simulated
failure labeled as a substitute. Confirm input retention/no false verdict for
provider failure and saved-record retention/error messaging for history failure.

## Acceptance status

- [x] Reviewable packaged-browser UI and synthetic failure-state evidence are generated locally by `npm run test:browser`; CI is configured to upload the bundle on its next run.
- [ ] Exact-source installed-extension run against the owner-confirmed protected staging API.
- [ ] Real provider classification, explanation, provenance and server-returned ID verified in the installed extension.
- [ ] Saved record found after popup reopen/extension reload; synthetic record cleanup verified.
- [ ] Connected provider failure and history-refresh failure captured, or clearly marked synthetic substitutes accepted by reviewer.
- [ ] Redacted connected Network evidence and required teammate review recorded.

Do not describe the synthetic browser artifact as real-AI or staging acceptance.
Auth activation, local-Llama acceptance and model-quality evaluation are separate
limits and remain outside this task's evidence unless explicitly added by the
owners.
