"""Social-media auto-posting infrastructure.

Two modes (admin chooses per platform):

A) **One-click POST** via official APIs (requires API keys/tokens):
   - YouTube · uses Google OAuth + YouTube Data API v3
   - Facebook + Instagram · Meta Graph API + page access token
   - LinkedIn · LinkedIn API v2 + access token
   - X (Twitter) · X API v2 + bearer token
   - TikTok · TikTok Content Posting API + access token

B) **Browser-session POST** via Playwright (where APIs are restricted/expensive):
   - Admin opens a Playwright login session in a browser, pastes their cookies
     OR scans an SSO QR. Cookies persist to /data/social_sessions/<platform>.json
   - Posts are scripted in headless mode using the saved cookies
   - This is the fallback for platforms with limited or paid APIs

For now this module exposes:
   - persistent token storage (db.cfg "social_tokens")
   - per-platform "test connection" probes
   - direct post endpoints for the API-friendly platforms
   - browser-session config endpoints (the Playwright runner runs in the
     bundled whatsapp_bridge container — already has Chromium)

Admin UI lets the user pick a video + caption, then "Post to all".
"""
from __future__ import annotations

import datetime as _dt
import json as _json
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import db
from .auth import require_admin

router = APIRouter(prefix="/api/admin/social", tags=["admin-social"],
                   dependencies=[Depends(require_admin)])


PLATFORMS = {
    "youtube":   {"label": "YouTube",
                  "fields": ["api_key", "channel_id", "client_id", "client_secret", "refresh_token"],
                  "help_url": "https://developers.google.com/youtube/v3/getting-started",
                  "method": "api"},
    "facebook":  {"label": "Facebook Page",
                  "fields": ["page_id", "page_access_token"],
                  "help_url": "https://developers.facebook.com/docs/pages-api/posts",
                  "method": "api"},
    "instagram": {"label": "Instagram (Business)",
                  "fields": ["ig_user_id", "page_access_token"],
                  "help_url": "https://developers.facebook.com/docs/instagram-api/getting-started",
                  "method": "api"},
    "linkedin":  {"label": "LinkedIn Page",
                  "fields": ["organization_urn", "access_token"],
                  "help_url": "https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/share-api",
                  "method": "api"},
    "twitter":   {"label": "X (Twitter)",
                  "fields": ["bearer_token", "api_key", "api_secret", "access_token", "access_token_secret"],
                  "help_url": "https://developer.x.com/en/docs/x-api/getting-started/about-x-api",
                  "method": "api"},
    "tiktok":    {"label": "TikTok (Business)",
                  "fields": ["access_token", "open_id"],
                  "help_url": "https://developers.tiktok.com/doc/content-posting-api-get-started",
                  "method": "api"},
    "pinterest": {"label": "Pinterest",
                  "fields": ["access_token", "board_id"],
                  "help_url": "https://developers.pinterest.com/docs/api/v5/",
                  "method": "api"},
    # Browser-session fallback (uses Playwright + saved cookies)
    "session-fallback": {"label": "Browser-session fallback",
                  "fields": ["enabled"],
                  "help_url": "https://playwright.dev/python/docs/auth",
                  "method": "session"},
}


def _load_tokens() -> dict:
    return db.cfg_get("social_tokens", {}) or {}


def _save_tokens(d: dict) -> None:
    db.cfg_set("social_tokens", d)


# ---------- meta + tokens ----------
class TokensBody(BaseModel):
    platform: str
    fields: dict[str, str]


@router.get("/platforms")
def list_platforms():
    cur = _load_tokens()
    out = []
    for p, info in PLATFORMS.items():
        saved = cur.get(p, {}) or {}
        out.append({
            "platform": p, "label": info["label"], "method": info["method"],
            "help_url": info["help_url"],
            "fields": info["fields"],
            "configured": all(saved.get(f) for f in info["fields"]),
            "values_present": {f: bool(saved.get(f)) for f in info["fields"]},
        })
    return {"platforms": out}


@router.post("/tokens")
def save_tokens(body: TokensBody):
    if body.platform not in PLATFORMS:
        raise HTTPException(400, f"unknown platform '{body.platform}'")
    cur = _load_tokens()
    p = cur.get(body.platform, {}) or {}
    for k, v in (body.fields or {}).items():
        if k in PLATFORMS[body.platform]["fields"]:
            p[k] = (v or "").strip()
    cur[body.platform] = p
    _save_tokens(cur)
    return {"ok": True, "platform": body.platform}


