"""PageSpeed Insights auto-checker.

After every deploy + once a day, hits Google's free PSI v5 API for the
homepage (mobile + desktop), stores the score history, and alerts admin
when Performance < 98. The admin dashboard reads psi_history to render
a small green/red strip showing latest score + trend.

Google PSI API is free, no key required for casual use, but a key gives
higher quota. Set env GOOGLE_PSI_API_KEY for reliability.
"""
from __future__ import annotations
import datetime as _dt
import os
from typing import Any

import httpx

from . import db


PSI_URL = "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed"
TARGET_SCORE = 98
HISTORY_KEY = "psi_history"
MAX_HISTORY = 30


def _domain() -> str:
    from .config import get_settings
    s = get_settings()
    return f"https://{s.BRAND_DOMAIN or 'servia.ae'}"


async def _run_one(url: str, strategy: str) -> dict[str, Any]:
    """Run PSI for one URL+strategy. Returns parsed score + key audits."""
    params = {
        "url": url,
        "strategy": strategy,        # "mobile" | "desktop"
        "category": "performance",
    }
    key = os.getenv("GOOGLE_PSI_API_KEY", "").strip()
    if key: params["key"] = key

    try:
        async with httpx.AsyncClient(timeout=90) as c:
            r = await c.get(PSI_URL, params=params)
        if r.status_code >= 400:
            return {"ok": False, "error": f"PSI {r.status_code}: {r.text[:200]}",
                    "strategy": strategy}
        j = r.json()
        lh = j.get("lighthouseResult", {})
        cats = (lh.get("categories") or {}).get("performance") or {}
        audits = lh.get("audits", {})
        score = cats.get("score")
        score_pct = int(score * 100) if isinstance(score, (int, float)) else None
        # Pull the headline metrics
        def _v(k):
            a = audits.get(k) or {}
            return a.get("displayValue") or a.get("numericValue")
        # Grab top failing opportunities
        opps = []
        for aid, a in audits.items():
            score_a = a.get("score")
            if (a.get("details", {}) or {}).get("type") == "opportunity" and \
               isinstance(score_a, (int, float)) and score_a < 0.9:
                savings = (a.get("details") or {}).get("overallSavingsMs", 0)
                opps.append({
                    "id": aid, "title": a.get("title"),
                    "savings_ms": int(savings or 0),
                    "display": a.get("displayValue", ""),
                })
        opps.sort(key=lambda x: x["savings_ms"], reverse=True)
        return {
            "ok": True,
            "strategy": strategy,
            "score": score_pct,
            "fcp": _v("first-contentful-paint"),
            "lcp": _v("largest-contentful-paint"),
            "tbt": _v("total-blocking-time"),
            "cls": _v("cumulative-layout-shift"),
            "speed_index": _v("speed-index"),
            "top_opportunities": opps[:5],
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "strategy": strategy, "error": str(e)[:200]}


async def run_psi_check(url: str | None = None) -> dict[str, Any]:
    """Run PSI for both mobile + desktop, store result, return summary.
    Sends admin alert if either score < TARGET_SCORE."""
    target_url = url or _domain()
    started = _dt.datetime.utcnow()
    import asyncio
    mobile, desktop = await asyncio.gather(
        _run_one(target_url, "mobile"),
        _run_one(target_url, "desktop"),
    )
    finished = _dt.datetime.utcnow()
    ms = (mobile.get("score") or 0) if mobile.get("ok") else 0
    ds = (desktop.get("score") or 0) if desktop.get("ok") else 0

    snap = {
        "url": target_url,
        "ts": finished.isoformat() + "Z",
        "duration_ms": int((finished - started).total_seconds() * 1000),
        "mobile": mobile,
        "desktop": desktop,
        "min_score": min(s for s in (ms, ds) if s) if (ms and ds) else (ms or ds),
        "passed": (ms >= TARGET_SCORE and ds >= TARGET_SCORE),
    }

    # Append to history (capped to MAX_HISTORY)
    hist = db.cfg_get(HISTORY_KEY, []) or []
    hist.insert(0, snap)
    db.cfg_set(HISTORY_KEY, hist[:MAX_HISTORY])

    # Alert admin if below target
    if not snap["passed"] and (ms or ds):
        try:
            from . import admin_alerts as _aa
            opps_text = ""
            for s, label in ((mobile, "MOBILE"), (desktop, "DESKTOP")):
                if s.get("ok") and (s.get("score") or 100) < TARGET_SCORE:
                    opps_text += f"\n*{label}* (score {s.get('score')}/100):\n"
                    for o in (s.get("top_opportunities") or [])[:3]:
                        opps_text += f"  • {o['title']} — save ~{o['savings_ms']}ms\n"
            _aa.notify_admin(
                f"⚠️ PSI score below {TARGET_SCORE}\n\n"
                f"URL: {target_url}\n"
                f"Mobile: {ms or '?'}/100  ·  Desktop: {ds or '?'}/100\n"
                f"FCP: {(mobile or {}).get('fcp','?')}  LCP: {(mobile or {}).get('lcp','?')}  "
                f"TBT: {(mobile or {}).get('tbt','?')}  CLS: {(mobile or {}).get('cls','?')}\n"
                f"{opps_text}",
                kind="psi_alert", urgency="high")
        except Exception: pass

    return snap


def latest() -> dict[str, Any] | None:
    h = db.cfg_get(HISTORY_KEY, []) or []
    return h[0] if h else None


def history(limit: int = 14) -> list[dict[str, Any]]:
    return (db.cfg_get(HISTORY_KEY, []) or [])[:limit]
