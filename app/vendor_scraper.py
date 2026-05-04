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


# Realistic browser User-Agent pool. We pick one per request so we don't
# get fingerprinted as a single bot. Mix of Chrome / Safari / Firefox on
# Mac / Windows / Linux so any pattern detection fails.
_UA_POOL = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.83",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]
import random as _random
def _rand_ua() -> str:
    return _random.choice(_UA_POOL)


async def _http_get(url: str, *, timeout: float = 15.0,
                    follow_redirects: bool = True,
                    extra_headers: dict | None = None,
                    via_scrapingbee: bool = False) -> tuple[int, str]:
    """Unified HTTP GET with rotating UA + optional ScrapingBee proxy.
    Returns (status, body_text). If ScrapingBee key is set in cfg AND
    via_scrapingbee=True, route through their proxy to bypass blocks."""
    headers = {
        "User-Agent": _rand_ua(),
        "Accept": "text/html,application/xhtml+xml,application/json",
        "Accept-Language": "en-US,en-AE,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "no-cache",
    }
    if extra_headers: headers.update(extra_headers)
    sb_key = (db.cfg_get("scrapingbee_api_key", "") or "").strip()
    if via_scrapingbee and sb_key:
        proxied = (f"https://app.scrapingbee.com/api/v1/?api_key={sb_key}"
                   f"&url={url}&render_js=false&country_code=ae")
        try:
            async with httpx.AsyncClient(timeout=timeout) as c:
                r = await c.get(proxied)
                return r.status_code, r.text
        except Exception:
            pass   # fall through to direct
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=follow_redirects,
                                     headers=headers) as c:
            r = await c.get(url)
            return r.status_code, r.text
    except Exception as e:
        return 0, f"__error__: {e}"


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
    """Scrape Yellow Pages UAE. Tries multiple URL patterns because YP has
    been redesigned 3x. Returns whatever the first working URL gives back."""
    out: list[dict] = []
    # Try every known URL pattern in order — first one that returns 200 wins
    URL_PATTERNS = [
        # Current (post-2024 redesign): /search-listing/<query>/<area>
        f"https://www.yellowpages.ae/search-listing/{query.replace(' ','-')}/{area.lower().replace(' ','-')}",
        # Path-based: /<query>-in-<area>.html
        f"https://www.yellowpages.ae/{query.replace(' ','-')}-in-{area.lower().replace(' ','-')}.html",
        # Older query form
        f"https://www.yellowpages.ae/search?q={query.replace(' ','+')}&loc={area.replace(' ','+')}",
        # Original (pre-2023)
        f"https://www.yellowpages.ae/category-search.html?searchKey={query.replace(' ','+')}&loc={area.replace(' ','+')}",
    ]
    html = ""
    used_url = ""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True,
                headers={"User-Agent":
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9"}) as client:
            for pattern in URL_PATTERNS:
                try:
                    r = await client.get(pattern)
                    if r.status_code == 200 and len(r.text) > 5000:
                        html = r.text; used_url = pattern; break
                except Exception: continue
        if not html:
            return [{"_error": f"YP no working URL pattern (tried {len(URL_PATTERNS)})"}]
    except Exception as e:
        return [{"_error": f"YP fetch failed: {e}"}]
    url = used_url
    # Pass 1: JSON-LD LocalBusiness blocks (Yellow Pages embeds these for SEO)
    for ld in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                         html, re.S | re.I):
        try:
            data = json.loads(ld)
            if not isinstance(data, dict): continue
            if data.get("@type") not in ("LocalBusiness", "Organization"):
                continue
            phone = (data.get("telephone") or "").strip()
            name = (data.get("name") or "").strip()
            if not phone or not name: continue
            out.append({
                "place_id": "yp_" + hashlib.sha1((name+phone).encode()).hexdigest()[:14],
                "name": name, "phone": phone,
                "website": (data.get("url") or "").strip(),
                "address": (data.get("address", {}) or {}).get("addressLocality", area) + ", UAE",
                "rating": float((data.get("aggregateRating", {}) or {}).get("ratingValue", 0)),
                "reviews_count": int((data.get("aggregateRating", {}) or {}).get("reviewCount", 0)),
                "source": "yellowpages_ae",
                "source_url": (data.get("url") or url),
                "emirate": area,
            })
        except Exception: pass
    if out: return out[:limit]
    # Pass 2: regex fallback when JSON-LD wasn't present
    cards = re.findall(
        r'<h[23][^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>(?:.{0,500}?)'
        r'(?:tel:|>)([+\d][\d\s()-]{6,18})',
        html, re.S | re.I,
    )
    for href, name, phone in cards[:limit]:
        out.append({
            "place_id": "yp_" + hashlib.sha1((name+phone).encode()).hexdigest()[:14],
            "name": name.strip(), "phone": phone.strip(),
            "website": "",
            "address": area + ", UAE",
            "rating": 0, "reviews_count": 0,
            "source": "yellowpages_ae",
            "source_url": href if href.startswith("http") else f"https://www.yellowpages.ae{href}",
            "emirate": area,
        })
    return out


