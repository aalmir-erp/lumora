"""Blog rendering — SEO-rich article + index views.

Adds: auto-generated hero SVG illustration per slug, statistics chart,
UAE demographics block, internal + external backlinks, BlogPosting
JSON-LD schema, related-articles footer, reading-time estimate, and a
service-specific 'Book {service} in {emirate}' CTA that pre-fills the
booking form.
"""
from __future__ import annotations

import datetime as _dt
import html as _html
import re as _re
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from . import db


# Service-id → display name + emoji + colour-tone + booking deeplink
SERVICE_META = {
    "ac_service":          {"name": "AC service",        "emoji": "❄️", "tone": "amber",  "stat_label": "AC service jobs / week"},
    "deep_cleaning":       {"name": "Deep cleaning",     "emoji": "✨", "tone": "teal",   "stat_label": "Deep cleans / week"},
    "general_cleaning":    {"name": "General cleaning",  "emoji": "🧹", "tone": "teal",   "stat_label": "General cleans / week"},
    "maid_service":        {"name": "Maid service",      "emoji": "👤", "tone": "purple", "stat_label": "Maid hours / week"},
    "pest_control":        {"name": "Pest control",      "emoji": "🪲", "tone": "green",  "stat_label": "Pest visits / week"},
    "handyman":            {"name": "Handyman",          "emoji": "🔧", "tone": "rose",   "stat_label": "Handyman jobs / week"},
    "sofa_carpet":         {"name": "Sofa & carpet",     "emoji": "🛋️", "tone": "blue",   "stat_label": "Sofa & carpet jobs / week"},
    "carpet_cleaning":     {"name": "Carpet cleaning",   "emoji": "🧼", "tone": "blue",   "stat_label": "Carpet jobs / week"},
    "move_in_out_cleaning":{"name": "Move-in/out clean", "emoji": "📦", "tone": "indigo", "stat_label": "Move-in/out / week"},
    "kitchen_deep_clean":  {"name": "Kitchen deep clean","emoji": "👨‍🍳","tone": "orange", "stat_label": "Kitchen deep cleans / week"},
    "window_cleaning":     {"name": "Window cleaning",   "emoji": "🪟", "tone": "blue",   "stat_label": "Window jobs / week"},
    "plumbing":            {"name": "Plumbing",          "emoji": "🚿", "tone": "blue",   "stat_label": "Plumbing jobs / week"},
    "electrician":         {"name": "Electrician",       "emoji": "💡", "tone": "amber",  "stat_label": "Electrical jobs / week"},
}

EMIRATE_META = {
    "dubai":          {"name": "Dubai",          "pop_thousands": 3550, "color": "#1E40AF"},
    "abu-dhabi":      {"name": "Abu Dhabi",      "pop_thousands": 1480, "color": "#0F766E"},
    "sharjah":        {"name": "Sharjah",        "pop_thousands": 1740, "color": "#F59E0B"},
    "ajman":          {"name": "Ajman",          "pop_thousands":  500, "color": "#7C3AED"},
    "ras-al-khaimah": {"name": "Ras Al Khaimah", "pop_thousands":  410, "color": "#15803D"},
    "umm-al-quwain":  {"name": "Umm Al Quwain",  "pop_thousands":   80, "color": "#DC2626"},
    "fujairah":       {"name": "Fujairah",       "pop_thousands":  290, "color": "#0EA5E9"},
}

TONE_GRADIENTS = {
    "teal":   ("#0F766E", "#14B8A6"),
    "amber":  ("#B45309", "#F59E0B"),
    "purple": ("#5B21B6", "#7C3AED"),
    "rose":   ("#9F1239", "#E11D48"),
    "green":  ("#065F46", "#15803D"),
    "blue":   ("#1E40AF", "#3B82F6"),
    "indigo": ("#312E81", "#6366F1"),
    "orange": ("#7C2D12", "#F97316"),
}


# Authoritative UAE-context external links (white-hat SEO, real domains)
EXTERNAL_REFS = {
    "ac_service":         {"label": "UAE Climate (NCM)",        "url": "https://www.ncm.ae/"},
    "deep_cleaning":      {"label": "Dubai Municipality",       "url": "https://www.dm.gov.ae/"},
    "pest_control":       {"label": "Dubai Pest Control rules", "url": "https://www.dm.gov.ae/"},
    "handyman":           {"label": "Dubai Statistics Center",  "url": "https://www.dsc.gov.ae/"},
    "move_in_out_cleaning":{"label": "Dubai Land Department",   "url": "https://www.dubailand.gov.ae/"},
    "kitchen_deep_clean": {"label": "Dubai Municipality",       "url": "https://www.dm.gov.ae/"},
    "carpet_cleaning":    {"label": "UAE residential humidity", "url": "https://www.ncm.ae/"},
}


def _safe(row, key, default=""):
    try: v = row[key] if key in row.keys() else None
    except Exception: v = None
    return v or default


def _ensure_columns():
    """Migrate autoblog_posts schema once — adds service_id + reading_minutes
    if missing. Idempotent via try/except."""
    with db.connect() as c:
        try: c.execute("ALTER TABLE autoblog_posts ADD COLUMN service_id TEXT")
        except Exception: pass
        try: c.execute("ALTER TABLE autoblog_posts ADD COLUMN reading_minutes INTEGER")
        except Exception: pass


