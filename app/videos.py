"""Servia mascot videos.

These are HTML5 'videos' — standalone pages with the Servia mascot SVG +
CSS keyframe animations + voiceover text overlay. They look like motion-
graphic explainer videos, no ffmpeg or external API needed.

Admin can:
  - View all videos in /admin (👀 Videos tab)
  - Generate new ones from a script via /api/admin/videos/generate (uses
    selected AI model from ai_router for the script)
  - Schedule auto-daily-video like the daily blog
"""
from __future__ import annotations

import datetime as _dt
import json as _json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import db
from .auth import require_admin


public_router = APIRouter(prefix="/api/videos", tags=["videos"])
admin_router = APIRouter(prefix="/api/admin/videos", tags=["admin-videos"],
                         dependencies=[Depends(require_admin)])


def _ensure_table():
    with db.connect() as c:
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS videos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE, title TEXT, mascot TEXT,
                tone TEXT, scenes_json TEXT,
                duration_sec INTEGER, view_count INTEGER DEFAULT 0,
                created_at TEXT)""")
        except Exception: pass


# ---------- 5 hand-crafted starter videos shipped with first deploy ----------
STARTER_VIDEOS = [
    {
        "slug": "welcome-to-servia",
        "title": "Hi 👋 — meet Servia",
        "mascot": "default",
        "tone": "teal",
        "duration_sec": 18,
        "scenes": [
            {"text": "Hi, I'm Servia 👋", "sub": "Your UAE concierge",       "anim": "wave"},
            {"text": "Need a service?",   "sub": "I've got 32 of them",       "anim": "point"},
            {"text": "Booked in 60s",     "sub": "Same-day across UAE",       "anim": "bounce"},
            {"text": "Pay only when slot is locked.", "sub": "Apple Pay · Google Pay · Card", "anim": "shake"},
            {"text": "Tap. Book. Done.",  "sub": "Try me on servia.ae",       "anim": "wave"},
        ],
    },
    {
        "slug": "book-in-60-seconds",
        "title": "How to book in 60 seconds",
        "mascot": "ac",
        "tone": "amber",
        "duration_sec": 22,
        "scenes": [
            {"text": "Step 1 · Pick a service", "sub": "AC · cleaning · pest · handyman", "anim": "point"},
            {"text": "Step 2 · Pick a slot",    "sub": "Same-day if booked before 11am", "anim": "bounce"},
            {"text": "Step 3 · Pay to confirm", "sub": "Apple Pay · Google Pay · Card · Tabby", "anim": "shake"},
            {"text": "Step 4 · Pro on the way", "sub": "Live ETA on WhatsApp every 5 min", "anim": "wave"},
            {"text": "Step 5 · All done.",      "sub": "Photos · invoice · 7-day re-do guarantee", "anim": "wave"},
        ],
    },
    {
        "slug": "ac-pre-summer-prep",
        "title": "AC pre-summer prep — Servia",
        "mascot": "ac",
        "tone": "purple",
        "duration_sec": 16,
        "scenes": [
            {"text": "UAE summer = 45°C", "sub": "Your AC runs 14h a day",       "anim": "shake"},
            {"text": "Skip a service?",   "sub": "Compressor failure costs AED 1,200+", "anim": "point"},
            {"text": "Servia AC service", "sub": "from AED 75 / unit · 90 min",   "anim": "bounce"},
            {"text": "Book this week",    "sub": "Slots disappearing fast",       "anim": "wave"},
        ],
    },
    {
        "slug": "deep-clean-feel",
        "title": "Deep cleaning that just works",
        "mascot": "cleaning",
        "tone": "green",
        "duration_sec": 20,
        "scenes": [
            {"text": "✨ Top-to-bottom deep clean", "sub": "Bathrooms · kitchens · floors · windows", "anim": "wave"},
            {"text": "2 cleaners · 4-6 hours",      "sub": "Supplies + equipment included", "anim": "point"},
            {"text": "from AED 350",                "sub": "Studio – 4 BR · transparent pricing", "anim": "bounce"},
            {"text": "AED 25,000 damage cover",     "sub": "Background-checked · insured", "anim": "shake"},
            {"text": "7-day re-do guarantee.",      "sub": "Not happy? We come back free.", "anim": "wave"},
        ],
    },
    {
        "slug": "ambassador-tier-ladder",
        "title": "Refer & climb — Servia Ambassador",
        "mascot": "default",
        "tone": "rose",
        "duration_sec": 18,
        "scenes": [
            {"text": "Refer a friend",        "sub": "They both get a discount",       "anim": "point"},
            {"text": "🥉 Bronze · 5% off",     "sub": "0–2 referrals",                 "anim": "bounce"},
            {"text": "🥈 Silver · 10% off",   "sub": "3–5 referrals",                 "anim": "bounce"},
            {"text": "🥇 Gold · 15% off",      "sub": "6–10 referrals",                "anim": "bounce"},
            {"text": "💎 Platinum · 20% off",  "sub": "11+ referrals · forever",       "anim": "wave"},
        ],
    },
]


def seed_videos_if_empty():
    _ensure_table()
    with db.connect() as c:
        try:
            n = c.execute("SELECT COUNT(*) AS n FROM videos").fetchone()["n"]
        except Exception:
            n = 0
    if n >= 5: return
    now = _dt.datetime.utcnow().isoformat() + "Z"
    with db.connect() as c:
        for v in STARTER_VIDEOS:
            try:
                c.execute(
                    "INSERT OR IGNORE INTO videos(slug, title, mascot, tone, scenes_json, duration_sec, created_at) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (v["slug"], v["title"], v["mascot"], v["tone"],
                     _json.dumps(v["scenes"]), v["duration_sec"], now))
            except Exception: pass


# ---------- HTML/SVG video player ----------
TONE_GRADIENTS = {
    "teal":   ("#0F766E", "#14B8A6"),
    "amber":  ("#B45309", "#F59E0B"),
    "purple": ("#5B21B6", "#7C3AED"),
    "rose":   ("#9F1239", "#E11D48"),
    "green":  ("#065F46", "#15803D"),
    "blue":   ("#1E40AF", "#3B82F6"),
}


def render_video_html(v: dict) -> str:
    a, b = TONE_GRADIENTS.get(v.get("tone") or "teal", TONE_GRADIENTS["teal"])
    scenes = v["scenes"]
    n = len(scenes)
    per = max(2.5, v.get("duration_sec", 18) / n)
    total = per * n
    # Build N scene divs with staggered animation-delay
    scene_html = []
    for i, s in enumerate(scenes):
        anim = s.get("anim") or "wave"
        scene_html.append(
            f'<div class="scene scene-{anim}" style="animation-delay:{i*per:.2f}s">'
            f'  <div class="scene-text">{s["text"]}</div>'
            f'  <div class="scene-sub">{s["sub"]}</div>'
            f'</div>')
    mascot_src = "/mascot.svg" if v.get("mascot","default") == "default" else f"/mascots/{v['mascot']}.svg"
    title = v.get("title", "Servia")
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Servia video</title>
<style>
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:#0F172A; min-height:100vh; display:flex; align-items:center; justify-content:center; }}
.video {{ position:relative; width:min(720px, 95vw); aspect-ratio: 16/9;
  background:linear-gradient(135deg,{a},{b}); border-radius:14px;
  box-shadow:0 24px 60px rgba(0,0,0,.4); overflow:hidden; color:#fff; }}
.video::before {{ content:""; position:absolute; inset:0;
  background-image: radial-gradient(circle at 20% 30%, rgba(255,255,255,.18) 0%, transparent 30%),
                    radial-gradient(circle at 80% 70%, rgba(255,255,255,.10) 0%, transparent 30%);
  pointer-events:none; }}
.brand {{ position:absolute; top:18px; left:20px; font-weight:800; font-size:14px;
  letter-spacing:.2em; text-transform:uppercase; opacity:.85; z-index:2; }}
.duration {{ position:absolute; top:18px; right:20px; font-size:11px;
  background:rgba(0,0,0,.18); padding:4px 8px; border-radius:999px; z-index:2; }}

.mascot-wrap {{ position:absolute; left:6%; bottom:8%; width:42%; height:80%;
  display:flex; align-items:flex-end; justify-content:center; z-index:2; }}
.mascot {{ width:100%; height:100%; object-fit:contain;
  filter: drop-shadow(0 8px 18px rgba(0,0,0,.35));
  animation: mascot-bob 3.4s ease-in-out infinite; }}
@keyframes mascot-bob {{ 0%,100% {{ transform: translateY(0) }} 50% {{ transform: translateY(-12px) }} }}

.scene-stack {{ position:absolute; right:6%; top:50%; transform:translateY(-50%);
  width:46%; max-width:420px; z-index:2; }}
.scene {{ position:absolute; left:0; right:0; top:0;
  opacity:0; transform:translateY(16px);
  animation: scene-fade {total}s linear infinite; }}
.scene-text {{ font-size:28px; font-weight:800; letter-spacing:-.01em;
  line-height:1.15; margin-bottom:8px; text-shadow:0 2px 6px rgba(0,0,0,.25); }}
.scene-sub {{ font-size:14px; opacity:.92; line-height:1.4;
  background:rgba(0,0,0,.18); display:inline-block; padding:5px 10px;
  border-radius:999px; backdrop-filter:blur(4px); }}

@keyframes scene-fade {{
  0%   {{ opacity:0; transform:translateY(16px) }}
  {(per*0.18/total*100):.1f}% {{ opacity:1; transform:translateY(0) }}
  {(per*0.85/total*100):.1f}% {{ opacity:1; transform:translateY(0) }}
  {(per/total*100):.1f}% {{ opacity:0; transform:translateY(-16px) }}
  100% {{ opacity:0; transform:translateY(-16px) }}
}}

/* Per-anim mascot flourishes */
.scene-wave   ~ .mascot-wrap .mascot {{ animation-name: mascot-bob }}
.scene-bounce ~ .mascot-wrap .mascot {{ animation: mascot-bounce 1.2s ease-in-out infinite }}
.scene-shake  ~ .mascot-wrap .mascot {{ animation: mascot-shake .8s ease-in-out infinite }}
.scene-point  ~ .mascot-wrap .mascot {{ animation: mascot-tilt 2.4s ease-in-out infinite }}
@keyframes mascot-bounce {{ 0%,100% {{ transform: translateY(0) scale(1) }} 50% {{ transform: translateY(-22px) scale(1.04) }} }}
@keyframes mascot-shake  {{ 0%,100% {{ transform: rotate(0) }} 25% {{ transform: rotate(-3deg) }} 75% {{ transform: rotate(3deg) }} }}
@keyframes mascot-tilt   {{ 0%,100% {{ transform: rotate(0) }} 50% {{ transform: rotate(8deg) translateX(8px) }} }}

.cta {{ position:absolute; bottom:14px; right:20px;
  background:#FCD34D; color:#7C2D12; padding:8px 16px; border-radius:999px;
  font-weight:800; font-size:13px; text-decoration:none;
  box-shadow:0 6px 18px rgba(0,0,0,.25); z-index:3; }}
.progress {{ position:absolute; left:0; bottom:0; right:0; height:3px;
  background:rgba(0,0,0,.18); z-index:3; }}
.progress::after {{ content:""; display:block; height:100%; width:0;
  background:#FCD34D; animation: progress {total}s linear infinite; }}
@keyframes progress {{ 0% {{ width:0 }} 100% {{ width:100% }} }}

@media (max-width:560px) {{
  .scene-stack {{ width:48%; max-width:none }}
  .scene-text {{ font-size:20px }}
  .scene-sub {{ font-size:12px }}
}}
</style>
</head>
<body>
<div class="video" role="img" aria-label="{title}">
  <div class="brand">SERVIA</div>
  <div class="duration">{int(v.get('duration_sec',18))}s · loop</div>
  <div class="scene-stack">
    {''.join(scene_html)}
  </div>
  <div class="mascot-wrap">
    <img class="mascot" src="{mascot_src}" alt="Servia mascot">
  </div>
  <a class="cta" href="https://servia.ae/book.html">Book on servia.ae →</a>
  <div class="progress"></div>
</div>
</body></html>"""


