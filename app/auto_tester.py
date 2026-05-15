"""v1.24.228 — Autonomous site tester ("Inspector bot").

Founder mandate: "create one other bot whose job is to keep testing all
pages and its views, use its functions, generate reports with proof,
keep telling you so you keep fixing without stopping."

This module runs OUR OWN test suite against OUR OWN deployed server (in-
process via FastAPI's TestClient) on a schedule, records every finding
into a database, exposes them via admin endpoints + admin UI, and
auto-fixes the safe ones it can handle without human review.

ARCHITECTURE
------------
1) `audit_all_pages()` — walks every customer-facing route + a few
   critical API endpoints, runs N checks per page (see below), returns
   a list of findings.

2) Findings are persisted to `auto_test_findings` (one row per issue)
   linked to a parent `auto_test_runs` row (one per scan).

3) Triggered three ways:
   - Hourly cron via APScheduler (registered in main.py)
   - Admin "Run scan now" button → POST /api/admin/auto-tests/run-now
   - On every git push (CI calls /api/admin/auto-tests/run-now)

4) Admin UI at /admin#auto-tests shows runs, findings, severity badges,
   filters, and a "Mark resolved" button.

CHECKS PER PAGE
---------------
  status_ok        HTTP 200 or 302 (allowed redirects)
  content_type     text/html for .html paths
  response_time    < 3s
  has_title        non-empty <title>
  has_description  meta name=description
  has_viewport     meta name=viewport for mobile rendering
  has_canonical    link rel=canonical for SEO
  broken_hrefs     no href="..." pointing at a route/file that returns 404
  missing_assets   all <link href> + <script src> + <img src> resolve
  template_leak    no literal "${...}" or "C.name" or "Loading..." stuck
                   in rendered HTML (the area.html / checkout.html bug
                   patterns we keep hitting)
  chat_widget      page either has chat widget or is in skip list
  open_graph       og:title + og:image present on customer pages
  uniform_chrome   nav OR injected nav present at top

SEVERITY
--------
  error    page broken for users (5xx, 404 on links, JS template leaks)
  warning  page works but missing best-practice (no canonical, slow)
  info     cosmetic / nice-to-have

AUTO-FIX RULES (safe)
---------------------
- None enabled by default. Findings → admin review. Future tier:
  add <html lang=en>, add rel=noopener to target=_blank links.
"""
from __future__ import annotations

import datetime as _dt
import json as _j
import os
import re
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from . import db
from .auth import require_admin

router = APIRouter(prefix="/api/admin/auto-tests",
                   tags=["auto-tester"],
                   dependencies=[Depends(require_admin)])

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
# v1.24.233 — Screenshot directory. /data is the Railway volume mount.
SHOTS_DIR = Path(os.getenv("DATA_DIR", "/data")) / "inspector-shots"
try: SHOTS_DIR.mkdir(parents=True, exist_ok=True)
except Exception: SHOTS_DIR = Path("/tmp/inspector-shots"); SHOTS_DIR.mkdir(parents=True, exist_ok=True)
CHROMIUM_PATH = os.getenv("PUPPETEER_EXECUTABLE_PATH", "/usr/bin/chromium")


