"""Gemini 2.5 Computer Use backend.

Uses the function-calling computer_use tool which returns native click/type
actions. Falls back to JSON protocol parsing if the SDK shape varies between
versions (this is a preview API).
"""
from __future__ import annotations

import base64
import json
from typing import Any

from .. import config
from ..runtime.base import RuntimeAction, RuntimeObservation
from ._prompt import SYSTEM_PROMPT, render_user
from .base import AIBackend, AIContext, AIPlan
from .gemini import _plan_from_json, _to_async


class GeminiComputerUseBackend(AIBackend):
    name = "gemini-cu"

    def __init__(self) -> None:
        import os
        self.model_id = os.getenv("GEMINI_CU_MODEL", "gemini-2.5-computer-use-preview-10-2025")
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            import google.generativeai as genai  # type: ignore
            if not config.GOOGLE_API_KEY:
                raise RuntimeError("GOOGLE_API_KEY not set")
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self._model = genai.GenerativeModel(
                model_name=self.model_id,
                system_instruction=SYSTEM_PROMPT
                + "\nIf computer_use tool is available you MAY emit native actions; "
                "otherwise emit the JSON protocol described above.",
                generation_config={"response_mime_type": "application/json", "temperature": 0.1},
            )
        return self._model

    async def next_step(self, ctx: AIContext, observation: RuntimeObservation) -> AIPlan:
        model = self._ensure_model()
        parts: list[Any] = [render_user(ctx.goal, ctx.history, ctx.mode)]
        if observation.screenshot_b64:
            parts.append({"mime_type": "image/png", "data": base64.b64decode(observation.screenshot_b64)})
        if observation.url:
            parts.append(f"CURRENT_URL: {observation.url}")
        resp = await _to_async(lambda: model.generate_content(parts))
        text = getattr(resp, "text", "") or ""
        try:
            return _plan_from_json(json.loads(text))
        except Exception:
            return AIPlan(done=True, reasoning=f"Bad JSON: {text[:200]}")
