"""v1.24.133 — Arabic landing pages for the UAE Arabic Google Ads market.

WHAT
----
~40% of UAE Google searches happen in Arabic. Bidding on Arabic keywords
("تنظيف مكيفات دبي") needs a destination URL in Arabic — Google Ads
landing-page-experience score penalises mismatched language pairs
(English LP for Arabic ad copy ≈ Quality Score 4/10).

This module registers 7 services × 7 emirates = 49 Arabic URL routes,
each rendering web/service.html with:
  - <html lang="ar" dir="rtl">
  - Arabic <title> / meta description / H1 fed from i18n_ar_slugs
  - canonical → the English /services/{slug} page (concentrates equity)
  - noindex,follow (thin translated content; if indexed Google might
    flag as duplicate / low-value. We'll switch to indexed once we
    write unique Arabic editorial content per landing page.)
  - hreflang link rel="alternate" hreflang="en" → English variant

EXTENDING
---------
1. Add service / emirate to i18n_ar_slugs.SERVICE_AR / EMIRATE_AR
2. Module auto-discovers — no code edit needed here

SEO POSITION
------------
Treat these the same way we treat the 17,324 English LPs: noindex paid
destinations. The "indexed" rich variants (rich_variant_pages.py) are a
separate, smaller, hand-written set. Same playbook will apply to Arabic
in a future iteration — write 5 hand-crafted Arabic rich pages, make
those indexed, leave the rest noindex.
"""
from __future__ import annotations

import html as _html

from fastapi.responses import HTMLResponse

from .config import get_settings
from .data.i18n_ar_slugs import SERVICE_AR, EMIRATE_AR


_settings = get_settings()


def _render_ar_lp(svc_id: str, ar_svc_slug: str, ar_svc_name: str,
                  emirate_id: str, ar_em_slug: str, ar_em_name: str) -> HTMLResponse:
    """Render an Arabic landing page for one service × emirate combo."""
    from fastapi import HTTPException as _HE
    tpl = _settings.WEB_DIR / "service.html"
    if not tpl.exists():
        raise _HE(status_code=500, detail="template missing")
    html = tpl.read_text(encoding="utf-8")
    brand = _settings.brand()
    domain = brand.get("domain", "servia.ae")
    brand_name = brand.get("name", "Servia")

    # Arabic title: "تنظيف مكيفات في دبي · سيرفيا الإمارات"
    title = f"{ar_svc_name} في {ar_em_name} · {brand_name} الإمارات"
    desc = (f"{ar_svc_name} في {ar_em_name} مع {brand_name} الإمارات. "
            f"حجز فوري عبر الواتساب، أسعار شفافة بالدرهم، فرق مؤمنة بالكامل، "
            f"خدمة في نفس اليوم متاحة.")

    # English canonical → consolidates SEO equity on the English service page.
    # The English page already has hreflang back to this Arabic URL.
    slug_kebab = svc_id.replace("_", "-")
    canonical = f"https://{domain}/services/{slug_kebab}"
    # English alt URL for hreflang
    en_url = f"https://{domain}/services/{slug_kebab}"
    ar_url = f"https://{domain}/{ar_svc_slug}-{ar_em_slug}"

    title_safe = title.replace('"', "&quot;")
    desc_safe = desc.replace('"', "&quot;")

    html = (
        html
        .replace("<title>Service • Servia</title>",
                 f"<title>{title_safe}</title>")
        .replace(
            '<meta name="description" content="Professional home services across all 7 UAE emirates. Same-day booking, transparent AED pricing, fully insured crews.">',
            f'<meta name="description" content="{desc_safe}">')
        .replace(
            '<link rel="canonical" href="https://servia.ae/services">',
            f'<link rel="canonical" href="{canonical}">'
            '<meta name="robots" content="noindex,follow">'
            # hreflang cross-links so Google knows the relationship between
            # the EN canonical and this Arabic translation. Even though this
            # page is noindex, the hreflang signal helps Google return the
            # Arabic page in Arabic search results (with the canonical
            # English content) if a user has Arabic locale set.
            f'<link rel="alternate" hreflang="ar-AE" href="{ar_url}">'
            f'<link rel="alternate" hreflang="en-AE" href="{en_url}">'
            f'<link rel="alternate" hreflang="x-default" href="{en_url}">')
        # Switch the document direction + language for the entire page.
        # Without this, Arabic text renders left-to-right and looks broken.
        .replace('<html lang="en"', '<html lang="ar" dir="rtl"', 1)
        .replace('<html>', '<html lang="ar" dir="rtl">', 1)
    )

    # Inject service id shim so service.html's JS loads the right service
    shim = (
        '<script>(function(){try{var u=new URL(location.href);'
        f'if(!u.searchParams.get("id"))u.searchParams.set("id","{svc_id}");'
        f'if(!u.searchParams.get("lang"))u.searchParams.set("lang","ar");'
        'history.replaceState(null,"",u.toString());'
        '}catch(_){}})();</script>'
    )
    html = html.replace("</head>", shim + "</head>", 1)

    return HTMLResponse(html)


def register_ar_routes(app) -> int:
    """Register all 7 × 7 Arabic LP routes on the FastAPI app.
    Returns the count for the boot-log line."""
    count = 0
    for svc_id, (ar_svc_slug, ar_svc_name) in SERVICE_AR.items():
        for em_id, (ar_em_slug, ar_em_name) in EMIRATE_AR.items():
            flat = f"{ar_svc_slug}-{ar_em_slug}"

            def make_handler(sid=svc_id, asg=ar_svc_slug, asn=ar_svc_name,
                             eid=em_id, aes=ar_em_slug, aen=ar_em_name):
                def handler():
                    return _render_ar_lp(sid, asg, asn, eid, aes, aen)
                return handler

            # Note: FastAPI handles unicode in URL paths via percent-encoding.
            # The actual registered route is the unicode form; FastAPI matches
            # both the raw and percent-encoded versions.
            app.add_api_route(
                f"/{flat}",
                make_handler(),
                methods=["GET"],
                include_in_schema=False,
                response_class=HTMLResponse,
            )
            count += 1
    return count