# ---------------------------------------------------------------------------
# Source 4: Connect.ae directory (UAE businesses) — free
# ---------------------------------------------------------------------------
async def _connect_ae_search(query: str, area: str,
                             limit: int = 10) -> list[dict]:
    """Scrape connect.ae search. Connect is a UAE-focused business directory
    with reasonable HTML structure. Returns best-effort results."""
    out: list[dict] = []
    try:
        url = (f"https://www.connect.ae/search/{query.replace(' ','-')}"
               f"-{area.lower().replace(' ','-')}.html")
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ServiaScraper/1.0)"}) as client:
            r = await client.get(url)
            if r.status_code != 200: return []
            html = r.text
    except Exception:
        return []
    # Connect.ae lists businesses with class="biz-name" + phone in a sibling
    cards = re.findall(
        r'<a[^>]*class="biz-name[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        r'(?:.{0,500}?)(\+?971[\d\s-]{6,15})',
        html, re.S | re.I,
    )
    for href, name, phone in cards[:limit]:
        out.append({
            "place_id": "ca_" + hashlib.sha1((name+phone).encode()).hexdigest()[:14],
            "name": name.strip(), "phone": phone.strip(),
            "website": "",
            "address": area + ", UAE",
            "rating": 0, "reviews_count": 0,
            "source": "connect_ae",
            "source_url": href if href.startswith("http") else f"https://www.connect.ae{href}",
            "emirate": area,
        })
    return out


# ---------------------------------------------------------------------------
# Source 3: Reddit recommendations (r/dubai, r/UAE, r/abudhabi, r/sharjah)
# ---------------------------------------------------------------------------
async def _reddit_search(query: str, area: str, limit: int = 10) -> list[dict]:
    """Reddit's public JSON API. Searches r/<sub> with the natural query
    (no restrict_sr=1, no +recommend) so we get all relevant threads.
    Tolerates 429 rate limits with backoff. Polite User-Agent."""
    out: list[dict] = []
    UA = "web:servia-vendor-scraper:v1.0 (by /u/serviaae)"
    sub_for_area = {
        "Dubai": "dubai", "Abu Dhabi": "abudhabi", "Sharjah": "sharjah",
        "Ajman": "dubai", "Ras Al Khaimah": "dubai",
        "Umm Al Quwain": "dubai", "Fujairah": "dubai",
    }
    primary_sub = sub_for_area.get(area, "dubai")
    subs = [primary_sub] if primary_sub == "UAE" else [primary_sub, "UAE"]

    async def _fetch_json(url: str):
        for _ in range(2):
            try:
                async with httpx.AsyncClient(timeout=12.0,
                        headers={"User-Agent": UA}) as client:
                    r = await client.get(url)
                    if r.status_code == 429:
                        await asyncio.sleep(2); continue
                    if r.status_code != 200: return None
                    return r.json()
            except Exception: return None
        return None

    for sub in subs:
        if len(out) >= limit: break
        search_url = (f"https://www.reddit.com/r/{sub}/search.json"
                      f"?q={query.replace(' ','+')}&sort=relevance&t=year&limit=15")
        data = await _fetch_json(search_url)
        if not data: continue
        posts = (data.get("data") or {}).get("children") or []
        for post in posts[:5]:
            if len(out) >= limit: break
            pd = post.get("data") or {}
            thread_url = "https://www.reddit.com" + (pd.get("permalink") or "")
            body_text = (pd.get("selftext") or "") + " " + (pd.get("title") or "")
            # Pull comments to mine for phone numbers people drop in replies
            cdata = await _fetch_json(thread_url + ".json?limit=20&depth=1")
            if cdata and isinstance(cdata, list) and len(cdata) >= 2:
                comments = (cdata[1].get("data") or {}).get("children") or []
                for c in comments[:15]:
                    body_text += " ||| " + ((c.get("data") or {}).get("body") or "")
            # Extract UAE phone numbers (+9715X XXXXXXX) and nearby names
            phones = re.findall(r"\+?9715[0-9](?:[\s-]?\d){7}", body_text)
            for ph in set(phones):
                ph_clean = re.sub(r"[\s-]", "", ph)
                if not ph_clean.startswith("+"): ph_clean = "+" + ph_clean
                idx = body_text.find(ph)
                window = body_text[max(0, idx-120):idx]
                name_match = re.findall(r"\b([A-Z][\w&'.-]{2,}(?:\s+[A-Z][\w&'.-]{2,}){0,4})\b", window)
                name = name_match[-1] if name_match else "Reddit-recommended vendor"
                out.append({
                    "place_id": "rd_" + hashlib.sha1((name+ph_clean).encode()).hexdigest()[:14],
                    "name": name[:80].strip(),
                    "phone": ph_clean, "website": "",
                    "address": area + ", UAE (Reddit-recommended)",
                    "rating": 0, "reviews_count": 1,
                    "source": "reddit_recommendation",
                    "source_url": thread_url, "emirate": area,
                })
                if len(out) >= limit: break
    return out


