from __future__ import annotations


class AIError(RuntimeError):
    """Base class for provider-agnostic AI integration errors."""


class AIConfigurationError(ValueError, AIError):
    """Raised when provider credentials or config are missing/invalid."""


class AISummarizationError(AIError):
    """Raised when provider summarization fails."""
