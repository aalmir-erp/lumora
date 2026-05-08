"""Local agent: runs on the user's PC, connects to the Railway server over
WebSocket, and executes browser/desktop actions on behalf of the server.

Run from services/scraper/:
    python -m local_agent.agent

Required env (or .env in the working directory):
    SCRAPER_SERVER_URL   e.g. wss://lumora-scraper-production.up.railway.app
    LOCAL_AGENT_TOKEN    shared secret matching the server
    AGENT_ID             unique id for this PC (default: hostname)

Optional:
    AGENT_DRY_RUN=1      desktop actions wait for ENTER before executing
    CHROME_USER_DATA_DIR override Chrome profile path
"""
from __future__ import annotations

import asyncio
import json
import os
import platform
import socket
import sys
from typing import Any

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

import websockets

from .browser import LocalBrowser
from .safety import install_failsafes
from . import desktop as desktop_mod


def _server_url() -> str:
    base = os.getenv("SCRAPER_SERVER_URL", "ws://127.0.0.1:8000")
    if base.startswith("http"):
        base = base.replace("http", "ws", 1)
    token = os.getenv("LOCAL_AGENT_TOKEN", "")
    agent_id = os.getenv("AGENT_ID") or socket.gethostname()
    return f"{base}/ws/agent?token={token}&agent_id={agent_id}"


class Agent:
    def __init__(self) -> None:
        self.browser: LocalBrowser | None = None
        self.mode: str = "browser"

    async def handle(self, ws) -> None:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            op = msg.get("op")
            if op == "start":
                self.mode = msg.get("mode", "browser")
                if self.mode == "browser":
                    self.browser = LocalBrowser()
                    await self.browser.start()
                else:
                    install_failsafes()
                await ws.send(json.dumps({"op": "started", "mode": self.mode}))
            elif op == "action":
                rid = msg.get("id")
                try:
                    data = await self.execute(msg.get("type"), msg.get("args", {}))
                    await ws.send(json.dumps({"op": "result", "id": rid, "data": data}))
                except Exception as e:
                    await ws.send(json.dumps({"op": "error", "id": rid, "message": str(e), "recoverable": True}))
            elif op == "stop":
                if self.browser:
                    await self.browser.stop()
                    self.browser = None
                await ws.send(json.dumps({"op": "stopped"}))

    async def execute(self, action_type: str, args: dict[str, Any]) -> dict[str, Any]:
        if action_type and action_type.startswith("desktop_"):
            return await self._desktop(action_type, args)
        if action_type in ("excel_read", "excel_write"):
            return await self._excel(action_type, args)
        if self.browser is None:
            self.browser = LocalBrowser()
            await self.browser.start()
        return await self.browser.execute(action_type, args)

    async def _desktop(self, action_type: str, args: dict[str, Any]) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        if action_type == "desktop_screenshot":
            shot = await loop.run_in_executor(None, desktop_mod.screenshot_b64)
            return {"screenshot_b64": shot}
        if action_type == "desktop_click":
            await loop.run_in_executor(None, desktop_mod.click,
                                       int(args["x"]), int(args["y"]), args.get("button", "left"))
        elif action_type == "desktop_type":
            await loop.run_in_executor(None, desktop_mod.type_text, args["text"], int(args.get("delay_ms", 40)))
        elif action_type == "desktop_hotkey":
            await loop.run_in_executor(None, desktop_mod.hotkey, list(args["keys"]))
        else:
            raise RuntimeError(f"unsupported desktop action {action_type}")
        shot = await loop.run_in_executor(None, desktop_mod.screenshot_b64)
        return {"screenshot_b64": shot}

    async def _excel(self, action_type: str, args: dict[str, Any]) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        if action_type == "excel_read":
            data = await loop.run_in_executor(
                None, desktop_mod.excel_read,
                args["path"], args.get("sheet"), args.get("range"),
            )
            return {"data": data}
        else:
            res = await loop.run_in_executor(
                None, desktop_mod.excel_write,
                args["path"], args.get("sheet"), args.get("cells", {}),
            )
            return {"data": res}


async def main() -> None:
    agent = Agent()
    url = _server_url()
    print(f"[agent] connecting to {url.split('?')[0]} (id={os.getenv('AGENT_ID') or socket.gethostname()}, "
          f"os={platform.system()})")
    while True:
        try:
            async with websockets.connect(url, max_size=20 * 1024 * 1024) as ws:
                print("[agent] connected, waiting for tasks...")
                await agent.handle(ws)
        except Exception as e:
            print(f"[agent] disconnected ({e}); retrying in 5s", file=sys.stderr)
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
