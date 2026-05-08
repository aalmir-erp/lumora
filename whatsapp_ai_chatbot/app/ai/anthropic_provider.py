"""Anthropic Claude provider with prompt caching on the system block."""
from __future__ import annotations

import logging

from anthropic import AsyncAnthropic

from .. import settings_store
from .base import AIProvider, ChatMessage

log = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    def __init__(self) -> None:
        key = settings_store.anthropic_api_key()
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self._client = AsyncAnthropic(api_key=key)

    async def generate(self, system_prompt: str, history: list[ChatMessage]) -> str:
        # System prompt + KB are stable — mark cacheable so repeat hits
        # are ~10x cheaper and faster.
        system_blocks = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        messages = [{"role": m.role, "content": m.content} for m in history]

        from ..config import settings as env_settings

        resp = await self._client.messages.create(
            model=settings_store.anthropic_model() or env_settings.anthropic_model,
            max_tokens=env_settings.anthropic_max_tokens,
            system=system_blocks,
            messages=messages,
        )
        parts: list[str] = []
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "".join(parts).strip()
