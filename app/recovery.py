"""Servia one-tap vehicle-recovery dispatch.

Customer (or watch) hits /api/recovery/dispatch with their real GPS
coordinates. We:
  1. Find all vendors who offer "vehicle_recovery"
  2. Compute great-circle distance from caller -> vendor's home base (we
     keep a per-vendor lat/lng in `recovery_vendor_base`; for unknown
     vendors we fall back to the city centroid for their phone area code).
  3. Pick the best (closest with rating tiebreak), assign a booking,
     return everything the caller needs to render a vendor card and
     dial in one tap: name, phone, eta_min, price, distance_km.

The caller then shows: vendor portrait + name + phone + ETA + a single
"📞 Call now" button. On the watch this is one extra tap; on mobile
it's one extra tap. Either way the customer never has to type, browse,
or pick anything.

Tables (idempotent):
  recovery_dispatches
    id              INTEGER PK
    booking_id      TEXT (FK bookings.id)
    customer_phone  TEXT
    customer_name   TEXT
    vehicle_make    TEXT
    vehicle_plate   TEXT
    issue           TEXT          -- breakdown / accident / flat_tyre / battery / fuel / locked_out / other
    lat             REAL
    lng             REAL
    accuracy_m      REAL
    vendor_id       INTEGER (FK vendors.id)
    eta_min         INTEGER
    price_aed       REAL
    distance_km     REAL
    status          TEXT          -- dispatched / vendor_otw / completed / cancelled
    source          TEXT          -- watch / mobile / web
    created_at      TEXT
    completed_at    TEXT
  recovery_vendor_base
    vendor_id       INTEGER PK
    lat             REAL
    lng             REAL
    base_label      TEXT          -- "Al Quoz", "Sharjah Industrial 13" …

Endpoints:
  POST /api/recovery/dispatch   { lat, lng, accuracy_m?, customer_phone?,
                                  customer_name?, issue?, vehicle_make?,
                                  vehicle_plate?, source? }
                                Optionally Bearer token to attach to customer.
                                Returns: { dispatch_id, booking_id, vendor:
                                {id, name, phone, rating, jobs, base_label},
                                eta_min, distance_km, price_aed, call_url,
                                track_url }
  GET  /api/recovery/dispatch/{dispatch_id}     -> live status
  POST /api/recovery/dispatch/{dispatch_id}/complete  -> mark complete (one tap)
  POST /api/recovery/dispatch/{dispatch_id}/cancel
  GET  /api/admin/recovery/list                  -> admin overview
"""
from __future__ import annotations

import datetime as _dt
import math
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field

from . import db, tools
from .auth import require_admin
from .auth_users import lookup_session


router = APIRouter()

# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------
def _ensure_schema() -> None:
    with db.connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS recovery_dispatches (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id      TEXT,
                customer_id     INTEGER,
                customer_phone  TEXT,
                customer_name   TEXT,
                vehicle_make    TEXT,
                vehicle_plate   TEXT,
                issue           TEXT,
                lat             REAL NOT NULL,
                lng             REAL NOT NULL,
                accuracy_m      REAL,
                vendor_id       INTEGER,
                eta_min         INTEGER,
                price_aed       REAL,
                distance_km     REAL,
                status          TEXT NOT NULL DEFAULT 'dispatched',
                source          TEXT DEFAULT 'web',
                created_at      TEXT NOT NULL,
                completed_at    TEXT
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_rec_status ON recovery_dispatches(status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rec_phone  ON recovery_dispatches(customer_phone)")
        # v1.24.10 — additive columns for service_id + photo + notes
        for ddl in (
            "ALTER TABLE recovery_dispatches ADD COLUMN service_id TEXT",
            "ALTER TABLE recovery_dispatches ADD COLUMN notes TEXT",
            "ALTER TABLE recovery_dispatches ADD COLUMN photo_url TEXT",
            "ALTER TABLE recovery_dispatches ADD COLUMN customer_email TEXT",
        ):
            try: c.execute(ddl)
            except Exception: pass
        c.execute("""
            CREATE TABLE IF NOT EXISTS recovery_vendor_base (
                vendor_id  INTEGER PRIMARY KEY,
                lat        REAL NOT NULL,
                lng        REAL NOT NULL,
                base_label TEXT
            )
        """)


# ---------------------------------------------------------------------------
# UAE city centroids — used when a vendor has no explicit base coordinates.
# Keyed by phone area code. Approximate but good enough to rank by distance.
# ---------------------------------------------------------------------------
UAE_BASES = {
    "dubai":     {"lat": 25.2048, "lng": 55.2708, "label": "Dubai"},
    "sharjah":   {"lat": 25.3463, "lng": 55.4209, "label": "Sharjah"},
    "abu_dhabi": {"lat": 24.4539, "lng": 54.3773, "label": "Abu Dhabi"},
    "ajman":     {"lat": 25.4052, "lng": 55.5136, "label": "Ajman"},
    "rak":       {"lat": 25.7895, "lng": 55.9432, "label": "Ras Al Khaimah"},
    "fujairah":  {"lat": 25.1288, "lng": 56.3265, "label": "Fujairah"},
    "uaq":       {"lat": 25.5650, "lng": 55.5532, "label": "Umm Al Quwain"},
    "al_ain":    {"lat": 24.2075, "lng": 55.7447, "label": "Al Ain"},
}

# Hand-curated bases for the seeded recovery vendors (matches vendors_seed.json).
SEEDED_BASES = {
    "dispatch@desertroad-recovery.lumora": {"lat": 25.1419, "lng": 55.2255, "label": "Al Quoz, Dubai"},
    "dispatch@swiftow-uae.lumora":         {"lat": 25.3270, "lng": 55.5180, "label": "Industrial Area, Sharjah"},
    "dispatch@al-falcon-recovery.lumora":  {"lat": 24.4112, "lng": 54.4710, "label": "Mussafah, Abu Dhabi"},
    "dispatch@dxbtow24.lumora":            {"lat": 25.0786, "lng": 55.1428, "label": "Dubai Marina/JLT"},
}


def _seed_bases_if_empty() -> None:
    """Populate recovery_vendor_base for our seeded vendors. Idempotent."""
    with db.connect() as c:
        rows = c.execute(
            "SELECT v.id AS vid, v.email AS email FROM vendors v "
            "WHERE v.email IN (" + ",".join(["?"] * len(SEEDED_BASES)) + ")",
            tuple(SEEDED_BASES.keys()),
        ).fetchall()
        for r in rows:
            base = SEEDED_BASES.get(r["email"])
            if not base:
                continue
            c.execute(
                "INSERT OR REPLACE INTO recovery_vendor_base(vendor_id, lat, lng, base_label) "
                "VALUES(?,?,?,?)",
                (r["vid"], base["lat"], base["lng"], base["label"]),
            )


# ---------------------------------------------------------------------------
def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km."""
    R = 6371.0
    a1, a2 = math.radians(lat1), math.radians(lat2)
    da = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    h = math.sin(da / 2) ** 2 + math.cos(a1) * math.cos(a2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def _now() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


def _fallback_base_for_vendor_phone(phone: str | None) -> dict:
    """Map +971 area code -> rough city centroid."""
    p = (phone or "").replace(" ", "").replace("-", "")
    if p.startswith("+9712") or p.startswith("9712"): return UAE_BASES["abu_dhabi"]
    if p.startswith("+9713") or p.startswith("9713"): return UAE_BASES["al_ain"]
    if p.startswith("+9716") or p.startswith("9716"): return UAE_BASES["sharjah"]
    if p.startswith("+9717") or p.startswith("9717"): return UAE_BASES["rak"]
    if p.startswith("+9719") or p.startswith("9719"): return UAE_BASES["fujairah"]
    return UAE_BASES["dubai"]


# ---------------------------------------------------------------------------
# Vendor selection
# ---------------------------------------------------------------------------
def _find_best_vendor(lat: float, lng: float, service_id: str = "vehicle_recovery") -> tuple[dict, dict] | None:
    """Return (vendor_row, {distance_km, base_lat, base_lng, base_label}) or None.

    v1.24.4: accept any service_id (not just vehicle_recovery). If no vendor
    is found for the requested service we fall back to vehicle_recovery
    so the user always gets *someone* dispatched.
    """
    def _query(svc):
        with db.connect() as c:
            return c.execute(
                "SELECT v.id AS id, v.name AS name, v.phone AS phone, v.email AS email, "
                "       v.rating AS rating, v.completed_jobs AS jobs, v.company AS company, "
                "       vs.price_aed AS price_aed, "
                "       b.lat AS base_lat, b.lng AS base_lng, b.base_label AS base_label "
                "FROM vendors v "
                "JOIN vendor_services vs ON vs.vendor_id = v.id "
                "LEFT JOIN recovery_vendor_base b ON b.vendor_id = v.id "
                "WHERE vs.service_id = ? "
                "  AND COALESCE(vs.active, 1) = 1 "
                "  AND COALESCE(v.is_active, 1) = 1 "
                "  AND COALESCE(v.is_approved, 1) = 1",
                (svc,)
            ).fetchall()

    rows = _query(service_id)
    if not rows and service_id != "vehicle_recovery":
        # Fallback: any vendor at all
        rows = _query("vehicle_recovery")
    if not rows:
        return None

    scored = []
    for r in rows:
        if r["base_lat"] is not None and r["base_lng"] is not None:
            base_lat, base_lng = float(r["base_lat"]), float(r["base_lng"])
            base_label = r["base_label"] or "Servia base"
        else:
            f = _fallback_base_for_vendor_phone(r["phone"])
            base_lat, base_lng, base_label = f["lat"], f["lng"], f["label"]
        d = _haversine_km(lat, lng, base_lat, base_lng)
        rating = float(r["rating"] or 4.5)
        # Higher rating subtracts a bit from "score" so it's preferred on ties.
        score = d - (rating - 4.0) * 1.5
        scored.append((score, d, dict(r), {
            "base_lat": base_lat, "base_lng": base_lng, "base_label": base_label,
        }))
    scored.sort(key=lambda x: x[0])
    _, d, vendor, meta = scored[0]
    meta["distance_km"] = round(d, 2)
    return vendor, meta


def _eta_minutes(distance_km: float) -> int:
    """Rough ETA: 5-min dispatch + 1.6 min/km (urban Dubai average ~38 km/h)."""
    return max(8, int(round(5 + distance_km * 1.6)))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
class DispatchBody(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    accuracy_m: Optional[float] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None     # v1.24.4 — wear onboarding hook
    customer_name: Optional[str] = None
    issue: Optional[str] = None              # breakdown | accident | flat_tyre | battery | fuel | locked_out | other
    vehicle_make: Optional[str] = None       # "Toyota Camry"
    vehicle_plate: Optional[str] = None      # "Dubai N 12345"
    notes: Optional[str] = None              # v1.24.4 — free-form details
    photo_url: Optional[str] = None          # v1.24.4 — uploaded photo URL (mobile only)
    service_id: Optional[str] = "vehicle_recovery"  # v1.24.4 — multi-SOS (vehicle / furniture / electrician / handyman …)
    source: Optional[str] = "web"            # watch | mobile | web | nfc


def _resolve_caller(authorization: str, body_phone: str | None,
                     body_name: str | None) -> tuple[int | None, str, str]:
    """Return (customer_id_or_none, phone, name) — Bearer token wins."""
    token = ""
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if token:
        u = lookup_session(token)
        if u and u.user_type == "customer":
            rec = u.record
            return (u.user_id, rec.get("phone") or body_phone or "",
                    rec.get("name") or body_name or "Servia customer")
    return (None, body_phone or "", body_name or "Roadside customer")


@router.post("/api/recovery/dispatch")
def recovery_dispatch(body: DispatchBody, request: Request,
                       authorization: str = Header(default="")):
    """One-tap recovery dispatch. Returns vendor + booking in <300 ms."""
    _ensure_schema()
    _seed_bases_if_empty()

    cust_id, phone, name = _resolve_caller(authorization, body.customer_phone, body.customer_name)
    if not phone:
        # Anonymous SOS — still dispatch, just flag for callback
        phone = "anonymous-sos"

    pick = _find_best_vendor(body.lat, body.lng)
    if not pick:
        raise HTTPException(503,
            "No recovery vendor available right now. Call our 24/7 hotline +971 56 690 0255.")
    vendor, meta = pick
    distance_km = meta["distance_km"]
    eta = _eta_minutes(distance_km)
    price = float(vendor["price_aed"] or 250)

    # Create the booking (so it shows up in /account.html, dispatch board, etc.)
    issue_label = (body.issue or "breakdown").replace("_", " ").title()
    address_str = (
        f"GPS {body.lat:.5f},{body.lng:.5f}" +
        (f" (±{int(body.accuracy_m)}m)" if body.accuracy_m else "") +
        f" — {issue_label}" +
        (f" — {body.vehicle_make}" if body.vehicle_make else "") +
        (f" [{body.vehicle_plate}]" if body.vehicle_plate else "")
    )
    notes = (
        f"ONE-TAP RECOVERY DISPATCH ({body.source or 'web'}). "
        f"Vendor: {vendor['name']} — {vendor['phone']}. "
        f"Distance {distance_km} km, ETA {eta} min. Price AED {price}."
    )
    today = _dt.date.today().isoformat()
    slot = _dt.datetime.utcnow().strftime("%H:%M")
    bid = ("RV" if (body.service_id == "vehicle_recovery" or not body.service_id)
           else "SO") + secrets.token_hex(4).upper()
    # Customer notes from the request body (separate from the auto-generated dispatch summary)
    customer_notes = (body.notes or "").strip()
    full_notes = notes if not customer_notes else (notes + "\n— customer note: " + customer_notes)
    if body.photo_url:
        full_notes += f"\n— photo: {body.photo_url}"

    with db.connect() as c:
        c.execute(
            "INSERT INTO bookings(id, service_id, target_date, time_slot, customer_name, phone, "
            "address, notes, status, estimated_total, currency, language, source, created_at, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (bid, body.service_id or "vehicle_recovery", today, slot, name, phone, address_str, full_notes,
             "dispatched", price, "AED", "en", body.source or "web", _now(), _now())
        )
        # Auto-assign to the picked vendor
        c.execute(
            "INSERT INTO assignments(booking_id, vendor_id, status, payout_amount, notes, claimed_at) "
            "VALUES(?,?,?,?,?,?)",
            (bid, int(vendor["id"]), "assigned", price * 0.85,
             f"Auto-dispatched by /api/recovery/dispatch (ETA {eta} min)", _now())
        )
        cur = c.execute(
            "INSERT INTO recovery_dispatches(booking_id, customer_id, customer_phone, customer_name, "
            "vehicle_make, vehicle_plate, issue, lat, lng, accuracy_m, vendor_id, eta_min, "
            "price_aed, distance_km, status, source, created_at, "
            "service_id, notes, photo_url, customer_email) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (bid, cust_id, phone, name, body.vehicle_make, body.vehicle_plate,
             body.issue or "breakdown", body.lat, body.lng, body.accuracy_m,
             int(vendor["id"]), eta, price, distance_km, "dispatched",
             body.source or "web", _now(),
             body.service_id or "vehicle_recovery",
             customer_notes or None, body.photo_url or None,
             body.customer_email or None)
        )
        dispatch_id = cur.lastrowid

    db.log_event("recovery", str(dispatch_id), "dispatched", actor=body.source or "web", details={
        "booking_id": bid, "vendor_id": vendor["id"], "vendor_name": vendor["name"],
        "lat": body.lat, "lng": body.lng, "distance_km": distance_km, "eta_min": eta,
    })

    # Best-effort: ping vendor on WhatsApp + admin alert. Never blocks the caller.
    try:
        gmaps = f"https://maps.google.com/?q={body.lat},{body.lng}"
        photo_line = ""
        if body.photo_url:
            full_photo = body.photo_url if body.photo_url.startswith("http") else f"https://servia.ae{body.photo_url}"
            photo_line = f"📷 Customer photo: {full_photo}\n"
        notes_line = ""
        if customer_notes:
            notes_line = f"📝 Notes: {customer_notes}\n"
        msg_v = (
            f"🚨 *SERVIA SOS DISPATCH*\n"
            f"Booking: *{bid}* · {(body.service_id or 'vehicle_recovery').replace('_',' ').title()}\n"
            f"Customer: {name} ({phone})\n"
            f"Issue: {issue_label}\n"
            f"Vehicle: {body.vehicle_make or '—'} {body.vehicle_plate or ''}\n"
            f"{notes_line}"
            f"{photo_line}"
            f"Location: {gmaps}\n"
            f"Distance: {distance_km} km · ETA promised: {eta} min\n"
            f"Payout: AED {round(price * 0.85, 2)}\n"
            f"Reply 'OTW {bid}' when on the way."
        )
        if vendor.get("phone"):
            tools.send_whatsapp(vendor["phone"], msg_v)
        msg_c = (
            f"🛟 *Servia Recovery on the way*\n"
            f"Booking: *{bid}*\n"
            f"Vendor: {vendor['name']} ({vendor['phone']})\n"
            f"ETA: ~{eta} min · {distance_km} km away\n"
            f"Track: https://servia.ae/account.html?b={bid}\n"
            f"Stay safe — turn on hazard lights, stand off the road."
        )
        if phone and not phone.startswith("anonymous"):
            tools.send_whatsapp(phone, msg_c)
    except Exception:
        pass
    try:
        from . import admin_alerts as _aa
        _aa.notify_admin(
            f"🚨 Recovery dispatch *{bid}* → {vendor['name']} ({vendor['phone']})\n"
            f"Customer: {name} ({phone}) · {issue_label}\n"
            f"GPS {body.lat:.4f},{body.lng:.4f} · {distance_km} km · ETA {eta} min · AED {price}",
            kind="recovery_dispatch", urgency="high",
            meta={"dispatch_id": dispatch_id, "booking_id": bid, "vendor_id": vendor["id"]}
        )
    except Exception:
        pass

    return {
        "ok": True,
        "dispatch_id": dispatch_id,
        "booking_id": bid,
        "status": "dispatched",
        "eta_min": eta,
        "distance_km": distance_km,
        "price_aed": price,
        "currency": "AED",
        "vendor": {
            "id": vendor["id"],
            "name": vendor["name"],
            "company": vendor.get("company"),
            "phone": vendor["phone"],
            "rating": float(vendor["rating"] or 4.5),
            "completed_jobs": int(vendor["jobs"] or 0),
            "base_label": meta["base_label"],
            "tel_url":  f"tel:{(vendor['phone'] or '').replace(' ', '')}",
            "wa_url":   f"https://wa.me/{(vendor['phone'] or '').replace(' ', '').lstrip('+')}",
        },
        "call_url":  f"tel:{(vendor['phone'] or '').replace(' ', '')}",
        "track_url": f"/account.html?b={bid}",
        "map_url":   f"https://maps.google.com/?q={body.lat},{body.lng}",
        "message":   f"{vendor['name']} dispatched. ETA {eta} min ({distance_km} km away). Tap to call.",
    }


@router.get("/api/recovery/dispatch/{dispatch_id}")
def get_dispatch(dispatch_id: int):
    _ensure_schema()
    with db.connect() as c:
        r = c.execute(
            "SELECT d.*, v.name AS vendor_name, v.phone AS vendor_phone, "
            "       v.rating AS vendor_rating "
            "FROM recovery_dispatches d "
            "LEFT JOIN vendors v ON v.id = d.vendor_id "
            "WHERE d.id = ?",
            (dispatch_id,)
        ).fetchone()
    if not r:
        raise HTTPException(404, "dispatch not found")
    d = dict(r)
    d["call_url"] = f"tel:{(d.get('vendor_phone') or '').replace(' ', '')}"
    d["track_url"] = f"/account.html?b={d.get('booking_id')}"
    return d


class _CompleteBody(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    note:   Optional[str] = None


@router.post("/api/recovery/dispatch/{dispatch_id}/complete")
def complete_dispatch(dispatch_id: int, body: _CompleteBody):
    _ensure_schema()
    with db.connect() as c:
        r = c.execute(
            "SELECT booking_id, vendor_id, customer_phone FROM recovery_dispatches WHERE id=?",
            (dispatch_id,)
        ).fetchone()
        if not r:
            raise HTTPException(404, "dispatch not found")
        c.execute(
            "UPDATE recovery_dispatches SET status='completed', completed_at=? WHERE id=?",
            (_now(), dispatch_id)
        )
        c.execute(
            "UPDATE bookings SET status='completed', updated_at=? WHERE id=?",
            (_now(), r["booking_id"])
        )
        c.execute(
            "UPDATE assignments SET status='completed', completed_at=? WHERE booking_id=?",
            (_now(), r["booking_id"])
        )
        if body.rating and r["vendor_id"]:
            c.execute(
                "INSERT INTO reviews(booking_id, vendor_id, customer_phone, rating, comment, created_at) "
                "VALUES(?,?,?,?,?,?)",
                (r["booking_id"], r["vendor_id"], r["customer_phone"],
                 body.rating, body.note or "Recovery completed via one-tap", _now())
            )
    db.log_event("recovery", str(dispatch_id), "completed",
                 details={"rating": body.rating, "note": body.note})
    return {"ok": True, "dispatch_id": dispatch_id, "status": "completed"}


@router.post("/api/recovery/dispatch/{dispatch_id}/cancel")
def cancel_dispatch(dispatch_id: int):
    _ensure_schema()
    with db.connect() as c:
        r = c.execute(
            "SELECT booking_id FROM recovery_dispatches WHERE id=?", (dispatch_id,)
        ).fetchone()
        if not r:
            raise HTTPException(404, "dispatch not found")
        c.execute(
            "UPDATE recovery_dispatches SET status='cancelled', completed_at=? WHERE id=?",
            (_now(), dispatch_id)
        )
        c.execute(
            "UPDATE bookings SET status='cancelled', updated_at=? WHERE id=?",
            (_now(), r["booking_id"])
        )
        c.execute(
            "UPDATE assignments SET status='cancelled', completed_at=? WHERE booking_id=?",
            (_now(), r["booking_id"])
        )
    db.log_event("recovery", str(dispatch_id), "cancelled")
    return {"ok": True, "dispatch_id": dispatch_id, "status": "cancelled"}


# ---------------------------------------------------------------------------
@router.get("/api/admin/recovery/list", dependencies=[Depends(require_admin)])
def admin_list(limit: int = 200):
    _ensure_schema()
    with db.connect() as c:
        rows = c.execute(
            "SELECT d.*, v.name AS vendor_name, v.phone AS vendor_phone "
            "FROM recovery_dispatches d "
            "LEFT JOIN vendors v ON v.id = d.vendor_id "
            "ORDER BY d.id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return {"items": [dict(r) for r in rows], "count": len(rows)}


@router.get("/api/admin/recovery/vendors", dependencies=[Depends(require_admin)])
def admin_list_vendors():
    """Show all recovery vendors + their base coordinates (so admin can edit)."""
    _ensure_schema()
    _seed_bases_if_empty()
    with db.connect() as c:
        rows = c.execute(
            "SELECT v.id AS id, v.name, v.phone, v.email, v.rating, v.completed_jobs, "
            "       vs.price_aed, b.lat, b.lng, b.base_label "
            "FROM vendors v "
            "JOIN vendor_services vs ON vs.vendor_id = v.id "
            "LEFT JOIN recovery_vendor_base b ON b.vendor_id = v.id "
            "WHERE vs.service_id='vehicle_recovery' ORDER BY v.rating DESC"
        ).fetchall()
    return {"items": [dict(r) for r in rows]}


class _BaseBody(BaseModel):
    lat: float
    lng: float
    base_label: Optional[str] = None


@router.put("/api/admin/recovery/vendors/{vendor_id}/base",
             dependencies=[Depends(require_admin)])
def admin_set_vendor_base(vendor_id: int, body: _BaseBody):
    _ensure_schema()
    with db.connect() as c:
        c.execute(
            "INSERT OR REPLACE INTO recovery_vendor_base(vendor_id, lat, lng, base_label) "
            "VALUES(?,?,?,?)",
            (vendor_id, body.lat, body.lng, body.base_label)
        )
    return {"ok": True, "vendor_id": vendor_id}
