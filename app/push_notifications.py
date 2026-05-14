"""Web Push (VAPID) for admin PWA notifications.

End-to-end:
- Server generates VAPID keypair on first call (stored in db.cfg)
- Browser fetches public key, registers subscription (PushManager.subscribe)
- Admin POSTs the subscription JSON → /api/admin/push/subscribe
- When admin_alerts.notify_admin() fires → push module sends payload to
  every saved subscription with custom vibration/icon/actions
- Subscriptions that return 410 Gone are auto-pruned

Pure server-side push so the admin's phone gets a notification even when
the admin tab is closed.
"""
from __future__ import annotations
import base64
import datetime as _dt
import json as _json
import os
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from . import db
from .auth import require_admin


router = APIRouter(prefix="/api/admin/push", tags=["admin-push"],
                   dependencies=[Depends(require_admin)])

# Public router (no auth) — exposes the VAPID public key for the browser
public_router = APIRouter(prefix="/api/push", tags=["public-push"])


# ---------- VAPID key management ----------
def _ensure_vapid_keys() -> dict:
    """Generate VAPID keypair on first call, return current keys."""
    keys = db.cfg_get("vapid_keys", None)
    if keys and keys.get("public") and keys.get("private"):
        return keys
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        priv = ec.generate_private_key(ec.SECP256R1())
        priv_pem = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        # Public key — uncompressed point, 65 bytes (0x04 + 32 + 32)
        pub_numbers = priv.public_key().public_numbers()
        x = pub_numbers.x.to_bytes(32, "big")
        y = pub_numbers.y.to_bytes(32, "big")
        raw_pub = b"\x04" + x + y
        pub_b64 = base64.urlsafe_b64encode(raw_pub).decode().rstrip("=")
        keys = {"public": pub_b64, "private": priv_pem,
                "created_at": _dt.datetime.utcnow().isoformat() + "Z"}
        db.cfg_set("vapid_keys", keys)
    except Exception as e:  # noqa: BLE001
        print(f"[push] VAPID gen failed: {e}", flush=True)
        return {"public": "", "private": ""}
    return keys


