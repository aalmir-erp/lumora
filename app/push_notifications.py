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


@router.get("/list")
def list_subs():
    _ensure_table()
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, endpoint, user_agent, created_at, last_sent_at, last_error "
            "FROM push_subscriptions ORDER BY id DESC").fetchall()
    return {"subscriptions": [dict(r) for r in rows], "count": len(rows)}


@router.post("/test")
def send_test():
    """Send a test notification to all subscribed devices."""
    n_sent = send_to_all({
        "title": "✅ Servia push working",
        "body": "If you see this, your admin PWA is fully wired for live alerts.",
        "kind": "test",
    })
    return {"ok": True, "sent": n_sent}


# ---------- Send a payload to all subscribers ----------
def send_to_all(payload: dict) -> int:
    """Sends `payload` (dict — title/body/kind/etc.) to every subscription.
    Returns count of successful deliveries. Auto-prunes 410-Gone subscribers."""
    keys = _ensure_vapid_keys()
    if not keys.get("private"):
        return 0
    _ensure_table()
    try:
        from pywebpush import webpush, WebPushException
    except Exception:
        print("[push] pywebpush not installed — skipping push send", flush=True)
        return 0
    with db.connect() as c:
        rows = c.execute("SELECT id, endpoint, subscription_json FROM push_subscriptions").fetchall()
    n_ok = 0
    pruned: list[int] = []
    vapid_claims = {"sub": "mailto:" + os.getenv("ADMIN_EMAIL", "admin@servia.ae")}
    for r in rows:
        try:
            sub = _json.loads(r["subscription_json"])
            webpush(
                subscription_info=sub,
                data=_json.dumps(payload),
                vapid_private_key=keys["private"],
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
            else:
                with db.connect() as c:
                    c.execute("UPDATE push_subscriptions SET last_error=? WHERE id=?",
                              (err, r["id"]))
        except Exception as e:  # noqa: BLE001
            print(f"[push] send error: {e}", flush=True)
    if pruned:
        with db.connect() as c:
            c.execute(f"DELETE FROM push_subscriptions WHERE id IN ({','.join('?'*len(pruned))})",
                      pruned)
        print(f"[push] pruned {len(pruned)} expired subscriptions", flush=True)
    return n_ok
