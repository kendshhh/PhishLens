# Simulate an AI Provider Failure

This local demo uses the analysis-only `POST /analyses` endpoint and the
extension's normal error state. It intentionally starts Gemini mode without a
key or model, so the backend returns a controlled `503` before making a network
call. No provider credential, production setting, or database write is used.

## Setup

1. Install the backend dependencies and extension prerequisites using the
   [README setup instructions](../README.md#local-setup).
2. Point `extension/js/config.js` to `http://127.0.0.1:8000` and add
   `http://127.0.0.1:8000/*` to `host_permissions` in `extension/manifest.json`.
   These are the same local-origin steps used for ordinary development.
3. Load or reload the unpacked `extension/` folder in Chrome.
4. From the repository root in PowerShell, run:

   ```powershell
   .\scripts\demo_ai_failure.ps1
   ```

   The script temporarily sets process-local `AI_MODE=gemini` and blank Gemini
   key/model values. It does not edit `.env` and restores the shell's prior
   environment values when the server exits.

## Demo

Highlight synthetic email text and choose **Analyze selection with VeriQo**.
The extension should show the unavailable state and message
`Analysis temporarily unavailable`. A direct request returns:

```json
{
  "error": {
    "code": "analysis_unavailable",
    "message": "Analysis temporarily unavailable"
  }
}
```

Stop the local server with `Ctrl+C`. The demo exercises missing provider
configuration, which follows the same safe unavailable response as a provider
outage. It does not claim to reproduce a Gemini network timeout or quota event.
It uses `/analyses`, which does not persist a saved report. For code-level
regression coverage of provider errors, see `backend/tests/test_ai_api.py`,
`backend/tests/test_provider_error_contract.py`, and the AI failure handling
tests under `backend/tests/`.

After the demo, restore the extension API origin and manifest host permission to
the target you intend to use, then reload the extension. The failure script
restores process environment variables when the server exits; it does not edit
extension files.