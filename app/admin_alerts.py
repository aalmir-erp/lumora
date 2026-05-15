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
    """Resolve the admin WhatsApp number. Priority order:
       1. db.cfg 'admin_wa_number'  (set via admin UI — runtime editable,
          no redeploy needed)
       2. ADMIN_WA_NUMBER env var   (set on Railway)
       3. Default                   (971523633995, the official number)

    v1.24.230 — Added DB-first lookup so the founder can change the
    target number from the admin UI without touching Railway env vars.
    """
    try:
        from . import db as _db
        v = (_db.cfg_get("admin_wa_number", "") or "").strip()
        if v:
            return v.lstrip("+").replace(" ", "").replace("-", "")
    except Exception: pass
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


def _push_admin(text: str) -> None:
    """v1.24.230 — Fan out to admin's web-push subscriptions when the
    WhatsApp bridge can't deliver (e.g. self-send case). Same phone,
    different transport — native push notification on the device."""
    try:
        from . import push_notifications as _pn
        payload = {
            "title": "Servia · admin",
            "body": (text or "")[:240],
            "kind": "manual_test",
            "url": "/admin#whatsapp",
            "requireInteraction": False,
        }
        _pn.send_to_all(payload, audience="all")
    except Exception as e:  # noqa: BLE001
        print(f"[admin_alerts] _push_admin failed: {e}", flush=True)


def reset_bridge_cooldown() -> None:
    """Clear the auto-degrade cooldown so the next send retries immediately.
    Called from /api/admin/whatsapp/reset-cooldown and automatically whenever
    a successful /status check confirms the bridge is healthy again."""
    global _BRIDGE_OUTAGE_UNTIL
    _BRIDGE_OUTAGE_UNTIL = 0.0


def get_bridge_cooldown_remaining() -> int:
    """Seconds remaining on the outage cooldown (0 if not active)."""
    import time as _t
    rem = int(_BRIDGE_OUTAGE_UNTIL - _t.time())
    return max(0, rem)


def _send_via_bridge(text: str, force: bool = False) -> tuple[bool, str | None]:
    """Send via WA bridge with graceful auto-degradation.

    v1.24.230 — IMPORTANT LIMITATION: WhatsApp does NOT let an account
    send a message to its own paired number (Meta-side protocol rule).
    That's the "No LID for user" error we kept hitting. If the admin
    number equals the bridge's paired number we DON'T even try the
    bridge — we send via Web Push instead (the admin's PWA subscription
    receives a native notification on the same phone). Real delivery,
    zero "No LID" errors.

    Bridge is still used for OUTBOUND messages to actual customers
    (different phone numbers) — those work fine.
    """
    import time as _t
    global _BRIDGE_OUTAGE_UNTIL
    s = get_settings()
    if not s.WA_BRIDGE_URL:
        return False, "WA_BRIDGE_URL not configured"
    now = _t.time()
    if not force and now < _BRIDGE_OUTAGE_UNTIL:
        rem = int(_BRIDGE_OUTAGE_UNTIL - now)
        return False, f"bridge in outage cooldown (auto-skipped, {rem}s remaining)"

    # v1.24.230 — Self-send guard. If ADMIN_WA_NUMBER == bridge's paired
    # number, WhatsApp will reject with "No LID for user" because you
    # can't WhatsApp yourself from the same account. Detect this case
    # BEFORE hitting the bridge and route via Web Push instead.
    try:
        import httpx as _httpx
        admin_digits = _admin_number()
        # Cheap /status check to learn the paired number
        rs = _httpx.get(
            s.WA_BRIDGE_URL.rstrip("/") + "/status",
            headers={"Authorization": f"Bearer {s.WA_BRIDGE_TOKEN}"},
            timeout=3,
        )
        if rs.is_success:
            j = rs.json()
            paired = (j.get("paired_number") or "").lstrip("+").replace(" ", "")
            if paired and admin_digits and paired == admin_digits:
                # Route via web push only — bridge can't deliver self-sends
                _push_admin(text)
                return True, "delivered_via_web_push_self_send_protected"
    except Exception:
        # Fall through to the regular bridge attempt
        pass
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
            # v1.24.230 — If bridge says "No LID for user" we can NEVER
            # deliver this via WhatsApp (Meta-side protocol limit). Fall
            # back to web push so the admin still hears about the alert.
            err_body = r.text[:200]
            if "No LID" in err_body or "no lid" in err_body.lower():
                _push_admin(text)
                _BRIDGE_OUTAGE_UNTIL = 0.0  # not a real outage
                return True, f"delivered_via_web_push (WA self-send blocked: {err_body[:80]})"
            return False, f"bridge {r.status_code}: {err_body}"
        # Successful send → clear any prior cooldown so next call doesn't
        # get auto-skipped because of a stale outage timestamp.
        _BRIDGE_OUTAGE_UNTIL = 0.0
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
                      urgency: str = "normal", meta: dict | None = None,
                      force: bool = False) -> dict:
    """Synchronous version — used by admin UI 'send test' so we can return
    the actual delivery result.

    v1.24.224 — `force=True` bypasses the outage cooldown so explicit admin
    actions (manual test send, fire-now daily summary) always actually try
    instead of being auto-skipped after a transient bridge outage. Manual
    test buttons default to force=True; background callers stay default
    (False) so they respect the cooldown."""
    # Explicit user-triggered kinds always bypass cooldown.
    if kind in ("manual_test", "fire_now") or urgency == "critical":
        force = True
    ok, err = _send_via_bridge(text, force=force)
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
