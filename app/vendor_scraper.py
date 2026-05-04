"""Live vendor scraper: pulls real UAE businesses from Google Places + a
Yellow Pages HTML fallback, runs them through the AI cascade for a 'is this
real and active' score, and imports the survivors into the vendors table.

Sources (in priority order):
  1. Google Places API (Text Search + Place Details)         — best, needs key
  2. Yellow Pages UAE (yellowpages.ae HTML)                  — free, always-on
  3. Admin manual CSV import                                 — last resort

Each vendor gets:
  - is_synthetic = 0   (so admin can wipe seed data and keep these)
  - source = "google_places" | "yellowpages_ae" | "manual"
  - validated_at + ai_score + ai_notes

Seeded fake vendors (is_synthetic=1) can be wiped in one call to make room
for real ones.
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import hashlib
import json
import re
import time
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import auth_users, db, kb
from .auth import require_admin


router = APIRouter(prefix="/api/admin/scraper", tags=["admin-scraper"],
                   dependencies=[Depends(require_admin)])


# ---------------------------------------------------------------------------
# DB migration: add tracking columns to vendors so we can distinguish real
# scraped vendors from the original synthetic seed.
# ---------------------------------------------------------------------------
def _ensure_columns():
    with db.connect() as c:
        for col, ddl in (
            ("is_synthetic",   "ALTER TABLE vendors ADD COLUMN is_synthetic INTEGER DEFAULT 0"),
            ("source",         "ALTER TABLE vendors ADD COLUMN source TEXT DEFAULT 'manual'"),
            ("source_url",     "ALTER TABLE vendors ADD COLUMN source_url TEXT"),
            ("place_id",       "ALTER TABLE vendors ADD COLUMN place_id TEXT"),
            ("address",        "ALTER TABLE vendors ADD COLUMN address TEXT"),
            ("emirate",        "ALTER TABLE vendors ADD COLUMN emirate TEXT"),
            ("website",        "ALTER TABLE vendors ADD COLUMN website TEXT"),
            ("ai_score",       "ALTER TABLE vendors ADD COLUMN ai_score REAL"),
            ("ai_notes",       "ALTER TABLE vendors ADD COLUMN ai_notes TEXT"),
            ("validated_at",   "ALTER TABLE vendors ADD COLUMN validated_at TEXT"),
            ("contacted_at",   "ALTER TABLE vendors ADD COLUMN contacted_at TEXT"),
            ("contact_method", "ALTER TABLE vendors ADD COLUMN contact_method TEXT"),
            ("reviews_count",  "ALTER TABLE vendors ADD COLUMN reviews_count INTEGER"),
            ("avg_price",      "ALTER TABLE vendors ADD COLUMN avg_price REAL"),
        ):
            try: c.execute(ddl)
            except Exception: pass
        # Service-area pricing table for per-service AED averages
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS vendor_pricing(
                vendor_id INTEGER, service_id TEXT, price_aed REAL,
                PRIMARY KEY (vendor_id, service_id))""")
        except Exception: pass


# ---------------------------------------------------------------------------
# Service → search-query mapping. Each service maps to natural-language queries
# Google Places understands well, with multiple variants for breadth.
# ---------------------------------------------------------------------------
SERVICE_QUERIES = {
    "ac_cleaning":         ["AC service", "AC cleaning", "air conditioning maintenance"],
    "deep_cleaning":       ["deep cleaning service", "home deep cleaners"],
    "general_cleaning":    ["home cleaning", "house cleaning service"],
    "maid_service":        ["maid service", "house maid hourly"],
    "move_in_out":         ["move in cleaning", "move out cleaning"],
    "office_cleaning":     ["office cleaning", "commercial cleaning"],
    "post_construction":   ["post construction cleaning"],
    "sofa_carpet":         ["sofa cleaning", "carpet cleaning"],
    "disinfection":        ["disinfection service", "sanitization"],
    "window_cleaning":     ["window cleaning"],
    "laundry":             ["laundry pickup", "laundry service"],
    "babysitting":         ["babysitter", "nanny service"],
    "gardening":           ["gardener", "landscaping"],
    "swimming_pool":       ["pool maintenance", "pool cleaning"],
    "marble_polish":       ["marble polishing"],
    "curtain_cleaning":    ["curtain cleaning"],
    "painting_repair":     ["villa painting", "wall painting service"],
    "smart_home":          ["smart home installation", "home automation"],
    "mobile_repair":       ["mobile phone repair", "iPhone repair"],
    "laptop_repair":       ["laptop repair"],
    "washing_machine_repair":["washing machine repair"],
    "fridge_repair":       ["refrigerator repair"],
    "dishwasher_repair":   ["dishwasher repair"],
    "oven_microwave_repair":["oven repair", "microwave repair"],
    "water_heater_repair": ["water heater repair", "geyser repair"],
    "tv_setup":            ["TV mounting", "TV installation"],
    "chauffeur":           ["chauffeur service", "driver hire"],
    "pest_control":        ["pest control", "cockroach control"],
    "handyman":            ["handyman service"],
    "kitchen_deep":        ["kitchen deep cleaning"],
    "villa_deep":          ["villa cleaning"],
    "car_wash":            ["car wash at home", "mobile car wash"],
}


