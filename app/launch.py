"""Admin launch + growth endpoints.

Three concerns wired together so admin can run the entire go-to-market
without touching code:

1. Snippets injector
   Admin pastes raw <script>/<meta> from Google Analytics, GTM, Meta Pixel,
   Microsoft Clarity, Search Console verification, etc. We persist via
   db.cfg_get/cfg_set and serve it back from a public /_snippets.js endpoint
   that runs on every page load (script tag wired into all HTML).

2. Launch checklist
   Each item is a structured row: id, label, group, action_url, info_url,
   status. Marked done/skipped via /api/admin/launch/toggle. Built-in starter
   set covers: webmaster tools, sitemap submission, AI search engines, listings,
   social profiles, analytics, and pixel tracking.

3. Listings & mentions tracker
   Admin records URLs where Servia is listed/mentioned across the web.
   We surface a 'find new mentions' helper that runs preset Google queries.
"""
from __future__ import annotations

import json as _json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from . import db
from .auth import require_admin

router = APIRouter(prefix="/api/admin/launch", tags=["admin-launch"],
                   dependencies=[Depends(require_admin)])

# ---------- snippets storage ----------

DEFAULT_SNIPPETS: dict[str, Any] = {
    "verifications": {
        "google_site_verification": "",
        "bing": "",
        "yandex": "",
        "facebook_domain_verification": "",
        "p_partytown": "",
    },
    "head": [],            # raw HTML strings injected into <head>
    "body": [],            # raw HTML strings injected at end of <body>
    "ga4_id": "",          # convenience: G-XXXXXXXXXX
    "gtm_id": "",          # convenience: GTM-XXXXXXX
    "meta_pixel_id": "",
    "tiktok_pixel_id": "",
    "clarity_id": "",
    "hotjar_id": "",
    "plausible_domain": "",
    "matomo_url": "",      # full URL like https://matomo.example.com
}


def _load() -> dict:
    cur = db.cfg_get("launch_snippets", {}) or {}
    out = {**DEFAULT_SNIPPETS, **cur}
    out["verifications"] = {**DEFAULT_SNIPPETS["verifications"],
                            **(cur.get("verifications") or {})}
    return out


def _save(d: dict) -> None:
    db.cfg_set("launch_snippets", d)


class SnippetsBody(BaseModel):
    verifications: dict[str, str] | None = None
    head: list[str] | None = None
    body: list[str] | None = None
    ga4_id: str | None = None
    gtm_id: str | None = None
    meta_pixel_id: str | None = None
    tiktok_pixel_id: str | None = None
    clarity_id: str | None = None
    hotjar_id: str | None = None
    plausible_domain: str | None = None
    matomo_url: str | None = None


@router.get("/snippets")
def get_snippets():
    return _load()


@router.post("/snippets")
def save_snippets(body: SnippetsBody):
    cur = _load()
    upd = body.dict(exclude_none=True)
    if "verifications" in upd:
        cur["verifications"] = {**cur["verifications"], **upd.pop("verifications")}
    cur.update(upd)
    _save(cur)
    return {"ok": True, "saved": cur}


# ---------- public snippets renderer ----------