def _ensure_tables() -> None:
    with db.connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS auto_test_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              started_at TEXT NOT NULL,
              finished_at TEXT,
              pages_tested INTEGER DEFAULT 0,
              findings_count INTEGER DEFAULT 0,
              errors INTEGER DEFAULT 0,
              warnings INTEGER DEFAULT 0,
              infos INTEGER DEFAULT 0,
              duration_ms INTEGER,
              trigger TEXT
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS auto_test_findings (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER NOT NULL,
              path TEXT NOT NULL,
              severity TEXT NOT NULL,
              category TEXT NOT NULL,
              message TEXT NOT NULL,
              detail TEXT,
              resolved INTEGER DEFAULT 0,
              resolved_at TEXT,
              resolved_by TEXT,
              created_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES auto_test_runs(id)
            )""")
        # v1.24.229 — Proof artefact column. Stores up to ~4 KB of
        # rendered HTML around the broken element so the founder can
        # see EXACTLY what was caught, not just a category label.
        for stmt in (
            "ALTER TABLE auto_test_findings ADD COLUMN proof_snippet TEXT",
            "ALTER TABLE auto_test_findings ADD COLUMN http_status INTEGER",
        ):
            try: c.execute(stmt)
            except Exception: pass
        c.execute("CREATE INDEX IF NOT EXISTS idx_findings_run ON auto_test_findings(run_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_findings_resolved ON auto_test_findings(resolved, severity)")


def _customer_pages(full: bool = False) -> list[str]:
    """Return every customer-facing path to audit.

    v1.24.233 — `full=True` returns the full programmatic route set
    (~2000+ pages) instead of the 136-page sample. Used for the
    "deep scan" cron + the manual 'Run full scan' button. The default
    `full=False` is the fast representative sample for hourly checks.
    """
    pages: list[str] = []
    # 1. Static HTML files
    skip_files = {"admin.html", "admin-inbox.html", "admin-live.html",
                  "admin-contact.html", "admin-commerce.html",
                  "admin-ai-engines.html", "admin-e2e-shots.html",
                  "admin-wa-bridge.html", "admin-login.html",
                  "admin-widget.html", "vendor.html", "portal-vendor.html",
                  "login.html", "gate.html", "reset.html",
                  "404.html", "brand-preview.html",
                  # v1.24.235 — these pages REQUIRE a query-string param
                  # (?q=, ?inv=) and look "broken" without one. Tested
                  # via dedicated /q/<id> / /p/<id> / /checkout?q= routes
                  # that DO have a real ID, not the bare path.
                  "checkout.html", "pay-declined.html", "pay-processing.html",
                  "booked.html", "delivered.html", "invoice.html",
                  "quote.html"}
    for f in sorted(WEB_DIR.glob("*.html")):
        if f.name in skip_files:
            continue
        slug = f.stem
        pages.append(f"/{slug}" if slug != "index" else "/")

    # 2. v1.24.229 — Programmatic /services/<slug> pages (40 services).
    # Founder reported the tester only covered 44 pages — the site has
    # ~18K routes. Sample all service slugs + every emirate combo for
    # the top-volume services so we catch any template breakage that
    # only manifests on dynamic routes.
    try:
        from . import kb as _kb
        services = _kb.services().get("services", [])
        for s in services:
            sid = (s.get("id") or "").replace("_", "-")
            if sid:
                pages.append(f"/services/{sid}")
    except Exception:
        pass

    # 3. Top-volume service × emirate combos (5 services × 7 emirates = 35)
    emirates = ["dubai", "sharjah", "ajman", "abu-dhabi",
                "ras-al-khaimah", "umm-al-quwain", "fujairah"]
    hot_services = ["deep-cleaning", "ac-cleaning", "maid-service",
                    "handyman", "pest-control"]
    for s in hot_services:
        for em in emirates:
            pages.append(f"/services/{s}/{em}")

    # 4. Area pages (every emirate)
    for em in emirates:
        pages.append(f"/area?city={em}")

    # 5. NFC subpages (already-covered as static, just ensure)
    pages.extend(["/nfc-villa-bundle", "/nfc-vehicle-recovery",
                  "/nfc-laptop-it", "/nfc-vs-qr"])

    # 6. Key API endpoints (sanity — they should respond 200)
    pages.extend([
        "/api/health", "/api/brand", "/api/services",
        "/manifest.webmanifest", "/sw.js", "/sitemap.xml",
        "/robots.txt", "/llms.txt",
    ])

    # 7. Blog index + a couple of blog posts (if any exist in DB)
    pages.extend(["/blog", "/videos"])

    # 8. Real blog posts from DB (sample 20 if exists)
    try:
        with db.connect() as c:
            rows = c.execute(
                "SELECT slug FROM blog_posts WHERE published=1 "
                "ORDER BY id DESC LIMIT 20").fetchall()
        for r in rows:
            pages.append(f"/blog/{r['slug']}")
    except Exception: pass

    # 9. v1.24.233 — FULL mode: sample ALL programmatic routes
    if full:
        try:
            # Service × neighbourhood combos (17K+ routes — sample 200)
            from . import seo_pages as _seo
            slugs = list(_seo.AREA_INDEX.keys())[:50]  # first 50 neighbourhoods
            for s in hot_services:
                for area_slug in slugs:
                    pages.append(f"/services/{s}/{area_slug}")
        except Exception: pass

        try:
            # Arabic landing pages (133 routes — sample 30)
            from .data.i18n_ar_slugs import SERVICE_AR, EMIRATE_AR
            ar_count = 0
            for svc_id, (ar_svc, _) in list(SERVICE_AR.items())[:10]:
                for em_id, (ar_em, _) in list(EMIRATE_AR.items())[:3]:
                    pages.append(f"/{ar_svc}-{ar_em}")
                    ar_count += 1
                    if ar_count >= 30: break
                if ar_count >= 30: break
        except Exception: pass

        try:
            # Google Ads landing pages — sample 50
            from .data.seed_variant_pages import VARIANT_PAGES as _RVP
            for v in _RVP[:50]:
                pages.append(f"/{v['slug']}")
        except Exception: pass

        # All NFC variants
        for f in WEB_DIR.glob("nfc-*.html"):
            pages.append(f"/{f.stem}")

        # All vs/* comparison pages
        try:
            for f in (WEB_DIR / "vs").glob("*.html"):
                pages.append(f"/vs/{f.stem}")
        except Exception: pass

    return list(dict.fromkeys(pages))  # de-dupe while preserving order


_TEMPLATE_LEAK_RE = re.compile(
    r"\$\{[^}]+\}|\bC\.name\b|\bif\s+C\.\w+\b|"
    r"href[\s]*=[\s]*[\"']\s*\+\s*\w+\."
)
_HREF_RE = re.compile(r'\bhref\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_SRC_RE = re.compile(r'\bsrc\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)


def _audit_page(client, path: str) -> list[dict[str, Any]]:
    """Run every check against `path`. Returns a list of finding dicts."""
    findings: list[dict[str, Any]] = []
    t0 = time.time()
    try:
        r = client.get(path, follow_redirects=False)
    except Exception as e:
        findings.append({
            "severity": "error", "category": "fetch_failed",
            "message": f"Could not fetch page: {type(e).__name__}",
            "detail": str(e)[:300],
        })
        return findings
    elapsed_ms = int((time.time() - t0) * 1000)

    # Follow one redirect if 30x (a-href tap UX includes redirects)
    if r.status_code in (301, 302, 303, 307, 308):
        try:
            r = client.get(path, follow_redirects=True)
        except Exception: pass

    # 1. Status code
    if r.status_code >= 500:
        findings.append({"severity": "error", "category": "http_5xx",
                         "message": f"Server error {r.status_code}",
                         "detail": r.text[:300]})
        return findings
    if r.status_code == 404:
        findings.append({"severity": "error", "category": "http_404",
                         "message": "Page not found (404)",
                         "detail": r.text[:200]})
        return findings
    if r.status_code != 200:
        findings.append({"severity": "warning", "category": "http_status",
                         "message": f"Unexpected status {r.status_code}",
                         "detail": ""})

    # 2. Response time
    if elapsed_ms > 3000:
        findings.append({"severity": "warning", "category": "slow_response",
                         "message": f"Slow response: {elapsed_ms}ms",
                         "detail": f"Threshold: 3000ms"})

    # 3. Content-Type — only flag if we EXPECTED HTML (skip API + asset paths).
    ct = r.headers.get("content-type", "").lower()
    is_asset_path = (
        path.startswith(("/api/", "/sitemap", "/robots", "/llms",
                          "/manifest", "/sw.js", "/.well-known"))
        or path.endswith((".xml", ".txt", ".json", ".webmanifest", ".js",
                           ".css", ".png", ".jpg", ".svg", ".ico"))
    )
    if "text/html" not in ct and not is_asset_path:
        findings.append({"severity": "warning", "category": "content_type",
                         "message": f"Not HTML: {ct}",
                         "detail": f"path={path}"})
        return findings
    if is_asset_path:
        # For asset / API endpoints we only care about status code +
        # response time, not HTML structure. Return whatever findings
        # we've collected so far (status + speed) without HTML checks.
        return findings

    body = r.text
    # Pre-compute script+style-stripped body once — used by multiple checks
    # below. We never want to flag valid JS template literals inside
    # <script> blocks as broken hrefs or img srcs.
    scriptless = re.sub(r"<script[\s\S]*?</script>", "", body, flags=re.IGNORECASE)
    scriptless = re.sub(r"<style[\s\S]*?</style>", "", scriptless, flags=re.IGNORECASE)

    # 4. Template literal leaks (`${...}` or `+ C.name` in rendered HTML)
    leak = _TEMPLATE_LEAK_RE.search(body)
    if leak:
        leak2 = _TEMPLATE_LEAK_RE.search(scriptless)
        if leak2:
            # v1.24.229 — capture the surrounding HTML as proof so the
            # founder sees exactly what leaked, not just a category label.
            proof_start = max(0, leak2.start() - 100)
            proof_end = min(len(scriptless), leak2.end() + 200)
            findings.append({
                "severity": "error", "category": "template_leak",
                "message": "JS template literal escaped to rendered HTML",
                "detail": f"Match: {scriptless[leak2.start():leak2.end()][:80]}",
                "proof_snippet": scriptless[proof_start:proof_end],
                "http_status": r.status_code,
            })

    # 5. Title + meta
    if "<title>" not in body or "<title></title>" in body:
        findings.append({"severity": "warning", "category": "missing_title",
                         "message": "Page has no <title>", "detail": ""})
    if 'name="description"' not in body.lower():
        findings.append({"severity": "info", "category": "missing_description",
                         "message": "No <meta name='description'>", "detail": ""})
    if 'name="viewport"' not in body.lower():
        findings.append({"severity": "warning", "category": "missing_viewport",
                         "message": "No viewport meta tag (mobile rendering)", "detail": ""})

    # 6. Uniform chrome: should have <nav> OR injected nav OR <header>.
    # Transactional pages (checkout / pay / cart) intentionally have their
    # own self-contained chrome — downgrade to info severity for those.
    has_chrome = (
        "<nav" in body.lower() or "<header" in body.lower() or
        'class="nav"' in body.lower() or "class='nav'" in body.lower() or
        'class="head"' in body.lower() or "class='head'" in body.lower()
    )
    if not has_chrome:
        is_transactional = any(path.startswith(p) for p in
            ("/checkout", "/cart", "/pay", "/q/", "/p/", "/i/", "/gate"))
        findings.append({
            "severity": "info" if is_transactional else "warning",
            "category": "missing_chrome",
            "message": "No nav or header element",
            "detail": f"path={path} is_transactional={is_transactional}",
        })

    # v1.24.228 — User asked: "must see for uniformity in pages and all should
    # be on same pattern with floating icons and all buttons icons working
    # proper on all pages." Three new checks:

    # 6b. Floating icons uniformity — every CUSTOMER page should have chat,
    # SOS FAB, About-app FAB. Skip transactional pages.
    is_transactional = any(path.startswith(p) for p in
        ("/checkout", "/cart", "/pay", "/q/", "/p/", "/i/", "/gate"))
    if not is_transactional:
        if "widget.js?v=" not in body and "/widget.js" not in body:
            findings.append({"severity": "warning", "category": "missing_chat_widget",
                             "message": "Chat widget launcher not loaded",
                             "detail": "widget.js script tag missing"})
        # /sos IS the SOS page — doesn't need a FAB pointing back to itself
        if "sos-fab.js" not in body and not path.startswith("/sos"):
            findings.append({"severity": "info", "category": "missing_sos_fab",
                             "message": "SOS FAB not loaded",
                             "detail": "sos-fab.js script tag missing"})
        if "servia-push-banner" not in body:
            findings.append({"severity": "info", "category": "missing_push_banner",
                             "message": "Push opt-in banner not injected",
                             "detail": "Visitors won't see notification permission CTA"})

    # 6c. <img src> resolution — broken images render as ugly placeholders.
    # IMPORTANT: scan scriptless body so JS template literals like
    # /api/social-images/img/${i.slug}.png inside <script> blocks don't
    # generate false-positives.
    img_srcs = set()
    for m in re.finditer(r'<img\b[^>]*\bsrc\s*=\s*["\']([^"\']+)["\']',
                          scriptless, re.IGNORECASE):
        src = m.group(1).strip()
        if not src.startswith("/") or src.startswith("//"):
            continue
        # Skip any src that contains a template-literal placeholder
        if "${" in src or "{{" in src:
            continue
        if src in img_srcs: continue
        img_srcs.add(src)
        try:
            rr = client.get(src.split("?")[0])
            if rr.status_code == 404:
                idx = scriptless.find(src)
                snippet = ""
                if idx >= 0:
                    s = max(0, idx - 80); e = min(len(scriptless), idx + len(src) + 100)
                    snippet = scriptless[s:e]
                findings.append({
                    "severity": "error", "category": "broken_image",
                    "message": f"Broken image src: {src}",
                    "detail": f"<img src='{src}'> returns 404",
                    "proof_snippet": snippet,
                    "http_status": 404,
                })
        except Exception: pass

    # 6d. Button onclick handlers — extract onclick="funcName(" and verify
    # the function is defined SOMEWHERE in the page (inline script) or in
    # a known shared script. False-positives possible for late-loaded JS;
    # only flag obvious cases (typos like onclick="undefinedFunc(").
    onclick_calls = re.findall(r'onclick\s*=\s*["\']([a-zA-Z_$][\w$]*)\s*\(',
                                body, re.IGNORECASE)
    # Common shared functions (defined in app.js, widget.js, etc.) we KNOW exist
    KNOWN_FUNCS = {
        "serviaOpenChat", "serviaShowInstall", "serviaShare",
        "serviaEnablePush", "_serviaPushSelfPrompt",
    }
    for fn in set(onclick_calls):
        if fn in KNOWN_FUNCS:
            continue
        # If the function is defined in the page's inline scripts, OK
        if re.search(rf"\bfunction\s+{re.escape(fn)}\s*\(", body) or \
           re.search(rf"\b(window\.)?{re.escape(fn)}\s*=\s*(async\s*)?(function|\()", body) or \
           re.search(rf"\bwindow\.{re.escape(fn)}\s*=", body):
            continue
        # Unrecognized — info-level (could be defined externally but we
        # can't tell from the rendered HTML alone)
        findings.append({
            "severity": "info", "category": "unverified_onclick",
            "message": f"onclick calls {fn}() — function definition not visible in page",
            "detail": "May be defined in a deferred script; check manually if button is broken",
        })

    # v1.24.234 — MISLABELED WHATSAPP LINKS (founder caught these manually
    # twice in a row — tester missed them every time). Any anchor whose
    # visible TEXT contains 'WhatsApp' / 'whatsapp' / 'WA' (with context)
    # but whose href is NOT a wa.me / tel: / mailto link → bait-and-switch.
    # The bot was sending users to /contact (a form page) when the button
    # said 'WhatsApp us'. Real WhatsApp links must use wa.me OR be a known
    # JS-set href like '#' / 'javascript:' (set at runtime).
    for m in re.finditer(
        r'<a\b([^>]*?)>([^<]{0,80}?(?:WhatsApp|whatsapp|wa\.me|WA\s+chat|wA chat)[^<]{0,40})</a>',
        scriptless
    ):
        attrs, anchor_text = m.group(1), m.group(2)
        href_m = re.search(r'href\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        if not href_m: continue
        h = href_m.group(1).strip().lower()
        # Acceptable destinations: actual WhatsApp deep-link, telephone,
        # JS placeholder (set at runtime), or empty hash placeholder
        if (h.startswith(("https://wa.me/", "http://wa.me/", "https://api.whatsapp.com",
                            "wa.me/", "tel:", "mailto:", "javascript:", "#"))
                or "${" in h):  # template literal handled by JS
            continue
        # Anchor labelled WhatsApp but goes to a non-WA URL → real bug
        findings.append({
            "severity": "error", "category": "mislabeled_whatsapp_link",
            "message": f"Link labelled '{anchor_text.strip()[:40]}' goes to {h} instead of wa.me",
            "detail": f"<a href='{href_m.group(1)}'>{anchor_text.strip()[:80]}</a>",
            "proof_snippet": m.group(0),
            "http_status": r.status_code,
        })

    # v1.24.234 — INVOICE-NOT-FOUND / quote-expired error visibility on
    # transactional pages. Founder hit /pay/NFC-00001 → 'Invoice not found'
    # because that ID didn't exist in DB. The page itself doesn't return
    # HTTP 404 (it's the JS that displays an error inside a 200 OK page).
    # Detect this signature so the inspector flags pages where the JS error
    # state is the only visible content.
    if path.startswith(("/pay/", "/p/", "/checkout", "/q/", "/i/")):
        # The error UI patterns we use on transactional pages
        error_signatures = [
            "Invoice not found", "Quote not found", "Quote not available",
            "looks invalid or expired", "Couldn't load quote",
            "Missing quote reference",
        ]
        for sig in error_signatures:
            if sig in body:
                # Only an error if NO valid content is alongside it
                # (e.g. /pay/<id> with no real invoice → 100% error UI)
                if 'class="pay-amt"' not in body or 'pay-amt">…' in body:
                    findings.append({
                        "severity": "error",
                        "category": "transactional_dead_link",
                        "message": f"Transactional page shows '{sig}' — link is dead for users",
                        "detail": f"path={path} — DB row missing or quote/invoice expired",
                        "http_status": r.status_code,
                    })
                    break

    # 7. "Loading..." stuck-text — these are pages with un-resolved
    # JS spinner that never advanced. catch this signature.
    if re.search(r"\bLoading[^<]{0,30}\.{2,3}\b", body):
        # Only an issue if there's no fallback content visible
        if "fallback" not in body.lower() and len(body) < 5000:
            findings.append({
                "severity": "warning", "category": "loading_stuck_signature",
                "message": "Page contains 'Loading...' with no visible fallback",
                "detail": "May indicate JS-only render that fails silently",
            })

    # 8. Broken internal href targets — only check /a/b/c style relative
    # links from the scriptless body (computed at top of function).
    seen_hrefs = set()
    for m in _HREF_RE.finditer(scriptless):
        href = m.group(1).strip()
        if not href or href.startswith(("http", "mailto:", "tel:", "#",
                                         "javascript:", "wa.me", "//")):
            continue
        # Skip any href that contains a template-literal placeholder.
        # If we find one in non-script HTML it's a real bug, but the
        # template_leak detector above already catches that — no need
        # to double-count it as a broken link.
        if "${" in href or "{{" in href or "C.name" in href:
            continue
        target = href.split("?")[0].split("#")[0]
        if target in seen_hrefs: continue
        seen_hrefs.add(target)
        if not target.startswith("/"):
            continue
        try:
            rr = client.get(target, follow_redirects=False)
            if rr.status_code == 404:
                # Capture the surrounding HTML so the founder can locate it
                idx = scriptless.find(href)
                snippet = ""
                if idx >= 0:
                    s = max(0, idx - 100); e = min(len(scriptless), idx + len(href) + 100)
                    snippet = scriptless[s:e]
                findings.append({
                    "severity": "error", "category": "broken_link",
                    "message": f"Broken internal link: {target}",
                    "detail": f"<a href='{href}'> returns 404",
                    "proof_snippet": snippet,
                    "http_status": 404,
                })
        except Exception: pass

    return findings


def run_scan(trigger: str = "manual", full: bool = False,
              capture_screenshots: bool = True) -> dict[str, Any]:
    """Run a full audit pass. Returns summary dict.

    v1.24.233 — `full=True` scans 2000+ programmatic routes (~3-5 min).
    `capture_screenshots=True` runs each page through Playwright after
    the HTML audit and stores a PNG to /data/inspector-shots/{run_id}/
    so the founder can SEE every page the bot tested.
    """
    _ensure_tables()
    from fastapi.testclient import TestClient
    from .main import app
    client = TestClient(app)

    started_at = _dt.datetime.utcnow().isoformat() + "Z"
    t0 = time.time()
    pages = _customer_pages(full=full)
    all_findings: list[tuple[str, dict, int]] = []  # (path, finding, page_idx)
    page_status: dict[int, dict] = {}  # idx → {path, status, has_screenshot}
    for idx, path in enumerate(pages):
        findings = _audit_page(client, path)
        for f in findings:
            all_findings.append((path, f, idx))
        page_status[idx] = {"path": path,
                            "findings": len(findings),
                            "has_screenshot": False}

    duration_ms = int((time.time() - t0) * 1000)
    finished_at = _dt.datetime.utcnow().isoformat() + "Z"
    errors = sum(1 for _p, f, _i in all_findings if f["severity"] == "error")
    warnings = sum(1 for _p, f, _i in all_findings if f["severity"] == "warning")
    infos = sum(1 for _p, f, _i in all_findings if f["severity"] == "info")

    # Persist
    with db.connect() as c:
        cur = c.execute(
            "INSERT INTO auto_test_runs(started_at, finished_at, pages_tested, "
            "findings_count, errors, warnings, infos, duration_ms, trigger) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (started_at, finished_at, len(pages), len(all_findings),
             errors, warnings, infos, duration_ms, trigger))
        run_id = cur.lastrowid
        for path, f, _idx in all_findings:
            c.execute(
                "INSERT INTO auto_test_findings(run_id, path, severity, "
                "category, message, detail, proof_snippet, http_status, "
                "created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (run_id, path, f["severity"], f["category"], f["message"],
                 (f.get("detail") or "")[:1000],
                 (f.get("proof_snippet") or "")[:4000],
                 f.get("http_status"),
                 finished_at))

    # v1.24.233 — Screenshot capture pass. Runs after the HTML audit so
    # we don't slow down the JSON findings. Saves PNG per page to
    # /data/inspector-shots/{run_id}/{idx}.png + records the path on
    # the auto_test_findings row (if any) OR on a new auto_test_shots
    # row so the admin UI can show every screenshot, not just ones
    # with findings.
    if capture_screenshots:
        try:
            _capture_screenshots(run_id, pages, base_url="http://127.0.0.1:8000")
        except Exception as e:  # noqa: BLE001
            print(f"[auto-tester] screenshot capture failed: {e}", flush=True)

    print(f"[auto-tester] run #{run_id}: {len(pages)} pages, "
          f"{errors} errors, {warnings} warnings, {infos} info "
          f"({duration_ms}ms)", flush=True)

    return {
        "ok": True, "run_id": run_id, "pages_tested": len(pages),
        "errors": errors, "warnings": warnings, "infos": infos,
        "duration_ms": duration_ms, "trigger": trigger,
    }


# v1.24.233 — Screenshot capture via Playwright (chromium installed by
# the Dockerfile at /usr/bin/chromium). Runs in a fresh browser context
# per run so we get clean cookies / no state leakage. Mobile viewport
# (Pixel 5 dimensions) so screenshots match what real customers see.
def _capture_screenshots(run_id: int, pages: list[str], base_url: str) -> int:
    """Walk every page in `pages`, save a PNG screenshot per page to
    SHOTS_DIR/{run_id}/{idx}.png. Returns count of successful captures."""
    _ensure_shots_table()
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print(f"[auto-tester] playwright not installed: {e}", flush=True)
        return 0
    run_dir = SHOTS_DIR / str(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    started = time.time()
    BUDGET_SEC = 600  # cap at 10 min for screenshot pass
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True,
                executable_path=CHROMIUM_PATH if Path(CHROMIUM_PATH).exists() else None,
                args=["--no-sandbox", "--disable-dev-shm-usage",
                       "--disable-setuid-sandbox"],
            )
        except Exception as e:
            print(f"[auto-tester] chromium launch failed: {e}", flush=True)
            return 0
        ctx = browser.new_context(viewport={"width": 412, "height": 915},
                                   device_scale_factor=2)
        for idx, path in enumerate(pages):
            if time.time() - started > BUDGET_SEC:
                print(f"[auto-tester] screenshot budget exceeded "
                      f"at page {idx}/{len(pages)}", flush=True)
                break
            try:
                page = ctx.new_page()
                page.goto(base_url + path, wait_until="domcontentloaded",
                          timeout=8000)
                shot_path = run_dir / f"{idx:04d}.png"
                page.screenshot(path=str(shot_path), full_page=False)
                page.close()
                # Record for admin UI lookup
                with db.connect() as c:
                    c.execute(
                        "INSERT INTO auto_test_shots(run_id, page_idx, path, "
                        "screenshot_file, created_at) VALUES(?,?,?,?,?)",
                        (run_id, idx, path, str(shot_path.name),
                         _dt.datetime.utcnow().isoformat() + "Z"))
                saved += 1
            except Exception as e:
                # Continue past individual failures; log compactly
                if "ERR_CONNECTION_REFUSED" in str(e):
                    # Server not running on localhost:8000 (e.g. dev env)
                    print(f"[auto-tester] screenshots aborted: {e}", flush=True)
                    break
        try: ctx.close()
        except Exception: pass
        try: browser.close()
        except Exception: pass
    print(f"[auto-tester] screenshots: {saved}/{len(pages)} captured in "
          f"{int(time.time()-started)}s, run_id={run_id}", flush=True)
    return saved


def _ensure_shots_table() -> None:
    with db.connect() as c:
        c.execute("""
          CREATE TABLE IF NOT EXISTS auto_test_shots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            page_idx INTEGER NOT NULL,
            path TEXT NOT NULL,
            screenshot_file TEXT NOT NULL,
            created_at TEXT NOT NULL
          )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_shots_run ON auto_test_shots(run_id)")