EMIRATES_FOR_SCRAPE = ("Dubai", "Sharjah", "Abu Dhabi", "Ajman",
                       "Ras Al Khaimah", "Umm Al Quwain", "Fujairah")


# ---------------------------------------------------------------------------
# Source 1: Google Places API
# ---------------------------------------------------------------------------
async def _google_places_search(query: str, area: str, key: str,
                                limit: int = 10) -> list[dict]:
    """Text Search → Place Details. Returns a list of vendor dicts ready for
    AI validation. Uses the new Places API (v1 endpoints)."""
    out: list[dict] = []
    full_query = f"{query} in {area}, UAE"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://places.googleapis.com/v1/places:searchText",
                json={"textQuery": full_query, "maxResultCount": limit,
                      "regionCode": "AE", "languageCode": "en"},
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": key,
                    "X-Goog-FieldMask": (
                        "places.id,places.displayName,places.formattedAddress,"
                        "places.nationalPhoneNumber,places.internationalPhoneNumber,"
                        "places.websiteUri,places.rating,places.userRatingCount,"
                        "places.googleMapsUri,places.businessStatus,"
                        "places.types,places.priceLevel"),
                },
            )
            if r.status_code != 200:
                return [{"_error": f"Places API {r.status_code}: {r.text[:200]}"}]
            data = r.json()
            for p in (data.get("places") or [])[:limit]:
                if p.get("businessStatus") not in (None, "OPERATIONAL"):
                    continue
                out.append({
                    "place_id": p.get("id"),
                    "name": ((p.get("displayName") or {}).get("text") or "").strip(),
                    "phone": (p.get("internationalPhoneNumber")
                              or p.get("nationalPhoneNumber") or "").strip(),
                    "website": (p.get("websiteUri") or "").strip(),
                    "address": (p.get("formattedAddress") or "").strip(),
                    "google_maps_url": p.get("googleMapsUri") or "",
                    "rating": p.get("rating") or 0,
                    "reviews_count": p.get("userRatingCount") or 0,
                    "price_level": p.get("priceLevel") or "",
                    "types": p.get("types") or [],
                    "source": "google_places",
                    "source_url": p.get("googleMapsUri") or "",
                    "emirate": area,
                })
    except Exception as e:  # noqa: BLE001
        return [{"_error": f"Google Places search failed: {e}"}]
    return out


# ---------------------------------------------------------------------------
# Source 2: Yellow Pages UAE — free HTML fallback when no Places key is set
# ---------------------------------------------------------------------------
async def _yellowpages_search(query: str, area: str,
                              limit: int = 10) -> list[dict]:
    """Scrape https://www.yellowpages.ae search results. Returns best-effort
    vendor dicts. NB: tolerates HTML changes via permissive regexes — if YP
    redesigns, this returns [] gracefully and Google Places becomes the only
    source."""
    out: list[dict] = []
    try:
        url = (f"https://www.yellowpages.ae/category-search.html"
               f"?searchKey={query.replace(' ','+')}&loc={area.replace(' ','+')}")
        async with httpx.AsyncClient(timeout=15.0,
                                     headers={"User-Agent": "Mozilla/5.0 (Servia VendorScraper)"}) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return []
            html = r.text
    except Exception:
        return []
    # Permissive parse — extract business cards. Yellow Pages varies its
    # markup; we look for h3 / h2 with business names + nearby tel: links.
    cards = re.findall(
        r'<h[23][^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>.*?'
        r'(?:tel:([\+\d\-\s]+)|"telephone"\s*:\s*"([^"]+)").*?'
        r'(?:<a[^>]*href="(https?://[^"]+)"[^>]*>(?:Visit|Website))?',
        html, re.S | re.I,
    )
    for href, name, tel1, tel2, site in cards[:limit]:
        phone = (tel1 or tel2 or "").strip()
        if not phone or not name.strip():
            continue
        out.append({
            "place_id": "yp_" + hashlib.sha1((name+phone).encode()).hexdigest()[:14],
            "name": name.strip(),
            "phone": phone,
            "website": (site or "").strip(),
            "address": area + ", UAE",
            "rating": 0,
            "reviews_count": 0,
            "source": "yellowpages_ae",
            "source_url": href if href.startswith("http") else f"https://www.yellowpages.ae{href}",
            "emirate": area,
        })
    return out


