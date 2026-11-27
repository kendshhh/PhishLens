import json
from typing import Protocol

from pydantic import ValidationError

from backend.ai.schemas import AIAnalysisResult


class AIProvider(Protocol):
    def analyze(self, email_text: str) -> AIAnalysisResult: ...


class AIService:
    def __init__(
        self,
        provider: AIProvider,
    ) -> None:
        self.provider = provider

    def estimate_request(
        self,
        *,
        subject: str | None,
        sender: str | None,
        body: str,
    ):
        """Return a provider's conservative estimate without making a call."""
        estimator = getattr(self.provider, "estimate_request", None)
        if not callable(estimator):
            raise TypeError("The configured provider cannot estimate a request")
        if not body.strip() or len(body) > 30_000:
            raise ValueError("Email body must contain 1 to 30000 characters")
        if any(value is not None and len(value) > 320 for value in (subject, sender)):
            raise ValueError("Subject and sender must not exceed 320 characters")
        email_text = self._prepare_email(subject=subject, sender=sender, body=body)
        return estimator(email_text)

    def analyze_email(
        self,
        *,
        subject: str | None,
        sender: str | None,
        body: str,
    ) -> AIAnalysisResult:
        if not body.strip() or len(body) > 30_000:
            raise ValueError("Email body must contain 1 to 30000 characters")
        if any(value is not None and len(value) > 320 for value in (subject, sender)):
            raise ValueError("Subject and sender must not exceed 320 characters")
        email_text = self._prepare_email(
            subject=subject,
            sender=sender,
            body=body,
        )

        try:
            result = AIAnalysisResult.model_validate(self.provider.analyze(email_text))
        except ValidationError as exc:
            raise RuntimeError("The AI provider returned an invalid analysis.") from exc

        # A quote must occur in the actual email, not in our wrapper or instructions.
        sources = [" ".join(value.split()) for value in (subject, sender, body) if value]
        for item in result.evidence:
            if not any(" ".join(item.text.split()) in source for source in sources):
                raise RuntimeError("The AI provider returned unsupported evidence.")
        return result

    @staticmethod
    def _prepare_email(
        *,
        subject: str | None,
        sender: str | None,
        body: str,
    ) -> str:

        # JSON escaping keeps email text from forging subject/sender boundaries.
        return json.dumps({"subject": subject, "sender": sender, "body": body}, ensure_ascii=False)
