"""Railway runtime: headless Playwright Chromium running inside the Railway container.

Datacenter IP. No display. Used for low-anti-bot tasks.
"""
from __future__ import annotations

import asyncio
import base64
from typing import Literal

from .base import BrowserRuntime, RuntimeAction, RuntimeObservation, RuntimeError


class RailwayRuntime(BrowserRuntime):
    name = "railway"

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def start(self, *, mode: Literal["browser", "desktop"] = "browser") -> None:
        if mode == "desktop":
            raise RuntimeError("Desktop mode is not supported on Railway (no display).", recoverable=False)
        from playwright.async_api import async_playwright  # type: ignore
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        self._page = await self._context.new_page()

    async def execute(self, action: RuntimeAction) -> RuntimeObservation:
        if self._page is None:
            raise RuntimeError("Runtime not started", recoverable=False)
        page = self._page
        a = action.args
        try:
            if action.type == "goto":
                await page.goto(a["url"], wait_until=a.get("wait_until", "domcontentloaded"), timeout=30000)
            elif action.type == "click":
                if "selector" in a:
                    await page.click(a["selector"], timeout=10000)
                else:
                    await page.mouse.click(a["x"], a["y"])
            elif action.type == "type":
                if "selector" in a:
                    await page.fill(a["selector"], a["text"])
                else:
                    await page.keyboard.type(a["text"], delay=a.get("delay_ms", 30))
            elif action.type == "press":
                await page.keyboard.press(a["key"])
            elif action.type == "scroll":
                await page.mouse.wheel(0, a.get("dy", 400))
            elif action.type == "wait":
                await asyncio.sleep(a.get("seconds", 1))
            elif action.type == "extract_text":
                text = await page.inner_text(a.get("selector", "body"))
                return RuntimeObservation(text=text, url=page.url)
            elif action.type == "extract_dom":
                dom = await page.content()
                return RuntimeObservation(dom=dom, url=page.url)
            elif action.type == "set_cookies":
                await self._context.add_cookies(a["cookies"])  # type: ignore
            elif action.type == "screenshot":
                pass
            else:
                raise RuntimeError(f"Action {action.type} not supported on Railway", recoverable=False)

            png = await page.screenshot(full_page=False)
            return RuntimeObservation(
                screenshot_b64=base64.b64encode(png).decode(), url=page.url
            )
        except Exception as e:
            blocked = self._looks_blocked(str(e))
            raise RuntimeError(str(e), recoverable=blocked)

    async def stop(self) -> None:
        try:
            if self._context: await self._context.close()
            if self._browser: await self._browser.close()
            if self._playwright: await self._playwright.stop()
        except Exception:
            pass

    @staticmethod
    def _looks_blocked(msg: str) -> bool:
        m = msg.lower()
        return any(k in m for k in ["captcha", "cloudflare", "403", "429", "blocked", "detected"])
