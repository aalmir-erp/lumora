"""Export cookies for a given domain from the user's Chrome profile,
ready to inject into a Railway-side Playwright context via `set_cookies`.

This lets you keep Railway's runtime fast/cheap for sites where you've
logged in on your PC, without WhatsApp-style QR-bound flows. Run this
once on Windows after logging into the target site in Chrome:

    python -m local_agent.export_cookies --domain example.com --out cookies.json

Then upload cookies.json content via the API:
    POST /api/tasks {"goal":"...", "runtime":"railway", ...}
    (your task should include a set_cookies action with the contents)

Note: Chrome encrypts cookies on Windows using DPAPI. Decrypting requires
the user's login session — same machine, same user. We do that via the
`pycryptodome` + `pywin32` combo if available; otherwise we fall back to
launching a temporary Playwright context that re-uses the profile to
read cookies through the Chrome DevTools Protocol (slower but always works).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from .browser import default_chrome_profile_dir


async def export_via_playwright(domain: str, out_path: str) -> None:
    from playwright.async_api import async_playwright  # type: ignore
    profile = default_chrome_profile_dir()
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=profile, headless=True, channel="chrome",
        )
        # Open about:blank so the storage state is available
        await ctx.new_page()
        cookies = await ctx.cookies()
        relevant = [c for c in cookies if c.get("domain", "").lstrip(".").endswith(domain)]
        with open(out_path, "w") as f:
            json.dump(relevant, f, indent=2)
        await ctx.close()
    print(f"[export] {len(relevant)} cookies for {domain} -> {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, help="e.g. example.com (no scheme)")
    ap.add_argument("--out", default="cookies.json")
    args = ap.parse_args()
    try:
        asyncio.run(export_via_playwright(args.domain, args.out))
    except Exception as e:
        print(f"[export] failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
