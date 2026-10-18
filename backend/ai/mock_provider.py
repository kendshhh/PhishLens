from backend.ai.schemas import AIAnalysisResult


class MockProvider:
    def analyze(self, _email_text: str) -> AIAnalysisResult:
        return AIAnalysisResult(
            classification="spam",
            tactics=["Mock analysis: AI_MODE=mock"],
            recommendations=[
                "Set AI_MODE=gemini and configure Gemini credentials for AI analysis."
            ],
        )
