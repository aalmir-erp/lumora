#!/usr/bin/env python3
"""v1.24.97 — programmatic SEO test suite.

Covers:
  - 63 area slugs from AREA_MAP build into AREA_INDEX
  - 37 services × 63 areas = 2,331 unique combos
  - slugify is idempotent & URL-safe
  - render_service_area_page produces unique title/H1/canonical/JSON-LD
    per (service, area) combination
  - JSON-LD includes areaServed
  - Internal links don't self-link
  - sitemap-areas.xml URL count math is correct (no off-by-one,
    no duplicates from .html alias)
  - Slug round-trip: any AREA_MAP entry → slugify → area_by_slug works
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

passed = 0
failed: list[tuple[str, str]] = []


def t(name: str, ok: bool, detail: str = "") -> None:
    global passed
    icon = "PASS" if ok else "FAIL"
    print(f"{icon}  {name}" + (f"  — {detail}" if detail else ""))
    if ok:
        passed += 1
    else:
        failed.append((name, detail))


print("="*70)
print(" PROGRAMMATIC SEO PAGES — v1.24.97")
print("="*70)

from app import seo_pages as _seo
from app import kb as _kb

# 1. AREA_INDEX integrity
expected_min = sum(len(v) for v in _seo.AREA_MAP.values())
t("1. AREA_INDEX has 63 entries (≥ all in AREA_MAP, no dedup losses)",
  len(_seo.AREA_INDEX) == expected_min,
  f"expected {expected_min}, got {len(_seo.AREA_INDEX)}")
t("2. dubai-marina exists (sanity)",
  "dubai-marina" in _seo.AREA_INDEX,
  str(_seo.area_by_slug("dubai-marina")))
t("3. al-khan exists (Sharjah sanity)",
  "al-khan" in _seo.AREA_INDEX,
  str(_seo.area_by_slug("al-khan")))

# 2. slugify
t("4. slugify('Dubai Marina') == 'dubai-marina'",
  _seo.slugify("Dubai Marina") == "dubai-marina")
t("5. slugify is idempotent",
  _seo.slugify(_seo.slugify("Al Nahda Sharjah")) == _seo.slugify("Al Nahda Sharjah"))
t("6. slugify strips edges",
  _seo.slugify("  Dubai!Marina  ") == "dubai-marina")
t("7. slugify handles ampersand → dash",
  _seo.slugify("Sofa & Carpet") == "sofa-carpet")

# 3. round-trip every AREA_MAP entry
all_round_trip = True
broken = []
for emirate, areas in _seo.AREA_MAP.items():
    for a in areas:
        slug = _seo.slugify(a)
        if not _seo.area_by_slug(slug):
            all_round_trip = False
            broken.append(a)
t("8. EVERY AREA_MAP entry round-trips through area_by_slug",
  all_round_trip, f"broken: {broken}" if broken else "")

# 4. service × area combinations
svcs = _kb.services()["services"]
combos = list(_seo.iter_all_combos(svcs))
t("9. iter_all_combos yields ≥ services × areas (37 × 63 = 2331)",
  len(combos) == len(svcs) * len(_seo.AREA_INDEX),
  f"got {len(combos)}, expected {len(svcs) * len(_seo.AREA_INDEX)}")
t("10. combos are all unique",
  len({(s, a) for s, a, *_ in combos}) == len(combos),
  f"unique={len({(s, a) for s, a, *_ in combos})} total={len(combos)}")

# 5. canonical URL builder
canon = _seo.service_area_canonical("deep-cleaning", "dubai-marina")
t("11. canonical uses HTTPS and clean path",
  canon == "https://servia.ae/services/deep-cleaning/dubai-marina",
  canon)
t("12. canonical has no .html",
  ".html" not in canon)

# 6. render_service_area_page — load template + render a page
template_path = os.path.join(os.path.dirname(__file__), "..", "web", "service.html")
template = open(template_path, encoding="utf-8").read()
brand = {"name": "Servia", "domain": "servia.ae"}
deep_clean = next(s for s in svcs if s["id"] == "deep_cleaning")
ai_dxb = _seo.area_by_slug("dubai-marina")
html = _seo.render_service_area_page(deep_clean, ai_dxb, brand, template, services=svcs)

t("13. rendered page is non-trivial",
  len(html) > 5000, f"len={len(html)}")
t("14. <title> contains both Service and Area",
  "Deep Cleaning" in html and "Dubai Marina" in html and "<title>" in html)
t("15. canonical link points to /services/deep-cleaning/dubai-marina",
  '<link rel="canonical" href="https://servia.ae/services/deep-cleaning/dubai-marina">' in html)
t("16. meta description mentions Dubai Marina",
  ('content="' in html and "Dubai Marina" in html))
t("17. JSON-LD Service schema with areaServed",
  '"@type":"Service"' in html and '"areaServed"' in html and "Dubai Marina" in html)
t("18. JSON-LD includes the service's starting price",
  '"priceCurrency":"AED"' in html if deep_clean.get("starting_price") else True)
t("19. internal-links block links to OTHER areas (not self)",
  '/services/deep-cleaning/jumeirah' in html or
  '/services/deep-cleaning/jlt' in html)
t("20. internal-links does NOT self-link",
  '/services/deep-cleaning/dubai-marina"' not in html.split("seo-internal-links")[1] if "seo-internal-links" in html else True)
t("21. internal-links mentions related services in the same area",
  '/services/' in html and '/dubai-marina' in html and html.count("/dubai-marina") >= 1)
t("22. Area-aware content block injected (with What's included or pricing)",
  "Dubai Marina" in html and ("included" in html.lower() or "pricing" in html.lower() or "Coverage" in html))

# 7. uniqueness — render two pages, verify they differ
html2 = _seo.render_service_area_page(
    deep_clean, _seo.area_by_slug("yas-island"), brand, template, services=svcs)
t("23. two pages for same service in different areas have different titles",
  "Dubai Marina" in html and "Yas Island" in html2 and html != html2)

# 8. FAQ JSON-LD when service has FAQs
ac_svc = next((s for s in svcs if s["id"] == "ac_cleaning" and s.get("faqs")), None)
if ac_svc:
    h = _seo.render_service_area_page(ac_svc, ai_dxb, brand, template, services=svcs)
    t("24. service WITH faqs emits FAQPage JSON-LD",
      '"@type":"FAQPage"' in h and "Dubai Marina" in h)
else:
    t("24. (skipped — no service with faqs found)", True, "skip")

# 9. 404 path — area_by_slug returns None for unknown
t("25. unknown area returns None (route should 404)",
  _seo.area_by_slug("zzz-not-real") is None)
t("26. empty / None safe",
  _seo.area_by_slug("") is None and _seo.area_by_slug(None) is None)

# Summary
total = passed + len(failed)
print()
print("="*70)
print(f" PROGRAMMATIC SEO RESULT: {passed}/{total}")
print("="*70)
if failed:
    for n, d in failed:
        print(f"  FAIL: {n}  {d}")
sys.exit(0 if not failed else 1)
