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
