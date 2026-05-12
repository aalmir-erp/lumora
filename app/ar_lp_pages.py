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
from .data.i18n_ar_content import SERVICE_AR_CONTENT, UI_AR


_settings = get_settings()


def _render_ar_lp(svc_id: str, ar_svc_slug: str, ar_svc_name: str,
                  emirate_id: str, ar_em_slug: str, ar_em_name: str) -> HTMLResponse:
    """Render an Arabic landing page for one service × emirate combo.

    v1.24.140 — Real Arabic content overlay:
      - Drops dir="rtl" (existing CSS is LTR-only — flipping it broke
        the layout with overflowing buttons + cut-off section headers).
        Keeps lang="ar" so screen-readers + Google use Arabic semantics.
      - Injects window.__SERVIA_AR_CONTENT (per-service + UI translations)
        + a small overlay script that swaps English strings to Arabic
        AFTER service.html's JS finishes rendering.
      - Adds a Phase-4 disclosure banner (Arabic content in progress).
    """
    import json as _json
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
    slug_kebab = svc_id.replace("_", "-")
    canonical = f"https://{domain}/services/{slug_kebab}"
    en_url = f"https://{domain}/services/{slug_kebab}"
    ar_url = f"https://{domain}/{ar_svc_slug}-{ar_em_slug}"

    title_safe = title.replace('"', "&quot;")
    desc_safe = desc.replace('"', "&quot;")

    # Per-service Arabic content blob (None if not yet translated)
    svc_ar = SERVICE_AR_CONTENT.get(svc_id) or {}

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
            f'<link rel="alternate" hreflang="ar-AE" href="{ar_url}">'
            f'<link rel="alternate" hreflang="en-AE" href="{en_url}">'
            f'<link rel="alternate" hreflang="x-default" href="{en_url}">')
        # v1.24.140 — DROPPED dir="rtl". Existing CSS is LTR-only.
        # Reinstating RTL requires a full CSS refactor (Phase 4). For now
        # we keep lang="ar" so screen-readers + Google get the language
        # signal, but the visual direction stays LTR to preserve layout.
        .replace('<html lang="en"', '<html lang="ar"', 1)
    )

    # Inject service-id shim + Arabic-content overlay BEFORE </head>.
    # The overlay runs every 100ms for 5 seconds, replacing English strings
    # with Arabic equivalents as service.html's async JS renders them.
    ar_payload = {
        "ar_service_name":   ar_svc_name,
        "ar_emirate_name":   ar_em_name,
        "service_id":        svc_id,
        "service":           svc_ar,    # full per-service Arabic blob
        "ui":                UI_AR,     # static UI string translations
    }
    ar_payload_json = _json.dumps(ar_payload, ensure_ascii=False)

    overlay = f"""
<script>(function(){{
  try{{
    // Service-id shim — load the right service via service.html's existing JS path.
    var u = new URL(location.href);
    if (!u.searchParams.get("id")) u.searchParams.set("id", "{svc_id}");
    if (!u.searchParams.get("lang")) u.searchParams.set("lang", "ar");
    history.replaceState(null, "", u.toString());

    // Arabic content payload.
    window.__SERVIA_AR_CONTENT = {ar_payload_json};

    // Overlay engine — swaps English strings → Arabic post-render.
    var AR = window.__SERVIA_AR_CONTENT;
    var SVC = AR.service || {{}};
    var UI = AR.ui || {{}};

    function setText(el, text) {{
      if (!el) return;
      if (el.textContent !== text) el.textContent = text;
    }}
    function setHTML(el, html) {{
      if (!el) return;
      if (el.innerHTML !== html) el.innerHTML = html;
    }}

    function applyAr() {{
      try {{
        // H1 service name + price prefix
        var h1 = document.getElementById("svc-name");
        if (h1 && SVC.name) {{
          // Find the inline <span class="price-big"> if service.html already set it
          var priceMatch = h1.innerHTML.match(/<span[^>]*class=['\\"]price-big['\\"][^>]*>([^<]+)<\\/span>/);
          var priceTxt = priceMatch ? priceMatch[1] : "";
          // Translate "from X AED" → "ابتداءً من X درهم"
          var arPrice = priceTxt
            .replace(/^\\s*from\\s+/i, "ابتداءً من ")
            .replace(/\\s+AED\\s*$/i, " درهم");
          setHTML(h1, SVC.name + (arPrice ? " <span class='price-big'>" + arPrice + "</span>" : ""));
        }}

        // Lead description
        if (SVC.description) {{
          setText(document.getElementById("svc-desc"), SVC.description);
        }}

        // Category pill — translate via UI map
        var pill = document.getElementById("cat-pill");
        if (pill) {{
          var txt = pill.textContent.replace(/^[^A-Za-z\\u0600-\\u06FF]*/, "").trim();
          if (UI[txt]) pill.textContent = "📂 " + UI[txt];
        }}

        // Duration + team badges
        if (SVC.duration_label || SVC.team_label) {{
          var badges = document.getElementById("badges");
          if (badges && badges.innerHTML.indexOf("hours") > -1) {{
            // Find duration <span> (⏱️) and team <span> (👥)
            badges.querySelectorAll("span").forEach(function(s) {{
              var t = s.textContent;
              if (/⏱/.test(t) && SVC.duration_label) {{
                s.textContent = "⏱️ " + SVC.duration_label;
              }} else if (/👥/.test(t) && SVC.team_label) {{
                s.textContent = "👥 " + SVC.team_label;
              }} else if (/Insured/i.test(t)) {{
                s.textContent = "✓ مؤمَّن";
              }} else if (/Background-checked/i.test(t)) {{
                s.textContent = "✓ موثَّق الخلفية";
              }}
            }});
          }}
        }}

        // Benefits grid
        if (SVC.benefits && SVC.benefits.length) {{
          var benefitsEl = document.getElementById("benefits");
          if (benefitsEl && benefitsEl.children.length === SVC.benefits.length) {{
            for (var i = 0; i < SVC.benefits.length; i++) {{
              var card = benefitsEl.children[i];
              // service.html's benefit-card structure has the title text as the
              // last <p> inside. Walk to find it.
              var ps = card.querySelectorAll("p");
              if (ps.length > 0) {{
                setText(ps[ps.length - 1], SVC.benefits[i]);
              }} else {{
                setText(card, SVC.benefits[i]);
              }}
            }}
          }}
        }}

        // CTAs in hero
        var btnBook = document.getElementById("cta-book");
        if (btnBook && /Get instant quote/.test(btnBook.textContent)) {{
          btnBook.textContent = "احصل على سعر فوري ←";
        }}
        var ctaWA = document.getElementById("cta-wa");
        if (ctaWA && /WhatsApp/i.test(ctaWA.textContent)) {{
          // Walk for innermost text node
          ctaWA.childNodes.forEach(function(n) {{
            if (n.nodeType === 3 && /WhatsApp/i.test(n.textContent)) {{
              n.textContent = " راسلنا واتساب";
            }}
          }});
        }}
        var ctaBundle = document.getElementById("cta-bundle");
        if (ctaBundle && /Add to bundle/i.test(ctaBundle.textContent)) {{
          ctaBundle.textContent = "أضف إلى الباقة";
        }}

        // Mascot title
        var mTitle = document.getElementById("mascot-title");
        if (mTitle && /^Servia/.test(mTitle.textContent)) {{
          var raw = mTitle.textContent;
          if (UI[raw]) mTitle.textContent = UI[raw];
          else mTitle.textContent = "سيرفيا · " + (SVC.name || "الفني");
        }}

        // Sticky bottom price + book button
        var sp = document.getElementById("sticky-price");
        if (sp && /from .* AED/.test(sp.textContent)) {{
          sp.textContent = sp.textContent
            .replace(/^from\\s+/, "ابتداءً من ")
            .replace(/\\s+AED$/, " درهم");
        }}

        // Pass over all visible H2 + button text via UI map
        document.querySelectorAll("h2, h3, button, a.btn, .btn-wa").forEach(function(el) {{
          var t = el.textContent.trim();
          if (UI[t]) setText(el, UI[t]);
        }});
      }} catch(_e) {{}}
    }}

    // Run shortly after page load, then poll for 5 seconds to catch async re-renders.
    if (document.readyState !== "loading") setTimeout(applyAr, 50);
    else document.addEventListener("DOMContentLoaded", function(){{ setTimeout(applyAr, 50); }});
    var ticks = 0;
    var iv = setInterval(function(){{ applyAr(); if (++ticks > 25) clearInterval(iv); }}, 200);
  }} catch(_e) {{}}
}})();</script>
"""
    # Phase-4 honest disclosure banner (Arabic, top of page).
    # Small, dismissible, doesn't break the layout.
    ar_banner = """
<style>#srv-ar-banner{position:fixed;top:0;left:0;right:0;background:linear-gradient(90deg,#0F766E,#0D9488);color:#fff;padding:8px 14px;text-align:center;font-size:12.5px;z-index:9999;display:flex;align-items:center;justify-content:center;gap:12px;font-weight:600}#srv-ar-banner a{color:#FCD34D;text-decoration:underline;font-weight:700}#srv-ar-banner button{background:transparent;border:0;color:rgba(255,255,255,.7);font-size:18px;cursor:pointer;padding:0 6px}body.has-ar-banner{padding-top:36px}@media(max-width:600px){#srv-ar-banner{font-size:11px;padding:6px 10px}}</style>
<script>(function(){if(sessionStorage.getItem("ar-banner-hide")==="1")return;var b=document.createElement("div");b.id="srv-ar-banner";b.innerHTML='<span>🌐 النسخة العربية تجريبية &middot; بعض المحتوى لا يزال بالإنجليزية &middot; <a href="REPLACE_EN_URL">عرض الإنجليزية</a></span><button aria-label="إغلاق" onclick="this.parentNode.remove();document.body.classList.remove(\\'has-ar-banner\\');sessionStorage.setItem(\\'ar-banner-hide\\',\\'1\\')">&times;</button>';document.body.appendChild(b);document.body.classList.add("has-ar-banner");})();</script>
""".replace("REPLACE_EN_URL", en_url)

    html = html.replace("</head>", overlay + ar_banner + "</head>", 1)

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