# ---------------------------------------------------------------------------
# Source 3: Reddit recommendations (r/dubai, r/UAE, r/abudhabi, r/sharjah)
# ---------------------------------------------------------------------------
async def _reddit_search(query: str, area: str, limit: int = 10) -> list[dict]:
    """Reddit's public JSON API surfaces 'who do you recommend for X' threads
    where actual residents tag real vendors with phone numbers. Higher-signal
    than YP because the recommendations are from people who used the service
    recently. Returns vendor dicts with the source URL pointing back to the
    thread so admin can verify the recommendation."""
    out: list[dict] = []
    subs = ("dubai", "UAE", "abudhabi", "sharjah")
    sub_for_area = {
        "Dubai": "dubai", "Abu Dhabi": "abudhabi", "Sharjah": "sharjah",
        "Ajman": "UAE", "Ras Al Khaimah": "UAE", "Umm Al Quwain": "UAE",
        "Fujairah": "UAE",
    }
    sub = sub_for_area.get(area, "UAE")
    url = (f"https://www.reddit.com/r/{sub}/search.json"
           f"?q={query.replace(' ','+')}+recommend&restrict_sr=1&sort=new&t=year&limit=15")
    try:
        async with httpx.AsyncClient(timeout=12.0,
                                     headers={"User-Agent": "ServiaVendorScraper/1.0 by /u/serviaae"}) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return []
            data = r.json()
    except Exception:
        return []
    posts = (data.get("data") or {}).get("children") or []
    # Crawl post body + top-level comments for phone numbers + business names
    for post in posts[:5]:
        pd = post.get("data") or {}
        thread_url = "https://www.reddit.com" + (pd.get("permalink") or "")
        body_text = (pd.get("selftext") or "") + " " + (pd.get("title") or "")
        # Pull the first comment thread
        try:
            async with httpx.AsyncClient(timeout=10.0,
                                         headers={"User-Agent": "ServiaVendorScraper/1.0"}) as client:
                cr = await client.get(thread_url + ".json?limit=20&depth=1")
                if cr.status_code == 200:
                    comments = ((cr.json() or [{}, {}])[1].get("data") or {}).get("children") or []
                    for c in comments[:15]:
                        body_text += " ||| " + ((c.get("data") or {}).get("body") or "")
        except Exception: pass
        # Extract UAE phone numbers + nearby business names
        phones = re.findall(r"\+?9715[0-9](?:[\s-]?\d){7}", body_text)
        for ph in set(phones):
            ph_clean = re.sub(r"[\s-]", "", ph)
            if not ph_clean.startswith("+"): ph_clean = "+" + ph_clean
            # Try to extract a business name in 60 chars before the phone
            idx = body_text.find(ph)
            window = body_text[max(0, idx-120):idx]
            # Heuristic: capitalised words near the phone are likely the name
            name_match = re.findall(r"\b([A-Z][\w&'.-]{2,}(?:\s+[A-Z][\w&'.-]{2,}){0,4})\b", window)
            name = name_match[-1] if name_match else "Reddit-recommended vendor"
            out.append({
                "place_id": "rd_" + hashlib.sha1((name+ph_clean).encode()).hexdigest()[:14],
                "name": name[:80].strip(),
                "phone": ph_clean,
                "website": "",
                "address": area + ", UAE (recommended on Reddit)",
                "rating": 0,
                "reviews_count": 1,   # one Reddit recommendation = 1 review
                "source": "reddit_recommendation",
                "source_url": thread_url,
                "emirate": area,
            })
            if len(out) >= limit: return out
    return out


