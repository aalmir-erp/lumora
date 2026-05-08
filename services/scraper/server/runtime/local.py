"""Local runtime: server forwards actions over WebSocket to a local agent
running on the user's PC (controls user's Chrome and/or desktop).
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Literal

from .base import BrowserRuntime, RuntimeAction, RuntimeObservation, RuntimeError
from .agent_registry import AGENT_REGISTRY


class LocalRuntime(BrowserRuntime):
    name = "local"

    def __init__(self, agent_id: str | None = None) -> None:
        self._agent_id = agent_id
        self._agent = None
        self._mode: str = "browser"

    async def start(self, *, mode: Literal["browser", "desktop"] = "browser") -> None:
        self._mode = mode
        agent = AGENT_REGISTRY.pick(self._agent_id)
        if agent is None:
            raise RuntimeError(
                "No local agent connected. Start the local agent on your PC: "
                "`python -m local_agent.agent`",
                recoverable=False,
            )
        self._agent = agent
        await agent.send({"op": "start", "mode": mode})
        ack = await agent.recv(timeout=15)
        if ack.get("op") != "started":
            raise RuntimeError(f"Local agent failed to start: {ack}", recoverable=False)

    async def execute(self, action: RuntimeAction) -> RuntimeObservation:
        if self._agent is None:
            raise RuntimeError("Local runtime not started", recoverable=False)
        rid = str(uuid.uuid4())
        await self._agent.send({"op": "action", "id": rid, "type": action.type, "args": action.args})
        try:
            reply = await self._agent.recv(timeout=60)
        except asyncio.TimeoutError:
            raise RuntimeError("Local agent timeout", recoverable=True)
        if reply.get("op") == "error":
            raise RuntimeError(reply.get("message", "agent error"), recoverable=reply.get("recoverable", True))
        d = reply.get("data") or {}
        return RuntimeObservation(
            screenshot_b64=d.get("screenshot_b64"),
            text=d.get("text"),
            dom=d.get("dom"),
            data=d.get("data"),
            url=d.get("url"),
        )

    async def stop(self) -> None:
        if self._agent is not None:
            try:
                await self._agent.send({"op": "stop"})
            except Exception:
                pass
            self._agent = None
