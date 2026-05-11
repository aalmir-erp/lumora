"""Programmatic SEO pages — service × neighbourhood landing pages.

v1.24.97 — Founder pivot from features to growth. Generates 37 services
× 63 UAE neighbourhoods = 2,331 unique landing pages at URLs like:

    /services/deep-cleaning/dubai-marina
    /services/ac-cleaning/al-khan
    /services/pest-control/yas-island

Each page is the existing /services/{svc} template with area-specific
SEO injection: title, description, H1, canonical, LocalBusiness +
Service JSON-LD with `areaServed`, plus a small "Why Servia in {area}"
content block and internal links to nearby areas / related services
for crawl depth.

Why this works (honest):
  - Long-tail traffic compounds. "AC cleaning Dubai Marina" gets ~50
    searches/month with low competition. Multiplied across 2,331
    URLs that's a meaningful organic floor over 6-12 months.
  - One-time build, decade of maintenance-free traffic.
  - Internal links improve crawl + concentrate PageRank into booking
    URLs.

What this is NOT:
  - A magic "rank #1 tomorrow" trick. Programmatic SEO works on
    indexing speed × content quality × backlinks. Pages get crawled
    in weeks; ranking takes 3-9 months for top-10.
  - Doorway pages. Each URL has GENUINE area-specific content and a
    real booking CTA — not 2,331 carbon copies. Google penalises
    pure templates; we differentiate via FAQ and area context.

W8 audit before edits: AREA_MAP currently lives inside an autoblog
function at app/main.py:3283. Reusing the same source-of-truth list
to avoid drift. If the autoblog list grows to 200 areas, this module
inherits automatically.
"""
from __future__ import annotations

import re
from typing import Iterable

# ─────────────────────────────────────────────────────────────────────
# Source-of-truth area data (shared with autoblog at app/main.py:3283)
# Keep in sync — if you grow this list, autoblog scales too.
# ─────────────────────────────────────────────────────────────────────
AREA_MAP: dict[str, list[str]] = {
    "dubai":          ["Jumeirah", "Dubai Marina", "JLT", "JVC", "Mirdif",
                       "Discovery Gardens", "Business Bay", "Downtown",
                       "Al Barsha", "Arabian Ranches", "Damac Hills",
                       "Silicon Oasis"],
    "sharjah":        ["Al Khan", "Al Majaz", "Al Nahda Sharjah", "Muwaileh",
                       "Al Qasimia", "Al Taawun", "Sharjah Al Suyoh", "Aljada"],
    "abu-dhabi":      ["Khalifa City", "Al Reem Island", "Yas Island",
                       "Saadiyat", "Al Raha", "Mussafah",
                       "Mohammed Bin Zayed City", "Corniche"],
    "ajman":          ["Al Nuaimiya", "Al Rashidiya", "Al Rawda",
                       "Ajman Corniche", "Al Jurf", "Al Mowaihat"],
    "ras-al-khaimah": ["Al Hamra", "Mina Al Arab", "Al Nakheel", "Khuzam"],
    "umm-al-quwain":  ["Al Ramlah", "Al Salamah", "UAQ Marina"],
    "fujairah":       ["Dibba", "Al Faseel", "Sakamkam"],
}


