"""Visibility tracker — auto-detect where Servia is appearing.

Two complementary signals:

A) **External index probes** (active scan)
   Hit Google/Bing/Brave/DuckDuckGo with `site:servia.ae` and parse the
   indexed-pages count. No API keys — uses the public HTML search results.
   Cached for 24h to avoid rate-limiting.

B) **AI bot crawl log** (passive logging)
   A FastAPI middleware records every request whose User-Agent matches a
   known AI/search-bot signature (GPTBot, ClaudeBot, PerplexityBot, Google,
   Bing, Brave, Yandex, etc) into a small `bot_visits` table. Admin can see
   "8 GPTBot visits this week, 12 ClaudeBot, 0 PerplexityBot — fix robots".
"""
from __future__ import annotations
import datetime as _dt
import os, re, time
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, Request

from . import db
from .auth import require_admin

router = APIRouter(prefix="/api/admin/launch/visibility",
                   tags=["admin-visibility"],
                   dependencies=[Depends(require_admin)])


# Known bot User-Agent fragments → friendly name.
# Any UA matching these substrings gets logged so admin sees crawl activity.
BOT_SIGNATURES = [
    # AI engines (priority — these mean LLMs are pulling our content)
    ("GPTBot",                "OpenAI GPTBot"),
    ("OAI-SearchBot",         "OpenAI SearchBot"),
    ("ChatGPT-User",          "ChatGPT (user)"),
    ("ClaudeBot",             "Anthropic ClaudeBot"),
    ("Claude-Web",             "Anthropic Claude-Web"),
    ("Claude-User",           "Claude (user)"),
    ("PerplexityBot",         "Perplexity"),
    ("Perplexity-User",       "Perplexity (user)"),
    ("Google-Extended",       "Google AI (Bard/Gemini training)"),
    ("Bytespider",            "ByteDance / TikTok AI"),
    ("Amazonbot",             "Amazon AI"),
    ("FacebookBot",           "Meta AI"),
    ("Meta-ExternalAgent",    "Meta AI"),
    ("YouBot",                "You.com"),
    ("PhindBot",              "Phind"),
    ("Diffbot",               "Diffbot"),
    ("Applebot-Extended",     "Apple AI"),
    ("CCBot",                 "Common Crawl (training)"),
    ("AI2Bot",                "Allen Institute"),
    ("anthropic-ai",          "Anthropic (legacy)"),
    ("cohere-ai",             "Cohere"),
    # Search engines
    ("Googlebot",             "Google Search"),
    ("AdsBot-Google",         "Google Ads"),
    ("Mediapartners-Google",  "Google AdSense"),
    ("bingbot",               "Bing"),
    ("BingPreview",           "Bing Preview"),
    ("Slurp",                 "Yahoo"),
    ("DuckDuckBot",           "DuckDuckGo"),
    ("YandexBot",             "Yandex"),
    ("Baiduspider",           "Baidu"),
    ("BraveBot",              "Brave Search"),
    ("MojeekBot",             "Mojeek"),
    ("Applebot",              "Apple Maps"),
    ("ia_archiver",           "Wayback Machine"),
    # Social previews (signal that the link is being shared)
    ("Twitterbot",            "X / Twitter share"),
    ("facebookexternalhit",   "Facebook share"),
    ("WhatsApp",              "WhatsApp share"),
    ("LinkedInBot",           "LinkedIn share"),
    ("TelegramBot",           "Telegram share"),
    ("Slackbot",              "Slack share"),
    ("Discordbot",            "Discord share"),
    ("Pinterestbot",          "Pinterest share"),
]


def _ensure_table() -> None:
    """Create bot_visits table if missing."""
    with db.connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS bot_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_name TEXT NOT NULL,
                user_agent TEXT,
                path TEXT,
                ip TEXT,
                referer TEXT,
                country TEXT,
                created_at TEXT NOT NULL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_bot_visits_name ON bot_visits(bot_name)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_bot_visits_at ON bot_visits(created_at)")


def detect_bot(ua: str) -> str | None:
    """Returns the friendly bot-name if UA matches a signature, else None."""
    if not ua: return None
    for fragment, name in BOT_SIGNATURES:
        if fragment.lower() in ua.lower():
            return name
    return None


def log_bot_visit(request: Request) -> None:
    """Called by the visibility middleware on every request. Cheap (~1ms) — only
    writes a row if the UA matches a known bot signature; otherwise no-op."""
    try:
        ua = request.headers.get("user-agent", "") or ""
        bot = detect_bot(ua)
        if not bot: return
        path = str(request.url.path)[:300]
        ip = (request.client.host if request.client else "")[:64]
        ref = (request.headers.get("referer") or "")[:300]
        # Try to lift CF country header if Railway proxies it through
        country = (request.headers.get("cf-ipcountry") or
                   request.headers.get("x-vercel-ip-country") or "")[:8]
        _ensure_table()
        with db.connect() as c:
            c.execute(
                "INSERT INTO bot_visits(bot_name, user_agent, path, ip, referer, country, created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (bot, ua[:300], path, ip, ref, country,
                 _dt.datetime.utcnow().isoformat() + "Z"))
    except Exception:
        pass  # never let logging break a request