def public_snippets_js() -> str:
    """Returns JavaScript that injects all configured tracking + verification
    code into the current page. Served by main.py at /_snippets.js so every
    page can include it via <script src='/_snippets.js' defer></script>."""
    s = _load()
    ver = s.get("verifications") or {}
    head_blocks: list[str] = []

    # Verification meta tags
    if ver.get("google_site_verification"):
        head_blocks.append(
            f'<meta name="google-site-verification" content="{ver["google_site_verification"]}">')
    if ver.get("bing"):
        head_blocks.append(f'<meta name="msvalidate.01" content="{ver["bing"]}">')
    if ver.get("yandex"):
        head_blocks.append(f'<meta name="yandex-verification" content="{ver["yandex"]}">')
    if ver.get("facebook_domain_verification"):
        head_blocks.append(
            f'<meta name="facebook-domain-verification" content="{ver["facebook_domain_verification"]}">')

    # GA4 (gtag) — auto-build from id if user supplied one
    if s.get("ga4_id"):
        head_blocks.append(
            f'<script async src="https://www.googletagmanager.com/gtag/js?id={s["ga4_id"]}"></script>')
        head_blocks.append(
            "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
            "gtag('js',new Date());gtag('config','" + s["ga4_id"] + "',{'anonymize_ip':true});</script>")

    # GTM
    if s.get("gtm_id"):
        head_blocks.append(
            "<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':"
            "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],"
            "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;"
            "j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;"
            "f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','" + s["gtm_id"] + "');</script>")

    # Meta Pixel
    if s.get("meta_pixel_id"):
        head_blocks.append(
            "<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){"
            "n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};"
            "if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';"
            "n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;"
            "s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}"
            "(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');"
            f"fbq('init','{s['meta_pixel_id']}');fbq('track','PageView');</script>")

    # TikTok Pixel
    if s.get("tiktok_pixel_id"):
        head_blocks.append(
            "<script>!function(w,d,t){w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];"
            "ttq.methods=['page','track','identify','instances','debug','on','off','once','ready','alias','group','enableCookie','disableCookie'];"
            "ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};"
            "for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);"
            "ttq.instance=function(t){for(var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e};"
            "ttq.load=function(e,n){var i='https://analytics.tiktok.com/i18n/pixel/events.js';"
            "ttq._i=ttq._i||{};ttq._i[e]=[];ttq._i[e]._u=i;ttq._t=ttq._t||{};ttq._t[e]=+new Date;"
            "ttq._o=ttq._o||{};ttq._o[e]=n||{};var o=document.createElement('script');"
            "o.type='text/javascript';o.async=!0;o.src=i+'?sdkid='+e+'&lib='+t;"
            "var a=document.getElementsByTagName('script')[0];a.parentNode.insertBefore(o,a)};"
            f"ttq.load('{s['tiktok_pixel_id']}');ttq.page();}}(window,document,'ttq');</script>")

    # Microsoft Clarity (heatmaps + session recording)
    if s.get("clarity_id"):
        head_blocks.append(
            "<script>(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){"
            "(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);"
            "t.async=1;t.src='https://www.clarity.ms/tag/'+i;"
            "y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);"
            f"}})(window,document,'clarity','script','{s['clarity_id']}');</script>")

    # Hotjar
    if s.get("hotjar_id"):
        head_blocks.append(
            f"<script>(function(h,o,t,j,a,r){{h.hj=h.hj||function(){{(h.hj.q=h.hj.q||[]).push(arguments)}};"
            f"h._hjSettings={{hjid:{s['hotjar_id']},hjsv:6}};a=o.getElementsByTagName('head')[0];"
            "r=o.createElement('script');r.async=1;"
            "r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;a.appendChild(r);"
            "})(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');</script>")

    # Plausible (privacy-respecting)
    if s.get("plausible_domain"):
        head_blocks.append(
            f'<script defer data-domain="{s["plausible_domain"]}" '
            'src="https://plausible.io/js/script.js"></script>')

    # Matomo
    if s.get("matomo_url"):
        head_blocks.append(
            "<script>var _paq=window._paq=window._paq||[];_paq.push(['trackPageView']);"
            "_paq.push(['enableLinkTracking']);(function(){var u='" + s["matomo_url"].rstrip("/") + "/';"
            "_paq.push(['setTrackerUrl',u+'matomo.php']);_paq.push(['setSiteId','1']);"
            "var d=document,g=d.createElement('script'),s=d.getElementsByTagName('script')[0];"
            "g.async=true;g.src=u+'matomo.js';s.parentNode.insertBefore(g,s);})();</script>")

    # Custom raw blocks
    for raw in (s.get("head") or []):
        if raw and raw.strip(): head_blocks.append(raw.strip())

    body_blocks: list[str] = list(s.get("body") or [])

    # Build the payload as JS that injects everything
    head_js = _json.dumps("".join(head_blocks))
    body_js = _json.dumps("".join(body_blocks))
    return (
        "/* Servia public snippets — injected into every page. */\n"
        "(function(){\n"
        f"  var H={head_js};\n"
        f"  var B={body_js};\n"
        "  if(H && document.head) document.head.insertAdjacentHTML('beforeend', H);\n"
        "  if(B && document.body) document.body.insertAdjacentHTML('beforeend', B);\n"
        "  else if(B) document.addEventListener('DOMContentLoaded', function(){ document.body.insertAdjacentHTML('beforeend', B); });\n"
        "})();\n"
    )


