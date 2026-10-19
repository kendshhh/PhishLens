import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)


api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL")


print("=== PhishLens Gemini Connection Test ===")
print()


if not ENV_PATH.exists():
    print("ERROR: .env file not found.")
    print(f"Expected: {ENV_PATH}")
    raise SystemExit(1)


if not api_key:
    print("ERROR: GEMINI_API_KEY is missing.")
    raise SystemExit(1)


if not model:
    print("ERROR: GEMINI_MODEL is missing.")
    raise SystemExit(1)


print("Environment file: FOUND")
print("API key loaded: YES")
print(f"Model: {model}")
print()
print("Sending one request to Gemini...")


client = genai.Client(
    api_key=api_key
)


try:
    response = client.models.generate_content(
        model=model,
        contents=(
            "This is a backend connectivity test "
            "for PhishLens. Reply with exactly: "
            "PHISHLENS_GEMINI_OK"
        ),
    )

except errors.ClientError as exc:
    print()
    print("Gemini request: FAIL")
    print("Client/API configuration error.")
    print()
    print(exc)

    raise SystemExit(1)

except errors.ServerError as exc:
    print()
    print("Gemini request: TEMPORARILY UNAVAILABLE")
    print()
    print(
        "Authentication reached Gemini, but the "
        "provider could not complete the request."
    )
    print()
    print(exc)

    raise SystemExit(2)

except Exception as exc:
    print()
    print("Gemini request: FAIL")
    print(
        f"{type(exc).__name__}: {exc}"
    )

    raise SystemExit(1)


if not response.text:
    print()
    print("Gemini request: FAIL")
    print("Gemini returned an empty response.")
    raise SystemExit(1)


print()
print("Gemini request: PASS")
print("Response received: PASS")
print()
print("Gemini response:")
print(response.text.strip())
print()
print("=== CONNECTION TEST PASSED ===")