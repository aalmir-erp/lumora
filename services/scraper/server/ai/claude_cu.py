"""Claude Sonnet 4.6 (Computer Use) backend.

Uses Anthropic's `computer_20250124` tool. We translate Claude's native action
space (key, type, mouse_move, left_click, screenshot) into our RuntimeAction
schema.
"""
from __future__ import annotations

import base64
from typing import Any

from .. import config
from ..runtime.base import RuntimeAction, RuntimeObservation
from ._prompt import SYSTEM_PROMPT
from .base import AIBackend, AIContext, AIPlan


class ClaudeComputerUseBackend(AIBackend):
    name = "claude-cu"

    def __init__(self, model_id: str = "claude-sonnet-4-6") -> None:
        self.model_id = model_id
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            import anthropic  # type: ignore
            if not config.ANTHROPIC_API_KEY:
                raise RuntimeError("ANTHROPIC_API_KEY not set")
            self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        return self._client

    async def next_step(self, ctx: AIContext, observation: RuntimeObservation) -> AIPlan:
        client = self._ensure_client()
        content: list[dict[str, Any]] = []
        if observation.screenshot_b64:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": observation.screenshot_b64},
            })
        content.append({"type": "text", "text": f"GOAL: {ctx.goal}\nMODE: {ctx.mode}\nURL: {observation.url or ''}"})

        import asyncio
        def _call():
            return client.messages.create(
                model=self.model_id,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=[{
                    "type": "computer_20250124",
                    "name": "computer",
                    "display_width_px": 1280,
                    "display_height_px": 800,
                    "display_number": 0,
                }],
                messages=[{"role": "user", "content": content}],
            )
        resp = await asyncio.get_running_loop().run_in_executor(None, _call)

        for block in resp.content:
            t = getattr(block, "type", None)
            if t == "tool_use" and block.name == "computer":
                return _translate_claude_action(block.input or {}, ctx.mode)
            if t == "text":
                txt = block.text or ""
                if "DONE" in txt.upper() or "FINAL" in txt.upper():
                    return AIPlan(done=True, reasoning=txt[:500], final_answer=txt)
        return AIPlan(done=True, reasoning="no tool_use returned")


def _translate_claude_action(inp: dict, mode: str) -> AIPlan:
    a = inp.get("action") or ""
    coord = inp.get("coordinate") or [0, 0]
    text = inp.get("text") or ""
    prefix = "desktop_" if mode == "desktop" else ""
    if a in ("screenshot",):
        return AIPlan(action=RuntimeAction(type=f"{prefix}screenshot" if mode == "desktop" else "screenshot"))
    if a == "left_click":
        return AIPlan(action=RuntimeAction(type=f"{prefix}click" if mode == "desktop" else "click",
                                           args={"x": coord[0], "y": coord[1]}))
    if a == "type":
        return AIPlan(action=RuntimeAction(type=f"{prefix}type" if mode == "desktop" else "type", args={"text": text}))
    if a == "key":
        if mode == "desktop":
            return AIPlan(action=RuntimeAction(type="desktop_hotkey", args={"keys": text.split("+")}))
        return AIPlan(action=RuntimeAction(type="press", args={"key": text}))
    if a == "mouse_move":
        return AIPlan(action=RuntimeAction(type="wait", args={"seconds": 0.1}))
    return AIPlan(done=True, reasoning=f"unsupported claude action: {a}")
