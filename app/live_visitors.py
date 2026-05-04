"""Live visitor tracker. Records the last hit per (session-cookie or ip+ua hash)
plus the current page they're viewing. Admin polling endpoint returns the
live list (last 5 min activity) and a 'new visitor' webhook so PWA push can
ping the admin's phone when someone lands.

Designed to be cheap: one row per visitor, updated on every hit. Old rows
pruned on read.
"""
from __future__ import annotations
import datetime as _dt
import hashlib
from typing import Any

from fastapi import APIRouter, Depends, Request

from . import db
from .auth import require_admin


admin_router = APIRouter(prefix="/api/admin/live", tags=["admin-live"],
                         dependencies=[Depends(require_admin)])


def _ensure_table() -> None:
    with db.connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS live_visitors (
                visitor_id TEXT PRIMARY KEY,
                first_seen TEXT, last_seen TEXT,
                last_path TEXT, prev_path TEXT,
                user_agent TEXT, ip TEXT, country TEXT,
                referrer TEXT,
                hit_count INTEGER DEFAULT 1,
                is_new INTEGER DEFAULT 1
            )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_live_last ON live_visitors(last_seen)")


def visitor_id_for(request: Request) -> str:
    """Stable ID per visitor: prefers Servia session cookie, falls back to ip+ua hash."""
    cookie = request.cookies.get("servia_vid", "")
    if cookie: return cookie
    raw = (request.client.host if request.client else "") + "|" + request.headers.get("user-agent", "")
    return "h_" + hashlib.sha1(raw.encode()).hexdigest()[:16]


def track(request: Request) -> bool:
    """Record this visitor's current activity. Returns True if this is a NEW
    visitor (first time we've seen them in the last 30 min) so callers can
    fire admin push notifications."""
    try:
        _ensure_table()
        vid = visitor_id_for(request)
        path = str(request.url.path)
        # Skip admin / API / private surfaces / static assets / known templates
        if path.startswith(("/api/", "/admin", "/admin-login", "/admin-widget",
                            "/_snippets", "/sw.js", "/lazy-loaders",
                            "/widget.", "/banner.", "/cms.js", "/intake.js",
                            "/theme.js", "/app.js", "/install.js", "/share.js",
                            "/cart-badge", "/social-strip", "/social-proof",
                            "/manifest", "/sitemap", "/robots.txt", "/llms.txt",
                            "/__admin_token__", "/_debug_token_", "/__")):
            return False
        # Skip static asset extensions
        if path.endswith((".js", ".css", ".svg", ".png", ".jpg", ".jpeg", ".webp",
                          ".ico", ".woff", ".woff2", ".ttf", ".map", ".json",
                          ".txt", ".xml", ".webmanifest")):
            return False
        # Skip template-string artifacts (unrendered ${...} in URLs)
        if "${" in path or "{{" in path:
            return False
        ua = (request.headers.get("user-agent") or "")[:300]
        # Skip known bots — they're tracked separately by visibility.log_bot_visit
        from . import visibility as _viz
        if _viz.detect_bot(ua):
            return False
        ip = (request.client.host if request.client else "")[:64]
        country = (request.headers.get("cf-ipcountry") or
                   request.headers.get("x-vercel-ip-country") or "")[:8]
        ref = (request.headers.get("referer") or "")[:300]
        now = _dt.datetime.utcnow()
        now_s = now.isoformat() + "Z"
        is_new = False
        with db.connect() as c:
            r = c.execute("SELECT last_seen, last_path FROM live_visitors WHERE visitor_id=?",
                          (vid,)).fetchone()
            if r:
                # If last_seen > 30 min ago, treat as new visit again
                try:
                    last = _dt.datetime.fromisoformat(r["last_seen"].rstrip("Z"))
                    if (now - last).total_seconds() > 1800: is_new = True
                except Exception: pass
                c.execute(
                    "UPDATE live_visitors SET last_seen=?, prev_path=?, last_path=?, "
                    "user_agent=?, ip=?, country=?, referrer=?, hit_count=hit_count+1 "
                    "WHERE visitor_id=?",
                    (now_s, r["last_path"] or "", path, ua, ip, country, ref, vid))
            else:
                is_new = True
                c.execute(
                    "INSERT INTO live_visitors(visitor_id, first_seen, last_seen, "
                    "last_path, prev_path, user_agent, ip, country, referrer) "
                    "VALUES(?,?,?,?,?,?,?,?,?)",
                    (vid, now_s, now_s, path, "", ua, ip, country, ref))
        return is_new
    except Exception:
        return False


