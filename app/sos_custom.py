"""Customer-defined SOS shortcut buttons (v1.24.15).

A user can save a fully-pre-configured one-tap dispatch:
  e.g. "🛞 My Marina flat tyre" → service_id=vehicle_recovery, issue=flat_tyre,
  lat/lng=Marina Pinnacle, building=…, notes="bring jack", photo_url=…

Each button gets:
  · A unique nfc_slug (URL-safe random string) used for the public
    /csos/<slug> dispatch URL — write it to an NFC tag, embed in voice
    routines (IFTTT / Google Home), use as a Wear shortcut, etc.
  · Per-button payment preference: "wallet" (use Servia wallet, fall
    back to standard payment if balance insufficient) or "ask" (always
    ask at booking time using stored cards).
  · Optional pin_required flag — if true, dispatching requires the
    customer's account-level PIN before truck is dispatched. Prevents
    accidental triggers (e.g. friend tapping the NFC tag).
  · Live stats: tap_count + last_tap_at + a per-tap log row in
    custom_sos_taps for full history (date · service · vendor · status).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import hmac
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from . import db, recovery
from .auth_users import lookup_session, current_customer


router = APIRouter()
public_router = APIRouter()  # no /api prefix — for /csos/<slug>

_SLUG_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"  # no l/o/0/1


def _new_slug(n: int = 12) -> str:
    return "".join(secrets.choice(_SLUG_ALPHABET) for _ in range(n))


# ---------------------------------------------------------------------------
def _ensure_schema() -> None:
    with db.connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS custom_sos_buttons (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                label       TEXT NOT NULL,
                emoji       TEXT,
                color       TEXT,
                service_id  TEXT NOT NULL,
                sub_option  TEXT,
                lat         REAL,
                lng         REAL,
                address     TEXT,
                building    TEXT,
                flat        TEXT,
                notes       TEXT,
                photo_url   TEXT,
                sort_order  INTEGER DEFAULT 0,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_custom_sos_cust "
                  "ON custom_sos_buttons(customer_id)")
        # v1.24.15 — additive columns (idempotent).
        for ddl in (
            "ALTER TABLE custom_sos_buttons ADD COLUMN payment_method TEXT DEFAULT 'ask'",
            "ALTER TABLE custom_sos_buttons ADD COLUMN pin_required INTEGER DEFAULT 0",
            "ALTER TABLE custom_sos_buttons ADD COLUMN nfc_slug TEXT",
            "ALTER TABLE custom_sos_buttons ADD COLUMN tap_count INTEGER DEFAULT 0",
            "ALTER TABLE custom_sos_buttons ADD COLUMN last_tap_at TEXT",
        ):
            try: c.execute(ddl)
            except Exception: pass
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_sos_slug "
                  "ON custom_sos_buttons(nfc_slug) WHERE nfc_slug IS NOT NULL")
        # Per-tap log
        c.execute("""
            CREATE TABLE IF NOT EXISTS custom_sos_taps (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                button_id   INTEGER NOT NULL,
                customer_id INTEGER,
                booking_id  TEXT,
                source      TEXT,
                outcome     TEXT,
                ts          TEXT NOT NULL,
                FOREIGN KEY (button_id) REFERENCES custom_sos_buttons(id) ON DELETE CASCADE
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_custom_sos_taps_btn "
                  "ON custom_sos_taps(button_id)")
        # Customer PIN (one PIN per customer, scrypt-hashed)
        for ddl in (
            "ALTER TABLE customers ADD COLUMN sos_pin_hash TEXT",
            "ALTER TABLE customers ADD COLUMN sos_pin_lockout_until TEXT",
            "ALTER TABLE customers ADD COLUMN sos_pin_failed_count INTEGER DEFAULT 0",
        ):
            try:
                with db.connect() as cc: cc.execute(ddl)
            except Exception: pass


def _now() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


