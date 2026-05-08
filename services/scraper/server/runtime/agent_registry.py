"""Tracks connected local agents and routes WebSocket messages by request id."""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket


class ConnectedAgent:
    def __init__(self, agent_id: str, ws: WebSocket) -> None:
        self.agent_id = agent_id
        self.ws = ws
        self._inbox: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._closed = False

    async def send(self, msg: dict[str, Any]) -> None:
        await self.ws.send_json(msg)

    async def recv(self, timeout: float = 60.0) -> dict[str, Any]:
        return await asyncio.wait_for(self._inbox.get(), timeout=timeout)

    async def push(self, msg: dict[str, Any]) -> None:
        await self._inbox.put(msg)

    def close(self) -> None:
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, ConnectedAgent] = {}
        self._lock = asyncio.Lock()

    async def register(self, agent_id: str, ws: WebSocket) -> ConnectedAgent:
        async with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].close()
            agent = ConnectedAgent(agent_id, ws)
            self._agents[agent_id] = agent
            return agent

    async def unregister(self, agent_id: str) -> None:
        async with self._lock:
            self._agents.pop(agent_id, None)

    def pick(self, agent_id: str | None = None) -> ConnectedAgent | None:
        if agent_id and agent_id in self._agents:
            return self._agents[agent_id]
        for a in self._agents.values():
            if not a.closed:
                return a
        return None

    def list_agents(self) -> list[str]:
        return [a for a, v in self._agents.items() if not v.closed]


AGENT_REGISTRY = AgentRegistry()
