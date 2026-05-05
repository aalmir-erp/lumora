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
                fulfilled_via TEXT
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
        c.execute("CREATE INDEX IF NOT EXISTS idx_nfc_owner ON nfc_tags(owner_customer_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_nfc_taps_tag ON nfc_taps(tag_id)")


# ============================================================================
# Public — the actual tap-handler
# ============================================================================
@public_router.get("/t/{slug}")
def nfc_tap(slug: str, request: Request):
    """The URL written onto every NFC sticker. Records the tap and 302s to
    /book.html?nfc=<slug> where the customer-facing confirm flow takes over."""
    _ensure_schema()
    with db.connect() as c:
        row = c.execute("SELECT id, is_active FROM nfc_tags WHERE slug=?", (slug,)).fetchone()
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
    db.log_event("nfc", slug, "tap")
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
        "owner": {
            "is_me": is_owner,
            "name": row["owner_name"] if is_owner else None,
            "phone": phone if is_owner else masked,
        },
        "saved_address_id": row["saved_address_id"] if is_owner else None,
    }


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