# ---------- post endpoints ----------
class PostBody(BaseModel):
    platform: str
    title: str
    body: str
    video_url: Optional[str] = None     # public URL of the video to share
    image_url: Optional[str] = None     # optional poster
    tags: list[str] | None = None


def _post_facebook(tokens: dict, body: PostBody) -> dict:
    pid = tokens.get("page_id"); pat = tokens.get("page_access_token")
    if not (pid and pat): return {"ok": False, "error": "Facebook page_id + page_access_token required"}
    payload = {"message": f"{body.title}\n\n{body.body}", "link": body.video_url, "access_token": pat}
    r = httpx.post(f"https://graph.facebook.com/v19.0/{pid}/feed", data=payload, timeout=20)
    if r.status_code >= 400: return {"ok": False, "error": f"FB {r.status_code}: {r.text[:200]}"}
    return {"ok": True, "post_id": r.json().get("id"), "url": f"https://facebook.com/{r.json().get('id','')}"}


def _post_twitter(tokens: dict, body: PostBody) -> dict:
    tok = tokens.get("bearer_token") or tokens.get("access_token")
    if not tok: return {"ok": False, "error": "X bearer_token or access_token required"}
    text = f"{body.title}\n\n{body.body}"
    if body.video_url: text += f"\n\n{body.video_url}"
    if body.tags: text += "\n\n" + " ".join("#" + t.replace(" ","_") for t in body.tags)
    r = httpx.post("https://api.twitter.com/2/tweets",
                   headers={"Authorization": f"Bearer {tok}", "content-type": "application/json"},
                   json={"text": text[:280]}, timeout=15)
    if r.status_code >= 400: return {"ok": False, "error": f"X {r.status_code}: {r.text[:200]}"}
    return {"ok": True, "post_id": r.json().get("data", {}).get("id"),
            "url": f"https://x.com/i/web/status/{r.json().get('data',{}).get('id','')}"}


def _post_linkedin(tokens: dict, body: PostBody) -> dict:
    tok = tokens.get("access_token"); urn = tokens.get("organization_urn")
    if not (tok and urn): return {"ok": False, "error": "LinkedIn organization_urn + access_token required"}
    payload = {
        "author": urn, "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": {
            "shareCommentary": {"text": f"{body.title}\n\n{body.body}\n\n{body.video_url or ''}"},
            "shareMediaCategory": "NONE"}},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    r = httpx.post("https://api.linkedin.com/v2/ugcPosts",
        headers={"Authorization": f"Bearer {tok}",
                 "X-Restli-Protocol-Version": "2.0.0", "content-type": "application/json"},
        json=payload, timeout=20)
    if r.status_code >= 400: return {"ok": False, "error": f"LinkedIn {r.status_code}: {r.text[:200]}"}
    return {"ok": True, "post_id": r.headers.get("x-restli-id"),
            "url": f"https://linkedin.com/feed/update/{r.headers.get('x-restli-id','')}"}


