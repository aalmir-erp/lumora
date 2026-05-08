from __future__ import annotations

from .base import BrowserRuntime
from .hybrid import HybridRuntime
from .local import LocalRuntime
from .railway import RailwayRuntime


def build_runtime(name: str, *, agent_id: str | None = None) -> BrowserRuntime:
    n = (name or "hybrid").lower()
    if n == "railway":
        return RailwayRuntime()
    if n == "local":
        return LocalRuntime(agent_id)
    return HybridRuntime(agent_id)
