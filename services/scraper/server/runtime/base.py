from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Literal

ActionType = Literal[
    "goto", "click", "type", "press", "scroll", "screenshot",
    "wait", "extract_text", "extract_dom", "set_cookies",
    "desktop_screenshot", "desktop_click", "desktop_type", "desktop_hotkey",
    "excel_read", "excel_write",
]


@dataclass
class RuntimeAction:
    type: ActionType
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeObservation:
    screenshot_b64: str | None = None
    text: str | None = None
    dom: str | None = None
    data: Any = None
    url: str | None = None
    error: str | None = None


class RuntimeError(Exception):
    """Raised when the runtime detects a hard failure (block, captcha, network)."""

    def __init__(self, message: str, *, recoverable: bool = True):
        super().__init__(message)
        self.recoverable = recoverable


class BrowserRuntime(abc.ABC):
    """Abstract runtime that executes actions and returns observations."""

    name: str = "abstract"

    @abc.abstractmethod
    async def start(self, *, mode: Literal["browser", "desktop"] = "browser") -> None: ...

    @abc.abstractmethod
    async def execute(self, action: RuntimeAction) -> RuntimeObservation: ...

    @abc.abstractmethod
    async def stop(self) -> None: ...