@router.post("/post")
def post_now(body: PostBody):
    if body.platform not in PLATFORMS:
        raise HTTPException(400, "unknown platform")
    tokens = (_load_tokens().get(body.platform) or {})
    method = PLATFORMS[body.platform]["method"]
    if method == "session":
        return {"ok": False, "error": "Browser-session posting requires Playwright runner — see /admin → 🌐 Social Auto-post for setup."}
    try:
        if   body.platform == "facebook":  res = _post_facebook(tokens, body)
        elif body.platform == "twitter":   res = _post_twitter(tokens, body)
        elif body.platform == "linkedin":  res = _post_linkedin(tokens, body)
        else:
            return {"ok": False, "error": f"Direct API posting for {body.platform} not yet implemented — store tokens, but use the manual share button for now."}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Log to history
    with db.connect() as c:
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS social_posts(
                id INTEGER PRIMARY KEY AUTOINCREMENT, platform TEXT,
                title TEXT, body TEXT, video_url TEXT, post_url TEXT,
                ok INTEGER, error TEXT, created_at TEXT)""")
        except Exception: pass
        c.execute(
            "INSERT INTO social_posts(platform, title, body, video_url, post_url, ok, error, created_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (body.platform, body.title, body.body, body.video_url,
             res.get("url"), 1 if res.get("ok") else 0, res.get("error"),
             _dt.datetime.utcnow().isoformat() + "Z"))
    return res


@router.get("/history")
def history(limit: int = 50):
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT * FROM social_posts ORDER BY id DESC LIMIT ?",
                (max(1, min(limit, 200)),)).fetchall()
        except Exception: rows = []
    return {"posts": [db.row_to_dict(r) for r in rows]}


# ---------- AI brainstorm: ideas + detailed prompt ----------
class IdeaBody(BaseModel):
    seed: Optional[str] = ""    # admin's brief input (or empty for full AI brainstorm)
    target_platform: Optional[str] = "tiktok"


@router.post("/idea")
async def brainstorm_idea(body: IdeaBody):
    """Returns a polished video brief using the configured 'video' AI model."""
    from . import ai_router
    cfg = ai_router._load_cfg()
    target = (cfg.get("defaults") or {}).get("video", "anthropic/claude-opus-4-7")
    if "/" not in target: target = "anthropic/" + target
    provider, model = target.split("/", 1)
    seed = (body.seed or "").strip()
    plat = body.target_platform or "tiktok"
    if seed:
        prompt = (
            "You write Servia mascot-video briefs. Servia = UAE home services platform.\n"
            f"Customer-supplied brief: {seed}\n"
            f"Target platform: {plat}\n\n"
            "Output a JSON object with: 'topic' (short title, max 60 chars), 'angle' (1-line "
            "creative angle), 'tone' (one of teal/amber/purple/rose/green/blue/indigo/orange), "
            "'mascot' (default/cleaning/ac/handyman/pool/garden/car/maid/pest), "
            "'duration_sec' (15 / 30 / 60), and 'detailed_prompt' "
            "(a 4-6 sentence detailed prompt that another AI will use to generate the actual scene-by-scene script).\n"
            "Output ONLY the JSON, no markdown."
        )
    else:
        prompt = (
            "You brainstorm Servia mascot-video ideas. Servia = UAE home services platform "
            "(cleaning, AC, pest, handyman, sofa, etc) operating across all 7 emirates.\n"
            f"Target platform: {plat}\n\n"
            "Pick a fresh, snackable, scroll-stopping idea no one's done before. Lean into UAE-specific "
            "context (heat, sandstorm, Ramadan, expat moves, traffic, school season, summer travel). "
            "Output a JSON object with: 'topic', 'angle', 'tone', 'mascot', 'duration_sec' (15 / 30 / 60), "
            "and 'detailed_prompt' (4-6 sentences).\n"
            "Output ONLY the JSON."
        )
    res = await ai_router.call_model(provider, model, prompt, cfg)
    if not res.get("ok"):
        raise HTTPException(400, res.get("error") or "AI call failed")
    txt = (res.get("text") or "").strip()
    if "```" in txt:
        import re as _re
        m = _re.search(r"```(?:json)?\s*(\{.*?\})\s*```", txt, _re.S)
        if m: txt = m.group(1)
    if "{" in txt and "}" in txt:
        txt = txt[txt.index("{"): txt.rindex("}") + 1]
    try:
        idea = _json.loads(txt)
    except Exception:
        raise HTTPException(500, f"Could not parse model output: {txt[:200]}")
    return {"ok": True, "idea": idea, "model": target}


# ---------- Multi-platform planner + how-to guides ----------
# Per-platform caption template + best-time hints. Captions aim at platform
# native voice (TikTok = punchy hook, LinkedIn = professional, etc).
_PLATFORM_HINTS = {
    "youtube":   {"max_chars": 5000, "best_time": "Tue/Wed/Thu 16:00–18:00 GST",
                  "hashtags": 3, "aspect": "16x9",
                  "voice": "Hooky title + 2 lines of value + 'subscribe for more'."},
    "facebook":  {"max_chars": 600, "best_time": "Mon–Fri 13:00–15:00 GST",
                  "hashtags": 4, "aspect": "16x9",
                  "voice": "Friendly 1–2 sentence hook + emoji + clear CTA."},
    "instagram": {"max_chars": 2200, "best_time": "Mon/Wed/Fri 11:00–13:00 GST",
                  "hashtags": 12, "aspect": "9x16",
                  "voice": "Lead with 1-line hook, then context + value, end with bold CTA + 8–12 niche hashtags."},
    "linkedin":  {"max_chars": 3000, "best_time": "Tue/Wed 09:00–10:00 GST",
                  "hashtags": 3, "aspect": "16x9",
                  "voice": "Professional tone, 3 short paragraphs, soft CTA, 3 hashtags max."},
    "twitter":   {"max_chars": 280, "best_time": "Mon–Fri 09:00 / 18:00 GST",
                  "hashtags": 2, "aspect": "16x9",
                  "voice": "Single-tweet thread-starter. Hook + 1 detail + link."},
    "tiktok":    {"max_chars": 2200, "best_time": "Daily 19:00–22:00 GST",
                  "hashtags": 6, "aspect": "9x16",
                  "voice": "Hook in <8 words, no fluff. End with native CTA + 5–7 hashtags."},
    "pinterest": {"max_chars": 500, "best_time": "Sat/Sun 14:00–16:00 GST",
                  "hashtags": 5, "aspect": "9x16",
                  "voice": "Search-style title (e.g. 'Sofa cleaning Dubai before & after') + 3-line description."},
}


def _howto() -> dict:
    """Step-by-step setup guides for each platform — what tokens, where to get them, what scopes.
    Returned as JSON so admin UI can render expandable cards. Click-throughs land on
    the platform's developer console."""
    return {
        "youtube": {
            "label": "YouTube",
            "summary": "Use Google Cloud OAuth + YouTube Data API v3 to upload videos to your channel.",
            "steps": [
                {"n": 1, "text": "Open Google Cloud Console", "link": "https://console.cloud.google.com/"},
                {"n": 2, "text": "Create a project → APIs & Services → Library → enable 'YouTube Data API v3'."},
                {"n": 3, "text": "Credentials → Create OAuth Client ID (type: Web). Add redirect URI https://servia.ae/oauth/youtube."},
                {"n": 4, "text": "Copy Client ID + Client Secret here. Use OAuth Playground to mint a refresh token with scope 'https://www.googleapis.com/auth/youtube.upload'.",
                 "link": "https://developers.google.com/oauthplayground"},
                {"n": 5, "text": "Paste channel_id, client_id, client_secret, refresh_token, api_key into the YouTube section."},
            ],
            "scopes_needed": ["youtube.upload", "youtube.readonly"],
            "free_tier": "10k quota units/day (~6 uploads/day for free).",
        },
        "facebook": {
            "label": "Facebook Page",
            "summary": "Use Meta Graph API + a Page Access Token (long-lived).",
            "steps": [
                {"n": 1, "text": "Open Meta for Developers", "link": "https://developers.facebook.com/"},
                {"n": 2, "text": "Create a 'Business' app → Add 'Facebook Login' + 'Pages API' products."},
                {"n": 3, "text": "Use the Graph API Explorer to grant pages_manage_posts + pages_read_engagement, then exchange the user token for a long-lived Page Access Token.",
                 "link": "https://developers.facebook.com/tools/explorer/"},
                {"n": 4, "text": "Find your Page ID under Settings → About on the page."},
                {"n": 5, "text": "Paste page_id + page_access_token here."},
            ],
            "scopes_needed": ["pages_manage_posts", "pages_read_engagement"],
            "free_tier": "Unlimited posts, rate-limited to ~200 calls/hour/app.",
        },
        "instagram": {
            "label": "Instagram (Business)",
            "summary": "Convert your IG to Business/Creator + connect to a FB Page, then post via Graph API.",
            "steps": [
                {"n": 1, "text": "Convert your IG account to a Business or Creator account (in IG app → Settings → Account)."},
                {"n": 2, "text": "Connect that IG account to a Facebook Page in FB → Settings → Linked Accounts."},
                {"n": 3, "text": "In the same Meta app you used for Facebook, add the 'Instagram Graph API' product."},
                {"n": 4, "text": "Find your IG User ID via Graph API Explorer: GET /me/accounts → look for 'instagram_business_account'.",
                 "link": "https://developers.facebook.com/tools/explorer/"},
                {"n": 5, "text": "Paste ig_user_id + page_access_token (same one used for FB) here."},
            ],
            "scopes_needed": ["instagram_basic", "instagram_content_publish"],
            "free_tier": "25 posts/24h via Graph API.",
        },
        "linkedin": {
            "label": "LinkedIn Page",
            "summary": "Use LinkedIn Marketing Developer Platform + a Company Page admin token.",
            "steps": [
                {"n": 1, "text": "Open LinkedIn Developers", "link": "https://developer.linkedin.com/"},
                {"n": 2, "text": "Create app → request access to 'Marketing Developer Platform' (approval can take 1-3 days)."},
                {"n": 3, "text": "Auth flow with scopes w_organization_social + r_organization_social. Use the 3-legged OAuth tool."},
                {"n": 4, "text": "Get your organization URN by GET https://api.linkedin.com/v2/organizationAcls?q=roleAssignee."},
                {"n": 5, "text": "Paste organization_urn (e.g. urn:li:organization:1234567) + access_token here."},
            ],
            "scopes_needed": ["w_organization_social", "r_organization_social"],
            "free_tier": "Up to 100 posts/day per organization.",
        },
        "twitter": {
            "label": "X (Twitter)",
            "summary": "Use X API v2 with a paid 'Basic' tier — free tier no longer allows posting.",
            "steps": [
                {"n": 1, "text": "Open X Developer Portal", "link": "https://developer.x.com/en/portal/dashboard"},
                {"n": 2, "text": "Subscribe to 'Basic' plan ($100/month) — free tier is read-only."},
                {"n": 3, "text": "Create a Project + App. Generate a Bearer Token + OAuth 1.0a user keys."},
                {"n": 4, "text": "Paste bearer_token (or the 4-piece OAuth1 set) here."},
            ],
            "scopes_needed": ["tweet.write", "users.read"],
            "free_tier": "❌ Posting requires paid plan ($100/mo).",
        },
        "tiktok": {
            "label": "TikTok (Business)",
            "summary": "Use TikTok Content Posting API. Apply for Business API access first (1-2 weeks review).",
            "steps": [
                {"n": 1, "text": "Open TikTok for Developers", "link": "https://developers.tiktok.com/"},
                {"n": 2, "text": "Create app → request 'Content Posting API' access (commercial review)."},
                {"n": 3, "text": "Auth with scope 'video.publish'. Implement OAuth → exchange code for access_token + open_id."},
                {"n": 4, "text": "Paste access_token + open_id here. Tokens expire in 24h — refresh via refresh_token."},
            ],
            "scopes_needed": ["video.publish", "user.info.basic"],
            "free_tier": "10 posts/24h on free Business plan.",
        },
        "pinterest": {
            "label": "Pinterest",
            "summary": "Use Pinterest API v5 with a board-level access token.",
            "steps": [
                {"n": 1, "text": "Open Pinterest Developers", "link": "https://developers.pinterest.com/"},
                {"n": 2, "text": "Create app → enable 'pins:write' + 'boards:read' scopes."},
                {"n": 3, "text": "OAuth flow → exchange code for an access_token (long-lived: 30 days)."},
                {"n": 4, "text": "Find your board_id via GET /v5/boards."},
                {"n": 5, "text": "Paste access_token + board_id here."},
            ],
            "scopes_needed": ["pins:write", "boards:read"],
            "free_tier": "1000 calls/hour.",
        },
        "session-fallback": {
            "label": "Browser-session fallback",
            "summary": "When a platform's API isn't an option, automate via Playwright using your own logged-in cookies.",
            "steps": [
                {"n": 1, "text": "On admin desktop: log into the target platform in Chrome."},
                {"n": 2, "text": "Export cookies (e.g. EditThisCookie extension) as JSON."},
                {"n": 3, "text": "Upload the cookies JSON via the upload widget in the platform's Browser-session entry."},
                {"n": 4, "text": "Posts will run in headless Chromium with those cookies — refresh every ~30 days."},
            ],
            "scopes_needed": [],
            "free_tier": "✅ Free, but risk of account flag if platform detects automation.",
        },
    }


