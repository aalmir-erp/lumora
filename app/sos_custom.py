"""Customer-defined SOS shortcut buttons (v1.24.11).

A user can save a fully-pre-configured one-tap dispatch:
  e.g. "🛞 My Marina flat tyre" → service_id=vehicle_recovery, issue=flat_tyre,
  lat/lng=Marina Pinnacle, building=…, notes="bring jack", photo_url=…

The save returns a button id. From any Servia surface (mobile /sos.html,
wear "My SOS" tile, future home-screen widget) the user can dispatch it
in ONE TAP — no service grid, no issue picker, no GPS prompt, no notes
field. The stored config is the dispatch.

Tables:
  custom_sos_buttons
    id              INTEGER PK
    customer_id     INTEGER (FK customers.id)
    label           TEXT (e.g. "Tyre at Marina")
    emoji           TEXT (e.g. "🛞")
    color           TEXT (e.g. "#DC2626")
    service_id      TEXT
    sub_option      TEXT (issue type, e.g. "flat_tyre")
    lat / lng       REAL
    address         TEXT
    building        TEXT
    flat            TEXT
    notes           TEXT
    photo_url       TEXT
    sort_order      INTEGER (drag-to-reorder later)
    created_at      TEXT
    updated_at      TEXT

Endpoints:
  POST   /api/sos/custom                    — create (auth required)
  GET    /api/sos/custom/me                 — list mine (auth required)
  PUT    /api/sos/custom/{id}               — update (auth + ownership)
  DELETE /api/sos/custom/{id}               — delete (auth + ownership)
  POST   /api/sos/custom/{id}/dispatch      — one-tap dispatch using stored config

The dispatch endpoint is also auth-gated so anyone can't call it on
your behalf.
"""
from __future__ import annotations

import datetime as _dt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field

from . import db, recovery
from .auth_users import lookup_session, current_customer


router = APIRouter()


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


def _now() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


# ---------------------------------------------------------------------------
class _CustomSosBody(BaseModel):
    label:      str = Field(..., min_length=1, max_length=60)
    emoji:      Optional[str] = "🆘"
    color:      Optional[str] = "#DC2626"
    service_id: str
    sub_option: Optional[str] = None
    lat:        Optional[float] = None
    lng:        Optional[float] = None
    address:    Optional[str] = None
    building:   Optional[str] = None
    flat:       Optional[str] = None
    notes:      Optional[str] = None
    photo_url:  Optional[str] = None
    sort_order: Optional[int] = 0


@router.post("/api/sos/custom")
def create_custom(body: _CustomSosBody,
                   user = Depends(current_customer)):
    """Save a one-tap SOS shortcut for the authenticated customer."""
    _ensure_schema()
    with db.connect() as c:
        cur = c.execute(
            "INSERT INTO custom_sos_buttons(customer_id, label, emoji, color, service_id, "
            "sub_option, lat, lng, address, building, flat, notes, photo_url, sort_order, "
            "created_at, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (user.user_id, body.label, body.emoji or "🆘", body.color or "#DC2626",
             body.service_id, body.sub_option, body.lat, body.lng, body.address,
             body.building, body.flat, body.notes, body.photo_url,
             body.sort_order or 0, _now(), _now())
        )
        bid = cur.lastrowid
        row = c.execute("SELECT * FROM custom_sos_buttons WHERE id=?", (bid,)).fetchone()
    db.log_event("sos_custom", str(bid), "created",
                 actor=str(user.user_id),
                 details={"label": body.label, "service_id": body.service_id})
    return {"ok": True, "button": dict(row)}


@router.get("/api/sos/custom/me")
def list_mine(user = Depends(current_customer)):
    """All custom SOS buttons for the authenticated customer."""
    _ensure_schema()
    with db.connect() as c:
        rows = c.execute(
            "SELECT * FROM custom_sos_buttons WHERE customer_id=? "
            "ORDER BY sort_order ASC, id ASC",
            (user.user_id,)
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
            "photo_url=?, sort_order=?, updated_at=? WHERE id=?",
            (body.label, body.emoji or "🆘", body.color or "#DC2626", body.service_id,
             body.sub_option, body.lat, body.lng, body.address, body.building,
             body.flat, body.notes, body.photo_url, body.sort_order or 0,
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
@router.post("/api/sos/custom/{btn_id}/dispatch")
def dispatch_custom(btn_id: int, request: Request,
                     authorization: str = Header(default="")):
    """One-tap dispatch using a stored custom SOS config.

    No body required — everything (service, issue, location, notes, photo)
    is pulled from the saved button. Ownership is enforced so a stranger
    can't trigger your customised dispatch.
    """
    _ensure_schema()
    user = lookup_session(_bearer(authorization))
    if not user or user.user_type != "customer":
        raise HTTPException(401, "customer login required")
    with db.connect() as c:
        row = c.execute(
            "SELECT * FROM custom_sos_buttons WHERE id=? AND customer_id=?",
            (btn_id, user.user_id)
        ).fetchone()
    if not row:
        raise HTTPException(404, "button not found")

    # Reuse recovery.recovery_dispatch by constructing a DispatchBody.
    if row["lat"] is None or row["lng"] is None:
        raise HTTPException(400,
            "button has no location saved — edit it and pin a spot first")
    addr_bits = []
    if row["building"]: addr_bits.append(row["building"])
    if row["flat"]:     addr_bits.append(row["flat"])
    if row["address"]:  addr_bits.append(row["address"])
    addr_str = " · ".join(addr_bits) if addr_bits else None

    body = recovery.DispatchBody(
        lat=float(row["lat"]),
        lng=float(row["lng"]),
        accuracy_m=10.0,
        customer_phone=user.record.get("phone"),
        customer_email=user.record.get("email"),
        customer_name=user.record.get("name"),
        issue=row["sub_option"] or "sos",
        notes=(row["notes"] or "") + (" · " + addr_str if addr_str else ""),
        photo_url=row["photo_url"],
        service_id=row["service_id"] or "vehicle_recovery",
        source="custom_sos",
    )
    return recovery.recovery_dispatch(body, request, authorization)


def _bearer(auth: str) -> str:
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""