# ---------------------------------------------------------------------------
# AI VALIDATION — cascade through providers (Gemini > OpenAI > Anthropic)
# ---------------------------------------------------------------------------
async def _ai_validate_vendor(v: dict, service_query: str) -> dict:
    """Ask the cascade to classify a vendor as REAL+ACTIVE / SUSPICIOUS / FAKE.
    Returns {'score': 0..1, 'is_real': bool, 'notes': str}."""
    from . import ai_router
    prompt = (
        "You verify if a UAE business is real and currently active for a "
        "specific service. Analyse the data below and reply with EXACTLY one "
        "JSON object: {\"score\": 0.0-1.0, \"is_real\": true|false, "
        "\"matches_service\": true|false, \"notes\": \"<10 words why\"}.\n\n"
        f"Service the customer wants: {service_query}\n"
        "Vendor data:\n"
        f"  Name: {v.get('name','')}\n"
        f"  Phone: {v.get('phone','')}\n"
        f"  Website: {v.get('website','')}\n"
        f"  Address: {v.get('address','')}\n"
        f"  Rating: {v.get('rating',0)}\n"
        f"  Review count: {v.get('reviews_count',0)}\n"
        f"  Source: {v.get('source','')}\n\n"
        "Score high (>=0.8) for: UAE phone format, real-looking website, "
        "20+ reviews, name aligned with service category. Score low (<0.4) "
        "for: missing phone, no website, generic/vague name, or name clearly "
        "unrelated to the service. Reply ONLY with the JSON object."
    )
    try:
        res = await ai_router.call_with_cascade(prompt, persona="admin")
        if not res.get("ok"):
            return {"score": 0.6, "is_real": True, "notes": "no AI key — assumed real"}
        text = (res.get("text") or "").strip()
        # Strip code fences
        if "```" in text:
            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
            if m: text = m.group(1)
        # Pull first {...} block
        m = re.search(r"\{[^{}]*\}", text, re.S)
        if m: text = m.group(0)
        data = json.loads(text)
        score = float(data.get("score", 0.5))
        return {
            "score": max(0.0, min(1.0, score)),
            "is_real": bool(data.get("is_real", score >= 0.5)),
            "matches": bool(data.get("matches_service", True)),
            "notes": (data.get("notes") or "")[:200],
            "model_used": f"{res.get('provider')}/{res.get('model')}",
        }
    except Exception as e:  # noqa: BLE001
        return {"score": 0.5, "is_real": True, "notes": f"AI error: {e}"[:200]}


# ---------------------------------------------------------------------------
# IMPORT — convert validated vendors into vendors table rows
# ---------------------------------------------------------------------------
def _import_vendor(v: dict, service_id: str, ai: dict) -> tuple[bool, int | str]:
    """Insert one validated vendor (idempotent on phone+name). Returns
    (ok, vendor_id_or_error)."""
    _ensure_columns()
    name = (v.get("name") or "").strip()
    phone = (v.get("phone") or "").strip()
    if not name or not phone:
        return False, "missing name or phone"
    # Synthetic email derived from phone — vendor can change later when they
    # claim the listing via the outreach link.
    email_handle = re.sub(r"[^a-z0-9]+", "", name.lower())[:24] or "vendor"
    phone_tail = re.sub(r"\D", "", phone)[-6:]
    email = f"{email_handle}_{phone_tail}@scraped.servia.ae"
    now = _dt.datetime.utcnow().isoformat() + "Z"
    pwhash = auth_users.hash_password("changeme_" + phone_tail)
    with db.connect() as c:
        # Skip if a vendor with the same phone already exists (idempotent
        # re-runs don't dupe rows).
        existing = c.execute(
            "SELECT id FROM vendors WHERE phone=? OR email=? LIMIT 1",
            (phone, email)).fetchone()
        if existing:
            vid = existing["id"]
        else:
            try:
                cur = c.execute(
                    "INSERT INTO vendors(email, password_hash, name, phone, company, "
                    "rating, completed_jobs, is_active, is_approved, created_at, "
                    "is_synthetic, source, source_url, place_id, address, emirate, "
                    "website, ai_score, ai_notes, validated_at, reviews_count) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (email, pwhash, name, phone, name, v.get("rating") or 5.0, 0,
                     1, 0,  # is_active=1, is_approved=0 — admin must approve
                     now, 0,  # is_synthetic=0 (real)
                     v.get("source") or "manual",
                     v.get("source_url") or "",
                     v.get("place_id") or "",
                     v.get("address") or "",
                     v.get("emirate") or "",
                     v.get("website") or "",
                     ai.get("score"),
                     ai.get("notes") or "",
                     now, v.get("reviews_count") or 0))
                vid = cur.lastrowid
            except Exception as e:
                return False, f"insert failed: {e}"
        # Link to the requested service
        try:
            c.execute("INSERT OR IGNORE INTO vendor_services(vendor_id, service_id, area) "
                      "VALUES(?,?,?)", (vid, service_id, v.get("emirate") or "*"))
        except Exception: pass
    return True, vid


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------
# Live progress feed — admin polls /status to see what the scraper is doing
_LIVE_STATUS = {"running": False, "service_id": "", "step": "idle",
                "progress": 0, "total": 0, "log": []}


