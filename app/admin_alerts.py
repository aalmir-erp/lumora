"""Admin alerts.

Pushes important events (article published, new booking, urgent bot
message, daily summary) to the admin's personal WhatsApp via the QR-paired
bridge service. Admin number is read from ADMIN_WA_NUMBER env (E.164 digits
only, e.g. 971XXXXXXXXX — set on Railway, not committed in source).

If the bridge isn't paired or configured, alerts are still recorded in the
admin_alerts table so the admin sees them in the admin UI when they next
log in.
"""
from __future__ import annotations

import datetime as _dt
import os
import threading

from . import db
from .config import get_settings


def _admin_number() -> str:
    # v1.24.221 — Default to the founder's official Servia WhatsApp number
    # so the admin test-send button works out-of-the-box (was returning
    # bridge 400: 'to + text required' because ADMIN_WA_NUMBER env wasn't
    # set, so `to` ended up empty when calling the bridge).
    return os.getenv("ADMIN_WA_NUMBER", "971523633995").strip().lstrip("+")


def _ensure_table() -> None:
    with db.connect() as c:
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS admin_alerts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT, urgency TEXT, text TEXT, meta TEXT,
                delivered INTEGER DEFAULT 0, delivery_error TEXT,
                created_at TEXT)""")
        except Exception:
            pass


def _store(kind: str, urgency: str, text: str, meta: dict | None,
           delivered: bool, error: str | None) -> int:
    import json as _json
    _ensure_table()
    with db.connect() as c:
        cur = c.execute(
            "INSERT INTO admin_alerts(kind, urgency, text, meta, delivered, "
            "delivery_error, created_at) VALUES(?,?,?,?,?,?,?)",
            (kind, urgency, text, _json.dumps(meta or {}),
             1 if delivered else 0, error,
             _dt.datetime.utcnow().isoformat() + "Z"))
        return cur.lastrowid or 0


_BRIDGE_OUTAGE_UNTIL = 0.0   # epoch ts; if now < this, skip the bridge call

def _send_via_bridge(text: str) -> tuple[bool, str | None]:
    """Send via WA bridge with graceful auto-degradation.

    v1.24.56 — if the bridge returns 503 (not paired), or 5xx, or times out,
    we cache that for 5 minutes and skip the call instead of blocking every
    notify_admin for 8 seconds. Web-Push remains the working channel during
    bridge outages.
    """
    import time as _t
    global _BRIDGE_OUTAGE_UNTIL
    s = get_settings()
    if not s.WA_BRIDGE_URL:
        return False, "WA_BRIDGE_URL not configured"
    now = _t.time()
    if now < _BRIDGE_OUTAGE_UNTIL:
        return False, "bridge in outage cooldown (auto-skipped)"
    try:
        import httpx
        r = httpx.post(
            s.WA_BRIDGE_URL.rstrip("/") + "/send",
            headers={
                "Authorization": f"Bearer {s.WA_BRIDGE_TOKEN}",
                "content-type": "application/json",
            },
            json={"to": _admin_number(), "text": text},
            timeout=8,
        )
        if r.status_code >= 500 or r.status_code == 503:
            # Bridge is down (Chromium booting, Puppeteer crashed, container
            # restarting). Mark unhealthy for 5 minutes so we don't burn
            # every notify_admin call on the same retry.
            _BRIDGE_OUTAGE_UNTIL = now + 300
            return False, f"bridge {r.status_code} (cooldown 5min): {r.text[:160]}"
        if r.status_code >= 400:
            return False, f"bridge {r.status_code}: {r.text[:200]}"
        return True, None
    except Exception as e:  # noqa: BLE001
        # Network/connection error → also cooldown
        _BRIDGE_OUTAGE_UNTIL = now + 120
        return False, f"bridge unreachable (cooldown 2min): {e}"


def notify_admin(text: str, *, kind: str = "general",
                 urgency: str = "normal", meta: dict | None = None) -> int:
    """Fire-and-forget: send a WhatsApp alert to the admin number AND push
    a notification to every registered admin PWA subscription.

    Returns the admin_alerts row id. Always records the alert; bridge delivery
    + web push are best-effort overlays. Off-thread so callers (e.g. webhook
    handlers) are never blocked on network.
    """
    def _worker():
        # WhatsApp bridge (existing path)
        ok, err = _send_via_bridge(text)
        _store(kind, urgency, text, meta, ok, err)
        # Web Push (NEW) — fires per-device sound + vibration via SW
        try:
            from . import push_notifications as _pn
            # First line of text is the title, rest is the body
            lines = (text or "").strip().split("\n", 1)
            title = lines[0] if lines else "Servia alert"
            body = lines[1].strip() if len(lines) > 1 else ""
            _pn.send_to_all({
                "title": title[:60],
                "body": body[:240],
                "kind": kind,
                "url": "/admin.html#dashboard" if kind != "new_visitor" else "/admin.html#live",
                "tag": f"servia-{kind}",
            })
        except Exception:
            pass
    threading.Thread(target=_worker, daemon=True).start()
    return 0


def notify_admin_sync(text: str, *, kind: str = "general",
                      urgency: str = "normal", meta: dict | None = None) -> dict:
    """Synchronous version — used by admin UI 'send test' so we can return
    the actual delivery result."""
    ok, err = _send_via_bridge(text)
    rid = _store(kind, urgency, text, meta, ok, err)
    return {"ok": ok, "error": err, "id": rid}


# ---------- daily AI summary ----------
def daily_summary_text() -> str:
    """Build a 1-message AI summary of yesterday's website activity using
    Claude. Falls back to plain stats if LLM is disabled."""
    s = get_settings()
    today = _dt.datetime.utcnow().date()
    yesterday = today - _dt.timedelta(days=1)
    since = yesterday.isoformat()
    until = today.isoformat()

    stats: dict = {"date": yesterday.isoformat()}
    with db.connect() as c:
        try:
            stats["bookings"] = c.execute(
                "SELECT COUNT(*) AS n FROM bookings WHERE created_at >= ? AND created_at < ?",
                (since, until)).fetchone()["n"]
        except Exception: stats["bookings"] = 0
        try:
            stats["articles"] = c.execute(
                "SELECT COUNT(*) AS n FROM autoblog_posts WHERE published_at >= ? AND published_at < ?",
                (since, until)).fetchone()["n"]
        except Exception: stats["articles"] = 0
        try:
            stats["chats"] = c.execute(
                "SELECT COUNT(DISTINCT session_id) AS n FROM conversations "
                "WHERE created_at >= ? AND created_at < ?",
                (since, until)).fetchone()["n"]
        except Exception: stats["chats"] = 0
        try:
            stats["installs"] = c.execute(
                "SELECT COUNT(*) AS n FROM app_installs "
                "WHERE created_at >= ? AND created_at < ? AND event='installed'",
                (since, until)).fetchone()["n"]
        except Exception: stats["installs"] = 0
        try:
            stats["referrals"] = c.execute(
                "SELECT COUNT(*) AS n FROM referrals WHERE created_at >= ? AND created_at < ?",
                (since, until)).fetchone()["n"]
        except Exception: stats["referrals"] = 0
        try:
            stats["reviews"] = c.execute(
                "SELECT COUNT(*) AS n FROM reviews WHERE created_at >= ? AND created_at < ?",
                (since, until)).fetchone()["n"]
        except Exception: stats["reviews"] = 0
        # last 5 messages from chat (sample of intent)
        try:
            recent = c.execute(
                "SELECT content FROM conversations WHERE role='user' AND created_at >= ? "
                "ORDER BY id DESC LIMIT 8", (since,)).fetchall()
            stats["recent_user_msgs"] = [r["content"][:120] for r in recent]
        except Exception:
            stats["recent_user_msgs"] = []

    fallback = (
        f"📊 *Servia daily summary — {yesterday.isoformat()}*\n\n"
        f"• Bookings: {stats['bookings']}\n"
        f"• New chats: {stats['chats']}\n"
        f"• Articles published: {stats['articles']}\n"
        f"• PWA installs: {stats['installs']}\n"
        f"• New referrals: {stats['referrals']}\n"
        f"• New reviews: {stats['reviews']}\n"
    )
    if not s.use_llm:
        return fallback
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=s.ANTHROPIC_API_KEY, timeout=20, max_retries=1)
        msg = client.messages.create(
            model=s.MODEL, max_tokens=600,
            messages=[{"role":"user","content":(
                "You are the Servia operations bot. Write a 1-message WhatsApp summary "
                "for the founder/admin (max 800 characters). Be candid and direct — "
                "no fluff, no emoji overload. Highlight the 1-2 most important data "
                "points and give 1 actionable suggestion. Use 1 small emoji per "
                "bullet. Output plain WhatsApp-style text (no markdown, no headers).\n\n"
                f"Stats:\n{fallback}\n"
                f"Sample of last user chats: {stats.get('recent_user_msgs')}\n"
            )}],
        )
        return msg.content[0].text or fallback
    except Exception:
        return fallback


def push_daily_summary() -> dict:
    txt = daily_summary_text()
    return notify_admin_sync(txt, kind="daily_summary", urgency="normal")