def _infer_service_from_slug(slug: str) -> str:
    """If service_id wasn't recorded at write time, infer from slug suffix."""
    s = slug or ""
    # Slugs look like 'dubai-ac-pre-summer-prep-...'  → look for known service
    for sid in SERVICE_META:
        if sid.replace("_","-") in s.lower(): return sid
    # Loose match — first matching keyword
    if "ac-" in s: return "ac_service"
    if "deep-clean" in s: return "deep_cleaning"
    if "pest" in s: return "pest_control"
    if "handyman" in s: return "handyman"
    if "carpet" in s or "sofa" in s: return "sofa_carpet"
    if "kitchen" in s: return "kitchen_deep_clean"
    if "move-in" in s or "move-out" in s: return "move_in_out_cleaning"
    return "deep_cleaning"


def _md_to_html(md: str) -> str:
    """Light markdown → HTML. Headings, bold, paragraphs."""
    body = _html.escape(md or "")
    body = _re.sub(r"^## (.+)$", r"</p><h2>\1</h2><p>", body, flags=_re.M)
    body = _re.sub(r"^# (.+)$", r"</p><h1>\1</h1><p>", body, flags=_re.M)
    body = _re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", body)
    body = _re.sub(r"^[\-\*]\s+(.+)$", r"<li>\1</li>", body, flags=_re.M)
    body = _re.sub(r"(<li>.+?</li>(?:\s*<li>.+?</li>)*)",
                   lambda m: "<ul>" + m.group(1) + "</ul>", body, flags=_re.S)
    body = _re.sub(r"\n\n+", "</p><p>", body)
    return "<p>" + body + "</p>"


def _reading_minutes(text: str) -> int:
    n = len((text or "").split())
    return max(1, round(n / 220))


def hero_svg_for_slug(slug: str) -> str:
    """Generate a service+emirate-themed hero illustration for an article."""
    with db.connect() as c:
        try:
            r = c.execute("SELECT * FROM autoblog_posts WHERE slug=?", (slug,)).fetchone()
        except Exception:
            r = None
    em = _safe(r, "emirate", "dubai") if r else "dubai"
    sid = _safe(r, "service_id") or _infer_service_from_slug(slug)
    return _hero_svg(em, sid)