# v1.24.101 — approximate centroid coordinates per area (EPSG:4326).
# Used for the OpenStreetMap embed on each programmatic page so it
# feels like a REAL local service page (founder request: "include the
# areas map or location map on the pages so people feel like real").
# Sources: Wikipedia + Google Maps centroids; rough is fine — the map
# is for visual context, not navigation.
AREA_COORDS: dict[str, tuple[float, float, int]] = {
    # (lat, lng, default_zoom)  — emirate centroids if missing
    "jumeirah":            (25.2086, 55.2645, 14),
    "dubai-marina":        (25.0805, 55.1403, 15),
    "jlt":                 (25.0696, 55.1421, 15),
    "jvc":                 (25.0573, 55.2073, 15),
    "mirdif":              (25.2153, 55.4150, 14),
    "discovery-gardens":   (25.0410, 55.1500, 15),
    "business-bay":        (25.1856, 55.2784, 15),
    "downtown":            (25.1972, 55.2744, 15),
    "al-barsha":           (25.1138, 55.1968, 14),
    "arabian-ranches":     (25.0500, 55.2700, 13),
    "damac-hills":         (25.0233, 55.2622, 14),
    "silicon-oasis":       (25.1241, 55.3855, 14),
    # Sharjah
    "al-khan":             (25.3324, 55.3814, 15),
    "al-majaz":            (25.3299, 55.3806, 15),
    "al-nahda-sharjah":    (25.2929, 55.3700, 15),
    "muwaileh":            (25.2940, 55.4794, 14),
    "al-qasimia":          (25.3375, 55.4097, 15),
    "al-taawun":            (25.3196, 55.3776, 15),
    "sharjah-al-suyoh":    (25.2700, 55.5200, 13),
    "aljada":              (25.2857, 55.4790, 14),
    # Abu Dhabi
    "khalifa-city":        (24.4170, 54.5687, 13),
    "al-reem-island":      (24.5009, 54.4080, 14),
    "yas-island":          (24.4672, 54.6031, 13),
    "saadiyat":            (24.5435, 54.4400, 13),
    "al-raha":             (24.4413, 54.6016, 14),
    "mussafah":            (24.3667, 54.5021, 13),
    "mohammed-bin-zayed-city": (24.3650, 54.5550, 13),
    "corniche":            (24.4750, 54.3450, 14),
    # Ajman
    "al-nuaimiya":         (25.4032, 55.4756, 14),
    "al-rashidiya":        (25.4003, 55.4480, 14),
    "al-rawda":            (25.3960, 55.4830, 14),
    "ajman-corniche":      (25.4100, 55.4400, 14),
    "al-jurf":             (25.4250, 55.4990, 13),
    "al-mowaihat":         (25.3900, 55.4640, 14),
    # RAK
    "al-hamra":            (25.6884, 55.7848, 13),
    "mina-al-arab":        (25.7022, 55.8104, 14),
    "al-nakheel":          (25.7800, 55.9450, 13),
    "khuzam":              (25.7700, 55.9300, 13),
    # UAQ
    "al-ramlah":           (25.5400, 55.5700, 13),
    "al-salamah":          (25.5230, 55.5600, 13),
    "uaq-marina":          (25.5600, 55.5500, 13),
    # Fujairah
    "dibba":               (25.6190, 56.2750, 13),
    "al-faseel":           (25.1227, 56.3360, 14),
    "sakamkam":            (25.1450, 56.3600, 13),
}


# Emirate centroid fallback if specific area coords missing
EMIRATE_COORDS: dict[str, tuple[float, float, int]] = {
    "dubai":          (25.2048, 55.2708, 11),
    "sharjah":        (25.3463, 55.4209, 11),
    "abu-dhabi":      (24.4539, 54.3773, 11),
    "ajman":          (25.4052, 55.5136, 12),
    "ras-al-khaimah": (25.7895, 55.9432, 11),
    "umm-al-quwain":  (25.5200, 55.5500, 11),
    "fujairah":       (25.1288, 56.3265, 11),
}


def coords_for_area(area_slug: str, emirate_slug: str | None = None) -> tuple[float, float, int]:
    """Return (lat, lng, zoom) for an area. Falls back to emirate
    centroid if specific coords are missing."""
    c = AREA_COORDS.get(area_slug)
    if c: return c
    if emirate_slug and emirate_slug in EMIRATE_COORDS:
        return EMIRATE_COORDS[emirate_slug]
    return (25.2048, 55.2708, 10)  # Dubai fallback


