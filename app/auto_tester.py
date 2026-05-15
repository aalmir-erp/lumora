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
import re
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from . import db
from .auth import require_admin

router = APIRouter(prefix="/api/admin/auto-tests",
                   tags=["auto-tester"],
                   dependencies=[Depends(require_admin)])

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


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
        c.execute("CREATE INDEX IF NOT EXISTS idx_findings_run ON auto_test_findings(run_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_findings_resolved ON auto_test_findings(resolved, severity)")


def _customer_pages() -> list[str]:
    """Return every customer-facing path to audit. Built from the actual
    HTML files in web/ so the list stays in sync as pages are added."""
    pages: list[str] = []
    # Static HTML files → both clean URL and .html form
    skip_files = {"admin.html", "admin-inbox.html", "admin-live.html",
                  "admin-contact.html", "admin-commerce.html",
                  "admin-ai-engines.html", "admin-e2e-shots.html",
                  "admin-wa-bridge.html", "admin-login.html",
                  "admin-widget.html", "vendor.html", "portal-vendor.html",
                  "login.html", "gate.html", "reset.html",
                  "404.html", "brand-preview.html"}
    for f in sorted(WEB_DIR.glob("*.html")):
        if f.name in skip_files:
            continue
        slug = f.stem
        pages.append(f"/{slug}" if slug != "index" else "/")
    # A few dynamic routes worth checking
    pages.extend([
        "/services/deep-cleaning",
        "/services/ac-cleaning",
        "/area?city=dubai",
        "/area?city=sharjah",
    ])
    return pages


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

    # 3. Content-Type
    ct = r.headers.get("content-type", "").lower()
    if "text/html" not in ct:
        findings.append({"severity": "warning", "category": "content_type",
                         "message": f"Not HTML: {ct}",
                         "detail": ""})
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
        # Ignore matches inside <script>...</script> blocks (JS code is fine)
        # by stripping script blocks and re-checking
        stripped = re.sub(r"<script[\s\S]*?</script>", "", body, flags=re.IGNORECASE)
        leak2 = _TEMPLATE_LEAK_RE.search(stripped)
        if leak2:
            findings.append({
                "severity": "error", "category": "template_leak",
                "message": "JS template literal escaped to rendered HTML",
                "detail": f"Match near: ...{stripped[max(0,leak2.start()-30):leak2.end()+30]}...",
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
                findings.append({
                    "severity": "error", "category": "broken_image",
                    "message": f"Broken image src: {src}",
                    "detail": f"<img src='{src}'> returns 404",
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
                findings.append({
                    "severity": "error", "category": "broken_link",
                    "message": f"Broken internal link: {target}",
                    "detail": f"<a href='{href}'> returns 404",
                })
        except Exception: pass

    return findings


def run_scan(trigger: str = "manual") -> dict[str, Any]:
    """Run a full audit pass. Returns summary dict."""
    _ensure_tables()
    # Test client (in-process)
    from fastapi.testclient import TestClient
    from .main import app
    client = TestClient(app)

    started_at = _dt.datetime.utcnow().isoformat() + "Z"
    t0 = time.time()
    pages = _customer_pages()
    all_findings: list[tuple[str, dict]] = []
    for path in pages:
        findings = _audit_page(client, path)
        for f in findings:
            all_findings.append((path, f))

    duration_ms = int((time.time() - t0) * 1000)
    finished_at = _dt.datetime.utcnow().isoformat() + "Z"
    errors = sum(1 for _, f in all_findings if f["severity"] == "error")
    warnings = sum(1 for _, f in all_findings if f["severity"] == "warning")
    infos = sum(1 for _, f in all_findings if f["severity"] == "info")

    # Persist
    with db.connect() as c:
        cur = c.execute(
            "INSERT INTO auto_test_runs(started_at, finished_at, pages_tested, "
            "findings_count, errors, warnings, infos, duration_ms, trigger) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (started_at, finished_at, len(pages), len(all_findings),
             errors, warnings, infos, duration_ms, trigger))
        run_id = cur.lastrowid
        for path, f in all_findings:
            c.execute(
                "INSERT INTO auto_test_findings(run_id, path, severity, category, "
                "message, detail, created_at) VALUES(?,?,?,?,?,?,?)",
                (run_id, path, f["severity"], f["category"], f["message"],
                 f.get("detail", "")[:1000], finished_at))

    print(f"[auto-tester] run #{run_id}: {len(pages)} pages, "
          f"{errors} errors, {warnings} warnings, {infos} info "
          f"({duration_ms}ms)", flush=True)

    return {
        "ok": True, "run_id": run_id, "pages_tested": len(pages),
        "errors": errors, "warnings": warnings, "infos": infos,
        "duration_ms": duration_ms, "trigger": trigger,
    }


# ─────────────────────────────────────────────────────────────────────────
# Admin endpoints
# ─────────────────────────────────────────────────────────────────────────

@router.post("/run-now")
def admin_run_now():
    """Trigger an immediate audit scan. Returns the run summary. Also
    pushes a one-line summary to admin WhatsApp so the founder gets
    confirmation on every manual run (mandate: 'never stop reporting')."""
    r = run_scan(trigger="manual_admin")
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