def _hash_pin(pin: str) -> str:
    salt = secrets.token_bytes(12)
    h = hashlib.scrypt(pin.strip().lower().encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${h.hex()}"


def _verify_pin(pin: str, stored: str) -> bool:
    try:
        algo, salt_hex, hash_hex = stored.split("$", 2)
        if algo != "scrypt": return False
        salt = bytes.fromhex(salt_hex); expect = bytes.fromhex(hash_hex)
        actual = hashlib.scrypt(pin.strip().lower().encode(), salt=salt,
                                n=2**14, r=8, p=1, dklen=32)
        return hmac.compare_digest(actual, expect)
    except Exception:
        return False


# ---------------------------------------------------------------------------
class _CustomSosBody(BaseModel):
    label:          str = Field(..., min_length=1, max_length=60)
    emoji:          Optional[str] = "🆘"
    color:          Optional[str] = "#DC2626"
    service_id:     str
    sub_option:     Optional[str] = None
    lat:            Optional[float] = None
    lng:            Optional[float] = None
    address:        Optional[str] = None
    building:       Optional[str] = None
    flat:           Optional[str] = None
    notes:          Optional[str] = None
    photo_url:      Optional[str] = None
    sort_order:     Optional[int] = 0
    payment_method: Optional[str] = "ask"   # 'wallet' | 'ask'
    pin_required:   Optional[bool] = False


@router.post("/api/sos/custom")
def create_custom(body: _CustomSosBody,
                   user = Depends(current_customer)):
    _ensure_schema()
    slug = _new_slug()
    # Tiny collision check (the unique index would also catch it)
    with db.connect() as c:
        for _ in range(5):
            exists = c.execute("SELECT id FROM custom_sos_buttons WHERE nfc_slug=?",
                               (slug,)).fetchone()
            if not exists: break
            slug = _new_slug()
        cur = c.execute(
            "INSERT INTO custom_sos_buttons(customer_id, label, emoji, color, service_id, "
            "sub_option, lat, lng, address, building, flat, notes, photo_url, sort_order, "
            "payment_method, pin_required, nfc_slug, created_at, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (user.user_id, body.label, body.emoji or "🆘", body.color or "#DC2626",
             body.service_id, body.sub_option, body.lat, body.lng, body.address,
             body.building, body.flat, body.notes, body.photo_url,
             body.sort_order or 0,
             body.payment_method or "ask",
             1 if body.pin_required else 0,
             slug, _now(), _now())
        )
        bid = cur.lastrowid
        row = c.execute("SELECT * FROM custom_sos_buttons WHERE id=?", (bid,)).fetchone()
    db.log_event("sos_custom", str(bid), "created",
                 actor=str(user.user_id),
                 details={"label": body.label, "service_id": body.service_id,
                          "slug": slug})
    return {"ok": True, "button": dict(row),
            "share_url": f"https://servia.ae/csos/{slug}"}


@router.get("/api/sos/custom/me")
def list_mine(user = Depends(current_customer)):
    _ensure_schema()
    with db.connect() as c:
        rows = c.execute(
            "SELECT * FROM custom_sos_buttons WHERE customer_id=? "
            "ORDER BY sort_order ASC, id ASC",
            (user.user_id,)
        ).fetchall()
    return {"items": [dict(r) for r in rows], "count": len(rows)}


@router.get("/api/sos/custom/{btn_id}/taps")
def my_button_taps(btn_id: int, user = Depends(current_customer), limit: int = 50):
    """Per-button tap history — date, service, vendor, status, booking_id."""
    _ensure_schema()
    with db.connect() as c:
        owned = c.execute(
            "SELECT id FROM custom_sos_buttons WHERE id=? AND customer_id=?",
            (btn_id, user.user_id)
        ).fetchone()
        if not owned:
            raise HTTPException(404, "button not found")
        rows = c.execute(
            "SELECT t.*, b.service_id AS booking_service, b.status AS booking_status, "
            "       b.estimated_total AS amount, "
            "       a.vendor_id AS vendor_id, v.name AS vendor_name "
            "FROM custom_sos_taps t "
            "LEFT JOIN bookings b    ON b.id = t.booking_id "
            "LEFT JOIN assignments a ON a.booking_id = t.booking_id "
            "LEFT JOIN vendors v     ON v.id = a.vendor_id "
            "WHERE t.button_id=? ORDER BY t.id DESC LIMIT ?",
            (btn_id, limit)
        ).fetchall()
    return {"items": [dict(r) for r in rows], "count": len(rows)}