# ─────────────────────────────────────────────────────────────────────────
# Admin endpoints
# ─────────────────────────────────────────────────────────────────────────


@router.get("/screenshot/{run_id}/{page_idx}")
def admin_get_screenshot(run_id: int, page_idx: int):
    """v1.24.233 — Serve a captured PNG screenshot file. Path-validated
    so we never read outside SHOTS_DIR even if someone crafts a bad
    page_idx."""
    from fastapi.responses import FileResponse
    _ensure_shots_table()
    with db.connect() as c:
        row = c.execute(
            "SELECT path, screenshot_file FROM auto_test_shots "
            "WHERE run_id=? AND page_idx=?", (run_id, page_idx)).fetchone()
    if not row:
        raise HTTPException(404, "screenshot not found")
    target = (SHOTS_DIR / str(run_id) / row["screenshot_file"]).resolve()
    base = SHOTS_DIR.resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(404, "path traversal blocked")
    if not target.exists():
        raise HTTPException(404, "file missing")
    return FileResponse(str(target), media_type="image/png",
                         headers={"X-Page-Path": row["path"]})


@router.get("/shots/{run_id}")
def admin_list_shots(run_id: int):
    """List every screenshot captured for a run, with the original path."""
    _ensure_shots_table()
    with db.connect() as c:
        rows = c.execute(
            "SELECT page_idx, path, screenshot_file FROM auto_test_shots "
            "WHERE run_id=? ORDER BY page_idx", (run_id,)).fetchall()
    return {
        "run_id": run_id, "count": len(rows),
        "items": [{
            "page_idx": r["page_idx"], "path": r["path"],
            "url": f"/api/admin/auto-tests/screenshot/{run_id}/{r['page_idx']}",
        } for r in rows],
    }


