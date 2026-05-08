"""Hybrid runtime: try Railway first, auto-fallback to local agent on block/captcha.

Hosts in FORCE_LOCAL_HOSTS always go local from the start (e.g. web.whatsapp.com).
Desktop mode is always local (Railway has no display).
"""
from __future__ import annotations

import fnmatch
from typing import Literal
from urllib.parse import urlparse

from .. import config
from .base import BrowserRuntime, RuntimeAction, RuntimeObservation, RuntimeError
from .local import LocalRuntime
from .railway import RailwayRuntime


def _force_local(url: str | None) -> bool:
    if not url:
        return False
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return False
    return any(fnmatch.fnmatch(host, p) for p in config.FORCE_LOCAL_HOSTS)


class HybridRuntime(BrowserRuntime):
    name = "hybrid"

    def __init__(self, agent_id: str | None = None) -> None:
        self._railway: RailwayRuntime | None = None
        self._local: LocalRuntime | None = None
        self._active: BrowserRuntime | None = None
        self._mode: str = "browser"
        self._agent_id = agent_id

    async def start(self, *, mode: Literal["browser", "desktop"] = "browser") -> None:
        self._mode = mode
        if mode == "desktop":
            self._local = LocalRuntime(self._agent_id)
            await self._local.start(mode="desktop")
            self._active = self._local
            return
        try:
            self._railway = RailwayRuntime()
            await self._railway.start(mode="browser")
            self._active = self._railway
        except Exception:
            self._railway = None
            self._local = LocalRuntime(self._agent_id)
            await self._local.start(mode="browser")
            self._active = self._local

    async def execute(self, action: RuntimeAction) -> RuntimeObservation:
        assert self._active is not None
        if action.type == "goto" and self._active is self._railway and _force_local(action.args.get("url")):
            await self._switch_to_local()
        try:
            return await self._active.execute(action)
        except RuntimeError as e:
            if e.recoverable and self._active is self._railway:
                await self._switch_to_local()
                return await self._active.execute(action)
            raise

    async def _switch_to_local(self) -> None:
        if self._railway is not None:
            await self._railway.stop()
            self._railway = None
        self._local = LocalRuntime(self._agent_id)
        await self._local.start(mode=self._mode)  # type: ignore
        self._active = self._local

    async def stop(self) -> None:
        if self._railway: await self._railway.stop()
        if self._local: await self._local.stop()

    @property
    def active_runtime(self) -> str:
        return self._active.name if self._active else "none"