# ---------- external index probes ----------
async def _probe_google(domain: str) -> dict:
    """Scrape Google's `site:` results page for the indexed-pages count."""
    url = f"https://www.google.com/search?q={quote('site:'+domain)}&hl=en&num=10"
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0 (compat; ServiaVisibility/1.0)"}) as c:
            r = await c.get(url)
        if r.status_code != 200:
            return {"ok": False, "engine": "google", "error": f"{r.status_code}"}
        html = r.text
        m = re.search(r'About ([\d,]+) result', html) or re.search(r'([\d,]+) result', html)
        count = int(m.group(1).replace(",", "")) if m else None
        return {"ok": True, "engine": "google", "indexed": count, "search_url": url}
    except Exception as e:
        return {"ok": False, "engine": "google", "error": str(e)}


async def _probe_bing(domain: str) -> dict:
    url = f"https://www.bing.com/search?q={quote('site:'+domain)}&form=QBLH"
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0 (compat; ServiaVisibility/1.0)"}) as c:
            r = await c.get(url)
        if r.status_code != 200:
            return {"ok": False, "engine": "bing", "error": f"{r.status_code}"}
        html = r.text
        m = (re.search(r'"sb_count">([\d,\.]+) result', html) or
             re.search(r'([\d,\.]+) result', html))
        count = int(m.group(1).replace(",", "").replace(".", "")) if m else None
        return {"ok": True, "engine": "bing", "indexed": count, "search_url": url}
    except Exception as e:
        return {"ok": False, "engine": "bing", "error": str(e)}


async def _probe_brave(domain: str) -> dict:
    url = f"https://search.brave.com/search?q={quote('site:'+domain)}"
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0 (compat; ServiaVisibility/1.0)"}) as c:
            r = await c.get(url)
        if r.status_code != 200:
            return {"ok": False, "engine": "brave", "error": f"{r.status_code}"}
        # Brave doesn't give a clean count — count the result <article> blocks
        results = len(re.findall(r'class="[^"]*result-row', r.text))
        return {"ok": True, "engine": "brave", "indexed": results, "search_url": url,
                "note": "approximate — counts visible results on page 1"}
    except Exception as e:
        return {"ok": False, "engine": "brave", "error": str(e)}


async def _probe_duckduckgo(domain: str) -> dict:
    url = f"https://html.duckduckgo.com/html/?q={quote('site:'+domain)}"
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0 (compat; ServiaVisibility/1.0)"}) as c:
            r = await c.get(url)
        if r.status_code != 200:
            return {"ok": False, "engine": "duckduckgo", "error": f"{r.status_code}"}
        results = len(re.findall(r'class="result__title"', r.text))
        return {"ok": True, "engine": "duckduckgo", "indexed": results,
                "search_url": f"https://duckduckgo.com/?q={quote('site:'+domain)}",
                "note": "approximate — counts visible results"}
    except Exception as e:
        return {"ok": False, "engine": "duckduckgo", "error": str(e)}


@router.post("/scan")
async def scan_now(domain: str = "servia.ae"):
    """Live-probe Google/Bing/Brave/DDG for site:{domain} and return indexed counts."""
    import asyncio
    results = await asyncio.gather(
        _probe_google(domain), _probe_bing(domain),
        _probe_brave(domain), _probe_duckduckgo(domain),
        return_exceptions=False)
    db.cfg_set("visibility_last_scan", {
        "ts": _dt.datetime.utcnow().isoformat() + "Z",
        "domain": domain,
        "results": results,
    })
    return {"ok": True, "ts": _dt.datetime.utcnow().isoformat() + "Z",
            "results": results}


@router.get("/scan")
def get_last_scan():
    """Returns the most recent cached scan result (don't hit search engines on every page load)."""
    cur = db.cfg_get("visibility_last_scan", None)
    if not cur:
        return {"ok": False, "msg": "No scan yet — click 'Scan now' to run the first one."}
    return {"ok": True, **cur}


@router.get("/bots")
def list_bot_visits(days: int = 7, limit: int = 200):
    """List recent bot visits for the admin Visibility panel.

    Returns:
      - per-bot weekly count + last_seen
      - last N rows of raw visits for inspection
    """
    _ensure_table()
    cutoff = (_dt.datetime.utcnow() - _dt.timedelta(days=days)).isoformat() + "Z"
    with db.connect() as c:
        # Weekly summary by bot
        rows = c.execute(
            "SELECT bot_name, COUNT(*) AS visits, MAX(created_at) AS last_seen, "
            "       COUNT(DISTINCT path) AS pages, COUNT(DISTINCT ip) AS ips "
            "FROM bot_visits WHERE created_at > ? "
            "GROUP BY bot_name ORDER BY visits DESC",
            (cutoff,)).fetchall()
        recent = c.execute(
            "SELECT bot_name, path, ip, country, created_at FROM bot_visits "
            "WHERE created_at > ? ORDER BY id DESC LIMIT ?",
            (cutoff, max(1, min(limit, 500)))).fetchall()
        total = c.execute(
            "SELECT COUNT(*) AS n FROM bot_visits WHERE created_at > ?",
            (cutoff,)).fetchone()
    return {
        "ok": True,
        "days": days,
        "total_visits": (total["n"] if total else 0),
        "by_bot": [dict(r) for r in rows],
        "recent": [dict(r) for r in recent],
    }
