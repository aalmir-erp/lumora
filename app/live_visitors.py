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
        # v1.24.56 — full click-trail. Every page visit (capped per-visitor)
        # so admin can replay exactly which pages a user navigated through.
        c.execute("""
            CREATE TABLE IF NOT EXISTS visitor_pageviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id TEXT,
                path TEXT, referrer TEXT, seen_at TEXT
            )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_pageviews_vid_id "
                  "ON visitor_pageviews(visitor_id, id DESC)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_live_last ON live_visitors(last_seen)")


def _is_private_ip(ip: str) -> bool:
    """RFC 1918 (10/8, 172.16/12, 192.168/16), CGNAT (100.64/10, RFC 6598),
    loopback (127/8), link-local (169.254/16), or IPv6 private/loopback. These
    show up on Railway/Vercel/Fly because the proxy/load-balancer hop is what
    request.client.host reports. They are NOT real visitors and must be skipped."""
    if not ip: return True
    ip = ip.strip()
    if ip in ("", "0.0.0.0", "::", "::1", "127.0.0.1", "localhost"): return True
    try:
        import ipaddress
        # Strip IPv4-mapped IPv6 prefix
        if ip.startswith("::ffff:"): ip = ip[7:]
        addr = ipaddress.ip_address(ip)
        if addr.is_loopback or addr.is_link_local or addr.is_multicast or addr.is_unspecified:
            return True
        if addr.is_private:
            return True
        # CGNAT 100.64.0.0/10 — Python's is_private covers this in 3.12+, older
        # versions don't, so add an explicit check.
        if isinstance(addr, ipaddress.IPv4Address):
            if addr in ipaddress.ip_network("100.64.0.0/10"): return True
    except Exception:
        return False
    return False


def real_client_ip(request: Request) -> str:
    """Extract the actual visitor IP, walking forwarded-for chain past private
    proxies. On Railway, request.client.host is always 100.64.x.x (their CGNAT
    edge); the real IP comes from one of the forwarded headers below."""
    # CDN/proxy headers carry the real IP. Cloudflare > Vercel > generic.
    for h in ("cf-connecting-ip", "true-client-ip", "x-real-ip", "fly-client-ip",
              "x-vercel-forwarded-for", "x-forwarded-for"):
        v = (request.headers.get(h) or "").strip()
        if not v: continue
        # x-forwarded-for is a comma-separated chain "client, proxy1, proxy2".
        # Walk left to right and take the first PUBLIC address — that's the
        # original client; everything after is internal hops.
        for hop in v.split(","):
            ip = hop.strip()
            if ip and not _is_private_ip(ip):
                return ip
    # Last resort: direct connection (always private on PaaS — that's why we
    # check headers first).
    return (request.client.host if request.client else "")


def visitor_id_for(request: Request) -> str:
    """Stable ID per visitor: prefers Servia session cookie, falls back to ip+ua hash."""
    cookie = request.cookies.get("servia_vid", "")
    if cookie: return cookie
    raw = real_client_ip(request) + "|" + request.headers.get("user-agent", "")
    return "h_" + hashlib.sha1(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Referrer parsing — figure out whether visitor came from a search engine,
# social platform, or another website. If from a search engine, extract the
# query string when the referer still includes it (Google strips it on
# HTTPS-to-HTTPS traffic for privacy, but Bing/DDG/Yandex/Brave still pass it).
#
# Returned dict has 4 keys:
#   traffic_source : "direct" | "search" | "social" | "referral"
#   source_label   : human label like "Google", "Facebook", "Reddit", "Direct"
#   search_query   : the query string the visitor typed, or None
#   referrer_domain: cleaned eTLD+1 of referrer, or None
#
SEARCH_ENGINES = {
    # host substring -> (label, query param name)
    "google.":           ("Google",        "q"),
    "bing.com":          ("Bing",          "q"),
    "duckduckgo.com":    ("DuckDuckGo",    "q"),
    "search.yahoo":      ("Yahoo",         "p"),
    "yandex.":           ("Yandex",        "text"),
    "baidu.com":         ("Baidu",         "wd"),
    "search.brave.com":  ("Brave",         "q"),
    "ecosia.org":        ("Ecosia",        "q"),
    "qwant.com":         ("Qwant",         "q"),
    "kagi.com":          ("Kagi",          "q"),
    "search.naver.com":  ("Naver",         "query"),
    "perplexity.ai":     ("Perplexity",    "q"),
    "chatgpt.com":       ("ChatGPT",       "q"),
    "claude.ai":         ("Claude",        "q"),
    "gemini.google":     ("Gemini",        "q"),
    "copilot.microsoft": ("Copilot",       "q"),
}
SOCIAL_PLATFORMS = {
    # host substring -> label
    "facebook.com":      "Facebook",
    "fb.com":            "Facebook",
    "l.facebook.com":    "Facebook (link wrapper)",
    "twitter.com":       "Twitter",
    "x.com":             "X (Twitter)",
    "t.co":              "Twitter (t.co)",
    "linkedin.com":      "LinkedIn",
    "lnkd.in":           "LinkedIn",
    "instagram.com":     "Instagram",
    "tiktok.com":        "TikTok",
    "youtube.com":       "YouTube",
    "youtu.be":          "YouTube",
    "reddit.com":        "Reddit",
    "redd.it":           "Reddit",
    "pinterest.":        "Pinterest",
    "snapchat.com":      "Snapchat",
    "telegram.me":       "Telegram",
    "t.me":              "Telegram",
    "wa.me":             "WhatsApp",
    "web.whatsapp.com":  "WhatsApp Web",
    "whatsapp.com":      "WhatsApp",
    "discord.com":       "Discord",
    "discord.gg":        "Discord",
    "medium.com":        "Medium",
    "github.com":        "GitHub",
    "stackoverflow.com": "Stack Overflow",
    "ph.com":            "Product Hunt",
    "producthunt.com":   "Product Hunt",
}
def parse_referrer(ref: str) -> dict:
    if not ref or ref.strip() == "":
        return {"traffic_source": "direct", "source_label": "Direct",
                "search_query": None, "referrer_domain": None}
    try:
        from urllib.parse import urlparse, parse_qs
        u = urlparse(ref)
        host = (u.netloc or "").lower()
        if not host:
            return {"traffic_source": "direct", "source_label": "Direct",
                    "search_query": None, "referrer_domain": None}
        # Strip leading "www."
        host_clean = host[4:] if host.startswith("www.") else host
        # Search engines (highest priority)
        for sub, (label, qp) in SEARCH_ENGINES.items():
            if sub in host:
                qs = parse_qs(u.query or "")
                q = (qs.get(qp, [None]) or [None])[0]
                return {"traffic_source": "search", "source_label": label,
                        "search_query": q.strip() if q else None,
                        "referrer_domain": host_clean}
        # Social
        for sub, label in SOCIAL_PLATFORMS.items():
            if sub in host:
                return {"traffic_source": "social", "source_label": label,
                        "search_query": None, "referrer_domain": host_clean}
        # Anything else = generic referral from another site
        return {"traffic_source": "referral", "source_label": host_clean,
                "search_query": None, "referrer_domain": host_clean}
    except Exception:
        return {"traffic_source": "direct", "source_label": "Direct",
                "search_query": None, "referrer_domain": None}


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
        # Skip the admin themselves: any request carrying a valid admin Bearer
        # token (or the admin session cookie) shouldn't count as a public visit
        try:
            from .auth import ADMIN_TOKEN, RECOVERY_ADMIN_TOKEN
            auth = (request.headers.get("authorization") or "").lower()
            if auth.startswith("bearer "):
                tok = auth.split(None, 1)[1].strip()
                if tok in (ADMIN_TOKEN, RECOVERY_ADMIN_TOKEN):
                    return False
        except Exception: pass
        # Also skip if the cookie 'lumora.admin.tok' is set client-side and
        # exposed via a custom 'X-Admin-Cookie' header (frontend sends this on
        # every fetch to flag itself)
        if request.headers.get("x-admin-cookie") == "1":
            return False
        # Real client IP (walks past Railway/Vercel/CF proxies). If we can't
        # find a real public IP, this hit came from internal infra (health
        # check, uptime monitor, container probe) and must NOT be tracked.
        ip = (real_client_ip(request) or "")[:64]
        if not ip or _is_private_ip(ip):
            return False
        # Detect headless / automation that survives basic UA filtering. These
        # are uptime monitors and synthetic testers: HeadlessChrome, PhantomJS,
        # Puppeteer, Playwright, Selenium, Lighthouse, etc. Mark and skip.
        ua_lower = ua.lower()
        if any(t in ua_lower for t in ("headless", "phantomjs", "puppeteer", "playwright",
                                       "selenium", "webdriver", "lighthouse", "chrome-lighthouse",
                                       "pingdom", "uptime", "monitor", "synthetic",
                                       "preview", "prerender", "speedcurve")):
            return False
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
                # v1.24.56 — log each pageview into the click-trail
                try:
                    c.execute(
                        "INSERT INTO visitor_pageviews(visitor_id, path, referrer, seen_at) "
                        "VALUES(?,?,?,?)", (vid, path, ref, now_s))
                except Exception: pass
            else:
                is_new = True
                c.execute(
                    "INSERT INTO live_visitors(visitor_id, first_seen, last_seen, "
                    "last_path, prev_path, user_agent, ip, country, referrer) "
                    "VALUES(?,?,?,?,?,?,?,?,?)",
                    (vid, now_s, now_s, path, "", ua, ip, country, ref))
                # First pageview row
                try:
                    c.execute(
                        "INSERT INTO visitor_pageviews(visitor_id, path, referrer, seen_at) "
                        "VALUES(?,?,?,?)", (vid, path, ref, now_s))
                except Exception: pass
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
        # Filter out private/CGNAT IPs (Railway proxy hops) and headless UAs —
        # legacy rows from before the track-side filter shipped. Stops the
        # widget showing 100.64.x.x "users" forever.
        ip_clean = (d.get("ip","") or "")
        if ip_clean.startswith("::ffff:"): ip_clean = ip_clean[7:]
        if not ip_clean or _is_private_ip(ip_clean):
            continue
        ua_l = (d.get("user_agent","") or "").lower()
        if any(t in ua_l for t in ("headless","phantomjs","puppeteer","playwright",
                                    "selenium","webdriver","lighthouse",
                                    "pingdom","uptime","monitor","synthetic")):
            continue
        d.update(parse_ua(d.get("user_agent","")))
        # v1.24.55 — figure out where the visitor actually came from. Adds 4
        # extra keys (traffic_source, source_label, search_query, referrer_domain)
        # that the admin UI renders as a chip like
        # "Google · 'ac repair dubai'" or "Direct" or "Facebook"
        d.update(parse_referrer(d.get("referrer","") or ""))
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


@admin_router.post("/visitors/purge-junk")
def purge_junk_visitors():
    """Wipes Railway-internal / private-IP / headless rows that slipped into
    the live_visitors table before the new filter shipped. Run once after
    deploying v1.22.8+ to get the widget showing only real visitors."""
    _ensure_table()
    with db.connect() as c:
        # Private + CGNAT IPs
        n_priv = c.execute("""
            DELETE FROM live_visitors
            WHERE ip LIKE '10.%' OR ip LIKE '192.168.%' OR ip LIKE '127.%'
               OR ip LIKE '169.254.%' OR ip LIKE '::1' OR ip = '0.0.0.0'
               OR ip GLOB '172.[123][0-9].*'
               OR ip GLOB '100.[6-9][0-9].*' OR ip GLOB '100.1[01][0-9].*'
               OR ip GLOB '100.12[0-7].*'
               OR ip IS NULL OR ip = ''""").rowcount
        # Headless / synthetic UAs
        n_bot = c.execute("""
            DELETE FROM live_visitors
            WHERE LOWER(user_agent) LIKE '%headless%'
               OR LOWER(user_agent) LIKE '%phantomjs%'
               OR LOWER(user_agent) LIKE '%puppeteer%'
               OR LOWER(user_agent) LIKE '%playwright%'
               OR LOWER(user_agent) LIKE '%selenium%'
               OR LOWER(user_agent) LIKE '%webdriver%'
               OR LOWER(user_agent) LIKE '%lighthouse%'
               OR LOWER(user_agent) LIKE '%pingdom%'
               OR LOWER(user_agent) LIKE '%uptime%'
               OR LOWER(user_agent) LIKE '%monitor%'
               OR LOWER(user_agent) LIKE '%synthetic%'""").rowcount
    return {"ok": True, "deleted_private": n_priv, "deleted_headless": n_bot,
            "total": n_priv + n_bot}


@admin_router.get("/stats")
def live_stats():
    """Quick dashboard counters: active now, today, this week, plus a 24h
    hourly breakdown so the home-screen widget can sparkline-chart it."""
    _ensure_table()
    now = _dt.datetime.utcnow()
    # SQL-side filter: skip rows whose IP is in the private/CGNAT space we
    # can detect via prefix (10., 192.168., 172.16.-31., 100.64.-127., 127.,
    # 169.254., loopback IPv6). Cheaper than re-running ipaddress for every
    # row from Python on the dashboard hot-path.
    JUNK = (
        "AND ip NOT LIKE '10.%' AND ip NOT LIKE '192.168.%' "
        "AND ip NOT LIKE '127.%' AND ip NOT LIKE '169.254.%' "
        "AND ip NOT LIKE '::1' AND ip NOT LIKE '0.0.0.0' "
        "AND ip NOT GLOB '172.[123][0-9].*' "
        "AND ip NOT GLOB '100.[6-9][0-9].*' AND ip NOT GLOB '100.1[01][0-9].*' "
        "AND ip NOT GLOB '100.12[0-7].*' "
        "AND ip NOT NULL AND ip != ''"
    )
    with db.connect() as c:
        n_now = c.execute(
            "SELECT COUNT(*) AS n FROM live_visitors WHERE last_seen > ? " + JUNK,
            ((now - _dt.timedelta(minutes=5)).isoformat() + "Z",)).fetchone()["n"]
        n_today = c.execute(
            "SELECT COUNT(*) AS n FROM live_visitors WHERE first_seen > ? " + JUNK,
            ((now - _dt.timedelta(hours=24)).isoformat() + "Z",)).fetchone()["n"]
        n_week = c.execute(
            "SELECT COUNT(*) AS n FROM live_visitors WHERE first_seen > ? " + JUNK,
            ((now - _dt.timedelta(days=7)).isoformat() + "Z",)).fetchone()["n"]
        pages = c.execute(
            "SELECT last_path, COUNT(*) AS n FROM live_visitors "
            "WHERE last_seen > ? " + JUNK + " GROUP BY last_path ORDER BY n DESC LIMIT 5",
            ((now - _dt.timedelta(minutes=15)).isoformat() + "Z",)).fetchall()
        rows24 = c.execute(
            "SELECT first_seen FROM live_visitors WHERE first_seen > ? " + JUNK,
            ((now - _dt.timedelta(hours=24)).isoformat() + "Z",)).fetchall()
    buckets = [0] * 24
    for r in rows24:
        try:
            t = _dt.datetime.fromisoformat((r["first_seen"] or "").rstrip("Z"))
            hours_ago = int((now - t).total_seconds() // 3600)
            if 0 <= hours_ago < 24:
                buckets[23 - hours_ago] += 1
        except Exception: pass
    return {
        "active_now": n_now,
        "today": n_today,
        "week": n_week,
        "top_pages_now": [{"path": p["last_path"], "count": p["n"]} for p in pages],
        "hourly_24h": buckets,
        "ts": now.isoformat() + "Z",
    }


# ---------------------------------------------------------------------------
# v1.24.56 — Full click-trail for a visitor.
@admin_router.get("/visitor/{vid}/trail")
def visitor_trail(vid: str, limit: int = 200) -> dict:
    """Returns last N pageviews for a visitor, newest first."""
    _ensure_table()
    with db.connect() as c:
        rows = c.execute(
            "SELECT path, referrer, seen_at FROM visitor_pageviews "
            "WHERE visitor_id=? ORDER BY id DESC LIMIT ?",
            (vid, max(1, min(limit, 500)))).fetchall()
        v = c.execute("SELECT * FROM live_visitors WHERE visitor_id=?",
                      (vid,)).fetchone()
    return {
        "visitor": dict(v) if v else None,
        "pageviews": [dict(r) for r in rows],
        "count": len(rows),
    }
