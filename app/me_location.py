"""v1.24.29 — /api/me/location for the watch + web location bar.

GET  /api/me/location  -> latest cached area+emirate (lightweight read for
                          the watch tile so it can render before any GPS
                          handshake).
POST /api/me/location  -> {lat, lng, accuracy_m?} → reverse-geocode via
                          OpenStreetMap Nominatim, persist to
                          saved_addresses (creates a default row if none),
                          return {area, emirate}.

Why a dedicated endpoint? saved_addresses is structured (building, flat,
street, etc.) which is overkill for the watch's "I'm here, dispatch SOS"
flow. The watch only needs area+emirate to display "📍 Marina Crown,
Dubai". The full editor still lives at /me.html on the phone.
"""

from __future__ import annotations
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import db
from .auth_users import current_customer

router = APIRouter()


class _LocBody(BaseModel):
    lat: float
    lng: float
    accuracy_m: Optional[float] = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _reverse_geocode(lat: float, lng: float) -> tuple[str, str]:
    """Return (area, emirate). Best-effort — Nominatim is free + no key."""
    try:
        q = urllib.parse.urlencode({
            "lat": lat, "lon": lng,
            "format": "jsonv2", "zoom": 14, "addressdetails": 1,
        })
        req = urllib.request.Request(
            f"https://nominatim.openstreetmap.org/reverse?{q}",
            headers={"User-Agent": "ServiaWear/1 (+https://servia.ae)"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
        addr = data.get("address", {}) or {}
        # Nominatim's most useful fields, in priority order
        area = (addr.get("neighbourhood") or addr.get("suburb")
                or addr.get("village") or addr.get("town")
                or addr.get("city_district") or addr.get("city")
                or data.get("name") or f"{lat:.4f},{lng:.4f}")
        emirate = (addr.get("state") or addr.get("region") or "")
        # Normalise common UAE emirate spellings
        if emirate:
            up = emirate.replace("Emirate of ", "").strip()
            emirate = up
        return str(area), str(emirate)
    except Exception:  # noqa: BLE001
        return f"{lat:.4f},{lng:.4f}", ""


@router.get("/api/me/location")
def get_location(user=Depends(current_customer)):
    """Return latest cached area+emirate from saved_addresses."""
    with db.connect() as c:
        row = c.execute(
            "SELECT area, emirate, address FROM saved_addresses "
            "WHERE customer_id=? ORDER BY is_default DESC, id DESC LIMIT 1",
            (user.user_id,),
        ).fetchone()
    if not row:
        return {"area": None, "emirate": None, "address": None}
    return {
        "area": row["area"],
        "emirate": row["emirate"],
        "address": row["address"],
    }


@router.post("/api/me/location")
def set_location(body: _LocBody, user=Depends(current_customer)):
    """Reverse-geocode + persist as default saved_address."""
    if not (-90 <= body.lat <= 90 and -180 <= body.lng <= 180):
        raise HTTPException(status_code=400, detail="lat/lng out of range")

    area, emirate = _reverse_geocode(body.lat, body.lng)
    full_address = area + (", " + emirate if emirate else "")

    with db.connect() as c:
        existing = c.execute(
            "SELECT id FROM saved_addresses "
            "WHERE customer_id=? AND is_default=1 LIMIT 1",
            (user.user_id,),
        ).fetchone()
        if existing:
            c.execute(
                "UPDATE saved_addresses SET area=?, emirate=?, address=? "
                "WHERE id=?",
                (area, emirate, full_address, existing["id"]),
            )
        else:
            c.execute(
                "INSERT INTO saved_addresses(customer_id, label, address, "
                "area, emirate, is_default, created_at) "
                "VALUES(?, ?, ?, ?, ?, 1, ?)",
                (user.user_id, "watch-gps", full_address, area, emirate,
                 _now_iso()),
            )

    db.log_event("me_location", str(user.user_id), "updated",
                 actor=str(user.user_id),
                 details={"lat": body.lat, "lng": body.lng,
                          "area": area, "emirate": emirate})

    return {"ok": True, "area": area, "emirate": emirate,
            "address": full_address}