# ---------------------------------------------------------------------------
# Source 5: Bing Search (no API needed, returns business results in HTML)
# ---------------------------------------------------------------------------
async def _bing_search(query: str, area: str, limit: int = 10) -> list[dict]:
    """Generic web fallback — scrape Bing's search-result page for
    'best <query> in <area> UAE'. Bing surfaces business listings + phone
    numbers right in SERP. Free, no API key, but parsing is fragile."""
    out: list[dict] = []
    full_q = f"best {query} in {area} UAE phone"
    url = f"https://www.bing.com/search?q={full_q.replace(' ','+')}&cc=AE"
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True,
                headers={"User-Agent":
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605.1.15 "
                    "(KHTML, like Gecko) Version/16.0 Safari/605.1.15",
                    "Accept-Language": "en-AE,en;q=0.9"}) as client:
            r = await client.get(url)
            if r.status_code != 200: return []
            html = r.text
    except Exception: return []
    # Extract result blocks: <h2><a href=...>Name</a></h2> followed by snippet
    # containing UAE phone numbers
    blocks = re.findall(
        r'<h2><a[^>]*href="(https?://[^"]+)"[^>]*>([^<]+)</a></h2>'
        r'(.{0,800}?)</li>', html, re.S | re.I)
    for href, name, snippet in blocks[:limit*2]:
        # Skip aggregator/listing sites — we want vendor sites themselves
        if any(d in href for d in ("yellowpages.ae", "connect.ae", "facebook.com",
                                    "linkedin.com", "tripadvisor", "instagram.com",
                                    "youtube.com", "twitter.com", "wikipedia",
                                    "yelp.com", "reddit.com")):
            continue
        # Find a UAE phone in the snippet
        m = re.search(r"\+?9715[0-9](?:[\s-]?\d){7}", snippet)
        if not m: continue
        phone = re.sub(r"[\s-]", "", m.group(0))
        if not phone.startswith("+"): phone = "+" + phone
        clean_name = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", name)).strip()[:80]
        out.append({
            "place_id": "bg_" + hashlib.sha1((clean_name+phone).encode()).hexdigest()[:14],
            "name": clean_name, "phone": phone,
            "website": href, "address": area + ", UAE",
            "rating": 0, "reviews_count": 0,
            "source": "bing_search", "source_url": href, "emirate": area,
        })
        if len(out) >= limit: return out
    return out


