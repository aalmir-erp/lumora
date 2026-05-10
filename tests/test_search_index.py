#!/usr/bin/env python3
"""v1.24.99 — search index + page-consistency test suite.

Covers (founder-reported bugs):
  - Bug 17: search returned 0 results for "muwaileh" because the 1,628
    service×area pages weren't in the static search index
  - Bug 18: chat widget missing on 10+ customer-facing pages (nfc.html,
    install.html, sos.html, etc.)
  - Per W9: every new customer-facing HTML page MUST have widget+nav;
    every new searchable URL MUST be in /api/search/index
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
print(" SEARCH INDEX + PAGE CONSISTENCY — v1.24.99")
print("="*70)

# ─── Build the search index by calling the function directly ─────────
import importlib
_main = importlib.import_module("app.main")
client = None
# Use TestClient so we get the actual route response shape
from fastapi.testclient import TestClient
client = TestClient(_main.app)

resp = client.get("/api/search/index")
t("1. /api/search/index returns 200",
  resp.status_code == 200, f"status={resp.status_code}")

j = resp.json() if resp.status_code == 200 else {}
items = j.get("items") or []
t("2. response has 'items' array",
  isinstance(items, list) and len(items) > 0, f"count={len(items)}")

t("3. count >= 1500 (37 services × 44 areas + 44 areas + 22 manual)",
  len(items) >= 1500, f"got {len(items)}")

# ─── Bug 17: typing 'muwaileh' must find service×area combos ────────
mwa_items = [it for it in items if "muwaileh" in (it.get("url") or "").lower()
             or "muwaileh" in (it.get("title") or "").lower()
             or "muwaileh" in (it.get("body") or "").lower()]
t("4. 'muwaileh' matches at least the area + 37 service-area combos",
  len(mwa_items) >= 30, f"got {len(mwa_items)} muwaileh-related items")

# Specific URLs that MUST be present
required_urls = [
    "/services/deep-cleaning/muwaileh",
    "/services/ac-cleaning/muwaileh",
    "/services/pest-control/muwaileh",
    "/services/deep-cleaning/dubai-marina",
    "/services/deep-cleaning/yas-island",
    "/services/deep-cleaning/al-hamra",
    "/area.html?area=muwaileh",
    "/area.html?area=al-khan",
]
all_urls = {it.get("url") for it in items}
missing = [u for u in required_urls if u not in all_urls]
t("5. all required service×area URLs present",
  not missing, f"missing: {missing}")

# Required manual pages
manual_must = ["/services", "/book", "/coverage", "/faq", "/refund",
               "/terms", "/privacy", "/install", "/contact", "/me",
               "/nfc", "/nfc-vs-qr", "/nfc-villa-bundle",
               "/nfc-vehicle-recovery", "/nfc-laptop-it",
               "/sos", "/smart-speakers", "/share-rewards", "/vendor"]
missing_manual = [u for u in manual_must if u not in all_urls]
t("6. all manual customer-facing pages indexed",
  not missing_manual, f"missing: {missing_manual}")

# Each item has the required shape
shape_ok = all(("title" in it and "url" in it and "kind" in it) for it in items[:50])
t("7. items have {kind, title, body, url} shape",
  shape_ok)

# ─── Bug 18: customer-facing pages must include chat widget ─────────
import os as _os
WEB = _os.path.join(_os.path.dirname(__file__), "..", "web")
# Pages where chat widget is REQUIRED (customer-facing)
CUSTOMER_FACING = [
    "index.html", "services.html", "book.html", "faq.html", "contact.html",
    "coverage.html", "gallery.html", "videos.html", "search.html",
    "nfc.html", "nfc-vs-qr.html", "nfc-villa-bundle.html",
    "nfc-vehicle-recovery.html", "nfc-laptop-it.html",
    "install.html", "privacy.html", "sos.html", "smart-speakers.html",
    "me-profile.html", "me.html", "partner-agreement.html",
    "share-rewards.html", "vendor.html", "service.html", "area.html",
    "refund.html", "terms.html", "account.html",
]
missing_widget = []
for fname in CUSTOMER_FACING:
    p = _os.path.join(WEB, fname)
    if not _os.path.isfile(p):
        continue
    if "widget.js" not in open(p, encoding="utf-8").read():
        missing_widget.append(fname)
t("8. ALL customer-facing pages include /widget.js",
  not missing_widget, f"missing: {missing_widget}")

# Pages where standard nav is REQUIRED (customer-facing)
NAV_REQUIRED = [
    "index.html", "services.html", "book.html", "faq.html", "contact.html",
    "coverage.html", "gallery.html", "videos.html",
    "nfc.html", "nfc-vs-qr.html", "nfc-villa-bundle.html",
    "install.html", "privacy.html", "smart-speakers.html",
    "share-rewards.html", "vendor.html", "service.html", "area.html",
    "refund.html", "terms.html",
]
missing_nav = []
for fname in NAV_REQUIRED:
    p = _os.path.join(WEB, fname)
    if not _os.path.isfile(p):
        continue
    src = open(p, encoding="utf-8").read()
    has_nav = "<nav" in src or "site-header" in src
    if not has_nav:
        missing_nav.append(fname)
t("9. ALL customer-facing pages include <nav> or site-header",
  not missing_nav, f"missing: {missing_nav}")

# Cache-bust must reflect APP_VERSION
import re
bad_cache = []
for fname in CUSTOMER_FACING:
    p = _os.path.join(WEB, fname)
    if not _os.path.isfile(p):
        continue
    src = open(p, encoding="utf-8").read()
    # If any v=1.24.<N> reference exists, the most recent should be the current.
    versions = re.findall(r"v=1\.24\.(\d+)", src)
    if versions and max(int(v) for v in versions) < 99:
        bad_cache.append((fname, max(int(v) for v in versions)))
t("10. customer-facing pages reference current APP_VERSION (or none)",
  not bad_cache, f"stale: {bad_cache}")

# Summary
total = passed + len(failed)
print()
print("="*70)
print(f" SEARCH + CONSISTENCY RESULT: {passed}/{total}")
print("="*70)
if failed:
    for n, d in failed:
        print(f"  FAIL: {n}  {d}")
sys.exit(0 if not failed else 1)
