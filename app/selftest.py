"""Self-test runner for the deployed app. Hits internal + external checks and
returns a comprehensive health report so admin gets a one-click 'is everything
working?' answer without needing devtools.

Endpoint: GET /api/admin/selftest
"""
from __future__ import annotations
import asyncio, datetime as _dt, json as _json, os, time
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends

from . import db
from .auth import require_admin
from .config import get_settings

router = APIRouter(prefix="/api/admin/selftest", tags=["admin-selftest"],
                   dependencies=[Depends(require_admin)])


async def _probe(url: str, timeout: float = 8.0) -> dict:
    """HEAD/GET a URL and return diagnostic info."""
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True,
                                     headers={"User-Agent": "ServiaSelfTest/1.0"}) as c:
            r = await c.get(url)
        return {
            "url": url, "ok": r.status_code < 400,
            "status": r.status_code,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "size_kb": round(len(r.content) / 1024, 1),
            "content_type": r.headers.get("content-type", ""),
        }
    except Exception as e:  # noqa: BLE001
        return {
            "url": url, "ok": False, "error": str(e)[:200],
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }


def _origin() -> str:
    """Best-guess public origin. Reads BRAND_DOMAIN env then falls back to
    the Railway internal URL so we always have something to probe."""
    s = get_settings()
    dom = (s.BRAND_DOMAIN or "servia.ae").strip()
    return f"https://{dom}"


