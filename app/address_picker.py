"""v1.24.84 — Pin-based address picker backend.

Uses OpenStreetMap Nominatim (free, no API key) for reverse geocoding.
Cached server-side to avoid hammering the public service.

UAE city guard: bounding box per emirate. Cross-checks the marker's
coordinates against the city the user claims to be in. If mismatch,
returns a friendly correction.
"""
from __future__ import annotations
import json as _json
import time
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel

import httpx

router = APIRouter(tags=["address-picker"])


# UAE emirate bounding boxes — generous to avoid false rejections
# Source: OpenStreetMap relations + manual padding.
EMIRATE_BOXES: dict[str, tuple[float, float, float, float]] = {
    # name → (south_lat, west_lng, north_lat, east_lng)
    "dubai":         (24.79, 54.85, 25.39, 55.65),
    "abu_dhabi":     (22.50, 51.50, 25.10, 56.00),
    "sharjah":       (24.95, 55.30, 25.55, 56.40),
    "ajman":         (25.30, 55.40, 25.60, 56.00),
    "umm_al_quwain": (25.45, 55.50, 25.78, 56.05),
    "ras_al_khaimah":(25.65, 55.70, 26.20, 56.45),
    "fujairah":      (24.95, 55.85, 26.00, 56.65),
}


def _bbox_area(b: tuple[float, float, float, float]) -> float:
    return abs((b[2] - b[0]) * (b[3] - b[1]))


# Authoritative emirate detection via NEAREST CITY CENTRE.
# Bbox alone fails for irregular emirate shapes (Dubai's bbox covers
# all of Sharjah city — they share a border). Using nearest-centroid
# distance gives the correct answer for any point inside the UAE.
EMIRATE_CENTRES = {
    "dubai":          (25.20, 55.27),
    "abu_dhabi":      (24.47, 54.37),
    "sharjah":        (25.346, 55.420),
    "ajman":          (25.405, 55.500),
    "umm_al_quwain":  (25.555, 55.555),
    "ras_al_khaimah": (25.789, 55.943),
    "fujairah":       (25.128, 56.327),
}


def _which_emirate(lat: float, lng: float) -> str | None:
    """Return the emirate whose city centre is nearest to (lat, lng),
    PROVIDED the point is within UAE's overall bbox. Returns None for
    points outside UAE."""
    # Quick reject: must fall in UAE's overall bbox
    if not (22.5 <= lat <= 26.4 and 51.5 <= lng <= 56.7):
        return None
    best_name = None
    best_d = float("inf")
    for name, (clat, clng) in EMIRATE_CENTRES.items():
        d = (lat - clat) ** 2 + (lng - clng) ** 2
        if d < best_d:
            best_d = d
            best_name = name
    return best_name


# Tiny in-memory cache: key = "lat,lng" rounded to 4 decimals (~11m).
_GEO_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 24 * 60 * 60  # 1 day
_NOMINATIM_DELAY = 1.05    # Nominatim usage policy: ≥1 req/sec


def _cache_key(lat: float, lng: float) -> str:
    # zero-padded to 4 decimals so "25.078" and "25.0780" hash to the same key
    return f"{lat:.4f},{lng:.4f}"


def _reverse_geocode_nominatim(lat: float, lng: float) -> dict:
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat, "lon": lng,
        "format": "json",
        "addressdetails": 1,
        "zoom": 18,
        "accept-language": "en",
    }
    headers = {
        "User-Agent": "Servia/1.24 (https://servia.ae; admin@servia.ae)",
    }
    try:
        with httpx.Client(timeout=8.0) as c:
            r = c.get(url, params=params, headers=headers)
        if r.status_code != 200:
            return {"ok": False, "error": f"nominatim {r.status_code}"}
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def reverse_geocode(lat: float, lng: float) -> dict:
    """Public function — cached + UAE-aware."""
    key = _cache_key(lat, lng)
    now = time.time()
    if key in _GEO_CACHE:
        ts, val = _GEO_CACHE[key]
        if now - ts < _CACHE_TTL:
            return val
    raw = _reverse_geocode_nominatim(lat, lng)
    if "error" in raw:
        return {"ok": False, "error": raw["error"]}
    addr = raw.get("address", {}) or {}
    out = {
        "ok": True,
        "lat": lat, "lng": lng,
        "city": (addr.get("city") or addr.get("state") or
                 addr.get("town") or addr.get("village") or "").strip(),
        "area": (addr.get("suburb") or addr.get("neighbourhood") or
                 addr.get("city_district") or addr.get("quarter") or
                 addr.get("residential") or "").strip(),
        "road": (addr.get("road") or addr.get("pedestrian") or "").strip(),
        "building": (addr.get("building") or addr.get("house_number") or "").strip(),
        "country": (addr.get("country") or "").strip(),
        "country_code": (addr.get("country_code") or "").strip().lower(),
        "display_name": raw.get("display_name") or "",
        "emirate": _which_emirate(lat, lng),
    }
    _GEO_CACHE[key] = (now, out)
    return out


class GeocodeReq(BaseModel):
    lat: float
    lng: float


@router.post("/api/geocode/reverse")
def api_reverse(req: GeocodeReq):
    if not (-90 <= req.lat <= 90) or not (-180 <= req.lng <= 180):
        return {"ok": False, "error": "invalid lat/lng"}
    return reverse_geocode(req.lat, req.lng)


class CityCheckReq(BaseModel):
    lat: float
    lng: float
    claimed_city: str   # e.g. "dubai", "Dubai", "DUBAI"


@router.post("/api/geocode/check-city")
def api_check_city(req: CityCheckReq):
    """Confirm the pin actually falls inside the bounding box of the
    city the customer claims. Returns the actual emirate so the UI can
    auto-correct."""
    actual = _which_emirate(req.lat, req.lng)
    claimed = (req.claimed_city or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not actual:
        return {"ok": False, "error": "outside UAE bounding boxes",
                "actual_emirate": None}
    matches = (actual == claimed) or (claimed in actual) or (actual in claimed)
    return {
        "ok": True,
        "claimed_city": req.claimed_city,
        "actual_emirate": actual,
        "matches": matches,
        "suggestion": (
            f"Your pin is in {actual.replace('_',' ').title()}. "
            f"You typed '{req.claimed_city}'. Update?" if not matches else None
        ),
    }
