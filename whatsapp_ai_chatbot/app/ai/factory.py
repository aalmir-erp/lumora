"""Pick the configured AI provider — re-resolved each call so the admin
panel can switch providers without a redeploy."""
from __future__ import annotations

from .. import settings_store
from .base import AIProvider


def get_provider() -> AIProvider:
    provider = settings_store.ai_provider()
    if provider == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    if provider == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider()
    raise RuntimeError(f"Unknown AI_PROVIDER: {provider!r}")
