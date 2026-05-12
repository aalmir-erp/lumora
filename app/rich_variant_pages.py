"""v1.24.133 — Rich indexed landing pages for the highest-CPC service variants.

WHAT THIS IS
------------
Of the 17,324 PPC landing pages registered by main._register_lp_routes,
the vast majority are NOINDEX templated pages — they exist purely for
Google Ads ad-group destinations. They have ~zero unique content.

For 5 specific high-CPC variants (the ones whose CPC × volume justifies
~600-800 words of unique editorial content) we render an INDEXED rich
page instead. Content data lives in seed_variant_pages.VARIANT_PAGES.

This module exposes one function — render_rich_variant(variant) — that
builds the full HTML by injecting rich content into web/service.html.

SEO BEHAVIOUR
-------------
- robots: "index,follow" (vs. noindex on the thin LPs)
- canonical: self (the rich URL is the indexed authority)
- All sister LPs of the same variant alias (e.g. /bed-bug-treatment-jumeirah,
  /bed-bug-treatment-marina) keep their noindex AND have their canonical
  switched to point at THIS rich URL — so link equity from the 50+ thin LPs
  concentrates on the rich page instead of being lost.

JSON-LD SCHEMA EMITTED
----------------------
- BreadcrumbList (Home → parent service → this variant)
- FAQPage (built from the 8 Q&As in the variant data)
- Service (with priceRange, areaServed, brand, image)

This module is intentionally small — the value is in the editorial content
of seed_variant_pages.py, not in clever rendering.
"""
from __future__ import annotations

import html as _html
import json
import urllib.parse

from fastapi.responses import HTMLResponse

from .config import get_settings
from .data.seed_variant_pages import VARIANT_PAGES, VARIANT_BY_SLUG, RICH_ALIAS_TO_SLUG

_settings = get_settings()


# Pollinations.ai endpoint — same as app.blog_image. Inlined here to avoid
# a circular import (blog_image imports settings, settings imports nothing
# from this file, but main imports both — keeping this self-contained).
_POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"


def _hero_image_url(slug: str, prompt: str, width: int = 1200, height: int = 630) -> str:
    """Build a Pollinations image URL with a deterministic seed from the slug."""
    seed = abs(hash(slug)) % 10_000_000
    encoded = urllib.parse.quote(prompt, safe="")
    return f"{_POLLINATIONS_BASE}{encoded}?width={width}&height={height}&nologo=true&seed={seed}"