@router.get("/howto")
def howto():
    """Returns step-by-step setup guides for each platform (admin-only)."""
    return {"howto": _howto(), "platforms": list(_howto().keys())}


class PlanBody(BaseModel):
    video_slug: str
    title: Optional[str] = ""
    summary: Optional[str] = ""    # 1-line description of the video
    tags: list[str] | None = None


@router.post("/plan")
def plan(body: PlanBody):
    """Returns a per-platform plan: caption tailored to platform voice + best-time hint
    + hashtag set + recommended aspect-ratio. Admin can review + tweak before
    'Post to all configured'."""
    base_url = "https://servia.ae"
    title = (body.title or "").strip() or "Servia tip"
    summary = (body.summary or "").strip() or "Watch this quick Servia explainer."
    tags = [t.strip().replace(" ","") for t in (body.tags or []) if t.strip()] or [
        "Servia", "UAE", "HomeServices", "Dubai", "AbuDhabi"]
    cur = _load_tokens()
    plan_items = []
    for p, info in PLATFORMS.items():
        h = _PLATFORM_HINTS.get(p, {})
        connected = bool(cur.get(p)) and all(cur[p].get(f) for f in info["fields"])
        url = f"{base_url}/api/videos/play/{body.video_slug}?aspect={h.get('aspect','16x9')}"
        ht_n = int(h.get("hashtags") or 3)
        ht = " ".join("#" + t for t in tags[:ht_n])
        max_chars = int(h.get("max_chars") or 280)
        if p == "twitter":
            caption = f"{title} — {summary[:100]}\n\n{url}\n{ht}"[:max_chars]
        elif p == "linkedin":
            caption = (f"{title}\n\n{summary}\n\n👉 Watch the full clip: {url}\n\n{ht}")[:max_chars]
        elif p == "instagram":
            caption = (f"✨ {title}\n\n{summary}\n\nLink in bio · or watch: {url}\n\n.\n.\n.\n{ht}")[:max_chars]
        elif p == "tiktok":
            caption = (f"{title} 👀\n{summary[:80]}\n{url}\n{ht}")[:max_chars]
        elif p == "youtube":
            caption = (f"{title} | Servia UAE\n\n{summary}\n\n🔔 Subscribe for weekly home-care tips.\n\n{ht}")[:max_chars]
        elif p == "pinterest":
            caption = (f"{title} — {summary[:120]}\n\nVisit: {url}\n\n{ht}")[:max_chars]
        else:
            caption = (f"{title}\n\n{summary}\n\n{url}\n\n{ht}")[:max_chars]
        plan_items.append({
            "platform": p,
            "label": info["label"],
            "connected": connected,
            "method": info["method"],
            "best_time": h.get("best_time", ""),
            "voice": h.get("voice", ""),
            "aspect": h.get("aspect", "16x9"),
            "max_chars": max_chars,
            "hashtags_used": ht_n,
            "caption": caption,
            "video_url": url,
        })
    return {"ok": True, "plan": plan_items}


