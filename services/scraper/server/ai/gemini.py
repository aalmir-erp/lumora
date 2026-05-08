"""Gemini 2.5 Pro / Flash backend. Uses vision + JSON action protocol."""
from __future__ import annotations

import base64
import json
from typing import Any

from .. import config
from ..runtime.base import RuntimeAction, RuntimeObservation
from ._prompt import SYSTEM_PROMPT, render_user
from .base import AIBackend, AIContext, AIPlan


class GeminiBackend(AIBackend):
    def __init__(self, model_id: str, name: str) -> None:
        self.model_id = model_id
        self.name = name
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            import google.generativeai as genai  # type: ignore
            if not config.GOOGLE_API_KEY:
                raise RuntimeError("GOOGLE_API_KEY not set")
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self._model = genai.GenerativeModel(
                model_name=self.model_id,
                system_instruction=SYSTEM_PROMPT,
                generation_config={"response_mime_type": "application/json", "temperature": 0.2},
            )
        return self._model

    async def next_step(self, ctx: AIContext, observation: RuntimeObservation) -> AIPlan:
        model = self._ensure_model()
        parts: list[Any] = [render_user(ctx.goal, ctx.history, ctx.mode)]
        if observation.screenshot_b64:
            parts.append({
                "mime_type": "image/png",
                "data": base64.b64decode(observation.screenshot_b64),
            })
        if observation.text:
            parts.append(f"PAGE_TEXT_EXCERPT: {observation.text[:4000]}")
        if observation.url:
            parts.append(f"CURRENT_URL: {observation.url}")
        resp = await _to_async(lambda: model.generate_content(parts))
        try:
            plan = json.loads(resp.text)
        except Exception:
            return AIPlan(done=True, reasoning=f"Bad JSON from model: {resp.text[:200]}")
        return _plan_from_json(plan)


def _plan_from_json(plan: dict) -> AIPlan:
    if plan.get("done"):
        return AIPlan(done=True, final_answer=plan.get("answer"), reasoning=plan.get("reasoning", ""))
    action_name = plan.get("action")
    if not action_name:
        return AIPlan(done=True, reasoning="no action returned")
    args = {k: v for k, v in plan.items() if k != "action"}
    return AIPlan(action=RuntimeAction(type=action_name, args=args), reasoning=plan.get("reasoning", ""))


async def _to_async(fn):
    import asyncio
    return await asyncio.get_running_loop().run_in_executor(None, fn)
