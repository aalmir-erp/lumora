"""Pick the configured AI provider."""
from __future__ import annotations

from functools import lru_cache

from ..config import settings
from .base import AIProvider


@lru_cache(maxsize=1)
def get_provider() -> AIProvider:
    if settings.ai_provider == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    if settings.ai_provider == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider()
    raise RuntimeError(f"Unknown AI_PROVIDER: {settings.ai_provider!r}")