@router.put("/api/sos/custom/{btn_id}")
def update_custom(btn_id: int, body: _CustomSosBody,
                   user = Depends(current_customer)):
    _ensure_schema()
    with db.connect() as c:
        owned = c.execute(
            "SELECT id FROM custom_sos_buttons WHERE id=? AND customer_id=?",
            (btn_id, user.user_id)
        ).fetchone()
        if not owned:
            raise HTTPException(404, "button not found")
        c.execute(
            "UPDATE custom_sos_buttons SET label=?, emoji=?, color=?, service_id=?, "
            "sub_option=?, lat=?, lng=?, address=?, building=?, flat=?, notes=?, "
            "photo_url=?, sort_order=?, payment_method=?, pin_required=?, updated_at=? "
            "WHERE id=?",
            (body.label, body.emoji or "🆘", body.color or "#DC2626", body.service_id,
             body.sub_option, body.lat, body.lng, body.address, body.building,
             body.flat, body.notes, body.photo_url, body.sort_order or 0,
             body.payment_method or "ask",
             1 if body.pin_required else 0,
             _now(), btn_id)
        )
        row = c.execute("SELECT * FROM custom_sos_buttons WHERE id=?", (btn_id,)).fetchone()
    return {"ok": True, "button": dict(row)}


@router.delete("/api/sos/custom/{btn_id}")
def delete_custom(btn_id: int, user = Depends(current_customer)):
    _ensure_schema()
    with db.connect() as c:
        n = c.execute(
            "DELETE FROM custom_sos_buttons WHERE id=? AND customer_id=?",
            (btn_id, user.user_id)
        ).rowcount
    if not n:
        raise HTTPException(404, "button not found")
    return {"ok": True, "deleted": btn_id}


# ---------------------------------------------------------------------------
# Customer PIN (set / change / verify-and-dispatch)
# ---------------------------------------------------------------------------
class _PinSetBody(BaseModel):
    pin: str = Field(..., min_length=4, max_length=12)
    old_pin: Optional[str] = None       # required if a pin already exists


@router.post("/api/auth/customer/pin")
def set_customer_pin(body: _PinSetBody, user = Depends(current_customer)):
    """Set or change the customer's account-level SOS PIN.

    PIN is hashed (scrypt) — we never store plaintext. Used per-button via
    pin_required flag. 6 alphanumeric chars recommended (UI hint), but we
    accept 4-12 to keep the door open for shorter PINs if user prefers.
    """
    _ensure_schema()
    pin = (body.pin or "").strip()
    if not pin or len(pin) < 4:
        raise HTTPException(400, "PIN must be 4-12 characters")
    if not pin.isalnum():
        raise HTTPException(400, "PIN must be alphanumeric (a-z 0-9)")
    with db.connect() as c:
        cur = c.execute(
            "SELECT sos_pin_hash FROM customers WHERE id=?", (user.user_id,)
        ).fetchone()
        existing = cur and cur["sos_pin_hash"]
        if existing and not body.old_pin:
            raise HTTPException(400, "Provide your current PIN as old_pin to change")
        if existing and not _verify_pin(body.old_pin or "", existing):
            raise HTTPException(403, "Current PIN is incorrect")
        c.execute(
            "UPDATE customers SET sos_pin_hash=?, sos_pin_failed_count=0, "
            "sos_pin_lockout_until=NULL WHERE id=?",
            (_hash_pin(pin), user.user_id)
        )
    db.log_event("auth", str(user.user_id), "sos_pin_set")
    return {"ok": True}


@router.delete("/api/auth/customer/pin")
def clear_customer_pin(body: _PinSetBody, user = Depends(current_customer)):
    """Remove the customer's PIN entirely. Requires confirming the old PIN."""
    _ensure_schema()
    with db.connect() as c:
        row = c.execute(
            "SELECT sos_pin_hash FROM customers WHERE id=?", (user.user_id,)
        ).fetchone()
        if not row or not row["sos_pin_hash"]:
            return {"ok": True, "had_pin": False}
        if not _verify_pin(body.old_pin or "", row["sos_pin_hash"]):
            raise HTTPException(403, "PIN incorrect")
        c.execute(
            "UPDATE customers SET sos_pin_hash=NULL, sos_pin_failed_count=0, "
            "sos_pin_lockout_until=NULL WHERE id=?",
            (user.user_id,)
        )
    return {"ok": True}