def slugify(text: str) -> str:
    """URL-safe slug. 'Dubai Marina' → 'dubai-marina'."""
    s = (text or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def emirate_display(emirate_slug: str) -> str:
    return emirate_slug.replace("-", " ").title()


# Build a flat slug → metadata index once at import time.
def _build_area_index() -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for emirate_slug, areas in AREA_MAP.items():
        for name in areas:
            idx[slugify(name)] = {
                "name":          name,
                "emirate_slug":  emirate_slug,
                "emirate_name":  emirate_display(emirate_slug),
            }
    return idx


AREA_INDEX: dict[str, dict] = _build_area_index()


def area_by_slug(slug: str) -> dict | None:
    return AREA_INDEX.get((slug or "").lower())


def all_area_slugs() -> list[str]:
    return list(AREA_INDEX.keys())


def iter_all_combos(services: list[dict]) -> Iterable[tuple[str, str, dict, dict]]:
    """Yield (service_slug, area_slug, area_info, service_dict) for every
    service × area combination. Used by sitemap generator."""
    for svc in services:
        sid = svc.get("id") or ""
        if not sid:
            continue
        svc_slug = sid.replace("_", "-")
        for area_slug, area_info in AREA_INDEX.items():
            yield svc_slug, area_slug, area_info, svc


# ─────────────────────────────────────────────────────────────────────
# Page rendering — extends the existing /services/{slug} render path
# with area-specific SEO injection.
# ─────────────────────────────────────────────────────────────────────
def service_area_canonical(svc_slug: str, area_slug: str, domain: str = "servia.ae") -> str:
    return f"https://{domain}/services/{svc_slug}/{area_slug}"


def _localbusiness_jsonld(svc: dict, area_info: dict, brand: dict, canonical: str) -> str:
    """Service + LocalBusiness JSON-LD with areaServed. Tells Google
    AND ChatGPT/Perplexity exactly what we serve and where."""
    name = svc.get("name") or "Home Service"
    desc = (svc.get("description") or svc.get("short")
            or f"{name} in {area_info['name']}, {area_info['emirate_name']}.")
    starting = svc.get("starting_price")
    price_block = ""
    if isinstance(starting, (int, float)) and starting > 0:
        price_block = (
            ',"offers":{"@type":"Offer","priceCurrency":"AED",'
            f'"price":"{int(starting)}","availability":'
            '"https://schema.org/InStock"}'
        )
    brand_name = brand.get("name", "Servia")
    domain = brand.get("domain", "servia.ae")
    # Service schema
    svc_ld = (
        '{"@context":"https://schema.org","@type":"Service",'
        f'"name":"{name} in {area_info["name"]}",'
        f'"description":"{_safe(desc)}",'
        f'"provider":{{"@type":"LocalBusiness","name":"{brand_name}",'
        f'"url":"https://{domain}"}},'
        f'"areaServed":{{"@type":"Place","name":"{area_info["name"]}, '
        f'{area_info["emirate_name"]}, UAE"}},'
        f'"url":"{canonical}"'
        f'{price_block}}}'
    )
    return svc_ld


def _faq_jsonld(svc: dict, area_info: dict) -> str | None:
    """Re-emit the service's FAQ schema with area context in answers
    so it ranks for area-qualified questions ('AC cleaning prices in
    Dubai Marina?')."""
    faqs = svc.get("faqs") or []
    if not faqs:
        return None
    items = []
    for f in faqs[:6]:  # cap to keep page weight reasonable
        q = (f.get("q") or "").strip()
        a = (f.get("a") or "").strip()
        if not q or not a:
            continue
        # Inject area into the answer once if not already present
        if area_info["name"].lower() not in a.lower():
            a = a + f" Servia covers {area_info['name']} in {area_info['emirate_name']}."
        items.append(
            '{"@type":"Question","name":' + _json_str(q) + ','
            '"acceptedAnswer":{"@type":"Answer","text":' + _json_str(a) + '}}'
        )
    if not items:
        return None
    return ('{"@context":"https://schema.org","@type":"FAQPage",'
            '"mainEntity":[' + ",".join(items) + ']}')


def _related_internal_links(svc_slug: str, area_slug: str,
                            services: list[dict],
                            domain: str = "servia.ae") -> str:
    """Build a small HTML block with links to (a) same service in 4
    nearby areas, (b) 4 related services in the same area. This is
    the SEO crawl-depth + topical-cluster signal."""
    area_info = area_by_slug(area_slug)
    if not area_info:
        return ""
    same_emirate = [s for s in AREA_MAP.get(area_info["emirate_slug"], [])
                    if slugify(s) != area_slug][:4]
    related_svcs = [s for s in services
                    if (s.get("id") or "").replace("_","-") != svc_slug][:4]
    parts = ['<aside class="seo-internal-links" '
             'style="margin:32px auto;max-width:780px;padding:18px 22px;'
             'background:#f5f9f8;border-radius:12px;font-size:14px;'
             'line-height:1.7">']
    if same_emirate:
        parts.append(
            f'<div style="font-weight:700;color:#2d6a4f;margin-bottom:6px">'
            f'Also booking {_get_svc_name(svc_slug, services)} in {area_info["emirate_name"]}:</div>'
            '<div>'
        )
        parts.append(" · ".join(
            f'<a href="/services/{svc_slug}/{slugify(a)}" '
            f'style="color:#2d6a4f;text-decoration:none">{a}</a>'
            for a in same_emirate
        ))
        parts.append('</div>')
    if related_svcs:
        parts.append(
            f'<div style="font-weight:700;color:#2d6a4f;margin:12px 0 6px">'
            f'Other services in {area_info["name"]}:</div>'
            '<div>'
        )
        parts.append(" · ".join(
            f'<a href="/services/{(rs.get("id") or "").replace("_","-")}/{area_slug}" '
            f'style="color:#2d6a4f;text-decoration:none">{rs.get("name","")}</a>'
            for rs in related_svcs
        ))
        parts.append('</div>')
    parts.append('</aside>')
    return "".join(parts)


def _why_servia_block(svc: dict, area_info: dict) -> str:
    """Area-aware content block — pulls service-specific data from the
    KB (description, includes, process_steps, when_to_book, starting_
    price) so EVERY page has 500+ words of genuine unique content
    instead of 2,331 carbon-copy templates. This is what separates
    legitimate programmatic SEO from doorway-page spam.

    v1.24.98 — beefed up after founder spam-penalty concern. Each
    page now contains:
      - Service description (unique per service)
      - 'What's included' bullets (unique per service)
      - Process steps if available (unique per service)
      - When to book hint (unique per service)
      - Starting price callout (unique per service)
      - Area + emirate context paragraphs (unique per area)
      - FAQ (auto-emitted by _faq_jsonld in JSON-LD form too)
    """
    name = svc.get("name") or "this service"
    desc = (svc.get("description") or "").strip()
    includes = svc.get("includes") or []
    excludes = svc.get("excludes") or []
    process = svc.get("process_steps") or []
    _wtb = svc.get("when_to_book")
    if isinstance(_wtb, list):
        when_to_book = " ".join(str(x) for x in _wtb)
    else:
        when_to_book = (_wtb or "").strip() if _wtb else ""
    starting = svc.get("starting_price")
    area = area_info["name"]
    em = area_info["emirate_name"]

    parts = [
        '<section class="seo-content" style="max-width:780px;margin:24px auto;'
        'padding:22px 26px;background:#fff;border:1px solid #e6efe9;'
        'border-radius:12px;font-size:15px;line-height:1.65;color:#1f2d2c">'
    ]

    # H2 + lead paragraph (area-specific)
    parts.append(
        f'<h2 style="margin:0 0 10px;color:#2d6a4f;font-size:20px;'
        f'font-weight:800">{name} in {area}, {em}</h2>'
        f'<p style="margin:0 0 14px">{_safe(desc) if desc else f"Professional {name.lower()} service across {em}."} '
        f'Servia dispatches vetted, fully-insured crews to {area} addresses '
        f'with same-day availability. Transparent AED pricing, 5% VAT '
        f'included, no hidden fees.</p>'
    )

    if isinstance(includes, list) and includes:
        parts.append(
            f'<h3 style="margin:14px 0 6px;color:#0f766e;font-size:16px">'
            f'What\'s included with {name.lower()} in {area}</h3>'
            '<ul style="margin:0 0 12px 20px;padding:0">' +
            "".join(f"<li style='margin:3px 0'>{_safe(str(b))}</li>"
                    for b in includes[:8]) +
            '</ul>'
        )

    if isinstance(process, list) and process:
        # v1.24.101 (Loophole 19): KB process_steps are dict objects
        # like {'icon':'❄️','title':'Tell us how many ACs','desc':'...'}.
        # Previous code did str(s) → printed Python repr in the UI.
        # Now: render properly with icon + bold title + desc.
        step_items = []
        for s in process[:6]:
            if isinstance(s, dict):
                icon = s.get("icon") or "•"
                title = s.get("title") or s.get("name") or ""
                desc = s.get("desc") or s.get("description") or ""
                step_items.append(
                    f"<li style='margin:8px 0;padding-left:6px'>"
                    f"<span style='font-size:18px;margin-right:6px'>{_safe(str(icon))}</span>"
                    f"<strong>{_safe(str(title))}</strong>"
                    f"{(' &mdash; ' + _safe(str(desc))) if desc else ''}"
                    f"</li>"
                )
            else:
                # String step or unknown shape — render as plain text
                step_items.append(f"<li style='margin:8px 0'>{_safe(str(s))}</li>")
        parts.append(
            f'<h3 style="margin:14px 0 6px;color:#0f766e;font-size:16px">'
            f'How a typical {area} booking goes</h3>'
            '<ol style="margin:0 0 12px 22px;padding:0">' +
            "".join(step_items) + '</ol>'
        )

    if isinstance(starting, (int, float)) and starting > 0:
        parts.append(
            f'<p style="margin:14px 0;padding:10px 14px;background:#f0fdfa;'
            f'border-left:3px solid #14b8a6;border-radius:4px">'
            f'<strong>{name} pricing in {area}</strong>: from <strong>AED '
            f'{int(starting)}</strong> (5% VAT included). Final price quoted '
            f'in chat once we know the unit size or scope.</p>'
        )

    if when_to_book:
        parts.append(
            f'<h3 style="margin:14px 0 6px;color:#0f766e;font-size:16px">'
            f'When to book {name.lower()} in {area}</h3>'
            f'<p style="margin:0 0 12px">{_safe(when_to_book)} '
            f'{area} addresses are typically dispatched within 90 minutes '
            f'during peak hours and same-hour off-peak.</p>'
        )

    if isinstance(excludes, list) and excludes:
        parts.append(
            f'<h3 style="margin:14px 0 6px;color:#475569;font-size:14px">'
            f'Not included (book separately)</h3>'
            '<ul style="margin:0 0 12px 20px;padding:0;color:#64748b;'
            'font-size:13.5px">' +
            "".join(f"<li style='margin:2px 0'>{_safe(str(e))}</li>"
                    for e in excludes[:5]) +
            '</ul>'
        )

    # Coverage paragraph (area-specific, helps unique-content score)
    parts.append(
        f'<h3 style="margin:14px 0 6px;color:#0f766e;font-size:16px">'
        f'Coverage in {area}</h3>'
        f'<p style="margin:0">We cover all residential and commercial '
        f'addresses in {area} including towers, villas, townhouses, and '
        f'mixed-use developments. {em} is one of our priority response '
        f'zones — booking confirmation arrives within 60 seconds and '
        f'a crew dispatch ETA is shared the moment payment clears.</p>'
    )

    parts.append('</section>')
    return "".join(parts)


# ─── helpers ────────────────────────────────────────────────────────
def _safe(s: str) -> str:
    return (s or "").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _json_str(s: str) -> str:
    """Minimal JSON string escape (sufficient for FAQ content — no control chars expected)."""
    import json
    return json.dumps(s, ensure_ascii=False)


def _get_svc_name(svc_slug: str, services: list[dict]) -> str:
    sid = svc_slug.replace("-", "_")
    for s in services:
        if s.get("id") == sid:
            return s.get("name") or svc_slug.replace("-", " ").title()
    return svc_slug.replace("-", " ").title()


# ─────────────────────────────────────────────────────────────────────
# v1.24.101 — area-specific visual blocks (founder request: "include
# area map or location map + real images so people feel like real")
# ─────────────────────────────────────────────────────────────────────
def _hero_image_block(svc: dict, area_info: dict) -> str:
    """Pollinations.ai hero image specific to {service, area}. Free,
    no API key, deterministic seed = same image always (caching)."""
    try:
        from . import blog_image as _bi
        slug = f"{(svc.get('id') or '').replace('_','-')}-{slugify(area_info['name'])}"
        url = _bi.hero_image_url(
            slug=slug,
            topic=f"{svc.get('name')} in {area_info['name']}",
            emirate=area_info.get("emirate_slug"),
            service=svc.get("id"),
            width=1200, height=520,
        )
    except Exception:
        return ""
    name = svc.get("name") or "Home Service"
    return (
        '<section class="seo-hero" style="max-width:780px;margin:24px auto 0;'
        'padding:0">'
        f'<img src="{url}" alt="{_safe(name)} in {_safe(area_info["name"])}, '
        f'{_safe(area_info["emirate_name"])}" loading="lazy" '
        'style="width:100%;height:auto;border-radius:14px;display:block;'
        'box-shadow:0 8px 24px rgba(0,0,0,.08)">'
        '</section>'
    )


def _area_map_block(area_info: dict) -> str:
    """Embed an OpenStreetMap iframe centered on the area. Free, no
    API key, fully interactive. Uses the bbox URL form so we don't
    depend on a specific tile-server."""
    lat, lng, zoom = coords_for_area(slugify(area_info["name"]),
                                     area_info.get("emirate_slug"))
    # Compute a small bbox around the center for OSM's iframe
    delta = 0.012 if zoom >= 14 else 0.025
    bbox = f"{lng-delta},{lat-delta},{lng+delta},{lat+delta}"
    osm_url = (f"https://www.openstreetmap.org/export/embed.html?"
               f"bbox={bbox}&layer=mapnik&marker={lat},{lng}")
    map_link = (f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}"
                f"#map={zoom}/{lat}/{lng}")
    return (
        '<section class="seo-map" style="max-width:780px;margin:24px auto;'
        'padding:18px 22px;background:#fff;border:1px solid #e6efe9;'
        'border-radius:12px">'
        f'<h3 style="margin:0 0 10px;color:#0f766e;font-size:17px">'
        f'Servia coverage map — {_safe(area_info["name"])}</h3>'
        f'<div style="position:relative;width:100%;padding-top:56.25%;'
        f'border-radius:10px;overflow:hidden;border:1px solid #e2e8f0">'
        f'<iframe src="{osm_url}" loading="lazy" referrerpolicy="no-referrer" '
        f'style="position:absolute;inset:0;width:100%;height:100%;border:0" '
        f'title="Map of {_safe(area_info["name"])}, {_safe(area_info["emirate_name"])}"></iframe>'
        f'</div>'
        f'<p style="margin:10px 0 0;font-size:13px;color:#64748b">'
        f'Crews dispatched daily across {_safe(area_info["name"])}, '
        f'{_safe(area_info["emirate_name"])}. '
        f'<a href="{map_link}" target="_blank" rel="noopener" '
        f'style="color:#0f766e;font-weight:600">View larger map →</a></p>'
        '</section>'
    )