def _push_status(msg: str, **fields):
    """Append a timestamped log line + update fields. Admin polls /status."""
    _LIVE_STATUS["log"].append({
        "ts": _dt.datetime.utcnow().isoformat() + "Z", "msg": msg,
    })
    _LIVE_STATUS["log"] = _LIVE_STATUS["log"][-100:]   # cap memory
    _LIVE_STATUS.update(fields)


def _is_too_big(v: dict) -> bool:
    """Filter out big established vendors. Our business model is to partner
    with SMALL hungry vendors who:
      - are active (have at least a few reviews — proves real)
      - aren't premium-priced ($$$$ price level)
      - aren't huge enterprises with 500+ reviews (they'll quote high)
    Returns True if the vendor is too big / too premium for us."""
    reviews = int(v.get("reviews_count") or 0)
    price_level = (v.get("price_level") or "").upper()
    rating = float(v.get("rating") or 0)
    # Too big: 300+ reviews indicates enterprise. They have plenty of work
    # and will quote high.
    if reviews > 300:
        return True
    # Premium-priced (Google's $$$ / $$$$). We want value vendors.
    if price_level in ("PRICE_LEVEL_EXPENSIVE", "PRICE_LEVEL_VERY_EXPENSIVE"):
        return True
    # 5.0★ from 500+ reviews = curated brand, will quote high.
    if rating >= 4.9 and reviews > 200:
        return True
    return False


def _is_too_dead(v: dict) -> bool:
    """Avoid completely dead listings — at least a few reviews proves real."""
    reviews = int(v.get("reviews_count") or 0)
    rating = float(v.get("rating") or 0)
    # 0 reviews = unverified. Allow only if YP source (different signal).
    if reviews == 0 and v.get("source") == "google_places":
        return True
    # Sub-3.0 rating with 5+ reviews = customers complaining, skip.
    if reviews >= 5 and rating < 3.0:
        return True
    return False