# ---------------------------------------------------------------------------
# Source 7: APIFY GOOGLE MAPS SCRAPER — the production-grade option.
#
# Apify hosts pre-built scrapers ('actors') that handle every anti-bot
# system (Cloudflare, captchas, IP rotation, browser fingerprinting). Their
# 'compass~google-maps-scraper' actor returns structured Google Maps data:
# name, phone, website, address, rating, reviews_count, hours, photos.
#
# Pricing: ~$0.0035 per result. Free trial: $5 credit = ~1400 results.
# Get a token at https://console.apify.com/account/integrations
# Admin pastes the token in cfg key 'apify_api_token'.
# ---------------------------------------------------------------------------
async def _apify_google_maps(query: str, area: str, limit: int = 10) -> list[dict]:
    token = (db.cfg_get("apify_api_token", "") or "").strip()
    if not token:
        return [{"_error": "Apify token not set — paste yours from console.apify.com/account/integrations into admin → Vendors → 🌐 Scrape live vendors → Apify token"}]
    # run-sync-get-dataset-items returns the result inline. Long actors timeout
    # at 5 min by default; 'compass~google-maps-scraper' usually finishes <1 min
    # for a 10-result query.
    try:
        async with httpx.AsyncClient(timeout=180.0) as c:
            r = await c.post(
                f"https://api.apify.com/v2/acts/compass~google-maps-scraper/"
                f"run-sync-get-dataset-items?token={token}",
                json={
                    "searchStringsArray": [f"{query} {area} UAE"],
                    "locationQuery": f"{area}, United Arab Emirates",
                    "maxCrawledPlacesPerSearch": limit,
                    "language": "en",
                    "scrapePlaceDetailPage": True,
                    "skipClosedPlaces": True,
                },
            )
            if r.status_code != 200:
                return [{"_error": f"Apify HTTP {r.status_code}: {r.text[:200]}"}]
            data = r.json()
    except Exception as e:
        return [{"_error": f"Apify exception: {e}"}]
    if not isinstance(data, list):
        return [{"_error": f"Apify returned non-list: {str(data)[:150]}"}]
    out: list[dict] = []
    for it in data[:limit]:
        if not isinstance(it, dict): continue
        name = (it.get("title") or it.get("name") or "").strip()
        phone = (it.get("phone") or it.get("phoneNumber") or "").strip()
        if not (name and phone): continue
        out.append({
            "place_id": "ap_" + hashlib.sha1((name+phone).encode()).hexdigest()[:14],
            "name": name[:100], "phone": phone[:24],
            "website": (it.get("website") or "").strip()[:200],
            "address": (it.get("address") or area).strip()[:240],
            "rating": float(it.get("totalScore") or it.get("rating") or 0),
            "reviews_count": int(it.get("reviewsCount") or it.get("userRatingCount") or 0),
            "source": "apify_google_maps",
            "source_url": (it.get("url") or "").strip(),
            "emirate": area,
        })
    return out