def _ensure_table() -> None:
    with db.connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT UNIQUE,
                subscription_json TEXT,
                user_agent TEXT,
                created_at TEXT,
                last_sent_at TEXT,
                last_error TEXT
            )""")


def vapid_public_key() -> str:
    return _ensure_vapid_keys().get("public", "")


# ---------- Public: serve VAPID public key ----------
@public_router.get("/vapid-key")
def public_vapid_key():
    """Browser fetches this to register a push subscription."""
    return {"public_key": vapid_public_key()}


# ---------- Subscribe / unsubscribe ----------
class SubscriptionBody(BaseModel):
    endpoint: str
    keys: dict[str, str]
    expirationTime: Any = None


# v1.24.205 — Customer-side push subscribe (no admin auth required).
# Used by the website / TWA when a customer-facing page calls
# window.serviaEnablePush() in app.js after granting notification
# permission. Without this endpoint the TWA never registered any
# subscriptions — founder reported "install time it didn't ask
# about any notifications permissions".
@public_router.post("/subscribe")
def public_subscribe(body: SubscriptionBody, request: Request):
    _ensure_table()
    sub_json = _json.dumps({
        "endpoint": body.endpoint,
        "keys": body.keys,
        "expirationTime": body.expirationTime,
    })
    ua = (request.headers.get("user-agent") or "")[:200]
    now = _dt.datetime.utcnow().isoformat() + "Z"
    with db.connect() as c:
        c.execute(
            "INSERT INTO push_subscriptions(endpoint, subscription_json, user_agent, created_at) "
            "VALUES(?,?,?,?) "
            "ON CONFLICT(endpoint) DO UPDATE SET "
            "subscription_json=excluded.subscription_json, user_agent=excluded.user_agent",
            (body.endpoint, sub_json, ua, now))
    return {"ok": True}


@router.post("/subscribe")
def subscribe(body: SubscriptionBody, request: Request):
    """Admin browser registers a push subscription."""
    _ensure_table()
    sub_json = _json.dumps({
        "endpoint": body.endpoint,
        "keys": body.keys,
        "expirationTime": body.expirationTime,
    })
    ua = (request.headers.get("user-agent") or "")[:200]
    now = _dt.datetime.utcnow().isoformat() + "Z"
    with db.connect() as c:
        c.execute(
            "INSERT INTO push_subscriptions(endpoint, subscription_json, user_agent, created_at) "
            "VALUES(?,?,?,?) "
            "ON CONFLICT(endpoint) DO UPDATE SET "
            "subscription_json=excluded.subscription_json, user_agent=excluded.user_agent",
            (body.endpoint, sub_json, ua, now))
    return {"ok": True}


@router.post("/unsubscribe")
def unsubscribe(body: SubscriptionBody):
    _ensure_table()
    with db.connect() as c:
        n = c.execute("DELETE FROM push_subscriptions WHERE endpoint=?",
                      (body.endpoint,)).rowcount
    return {"ok": True, "deleted": n}


@router.get("/subscribers/summary")
def subscribers_summary():
    """Quick audience summary for the admin push composer:
    total subscribers, how many are linked to a customer, how many to a
    vendor, how many anonymous."""
    _ensure_table()
    with db.connect() as c:
        for stmt in (
            "ALTER TABLE push_subscriptions ADD COLUMN customer_id INTEGER",
            "ALTER TABLE push_subscriptions ADD COLUMN vendor_id INTEGER",
        ):
            try: c.execute(stmt)
            except Exception: pass
        total = c.execute("SELECT COUNT(*) AS n FROM push_subscriptions").fetchone()["n"]
        cust  = c.execute("SELECT COUNT(*) AS n FROM push_subscriptions WHERE customer_id IS NOT NULL").fetchone()["n"]
        vend  = c.execute("SELECT COUNT(*) AS n FROM push_subscriptions WHERE vendor_id IS NOT NULL").fetchone()["n"]
        logged = c.execute("SELECT COUNT(*) AS n FROM push_subscriptions WHERE customer_id IS NOT NULL OR vendor_id IS NOT NULL").fetchone()["n"]
    return {"total": total, "customers": cust, "vendors": vend,
            "logged_in": logged, "anonymous": total - logged}


@router.get("/list")
def list_subs():
    _ensure_table()
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, endpoint, user_agent, created_at, last_sent_at, last_error "
            "FROM push_subscriptions ORDER BY id DESC").fetchall()
    return {"subscriptions": [dict(r) for r in rows], "count": len(rows)}


@router.delete("/subscriptions/all")
def prune_all_subscriptions():
    """Delete ALL push subscriptions so devices re-register fresh on next visit.
    Use this after a VAPID key rotation or format change that invalidated
    existing subscriptions."""
    _ensure_table()
    with db.connect() as c:
        n = c.execute("DELETE FROM push_subscriptions").rowcount
    print(f"[push] admin pruned all {n} push subscriptions", flush=True)
    return {"ok": True, "deleted": n}


@router.post("/test")
def send_test():
    """Send a test notification to all subscribed devices."""
    # v1.24.205 — send_to_all() returns a DICT
    # {sent,pruned,failed,matched,errors}; the previous code returned
    # the whole dict under the 'sent' key, so the admin UI rendered
    # "Test sent to [object Object] device(s)" instead of a count.
    result = send_to_all({
        "title": "✅ Servia push working",
        "body": "If you see this, your admin PWA is fully wired for live alerts.",
        "kind": "test",
    })
    return {"ok": True,
            "sent": result.get("sent", 0),
            "pruned": result.get("pruned", 0),
            "failed": result.get("failed", 0),
            "matched": result.get("matched", 0),
            "errors": result.get("errors", [])}


# ---------- Broadcast a custom-styled notification ----------
class BroadcastBody(BaseModel):
    title: str
    body: str
    icon: str | None = None        # URL to small icon (default /icon-192.svg)
    image: str | None = None       # large image URL for richer notifications
    url: str | None = None         # tap-target URL ("/me.html", etc)
    kind: str | None = None        # arbitrary tag (powers vibration pattern in sw.js)
    audience: str = "all"          # "all" | "customers" | "vendors" | "logged_in"
    require_interaction: bool = False  # stick around until user dismisses


@router.post("/broadcast")
def broadcast(body: BroadcastBody):
    """Send a styled push notification to a chosen audience. Admin-only.
    The audience filter is best-effort — push subscriptions are stored
    by user_agent + customer_id (when known), so 'customers' = all subs
    with a non-null customer_id, 'logged_in' = same, etc."""
    payload = {
        "title": body.title.strip()[:120] or "Servia",
        "body": (body.body or "").strip()[:300],
        "kind": body.kind or "broadcast",
    }
    if body.icon: payload["icon"] = body.icon
    if body.image: payload["image"] = body.image
    if body.url: payload["url"] = body.url
    if body.require_interaction: payload["requireInteraction"] = True

    # Audience filter — passes through to send_to_all which queries
    # push_subscriptions filtered by linked customer/vendor.
    result = send_to_all(payload, audience=body.audience or "all", filters=getattr(body, 'filters', None))
    return {"ok": True, "audience": body.audience or "all", **result}


# ---------- Send a payload to all subscribers ----------
def send_to_all(payload: dict, audience: str = "all", filters: dict | None = None) -> dict:
    """Sends `payload` (dict — title/body/kind/etc.) to subscribers in the
    selected `audience` ('all' | 'customers' | 'vendors' | 'logged_in').
    Returns count of successful deliveries. Auto-prunes 410-Gone subscribers.

    Audience filter rationale:
      - 'all'        — every push subscription
      - 'customers'  — subscriptions linked to a customer record
      - 'vendors'    — subscriptions linked to a vendor record
      - 'logged_in'  — any subscription with a non-null linked user
    The push_subscriptions table has columns customer_id + vendor_id that
    are populated when the user is logged in at subscribe time."""
    keys = _ensure_vapid_keys()
    if not keys.get("private"):
        print("[push] no VAPID keys — call /api/admin/push/test once to generate", flush=True)
        return {"sent": 0, "pruned": 0, "failed": 0, "matched": 0,
                "errors": ["VAPID keys not configured. Generate them via /api/admin/push/test."]}
    _ensure_table()
    try:
        from pywebpush import webpush, WebPushException
    except Exception:
        print("[push] pywebpush not installed — skipping push send", flush=True)
        return {"sent": 0, "pruned": 0, "failed": 0, "matched": 0,
                "errors": ["pywebpush library missing on the server. pip install pywebpush"]}
    # pywebpush calls py_vapid's Vapid.from_string() which does NOT parse PEM —
    # it strips newlines from the whole input (header+body+footer) and tries to
    # base64-decode the garbage, producing ASN.1 parse errors. We need to give it
    # either a Vapid object OR a base64url-encoded 32-byte raw EC scalar.
    # Extract the raw scalar from our stored PKCS8 PEM and base64url-encode it.
    priv_key_str = keys["private"]
    if priv_key_str.strip().startswith("-----BEGIN"):
        try:
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            _priv_obj = load_pem_private_key(priv_key_str.encode(), password=None)
            _raw = _priv_obj.private_numbers().private_value.to_bytes(32, "big")
            priv_key_str = base64.urlsafe_b64encode(_raw).rstrip(b"=").decode()
            print(f"[push] converted PEM → raw b64url scalar ({len(priv_key_str)} chars) for pywebpush", flush=True)
        except Exception as _e:
            print(f"[push] key format conversion error: {_e}", flush=True)
    # Build the WHERE clause for audience filtering. v1.22.88 expanded
    # to support a granular `filters` object: location/language/booking/...
    where_parts: list[str] = []
    params: list = []
    if audience == "customers":
        where_parts.append("customer_id IS NOT NULL")
    elif audience == "vendors":
        where_parts.append("vendor_id IS NOT NULL")
    elif audience == "logged_in":
        where_parts.append("(customer_id IS NOT NULL OR vendor_id IS NOT NULL)")
    elif audience == "anonymous":
        where_parts.append("customer_id IS NULL AND vendor_id IS NULL")
    # Per-feature filters (each one ANDs with audience)
    f = filters or {}
    if f.get("emirate"):
        where_parts.append("(emirate = ? OR emirate IS NULL)")
        params.append(f["emirate"])
    if f.get("language"):
        where_parts.append("(language = ? OR language IS NULL)")
        params.append(f["language"])
    if f.get("subscribed_within_days"):
        try:
            days = int(f["subscribed_within_days"])
            cutoff = (_dt.datetime.utcnow() - _dt.timedelta(days=days)).isoformat() + "Z"
            where_parts.append("created_at >= ?")
            params.append(cutoff)
        except Exception: pass
    if f.get("only_installed_app"):
        # TWAs identify themselves with "TWA" in the user_agent header
        # (Bubblewrap injects "wv" + display-mode standalone hints).
        where_parts.append("(user_agent LIKE '%; wv)%' OR user_agent LIKE '%TWA%' OR user_agent LIKE '%Servia%')")
    where = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
    with db.connect() as c:
        # Idempotent migrations for the new columns we filter on
        for stmt in (
            "ALTER TABLE push_subscriptions ADD COLUMN customer_id INTEGER",
            "ALTER TABLE push_subscriptions ADD COLUMN vendor_id INTEGER",
            "ALTER TABLE push_subscriptions ADD COLUMN emirate TEXT",
            "ALTER TABLE push_subscriptions ADD COLUMN language TEXT",
        ):
            try: c.execute(stmt)
            except Exception: pass
        rows = c.execute(
            f"SELECT id, endpoint, subscription_json FROM push_subscriptions{where}", params).fetchall()
    print(f"[push] sending '{payload.get('title','?')[:50]}' to {len(rows)} sub(s) "
          f"(audience={audience})", flush=True)
    n_ok = 0
    pruned: list[int] = []
    failed_errors: list[str] = []
    vapid_claims = {"sub": "mailto:" + os.getenv("ADMIN_EMAIL", "admin@servia.ae")}
    for r in rows:
        try:
            sub = _json.loads(r["subscription_json"])
            webpush(
                subscription_info=sub,
                data=_json.dumps(payload),
                vapid_private_key=priv_key_str,
                vapid_claims=vapid_claims,
                ttl=86400,
            )
            n_ok += 1
            with db.connect() as c:
                c.execute("UPDATE push_subscriptions SET last_sent_at=?, last_error=NULL WHERE id=?",
                          (_dt.datetime.utcnow().isoformat() + "Z", r["id"]))
        except WebPushException as e:
            err = str(e)[:300]
            # 410 Gone or 404 → subscription expired/revoked → prune
            if "410" in err or "404" in err:
                pruned.append(r["id"])
                failed_errors.append(f"sub#{r['id']}: 410 Gone (browser unregistered) — pruned")
            else:
                with db.connect() as c:
                    c.execute("UPDATE push_subscriptions SET last_error=? WHERE id=?",
                              (err, r["id"]))
                failed_errors.append(f"sub#{r['id']}: {err[:120]}")
        except Exception as e:  # noqa: BLE001
            print(f"[push] send error: {e}", flush=True)
            failed_errors.append(f"sub#{r['id']}: {type(e).__name__}: {str(e)[:120]}")
    if pruned:
        with db.connect() as c:
            c.execute(f"DELETE FROM push_subscriptions WHERE id IN ({','.join('?'*len(pruned))})",
                      pruned)
        print(f"[push] pruned {len(pruned)} expired subscriptions", flush=True)
    return {
        "sent": n_ok,
        "pruned": len(pruned),
        "failed": len(failed_errors),
        "matched": len(rows),
        "errors": failed_errors[:30],   # cap so admin doesn't get a 1MB JSON
    }


# ---------------------------------------------------------------------------
def send_to_phone(phone: str | None, *, title: str, body: str,
                  url: str | None = None, kind: str = "info") -> dict:
    """Convenience helper: send a push to all subscriptions tied to a phone.
    No-ops if phone is missing or no subs found. Used by quote status updates."""
    if not phone:
        return {"sent": 0, "matched": 0}
    payload = {"title": title, "body": body, "kind": kind, "url": url or "/"}
    audience = {"phone": phone}
    try:
        return broadcast(payload, audience)
    except NameError:
        # `broadcast()` may not be defined in older versions; fall back to a
        # direct send to all subs.
        return _send_all(payload)


def _send_all(payload: dict) -> dict:
    """Final fallback: send to all subscriptions ignoring audience."""
    keys = _ensure_vapid_keys()
    if not keys: return {"sent": 0}
    priv_key_str = keys.get("private", "")
    if priv_key_str.strip().startswith("-----BEGIN"):
        try:
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            _po = load_pem_private_key(priv_key_str.encode(), password=None)
            _raw = _po.private_numbers().private_value.to_bytes(32, "big")
            priv_key_str = base64.urlsafe_b64encode(_raw).rstrip(b"=").decode()
        except Exception: pass
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, endpoint, subscription_json FROM push_subscriptions"
        ).fetchall()
    n = 0
    vapid_claims = {"sub": "mailto:" + os.getenv("ADMIN_EMAIL", "admin@servia.ae")}
    for r in rows:
        try:
            sub = _json.loads(r["subscription_json"])
            webpush(subscription_info=sub, data=_json.dumps(payload),
                    vapid_private_key=priv_key_str, vapid_claims=vapid_claims, ttl=86400)
            n += 1
        except Exception:
            pass
    return {"sent": n, "matched": len(rows)}