@router.get("/api/auth/customer/pin/status")
def pin_status(user = Depends(current_customer)):
    _ensure_schema()
    with db.connect() as c:
        row = c.execute(
            "SELECT sos_pin_hash, sos_pin_lockout_until FROM customers WHERE id=?",
            (user.user_id,)
        ).fetchone()
    has_pin = bool(row and row["sos_pin_hash"])
    locked = False
    if row and row["sos_pin_lockout_until"]:
        locked = row["sos_pin_lockout_until"] > _now()
    return {"has_pin": has_pin, "locked": locked,
            "lockout_until": row["sos_pin_lockout_until"] if locked else None}


# ---------------------------------------------------------------------------
# Public slug-based dispatch  +  authenticated dispatch with optional PIN
# ---------------------------------------------------------------------------
class _DispatchBody(BaseModel):
    pin: Optional[str] = None


def _verify_pin_or_lock(c, customer_id: int, pin: str) -> tuple[bool, str | None]:
    row = c.execute(
        "SELECT sos_pin_hash, sos_pin_lockout_until, sos_pin_failed_count "
        "FROM customers WHERE id=?", (customer_id,)
    ).fetchone()
    if not row or not row["sos_pin_hash"]:
        return True, None  # no pin set — fail open (button.pin_required already false)
    if row["sos_pin_lockout_until"] and row["sos_pin_lockout_until"] > _now():
        return False, f"Locked out until {row['sos_pin_lockout_until']}"
    if not pin:
        return False, "PIN required"
    if _verify_pin(pin, row["sos_pin_hash"]):
        c.execute("UPDATE customers SET sos_pin_failed_count=0 WHERE id=?", (customer_id,))
        return True, None
    failed = (row["sos_pin_failed_count"] or 0) + 1
    if failed >= 3:
        lockout = (_dt.datetime.utcnow() + _dt.timedelta(minutes=5)).isoformat() + "Z"
        c.execute(
            "UPDATE customers SET sos_pin_failed_count=0, sos_pin_lockout_until=? "
            "WHERE id=?", (lockout, customer_id)
        )
        return False, "Wrong PIN — locked out for 5 minutes."
    c.execute("UPDATE customers SET sos_pin_failed_count=? WHERE id=?",
              (failed, customer_id))
    return False, f"Wrong PIN — {3 - failed} attempts left."


@router.post("/api/sos/custom/{btn_id}/dispatch")
def dispatch_custom(btn_id: int, body: _DispatchBody, request: Request,
                     authorization: str = Header(default="")):
    """Authenticated one-tap dispatch. Auto-handles wallet payment + PIN check."""
    _ensure_schema()
    user = lookup_session(_bearer(authorization))
    if not user or user.user_type != "customer":
        raise HTTPException(401, "customer login required")
    return _do_dispatch(btn_id, user.user_id, user.record, body.pin or "",
                         request, authorization, source="custom_sos")


@public_router.get("/csos/{slug}")
def slug_landing(slug: str, request: Request):
    """Public landing for an NFC-tap or shortcut hit. The slug alone doesn't
    auto-dispatch — we 302 to /sos.html?csos=<slug> so the web app can:
      1. Confirm the user is the owner (via stored token), and
      2. Prompt for PIN if the button requires it, and
      3. Show payment-method confirmation, before firing.
    """
    _ensure_schema()
    with db.connect() as c:
        row = c.execute(
            "SELECT id FROM custom_sos_buttons WHERE nfc_slug=?", (slug,)
        ).fetchone()
    if not row:
        return RedirectResponse(f"/sos.html?csos_unknown={slug}", status_code=302)
    return RedirectResponse(f"/sos.html?csos={slug}", status_code=302)