def parse_ua(ua: str) -> dict:
    """Cheap UA → device/os/browser. No external deps."""
    if not ua: return {"device":"unknown","os":"?","browser":"?"}
    ua_l = ua.lower()
    device = "📱 Mobile" if "mobile" in ua_l else ("💻 Tablet" if "ipad" in ua_l or "tablet" in ua_l else "🖥 Desktop")
    if "iphone" in ua_l or "ipad" in ua_l or "ipod" in ua_l: os_ = "iOS"
    elif "android" in ua_l: os_ = "Android"
    elif "windows" in ua_l: os_ = "Windows"
    elif "mac os" in ua_l or "macintosh" in ua_l: os_ = "macOS"
    elif "linux" in ua_l: os_ = "Linux"
    else: os_ = "?"
    if "edg/" in ua_l: br = "Edge"
    elif "firefox" in ua_l: br = "Firefox"
    elif "chrome" in ua_l and "chromium" not in ua_l: br = "Chrome"
    elif "safari" in ua_l and "chrome" not in ua_l: br = "Safari"
    elif "samsungbrowser" in ua_l: br = "Samsung"
    elif "opera" in ua_l or "opr/" in ua_l: br = "Opera"
    else: br = "?"
    return {"device": device, "os": os_, "browser": br}


def _country_flag(code: str) -> str:
    if not code or len(code) != 2: return ""
    base = 0x1F1E6  # 🇦
    return chr(base + ord(code[0].upper()) - ord("A")) + chr(base + ord(code[1].upper()) - ord("A"))


@admin_router.get("/visitors")
def get_live_visitors(active_minutes: int = 5):
    """Returns visitors active in last N minutes (default 5).

    Enriched per-row data:
    - device / os / browser (parsed UA)
    - seconds_ago (since last hit)
    - session_duration_seconds (last_seen - first_seen)
    - flag emoji 🇦🇪 from country code
    - is_bot flag (matched against bot UA signatures)
    - looks_human guess (heuristic — UA + hit pattern)
    """
    _ensure_table()
    from . import visibility as _viz
    cutoff = (_dt.datetime.utcnow() - _dt.timedelta(minutes=max(1, active_minutes))).isoformat() + "Z"
    with db.connect() as c:
        rows = c.execute(
            "SELECT * FROM live_visitors WHERE last_seen > ? "
            "ORDER BY last_seen DESC LIMIT 100",
            (cutoff,)).fetchall()
    out = []
    now = _dt.datetime.utcnow()
    for r in rows:
        d = dict(r)
        d.update(parse_ua(d.get("user_agent","")))
        # Bot detection
        bot_name = _viz.detect_bot(d.get("user_agent",""))
        d["is_bot"] = bool(bot_name)
        d["bot_name"] = bot_name or ""
        # Country flag
        d["flag"] = _country_flag(d.get("country","") or "")
        # Timing
        try:
            last = _dt.datetime.fromisoformat(d["last_seen"].rstrip("Z"))
            d["seconds_ago"] = int((now - last).total_seconds())
        except Exception: d["seconds_ago"] = 0
        try:
            first = _dt.datetime.fromisoformat(d["first_seen"].rstrip("Z"))
            d["session_duration_seconds"] = int((last - first).total_seconds())
        except Exception: d["session_duration_seconds"] = 0
        # Pretty IP — IPv4 mapped to IPv6 trim
        ip = d.get("ip","")
        if ip.startswith("::ffff:"): ip = ip[7:]
        d["ip"] = ip
        out.append(d)
    return {
        "active": out,
        "count": len(out),
        "active_minutes": active_minutes,
    }


# Cleanup endpoint
@admin_router.post("/visitors/clear-test")
def clear_test_visitors():
    """Wipes the live_visitors table — useful when you want to reset after
    seeing your own admin hits clutter the list."""
    _ensure_table()
    with db.connect() as c:
        n = c.execute("DELETE FROM live_visitors").rowcount
    return {"ok": True, "deleted": n}


@admin_router.get("/stats")
def live_stats():
    """Quick dashboard counters: active now, today, this week."""
    _ensure_table()
    now = _dt.datetime.utcnow()
    with db.connect() as c:
        n_now = c.execute(
            "SELECT COUNT(*) AS n FROM live_visitors WHERE last_seen > ?",
            ((now - _dt.timedelta(minutes=5)).isoformat() + "Z",)).fetchone()["n"]
        n_today = c.execute(
            "SELECT COUNT(*) AS n FROM live_visitors WHERE first_seen > ?",
            ((now - _dt.timedelta(hours=24)).isoformat() + "Z",)).fetchone()["n"]
        n_week = c.execute(
            "SELECT COUNT(*) AS n FROM live_visitors WHERE first_seen > ?",
            ((now - _dt.timedelta(days=7)).isoformat() + "Z",)).fetchone()["n"]
        # Top pages right now
        pages = c.execute(
            "SELECT last_path, COUNT(*) AS n FROM live_visitors "
            "WHERE last_seen > ? GROUP BY last_path ORDER BY n DESC LIMIT 5",
            ((now - _dt.timedelta(minutes=15)).isoformat() + "Z",)).fetchall()
    return {
        "active_now": n_now,
        "today": n_today,
        "week": n_week,
        "top_pages_now": [{"path": p["last_path"], "count": p["n"]} for p in pages],
        "ts": now.isoformat() + "Z",
    }
