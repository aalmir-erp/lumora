#!/usr/bin/env python3
"""Scrape UAE vehicle-recovery vendors from OpenStreetMap Overpass API
(completely free, no API key, no Cloudflare blocks since OSM serves
unauthenticated queries).

Queries OSM for nodes/ways tagged as:
  · amenity=car_repair  (general repair shops, many do roadside)
  · shop=car_repair
  · service=tyres / tyre_change / battery_charging
  · operator~"recovery|towing|breakdown"

Filters to UAE bounding box, dedup by phone, output JSON.

Usage (production / Railway):
    python3 .scripts/scrape-uae-recovery-osm.py > app/data/vendors_recovery_uae.json

Idempotent. Safe to re-run.
"""
from __future__ import annotations
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# UAE bounding box (covers all 7 emirates + Al Ain + Hatta enclave)
UAE_BBOX = "(22.5, 51.0, 26.5, 56.5)"

OVERPASS = "https://overpass-api.de/api/interpreter"

QUERIES = [
    # Standard car-repair shops — many in UAE offer roadside / towing
    f"""[out:json][timeout:60];
       (node[amenity=car_repair]{UAE_BBOX};
        way[amenity=car_repair]{UAE_BBOX};
        node[shop=car_repair]{UAE_BBOX};
       );
       out tags center;""",
    # Tyre service points (often have recovery)
    f"""[out:json][timeout:60];
       (node[shop=tyres]{UAE_BBOX};
        way[shop=tyres]{UAE_BBOX};
        node[shop="car_parts"]{UAE_BBOX};
       );
       out tags center;""",
    # Filling stations with recovery (ENOC / ADNOC roadside)
    f"""[out:json][timeout:60];
       (node[amenity=fuel][operator~"ENOC|ADNOC|EPPCO|Emarat",i]{UAE_BBOX};
       );
       out tags center;""",
    # Anything explicitly tagged with "recovery" or "tow" in name
    f"""[out:json][timeout:60];
       (node[name~"recovery|towing|breakdown",i]{UAE_BBOX};
        way[name~"recovery|towing|breakdown",i]{UAE_BBOX};
       );
       out tags center;""",
]


def fetch_overpass(q: str) -> dict:
    data = ("data=" + urllib.parse.quote(q)).encode()
    req = urllib.request.Request(OVERPASS, data=data,
        headers={"User-Agent": "Servia-vendor-scraper/1.0 (contact: hello@servia.ae)"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ⚠ overpass error: {e}", file=sys.stderr)
        return {"elements": []}


def emirate_for_latlng(lat: float, lng: float) -> str:
    """Rough emirate from coords. Good enough for vendor base assignment."""
    # Dubai ~ 24.95-25.40N, 54.85-55.65E
    if 24.8 <= lat <= 25.45 and 54.85 <= lng <= 55.65: return "dubai"
    # Abu Dhabi ~ 22.5-25.0N, 51.5-55.0E (excluding Dubai band)
    if 22.5 <= lat <= 24.7 and 51.5 <= lng <= 55.5:    return "abu_dhabi"
    # Sharjah ~ 25.10-25.50N, 55.30-55.80E
    if 25.05 <= lat <= 25.55 and 55.30 <= lng <= 55.85: return "sharjah"
    # Ajman ~ 25.40-25.50N, 55.40-55.60E
    if 25.38 <= lat <= 25.50 and 55.38 <= lng <= 55.65: return "ajman"
    # Umm Al Quwain ~ 25.55N, 55.55E
    if 25.50 <= lat <= 25.70 and 55.45 <= lng <= 55.85: return "uaq"
    # Ras Al Khaimah ~ 25.65-26.10N, 55.85-56.20E
    if 25.60 <= lat <= 26.20 and 55.65 <= lng <= 56.30: return "rak"
    # Fujairah ~ 25.10-25.85N, 56.20-56.40E
    if 25.10 <= lat <= 25.90 and 56.10 <= lng <= 56.50: return "fujairah"
    return "uae"


def normalize_phone(raw: str) -> str | None:
    if not raw: return None
    digits = re.sub(r"[^\d+]", "", raw)
    if digits.startswith("00"): digits = "+" + digits[2:]
    if digits.startswith("0") and len(digits) >= 9: digits = "+971" + digits[1:]
    if not digits.startswith("+"): digits = "+" + digits
    # UAE phones are typically +971 followed by 8-9 digits
    if digits.startswith("+971") and 11 <= len(digits) <= 13:
        return digits
    return None


def categorize(name: str, tags: dict) -> list[str]:
    """Return the category list for this vendor."""
    n = (name or "").lower()
    cats = []
    if any(k in n for k in ("recovery", "towing", "tow truck", "breakdown")):
        cats.append("tow")
    if any(k in n for k in ("battery",)) or tags.get("service:vehicle:battery_charging") == "yes":
        cats.append("battery")
    if any(k in n for k in ("tyre", "tire", "wheel")):
        cats.append("tyre")
    if any(k in n for k in ("locksmith", "key", "lockout")):
        cats.append("lockout")
    if any(k in n for k in ("garage", "auto", "motor", "service")):
        cats.append("garage")
    if "24" in n or "open_24/7" in (tags.get("opening_hours") or "").lower():
        cats.append("24/7")
    return cats or ["garage"]


def main():
    out = Path("app/data/vendors_recovery_uae.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = {}
    print(f"Fetching from OpenStreetMap Overpass API…", file=sys.stderr)
    for i, q in enumerate(QUERIES, 1):
        print(f"  [{i}/{len(QUERIES)}] {q[:60]}…", file=sys.stderr)
        d = fetch_overpass(q)
        for el in d.get("elements", []):
            tags = el.get("tags", {})
            name = (tags.get("name") or "").strip()
            if not name: continue
            phone = normalize_phone(tags.get("phone") or tags.get("contact:phone") or "")
            email = (tags.get("email") or tags.get("contact:email") or "").strip().lower() or None
            website = (tags.get("website") or tags.get("contact:website") or "").strip() or None
            lat = el.get("lat") or (el.get("center") or {}).get("lat")
            lng = el.get("lon") or (el.get("center") or {}).get("lon")
            if not lat or not lng: continue
            emirate = emirate_for_latlng(float(lat), float(lng))
            cats = categorize(name, tags)
            # Dedupe by phone (when present) else by (name + lat round)
            key = phone or f"{name.lower()}|{round(float(lat),3)}|{round(float(lng),3)}"
            if key in seen: continue
            address_parts = [tags.get("addr:street"), tags.get("addr:housenumber"),
                             tags.get("addr:suburb"), tags.get("addr:city")]
            address = ", ".join(p for p in address_parts if p) or None
            seen[key] = {
                "name":        name,
                "phone":       phone,
                "email":       email,
                "website":     website,
                "lat":         float(lat),
                "lng":         float(lng),
                "emirate":     emirate,
                "address":     address,
                "categories":  cats,
                "source":      "openstreetmap",
                "osm_id":      f"{el.get('type','node')}/{el.get('id','')}",
                "needs_phone_verification": phone is None,
            }
        time.sleep(2)  # respectful Overpass rate
    print(f"Found {len(seen)} unique vendors", file=sys.stderr)
    out.write_text(json.dumps({
        "_note": "UAE vehicle-recovery vendors scraped from OpenStreetMap. "
                 "Phones may need verification — check website / call to confirm.",
        "_generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "_count": len(seen),
        "vendors": list(seen.values()),
    }, indent=2, ensure_ascii=False))
    print(f"✓ wrote {out} ({len(seen)} vendors)", file=sys.stderr)


if __name__ == "__main__":
    main()
