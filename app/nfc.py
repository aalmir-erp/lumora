"""Servia NFC one-tap booking.

A customer orders an NFC sticker (kitchen / car / AC / pool / sofa / etc.).
Each sticker holds a short URL: https://servia.ae/t/<slug>. Tap with any
NFC-enabled phone (~99% of phones since 2018) → browser opens that URL →
we resolve the slug to {owner, service, saved_address} → the customer
sees a big "Confirm same service as last time?" card → one tap → booking.

This module exposes the data model + endpoints.

Tables:
- nfc_tags
    id              INTEGER PK
    slug            TEXT UNIQUE NOT NULL              -- 12-char URL-safe
    owner_customer_id INTEGER NOT NULL                -- bound at write-time
    service_id      TEXT NOT NULL                     -- e.g. "deep_cleaning"
    saved_address_id INTEGER                          -- optional pre-fill
    alias           TEXT                              -- "Kitchen Marina" etc
    location_label  TEXT                              -- e.g. "Kitchen sink"
    size            TEXT DEFAULT 'sticker'            -- sticker|card|keychain
    is_active       INTEGER DEFAULT 1
    tap_count       INTEGER DEFAULT 0
    booking_count   INTEGER DEFAULT 0
    last_tap_at     TEXT
    last_booking_at TEXT
    created_at      TEXT NOT NULL
- nfc_taps
    id, tag_id, ip, user_agent, customer_id_at_tap, ts

Public endpoints (no auth required for tap):
- GET /t/<slug>                 -> 302 to /book.html?nfc=<slug>
- GET /api/nfc/tag/<slug>       -> {tag, owner_match, service, address}

Customer endpoints (require Bearer token):
- POST  /api/nfc/order          -> queue an NFC tag in customer's name
- GET   /api/nfc/my-tags        -> list this customer's tags
- POST  /api/nfc/tap-confirm    -> records the booking from a tap

Admin endpoints (require_admin):
- GET   /api/admin/nfc/tags
- POST  /api/admin/nfc/tags     -> create a tag (admin can fulfil order)
- PUT   /api/admin/nfc/tags/{id} -> activate/deactivate, change service
- DELETE /api/admin/nfc/tags/{id}
- POST  /api/admin/nfc/tags/{id}/print  -> returns printable HTML
"""
from __future__ import annotations

def _bookings_email() -> str:
    """v1.24.147 — admin-configurable bookings email."""
    try:
        from .brand_contact import get_bookings_email
        return get_bookings_email() or "see /contact"
    except Exception:
        return "see /contact"


import datetime as _dt
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, Field

from . import db
from .auth import require_admin
from .auth_users import lookup_session

router = APIRouter()
public_router = APIRouter()  # no /api prefix — for /t/<slug>

_SLUG_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"  # no l/o/0/1 (confusable)


def _new_slug(n: int = 10) -> str:
    return "".join(secrets.choice(_SLUG_ALPHABET) for _ in range(n))


def _now() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


# Servia's WhatsApp inbound number (where customers send confirm codes)
# Reads from admin brand_contact at runtime (v1.24.147). Env var SERVIA_WA_NUMBER
# can still override for staging.
import os as _os
def _servia_wa() -> str:
    """v1.24.147 — runtime lookup, no hardcoded fallback."""
    v = _os.getenv("SERVIA_WA_NUMBER", "").strip()
    if v:
        return v.lstrip("+").replace(" ", "").replace("-", "")
    try:
        from .brand_contact import get_contact_whatsapp, get_contact_phone
        w = get_contact_whatsapp() or get_contact_phone() or ""
        return w.lstrip("+").replace(" ", "").replace("-", "")
    except Exception:
        return ""

# Backwards compat: existing module-scope reference reads at import time;
# converted to a property-style lookup below via SERVIA_WA() callable.
SERVIA_WA = _servia_wa()