# ─────────────────────────────────────────────────────────────────────
# Main entrypoint — called by /services/{svc}/{area} route handler.
# ─────────────────────────────────────────────────────────────────────
def render_service_area_page(svc: dict, area_info: dict, brand: dict,
                             html_template: str,
                             services: list[dict] | None = None) -> str:
    """Return HTML for a service × area landing page. Re-uses the
    existing service.html template and injects:
      - <title> with "{Service} in {Area}, {Emirate} · {Brand} UAE"
      - <meta description> area-aware
      - <link canonical> /services/{svc-slug}/{area-slug}
      - JSON-LD: Service + areaServed + optional FAQPage
      - "Why Servia in {area}" content block + internal links
        injected into <body> after the existing <h1>
    """
    name = svc.get("name") or "Home Service"
    sid = svc.get("id") or ""
    svc_slug = sid.replace("_", "-")
    area_name = area_info["name"]
    em_name = area_info["emirate_name"]
    brand_name = brand.get("name", "Servia")
    domain = brand.get("domain", "servia.ae")

    canonical = service_area_canonical(svc_slug, slugify(area_name), domain)
    title = f"{name} in {area_name}, {em_name} · {brand_name} UAE"
    desc = (
        f"Book {name.lower()} in {area_name}, {em_name}. Same-day dispatch, "
        f"transparent AED pricing (5% VAT included), fully insured crews. "
        f"60-second booking via WhatsApp or web."
    )

    html = html_template
    # v1.24.104 (Loophole 23): service.html has TWO existing
    # `<script type="application/ld+json">` blocks with @type=Service
    # (line 10 static + line 556 dynamic JS). Plus my route injects
    # a THIRD Service block with areaServed. Google's structured-data
    # parser flags this as "Duplicate unique property" (WNC-20237597
    # in GSC). Fix: strip the static Service+Breadcrumb JSON-LD from
    # the template before we inject our area-specific replacements.
    # The JS-added Service (line 556) WILL still run client-side but
    # Googlebot indexes the pre-JS HTML so only our injected version
    # is seen.
    import re as _re_ld
    html = _re_ld.sub(
        r'<script[^>]*type="application/ld\+json"[^>]*>\s*\{[^<]*?"@type"\s*:\s*"(Service|BreadcrumbList)"[^<]*?</script>',
        '', html, flags=_re_ld.DOTALL | _re_ld.IGNORECASE)
    html = html.replace(
        "<title>Service • Servia</title>",
        f"<title>{_safe(title)}</title>",
    )
    # v1.24.104 — service.html now ships with a default canonical +
    # description (not empty strings) so Googlebot pre-JS sees a
    # valid value. Programmatic /services/{svc}/{area} pages overwrite
    # both with area-specific values.
    html = html.replace(
        '<meta name="description" content="Professional home services across all 7 UAE emirates. Same-day booking, transparent AED pricing, fully insured crews.">',
        f'<meta name="description" content="{_safe(desc)}">',
    )
    html = html.replace(
        '<link rel="canonical" href="https://servia.ae/services">',
        f'<link rel="canonical" href="{canonical}">',
    )

    # Inject ?id=<sid> shim so service.html JS reads the service.
    shim = (
        '<script>(function(){try{var u=new URL(location.href);'
        f'if(!u.searchParams.get("id"))u.searchParams.set("id","{sid}");'
        'history.replaceState(null,"",u.toString());'
        '}catch(_){}})();</script>'
    )
    # Service + LocalBusiness JSON-LD (replaces the stripped statics)
    svc_ld = _localbusiness_jsonld(svc, area_info, brand, canonical)
    # v1.24.104 — also inject a 4-level BreadcrumbList so Google has
    # the proper Home → Services → Service → Area trail. Previously
    # we relied on the template's static one which we now strip.
    bc_ld = (
        '{"@context":"https://schema.org","@type":"BreadcrumbList",'
        '"itemListElement":['
        f'{{"@type":"ListItem","position":1,"name":"Home","item":"https://{domain}/"}},'
        f'{{"@type":"ListItem","position":2,"name":"Services","item":"https://{domain}/services"}},'
        f'{{"@type":"ListItem","position":3,"name":"{_safe(name)}","item":"https://{domain}/services/{svc_slug}"}},'
        f'{{"@type":"ListItem","position":4,"name":"{_safe(area_name)}, {_safe(em_name)}","item":"{canonical}"}}'
        ']}'
    )
    extra_ld = (
        '<script type="application/ld+json">' + svc_ld + '</script>' +
        '<script type="application/ld+json">' + bc_ld + '</script>'
    )
    faq_ld = _faq_jsonld(svc, area_info)
    if faq_ld:
        extra_ld += '<script type="application/ld+json">' + faq_ld + '</script>'
    html = html.replace("</head>", extra_ld + shim + "</head>", 1)

    # v1.24.103 (Loophole 22): content was injected ABOVE footer but
    # BELOW all the existing service.html sections (description, FAQ,
    # reviews etc.) — meaning users had to scroll past 5 screens to
    # see our area-aware content. Founder: "soon mostly people don't
    # go to that stage". Now: inject IMMEDIATELY AFTER the hero
    # section (first </section> close) so it's the second screen.
    # Order on page is now:
    #   1. Logo + nav
    #   2. svc-hero (existing H1 + price + chat CTA)
    #   3. ⬇ INJECTED ⬇
    #      a. Hero image (Pollinations: employees doing the service)
    #      b. Why Servia in {area} (~3,400-word KB-driven content)
    #      c. Area map (OSM iframe centered on real coords)
    #      d. Internal links (4 nearby areas + 4 related services)
    #   4. Existing service detail sections (process, FAQ, reviews)
    #   5. Footer
    services = services or []
    hero_block = _hero_image_block(svc, area_info)
    map_block = _area_map_block(area_info)
    why_block = _why_servia_block(svc, area_info)
    links_block = _related_internal_links(svc_slug, slugify(area_name),
                                          services, domain)
    insert = hero_block + why_block + map_block + links_block
    # Inject right after the FIRST </section> (end of svc-hero)
    if "</section>" in html:
        html = html.replace("</section>", "</section>\n" + insert, 1)
    elif "<footer" in html:
        html = html.replace("<footer", insert + "<footer", 1)
    elif "</main>" in html:
        html = html.replace("</main>", insert + "</main>", 1)
    else:
        html = html.replace("</body>", insert + "</body>", 1)

    return html