class PostAllBody(BaseModel):
    plan: list[dict]      # list of {platform, caption, video_url, title, ...}


@router.post("/post-all")
def post_all(body: PostAllBody):
    """Sequentially posts the prepared plan to every configured platform.
    Returns per-platform results. Skips platforms that aren't connected."""
    cur = _load_tokens()
    results = []
    for item in (body.plan or []):
        pf = item.get("platform")
        if pf not in PLATFORMS:
            results.append({"platform": pf, "ok": False, "error": "unknown platform"}); continue
        info = PLATFORMS[pf]
        if info["method"] == "session":
            results.append({"platform": pf, "ok": False, "error": "browser-session — run via Playwright runner"}); continue
        toks = cur.get(pf) or {}
        if not all(toks.get(f) for f in info["fields"]):
            results.append({"platform": pf, "ok": False, "error": "not connected"}); continue
        body_obj = PostBody(
            platform=pf, title=item.get("title") or "Servia",
            body=item.get("caption") or "",
            video_url=item.get("video_url"),
            tags=item.get("tags") or [])
        try:
            if   pf == "facebook": res = _post_facebook(toks, body_obj)
            elif pf == "twitter":  res = _post_twitter(toks, body_obj)
            elif pf == "linkedin": res = _post_linkedin(toks, body_obj)
            else:
                res = {"ok": False, "error": f"direct API for {pf} not yet implemented — saved tokens, manual share for now"}
        except Exception as e:  # noqa: BLE001
            res = {"ok": False, "error": str(e)}
        # Log to history same as single-post
        with db.connect() as c:
            try:
                c.execute("""CREATE TABLE IF NOT EXISTS social_posts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, platform TEXT,
                    title TEXT, body TEXT, video_url TEXT, post_url TEXT,
                    ok INTEGER, error TEXT, created_at TEXT)""")
            except Exception: pass
            c.execute("INSERT INTO social_posts(platform, title, body, video_url, post_url, ok, error, created_at) "
                      "VALUES(?,?,?,?,?,?,?,?)",
                      (pf, body_obj.title, body_obj.body, body_obj.video_url,
                       res.get("url"), 1 if res.get("ok") else 0, res.get("error"),
                       _dt.datetime.utcnow().isoformat() + "Z"))
        results.append({"platform": pf, **res})
    return {"ok": True, "results": results}