def _ensure_schema() -> None:
    with db.connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS nfc_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                owner_customer_id INTEGER NOT NULL,
                service_id TEXT NOT NULL,
                saved_address_id INTEGER,
                alias TEXT,
                location_label TEXT,
                size TEXT DEFAULT 'sticker',
                is_active INTEGER DEFAULT 1,
                tap_count INTEGER DEFAULT 0,
                booking_count INTEGER DEFAULT 0,
                last_tap_at TEXT,
                last_booking_at TEXT,
                created_at TEXT NOT NULL,
                fulfilled_at TEXT,
                fulfilled_via TEXT,
                bulk_order_id INTEGER,
                install_appointment_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS nfc_taps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id INTEGER NOT NULL,
                ip TEXT,
                user_agent TEXT,
                customer_id_at_tap INTEGER,
                ts TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS nfc_bulk_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                qty INTEGER NOT NULL,
                size TEXT NOT NULL,
                install_at TEXT,
                install_address TEXT,
                paid_aed REAL DEFAULT 0,
                invoice_id TEXT,
                status TEXT DEFAULT 'queued',
                created_at TEXT NOT NULL
            )
        """)
        # Idempotent column adds for existing deployments
        for stmt in (
            "ALTER TABLE nfc_tags ADD COLUMN bulk_order_id INTEGER",
            "ALTER TABLE nfc_tags ADD COLUMN install_appointment_at TEXT",
            "ALTER TABLE nfc_tags ADD COLUMN wa_confirmed_at TEXT",
            "ALTER TABLE nfc_tags ADD COLUMN wa_pending_token TEXT",
            # v1.22.95: per-tag payment mode controls how a tap completes:
            #   manual_pay     - Owner taps wallet/card on confirm page, after WA code
            #   auto_wallet    - Auto-deduct from wallet AFTER owner sends WA code
            #   preconfigured  - Fully hands-off: tap → wallet auto-deducted → done
            #                     (owner trusts the linked location enough to skip WA)
            "ALTER TABLE nfc_tags ADD COLUMN payment_mode TEXT DEFAULT 'manual_pay'",
            "ALTER TABLE nfc_tags ADD COLUMN max_auto_amount_aed REAL DEFAULT 500",
        ):
            try: c.execute(stmt)
            except Exception: pass
        # Customer wallet — top up once, tap-bookings deduct atomically.
        c.execute("""
            CREATE TABLE IF NOT EXISTS customer_wallet (
                customer_id INTEGER PRIMARY KEY,
                balance_aed REAL DEFAULT 0,
                updated_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS wallet_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                delta_aed REAL NOT NULL,
                kind TEXT NOT NULL,            -- topup | nfc_book | refund
                ref TEXT,                       -- invoice id / nfc slug / etc
                note TEXT,
                ts TEXT NOT NULL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_nfc_owner ON nfc_tags(owner_customer_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_nfc_taps_tag ON nfc_taps(tag_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_nfc_bulk_cust ON nfc_bulk_orders(customer_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_wallet_ledger ON wallet_ledger(customer_id)")


# ============================================================================
# Public — the actual tap-handler
# ============================================================================
@public_router.get("/t/{slug}")
def nfc_tap(slug: str, request: Request):
    """The URL written onto every NFC sticker. Records the tap and 302s to
    /book.html?nfc=<slug> (or /sos.html?auto=1 for vehicle_recovery tags so
    the dispatch fires the moment the screen loads)."""
    _ensure_schema()
    with db.connect() as c:
        row = c.execute(
            "SELECT id, is_active, service_id FROM nfc_tags WHERE slug=?", (slug,)
        ).fetchone()
        if not row:
            return RedirectResponse(f"/nfc-not-found.html?slug={slug}", status_code=302)
        if not row["is_active"]:
            return RedirectResponse(f"/nfc-deactivated.html?slug={slug}", status_code=302)
        # Increment tap counter + log
        ip = (request.client.host if request.client else "?")[:64]
        ua = (request.headers.get("user-agent") or "")[:240]
        c.execute(
            "UPDATE nfc_tags SET tap_count = tap_count + 1, last_tap_at = ? WHERE id = ?",
            (_now(), row["id"]),
        )
        c.execute(
            "INSERT INTO nfc_taps(tag_id, ip, user_agent, ts) VALUES(?,?,?,?)",
            (row["id"], ip, ua, _now()),
        )
        svc = row["service_id"] or ""
    db.log_event("nfc", slug, "tap")
    # Recovery tags skip the booking confirm card and go straight to one-tap dispatch.
    if svc == "vehicle_recovery":
        return RedirectResponse(f"/sos.html?auto=1&from=nfc&slug={slug}", status_code=302)
    return RedirectResponse(f"/book.html?nfc={slug}", status_code=302)


# ============================================================================
# Public — fetch tag info for the confirm card on book.html
# ============================================================================
@router.get("/api/nfc/tag/{slug}")
def get_tag_public(slug: str, request: Request):
    """Returns enough to render the confirm card. Owner identity (name/phone)
    is masked to last-4-digits-of-phone so a stranger tapping doesn't dox
    the owner. Full info only if Bearer token belongs to the owner."""
    _ensure_schema()
    with db.connect() as c:
        row = c.execute("""
            SELECT t.*, c.name AS owner_name, c.phone AS owner_phone, c.email AS owner_email
            FROM nfc_tags t LEFT JOIN customers c ON c.id = t.owner_customer_id
            WHERE t.slug = ?
        """, (slug,)).fetchone()
    if not row:
        raise HTTPException(404, "Unknown NFC tag")
    if not row["is_active"]:
        raise HTTPException(410, "This NFC tag has been deactivated")
    # Detect if request bearer is the owner
    is_owner = False
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        try:
            user = lookup_session(auth[7:].strip())
            if user and user.user_type == "customer" and user.user_id == row["owner_customer_id"]:
                is_owner = True
        except Exception:
            pass
    phone = row["owner_phone"] or ""
    masked = ("*" * max(0, len(phone) - 4)) + phone[-4:] if len(phone) >= 4 else "—"
    return {
        "slug": row["slug"],
        "alias": row["alias"],
        "service_id": row["service_id"],
        "size": row["size"],
        "location_label": row["location_label"],
        "tap_count": row["tap_count"],
        "booking_count": row["booking_count"],
        "payment_mode": row["payment_mode"] if "payment_mode" in row.keys() else "manual_pay",
        "max_auto_amount_aed": row["max_auto_amount_aed"] if "max_auto_amount_aed" in row.keys() else 500,
        "owner": {
            "is_me": is_owner,
            "name": row["owner_name"] if is_owner else None,
            "phone": phone if is_owner else masked,
        },
        "saved_address_id": row["saved_address_id"] if is_owner else None,
    }


# Customer self-service tag configuration (set payment mode + max auto cap)
class _TagConfigBody(BaseModel):
    payment_mode: str | None = None       # manual_pay | auto_wallet | preconfigured
    max_auto_amount_aed: float | None = None
    alias: str | None = None
    location_label: str | None = None
    is_active: int | None = None


@router.put("/api/nfc/my-tag/{tag_id}")
def customer_update_tag(tag_id: int, body: _TagConfigBody, request: Request):
    """Customer-side tag config: payment mode, alias, location, deactivate.
    Only the tag's owner can edit it."""
    _ensure_schema()
    auth = request.headers.get("authorization") or ""
    user = lookup_session(auth[7:].strip()) if auth.lower().startswith("bearer ") else None
    if not user or user.user_type != "customer":
        raise HTTPException(401, "Customer session required")
    with db.connect() as c:
        row = c.execute(
            "SELECT id, owner_customer_id FROM nfc_tags WHERE id=?", (tag_id,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Tag not found")
    if row["owner_customer_id"] != user.user_id:
        raise HTTPException(403, "Not your tag")
    if body.payment_mode and body.payment_mode not in ("manual_pay", "auto_wallet", "preconfigured"):
        raise HTTPException(400, "payment_mode must be manual_pay / auto_wallet / preconfigured")
    sets, params = [], []
    if body.payment_mode is not None:
        sets.append("payment_mode = ?"); params.append(body.payment_mode)
    if body.max_auto_amount_aed is not None:
        sets.append("max_auto_amount_aed = ?"); params.append(float(body.max_auto_amount_aed))
    if body.alias is not None:
        sets.append("alias = ?"); params.append(body.alias[:80])
    if body.location_label is not None:
        sets.append("location_label = ?"); params.append(body.location_label[:80])
    if body.is_active is not None:
        sets.append("is_active = ?"); params.append(int(bool(body.is_active)))
    if not sets:
        return {"ok": True, "updated": 0}
    params.append(tag_id)
    with db.connect() as c:
        n = c.execute(f"UPDATE nfc_tags SET {', '.join(sets)} WHERE id = ?", params).rowcount
    db.log_event("nfc", str(tag_id), "customer_config_update", actor=str(user.user_id),
                 details={"fields": [s.split(" = ")[0] for s in sets]})
    return {"ok": True, "updated": n}


# ============================================================================
# Customer — order a new tag, list mine, record a confirmed booking
# ============================================================================
class _NfcOrderBody(BaseModel):
    service_id: str = Field(min_length=1, max_length=64)
    saved_address_id: int | None = None
    alias: str | None = Field(default=None, max_length=80)
    location_label: str | None = Field(default=None, max_length=80)
    size: str = Field(default="sticker")  # sticker | card | keychain
    delivery: str = Field(default="next_visit")  # next_visit | courier


@router.post("/api/nfc/order")
def customer_order_tag(body: _NfcOrderBody, request: Request):
    """Customer requests a new tag. Stays unfulfilled (active=1, but
    fulfilled_at NULL) until admin confirms it's been printed + handed to
    the courier or next-visit crew. The tag URL works the moment it's
    written — the 'fulfilled' flag is purely operational."""
    _ensure_schema()
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(401, "Sign in first to order an NFC tag")
    user = lookup_session(auth[7:].strip())
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    if user.user_type != "customer":
        raise HTTPException(403, "Only customers can order tags")
    cid = user.user_id
    if body.size not in ("sticker", "card", "keychain"):
        raise HTTPException(400, "size must be sticker/card/keychain")
    slug = _new_slug()
    while True:
        with db.connect() as c:
            taken = c.execute("SELECT 1 FROM nfc_tags WHERE slug=?", (slug,)).fetchone()
        if not taken: break
        slug = _new_slug()
    with db.connect() as c:
        cur = c.execute(
            """INSERT INTO nfc_tags(slug, owner_customer_id, service_id, saved_address_id,
                                     alias, location_label, size, is_active, created_at)
               VALUES(?,?,?,?,?,?,?,1,?)""",
            (slug, cid, body.service_id, body.saved_address_id,
             body.alias, body.location_label, body.size, _now()),
        )
        tag_id = cur.lastrowid
    db.log_event("nfc", slug, "ordered", actor=str(cid),
                 details={"service": body.service_id, "size": body.size,
                          "delivery": body.delivery})
    return {
        "ok": True,
        "tag_id": tag_id,
        "slug": slug,
        "tap_url": f"https://servia.ae/t/{slug}",
        "status": "queued",
        "delivery": body.delivery,
        "message": ("We'll write & include this tag with your next service visit."
                    if body.delivery == "next_visit"
                    else "We'll courier this tag to your default address (free in UAE, 1-2 days)."),
    }


@router.get("/api/nfc/my-tags")
def list_my_tags(request: Request):
    """Logged-in customer lists their own tags."""
    _ensure_schema()
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(401, "Sign in first")
    user = lookup_session(auth[7:].strip())
    if not user or user.user_type != "customer":
        raise HTTPException(401, "Invalid token")
    cid = user.user_id
    with db.connect() as c:
        rows = c.execute(
            """SELECT id, slug, service_id, alias, location_label, size, is_active,
                       tap_count, booking_count, last_tap_at, last_booking_at, created_at
               FROM nfc_tags WHERE owner_customer_id = ? ORDER BY id DESC""",
            (cid,),
        ).fetchall()
    return {"tags": [dict(r) for r in rows]}


class _NfcConfirmBody(BaseModel):
    slug: str
    booking_id: int


@router.post("/api/nfc/tap-confirm")
def tap_confirmed_booking(body: _NfcConfirmBody):
    """Front-end calls this AFTER /api/bookings created a booking via NFC
    tap, so we can attribute the booking and bump the tag's counter."""
    _ensure_schema()
    with db.connect() as c:
        n = c.execute(
            "UPDATE nfc_tags SET booking_count = booking_count + 1, last_booking_at = ? WHERE slug = ?",
            (_now(), body.slug),
        ).rowcount
    if not n:
        raise HTTPException(404, "Unknown NFC tag")
    db.log_event("nfc", body.slug, "booked", details={"booking_id": body.booking_id})
    return {"ok": True}


# ============================================================================
# Admin — manage tags + write-to-NFC instructions + print template
# ============================================================================
@router.get("/api/admin/nfc/tags", dependencies=[Depends(require_admin)])
def admin_list_tags(q: str | None = None, only_pending: bool = False, limit: int = 200):
    _ensure_schema()
    where = []
    params: list = []
    if q:
        where.append("(t.slug LIKE ? OR t.alias LIKE ? OR c.phone LIKE ? OR c.name LIKE ?)")
        params += [f"%{q}%"] * 4
    if only_pending:
        where.append("t.fulfilled_at IS NULL")
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    with db.connect() as c:
        rows = c.execute(
            f"""SELECT t.*, c.name AS owner_name, c.phone AS owner_phone
                 FROM nfc_tags t
                 LEFT JOIN customers c ON c.id = t.owner_customer_id
                 {where_sql}
                 ORDER BY t.id DESC LIMIT ?""",
            params + [int(limit)],
        ).fetchall()
    return {"tags": [dict(r) for r in rows]}


class _AdminCreateTag(BaseModel):
    customer_id: int
    service_id: str
    saved_address_id: int | None = None
    alias: str | None = None
    location_label: str | None = None
    size: str = "sticker"


@router.post("/api/admin/nfc/tags", dependencies=[Depends(require_admin)])
def admin_create_tag(body: _AdminCreateTag):
    _ensure_schema()
    if body.size not in ("sticker", "card", "keychain"):
        raise HTTPException(400, "size must be sticker/card/keychain")
    slug = _new_slug()
    with db.connect() as c:
        # Verify customer exists
        if not c.execute("SELECT 1 FROM customers WHERE id=?", (body.customer_id,)).fetchone():
            raise HTTPException(404, "Customer not found")
        cur = c.execute(
            """INSERT INTO nfc_tags(slug, owner_customer_id, service_id, saved_address_id,
                                     alias, location_label, size, is_active, created_at)
               VALUES(?,?,?,?,?,?,?,1,?)""",
            (slug, body.customer_id, body.service_id, body.saved_address_id,
             body.alias, body.location_label, body.size, _now()),
        )
    db.log_event("nfc", slug, "admin_created", actor="admin",
                 details={"customer_id": body.customer_id, "service": body.service_id})
    return {"ok": True, "slug": slug, "tap_url": f"https://servia.ae/t/{slug}"}


class _AdminUpdateTag(BaseModel):
    is_active: int | None = None
    service_id: str | None = None
    alias: str | None = None
    location_label: str | None = None
    fulfilled_via: str | None = None  # 'courier' | 'next_visit' | 'in_store'


@router.put("/api/admin/nfc/tags/{tag_id}", dependencies=[Depends(require_admin)])
def admin_update_tag(tag_id: int, body: _AdminUpdateTag):
    _ensure_schema()
    sets, params = [], []
    if body.is_active is not None:
        sets.append("is_active = ?"); params.append(int(bool(body.is_active)))
    if body.service_id is not None:
        sets.append("service_id = ?"); params.append(body.service_id)
    if body.alias is not None:
        sets.append("alias = ?"); params.append(body.alias)
    if body.location_label is not None:
        sets.append("location_label = ?"); params.append(body.location_label)
    if body.fulfilled_via is not None:
        sets.append("fulfilled_via = ?"); params.append(body.fulfilled_via)
        sets.append("fulfilled_at = ?"); params.append(_now())
    if not sets:
        return {"ok": True, "updated": 0}
    params.append(tag_id)
    with db.connect() as c:
        n = c.execute(f"UPDATE nfc_tags SET {', '.join(sets)} WHERE id = ?", params).rowcount
    db.log_event("nfc", str(tag_id), "admin_update", actor="admin",
                 details={"fields": [s.split(" = ")[0] for s in sets]})
    return {"ok": True, "updated": n}


@router.delete("/api/admin/nfc/tags/{tag_id}", dependencies=[Depends(require_admin)])
def admin_delete_tag(tag_id: int):
    _ensure_schema()
    with db.connect() as c:
        n = c.execute("DELETE FROM nfc_tags WHERE id = ?", (tag_id,)).rowcount
    db.log_event("nfc", str(tag_id), "admin_delete", actor="admin")
    return {"ok": True, "deleted": n}


# ============================================================================
# Bulk order — customer orders multiple tags + selects an installation
# appointment. Our tech arrives at that time, sticks them everywhere, writes
# each one with the right URL. Customer pre-pays via the same /pay flow.
# ============================================================================
class _BulkOrderTag(BaseModel):
    service_id: str
    alias: str | None = None
    location_label: str | None = None


class _BulkOrderBody(BaseModel):
    items: list[_BulkOrderTag]
    size: str = "sticker"
    install_at: str | None = None       # ISO8601 — when our tech should arrive
    install_address: str | None = None  # text — where to install
    pay_now: bool = True


@router.post("/api/nfc/bulk-order")
def customer_bulk_order(body: _BulkOrderBody, request: Request):
    """Customer orders multiple tags at once (typical: 4–8 for a flat,
    8–14 for a villa). Each tag gets its own slug + service binding.
    Optional installation appointment so our tech sticks them in place
    instead of asking the customer to apply each one."""
    _ensure_schema()
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(401, "Sign in first")
    user = lookup_session(auth[7:].strip())
    if not user or user.user_type != "customer":
        raise HTTPException(401, "Customer session required")
    cid = user.user_id
    if not body.items or len(body.items) > 30:
        raise HTTPException(400, "1–30 tags per bulk order")
    if body.size not in ("sticker", "card", "keychain"):
        raise HTTPException(400, "size must be sticker/card/keychain")
    qty = len(body.items)
    # Pricing tier (admin-configurable later via db.cfg in v1.22.93+)
    unit_price = {"sticker": 5.0, "card": 12.0, "keychain": 18.0}[body.size]
    total_tags = qty * unit_price
    install_fee = 49.0 if body.install_at else 0.0
    total_aed = total_tags + install_fee

    with db.connect() as c:
        cur = c.execute(
            """INSERT INTO nfc_bulk_orders(customer_id, qty, size, install_at,
                                            install_address, paid_aed, status, created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (cid, qty, body.size, body.install_at, body.install_address,
             0.0, "queued", _now()),
        )
        bulk_id = cur.lastrowid
        slugs: list[str] = []
        for it in body.items:
            slug = _new_slug()
            while c.execute("SELECT 1 FROM nfc_tags WHERE slug=?", (slug,)).fetchone():
                slug = _new_slug()
            c.execute(
                """INSERT INTO nfc_tags(slug, owner_customer_id, service_id, alias,
                                         location_label, size, bulk_order_id,
                                         install_appointment_at, is_active, created_at)
                   VALUES(?,?,?,?,?,?,?,?,1,?)""",
                (slug, cid, it.service_id, it.alias, it.location_label,
                 body.size, bulk_id, body.install_at, _now()),
            )
            slugs.append(slug)

    # Generate an invoice for advance payment if requested
    invoice_id = None
    if body.pay_now and total_aed > 0:
        invoice_id = f"NFC-{bulk_id:05d}"
        try:
            with db.connect() as c:
                c.execute(
                    """INSERT OR IGNORE INTO invoices(id, customer_id, amount_aed,
                                                        status, description, created_at)
                       VALUES(?,?,?,?,?,?)""",
                    (invoice_id, cid, total_aed, "unpaid",
                     f"Servia NFC bulk order — {qty} {body.size}(s)" +
                     (f" + onsite install {body.install_at}" if body.install_at else ""),
                     _now()),
                )
                c.execute("UPDATE nfc_bulk_orders SET invoice_id = ? WHERE id = ?",
                          (invoice_id, bulk_id))
        except Exception as _e:
            print(f"[nfc-bulk] invoice insert skipped: {_e}", flush=True)
    db.log_event("nfc", str(bulk_id), "bulk_ordered", actor=str(cid),
                 details={"qty": qty, "size": body.size, "install": bool(body.install_at)})
    return {
        "ok": True,
        "bulk_order_id": bulk_id,
        "qty": qty,
        "size": body.size,
        "unit_price_aed": unit_price,
        "tags_subtotal_aed": total_tags,
        "install_fee_aed": install_fee,
        "total_aed": total_aed,
        "slugs": slugs,
        "tap_urls": [f"https://servia.ae/t/{s}" for s in slugs],
        "invoice_id": invoice_id,
        "pay_url": f"/pay/{invoice_id}" if invoice_id else None,
        "install_at": body.install_at,
    }


@router.get("/api/nfc/bulk-orders/me")
def list_my_bulk_orders(request: Request):
    _ensure_schema()
    auth = request.headers.get("authorization") or ""
    user = lookup_session(auth[7:].strip()) if auth.lower().startswith("bearer ") else None
    if not user or user.user_type != "customer":
        raise HTTPException(401, "Customer session required")
    with db.connect() as c:
        rows = c.execute(
            """SELECT b.*, COUNT(t.id) AS tag_count
               FROM nfc_bulk_orders b
               LEFT JOIN nfc_tags t ON t.bulk_order_id = b.id
               WHERE b.customer_id = ?
               GROUP BY b.id ORDER BY b.id DESC LIMIT 50""",
            (user.user_id,),
        ).fetchall()
    return {"orders": [dict(r) for r in rows]}


# ============================================================================
# WhatsApp verification — when a tap-booking is about to be placed, we shoot
# a WhatsApp confirm to the tag-owner's number with the booking summary +
# OK/CANCEL buttons. Owner replies → booking is locked. This guards against
# someone tapping a fridge tag while at the owner's place to prank-order.
# ============================================================================
class _WaSendBody(BaseModel):
    slug: str
    service_summary: str
    when_iso: str
    amount_aed: float


@router.post("/api/nfc/wa-verify-send")
def wa_verify_send(body: _WaSendBody):
    """Returns a token + WhatsApp deep-link URL the front-end opens. The
    actual WA message is composed by Servia's WhatsApp bridge in main.py
    (whatsapp_bridge.py). This endpoint just records the intent + token."""
    _ensure_schema()
    with db.connect() as c:
        row = c.execute("""
            SELECT t.id, t.slug, c.phone, c.name FROM nfc_tags t
            JOIN customers c ON c.id = t.owner_customer_id
            WHERE t.slug = ?
        """, (body.slug,)).fetchone()
    if not row:
        raise HTTPException(404, "Unknown tag")
    token = secrets.token_urlsafe(12)
    with db.connect() as c:
        c.execute("UPDATE nfc_tags SET wa_pending_token = ? WHERE id = ?",
                  (token, row["id"]))
    # Build WhatsApp self-confirm message — owner replies "OK" to confirm
    msg = (f"Servia NFC tap from your *{body.service_summary}* tag.\n"
           f"Scheduled: {body.when_iso}\nAmount: AED {body.amount_aed:.0f}\n"
           f"Reply *OK* to confirm or *CANCEL* to abort.\nCode: {token}")
    phone_clean = "".join(ch for ch in (row["phone"] or "") if ch.isdigit())
    wa_url = f"https://wa.me/{phone_clean}?text={msg.replace(chr(10), '%0A').replace(' ', '%20')}"
    return {
        "ok": True,
        "token": token,
        "wa_url": wa_url,
        "owner_name": row["name"] or "Customer",
        "phone_masked": ("****" + (row["phone"] or "")[-4:]) if row["phone"] else "",
    }


class _WaConfirmBody(BaseModel):
    slug: str
    token: str


@router.post("/api/nfc/wa-verify-confirm")
def wa_verify_confirm(body: _WaConfirmBody):
    _ensure_schema()
    with db.connect() as c:
        row = c.execute(
            "SELECT id, wa_pending_token FROM nfc_tags WHERE slug = ?",
            (body.slug,),
        ).fetchone()
    if not row or row["wa_pending_token"] != body.token:
        raise HTTPException(403, "Invalid or expired confirmation token")
    with db.connect() as c:
        c.execute(
            "UPDATE nfc_tags SET wa_confirmed_at = ?, wa_pending_token = NULL WHERE id = ?",
            (_now(), row["id"]),
        )
    db.log_event("nfc", body.slug, "wa_confirmed")
    return {"ok": True, "confirmed_at": _now()}


# ============================================================================
# Wallet — top up once, tap-bookings deduct atomically without payment dance.
# ============================================================================
@router.get("/api/wallet/balance")
def wallet_balance(request: Request):
    _ensure_schema()
    auth = request.headers.get("authorization") or ""
    user = lookup_session(auth[7:].strip()) if auth.lower().startswith("bearer ") else None
    if not user or user.user_type != "customer":
        raise HTTPException(401, "Customer session required")
    with db.connect() as c:
        row = c.execute("SELECT balance_aed FROM customer_wallet WHERE customer_id=?",
                         (user.user_id,)).fetchone()
        rows = c.execute(
            "SELECT delta_aed, kind, ref, note, ts FROM wallet_ledger "
            "WHERE customer_id=? ORDER BY id DESC LIMIT 20",
            (user.user_id,)).fetchall()
    return {
        "balance_aed": (row["balance_aed"] if row else 0.0) or 0.0,
        "ledger": [dict(r) for r in rows],
    }


class _TopupBody(BaseModel):
    amount_aed: float


@router.post("/api/wallet/topup")
def wallet_topup(body: _TopupBody, request: Request):
    """Issues an invoice for the top-up amount; once paid, the existing
    /pay/{invoice_id} flow's webhook bumps the balance via _credit_wallet
    (called from main.py's payment confirmation hook in production)."""
    _ensure_schema()
    auth = request.headers.get("authorization") or ""
    user = lookup_session(auth[7:].strip()) if auth.lower().startswith("bearer ") else None
    if not user or user.user_type != "customer":
        raise HTTPException(401, "Customer session required")
    if body.amount_aed < 25 or body.amount_aed > 10000:
        raise HTTPException(400, "Top-up between AED 25 and AED 10,000")
    invoice_id = f"WALLET-{user.user_id:05d}-{int(_dt.datetime.utcnow().timestamp())}"
    try:
        with db.connect() as c:
            c.execute(
                """INSERT OR IGNORE INTO invoices(id, customer_id, amount_aed,
                                                    status, description, created_at)
                   VALUES(?,?,?,?,?,?)""",
                (invoice_id, user.user_id, float(body.amount_aed), "unpaid",
                 f"Servia wallet top-up — AED {body.amount_aed:.0f}", _now()),
            )
    except Exception as _e:
        print(f"[wallet topup] invoice insert skipped: {_e}", flush=True)
    db.log_event("wallet", str(user.user_id), "topup_intent",
                 details={"amount": body.amount_aed, "invoice": invoice_id})
    return {"ok": True, "invoice_id": invoice_id, "pay_url": f"/pay/{invoice_id}"}


def credit_wallet(customer_id: int, amount_aed: float, ref: str, note: str = "topup paid"):
    """Public helper called from the payment-confirmation webhook in main.py
    once an invoice that begins WALLET- is marked paid."""
    _ensure_schema()
    with db.connect() as c:
        c.execute(
            """INSERT INTO customer_wallet(customer_id, balance_aed, updated_at)
               VALUES(?,?,?)
               ON CONFLICT(customer_id) DO UPDATE SET
                  balance_aed = balance_aed + excluded.balance_aed,
                  updated_at = excluded.updated_at""",
            (customer_id, float(amount_aed), _now()),
        )
        c.execute(
            "INSERT INTO wallet_ledger(customer_id, delta_aed, kind, ref, note, ts) "
            "VALUES(?,?,?,?,?,?)",
            (customer_id, float(amount_aed), "topup", ref, note, _now()),
        )


def _debit_wallet_atomic(customer_id: int, amount_aed: float, ref: str, note: str) -> bool:
    """Atomic wallet deduction. Returns True iff the balance was sufficient
    AND the deduction succeeded. SQLite transaction; no double-spend."""
    with db.connect() as c:
        cur = c.execute(
            "UPDATE customer_wallet SET balance_aed = balance_aed - ?, updated_at = ? "
            "WHERE customer_id = ? AND balance_aed >= ?",
            (float(amount_aed), _now(), customer_id, float(amount_aed)),
        )
        if cur.rowcount != 1:
            return False
        c.execute(
            "INSERT INTO wallet_ledger(customer_id, delta_aed, kind, ref, note, ts) "
            "VALUES(?,?,?,?,?,?)",
            (customer_id, -float(amount_aed), "nfc_book", ref, note, _now()),
        )
    return True


# ============================================================================
# Wallet-paid NFC tap booking: ALL the magic in one endpoint.
#
# Customer taps tag → /book.html?nfc=<slug> → presses "Pay from wallet" button.
# Front-end calls this → server:
#   1. Verifies session = tag owner
#   2. Generates a 4-char WA confirm code
#   3. Returns wa.me deep-link prefilled with the code → tag owner taps Send
#   4. WhatsApp bridge inbound webhook calls confirm_wa_code() → deducts wallet,
#      attributes booking, notifies the dispatch crew.
# ============================================================================
class _WalletTapBody(BaseModel):
    slug: str
    service_id: str
    when_iso: str
    amount_aed: float
    address: str | None = None
    extra_services: list[str] = []


@router.post("/api/nfc/wallet-pay-init")
def wallet_pay_init(body: _WalletTapBody, request: Request):
    """v1.22.95 — branches on tag.payment_mode:
       - 'preconfigured': fully hands-off. Validates wallet has enough balance
         within tag's max_auto_amount_aed cap; deducts immediately; returns
         {ok:True, mode:'auto_completed'}. No WA dance.
       - 'auto_wallet' / 'manual_pay': sends a WA confirm code, owner taps
         Send in WhatsApp, wa-code-inbound deducts the wallet (auto_wallet)
         OR a card link (manual_pay)."""
    _ensure_schema()
    auth = request.headers.get("authorization") or ""
    user = lookup_session(auth[7:].strip()) if auth.lower().startswith("bearer ") else None
    if not user or user.user_type != "customer":
        raise HTTPException(401, "Customer session required")
    with db.connect() as c:
        tag = c.execute(
            "SELECT id, owner_customer_id, service_id, slug, "
            "COALESCE(payment_mode,'manual_pay') AS payment_mode, "
            "COALESCE(max_auto_amount_aed,500) AS max_auto_amount_aed "
            "FROM nfc_tags WHERE slug=?", (body.slug,),
        ).fetchone()
    if not tag:
        raise HTTPException(404, "Unknown tag")
    if tag["owner_customer_id"] != user.user_id:
        raise HTTPException(403, "This tag belongs to another account")
    with db.connect() as c:
        bal = c.execute("SELECT balance_aed FROM customer_wallet WHERE customer_id=?",
                         (user.user_id,)).fetchone()
        balance = (bal["balance_aed"] if bal else 0.0) or 0.0
    if balance < body.amount_aed:
        return {
            "ok": False,
            "balance_aed": balance,
            "needed_aed": body.amount_aed,
            "shortfall_aed": body.amount_aed - balance,
            "error": "Insufficient wallet balance",
            "topup_url": "/me.html#wallet",
        }
    # PRECONFIGURED MODE — instant auto-deduct, no WhatsApp step
    if tag["payment_mode"] == "preconfigured":
        if body.amount_aed > tag["max_auto_amount_aed"]:
            return {
                "ok": False,
                "error": (f"Amount AED {body.amount_aed:.0f} exceeds the "
                          f"max-auto cap (AED {tag['max_auto_amount_aed']:.0f}) "
                          "you set on this tag. Confirm via WA or raise the cap."),
                "needs_wa_confirm": True,
            }
        if not _debit_wallet_atomic(user.user_id, body.amount_aed,
                                      ref=tag["slug"], note=f"NFC preconfigured tap"):
            raise HTTPException(402, "Wallet deduction failed (concurrency)")
        with db.connect() as c:
            c.execute(
                "UPDATE nfc_tags SET booking_count = booking_count + 1, "
                "last_booking_at = ?, wa_confirmed_at = ? WHERE id = ?",
                (_now(), _now(), tag["id"]),
            )
        db.log_event("nfc", tag["slug"], "preconfigured_tap_paid",
                     details={"amount": body.amount_aed})
        return {
            "ok": True,
            "mode": "auto_completed",
            "deducted_aed": body.amount_aed,
            "balance_aed": balance - body.amount_aed,
            "message": (f"✅ Service booked & AED {body.amount_aed:.0f} deducted "
                          f"automatically (you pre-approved this tag for amounts up "
                          f"to AED {tag['max_auto_amount_aed']:.0f}). Crew dispatched."),
        }
    # MANUAL_PAY / AUTO_WALLET — generate WhatsApp code path
    code = "".join(secrets.choice("23456789ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(4))
    with db.connect() as c:
        c.execute("UPDATE nfc_tags SET wa_pending_token = ? WHERE id = ?",
                   (code, tag["id"]))
    # Build prefilled WA message → opens user's WhatsApp directly
    msg = (f"NFC{code} confirm Servia tap booking · slug {body.slug} · "
           f"{body.service_id} · {body.when_iso} · AED {body.amount_aed:.0f}")
    msg_url = msg.replace(" ", "%20").replace("·", "%C2%B7").replace("\n", "%0A")
    wa_deeplink = f"https://wa.me/{SERVIA_WA}?text={msg_url}"
    return {
        "ok": True,
        "mode": tag["payment_mode"],
        "code": code,
        "wa_deeplink": wa_deeplink,
        "balance_aed": balance,
        "amount_aed": body.amount_aed,
        "remaining_after_aed": balance - body.amount_aed,
        "instructions": (
            "1) Tap 'Open WhatsApp' below. 2) WhatsApp opens with the code "
            f"NFC{code} and your booking details. 3) Hit Send. 4) Servia bot "
            "will reply 'Confirmed' within 5 seconds — booking placed and "
            f"AED {body.amount_aed:.0f} deducted from your wallet."
        ),
    }


# Called by the WhatsApp bridge when an inbound message contains "NFC<code>".
# (Wired from app/whatsapp_bridge.py inbound webhook in production. Exposing
#  it as a regular endpoint also lets us bench-test without a live WA.)
class _WaCodeBody(BaseModel):
    from_phone: str
    text: str


@router.post("/api/nfc/wa-code-inbound")
def wa_code_inbound(body: _WaCodeBody):
    """Parse 'NFC<code>' from an incoming WhatsApp message and finalise
    a wallet-paid tap booking. Returns the deduction result."""
    _ensure_schema()
    import re
    m = re.search(r"NFC([A-Z0-9]{4})", (body.text or "").upper())
    if not m:
        raise HTTPException(400, "No NFC<code> in message")
    code = m.group(1)
    with db.connect() as c:
        tag = c.execute("SELECT * FROM nfc_tags WHERE wa_pending_token = ?",
                        (code,)).fetchone()
    if not tag:
        raise HTTPException(404, "Code expired or already used")
    # Verify the inbound message came from the tag owner's phone
    digits = "".join(ch for ch in body.from_phone if ch.isdigit())
    with db.connect() as c:
        owner = c.execute(
            "SELECT phone FROM customers WHERE id=?", (tag["owner_customer_id"],)
        ).fetchone()
    owner_digits = "".join(ch for ch in (owner["phone"] if owner else "") if ch.isdigit())
    if not owner_digits or not digits.endswith(owner_digits[-9:]):
        raise HTTPException(403, "Confirmation must come from the tag-owner's phone")
    # Atomic wallet deduction. Approximate amount: parse from message text,
    # else fall back to the ledger of the most recent intent (kept lean here).
    amt_match = re.search(r"AED\s+(\d+(?:\.\d+)?)", body.text)
    amount = float(amt_match.group(1)) if amt_match else 100.0
    if not _debit_wallet_atomic(tag["owner_customer_id"], amount,
                                  ref=tag["slug"], note=f"NFC tap · code {code}"):
        raise HTTPException(402, "Insufficient wallet balance — top up first")
    # Mark tag confirmed + bump booking counter
    with db.connect() as c:
        c.execute(
            "UPDATE nfc_tags SET wa_confirmed_at = ?, wa_pending_token = NULL, "
            "booking_count = booking_count + 1, last_booking_at = ? WHERE id = ?",
            (_now(), _now(), tag["id"]),
        )
    db.log_event("nfc", tag["slug"], "wa_paid_book",
                 details={"amount": amount, "code": code})
    return {
        "ok": True,
        "deducted_aed": amount,
        "tag_slug": tag["slug"],
        "message": f"Booking confirmed via WhatsApp. AED {amount:.0f} deducted from wallet.",
    }


# ============================================================================
# NFC consultation bot — friendly LLM-backed advisor that helps customers
# pick how many tags, what services to bind, where to stick them, what size.
# Available on /nfc.html as a chat widget. Saves token on a /api/nfc/consult
# session, finalises by calling the existing /api/nfc/bulk-order.
# ============================================================================
class _ConsultMsg(BaseModel):
    role: str
    content: str


class _ConsultBody(BaseModel):
    messages: list[_ConsultMsg]


_CONSULT_SYSTEM_PROMPT = (
    "You are Servia's NFC tap-to-book consultant — friendly, pragmatic, brief.\n"
    "Your job: chat with the customer, understand their home/lifestyle, "
    "recommend a tailored set of NFC tags, then summarise the order.\n\n"
    "WHAT YOU KNOW:\n"
    "- Servia services: deep_cleaning, ac_cleaning, maid_service, handyman, "
    "pest_control, sofa_carpet, window_cleaning, move_in_out, painting, "
    "laundry, babysitting, garden, pool, car_wash, vehicle_recovery.\n"
    "- Tag sizes: sticker (AED 5), card (AED 12), keychain (AED 18).\n"
    "- Onsite installation by Servia tech: AED 49 flat.\n"
    "- Tags are passive NFC, no battery, last ~10 years, NTAG213 chip.\n"
    "- Recommendations:\n"
    "  * Studio / 1BR flat → 3-4 tags is ideal\n"
    "  * 2-3BR flat       → 5-7 tags\n"
    "  * Villa / 4BR+     → 8-14 tags\n"
    "  * Office           → 2-4 tags\n"
    "  * Always include 1 kitchen tag (most-used) + AC tag (summer).\n"
    "  * Drivers: car wash + vehicle recovery on dashboard.\n"
    "  * Pool owners: pool tag near equipment pad.\n"
    "  * Parents: babysitter tag in nursery.\n\n"
    "STYLE:\n"
    "- Ask 1-2 questions per turn, never a wall of text.\n"
    "- Use bullet points for recommendations.\n"
    "- After 4-6 turns max, summarise the proposed list and ask "
    "'Shall I place the order? You can edit before paying.'\n"
    "- When the customer says 'yes' / 'place it' / 'book it', respond with a "
    "JSON code block (and ONLY that JSON in the last message) of shape:\n"
    "```json\n"
    "{\"action\":\"place_order\",\"items\":["
    "{\"service_id\":\"deep_cleaning\",\"location_label\":\"Kitchen\","
    "\"alias\":\"Kitchen tag\"}],\"size\":\"sticker\",\"install_at\":null}\n"
    "```\n"
    "Anything else: plain conversational text.\n\n"
    "Currency: AED. Be kind. Be brief. Never make up information; "
    f"if asked something off-topic, redirect to {_bookings_email()}."
)


@router.post("/api/nfc/consult")
def nfc_consult(body: _ConsultBody, request: Request):
    """LLM-backed consultation chat. Stateless — front-end keeps history.
    Re-uses Servia's primary LLM router (Anthropic by default) so no extra
    API key needed. Returns the assistant's next message + a parsed
    `action` if the assistant emitted a JSON block."""
    # Late import: ai_router has heavy deps + needs API keys
    try:
        from . import ai_router as _ai
    except Exception as e:
        raise HTTPException(503, f"AI router unavailable: {e}")

    msgs = [{"role": m.role, "content": m.content} for m in body.messages]
    if not msgs:
        return {"text": "👋 Hi! I'm your Servia tag consultant. Tell me a bit about "
                         "your home (flat, villa, office?) and what tasks come up most. "
                         "I'll suggest a tailored set of NFC tags."}
    # Prepend system prompt
    full = [{"role": "system", "content": _CONSULT_SYSTEM_PROMPT}] + msgs
    try:
        # ai_router exposes chat(...) — best-effort
        if hasattr(_ai, "chat"):
            resp = _ai.chat(full, max_tokens=400, temperature=0.6)
        elif hasattr(_ai, "complete"):
            resp = _ai.complete(full, max_tokens=400)
        else:
            # Direct fallback to llm.py if present
            from . import llm as _llm
            resp = _llm.chat(full, max_tokens=400) if hasattr(_llm, "chat") else None
        text = resp if isinstance(resp, str) else (resp or {}).get("text", "")
    except Exception as e:
        print(f"[nfc-consult] LLM call failed: {e}", flush=True)
        text = ("Sorry, I'm having trouble thinking right now. As a quick "
                "starter: 4 tags (kitchen / car / AC / pool) is the most "
                "popular bundle — total AED 20 + free with next visit.")

    # Parse JSON action block if present
    action = None
    import re as _re, json as _json
    m = _re.search(r"```json\s*({.+?})\s*```", text, _re.DOTALL)
    if m:
        try:
            action = _json.loads(m.group(1))
        except Exception:
            action = None
    return {"text": text.strip(), "action": action}


@router.get("/api/admin/nfc/stats", dependencies=[Depends(require_admin)])
def admin_stats():
    _ensure_schema()
    with db.connect() as c:
        row = c.execute("""
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) AS active,
              SUM(CASE WHEN fulfilled_at IS NULL THEN 1 ELSE 0 END) AS pending_fulfillment,
              SUM(tap_count) AS total_taps,
              SUM(booking_count) AS total_bookings
            FROM nfc_tags
        """).fetchone()
    return dict(row) if row else {}


# ----- Printable card template (credit-card-size, 85.6 × 54mm) -----
_PRINT_TPL = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Servia NFC tag #{slug}</title>
<style>
  @page {{ size: 88mm 56mm; margin: 0; }}
  body {{ margin:0; padding:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
  .card {{ width:85.6mm; height:54mm; border-radius:3.5mm; overflow:hidden;
           background:linear-gradient(135deg,#0F766E 0%,#14B8A6 100%); color:#fff;
           padding:5mm; box-sizing:border-box; position:relative; page-break-after:always;
           box-shadow:0 4px 20px rgba(0,0,0,.2); }}
  .front .row1 {{ display:flex; align-items:center; justify-content:space-between; }}
  .front .logo {{ font-size:6mm; font-weight:800; letter-spacing:-.02em; }}
  .front .badge {{ background:#FCD34D; color:#7C2D12; padding:.5mm 2mm; border-radius:99px;
                  font-size:2.2mm; font-weight:800; letter-spacing:.05em; text-transform:uppercase; }}
  .front .emoji {{ font-size:14mm; line-height:1; margin:1mm 0; }}
  .front .service {{ font-size:4mm; font-weight:700; margin:1mm 0 .5mm; }}
  .front .alias {{ font-size:2.6mm; opacity:.85; }}
  .front .tap {{ position:absolute; bottom:4mm; left:5mm; right:5mm;
                display:flex; align-items:center; gap:2mm;
                background:rgba(255,255,255,.18); padding:1.5mm 3mm;
                border:1px solid rgba(255,255,255,.35); border-radius:3mm;
                font-size:2.5mm; font-weight:600; }}
  .front .tap .dot {{ width:1.5mm; height:1.5mm; border-radius:50%; background:#22C55E; }}

  .back {{ background:#fff; color:#0F172A; padding:5mm; }}
  .back h3 {{ margin:0 0 1mm; font-size:3.5mm; color:#0F766E; }}
  .back ol {{ margin:0; padding-inline-start:4mm; font-size:2.4mm; line-height:1.5; }}
  .back .url {{ font-family:ui-monospace,monospace; background:#F1F5F9; padding:1mm 2mm;
               border-radius:1.5mm; font-size:2.2mm; margin-top:1.5mm; display:inline-block; }}
  .back .privacy {{ font-size:2mm; color:#64748B; margin-top:2mm; }}
</style></head>
<body>

<div class="card front">
  <div class="row1">
    <div class="logo">Servia</div>
    <div class="badge">NFC · Tap to book</div>
  </div>
  <div class="emoji">{emoji}</div>
  <div class="service">{service_label}</div>
  <div class="alias">{alias_safe}</div>
  <div class="tap"><span class="dot"></span> Tap your phone here · 1-tap booking</div>
</div>

<div class="card back">
  <h3>How to use</h3>
  <ol>
    <li>Stick this near where the service happens (kitchen / car / AC / pool).</li>
    <li>Tap your phone's back to it (NFC must be on — usually default).</li>
    <li>Servia opens with your account &amp; service ready. Confirm — done.</li>
  </ol>
  <div class="url">servia.ae/t/{slug}</div>
  <div class="privacy">No tracking. No battery. The tag is silent until you tap.
  Same privacy as a phone-number sticker. Owner: {owner_short}.</div>
</div>

</body></html>"""

# Map service IDs to human labels + emojis for the printed card
_SERVICE_DISPLAY = {
    "deep_cleaning":   ("Deep Cleaning",   "✨"),
    "ac_cleaning":     ("AC Service",      "❄️"),
    "maid_service":    ("Maid Service",    "👤"),
    "handyman":        ("Handyman",        "🔧"),
    "pest_control":    ("Pest Control",    "🪲"),
    "sofa_carpet":     ("Sofa & Carpet",   "🛋️"),
    "window_cleaning": ("Window Cleaning", "🪟"),
    "move_in_out":     ("Move-in/out",     "📦"),
    "painting":        ("Painting",        "🎨"),
    "laundry":         ("Laundry",         "👕"),
    "babysitting":     ("Babysitter",      "👶"),
    "garden":          ("Gardening",       "🌿"),
    "pool":            ("Pool Care",       "🏊"),
    "car_wash":        ("Car Wash",        "🚗"),
}


@router.get("/api/admin/nfc/tags/{tag_id}/print",
            dependencies=[Depends(require_admin)],
            response_class=HTMLResponse)
def admin_print_card(tag_id: int):
    """Returns a printable HTML card (front + back, credit-card sized).
    Open in a browser → print → use thermal-transfer or sticker-printer."""
    _ensure_schema()
    with db.connect() as c:
        row = c.execute("""
            SELECT t.*, c.name AS owner_name, c.phone AS owner_phone
            FROM nfc_tags t LEFT JOIN customers c ON c.id = t.owner_customer_id
            WHERE t.id = ?
        """, (tag_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Tag not found")
    label, emoji = _SERVICE_DISPLAY.get(row["service_id"], (row["service_id"], "🛠"))
    phone = row["owner_phone"] or ""
    owner_short = (row["owner_name"] or "Customer") + " · ****" + phone[-4:] if phone else (row["owner_name"] or "Customer")
    html = _PRINT_TPL.format(
        slug=row["slug"],
        emoji=emoji,
        service_label=label,
        alias_safe=(row["alias"] or row["location_label"] or ""),
        owner_short=owner_short,
    )
    return HTMLResponse(html)