# ---------- public endpoints ----------
@public_router.get("/list")
def list_videos_public():
    seed_videos_if_empty()
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT slug, title, mascot, tone, duration_sec, view_count "
                "FROM videos ORDER BY id DESC LIMIT 50").fetchall()
        except Exception: rows = []
    return {"videos": [db.row_to_dict(r) for r in rows]}


@public_router.get("/play/{slug}", response_class=HTMLResponse)
def play_video(slug: str):
    seed_videos_if_empty()
    with db.connect() as c:
        try:
            r = c.execute("SELECT * FROM videos WHERE slug=?", (slug,)).fetchone()
        except Exception: r = None
    if not r:
        raise HTTPException(404, "Video not found")
    v = db.row_to_dict(r) or {}
    try: v["scenes"] = _json.loads(v.get("scenes_json") or "[]")
    except Exception: v["scenes"] = []
    with db.connect() as c:
        try: c.execute("UPDATE videos SET view_count=view_count+1 WHERE slug=?", (slug,))
        except Exception: pass
    return HTMLResponse(render_video_html(v))


# ---------- admin endpoints ----------
class GenerateBody(BaseModel):
    topic: str
    mascot: Optional[str] = "default"
    tone: Optional[str] = "teal"
    target_seconds: Optional[int] = 18