def _build_rich_content_html(variant: dict, brand_name: str) -> str:
    """Build the HTML block that gets injected into service.html.

    Layout:
      [stats bar]
      [why-us bullets]
      [editorial body — variant['body_html']]
      [FAQ accordion]
    """
    # Stats bar — 4 quick-fact tiles
    stats_html = '<div class="rv-stats" role="list">'
    for label, value in variant["stats"]:
        stats_html += (
            '<div class="rv-stat" role="listitem">'
            f'<div class="rv-stat-val">{_html.escape(value)}</div>'
            f'<div class="rv-stat-label">{_html.escape(label)}</div>'
            '</div>'
        )
    stats_html += '</div>'

    # Why-us bullets
    why_html = '<ul class="rv-why">'
    for bullet in variant["why_us"]:
        # bullets contain inline em-dashes + parentheticals; preserve as-is
        why_html += f'<li>{bullet}</li>'
    why_html += '</ul>'

    # FAQ accordion (vanilla <details>/<summary> — no JS needed, accessible)
    faq_html = '<div class="rv-faq">'
    for q, a in variant["faqs"]:
        faq_html += (
            '<details class="rv-faq-item">'
            f'<summary class="rv-faq-q">{_html.escape(q)}</summary>'
            f'<div class="rv-faq-a">{_html.escape(a)}</div>'
            '</details>'
        )
    faq_html += '</div>'

    return f"""
<style>
.rv-section{{padding:32px 16px;background:#fff;border-top:1px solid #E2E8F0}}
.rv-section.alt{{background:linear-gradient(180deg,#F8FAFC,#fff)}}
.rv-container{{max-width:980px;margin:0 auto}}
.rv-eyebrow{{color:#0F766E;font-weight:800;font-size:11px;letter-spacing:.1em;text-transform:uppercase;margin:0 0 6px}}
.rv-h2{{margin:0 0 16px;font-size:24px;letter-spacing:-.02em;color:#0F172A}}
.rv-stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:0 0 8px}}
.rv-stat{{background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:14px;text-align:center}}
.rv-stat-val{{font-size:18px;font-weight:800;color:#0F766E;letter-spacing:-.01em}}
.rv-stat-label{{font-size:11.5px;color:#64748B;font-weight:600;margin-top:4px;text-transform:uppercase;letter-spacing:.05em}}
.rv-why{{padding:0;list-style:none;display:grid;gap:10px;margin:8px 0 0}}
.rv-why li{{position:relative;padding:12px 14px 12px 38px;background:#fff;border:1px solid #E2E8F0;border-radius:12px;font-size:14.5px;line-height:1.55;color:#0F172A}}
.rv-why li::before{{content:"\\2713";position:absolute;left:12px;top:12px;width:20px;height:20px;background:#0F766E;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px}}
.rv-body{{font-size:15.5px;line-height:1.65;color:#1E293B}}
.rv-body h2{{font-size:21px;margin:28px 0 12px;letter-spacing:-.01em;color:#0F172A}}
.rv-body h3{{font-size:17px;margin:20px 0 8px;color:#0F172A}}
.rv-body p{{margin:0 0 14px}}
.rv-body ul,.rv-body ol{{margin:8px 0 16px;padding-left:22px}}
.rv-body li{{margin-bottom:6px}}
.rv-body table{{margin:14px 0}}
.rv-faq{{display:grid;gap:8px;margin:16px 0 0}}
.rv-faq-item{{background:#fff;border:1px solid #E2E8F0;border-radius:12px;overflow:hidden}}
.rv-faq-q{{padding:14px 16px;font-weight:700;color:#0F172A;cursor:pointer;list-style:none;font-size:14.5px;display:flex;justify-content:space-between;align-items:center}}
.rv-faq-q::after{{content:"+";font-size:22px;font-weight:300;color:#0F766E;margin-left:12px;flex-shrink:0}}
.rv-faq-item[open] .rv-faq-q::after{{content:"\\2013"}}
.rv-faq-a{{padding:0 16px 16px;color:#475569;font-size:14px;line-height:1.6}}
@media(max-width:640px){{.rv-stats{{grid-template-columns:repeat(2,1fr)}}.rv-h2{{font-size:20px}}}}
</style>

<section class="rv-section">
  <div class="rv-container">
    <p class="rv-eyebrow">✨ At a glance</p>
    {stats_html}
  </div>
</section>

<section class="rv-section alt">
  <div class="rv-container">
    <p class="rv-eyebrow">Why {_html.escape(brand_name)}</p>
    <h2 class="rv-h2">What makes our service genuinely different</h2>
    {why_html}
  </div>
</section>

<section class="rv-section">
  <div class="rv-container rv-body">
    {variant["body_html"]}
  </div>
</section>

<section class="rv-section alt">
  <div class="rv-container">
    <p class="rv-eyebrow">FAQ</p>
    <h2 class="rv-h2">Honest answers, no fluff</h2>
    {faq_html}
  </div>
</section>
"""


