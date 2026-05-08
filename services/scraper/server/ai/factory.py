from __future__ import annotations

from .base import AIBackend
from .demo import DemoBackend
from .gemini import GeminiBackend
from .gemini_cu import GeminiComputerUseBackend
from .claude_cu import ClaudeComputerUseBackend


def build_backend(name: str) -> AIBackend:
    n = (name or "gemini-pro").lower()
    if n == "demo":
        return DemoBackend()
    if n == "gemini-pro":
        return GeminiBackend("gemini-2.5-pro", "gemini-pro")
    if n == "gemini-flash":
        return GeminiBackend("gemini-2.5-flash", "gemini-flash")
    if n == "gemini-cu":
        return GeminiComputerUseBackend()
    if n == "claude-cu":
        return ClaudeComputerUseBackend()
    raise ValueError(f"Unknown backend {name}")
