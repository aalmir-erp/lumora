"""OpenAI GPT provider."""
from __future__ import annotations

import logging

from openai import AsyncOpenAI

from .. import settings_store
from .base import AIProvider, ChatMessage

log = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        key = settings_store.openai_api_key()
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self._client = AsyncOpenAI(api_key=key)

    async def generate(self, system_prompt: str, history: list[ChatMessage]) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend({"role": m.role, "content": m.content} for m in history)

        from ..config import settings as env_settings

        resp = await self._client.chat.completions.create(
            model=settings_store.openai_model() or env_settings.openai_model,
            max_tokens=env_settings.openai_max_tokens,
            messages=messages,
        )
        return (resp.choices[0].message.content or "").strip()
