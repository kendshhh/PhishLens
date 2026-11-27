"""Error types shared by AI providers and the backend API."""


class AnalysisUnavailableError(RuntimeError):
    """The configured AI provider cannot currently accept analysis requests."""


class AIProviderTimeoutError(RuntimeError):
    """The provider request exceeded its network or upstream time limit."""


class ModelUnavailableError(AnalysisUnavailableError):
    """The configured local model cannot be used for inference."""
