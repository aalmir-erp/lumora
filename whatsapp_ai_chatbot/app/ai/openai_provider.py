"""OpenAI GPT provider."""
from __future__ import annotations

import logging

from openai import AsyncOpenAI

from ..config import settings
from .base import AIProvider, ChatMessage

log = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate(self, system_prompt: str, history: list[ChatMessage]) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend({"role": m.role, "content": m.content} for m in history)

        resp = await self._client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=settings.openai_max_tokens,
            messages=messages,
        )
        return (resp.choices[0].message.content or "").strip()