# ---------------------------------------------------------------------------
# Source 6: GEMINI GROUNDED SEARCH — the only thing that actually works.
#
# Reality check (May 2026): every direct HTML source we tried returns 403:
#   - Yellow Pages UAE  → Cloudflare 403
#   - Bing search       → bot protection 403
#   - DuckDuckGo HTML   → 403
#   - Connect.ae        → blocked / DNS issues
#   - Reddit (no OAuth) → empty body
#
# The reliable way in 2026 is AI-powered web search. Gemini's
# `google_search` tool grounds the model in fresh web results and we ask it
# to return structured vendor data as JSON. Same Google API key as text gen.
# ---------------------------------------------------------------------------
async def _gemini_search(query: str, area: str, limit: int = 10) -> list[dict]:
    """Use Gemini grounded search to find real UAE vendors. Tries multiple
    model + tool combos because Google keeps changing the grounding API:

      gemini-2.0-flash-exp  with tool {"google_search": {}}     (newest)
      gemini-1.5-pro        with tool {"google_search_retrieval": {}}  (older)
      gemini-1.5-flash      same                                (cheapest)

    First combo that returns a 200 with parseable JSON wins.
    Same Google API key the user pasted in AI Arena — no extra setup.
    Bypasses every direct-scrape block because search runs on Google infra."""
    from . import ai_router
    cfg = ai_router._load_cfg()
    keys = cfg.get("keys") or {}
    key = (keys.get("google_image") or keys.get("google") or "").strip()
    if not key:
        return [{"_error": "Gemini search needs a Google AI key — paste it in admin → 🤖 AI Arena under 'Google AI'"}]
    prompt = (
        f"Find real, currently-operating UAE businesses that offer '{query}' "
        f"in {area}, UAE. Use Google Search to find them. Prefer SMALL active "
        f"vendors (under 200 reviews — we need hungry vendors who quote "
        f"competitively, not big established brands).\n\n"
        f"Return EXACTLY a JSON array of up to {limit} vendors. NO commentary, "
        "NO markdown fences, JUST the JSON array. Each vendor object has:\n"
        '  {"name": "...", "phone": "+9715XXXXXXXX", "website": "https://...", '
        '"address": "...", "rating": 4.5, "reviews_count": 75, "summary": "1-line"}\n\n'
        "Rules:\n"
        "- Phone MUST be valid UAE mobile (starts with +9715)\n"
        "- Skip if no phone or only landline\n"
        "- Skip enterprise brands with 500+ reviews\n"
        "- Skip directory aggregators — only direct vendor businesses\n"
        "- Output ONLY the JSON array."
    )
    # Combos to try, newest API first
    combos = [
        ("gemini-2.0-flash-exp",   {"google_search": {}}),
        ("gemini-2.0-flash",       {"google_search": {}}),
        ("gemini-1.5-pro-latest",  {"google_search_retrieval": {}}),
        ("gemini-1.5-flash-latest",{"google_search_retrieval": {}}),
    ]
    text = ""
    last_err = None
    for model, tool in combos:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={key}")
        try:
            async with httpx.AsyncClient(timeout=45.0) as c:
                r = await c.post(url, json={
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "tools": [tool],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4000},
                })
                if r.status_code == 200:
                    data = r.json()
                    for cand in data.get("candidates", []):
                        for part in (cand.get("content", {}) or {}).get("parts", []):
                            text += part.get("text") or ""
                    if text.strip(): break
                last_err = f"{model} HTTP {r.status_code}: {r.text[:150]}"
        except Exception as e:
            last_err = f"{model} exception: {e}"
            continue
    if not text.strip():
        return [{"_error": f"All Gemini grounding combos failed. Last: {last_err}"}]
    # Extract JSON array — model sometimes wraps in fences or prose
    if "```" in text:
        m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.S)
        if m: text = m.group(1)
    if "[" in text and "]" in text:
        text = text[text.index("["): text.rindex("]") + 1]
    try:
        items = json.loads(text)
        if not isinstance(items, list): return []
    except Exception as e:
        return [{"_error": f"Gemini search returned unparseable JSON: {str(e)[:100]} · raw: {text[:200]}"}]
    out: list[dict] = []
    for it in items[:limit]:
        if not isinstance(it, dict): continue
        name = (it.get("name") or "").strip()
        phone = (it.get("phone") or "").strip()
        if not (name and phone): continue
        out.append({
            "place_id": "gem_" + hashlib.sha1((name+phone).encode()).hexdigest()[:14],
            "name": name[:100], "phone": phone[:24],
            "website": (it.get("website") or "").strip()[:200],
            "address": (it.get("address") or area).strip()[:240],
            "rating": float(it.get("rating") or 0),
            "reviews_count": int(it.get("reviews_count") or 0),
            "source": "gemini_search",
            "source_url": "https://www.google.com/search?q=" + (name + " " + area).replace(" ", "+"),
            "emirate": area, "summary": (it.get("summary") or "")[:200],
        })
    return out


