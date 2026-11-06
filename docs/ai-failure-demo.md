# Simulate an AI Provider Failure

This local demo sends a fixed synthetic request directly to the analysis-only
`POST /analyses` endpoint. It intentionally starts Gemini mode without a key
or model, so the backend returns a controlled `503` before making a provider
network call. No provider credential, production setting, extension change, or
database write is used.

## Setup

1. Install the backend dependencies using the
   [README setup instructions](../README.md#local-setup).
2. From the repository root in PowerShell, run:

   ```powershell
   .\scripts\demo_ai_failure.ps1
   ```

   The script temporarily sets process-local `AI_MODE=gemini` and blank Gemini
   key/model values, then starts the API on its local development address. It
   does not edit `.env` and restores the shell's prior environment values when
   the server exits.

## Demo

Keep the server running. In a second PowerShell window, submit the fixed
synthetic request:

```powershell
$payload = '{"subject":"Synthetic PhishLens provider smoke","sender":"smoke@example.invalid","text":"Synthetic test message only. Visit https://example.invalid/verify to confirm this fictional account. No real person or account is involved."}'
curl.exe -i -X POST http://127.0.0.1:8000/analyses -H "Content-Type: application/json" -H "Accept: application/json" --data-binary $payload
```

The expected response is HTTP `503` with this error body:

```json
{
  "error": {
    "code": "analysis_unavailable",
    "message": "Analysis temporarily unavailable"
  }
}
```

Stop the local server with `Ctrl+C`. This demonstrates the missing-provider-
configuration path and its safe unavailable response. It does not claim to
reproduce a provider network timeout or quota event, and it does not exercise
the extension UI. The `/analyses` endpoint does not persist a saved report.
For code-level regression coverage of provider errors, see
`backend/tests/test_ai_api.py`, `backend/tests/test_provider_error_contract.py`,
and the AI failure handling tests under `backend/tests/`.
