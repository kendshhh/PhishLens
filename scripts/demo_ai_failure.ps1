$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Create the repository virtual environment and install requirements.txt first."
}

$names = @("AI_MODE", "GEMINI_API_KEY", "GEMINI_MODEL")
$previous = @{}
foreach ($name in $names) {
    $previous[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

try {
    $env:AI_MODE = "gemini"
    # Keep these variables present in Windows PowerShell 5.1, where assigning
    # an empty string removes them and can let python-dotenv reload a .env key.
    # The backend trims whitespace, so both values remain effectively unset.
    $env:GEMINI_API_KEY = " "
    $env:GEMINI_MODEL = " "
    Write-Host "Starting local PhishLens API with Gemini credentials intentionally unset."
    Write-Host "POST /analyses will return a controlled 503 without contacting Gemini."
    Write-Host "Press Ctrl+C to stop the server."
    & $python -m uvicorn backend.app.main:app --loop backend.core.event_loop:new_event_loop
}
finally {
    foreach ($name in $names) {
        [Environment]::SetEnvironmentVariable($name, $previous[$name], "Process")
    }
}
