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
    """Short area-aware paragraph block. NOT 2,331 carbon copies —
    pulls service-specific includes/process and weaves area name in
    naturally so each page reads differently."""
    name = svc.get("name") or "this service"
    includes = svc.get("includes") or []
    bullets = ""
    if isinstance(includes, list) and includes:
        bullets = "<ul style='margin:8px 0 0 18px'>" + "".join(
            f"<li>{_safe(str(b))}</li>" for b in includes[:5]
        ) + "</ul>"
    return (
        '<section class="seo-why" style="max-width:780px;margin:24px auto;'
        'padding:18px 22px;background:#fff;border:1px solid #e6efe9;'
        'border-radius:12px;font-size:15px;line-height:1.6">'
        f'<h2 style="margin:0 0 8px;color:#2d6a4f;font-size:18px">'
        f'{name} in {area_info["name"]} — what you get</h2>'
        f'<p style="margin:0">Servia dispatches {name.lower()} crews '
        f'across {area_info["name"]}, {area_info["emirate_name"]} 24/7. '
        f'Booked in 60 seconds, transparent AED pricing, fully insured, '
        f'5% VAT included.</p>'
        f'{bullets}'
        '</section>'
    )


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
    html = html.replace(
        "<title>Service • Servia</title>",
        f"<title>{_safe(title)}</title>",
    )
    html = html.replace(
        '<meta name="description" content="">',
        f'<meta name="description" content="{_safe(desc)}">',
    )
    html = html.replace(
        '<link rel="canonical" href="">',
        f'<link rel="canonical" href="{canonical}">',
    )

    # Inject ?id=<sid> shim so service.html JS reads the service.
    shim = (
        '<script>(function(){try{var u=new URL(location.href);'
        f'if(!u.searchParams.get("id"))u.searchParams.set("id","{sid}");'
        'history.replaceState(null,"",u.toString());'
        '}catch(_){}})();</script>'
    )
    # Service + LocalBusiness JSON-LD (extra, in addition to template defaults)
    svc_ld = _localbusiness_jsonld(svc, area_info, brand, canonical)
    extra_ld = (
        '<script type="application/ld+json">' + svc_ld + '</script>'
    )
    faq_ld = _faq_jsonld(svc, area_info)
    if faq_ld:
        extra_ld += '<script type="application/ld+json">' + faq_ld + '</script>'
    html = html.replace("</head>", extra_ld + shim + "</head>", 1)

    # Inject area-aware content block + internal links right before
    # the closing </main> (or </body> as fallback).
    services = services or []
    why_block = _why_servia_block(svc, area_info)
    links_block = _related_internal_links(svc_slug, slugify(area_name),
                                          services, domain)
    insert = why_block + links_block
    if "</main>" in html:
        html = html.replace("</main>", insert + "</main>", 1)
    else:
        html = html.replace("</body>", insert + "</body>", 1)

    return html