@router.get("")
async def run_selftest():
    """Runs ~30 health checks and returns a structured report."""
    origin = _origin()
    started = _dt.datetime.utcnow()
    report: dict = {
        "started_at": started.isoformat() + "Z",
        "origin": origin,
        "groups": {},
    }

    # ---- 1) public pages
    pages = ["/", "/services.html", "/book.html", "/cart.html", "/coverage.html",
             "/videos.html", "/me.html", "/contact.html", "/privacy.html", "/terms.html"]
    page_probes = await asyncio.gather(*[_probe(origin + p) for p in pages],
                                       return_exceptions=False)
    report["groups"]["public_pages"] = {
        "ok": all(p.get("ok") for p in page_probes),
        "items": page_probes,
    }

    # ---- 2) seo + crawler manifests
    seo = ["/sitemap.xml", "/robots.txt", "/llms.txt", "/manifest.webmanifest"]
    seo_probes = await asyncio.gather(*[_probe(origin + p) for p in seo])
    report["groups"]["seo_manifests"] = {
        "ok": all(p.get("ok") for p in seo_probes),
        "items": seo_probes,
    }

    # ---- 3) api endpoints (public)
    api = ["/api/health", "/api/site/social", "/api/activity/live",
           "/api/services", "/api/videos/list?limit=10"]
    api_probes = await asyncio.gather(*[_probe(origin + p) for p in api])
    report["groups"]["public_api"] = {
        "ok": all(p.get("ok") for p in api_probes),
        "items": api_probes,
    }

    # ---- 4) llm health (uses ai_router's diagnose path internally)
    llm_status = {"checked": False}
    try:
        s = get_settings()
        if s.ANTHROPIC_API_KEY:
            import anthropic
            t0 = time.perf_counter()
            try:
                client = anthropic.Anthropic(api_key=s.ANTHROPIC_API_KEY,
                                             timeout=8.0, max_retries=0)
                r = client.messages.create(
                    model=s.MODEL, max_tokens=10,
                    messages=[{"role": "user", "content": "Reply: ok"}])
                txt = ""
                for b in r.content:
                    if getattr(b, "type", "") == "text": txt += b.text
                llm_status = {
                    "checked": True, "ok": True,
                    "model": getattr(r, "model", s.MODEL),
                    "latency_ms": int((time.perf_counter() - t0) * 1000),
                    "sample": txt[:60],
                }
            except Exception as e:
                llm_status = {"checked": True, "ok": False,
                              "model": s.MODEL, "error": str(e)[:200],
                              "latency_ms": int((time.perf_counter() - t0) * 1000)}
        else:
            llm_status = {"checked": True, "ok": False,
                          "error": "ANTHROPIC_API_KEY env var not set"}
    except Exception as e:
        llm_status = {"checked": True, "ok": False, "error": str(e)[:200]}
    report["groups"]["llm"] = {"ok": bool(llm_status.get("ok")),
                               "items": [llm_status]}

    # ---- 5) whatsapp bridge ping
    wa = {"checked": True, "ok": False}
    try:
        s = get_settings()
        if s.WA_BRIDGE_URL:
            url = s.WA_BRIDGE_URL.rstrip("/") + "/status"
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(url, headers={"Authorization": f"Bearer {s.WA_BRIDGE_TOKEN}"})
            j = r.json() if r.status_code == 200 else {"error": r.text[:200]}
            wa = {"checked": True, "ok": r.status_code == 200,
                  "ready": j.get("ready", False),
                  "paired_number": j.get("paired_number"),
                  "has_qr": j.get("has_qr", False),
                  "raw": j}
        else:
            wa = {"checked": True, "ok": False, "error": "WA_BRIDGE_URL not set"}
    except Exception as e:
        wa = {"checked": True, "ok": False, "error": str(e)[:200]}
    # v1.24.190 — Three-state classifier (founder hit: '❌ WhatsApp' shown
    # even when bridge was reachable with QR waiting — that's not a failure):
    #   ok+ready                   → state='paired', group.ok=True
    #   ok+!ready+has_qr           → state='awaiting_scan', group.ok=True
    #                                 (bridge up + QR ready; admin just needs to scan)
    #   ok+!ready+!has_qr          → state='no_qr_yet', group.ok=False
    #   !ok                        → state='unreachable', group.ok=False
    if wa.get("ok") and wa.get("ready"):
        wa["state"] = "paired";          wa_ok = True
    elif wa.get("ok") and wa.get("has_qr"):
        wa["state"] = "awaiting_scan";   wa_ok = True
        wa["hint"]  = "Bridge is up + QR is ready. Open /admin → WhatsApp tab (or /admin-wa-bridge) and scan."
    elif wa.get("ok"):
        wa["state"] = "no_qr_yet";       wa_ok = False
        wa["hint"]  = "Bridge reachable but no QR yet. Restart the bridge service or check its logs."
    else:
        wa["state"] = "unreachable";     wa_ok = False
        wa["hint"]  = "Bridge not reachable. Confirm WA_BRIDGE_URL + WA_BRIDGE_TOKEN on the bot AND that the bridge service is deployed."
    report["groups"]["whatsapp"] = {"ok": wa_ok, "state": wa["state"],
                                    "items": [wa]}

    # ---- 6) database health (counts of key tables)
    try:
        with db.connect() as c:
            counts = {}
            for tbl in ("conversations", "bookings", "services", "vendors",
                         "customers", "videos", "blog_posts"):
                try:
                    counts[tbl] = c.execute(f"SELECT COUNT(*) AS n FROM {tbl}").fetchone()["n"]
                except Exception:
                    counts[tbl] = None
        report["groups"]["database"] = {"ok": True, "items": [{"counts": counts}]}
    except Exception as e:
        report["groups"]["database"] = {"ok": False, "items": [{"error": str(e)[:200]}]}

    # ---- 7) ai router config — how many providers have keys?
    try:
        from . import ai_router
        cfg = ai_router._load_cfg()
        providers_with_keys = [
            {"provider": p, "has_key": bool(cfg["keys"].get(p, "").strip())}
            for p in ai_router.MODEL_CATALOG.keys()]
        n_ready = sum(1 for p in providers_with_keys if p["has_key"])
        report["groups"]["ai_router"] = {
            "ok": n_ready > 0,
            "items": [{"providers_with_keys": n_ready,
                       "total_providers": len(providers_with_keys),
                       "details": providers_with_keys,
                       "default_customer": (cfg.get("defaults") or {}).get("customer")}],
        }
    except Exception as e:
        report["groups"]["ai_router"] = {"ok": False, "items": [{"error": str(e)[:200]}]}

    # ---- 8) bot crawl summary (passive visibility)
    try:
        from . import visibility
        visibility._ensure_table()
        with db.connect() as c:
            cutoff = (_dt.datetime.utcnow() - _dt.timedelta(days=7)).isoformat() + "Z"
            n = c.execute(
                "SELECT COUNT(*) AS n FROM bot_visits WHERE created_at > ?",
                (cutoff,)).fetchone()["n"]
            rows = c.execute(
                "SELECT bot_name, COUNT(*) AS visits FROM bot_visits "
                "WHERE created_at > ? GROUP BY bot_name ORDER BY visits DESC LIMIT 10",
                (cutoff,)).fetchall()
        report["groups"]["bot_visibility"] = {
            "ok": True,
            "items": [{"total_visits_7d": n,
                       "top_bots": [dict(r) for r in rows]}],
        }
    except Exception as e:
        report["groups"]["bot_visibility"] = {"ok": False, "items": [{"error": str(e)[:200]}]}

    # ---- summary
    n_pass = sum(1 for g in report["groups"].values() if g.get("ok"))
    n_total = len(report["groups"])
    report["summary"] = {
        "passed": n_pass, "total": n_total,
        "score_pct": round(n_pass * 100 / max(1, n_total)),
        "duration_ms": int((time.perf_counter() - time.perf_counter()) * 1000),
        "finished_at": _dt.datetime.utcnow().isoformat() + "Z",
    }
    db.cfg_set("last_selftest", report)
    return report
