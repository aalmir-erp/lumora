"""Local browser controller — Playwright launching the user's real Chrome
profile so cookies and session persist between runs.

Profile path defaults are platform-specific. Override with CHROME_USER_DATA_DIR.
"""
from __future__ import annotations

import asyncio
import base64
import os
import platform
from typing import Any


def default_chrome_profile_dir() -> str:
    override = os.getenv("CHROME_USER_DATA_DIR")
    if override:
        return override
    p = platform.system().lower()
    home = os.path.expanduser("~")
    if p == "windows":
        return os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data")
    if p == "darwin":
        return os.path.join(home, "Library", "Application Support", "Google", "Chrome")
    return os.path.join(home, ".config", "google-chrome")


class LocalBrowser:
    def __init__(self) -> None:
        self._pw = None
        self._ctx = None
        self._page = None

    async def start(self) -> None:
        from playwright.async_api import async_playwright  # type: ignore
        self._pw = await async_playwright().start()
        profile = default_chrome_profile_dir()
        self._ctx = await self._pw.chromium.launch_persistent_context(
            user_data_dir=profile,
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800},
        )
        self._page = self._ctx.pages[0] if self._ctx.pages else await self._ctx.new_page()

    async def execute(self, action_type: str, args: dict[str, Any]) -> dict[str, Any]:
        page = self._page
        if page is None:
            raise RuntimeError("browser not started")
        if action_type == "goto":
            await page.goto(args["url"], wait_until=args.get("wait_until", "domcontentloaded"), timeout=30000)
        elif action_type == "click":
            if "selector" in args:
                await page.click(args["selector"], timeout=10000)
            else:
                await page.mouse.click(args["x"], args["y"])
        elif action_type == "type":
            if "selector" in args:
                await page.fill(args["selector"], args["text"])
            else:
                await page.keyboard.type(args["text"], delay=args.get("delay_ms", 40))
        elif action_type == "press":
            await page.keyboard.press(args["key"])
        elif action_type == "scroll":
            await page.mouse.wheel(0, args.get("dy", 400))
        elif action_type == "wait":
            await asyncio.sleep(args.get("seconds", 1))
        elif action_type == "extract_text":
            text = await page.inner_text(args.get("selector", "body"))
            png = await page.screenshot(full_page=False)
            return {"text": text, "url": page.url, "screenshot_b64": base64.b64encode(png).decode()}
        elif action_type == "extract_dom":
            dom = await page.content()
            png = await page.screenshot(full_page=False)
            return {"dom": dom, "url": page.url, "screenshot_b64": base64.b64encode(png).decode()}
        elif action_type == "set_cookies":
            await self._ctx.add_cookies(args["cookies"])  # type: ignore
        elif action_type == "screenshot":
            pass
        else:
            raise RuntimeError(f"unsupported action {action_type}")

        png = await page.screenshot(full_page=False)
        return {"screenshot_b64": base64.b64encode(png).decode(), "url": page.url}

    async def stop(self) -> None:
        try:
            if self._ctx: await self._ctx.close()
            if self._pw: await self._pw.stop()
        except Exception:
            pass