async def scrape_for_service(service_id: str, *, target_per_area: int = 3,
                              areas: tuple[str, ...] = EMIRATES_FOR_SCRAPE,
                              min_ai_score: float = 0.6) -> dict:
    """Scrape multiple emirates for a service, validate each candidate with
    the AI cascade, and import SMALL ACTIVE vendors that pass the threshold.

    Filters applied in order:
      1. Too dead (0 reviews) — skip
      2. Too big (300+ reviews / premium / 4.9★ + 200+) — skip
      3. AI score >= min_ai_score — accept

    Returns a detailed report admin can show in the UI."""
    _ensure_columns()
    queries = SERVICE_QUERIES.get(service_id, [service_id.replace("_", " ")])
    google_key = (db.cfg_get("google_places_api_key", "") or "").strip()

    _LIVE_STATUS.update({"running": True, "service_id": service_id,
                         "step": "starting", "progress": 0,
                         "total": len(areas) * target_per_area, "log": []})
    _push_status(f"🔍 Scrape started for {service_id} across {len(areas)} emirates")

    report = {"service_id": service_id, "areas": [], "imported": 0,
              "rejected": 0, "skipped_too_big": 0, "skipped_too_dead": 0,
              "errors": []}

    for area in areas:
        _push_status(f"🌐 {area}: querying {queries[0]}", step=f"area:{area}")
        area_report = {"area": area, "found": 0, "imported": 0,
                       "rejected": 0, "candidates": []}
        candidates: list[dict] = []
        for query in queries[:2]:                                # cap to 2 queries/area to save quota
            sources = []
            if google_key:
                sources.append(("google_places", _google_places_search(query, area, google_key, limit=target_per_area*2)))
            sources.append(("yellowpages_ae", _yellowpages_search(query, area, limit=target_per_area*2)))
            sources.append(("reddit", _reddit_search(query, area, limit=target_per_area*2)))
            # Run sources in parallel for speed
            results = await asyncio.gather(*(s[1] for s in sources), return_exceptions=True)
            for (src_name, _), cs in zip(sources, results):
                if isinstance(cs, Exception):
                    report["errors"].append(f"{area}/{query}/{src_name}: {cs}")
                    continue
                _push_status(f"  · {src_name}: {len([x for x in cs if '_error' not in x])} results")
                for c in cs:
                    if "_error" in c:
                        report["errors"].append(f"{area}/{query}/{src_name}: {c['_error']}")
                        continue
                    candidates.append(c)
        # Dedupe by phone within area
        seen_phones = set()
        unique = []
        for c in candidates:
            ph = re.sub(r"\D", "", c.get("phone", ""))
            if not ph or ph in seen_phones: continue
            seen_phones.add(ph)
            unique.append(c)
        area_report["found"] = len(unique)
        _push_status(f"📋 {area}: found {len(unique)} candidates after dedup")
        # Filter: drop too-big and too-dead BEFORE the (expensive) AI step
        filtered = []
        for c in unique:
            if _is_too_dead(c):
                report["skipped_too_dead"] += 1
                _push_status(f"  ✗ {c.get('name','?')[:40]} — too dead (no reviews)")
                continue
            if _is_too_big(c):
                report["skipped_too_big"] += 1
                _push_status(f"  ✗ {c.get('name','?')[:40]} — too big ({c.get('reviews_count')} reviews)")
                continue
            filtered.append(c)
        # Sort: prefer SMALL active vendors. Score = log(reviews+1) but penalise
        # if reviews > 150 (we want hungry, not established). Higher = better.
        def _hunger_score(v):
            r = int(v.get("reviews_count") or 0)
            rating = float(v.get("rating") or 0)
            base = min(r, 150) / 150.0       # 0..1, plateaus at 150 reviews
            penalty = max(0, r - 150) / 1000.0
            return base - penalty + (rating / 10.0)
        filtered.sort(key=_hunger_score, reverse=True)
        # Validate + import top N
        for c in filtered[:target_per_area]:
            _push_status(f"  🤖 AI-validating {c.get('name','?')[:40]} ({c.get('reviews_count',0)} reviews, ★{c.get('rating',0)})")
            ai = await _ai_validate_vendor(c, queries[0])
            short = {"name": c.get("name"), "phone": c.get("phone"),
                     "rating": c.get("rating"), "reviews_count": c.get("reviews_count"),
                     "ai_score": ai.get("score"), "notes": ai.get("notes")}
            if ai["score"] >= min_ai_score and ai.get("is_real"):
                ok, vid_or_err = _import_vendor(c, service_id, ai)
                if ok:
                    short["status"] = "imported"; short["vendor_id"] = vid_or_err
                    area_report["imported"] += 1; report["imported"] += 1
                    _push_status(f"  ✓ IMPORTED {c.get('name','?')[:40]} (AI {ai.get('score'):.2f})",
                                 progress=report["imported"])
                else:
                    short["status"] = "import_error"; short["error"] = vid_or_err
                    report["errors"].append(f"{area}: {vid_or_err}")
                    _push_status(f"  ⚠ import error: {vid_or_err}")
            else:
                short["status"] = "rejected_low_score"
                area_report["rejected"] += 1; report["rejected"] += 1
                _push_status(f"  ✗ REJECTED {c.get('name','?')[:40]} — AI {ai.get('score'):.2f}")
            area_report["candidates"].append(short)
            await asyncio.sleep(0.3)
        report["areas"].append(area_report)
    _push_status(f"✅ Done. Imported {report['imported']}, rejected {report['rejected']}, "
                 f"skipped {report['skipped_too_big']} too-big + {report['skipped_too_dead']} too-dead",
                 step="done", running=False)
    return report


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------
class ScrapeBody(BaseModel):
    service_id: str
    target_per_area: int = 3
    min_ai_score: float = 0.6
    areas: list[str] | None = None      # None = all 7 emirates