# ---------- launch checklist ----------

# Built-in starter checklist. Admin can mark items done; status persisted.
STARTER_CHECKLIST = [
    # ----- Webmaster / search engines -----
    {"id": "gsc",           "group": "Search engines",
     "label": "Verify in Google Search Console + submit sitemap",
     "info": "Get your verification meta tag, paste it in 'Verifications · google_site_verification'. Then click 'Submit sitemap' below.",
     "action_url": "https://search.google.com/search-console/welcome",
     "submit_url": "https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Fservia.ae%2F&sitemap_url=https%3A%2F%2Fservia.ae%2Fsitemap.xml"},
    {"id": "bing",          "group": "Search engines",
     "label": "Verify in Bing Webmaster Tools + submit sitemap",
     "info": "Get the BingSiteAuth content. Paste in 'Verifications · bing'. Then submit sitemap on Bing.",
     "action_url": "https://www.bing.com/webmasters/about",
     "submit_url": "https://www.bing.com/webmasters/sitemaps?siteUrl=https%3A%2F%2Fservia.ae%2F"},
    {"id": "yandex",        "group": "Search engines",
     "label": "Verify in Yandex Webmaster",
     "info": "Important for Russian-speaking UAE residents — large audience.",
     "action_url": "https://webmaster.yandex.com/welcome/"},
    {"id": "duck",          "group": "Search engines",
     "label": "Auto-indexed by DuckDuckGo (no action needed)",
     "info": "DDG pulls from Bing — verifying Bing covers DuckDuckGo.",
     "action_url": "https://duckduckgo.com/?q=site%3Aservia.ae"},

    # ----- AI search visibility -----
    {"id": "llms-txt",      "group": "AI engines",
     "label": "/llms.txt is published — submit to AI directories",
     "info": "Servia already exposes /llms.txt for LLM crawlers. Submit to AI registries below.",
     "action_url": "https://servia.ae/llms.txt"},
    {"id": "perplexity",    "group": "AI engines",
     "label": "Perplexity — verify domain ownership for citations",
     "info": "Perplexity + ChatGPT search prioritize verified-owner content.",
     "action_url": "https://www.perplexity.ai/hub"},
    {"id": "openai-cse",    "group": "AI engines",
     "label": "Allow GPTBot in robots.txt (already enabled)",
     "info": "Servia robots.txt allows GPTBot, ClaudeBot, PerplexityBot, etc. Verify on this URL.",
     "action_url": "https://servia.ae/robots.txt"},
    {"id": "schema-test",   "group": "AI engines",
     "label": "Validate Schema.org structured data",
     "info": "Servia emits LocalBusiness + Service + FAQPage + BlogPosting JSON-LD. Test it:",
     "action_url": "https://search.google.com/test/rich-results?url=https%3A%2F%2Fservia.ae"},

    # ----- Listings -----
    {"id": "gbp",           "group": "Listings",
     "label": "Google Business Profile (Maps)",
     "info": "Free verified listing — drives ~30% of small-business calls.",
     "action_url": "https://www.google.com/business/"},
    {"id": "apple-maps",    "group": "Listings",
     "label": "Apple Maps Connect",
     "info": "iOS users searching nearby services see this.",
     "action_url": "https://mapsconnect.apple.com/"},
    {"id": "bing-places",   "group": "Listings",
     "label": "Bing Places for Business",
     "info": "Same data feeds DuckDuckGo + Yahoo.",
     "action_url": "https://www.bingplaces.com/"},
    {"id": "trustpilot",    "group": "Listings",
     "label": "Trustpilot business profile",
     "info": "Critical for trust signals + paid-ad CTR.",
     "action_url": "https://business.trustpilot.com/signup"},
    {"id": "connect-ae",    "group": "Listings",
     "label": "Connect.ae UAE business directory",
     "info": "Top UAE local directory — high domain authority.",
     "action_url": "https://www.connect.ae/"},
    {"id": "yellowpages-uae","group": "Listings",
     "label": "Yellow Pages UAE",
     "info": "Old-school but still ranked high in UAE searches.",
     "action_url": "https://www.yellowpages.ae/"},
    {"id": "souqalmal",     "group": "Listings",
     "label": "Souqalmal UAE",
     "info": "Comparison site UAE consumers trust.",
     "action_url": "https://www.souqalmal.com/"},

    # ----- Social media -----
    {"id": "instagram",     "group": "Social",
     "label": "Instagram @servia.ae", "info": "Pin Reels of completed services.",
     "action_url": "https://www.instagram.com/accounts/emailsignup/"},
    {"id": "tiktok",        "group": "Social",
     "label": "TikTok @servia.ae", "info": "Highest organic reach in UAE.",
     "action_url": "https://www.tiktok.com/signup"},
    {"id": "facebook",      "group": "Social",
     "label": "Facebook Page",
     "info": "Required for Meta Pixel + WhatsApp Business sync.",
     "action_url": "https://www.facebook.com/pages/create"},
    {"id": "x",             "group": "Social",
     "label": "X / Twitter @servia",
     "action_url": "https://x.com/i/flow/signup"},
    {"id": "linkedin",      "group": "Social",
     "label": "LinkedIn Company Page",
     "info": "Critical for B2B leads (office cleaning, corporate handyman).",
     "action_url": "https://www.linkedin.com/company/setup/new/"},
    {"id": "youtube",       "group": "Social",
     "label": "YouTube Channel",
     "info": "Long-form how-to videos rank for years.",
     "action_url": "https://www.youtube.com/create_channel"},
    {"id": "pinterest",     "group": "Social",
     "label": "Pinterest Business",
     "info": "Surprisingly strong for home/cleaning audiences.",
     "action_url": "https://business.pinterest.com/en/business/create/"},

    # ----- Analytics -----
    {"id": "ga4",           "group": "Analytics",
     "label": "Google Analytics 4",
     "info": "Paste your G-XXXXXXXXXX in 'Convenience IDs · ga4_id' below — we wire up gtag automatically.",
     "action_url": "https://analytics.google.com/"},
    {"id": "gtm",           "group": "Analytics",
     "label": "Google Tag Manager",
     "info": "Optional but recommended. Paste GTM-XXXXXXX in 'gtm_id'.",
     "action_url": "https://tagmanager.google.com/"},
    {"id": "clarity",       "group": "Analytics",
     "label": "Microsoft Clarity (heatmaps + session recording)",
     "info": "Free. Paste your project ID in 'clarity_id' below.",
     "action_url": "https://clarity.microsoft.com/"},
    {"id": "meta-pixel",    "group": "Analytics",
     "label": "Meta Pixel (Facebook + Instagram ads)",
     "info": "Paste your numeric pixel ID in 'meta_pixel_id'.",
     "action_url": "https://business.facebook.com/events_manager"},
    {"id": "tiktok-pixel",  "group": "Analytics",
     "label": "TikTok Pixel",
     "info": "Paste pixel ID in 'tiktok_pixel_id'. We wire up the loader.",
     "action_url": "https://ads.tiktok.com/i18n/events_manager/"},
    {"id": "plausible",     "group": "Analytics",
     "label": "Plausible (privacy-respecting analytics, optional)",
     "info": "Paste your domain in 'plausible_domain' to enable.",
     "action_url": "https://plausible.io/"},
]


