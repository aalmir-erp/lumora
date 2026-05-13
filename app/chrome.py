"""v1.24.108 — chrome unification. SINGLE SOURCE OF TRUTH for the
canonical Servia nav, footer, and FAB stack.

Founder reported repeatedly: "home page and inner pages header and
footer are not matching" and "floating buttons are not similar".

ROOT CAUSE (per W8 audit): 34 HTML pages each shipped their own
hardcoded <nav class="nav"> and <footer> markup. universal-nav.js
v1.24.32 was rewritten to be additive-only (no nav/footer replacement)
to avoid layout shift — but at the cost of permanent drift.

FIX: server-side substitution via FastAPI middleware. On every HTML
response for a customer-facing page:
  - Replace <nav class="nav"> ... </nav> with NAV_HTML
  - Replace <footer> ... </footer> with FOOTER_HTML
Skip list: api, admin, pay, invoice, gate, reset, brand-preview.

Tests assert every customer route returns BYTE-IDENTICAL nav and
footer. Drift becomes a CI failure.
"""
from __future__ import annotations
import re


# ─────────────────────────────────────────────────────────────────────
# CANONICAL NAV — single source of truth.
# ─────────────────────────────────────────────────────────────────────
NAV_HTML = """<div class="uae-flag-strip" aria-hidden="true" style="height:4px;background:linear-gradient(90deg,#00732F 0% 25%,#fff 25% 50%,#000 50% 75%,#FF0000 75% 100%)"></div>
<nav class="nav" id="servia-canonical-nav"><div class="nav-inner">
  <a href="/" aria-label="Servia home" class="nav-logo"><img src="/logo.svg" width="160" height="52" alt="Servia" decoding="async"></a>
  <small id="lumora-version" style="font-size:10px;color:var(--muted);margin-inline-start:6px;font-weight:600;background:var(--bg);padding:2px 6px;border-radius:6px">v?</small>
  <div class="nav-links">
    <a href="/services">Services</a>
    <a href="/coverage">Coverage</a>
    <a href="/blog">Blog</a>
    <a href="/me">My account</a>
  </div>
  <div class="nav-cta" style="margin-inline-start:auto;display:flex;gap:8px;align-items:center">
    <select class="lang-dropdown" aria-label="Language" id="canonical-lang-dropdown">
      <option value="en">EN</option><option value="ar">عربي</option>
      <option value="hi">हिंदी</option><option value="ur">اردو</option>
      <option value="tl">FIL</option><option value="fr">FR</option>
    </select>
    <a class="btn btn-icon" href="/search" aria-label="Search">🔍</a>
    <a class="btn btn-primary" href="/book">Book now</a>
  </div>
</div></nav>"""


# ─────────────────────────────────────────────────────────────────────
# CANONICAL FOOTER — single source of truth.
# v1.24.147 — phone number is a placeholder `{{BC_WA_RAW}}` substituted
# at request time by inject_chrome() with brand_contact.get_contact_whatsapp()
# so the admin can change it once in /admin-contact and it flows to every page.
# ─────────────────────────────────────────────────────────────────────
FOOTER_HTML = """<footer id="servia-canonical-footer"><div class="container">
  <div>
    <img src="/logo.svg" width="112" height="36" alt="Servia" style="filter:brightness(0) invert(1)" decoding="async">
    <p style="margin:12px 0;font-size:13px;opacity:.85" data-i18n="footer_tagline">Built for UAE homes &amp; businesses · 4.9★ from 2,400+ families.</p>
    <div style="display:flex;gap:8px;margin-top:14px">
      <a href="https://wa.me/{{BC_WA_RAW}}" target="_blank" rel="noopener" style="background:#075E54;color:#fff;padding:8px 14px;border-radius:999px;font-size:12px;font-weight:700;text-decoration:none">WhatsApp</a>
      <a href="/install" style="background:#fff;color:#0F172A;padding:8px 14px;border-radius:999px;font-size:12px;font-weight:700;text-decoration:none">Install app</a>
    </div>
  </div>
  <div>
    <h3>Services</h3>
    <a href="/services/deep-cleaning">Deep cleaning</a><br>
    <a href="/services/ac-cleaning">AC service</a><br>
    <a href="/services/pest-control">Pest control</a><br>
    <a href="/services/maid-service">Maid service</a><br>
    <a href="/services/handyman">Handyman</a><br>
    <a href="/services">All 32 services &rarr;</a>
  </div>
  <div>
    <h3>Coverage</h3>
    <a href="/area.html?city=dubai">Dubai</a><br>
    <a href="/area.html?city=sharjah">Sharjah</a><br>
    <a href="/area.html?city=abu-dhabi">Abu Dhabi</a><br>
    <a href="/area.html?city=ajman">Ajman</a><br>
    <a href="/coverage">All 7 emirates</a>
  </div>
  <div>
    <h3>Company</h3>
    <a href="/blog">Servia Journal</a><br>
    <a href="/about">About</a><br>
    <a href="/contact">Contact</a><br>
    <a href="/vendor">Become a partner</a><br>
    <a href="/share-rewards">Refer &amp; earn</a>
  </div>
  <div>
    <h3>Legal</h3>
    <a href="/terms">Terms</a><br>
    <a href="/privacy">Privacy</a><br>
    <a href="/refund">Refund policy</a><br>
    <a href="/faq">FAQ</a>
  </div>
</div></footer>"""


