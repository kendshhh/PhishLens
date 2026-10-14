from typing import Protocol

from backend.ai.schemas import AIAnalysisResult


class AIProvider(Protocol):
    def analyze(self, email_text: str) -> AIAnalysisResult: ...


class AIService:
    def __init__(
        self,
        provider: AIProvider,
    ) -> None:
        self.provider = provider

    def analyze_email(
        self,
        *,
        subject: str | None,
        sender: str | None,
        body: str,
    ) -> AIAnalysisResult:

        email_text = self._prepare_email(
            subject=subject,
            sender=sender,
            body=body,
        )

        return self.provider.analyze(email_text)

    @staticmethod
    def _prepare_email(
        *,
        subject: str | None,
        sender: str | None,
        body: str,
    ) -> str:

        return f"""
SUBJECT:
{subject or "(not supplied)"}

SENDER:
{sender or "(not supplied)"}

EMAIL BODY:
{body}
""".strip()