@admin_router.get("/list")
def list_videos_admin():
    seed_videos_if_empty()
    return list_videos_public()


@admin_router.post("/generate")
async def generate_video(body: GenerateBody):
    """Use the configured AI router to script a new mascot video.
    The model returns 4-6 scenes as JSON, we save it."""
    from . import ai_router
    cfg = ai_router._load_cfg()
    target = (cfg.get("defaults") or {}).get("video", "anthropic/claude-opus-4-7")
    if "/" not in target:
        target = "anthropic/" + target
    provider, model = target.split("/", 1)
    prompt = (
        "You write Servia mascot-video scripts. Servia is a UAE home-services platform.\n"
        f"Topic: {body.topic}\n"
        "Output a JSON array of 4 to 5 scenes. Each scene has: 'text' (max 36 chars, "
        "punchy headline), 'sub' (max 60 chars, supporting line), 'anim' (one of "
        "'wave', 'bounce', 'shake', 'point').\n"
        "Style: friendly, concrete UAE context, real numbers, no AI mannerisms. "
        "Use AED prices if relevant. End with a CTA-style scene.\n"
        "Output ONLY the JSON array, no markdown, no commentary."
    )
    res = await ai_router.call_model(provider, model, prompt, cfg)
    if not res.get("ok"):
        raise HTTPException(400, res.get("error") or "model call failed")
    txt = (res.get("text") or "").strip()
    # Extract JSON
    if "```" in txt:
        import re as _re
        m = _re.search(r"```(?:json)?\s*(\[.*?\])\s*```", txt, _re.S)
        if m: txt = m.group(1)
    if "[" in txt and "]" in txt:
        txt = txt[txt.index("["): txt.rindex("]") + 1]
    try:
        scenes = _json.loads(txt)
        assert isinstance(scenes, list) and len(scenes) >= 3
    except Exception:
        raise HTTPException(500, f"Could not parse model output: {txt[:200]}")

    slug = "ai-" + "".join(c.lower() if c.isalnum() else "-" for c in body.topic).strip("-")[:80]
    slug = slug + "-" + _dt.datetime.utcnow().strftime("%H%M%S")
    title = body.topic[:120]
    duration = body.target_seconds or 18
    seed_videos_if_empty()
    with db.connect() as c:
        try:
            c.execute(
                "INSERT INTO videos(slug, title, mascot, tone, scenes_json, duration_sec, created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (slug, title, body.mascot or "default", body.tone or "teal",
                 _json.dumps(scenes), duration,
                 _dt.datetime.utcnow().isoformat() + "Z"))
        except Exception as e:
            raise HTTPException(500, f"db insert failed: {e}")
    return {"ok": True, "slug": slug, "title": title, "scenes": scenes,
            "model": target, "url": f"/api/videos/play/{slug}"}


@admin_router.delete("/{slug}")
def delete_video(slug: str):
    with db.connect() as c:
        c.execute("DELETE FROM videos WHERE slug=?", (slug,))
    return {"ok": True}