def _build_jsonld(variant: dict, brand: dict, full_url: str, image_url: str) -> str:
    """Emit BreadcrumbList + FAQPage + Service JSON-LD as a single <script> block."""
    brand_name = brand.get("name", "Servia")
    domain = brand.get("domain", "servia.ae")
    parent_slug = variant["parent_svc_id"].replace("_", "-")

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home",
             "item": f"https://{domain}/"},
            {"@type": "ListItem", "position": 2, "name": variant["h1"].split("—")[0].strip(),
             "item": f"https://{domain}/services/{parent_slug}"},
            {"@type": "ListItem", "position": 3, "name": variant["h1"],
             "item": full_url},
        ],
    }

    faqpage = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in variant["faqs"]
        ],
    }

    # Extract price range from stats — first stat's value if it has "AED"
    price_range = ""
    for label, val in variant["stats"]:
        if "AED" in val:
            price_range = f"AED {val.replace('AED', '').strip()}+"
            break

    service = {
        "@context": "https://schema.org",
        "@type": "Service",
        "serviceType": variant["schema_service_type"],
        "name": variant["h1"],
        "provider": {
            "@type": "Organization",
            "name": brand_name,
            "url": f"https://{domain}/",
            "logo": f"https://{domain}/mascot.svg",
        },
        "areaServed": {"@type": "City", "name": "Dubai"},
        "url": full_url,
        "image": image_url,
        "description": variant.get("meta_desc", ""),
    }
    if price_range:
        service["offers"] = {
            "@type": "AggregateOffer",
            "priceCurrency": "AED",
            "priceRange": price_range,
        }

    parts = [breadcrumb, faqpage, service]
    return "\n".join(
        f'<script type="application/ld+json">{json.dumps(p, ensure_ascii=False)}</script>'
        for p in parts
    )


def render_rich_variant(variant: dict) -> HTMLResponse:
    """Render a rich indexed landing page for a high-CPC variant.

    The page reuses service.html (so nav/footer/CTAs/booking form stay
    consistent) and INJECTS the rich content + JSON-LD schema, while
    overriding title/meta/canonical/robots for SEO.
    """
    tpl = _settings.WEB_DIR / "service.html"
    if not tpl.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="service.html template missing")
    html = tpl.read_text(encoding="utf-8")
    brand = _settings.brand()
    brand_name = brand.get("name", "Servia")
    domain = brand.get("domain", "servia.ae")
    full_url = f"https://{domain}/{variant['slug']}"

    # 1. Title + meta description + canonical override
    title_safe = variant["meta_title"].replace('"', "&quot;")
    desc_safe = variant["meta_desc"].replace('"', "&quot;")
    html = (
        html
        .replace("<title>Service • Servia</title>",
                 f"<title>{title_safe}</title>")
        .replace(
            '<meta name="description" content="Professional home services across all 7 UAE emirates. Same-day booking, transparent AED pricing, fully insured crews.">',
            f'<meta name="description" content="{desc_safe}">')
        .replace(
            '<link rel="canonical" href="https://servia.ae/services">',
            f'<link rel="canonical" href="{full_url}">'
            '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">')
    )

    # 2. Inject service id shim so service.html JS loads the right service
    svc_id = variant["parent_svc_id"]
    shim = (
        '<script>(function(){try{var u=new URL(location.href);'
        f'if(!u.searchParams.get("id"))u.searchParams.set("id","{svc_id}");'
        'history.replaceState(null,"",u.toString());'
        '}catch(_){}})();</script>'
    )
    html = html.replace("</head>", shim + "</head>", 1)

    # 3. Inject JSON-LD schema right before </head>
    image_url = _hero_image_url(variant["slug"], variant["image_prompt"])
    jsonld_block = _build_jsonld(variant, brand, full_url, image_url)
    html = html.replace("</head>", jsonld_block + "</head>", 1)

    # 4. Inject the rich content block. Anchor: before the closing </body> tag
    # so it appears AFTER the booking form. SEO crawlers don't care about
    # placement order within body — they read the whole DOM.
    content_block = _build_rich_content_html(variant, brand_name)
    html = html.replace("</body>", content_block + "</body>", 1)

    return HTMLResponse(html)


def is_rich_variant(alias: str, area_slug: str) -> bool:
    """Check whether a given (alias, area) URL combo is a rich variant page."""
    return f"{alias}-{area_slug}" in VARIANT_BY_SLUG


def get_rich_variant(alias: str, area_slug: str) -> dict | None:
    """Return the variant dict for an (alias, area) URL combo, or None."""
    return VARIANT_BY_SLUG.get(f"{alias}-{area_slug}")


def canonical_for_sister_lp(alias: str, brand_domain: str) -> str | None:
    """If `alias` has a rich variant page, return the canonical URL to point
    sister LPs at. Otherwise None (caller falls back to default canonical)."""
    rich_slug = RICH_ALIAS_TO_SLUG.get(alias)
    if rich_slug:
        return f"https://{brand_domain}/{rich_slug}"
    return None
