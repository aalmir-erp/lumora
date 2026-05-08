"""Per-user conversation history.

Default backend is an in-process dict, which is fine for a single
worker. If `REDIS_URL` is set, history is persisted in Redis so
multiple workers / restarts don't lose context.
"""
from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Protocol

from .config import settings


@dataclass
class Turn:
    role: str  # "user" or "assistant"
    content: str
    ts: float


class ConversationStore(Protocol):
    async def append(self, wa_id: str, turn: Turn) -> None: ...
    async def history(self, wa_id: str) -> list[Turn]: ...
    async def clear(self, wa_id: str) -> None: ...


class InMemoryStore:
    def __init__(self, max_turns: int) -> None:
        self._max = max_turns
        self._data: dict[str, Deque[Turn]] = {}

    async def append(self, wa_id: str, turn: Turn) -> None:
        dq = self._data.setdefault(wa_id, deque(maxlen=self._max * 2))
        dq.append(turn)

    async def history(self, wa_id: str) -> list[Turn]:
        return list(self._data.get(wa_id, ()))

    async def clear(self, wa_id: str) -> None:
        self._data.pop(wa_id, None)


class RedisStore:
    """Redis-backed store. Each user's history is a capped LIST."""

    def __init__(self, url: str, max_turns: int) -> None:
        # Lazy import so the dependency is optional.
        import redis.asyncio as redis  # type: ignore[import-not-found]

        self._r = redis.from_url(url, decode_responses=True)
        self._max = max_turns

    def _key(self, wa_id: str) -> str:
        return f"wa:hist:{wa_id}"

    async def append(self, wa_id: str, turn: Turn) -> None:
        key = self._key(wa_id)
        payload = json.dumps({"role": turn.role, "content": turn.content, "ts": turn.ts})
        async with self._r.pipeline() as pipe:
            await pipe.rpush(key, payload)
            await pipe.ltrim(key, -self._max * 2, -1)
            await pipe.expire(key, 60 * 60 * 24 * 7)  # 7-day TTL
            await pipe.execute()

    async def history(self, wa_id: str) -> list[Turn]:
        items = await self._r.lrange(self._key(wa_id), 0, -1)
        out: list[Turn] = []
        for raw in items:
            try:
                d = json.loads(raw)
                out.append(Turn(role=d["role"], content=d["content"], ts=d.get("ts", 0)))
            except (ValueError, KeyError):
                continue
        return out

    async def clear(self, wa_id: str) -> None:
        await self._r.delete(self._key(wa_id))


def make_store() -> ConversationStore:
    if settings.redis_url:
        try:
            return RedisStore(settings.redis_url, settings.history_turns)
        except ImportError:
            # `redis` package not installed — fall back to in-memory.
            pass
    return InMemoryStore(settings.history_turns)


async def record_user_and_history(
    store: ConversationStore, wa_id: str, user_text: str
) -> list[Turn]:
    """Append the user's new turn and return the full history slice."""
    await store.append(wa_id, Turn(role="user", content=user_text, ts=time.time()))
    return await store.history(wa_id)


async def record_assistant(store: ConversationStore, wa_id: str, reply: str) -> None:
    await store.append(wa_id, Turn(role="assistant", content=reply, ts=time.time()))
