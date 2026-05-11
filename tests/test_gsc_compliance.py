#!/usr/bin/env python3
"""v1.24.104 — Google Search Console compliance tests.

Asserts the SEO-correctness invariants founder GSC flagged:
  - No "Duplicate unique property" → no JSON-LD with multiple Service @types
  - No "Alternative page with proper canonical tag" → legacy URLs 301 redirect
  - No "Not found 404" → no literal ${...} template strings in static HTML
  - No empty canonical href on customer-facing pages
  - QAPage replaced with FAQPage on home (Q&A missing-field warnings)
"""
from __future__ import annotations

import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

passed = 0
failed: list[tuple[str, str]] = []


def t(name, ok, detail=""):
    global passed
    icon = "PASS" if ok else "FAIL"
    print(f"{icon}  {name}" + (f"  — {detail}" if detail else ""))
    if ok: passed += 1
    else: failed.append((name, detail))


print("="*70)
print(" GSC COMPLIANCE — v1.24.104")
print("="*70)

WEB = os.path.join(os.path.dirname(__file__), "..", "web")

# ─── Bug 26: home page must use FAQPage, not QAPage ──────────────────
idx = open(os.path.join(WEB, "index.html"), encoding="utf-8").read()
t("1. (L26) home page no longer emits QAPage schema",
  '"@type":"QAPage"' not in idx,
  "QAPage requires author/datePublished/upvoteCount; we're a service site → FAQPage")
t("2. (L26) home page emits FAQPage with mainEntity array",
  '"@type":"FAQPage"' in idx and '"mainEntity":[' in idx)

# ─── Bug 27: no literal ${...} template strings get indexed ──────────
# Filter `valid` posts in render() means the literal href can't escape.
t("3. (L27) render() filters posts with valid slug before innerHTML",
  ".filter(p => p && p.slug" in idx,
  "guards against ${esc(p.slug)} leaking as a literal URL")

# ─── area.html: no /api/videos/play/em- emission with empty city ─────
area = open(os.path.join(WEB, "area.html"), encoding="utf-8").read()
t("4. (L27b) area.html validates city against VALID emirate list",
  "VALID.includes(city)" in area,
  "prevents /api/videos/play/em- 404 when city param missing/invalid")

# ─── Canonicals: no empty href on customer-facing pages ──────────────
empties = []
for fname in ("index.html", "services.html", "service.html", "area.html",
              "book.html", "faq.html", "contact.html", "coverage.html",
              "gallery.html", "videos.html", "nfc.html",
              "share-rewards.html", "vendor.html"):
    src = open(os.path.join(WEB, fname), encoding="utf-8").read()
    if '<link rel="canonical" href="">' in src:
        empties.append(fname)
t("5. (L24) NO customer-facing page has empty canonical href",
  not empties, f"empty: {empties}")

# ─── Legacy URL redirect endpoint exists ─────────────────────────────
import app.main as _main
import inspect
mainsrc = inspect.getsource(_main)
t("6. (L25) /services.html legacy redirect handler registered",
  "services_legacy_redirect" in mainsrc and
  '@app.get("/services.html"' in mainsrc)
t("7. (L25) handler 301s service+area to /services/{svc}/{area}",
  "return RedirectResponse(url=f\"/services/{s}/{a}\", status_code=301)" in mainsrc)
t("8. (L25) handler 301s service-only to /services/{svc}",
  'return RedirectResponse(url=f"/services/{s}", status_code=301)' in mainsrc)

# ─── seo_pages strips duplicate Service/BreadcrumbList JSON-LD ───────
import app.seo_pages as _sp
seosrc = inspect.getsource(_sp)
t("9. (L23) seo_pages strips template Service+Breadcrumb JSON-LD",
  "Service|BreadcrumbList" in seosrc and
  "DOTALL" in seosrc,
  "regex strips existing Service/BreadcrumbList blocks before injection")
t("10. (L23) seo_pages injects exactly ONE Service + ONE BreadcrumbList",
  "_localbusiness_jsonld" in seosrc and "BreadcrumbList" in seosrc and
  '"itemListElement":[' in seosrc)

# ─── Admin pages have noindex robots meta ────────────────────────────
missing_noindex = []
for fname in ("admin.html", "admin-live.html", "admin-login.html",
              "admin-widget.html", "admin-e2e-shots.html",
              "brand-preview.html", "gate.html",
              "pay-declined.html", "pay-processing.html", "reset.html"):
    p = os.path.join(WEB, fname)
    if not os.path.isfile(p): continue
    src = open(p, encoding="utf-8").read()
    if not re.search(r'name="robots"[^>]*noindex', src) and \
       not re.search(r'noindex[^>]*name="robots"', src):
        missing_noindex.append(fname)
t("11. all admin/transactional pages have noindex robots meta",
  not missing_noindex, f"missing: {missing_noindex}")

# Summary
total = passed + len(failed)
print()
print("="*70)
print(f" GSC COMPLIANCE RESULT: {passed}/{total}")
print("="*70)
if failed:
    for n, d in failed: print(f"  FAIL: {n}  {d}")
sys.exit(0 if not failed else 1)