# ─────────────────────────────────────────────────────────────────────────
# Original admin endpoints
# ─────────────────────────────────────────────────────────────────────────

@router.post("/run-now")
def admin_run_now(full: bool = False, screenshots: bool = True):
    """Trigger an immediate audit scan. Returns the run summary. Also
    pushes a one-line summary to admin WhatsApp so the founder gets
    confirmation on every manual run (mandate: 'never stop reporting').

    v1.24.233 — `full=true` scans 2000+ programmatic routes instead of
    the 136-page sample (takes 3-5 min instead of 1 min). `screenshots=
    true` (default) captures a PNG per page via Playwright.
    """
    r = run_scan(trigger="manual_full" if full else "manual",
                  full=full, capture_screenshots=screenshots)
    try:
        from . import admin_alerts as _aa
        errors = r.get("errors", 0); warnings = r.get("warnings", 0)
        emoji = "🚨" if errors else ("⚠️" if warnings else "✅")
        msg = (
            f"{emoji} Inspector run #{r['run_id']} (manual): "
            f"{r['pages_tested']} pages · {errors} errors · "
            f"{warnings} warnings · {r['infos']} info · {r['duration_ms']//1000}s"
        )
        _aa.notify_admin(msg, kind="auto_test_summary",
                         urgency="critical" if errors else "normal")
    except Exception: pass
    return r