@router.post("/api/sos/custom/by-slug/{slug}/dispatch")
def dispatch_by_slug(slug: str, body: _DispatchBody, request: Request,
                      authorization: str = Header(default="")):
    """Same as /custom/{id}/dispatch but looked up by the public slug.
    Authenticated — only the owner of the slug can dispatch it.
    """
    _ensure_schema()
    user = lookup_session(_bearer(authorization))
    if not user or user.user_type != "customer":
        raise HTTPException(401, "customer login required")
    with db.connect() as c:
        row = c.execute(
            "SELECT id, customer_id FROM custom_sos_buttons WHERE nfc_slug=?", (slug,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "shortcut not found")
    if row["customer_id"] != user.user_id:
        raise HTTPException(403, "this shortcut belongs to a different customer")
    return _do_dispatch(int(row["id"]), user.user_id, user.record, body.pin or "",
                         request, authorization, source="csos_slug")


def _do_dispatch(btn_id: int, customer_id: int, customer_rec: dict,
                 pin: str, request: Request, authorization: str, source: str):
    with db.connect() as c:
        row = c.execute(
            "SELECT * FROM custom_sos_buttons WHERE id=? AND customer_id=?",
            (btn_id, customer_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "button not found")
        if row["pin_required"]:
            ok, err = _verify_pin_or_lock(c, customer_id, pin)
            if not ok:
                raise HTTPException(403, err or "PIN incorrect")
        # Bump tap counters
        c.execute(
            "UPDATE custom_sos_buttons SET tap_count=COALESCE(tap_count,0)+1, "
            "last_tap_at=? WHERE id=?", (_now(), btn_id)
        )
    if row["lat"] is None or row["lng"] is None:
        raise HTTPException(400,
            "shortcut has no location — edit it and pin a spot first")
    addr_bits = []
    if row["building"]: addr_bits.append(row["building"])
    if row["flat"]:     addr_bits.append(row["flat"])
    if row["address"]:  addr_bits.append(row["address"])
    addr_str = " · ".join(addr_bits) if addr_bits else None

    body = recovery.DispatchBody(
        lat=float(row["lat"]),
        lng=float(row["lng"]),
        accuracy_m=10.0,
        customer_phone=customer_rec.get("phone"),
        customer_email=customer_rec.get("email"),
        customer_name=customer_rec.get("name"),
        issue=row["sub_option"] or "sos",
        notes=(row["notes"] or "") + (" · " + addr_str if addr_str else ""),
        photo_url=row["photo_url"],
        service_id=row["service_id"] or "vehicle_recovery",
        source=source,
    )
    res = recovery.recovery_dispatch(body, request, authorization)
    # Log the tap with the resulting booking_id + outcome
    try:
        with db.connect() as c:
            c.execute(
                "INSERT INTO custom_sos_taps(button_id, customer_id, booking_id, "
                "source, outcome, ts) VALUES(?,?,?,?,?,?)",
                (btn_id, customer_id, res.get("booking_id"), source,
                 "dispatched" if res.get("ok") else "failed", _now())
            )
    except Exception:
        pass
    # v1.24.35 — fire a success push so phone + watch + admin all light up.
    # The watch's WearMessageListenerService catches /servia/booking_created
    # via its own path; here we use the cross-platform admin_alerts pipe so
    # web push subscribers (which include the customer's phone PWA, mirrored
    # to the watch) see it immediately. Best-effort, never blocks.
    try:
        from . import admin_alerts as _aa
        bk_id = res.get("booking_id", "")
        vendor = res.get("vendor") or {}
        eta = res.get("eta_min")
        _aa.notify_admin(
            f"✅ SOS dispatched · {row['label']}\n"
            f"Booking: {bk_id}\n"
            f"Vendor: {vendor.get('name', '?')}"
            + (f"\nETA: {eta}m" if eta else "")
            + f"\nSource: {source}",
            kind="booking_confirmed",
            urgency="urgent",
            meta={"booking_id": bk_id, "source": source,
                  "shortcut_label": row["label"]},
        )
    except Exception:
        pass
    # Surface payment_method preference on the response so the UI can
    # decide whether to charge wallet first or prompt standard payment.
    res["payment_method"] = row["payment_method"]
    return res


def _bearer(auth: str) -> str:
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""

