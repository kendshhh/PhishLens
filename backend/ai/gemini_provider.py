from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from backend.ai.prompts import SYSTEM_INSTRUCTION
from backend.ai.schemas import AIAnalysisResult


class GeminiProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ) -> None:
        self.client = genai.Client(
            api_key=api_key
        )
        self.model = model

    def analyze(
        self,
        email_text: str,
    ) -> AIAnalysisResult:

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=email_text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=AIAnalysisResult,
                    temperature=0.1,
                ),
            )
        except errors.APIError as exc:
            if exc.code in {429, 500, 502, 503, 504}:
                message = (
                    f"Gemini is temporarily unavailable (HTTP {exc.code}). "
                    "Please try again."
                )
            elif exc.code in {401, 403}:
                message = (
                    f"Gemini rejected the API credentials (HTTP {exc.code}). "
                    "Check GEMINI_API_KEY."
                )
            elif exc.code == 404:
                message = (
                    "The configured Gemini model is unavailable (HTTP 404). "
                    "Check GEMINI_MODEL and model access."
                )
            else:
                message = f"Gemini request failed (HTTP {exc.code})."
            raise RuntimeError(message) from exc

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        try:
            return AIAnalysisResult.model_validate_json(response.text)
        except ValidationError as exc:
            raise RuntimeError("Gemini returned an invalid analysis response.") from exc