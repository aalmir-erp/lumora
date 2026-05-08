"""Provider-agnostic AI interface.

Both Anthropic and OpenAI adapters implement `AIProvider.generate`.
The rest of the app talks only to this interface, so swapping providers
is a one-line config change.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ChatMessage:
    role: str  # "user" or "assistant"
    content: str


class AIProvider(Protocol):
    async def generate(
        self,
        system_prompt: str,
        history: list[ChatMessage],
    ) -> str:
        """Return the assistant's reply text for the given history.

        `history` ends with the latest user turn. The provider is
        expected to handle context window trimming if needed.
        """
        ...
