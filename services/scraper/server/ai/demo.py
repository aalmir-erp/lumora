"""Demo backend — works WITHOUT any API keys. Emits a small scripted plan
based on simple keyword routing in the goal. Useful to:

  1. Verify the UI/server/runtime plumbing right after a Railway deploy,
     before you've pasted GOOGLE_API_KEY / ANTHROPIC_API_KEY.
  2. Smoke-test the local agent without burning model tokens.

It is NOT intelligent. It can: open a URL, screenshot, scroll once, extract
text, and stop. That's enough to prove the loop.
"""
from __future__ import annotations

import re

from ..runtime.base import RuntimeAction, RuntimeObservation
from .base import AIBackend, AIContext, AIPlan


URL_RE = re.compile(r"https?://\S+")


class DemoBackend(AIBackend):
    name = "demo"

    async def next_step(self, ctx: AIContext, observation: RuntimeObservation) -> AIPlan:
        step = len(ctx.history)
        urls = URL_RE.findall(ctx.goal)
        target = urls[0].rstrip(".,)") if urls else "https://example.com"

        if step == 0:
            return AIPlan(action=RuntimeAction(type="goto", args={"url": target}),
                          reasoning=f"demo: navigate to {target}")
        if step == 1:
            return AIPlan(action=RuntimeAction(type="wait", args={"seconds": 2}),
                          reasoning="demo: let page settle")
        if step == 2:
            return AIPlan(action=RuntimeAction(type="extract_text", args={"selector": "body"}),
                          reasoning="demo: grab body text")
        snippet = (observation.text or "")[:240]
        return AIPlan(done=True, final_answer=snippet, reasoning="demo: returning page text snippet")
