"""Anthropic Claude provider with prompt caching on the system block."""
from __future__ import annotations

import logging

from anthropic import AsyncAnthropic

from ..config import settings
from .base import AIProvider, ChatMessage

log = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(self, system_prompt: str, history: list[ChatMessage]) -> str:
        # System prompt + KB are large and stable — mark them cacheable.
        # Cached prefixes give a ~10x cost reduction on repeat hits and
        # are a no-op the first time.
        system_blocks = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        messages = [{"role": m.role, "content": m.content} for m in history]

        resp = await self._client.messages.create(
            model=settings.anthropic_model,
            max_tokens=settings.anthropic_max_tokens,
            system=system_blocks,
            messages=messages,
        )
        # Concatenate any text blocks the model returned.
        parts: list[str] = []
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "".join(parts).strip()
