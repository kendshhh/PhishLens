"""Error types shared by AI providers and the backend API."""

class ModelUnavailableError(RuntimeError):
    """The configured local model cannot be used for inference."""
