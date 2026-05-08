"""End-to-end scenarios for sale.mir.ae/demo + web.whatsapp.com OTP retrieval.

These scenarios call the running scraper API (not the AI/runtime directly),
so they exercise the full stack: server -> backend -> runtime -> agent.

Run after deploying the scraper and starting the local agent:
    SCRAPER_URL=https://lumora-scraper-production.up.railway.app \
        python -m tests.scenarios.mir_demo

Each scenario:
    1. POSTs a task to /api/tasks
    2. Streams events
    3. Saves screenshots into ./out/<scenario>/
    4. Posts a result summary to STATUS_WEBHOOK_URL (if set on the server)
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import pathlib
import sys
import time

import httpx


SCRAPER_URL = os.getenv("SCRAPER_URL", "http://127.0.0.1:8000")


SCENARIOS = {
    "smoke_demo": {
        "goal": "Visit https://sale.mir.ae/demo, take a screenshot of the landing page, "
                "then summarise the visible content (headline, primary CTA buttons, any visible products).",
        "backend": "gemini-flash",
        "runtime": "hybrid",
        "mode": "browser",
        "max_steps": 6,
    },
    "demo_login_flow": {
        "goal": "Visit https://sale.mir.ae/demo. If a login form is present, fill the demo "
                "credentials shown on the page. Report what is visible after login. Stop if no login form is found.",
        "backend": "gemini-pro",
        "runtime": "hybrid",
        "mode": "browser",
        "max_steps": 12,
    },
    "whatsapp_otp": {
        "goal": "Open https://web.whatsapp.com in the user's existing logged-in session. "
                "Locate the most recent incoming message that contains a numeric OTP code "
                "(4-8 digits). Return the OTP code and the sender name. "
                "If WhatsApp is not logged in, stop and report 'NOT_LOGGED_IN'.",
        "backend": "gemini-pro",
        "runtime": "local",          # web.whatsapp.com is QR-bound to user's phone
        "mode": "browser",
        "max_steps": 15,
    },
    "demo_with_otp": {
        "goal": "Step 1: Visit https://sale.mir.ae/demo and trigger any 'send code' / OTP / "
                "WhatsApp verification flow. Step 2: Switch to https://web.whatsapp.com and "
                "read the latest OTP code received. Step 3: Return to sale.mir.ae and enter "
                "the OTP. Step 4: Report final state. Use local runtime for whatsapp.",
        "backend": "gemini-pro",
        "runtime": "hybrid",   # router auto-forces whatsapp tabs to local
        "mode": "browser",
        "max_steps": 25,
    },
    "excel_round_trip": {
        "goal": "On the desktop, open or create C:/temp/scraper_test.xlsx. Write headers "
                "Name, Qty, Price into A1:C1, then write three sample rows. Save the file. "
                "Then read the file back and return the contents.",
        "backend": "gemini-pro",
        "runtime": "local",
        "mode": "desktop",
        "max_steps": 10,
    },
}


async def run_scenario(name: str, cfg: dict) -> dict:
    out_dir = pathlib.Path("out") / name
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n=== {name} ===")
    print(f"goal: {cfg['goal']}")
    async with httpx.AsyncClient(timeout=None) as c:
        r = await c.post(f"{SCRAPER_URL}/api/tasks", json=cfg)
        r.raise_for_status()
        tid = r.json()["id"]
        print(f"task: {tid}")

        async with c.stream("GET", f"{SCRAPER_URL}/api/tasks/{tid}/events") as stream:
            async for line in stream.aiter_lines():
                if not line.startswith("data: "):
                    continue
                ev = json.loads(line[6:])
                kind = ev.get("kind")
                data = ev.get("data") or {}
                if kind == "screenshot":
                    step = data.get("step", 0)
                    shot = await c.get(f"{SCRAPER_URL}/api/tasks/{tid}/screenshot/{step}")
                    if shot.status_code == 200:
                        b64 = shot.json().get("b64")
                        if b64:
                            (out_dir / f"step-{step:02d}.png").write_bytes(base64.b64decode(b64))
                            print(f"  [screenshot] step={step} url={data.get('url','')}")
                elif kind == "step":
                    print(f"  [step] {data.get('action')} {str(data.get('args',''))[:80]}")
                elif kind == "error":
                    print(f"  [error] {data.get('message')}")
                elif kind == "done":
                    print(f"  [done] {data.get('reasoning','')}")
                    return {"id": tid, "answer": data.get("answer"), "name": name}
        return {"id": tid, "answer": None, "name": name}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", nargs="?", default="all", choices=["all", *SCENARIOS.keys()])
    args = parser.parse_args()
    targets = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    results = []
    for name in targets:
        try:
            results.append(await run_scenario(name, SCENARIOS[name]))
        except Exception as e:
            print(f"  [scenario error] {e}", file=sys.stderr)
            results.append({"name": name, "error": str(e)})
    print("\n=== SUMMARY ===")
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