SKIP_PREFIXES = (
    "/api/", "/admin", "/vendor", "/portal", "/pay",
    "/invoice", "/gate", "/reset", "/brand-preview",
    "/admin-", "/sitemap", "/robots", "/llms", "/.well-known",
    "/static/", "/img/", "/web/", "/_snippets", "/manifest",
    "/sw.js", "/widget.",
    # v1.24.148 — self-contained pages with their own intentional dashboard/UI
    # design. Chrome injection would break their layout because they don't
    # load /style.css (their styles are inline + self-sufficient).
    "/checkout", "/host", "/pitch", "/sos",
)


def should_skip_chrome(path: str) -> bool:
    if not path:
        return True
    return any(path.startswith(p) for p in SKIP_PREFIXES)


_NAV_RE = re.compile(
    r'(<div\s+class="uae-flag-strip"[^>]*>\s*</div>\s*)?'
    r'<nav\s+class="nav"[^>]*>.*?</nav>',
    re.DOTALL | re.IGNORECASE,
)
_FOOTER_RE = re.compile(
    r'<footer[^>]*>.*?</footer>',
    re.DOTALL | re.IGNORECASE,
)


def inject_chrome(html: str, path: str = "") -> str:
    """Replace nav + footer in `html` with canonical versions, AND
    substitute brand-contact placeholders ({{BC_PHONE}}, {{BC_EMAIL}},
    {{BC_WA_RAW}}, {{BC_BRAND}}) anywhere they appear in the body.
    Skips admin/transactional.

    v1.24.147 — Placeholder substitution runs even when no <nav> match
    (so admin pages, transactional pages, and any HTML can use them).
    Skip list still suppresses both nav-replace AND placeholder-replace
    for genuinely-private surfaces (/api/, /admin, /pay, etc.).
    """
    if not html:
        return html
    if path and should_skip_chrome(path):
        return html

    new_html = html
    if "<nav" in html.lower():
        new_html = _NAV_RE.sub(NAV_HTML, new_html, count=1)
        new_html = _FOOTER_RE.sub(FOOTER_HTML, new_html, count=1)

    # Substitute brand-contact placeholders anywhere in body
    # so static HTML pages can reference {{BC_PHONE}} etc directly.
    if "{{BC_" in new_html:
        try:
            from .brand_contact import get_brand_block
            b = get_brand_block()
            wa_raw = (b.get("contact_whatsapp") or b.get("contact_phone") or "").lstrip("+").replace(" ", "").replace("-", "")
            phone_raw = (b.get("contact_phone") or "").replace(" ", "")
            tel_url = f"tel:{phone_raw}" if phone_raw else "tel:"
            wa_url = f"https://wa.me/{wa_raw}" if wa_raw else ""
            new_html = (new_html
                .replace("{{BC_WA_RAW}}",  wa_raw)
                .replace("{{BC_WA_URL}}",  wa_url)
                .replace("{{BC_PHONE}}",   b.get("contact_phone")    or "")
                .replace("{{BC_TEL_URL}}", tel_url)
                .replace("{{BC_EMAIL}}",   b.get("contact_email")    or "")
                .replace("{{BC_BRAND}}",   b.get("brand_name")       or "Servia"))
        except Exception:
            pass
    return new_html