def _load_status() -> dict:
    return db.cfg_get("launch_status", {}) or {}


@router.get("/checklist")
def get_checklist():
    status = _load_status()
    items = [{**item, "status": status.get(item["id"], "pending")}
             for item in STARTER_CHECKLIST]
    by_group: dict[str, list] = {}
    for it in items:
        by_group.setdefault(it["group"], []).append(it)
    return {"groups": by_group, "all": items,
            "summary": {"total": len(items),
                        "done": sum(1 for it in items if it["status"] == "done"),
                        "skipped": sum(1 for it in items if it["status"] == "skipped")}}


class ToggleBody(BaseModel):
    id: str
    status: str  # 'done' / 'skipped' / 'pending'


@router.post("/toggle")
def toggle_item(body: ToggleBody):
    if body.status not in ("done", "skipped", "pending"):
        raise HTTPException(400, "status must be done/skipped/pending")
    cur = _load_status()
    if body.status == "pending":
        cur.pop(body.id, None)
    else:
        cur[body.id] = body.status
    db.cfg_set("launch_status", cur)
    return {"ok": True}


# ---------- listings + mentions tracker ----------
class ListingBody(BaseModel):
    name: str
    url: str
    notes: str | None = None


@router.get("/listings")
def get_listings():
    return {"listings": db.cfg_get("launch_listings", []) or []}