# ---------------------------------------------------------------------------
# Per-source health check — admin can verify which sources actually respond
# from production (not sandbox). Returns one row per source with status code.
# ---------------------------------------------------------------------------
async def _probe_source(name: str, fn) -> dict:
    """Run a single tiny test query against one source, return what happened."""
    try:
        results = await fn("cleaning service", "Dubai", limit=2)
        errors = [r for r in results if isinstance(r, dict) and "_error" in r]
        ok_results = [r for r in results if isinstance(r, dict) and "_error" not in r]
        return {
            "source": name,
            "ok": len(ok_results) > 0,
            "found": len(ok_results),
            "error": errors[0]["_error"] if errors else None,
        }
    except Exception as e:
        return {"source": name, "ok": False, "found": 0, "error": str(e)[:200]}


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
            # Per-source toggles persisted in db.cfg — admin can disable
            # individual sources from the UI if one is rate-limited or
            # serving junk that day.
            enabled = db.cfg_get("scraper_sources_enabled", None)
            if enabled is None:
                # Default: only sources that actually work without paid proxy.
                # Direct HTML scrapers (YP / Connect / Bing) are 403'd by
                # Cloudflare from datacenter IPs — disabled by default.
                enabled = {"google_places": True, "gemini_search": True,
                           "reddit": True, "yellowpages_ae": False,
                           "connect_ae": False, "bing": False}
            # Apify Google Maps — production-grade if admin set the token
            if enabled.get("apify", True) and (db.cfg_get("apify_api_token", "") or "").strip():
                sources.append(("apify_google_maps", _apify_google_maps(query, area, limit=target_per_area*2)))
            # Gemini grounded search — free + reliable when key is set
            if enabled.get("gemini_search", True):
                sources.append(("gemini_search", _gemini_search(query, area, limit=target_per_area*2)))
            if google_key and enabled.get("google_places", True):
                sources.append(("google_places", _google_places_search(query, area, google_key, limit=target_per_area*2)))
            if enabled.get("yellowpages_ae", False):
                sources.append(("yellowpages_ae", _yellowpages_search(query, area, limit=target_per_area*2)))
            if enabled.get("connect_ae", False):
                sources.append(("connect_ae", _connect_ae_search(query, area, limit=target_per_area*2)))
            if enabled.get("reddit", True):
                sources.append(("reddit", _reddit_search(query, area, limit=target_per_area*2)))
            if enabled.get("bing", False):
                sources.append(("bing", _bing_search(query, area, limit=target_per_area*2)))
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
    """Delete every vendor flagged as synthetic / seed / non-scraped.
    Real scraped vendors (validated_at IS NOT NULL) are untouched.
    Surfaces the actual SQL error if anything fails so admin sees why
    instead of a generic 'Error' toast."""
    try:
        _ensure_columns()    # idempotent — adds columns if missing
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"migration failed: {e}")
    deleted = 0
    try:
        with db.connect() as c:
            # Defensive: figure out if the column exists at all (older DBs may
            # have the migration silently failed in another container).
            cols = [r["name"] for r in c.execute("PRAGMA table_info(vendors)").fetchall()]
            has_synth = "is_synthetic" in cols
            has_validated = "validated_at" in cols
            # Strategy: wipe every vendor that DOES NOT have validated_at set.
            # Any vendor imported by the scraper has validated_at populated;
            # everything else is the original seed (or admin-added test data).
            if has_validated:
                ids = [r["id"] for r in c.execute(
                    "SELECT id FROM vendors WHERE validated_at IS NULL OR validated_at = ''"
                ).fetchall()]
            elif has_synth:
                ids = [r["id"] for r in c.execute(
                    "SELECT id FROM vendors WHERE is_synthetic=1 OR is_synthetic IS NULL"
                ).fetchall()]
            else:
                # No migration columns at all — wipe everything (rare)
                ids = [r["id"] for r in c.execute(
                    "SELECT id FROM vendors").fetchall()]
            for vid in ids:
                try: c.execute("DELETE FROM vendor_services WHERE vendor_id=?", (vid,))
                except Exception: pass
                try: deleted += c.execute("DELETE FROM vendors WHERE id=?", (vid,)).rowcount
                except Exception: pass
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"wipe failed: {type(e).__name__}: {e}")
    db.log_event("scraper", "all", "wipe_synthetic", actor="admin",
                 details={"deleted": deleted})
    return {"ok": True, "deleted": deleted}


# ---------------------------------------------------------------------------
# Cfg get/set: Google Places API key
# ---------------------------------------------------------------------------
class GoogleKeyBody(BaseModel):
    api_key: str


@router.get("/apify-token")
def get_apify_token():
    """Return whether the Apify token is set + a preview (never the full key)."""
    t = (db.cfg_get("apify_api_token", "") or "").strip()
    return {"set": bool(t), "preview": (t[:6] + "…" + t[-4:]) if len(t) >= 12 else ""}


class ApifyTokenBody(BaseModel):
    api_token: str


@router.post("/apify-token")
def set_apify_token(body: ApifyTokenBody):
    db.cfg_set("apify_api_token", body.api_token.strip())
    return {"ok": True}