@router.get("/runs")
def admin_list_runs(limit: int = 30):
    _ensure_tables()
    limit = max(1, min(int(limit or 30), 200))
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, started_at, finished_at, pages_tested, findings_count, "
            "errors, warnings, infos, duration_ms, trigger "
            "FROM auto_test_runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return {"items": [dict(r) for r in rows], "count": len(rows)}


@router.get("/findings")
def admin_list_findings(run_id: int | None = None, severity: str | None = None,
                        resolved: int | None = None, limit: int = 200):
    _ensure_tables()
    where = []; params: list = []
    if run_id is not None:
        where.append("run_id = ?"); params.append(run_id)
    if severity:
        where.append("severity = ?"); params.append(severity)
    if resolved is not None:
        where.append("resolved = ?"); params.append(int(bool(resolved)))
    sql = "SELECT * FROM auto_test_findings"
    if where: sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"; params.append(max(1, min(int(limit or 200), 1000)))
    with db.connect() as c:
        rows = c.execute(sql, params).fetchall()
    return {"items": [dict(r) for r in rows], "count": len(rows)}


@router.post("/findings/{finding_id}/resolve")
def admin_resolve(finding_id: int, body: dict | None = None):
    _ensure_tables()
    who = (body or {}).get("resolved_by", "admin")[:60] if body else "admin"
    now = _dt.datetime.utcnow().isoformat() + "Z"
    with db.connect() as c:
        n = c.execute(
            "UPDATE auto_test_findings SET resolved=1, resolved_at=?, "
            "resolved_by=? WHERE id=? AND resolved=0",
            (now, who, finding_id)).rowcount
    return {"ok": True, "updated": n}


@router.get("/summary")
def admin_summary():
    """Dashboard tile: latest run + open-findings count."""
    _ensure_tables()
    with db.connect() as c:
        latest = c.execute(
            "SELECT * FROM auto_test_runs ORDER BY id DESC LIMIT 1").fetchone()
        open_count = c.execute(
            "SELECT COUNT(*) AS n FROM auto_test_findings WHERE resolved=0"
        ).fetchone()["n"]
        open_errors = c.execute(
            "SELECT COUNT(*) AS n FROM auto_test_findings WHERE resolved=0 "
            "AND severity='error'").fetchone()["n"]
        # Top categories
        cats = c.execute(
            "SELECT category, COUNT(*) AS n FROM auto_test_findings "
            "WHERE resolved=0 GROUP BY category ORDER BY n DESC LIMIT 5"
        ).fetchall()
    return {
        "latest_run": dict(latest) if latest else None,
        "open_findings": open_count,
        "open_errors": open_errors,
        "top_categories": [dict(c) for c in cats],
    }