@router.post("/listings")
def add_listing(body: ListingBody):
    arr = db.cfg_get("launch_listings", []) or []
    arr.append({"name": body.name, "url": body.url, "notes": body.notes,
                "added_at": __import__("datetime").datetime.utcnow().isoformat() + "Z"})
    db.cfg_set("launch_listings", arr)
    return {"ok": True, "count": len(arr)}


@router.delete("/listings")
def remove_listing(url: str):
    arr = db.cfg_get("launch_listings", []) or []
    arr = [x for x in arr if x.get("url") != url]
    db.cfg_set("launch_listings", arr)
    return {"ok": True, "count": len(arr)}


# ---------- social profile URLs (also rendered on every public page footer) ----------
class SocialBody(BaseModel):
    instagram: str | None = None
    tiktok: str | None = None
    facebook: str | None = None
    twitter: str | None = None
    linkedin: str | None = None
    youtube: str | None = None
    pinterest: str | None = None


@router.get("/social")
def get_social():
    return db.cfg_get("social_profiles", {}) or {}


@router.post("/social")
def save_social(body: SocialBody):
    cur = db.cfg_get("social_profiles", {}) or {}
    upd = {k: (v or "").strip() for k, v in body.dict(exclude_none=True).items()}
    cur.update(upd)
    db.cfg_set("social_profiles", cur)
    return {"ok": True, "saved": cur}


@router.get("/mentions/queries")
def mention_queries():
    """Returns preset Google search URLs to discover where Servia is mentioned."""
    qs = [
        "Servia UAE",
        '"servia.ae"',
        "Servia home services Dubai",
        "Servia AC service Dubai",
        "Servia cleaning Sharjah",
        "Servia review",
        "Servia ambassador program",
    ]
    out = []
    for q in qs:
        from urllib.parse import quote
        out.append({"query": q,
                    "google": f"https://www.google.com/search?q={quote(q)}",
                    "bing":   f"https://www.bing.com/search?q={quote(q)}",
                    "duck":   f"https://duckduckgo.com/?q={quote(q)}"})
    return {"queries": out}