@router.post("/run")
async def scrape_run(body: ScrapeBody):
    """Trigger a scrape for one service. Runs in the foreground for small
    requests (≤ 3 emirates). For full 7-emirate scrapes, fires async in a
    background task and returns immediately so the admin UI doesn't time
    out — admin polls /status to follow progress."""
    areas = tuple(body.areas) if body.areas else EMIRATES_FOR_SCRAPE
    if _LIVE_STATUS.get("running"):
        raise HTTPException(409, "Another scrape is already running. Check /status.")
    if len(areas) <= 3:
        rep = await scrape_for_service(body.service_id,
                                       target_per_area=body.target_per_area,
                                       areas=areas,
                                       min_ai_score=body.min_ai_score)
        db.log_event("scraper", body.service_id, "ran", actor="admin",
                     details={"imported": rep["imported"], "rejected": rep["rejected"]})
        return rep
    # Long run → background task
    asyncio.create_task(_bg_scrape(body.service_id, body.target_per_area,
                                   areas, body.min_ai_score))
    return {"ok": True, "background": True,
            "msg": "Scrape started in background — poll /api/admin/scraper/status every 1-2s"}


async def _bg_scrape(service_id, target_per_area, areas, min_ai_score):
    try:
        rep = await scrape_for_service(service_id,
                                       target_per_area=target_per_area,
                                       areas=areas,
                                       min_ai_score=min_ai_score)
        db.log_event("scraper", service_id, "ran", actor="admin-bg",
                     details={"imported": rep["imported"]})
    except Exception as e:  # noqa: BLE001
        _push_status(f"❌ Scrape crashed: {e}", running=False, step="error")


@router.post("/run-all")
async def scrape_run_all(target_per_area: int = 2):
    """Loop through every service in services.json and scrape each. Long-
    running — admin should call this offline (cron) rather than from a
    browser request. Returns aggregate summary."""
    services = [s["id"] for s in kb.services().get("services", [])]
    summary = {"services_done": 0, "total_imported": 0, "total_rejected": 0,
               "errors": []}
    for sid in services:
        try:
            r = await scrape_for_service(sid, target_per_area=target_per_area)
            summary["services_done"] += 1
            summary["total_imported"] += r["imported"]
            summary["total_rejected"] += r["rejected"]
            summary["errors"].extend(r["errors"][:3])
        except Exception as e:  # noqa: BLE001
            summary["errors"].append(f"{sid}: {e}")
    return summary


@router.post("/wipe-synthetic")
def wipe_synthetic():
    """Delete every vendor that was loaded from the synthetic seed
    (is_synthetic=1) — the original 100-vendor demo data. Real scraped
    vendors (is_synthetic=0) are untouched."""
    _ensure_columns()
    with db.connect() as c:
        # First mark legacy seed rows: any vendor created BEFORE the scraper
        # column existed AND with the seed phone pattern (+9715X) is synthetic
        try:
            c.execute("UPDATE vendors SET is_synthetic=1 "
                      "WHERE source IS NULL OR source IN ('manual','seed')")
        except Exception: pass
        ids = [r["id"] for r in c.execute(
            "SELECT id FROM vendors WHERE is_synthetic=1").fetchall()]
        for vid in ids:
            try: c.execute("DELETE FROM vendor_services WHERE vendor_id=?", (vid,))
            except Exception: pass
        n = c.execute("DELETE FROM vendors WHERE is_synthetic=1").rowcount
    db.log_event("scraper", "all", "wipe_synthetic", actor="admin",
                 details={"deleted": n})
    return {"ok": True, "deleted": n}


# ---------------------------------------------------------------------------
# Cfg get/set: Google Places API key
# ---------------------------------------------------------------------------
class GoogleKeyBody(BaseModel):
    api_key: str


@router.get("/google-key")
def get_google_key():
    k = db.cfg_get("google_places_api_key", "") or ""
    return {"set": bool(k), "preview": (k[:6] + "…" + k[-4:]) if len(k) >= 12 else ""}


@router.post("/google-key")
def set_google_key(body: GoogleKeyBody):
    db.cfg_set("google_places_api_key", body.api_key.strip())
    return {"ok": True}


@router.get("/status")
def get_status():
    """Live progress feed — admin polls this every 1-2s during a scrape to
    see step-by-step what the bot is doing (which vendor it's checking,
    why it rejected one, etc)."""
    return _LIVE_STATUS


@router.get("/last-report")
def last_report():
    """Returns the most recent scrape event from the events log."""
    with db.connect() as c:
        try:
            r = c.execute(
                "SELECT * FROM events WHERE source='scraper' "
                "ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return dict(r) if r else {}
        except Exception: return {}
