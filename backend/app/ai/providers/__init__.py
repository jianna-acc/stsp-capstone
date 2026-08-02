# File: /backend/app/ai/providers/__init__.py
# Purpose: Exposes concrete AI provider implementations used by
# backend services.

from app.ai.providers.gemini import GeminiProvider

__all__ = [
    "GeminiProvider",
]