@router.get("/sources")
def get_sources():
    """Return the list of available scraper sources + their enabled state.
    Apify (paid, $0.0035/result, $5 free trial) is the production-grade
    option — handles every anti-bot system. Gemini grounded search is the
    free fallback. Direct HTML scrapers are off by default because
    Cloudflare 403s datacenter IPs."""
    enabled = db.cfg_get("scraper_sources_enabled", None) or {
        "apify": True, "google_places": True, "gemini_search": True,
        "reddit": True, "yellowpages_ae": False, "connect_ae": False, "bing": False}
    cfg_keys = {}
    try:
        from . import ai_router
        cfg_keys = (ai_router._load_cfg().get("keys") or {})
    except Exception: pass
    google_key = (db.cfg_get("google_places_api_key", "") or "").strip()
    apify_token = (db.cfg_get("apify_api_token", "") or "").strip()
    has_gemini_key = bool((cfg_keys.get("google_image") or cfg_keys.get("google") or "").strip())
    return {"sources": [
        {"key": "apify", "label": "🏆 Apify Google Maps (PRODUCTION)",
         "enabled": enabled.get("apify", True),
         "needs_key": True, "key_set": bool(apify_token),
         "note": "Best results. Handles every anti-bot system. ~$0.0035/result, $5 free trial = ~1400 vendors. Get token at console.apify.com/account/integrations."},
        {"key": "gemini_search", "label": "🌟 Gemini grounded search (FREE FALLBACK)",
         "enabled": enabled.get("gemini_search", True),
         "needs_key": True, "key_set": has_gemini_key,
         "note": "AI-powered web search via Google. Reuses your Gemini text key. Most reliable in 2026 — bypasses 403 bot blocks because search runs on Google's infra."},
        {"key": "google_places", "label": "Google Places API",
         "enabled": enabled.get("google_places", True),
         "needs_key": True, "key_set": bool(google_key),
         "note": "Best structured data. Free tier 10K calls/month. Separate key needed."},
        {"key": "reddit", "label": "Reddit (r/dubai, r/UAE)",
         "enabled": enabled.get("reddit", True),
         "needs_key": False,
         "note": "Real resident recommendations. May rate-limit datacenter IPs."},
        {"key": "yellowpages_ae", "label": "Yellow Pages UAE (off by default)",
         "enabled": enabled.get("yellowpages_ae", False),
         "needs_key": False,
         "note": "⚠ Cloudflare 403s datacenter IPs. Only enable if you have a ScrapingBee key."},
        {"key": "connect_ae", "label": "Connect.ae (off by default)",
         "enabled": enabled.get("connect_ae", False),
         "needs_key": False,
         "note": "⚠ Same 403 issue as YP. Off by default."},
        {"key": "bing", "label": "Bing Search (off by default)",
         "enabled": enabled.get("bing", False),
         "needs_key": False,
         "note": "⚠ Bing 403s datacenter IPs. Off by default."},
    ]}


@router.get("/health")
async def sources_health():
    """Probe every source with one tiny query and report which actually
    work from THIS server's IP. Helps admin understand why a scrape
    returned 0 results."""
    google_key = (db.cfg_get("google_places_api_key", "") or "").strip()
    probes = [
        ("gemini_search", lambda q, a, limit: _gemini_search(q, a, limit)),
        ("reddit",        lambda q, a, limit: _reddit_search(q, a, limit)),
        ("yellowpages_ae",lambda q, a, limit: _yellowpages_search(q, a, limit)),
        ("connect_ae",    lambda q, a, limit: _connect_ae_search(q, a, limit)),
        ("bing",          lambda q, a, limit: _bing_search(q, a, limit)),
    ]
    if google_key:
        probes.insert(1, ("google_places",
            lambda q, a, limit: _google_places_search(q, a, google_key, limit)))
    results = []
    for name, fn in probes:
        results.append(await _probe_source(name, fn))
    return {"sources": results}


class SourcesBody(BaseModel):
    enabled: dict[str, bool]


@router.post("/sources")
def set_sources(body: SourcesBody):
    db.cfg_set("scraper_sources_enabled", body.enabled)
    return {"ok": True, "enabled": body.enabled}


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