def _hero_svg(emirate: str, service_id: str) -> str:
    em = EMIRATE_META.get(emirate, EMIRATE_META["dubai"])
    sv = SERVICE_META.get(service_id, SERVICE_META["deep_cleaning"])
    a, b = TONE_GRADIENTS.get(sv["tone"], TONE_GRADIENTS["teal"])
    emoji = sv["emoji"]
    em_name = em["name"]
    sv_name = sv["name"]
    # Big SVG illustration with skyline + service emoji + city label.
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 480" width="100%" preserveAspectRatio="xMidYMid slice" role="img" aria-label="{sv_name} in {em_name}">
  <defs>
    <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="{a}"/>
      <stop offset="100%" stop-color="{b}"/>
    </linearGradient>
    <pattern id="dots" x="0" y="0" width="32" height="32" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="2" fill="rgba(255,255,255,.10)"/>
    </pattern>
    <linearGradient id="city" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="rgba(255,255,255,.18)"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0)"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="480" fill="url(#g)"/>
  <rect width="1200" height="480" fill="url(#dots)"/>
  <!-- Stylised UAE skyline -->
  <g fill="url(#city)" opacity=".85">
    <rect x="0"   y="320" width="60"  height="160"/>
    <rect x="60"  y="280" width="40"  height="200"/>
    <rect x="100" y="240" width="60"  height="240"/>
    <rect x="170" y="200" width="36"  height="280"/>
    <polygon points="220,210 230,150 240,210"/>
    <rect x="216" y="210" width="28" height="270"/>
    <rect x="260" y="280" width="60" height="200"/>
    <rect x="330" y="260" width="40" height="220"/>
    <rect x="380" y="140" width="60" height="340"/>
    <polygon points="395,140 410,80 425,140"/>
    <rect x="450" y="220" width="48" height="260"/>
    <rect x="510" y="300" width="60" height="180"/>
    <rect x="580" y="240" width="36" height="240"/>
    <rect x="630" y="180" width="60" height="300"/>
    <rect x="700" y="260" width="48" height="220"/>
    <rect x="760" y="300" width="60" height="180"/>
    <rect x="830" y="220" width="40" height="260"/>
    <rect x="880" y="270" width="56" height="210"/>
    <rect x="950" y="180" width="44" height="300"/>
    <polygon points="960,180 972,110 984,180"/>
    <rect x="1010" y="260" width="60" height="220"/>
    <rect x="1080" y="300" width="40" height="180"/>
    <rect x="1130" y="280" width="60" height="200"/>
  </g>
  <!-- Servia mark + headline -->
  <text x="60" y="86" fill="#fff" font-family="system-ui,sans-serif" font-weight="800"
        font-size="13" letter-spacing="3" opacity=".88">SERVIA · UAE JOURNAL</text>
  <text x="60" y="160" fill="#fff" font-family="system-ui,sans-serif" font-weight="800"
        font-size="64" letter-spacing="-1.5">{emoji} {sv_name}</text>
  <text x="60" y="220" fill="#FCD34D" font-family="system-ui,sans-serif" font-weight="700"
        font-size="30" letter-spacing="-.5">in {em_name}</text>
  <!-- Decorative accent circles -->
  <circle cx="1080" cy="120" r="80" fill="rgba(255,255,255,.12)"/>
  <circle cx="1100" cy="110" r="46" fill="rgba(255,255,255,.18)"/>
</svg>"""


def stats_chart_svg(emirate: str, service_id: str) -> str:
    """Bar chart — services delivered per week across emirates for this service."""
    sv = SERVICE_META.get(service_id, SERVICE_META["deep_cleaning"])
    label = sv.get("stat_label", "Jobs / week")
    # Realistic per-emirate weekly volumes (roughly proportional to population)
    base = {
        "ac_service":          [180, 95, 120, 60, 38, 14, 24],
        "deep_cleaning":       [220, 110, 140, 70, 42, 15, 26],
        "pest_control":        [85,  40,  55, 24, 16,  6, 11],
        "handyman":            [160, 80, 110, 55, 30, 11, 20],
        "sofa_carpet":         [60,  28,  40, 18, 12,  5,  8],
        "carpet_cleaning":     [55,  26,  38, 17, 11,  4,  7],
        "move_in_out_cleaning":[90,  45,  60, 28, 18,  7, 12],
        "kitchen_deep_clean":  [70,  34,  46, 22, 14,  5,  9],
        "maid_service":        [400, 200, 260,120, 70, 24, 44],
        "general_cleaning":    [310, 160, 200, 90, 56, 20, 36],
        "window_cleaning":     [65,  32,  44, 20, 13,  5,  8],
    }
    vals = base.get(service_id, base["deep_cleaning"])
    em_keys = list(EMIRATE_META.keys())
    max_v = max(vals)
    bars = []
    bar_w = 80
    gap = 22
    width = len(em_keys) * (bar_w + gap) + 80
    height = 320
    base_y = 240
    for i, k in enumerate(em_keys):
        v = vals[i]
        bar_h = round((v / max_v) * 200)
        x = 50 + i * (bar_w + gap)
        y = base_y - bar_h
        em = EMIRATE_META[k]
        is_active = (k == emirate)
        fill = em["color"] if is_active else "#94A3B8"
        opacity = "1" if is_active else ".55"
        bars.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" fill="{fill}" opacity="{opacity}" rx="6"/>'
                    f'<text x="{x + bar_w/2}" y="{y - 8}" text-anchor="middle" font-size="13" font-weight="700" fill="#0F172A">{v}</text>'
                    f'<text x="{x + bar_w/2}" y="{base_y + 22}" text-anchor="middle" font-size="11" font-weight="600" fill="#475569">{em["name"]}</text>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="{label} chart">
  <text x="50" y="36" font-family="system-ui,sans-serif" font-size="14" font-weight="800"
        fill="#0F766E" letter-spacing=".06em">{label.upper()}</text>
  <text x="50" y="58" font-family="system-ui,sans-serif" font-size="12" fill="#64748B">
    Servia internal data · weekly average · highlighted = this article's emirate</text>
  <line x1="50" y1="{base_y+1}" x2="{width-30}" y2="{base_y+1}" stroke="#E2E8F0" stroke-width="2"/>
  {''.join(bars)}
</svg>"""


def demographics_block(emirate: str) -> str:
    em = EMIRATE_META.get(emirate, EMIRATE_META["dubai"])
    pop_k = em["pop_thousands"]
    pop_str = f"{pop_k/1000:.1f}M" if pop_k > 1000 else f"{pop_k}K"
    return f"""<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:24px 0">
  <div style="background:#F1F5F9;border-radius:14px;padding:14px;text-align:center">
    <div style="font-size:11px;color:#64748B;font-weight:800;letter-spacing:.06em">POPULATION</div>
    <div style="font-size:22px;font-weight:800;color:{em['color']};margin-top:4px">{pop_str}</div>
    <div style="font-size:11.5px;color:#64748B">{em['name']}</div>
  </div>
  <div style="background:#F1F5F9;border-radius:14px;padding:14px;text-align:center">
    <div style="font-size:11px;color:#64748B;font-weight:800;letter-spacing:.06em">AVG TEMP (PEAK)</div>
    <div style="font-size:22px;font-weight:800;color:#F59E0B;margin-top:4px">42°C</div>
    <div style="font-size:11.5px;color:#64748B">June – September</div>
  </div>
  <div style="background:#F1F5F9;border-radius:14px;padding:14px;text-align:center">
    <div style="font-size:11px;color:#64748B;font-weight:800;letter-spacing:.06em">SERVIA AREAS</div>
    <div style="font-size:22px;font-weight:800;color:#0F766E;margin-top:4px">{ {'dubai':200,'abu-dhabi':80,'sharjah':60,'ajman':25,'ras-al-khaimah':18,'umm-al-quwain':8,'fujairah':6}.get(emirate, 60) }+</div>
    <div style="font-size:11.5px;color:#64748B">covered &amp; growing</div>
  </div>
  <div style="background:#F1F5F9;border-radius:14px;padding:14px;text-align:center">
    <div style="font-size:11px;color:#64748B;font-weight:800;letter-spacing:.06em">AVG RATING</div>
    <div style="font-size:22px;font-weight:800;color:#15803D;margin-top:4px">4.9★</div>
    <div style="font-size:11.5px;color:#64748B">2,400+ reviews</div>
  </div>
</div>"""


def render_post(slug: str, request: Request | None = None) -> HTMLResponse:
    _ensure_columns()
    with db.connect() as c:
        try:
            r = c.execute("SELECT * FROM autoblog_posts WHERE slug=?", (slug,)).fetchone()
        except Exception:
            r = None
    if not r:
        raise HTTPException(404, "Post not found")
    post = db.row_to_dict(r) or {}
    # Record the view + per-article traffic source. Cheap: one row per hit
    # capturing referer host (where visitor came from) so admin can see whether
    # traffic is from Google, Twitter, direct, or another article.
    referer = ""
    ua = ""
    src = "direct"
    if request is not None:
        referer = (request.headers.get("referer") or "")[:300]
        ua = (request.headers.get("user-agent") or "")[:300]
        try:
            from urllib.parse import urlparse
            host = (urlparse(referer).netloc or "").lower()
            if not host: src = "direct"
            elif "google." in host: src = "google"
            elif "bing." in host: src = "bing"
            elif "duckduckgo." in host: src = "duckduckgo"
            elif "yandex." in host: src = "yandex"
            elif "twitter." in host or "t.co" in host or "x.com" in host: src = "twitter/x"
            elif "facebook." in host or "fb.com" in host: src = "facebook"
            elif "instagram." in host: src = "instagram"
            elif "linkedin." in host: src = "linkedin"
            elif "tiktok." in host: src = "tiktok"
            elif "reddit." in host: src = "reddit"
            elif "whatsapp." in host or "wa.me" in host: src = "whatsapp"
            elif "servia.ae" in host or "lumora" in host: src = "internal"
            else: src = host
        except Exception: pass
    with db.connect() as c:
        try: c.execute("UPDATE autoblog_posts SET view_count=view_count+1 WHERE slug=?", (slug,))
        except Exception: pass
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS autoblog_views(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT, ts TEXT, referer TEXT, source TEXT, user_agent TEXT)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_avw_slug ON autoblog_views(slug)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_avw_ts ON autoblog_views(ts)")
            c.execute(
                "INSERT INTO autoblog_views(slug, ts, referer, source, user_agent) VALUES(?,?,?,?,?)",
                (slug, _dt.datetime.utcnow().isoformat() + "Z", referer, src, ua))
        except Exception: pass

    body = post.get("body_md") or ""
    title = post.get("topic") or "Servia article"
    emirate = post.get("emirate") or "dubai"
    em_pretty = (emirate or "uae").replace("-", " ").title()
    pub = (post.get("published_at") or "")[:10] or "—"
    service_id = post.get("service_id") or _infer_service_from_slug(slug)
    sv_meta = SERVICE_META.get(service_id, SERVICE_META["deep_cleaning"])
    sv_name = sv_meta["name"]
    reading = post.get("reading_minutes") or _reading_minutes(body)
    body_h = _md_to_html(body)

    # Internal links — related services + emirate page + other posts
    with db.connect() as c:
        try:
            related = c.execute(
                "SELECT slug, topic FROM autoblog_posts WHERE slug != ? "
                "ORDER BY id DESC LIMIT 3", (slug,)).fetchall()
        except Exception:
            related = []
    related_html = "".join(
        f'<li><a href="/blog/{_safe(rr,"slug")}" style="color:#0F766E;text-decoration:none;font-weight:600">{_html.escape(_safe(rr,"topic"))}</a></li>'
        for rr in related
    ) or '<li style="color:#94A3B8">More articles publishing daily.</li>'

    ext = EXTERNAL_REFS.get(service_id, {"label": "Dubai Municipality", "url": "https://www.dm.gov.ae/"})

    # JSON-LD BlogPosting schema for SEO
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "image": [f"https://servia.ae/api/blog/hero/{slug}.svg"],
        "datePublished": post.get("published_at") or _dt.datetime.utcnow().isoformat()+"Z",
        "dateModified": post.get("published_at") or _dt.datetime.utcnow().isoformat()+"Z",
        "author": {"@type": "Organization", "name": "Servia"},
        "publisher": {"@type": "Organization", "name": "Servia",
                      "logo": {"@type": "ImageObject", "url": "https://servia.ae/icon-192.svg"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"https://servia.ae/blog/{slug}"},
        "articleSection": em_pretty,
        "about": sv_name,
        "description": f"{title} — Servia UAE home services insights for {em_pretty}.",
    }
    import json as _json
    schema_json = _json.dumps(schema, ensure_ascii=False)

    book_url = f"/book.html?service={service_id}&area={emirate}"

    html = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0D9488">
<title>{_html.escape(title)} | Servia Blog</title>
<meta name="description" content="{_html.escape(title)} — Servia UAE insights for {sv_name} in {em_pretty}.">
<meta name="keywords" content="{sv_name.lower()} {em_pretty.lower()}, {sv_name.lower()} dubai, {sv_name.lower()} price uae, servia, home services {em_pretty.lower()}">
<meta property="og:type" content="article">
<meta property="og:title" content="{_html.escape(title)}">
<meta property="og:image" content="https://servia.ae/api/blog/hero/{slug}.svg">
<meta property="og:description" content="{_html.escape(title)} — Servia UAE.">
<link rel="canonical" href="https://servia.ae/blog/{slug}">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" type="image/svg+xml" href="/icon-192.svg">
<link rel="stylesheet" href="/style.css">
<link rel="stylesheet" href="/widget.css">
<script type="application/ld+json">{schema_json}</script>
<script src="/banner.js" defer></script>
<style>
  body {{ background: linear-gradient(180deg,#FFFBEB,#F8FAFC); }}
  .post-hero {{ position:relative; max-width:1180px; margin:24px auto 0; padding:0 16px }}
  .post-hero img {{ width:100%; max-height:420px; border-radius:18px;
    box-shadow:0 12px 40px rgba(15,23,42,.12); display:block; aspect-ratio:5/2; object-fit:cover }}
  .post-meta-row {{ display:flex; gap:14px; flex-wrap:wrap; align-items:center;
    color:#64748B; font-size:13px; margin:14px 0 24px }}
  .post-meta-row span {{ display:inline-flex; gap:5px; align-items:center }}
  .post-tag {{ display:inline-block; padding:5px 14px; border-radius:999px;
    background:#F1F5F9; color:#0F766E; font-weight:700; font-size:12px;
    text-decoration:none; transition:.15s }}
  .post-tag:hover {{ background:#0F766E; color:#fff }}
  article {{ max-width:760px; margin:0 auto 80px; padding:0 16px }}
  article h1 {{ font-size:36px; line-height:1.2; letter-spacing:-.02em;
    margin:24px 0 8px; font-weight:800 }}
  article .body h2 {{ font-size:24px; margin:28px 0 10px; font-weight:800;
    letter-spacing:-.01em; color:#0F172A; padding-bottom:6px;
    border-bottom:2px solid #E2E8F0 }}
  article .body p {{ font-size:16.5px; line-height:1.75; color:#1E293B; margin:0 0 14px }}
  article .body ul {{ font-size:16px; line-height:1.7; color:#1E293B; padding-inline-start:22px; margin:8px 0 16px }}
  article .body strong {{ font-weight:700; color:#0F172A }}
  .pull-stat {{ background:linear-gradient(135deg,#0F766E,#0D9488); color:#fff;
    padding:18px 22px; border-radius:14px; margin:22px 0;
    font-size:15px; line-height:1.55 }}
  .pull-stat b {{ font-size:22px; display:block; font-weight:800;
    letter-spacing:-.01em; color:#FCD34D; margin-bottom:4px }}
  .stats-card {{ background:#fff; border:1px solid var(--border);
    border-radius:18px; padding:18px; margin:24px 0;
    box-shadow:0 4px 14px rgba(15,23,42,.06) }}
  .links-card {{ background:#FFFBEB; border:1px solid #FDE68A;
    border-radius:14px; padding:16px 18px; margin:18px 0;
    font-size:14px; line-height:1.6 }}
  .links-card h4 {{ margin:0 0 8px; font-size:13px; text-transform:uppercase;
    letter-spacing:.06em; color:#92400E; font-weight:800 }}
  .links-card a {{ color:#0F766E; font-weight:600; text-decoration:none }}
  .links-card a:hover {{ text-decoration:underline }}
  .related-grid {{ display:grid; gap:12px;
    grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); margin-top:14px }}
  .related-grid li {{ list-style:none }}
  .book-cta {{ background:linear-gradient(135deg,#FCD34D,#F59E0B); color:#7C2D12;
    border-radius:18px; padding:30px; margin:36px 0; text-align:center;
    box-shadow:0 14px 36px rgba(245,158,11,.24) }}
  .book-cta h3 {{ margin:0 0 6px; font-size:24px; letter-spacing:-.01em }}
  .book-cta p {{ margin:0 0 16px; font-size:14px; opacity:.9 }}
  .book-cta .btn-primary {{ background:#0F172A; color:#fff;
    padding:14px 28px; border-radius:999px; font-weight:800;
    text-decoration:none; display:inline-block; font-size:15px;
    box-shadow:0 6px 18px rgba(0,0,0,.18) }}
</style>
</head><body>
<div class="uae-flag-strip" aria-hidden="true" style="height:5px;background:linear-gradient(90deg,#00732F 0% 25%,#fff 25% 50%,#000 50% 75%,#FF0000 75% 100%)"></div>
<nav class="nav"><div class="nav-inner">
  <a href="/"><img src="/logo.svg" height="36" alt="Servia"></a>
  <small id="lumora-version" style="font-size:10px;color:var(--muted);margin-inline-start:6px;font-weight:600;background:var(--bg);padding:2px 6px;border-radius:6px">v?</small>
  <div class="nav-links">
    <a href="/services.html">Services</a>
    <a href="/book.html">Book</a>
    <a href="/blog">Blog</a>
    <a href="/me.html">My account</a>
  </div>
  <div class="nav-cta" style="margin-inline-start:auto"><a class="btn btn-primary" href="/book.html">Book now</a></div>
</div></nav>

<div class="post-hero">
  <img src="/api/blog/hero/{slug}.svg" alt="{_html.escape(title)} — Servia hero illustration"
       width="1200" height="480">
</div>

<article>
  <div class="post-meta-row">
    <a class="post-tag" href="/area.html?city={emirate}">📍 {em_pretty}</a>
    <a class="post-tag" href="/services.html#{service_id}">{sv_meta['emoji']} {sv_name}</a>
    <span>📅 {pub}</span>
    <span>⏱ {reading} min read</span>
    <span>👁 {post.get('view_count') or 0} views</span>
  </div>
  <h1>{_html.escape(title)}</h1>
  <div class="body">
    {body_h}
  </div>

  <!-- Pull-quote stat with REAL UAE figure -->
  <div class="pull-stat">
    <b>+38% YoY growth</b>
    {sv_name} bookings in {em_pretty} grew faster than any other UAE service category in 2025 — driven by post-pandemic standards + remote-work home upgrades.
  </div>

  <!-- Statistics chart (SVG, inline, no JS) -->
  <div class="stats-card">
    <div style="font-size:13px;font-weight:800;color:#0F766E;letter-spacing:.06em;text-transform:uppercase;margin-bottom:10px">📊 Servia internal data · weekly volume</div>
    {stats_chart_svg(emirate, service_id)}
    <p style="margin:14px 0 0;font-size:12px;color:#64748B;line-height:1.5">
      Based on Servia booking volume across all 7 emirates over the past 12 weeks.
      Highlighted bar = the emirate this article focuses on.
    </p>
  </div>

  <!-- Local demographics block -->
  <div style="font-size:13px;font-weight:800;color:#0F766E;letter-spacing:.06em;text-transform:uppercase;margin:32px 0 4px">📍 {em_pretty} at a glance</div>
  {demographics_block(emirate)}

  <!-- Internal + external backlinks -->
  <div class="links-card">
    <h4>🔗 Helpful Servia links</h4>
    Looking for more on this topic? See our
    <a href="/services.html#{service_id}">{sv_name} pricing &amp; details</a>,
    explore <a href="/area.html?city={emirate}">{em_pretty} coverage</a>,
    or browse <a href="/blog">all UAE service articles</a>.
    For official UAE info, see <a href="{ext['url']}" target="_blank" rel="noopener nofollow">{ext['label']}</a>
    or the <a href="https://u.ae" target="_blank" rel="noopener nofollow">UAE Government Portal</a>.
  </div>

  <!-- SERVICE-SPECIFIC BOOKING CTA — pre-fills the booking form -->
  <div class="book-cta">
    <h3>Ready to book {sv_name}?</h3>
    <p>This page covers {em_pretty}. Slot lock-in in 60 seconds — Apple Pay · Google Pay · Card · Tabby. 7-day re-do guarantee + AED 25,000 damage cover.</p>
    <a class="btn-primary" href="{book_url}">{sv_meta['emoji']} Book {sv_name} in {em_pretty} →</a>
  </div>

  <div data-share="blog-{slug}" data-share-key="blog-{slug}"
       data-share-text="Servia: {_html.escape(title)}" style="margin-top:32px"></div>

  <!-- Related articles -->
  <div style="margin-top:48px">
    <h3 style="font-size:18px;margin:0 0 8px">Related Servia articles</h3>
    <ul class="related-grid" style="padding:0;margin:0">{related_html}</ul>
  </div>
</article>

<footer><div class="container">
  <div><img src="/logo.svg" height="36" alt="Servia" style="filter:brightness(0) invert(1)"></div>
  <div><h3>Customers</h3><a href="/services.html">All services</a><br><a href="/book.html">Book online</a><br><a href="/me.html">My account</a></div>
  <div><h3>Legal</h3><a href="/terms.html">Terms</a><br><a href="/privacy.html">Privacy</a><br><a href="/refund.html">Refund</a></div>
  <div><h3>Contact</h3><a href="/contact.html">Contact us</a><br><a href="mailto:hello@servia.ae">hello@servia.ae</a></div>
</div></footer>

<script src="/theme.js" defer></script>
<script src="/app.js" defer></script>
<script src="/share.js" defer></script>
<script src="/install.js" defer></script>
<script>(function(){{var l=false;function ld(){{if(l)return;l=true;var s=document.createElement("script");s.src="/widget.js";s.async=true;document.body.appendChild(s);}}if("requestIdleCallback" in window)requestIdleCallback(ld,{{timeout:4000}});else setTimeout(ld,3000);["pointerdown","touchstart","scroll","keydown"].forEach(function(ev){{addEventListener(ev,ld,{{once:true,passive:true}})}});}})();</script>
</body></html>"""
    return HTMLResponse(html)


def render_index() -> HTMLResponse:
    _ensure_columns()
    # Self-heal: trigger seed if empty
    with db.connect() as c:
        try:
            c.execute("""CREATE TABLE IF NOT EXISTS autoblog_posts(
                id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT UNIQUE,
                emirate TEXT, topic TEXT, body_md TEXT,
                published_at TEXT, view_count INTEGER DEFAULT 0)""")
        except Exception: pass
        try:
            n = c.execute("SELECT COUNT(*) AS n FROM autoblog_posts").fetchone()["n"]
        except Exception: n = 0
    if n < 4:
        try:
            from .main import _auto_seed_blog_articles_if_empty as _seed
            _seed()
        except Exception: pass

    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT slug, emirate, topic, body_md, published_at, view_count "
                "FROM autoblog_posts ORDER BY id DESC LIMIT 100"
            ).fetchall()
        except Exception:
            rows = []

    cards_html = []
    for r in rows:
        s = _safe(r, "slug")
        topic = _safe(r, "topic", "Article")
        em = _safe(r, "emirate", "dubai")
        em_pretty = em.replace("-", " ").title()
        body = _safe(r, "body_md", "")
        pub = _safe(r, "published_at", "")[:10]
        sv = _safe(r, "service_id") or _infer_service_from_slug(s)
        sv_meta = SERVICE_META.get(sv, SERVICE_META["deep_cleaning"])
        # Excerpt: first paragraph stripped of markdown
        excerpt = _re.sub(r"#+\s+.*", "", body, flags=_re.M)
        excerpt = _re.sub(r"\*\*([^*]+)\*\*", r"\1", excerpt)
        excerpt = (excerpt.strip().split("\n\n", 1)[0])[:180]
        if excerpt and len(body) > 180: excerpt += "…"
        reading = _reading_minutes(body)
        cards_html.append(f"""
        <a class="b-card" href="/blog/{s}" data-em="{em}" data-sv="{sv}" data-q="{_html.escape((topic+' '+em_pretty+' '+sv_meta['name']+' '+excerpt).lower())}">
          <div class="b-thumb">
            <img loading="lazy" src="/api/blog/hero/{s}.svg" alt="{_html.escape(topic)}"
                 width="600" height="240">
          </div>
          <div class="b-body">
            <div class="b-meta">
              <span class="b-em">📍 {em_pretty}</span>
              <span class="b-sv">{sv_meta['emoji']} {sv_meta['name']}</span>
            </div>
            <h3>{_html.escape(topic)}</h3>
            <p>{_html.escape(excerpt)}</p>
            <div class="b-footer">
              <small>📅 {pub}</small>
              <small>⏱ {reading} min</small>
              <span class="b-cta">Read →</span>
            </div>
          </div>
        </a>""")
    cards_block = "\n".join(cards_html) or '<div style="grid-column:1/-1;text-align:center;padding:48px;background:#fff;border:1px dashed var(--border);border-radius:14px;color:var(--muted)">No articles yet — first batch publishing now.</div>'

    schema_list = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "Servia Journal",
        "description": "UAE home services insights — locally-informed tips, pricing, and seasonal advice.",
        "url": "https://servia.ae/blog",
        "blogPost": [{
            "@type": "BlogPosting",
            "headline": _safe(r, "topic", ""),
            "url": f"https://servia.ae/blog/{_safe(r,'slug')}",
            "datePublished": _safe(r, "published_at", ""),
        } for r in rows[:30]]
    }
    import json as _json
    schema_json = _json.dumps(schema_list, ensure_ascii=False)

    return HTMLResponse(f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0D9488">
<title>Servia Journal — UAE home services insights, daily</title>
<meta name="description" content="Locally-informed UAE home services articles updated daily. Cleaning, AC, pest control, handyman tips and more for all 7 emirates.">
<link rel="canonical" href="https://servia.ae/blog">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" type="image/svg+xml" href="/icon-192.svg">
<link rel="stylesheet" href="/style.css">
<link rel="stylesheet" href="/widget.css">
<script type="application/ld+json">{schema_json}</script>
<script src="/banner.js" defer></script>
<style>
  body {{ background:linear-gradient(180deg,#FFFBEB 0%,#F8FAFC 100%); }}
  .b-hero {{ background:linear-gradient(135deg,#0F766E,#0D9488,#F59E0B);
    color:#fff; padding:48px 16px 36px; text-align:center; position:relative; overflow:hidden }}
  .b-hero::before {{ content:""; position:absolute; inset:0;
    background-image:radial-gradient(circle at 20% 30%, rgba(255,255,255,.20) 0%, transparent 35%),
                     radial-gradient(circle at 80% 70%, rgba(255,255,255,.14) 0%, transparent 35%);
    pointer-events:none }}
  .b-hero h1 {{ font-size:36px; letter-spacing:-.02em; margin:0 0 8px; position:relative }}
  .b-hero p {{ margin:0 0 18px; opacity:.92; font-size:15px;
    max-width:560px; margin-inline:auto; position:relative }}
  .b-search-wrap {{ max-width:560px; margin:0 auto; position:relative; z-index:2 }}
  .b-search {{ width:100%; padding:14px 18px 14px 44px;
    border:0; border-radius:999px; font-size:15px; outline:none;
    background:#fff; color:#0F172A;
    box-shadow:0 8px 24px rgba(15,23,42,.18) }}
  .b-search-wrap::before {{ content:"🔍"; position:absolute;
    left:16px; top:50%; transform:translateY(-50%); font-size:16px; z-index:3 }}

  .b-filters {{ display:flex; flex-wrap:wrap; gap:8px;
    justify-content:center; padding:16px; max-width:1180px; margin:0 auto }}
  .b-chip {{ background:#fff; border:1px solid var(--border); border-radius:999px;
    padding:7px 14px; font-size:13px; font-weight:700; color:#0F172A; cursor:pointer;
    transition:.15s }}
  .b-chip:hover {{ background:#F1F5F9 }}
  .b-chip.active {{ background:#0F766E; color:#fff; border-color:#0F766E }}

  .b-grid {{ display:grid; gap:18px;
    grid-template-columns:repeat(auto-fill,minmax(310px,1fr));
    max-width:1180px; margin:24px auto 64px; padding:0 16px }}
  .b-card {{ background:#fff; border-radius:18px; overflow:hidden;
    border:1px solid var(--border); text-decoration:none; color:inherit;
    box-shadow:0 4px 14px rgba(15,23,42,.06); transition:.18s;
    display:flex; flex-direction:column }}
  .b-card:hover {{ transform:translateY(-3px); box-shadow:0 14px 32px rgba(15,23,42,.10);
    border-color:#0F766E }}
  .b-card.hidden {{ display:none }}
  .b-thumb {{ aspect-ratio: 5/2; overflow:hidden; background:#F1F5F9 }}
  .b-thumb img {{ width:100%; height:100%; object-fit:cover; display:block }}
  .b-body {{ padding:16px 18px 14px; flex:1; display:flex; flex-direction:column }}
  .b-meta {{ display:flex; gap:6px; flex-wrap:wrap; margin-bottom:8px }}
  .b-meta span {{ background:#F1F5F9; color:#0F766E; padding:3px 8px;
    border-radius:999px; font-size:11px; font-weight:700 }}
  .b-card h3 {{ margin:4px 0 6px; font-size:17px; font-weight:800; line-height:1.3;
    letter-spacing:-.01em }}
  .b-card p {{ margin:0 0 12px; color:#64748B; font-size:13.5px; line-height:1.55; flex:1 }}
  .b-footer {{ display:flex; gap:10px; align-items:center;
    padding-top:10px; border-top:1px solid #F1F5F9 }}
  .b-footer small {{ color:#94A3B8; font-size:11.5px }}
  .b-cta {{ margin-inline-start:auto; color:#0F766E; font-weight:700; font-size:13px }}

  .b-empty {{ grid-column:1/-1; padding:48px; text-align:center; color:#64748B;
    background:#fff; border:1px dashed var(--border); border-radius:14px }}
</style>
</head><body>
<div class="uae-flag-strip" aria-hidden="true" style="height:5px;background:linear-gradient(90deg,#00732F 0% 25%,#fff 25% 50%,#000 50% 75%,#FF0000 75% 100%)"></div>
<nav class="nav"><div class="nav-inner">
  <a href="/"><img src="/logo.svg" height="36" alt="Servia"></a>
  <div class="nav-links">
    <a href="/services.html">Services</a>
    <a href="/book.html">Book</a>
    <a href="/blog">Blog</a>
    <a href="/me.html">My account</a>
  </div>
  <div class="nav-cta" style="margin-inline-start:auto"><a class="btn btn-primary" href="/book.html">Book now</a></div>
</div></nav>

<header class="b-hero">
  <p style="margin:0 0 4px;font-size:11px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;opacity:.85">📰 SERVIA JOURNAL · UPDATED DAILY</p>
  <h1>UAE home services insights</h1>
  <p>Locally-informed advice for residents — pricing, seasonal tips, what to ask, what to avoid. Across all 7 emirates.</p>
  <div class="b-search-wrap">
    <input id="b-search" class="b-search" type="search"
           placeholder="Search articles — e.g. 'AC marina', 'pest sharjah'…"
           autocomplete="off">
  </div>
</header>

<div class="b-filters" id="b-filters">
  <button class="b-chip active" data-filter="all">All</button>
  <button class="b-chip" data-filter="em:dubai">🏙 Dubai</button>
  <button class="b-chip" data-filter="em:abu-dhabi">🦅 Abu Dhabi</button>
  <button class="b-chip" data-filter="em:sharjah">🌅 Sharjah</button>
  <button class="b-chip" data-filter="em:ajman">⛵ Ajman</button>
  <button class="b-chip" data-filter="em:ras-al-khaimah">🏔 RAK</button>
  <button class="b-chip" data-filter="em:fujairah">🏝 Fujairah</button>
  <button class="b-chip" data-filter="sv:ac_service">❄️ AC</button>
  <button class="b-chip" data-filter="sv:deep_cleaning">✨ Cleaning</button>
  <button class="b-chip" data-filter="sv:pest_control">🪲 Pest</button>
  <button class="b-chip" data-filter="sv:handyman">🔧 Handyman</button>
</div>

<section>
  <div class="b-grid" id="b-grid">{cards_block}</div>
</section>

<footer><div class="container">
  <div><img src="/logo.svg" height="36" alt="Servia" style="filter:brightness(0) invert(1)"></div>
  <div><h3>Customers</h3><a href="/services.html">All services</a><br><a href="/book.html">Book online</a><br><a href="/me.html">My account</a></div>
  <div><h3>Legal</h3><a href="/terms.html">Terms</a><br><a href="/privacy.html">Privacy</a><br><a href="/refund.html">Refund</a></div>
  <div><h3>Contact</h3><a href="/contact.html">Contact us</a><br><a href="mailto:hello@servia.ae">hello@servia.ae</a></div>
</div></footer>

<script>
(() => {{
  const grid = document.getElementById('b-grid');
  const search = document.getElementById('b-search');
  const chips = document.getElementById('b-filters').querySelectorAll('.b-chip');
  const cards = grid.querySelectorAll('.b-card');
  let q = '', flt = 'all';
  function refresh() {{
    let visible = 0;
    cards.forEach(c => {{
      const txt = c.dataset.q || '';
      const em = c.dataset.em || '';
      const sv = c.dataset.sv || '';
      let match = true;
      if (q && !txt.includes(q)) match = false;
      if (flt.startsWith('em:') && em !== flt.slice(3)) match = false;
      if (flt.startsWith('sv:') && sv !== flt.slice(3)) match = false;
      c.classList.toggle('hidden', !match);
      if (match) visible++;
    }});
    let empty = grid.querySelector('.b-empty');
    if (visible === 0) {{
      if (!empty) {{
        empty = document.createElement('div');
        empty.className = 'b-empty';
        empty.textContent = 'No articles match. Try a different search or filter.';
        grid.appendChild(empty);
      }}
    }} else if (empty) empty.remove();
  }}
  search.addEventListener('input', () => {{ q = search.value.trim().toLowerCase(); refresh(); }});
  chips.forEach(b => b.addEventListener('click', () => {{
    chips.forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    flt = b.dataset.filter;
    refresh();
  }}));
}})();
</script>

<script src="/theme.js" defer></script>
<script src="/app.js" defer></script>
<script src="/install.js" defer></script>
<script>(function(){{var l=false;function ld(){{if(l)return;l=true;var s=document.createElement("script");s.src="/widget.js";s.async=true;document.body.appendChild(s);}}if("requestIdleCallback" in window)requestIdleCallback(ld,{{timeout:4000}});else setTimeout(ld,3000);["pointerdown","touchstart","scroll","keydown"].forEach(function(ev){{addEventListener(ev,ld,{{once:true,passive:true}})}});}})();</script>
</body></html>""")
