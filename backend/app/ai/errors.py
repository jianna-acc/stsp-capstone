# File: /backend/app/ai/errors.py
# Purpose: Defines safe provider-independent exceptions for AI
# configuration, requests, and provider responses.


class AIProviderError(RuntimeError):
    """Base exception for controlled AI provider failures."""


class AIProviderConfigurationError(AIProviderError):
    """Raised when an AI provider is missing required configuration."""


class AIProviderRequestError(AIProviderError):
    """Raised when the external provider rejects or fails a request."""


class AIProviderResponseError(AIProviderError):
    """Raised when the provider returns an unusable response."""
