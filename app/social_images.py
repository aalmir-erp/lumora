"""Social image generator + scheduler.

Mirror of videos.py but for static images. Generates per-aspect packs
optimised for each platform:

  1:1   → Instagram feed, Facebook, LinkedIn
  4:5   → Instagram portrait
  9:16  → TikTok / Reels / Stories / YouTube Shorts
  2:3   → Pinterest

Each image gets:
  - SEO title + description + alt text
  - public slug → /image/{slug} page indexed in sitemap
  - posted_to_* flags so we don't double-post
  - cron schedule: 10/day at 09:00 Asia/Dubai
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import hashlib
import json as _json
import random
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from . import db, kb
from .auth import require_admin


admin_router = APIRouter(prefix="/api/admin/social-images",
                         tags=["admin-social-images"],
                         dependencies=[Depends(require_admin)])
public_router = APIRouter(prefix="/api/social-images", tags=["public-social-images"])


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
def _ensure_table():
    with db.connect() as c:
        c.execute("""
          CREATE TABLE IF NOT EXISTS social_images(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            service_id TEXT, area TEXT, emirate TEXT,
            aspect TEXT,                                -- 1x1, 4x5, 9x16, 2x3
            prompt TEXT, model TEXT,                    -- generation provenance
            image_data_url TEXT,                        -- base64 PNG inline
            title TEXT, description TEXT, alt_text TEXT,
            view_count INTEGER DEFAULT 0,
            created_at TEXT,
            posted_facebook INTEGER DEFAULT 0,
            posted_instagram INTEGER DEFAULT 0,
            posted_tiktok INTEGER DEFAULT 0,
            posted_pinterest INTEGER DEFAULT 0,
            posted_linkedin INTEGER DEFAULT 0
          )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_si_created ON social_images(created_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_si_service ON social_images(service_id)")


# ---------------------------------------------------------------------------
# Best-of-breed prompt template (admin-overridable via cfg)
# ---------------------------------------------------------------------------
_DEFAULT_PROMPT_TEMPLATE = (
    "Eye-catching social-media post background for Servia (UAE home services brand). "
    "Subject: {service_pretty} happening in {area}. "
    "Style: photorealistic, warm natural light, golden-hour glow, premium-but-relatable. "
    "Show: real-looking UAE home interior or exterior — Dubai Marina apartment, "
    "Jumeirah villa, Sharjah townhouse — with subtle UAE cues (palm trees, majlis cushions, "
    "kandura silhouette in distance). NOT touristy stock photography. "
    "Color palette: warm whites + sand beige + teal accent (#0F766E) + gold sparkle. "
    "Composition: KEEP THE {text_side} 35% OF THE FRAME LARGELY EMPTY (clean negative space) "
    "so a bold headline + CTA button can be overlaid there cleanly. The empty area should "
    "have a soft uniform tone, no busy details, ready to host text. "
    "Mood: trustworthy, family-friendly, hopeful, makes the viewer think 'I want this for my home'. "
    "Avoid: cliched handshakes, fake smiles, awkward AI faces, stock-photo cleaning products, "
    "watermarks, signatures. "
    "Aspect: {aspect_label}. The image is a BACKGROUND that will be overlaid with logo + headline "
    "+ CTA — leave room for them on the {text_side} side."
)


_DEFAULT_TITLE_TEMPLATE = (
    "Write ONE social-media caption + ONE SEO title + ONE alt-text for an image of "
    "{service_pretty} in {area}, UAE.\n"
    "Reply STRICTLY as JSON: {{\"title\": \"...\", \"description\": \"...\", \"alt\": \"...\"}}.\n"
    "Rules:\n"
    "- title: 60-70 chars, includes service + area, ends with brand 'Servia'.\n"
    "- description: 140-180 chars, conversational, includes a CTA like 'Book on servia.ae', no emoji.\n"
    "- alt: 8-15 words, plain factual description for accessibility (e.g. 'Bright clean Dubai Marina apartment after deep cleaning').\n"
    "- NO em-dashes, NO semicolons, NO AI cliches (delve, comprehensive, leverage)."
)


# ---------------------------------------------------------------------------
# Image generation cascade — try Gemini Nano Banana → DALL-E 3 → Stability
# Variety is good for social: rotate models for different visual styles
# ---------------------------------------------------------------------------
IMAGE_PROVIDERS_BY_AESTHETIC = {
    "vibrant":    ("google_image", "gemini-2.5-flash-image"),
    "premium":    ("openai_image", "dall-e-3"),
    "fast":       ("fal_image",    "fal-ai/flux/schnell"),       # cheapest + fastest
    "balanced":   ("fal_image",    "fal-ai/flux/dev"),
    "flux_pro":   ("fal_image",    "fal-ai/flux-pro"),
    "grok":       ("xai_image",    "grok-2-image-1212"),
    "artistic":   ("stability",    "sd3.5-large"),
}


def _has_image_key(provider: str, cfg: dict) -> bool:
    """Image providers can use their own slot OR fall back to the matching
    text-provider key (Gemini key works for google_image, OpenAI key works
    for openai_image). Mirrors the fallback logic in ai_router.call_image_model."""
    keys = cfg.get("keys") or {}
    fallback = {"google_image": ["google_image", "google"],
                "openai_image": ["openai_image", "openai"],
                "xai_image":    ["xai_image", "xai"],
                "fal_image":    ["fal_image"],
                "stability":    ["stability"]}.get(provider, [provider])
    return any((keys.get(s) or "").strip() for s in fallback)


async def _gen_one_image(prompt: str, *, provider: str | None = None,
                         model: str | None = None) -> dict:
    """Cascade: try preferred → other configured providers. Returns
    {ok, image_data_url, model, latency_ms, ...}.

    Considers a provider 'configured' if EITHER its own key slot OR its
    text-counterpart's key is set — so admin only needs one Gemini /
    OpenAI key entry, not two."""
    from . import ai_router
    cfg = ai_router._load_cfg()
    chain: list[tuple[str, str]] = []
    if provider and model:
        chain.append((provider, model))
    # Add every image provider that has a key (or its text-counterpart's key)
    for name, mdl in IMAGE_PROVIDERS_BY_AESTHETIC.values():
        if (name, mdl) in chain: continue
        if _has_image_key(name, cfg): chain.append((name, mdl))
    if not chain:
        return {"ok": False, "error": (
            "No image-provider key configured. In admin → AI Arena set ANY of: "
            "Google AI (Gemini), OpenAI, or Stability AI. Same Google/OpenAI key "
            "you use for text generation works automatically."
        )}
    last_err = None
    for prov, mdl in chain:
        res = await ai_router.call_image_model(prov, mdl, prompt, cfg)
        if res.get("ok") and (res.get("image_data_url") or res.get("image_url")):
            return res
        last_err = res.get("error") or "no image returned"
    return {"ok": False, "error": last_err or "all image providers failed"}


# ---------------------------------------------------------------------------
# Build prompts — pulls live service + area pool, picks a random aesthetic
# ---------------------------------------------------------------------------
ASPECT_MAP = {
    "1x1":  ("1024x1024", "Square (Instagram feed / Facebook post)"),
    "4x5":  ("1024x1280", "Portrait 4:5 (Instagram in-feed)"),
    "9x16": ("1080x1920", "Vertical 9:16 (TikTok / Stories / Reels / Shorts)"),
    "2x3":  ("1024x1536", "Pinterest 2:3 (long pin)"),
}


AREA_POOL = [
    ("dubai", "Dubai Marina"), ("dubai", "Jumeirah"), ("dubai", "JLT"),
    ("dubai", "JVC"), ("dubai", "Mirdif"), ("dubai", "Business Bay"),
    ("dubai", "Downtown"), ("dubai", "Al Barsha"), ("dubai", "Discovery Gardens"),
    ("sharjah", "Al Khan"), ("sharjah", "Al Majaz"), ("sharjah", "Aljada"),
    ("sharjah", "Al Nahda Sharjah"), ("sharjah", "Muwaileh"),
    ("abu-dhabi", "Khalifa City"), ("abu-dhabi", "Al Reem Island"),
    ("abu-dhabi", "Yas Island"), ("abu-dhabi", "Saadiyat"),
    ("ajman", "Al Nuaimiya"), ("ajman", "Al Rashidiya"),
    ("ras-al-khaimah", "Al Hamra"), ("umm-al-quwain", "UAQ Marina"),
    ("fujairah", "Dibba"),
]


def _build_image_prompt(service_id: str, service_name: str, emirate: str,
                        area: str, aspect: str) -> str:
    """Compose the final image-gen prompt. Admin can override the template
    via cfg key 'social_image_prompt_template'."""
    tpl = (db.cfg_get("social_image_prompt_template", "")
           or _DEFAULT_PROMPT_TEMPLATE)
    text_side = random.choice(("left", "right", "bottom"))
    aspect_label = ASPECT_MAP.get(aspect, ("1024x1024", "Square"))[1]
    try:
        return tpl.format(
            service_id=service_id,
            service_pretty=service_name,
            area=area,
            emirate=emirate,
            aspect=aspect,
            aspect_label=aspect_label,
            text_side=text_side,
        )
    except Exception:
        return _DEFAULT_PROMPT_TEMPLATE.format(
            service_id=service_id, service_pretty=service_name, area=area,
            emirate=emirate, aspect=aspect, aspect_label=aspect_label,
            text_side=text_side)


async def _gen_seo_meta(service_name: str, area: str) -> dict:
    """Use the AI text cascade to write title + description + alt for this image."""
    from . import ai_router
    tpl = (db.cfg_get("social_image_title_template", "")
           or _DEFAULT_TITLE_TEMPLATE)
    prompt = tpl.format(service_pretty=service_name, area=area)
    try:
        res = await ai_router.call_with_cascade(prompt, persona="blog")
        if not res.get("ok"):
            return _meta_fallback(service_name, area)
        text = (res.get("text") or "").strip()
        if "```" in text:
            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
            if m: text = m.group(1)
        m = re.search(r"\{[^{}]*\}", text, re.S)
        if m: text = m.group(0)
        data = _json.loads(text)
        return {
            "title": (data.get("title") or "").strip()[:90],
            "description": (data.get("description") or "").strip()[:200],
            "alt": (data.get("alt") or "").strip()[:140],
        }
    except Exception:
        return _meta_fallback(service_name, area)


def _meta_fallback(service_name: str, area: str) -> dict:
    return {
        "title": f"{service_name} in {area}: book in 60 seconds | Servia",
        "description": (f"Trusted {service_name.lower()} for {area} homes. "
                        f"Book on servia.ae and get a vetted UAE pro at your door."),
        "alt": f"Servia {service_name.lower()} service in {area}, UAE",
    }


# ---------------------------------------------------------------------------
# Post-processing: composite the REAL Servia branding onto the AI background.
# AI image models still mangle text (especially small text), so we render
# headline + CTA + logo with PIL on top — pixel-perfect, every time.
# ---------------------------------------------------------------------------
def _overlay_branding(bg_data_url: str, *, headline: str, cta: str,
                       service_pretty: str, area: str,
                       text_side: str = "left") -> str | None:
    """Take an AI-generated image (base64 data URL), composite a translucent
    panel + headline + CTA + logo on top, return the new data URL.
    Returns None if anything fails — caller falls back to the raw image."""
    if not bg_data_url.startswith("data:image"):
        return None
    try:
        import base64, io
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        # Decode the AI background
        b64 = bg_data_url.split(",", 1)[1]
        bg = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGBA")
        W, H = bg.size

        # Translucent dark panel on the chosen side so text is always readable
        # regardless of the underlying photo
        panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        if text_side == "right":
            x0 = int(W * 0.55); x1 = W
        elif text_side == "bottom":
            x0 = 0; x1 = W
        else:                   # left
            x0 = 0; x1 = int(W * 0.55)
        if text_side == "bottom":
            y0 = int(H * 0.55); y1 = H
        else:
            y0 = 0; y1 = H
        # Soft gradient panel — deep at the edge, fading toward content
        for i in range(40):
            alpha = int(160 * (1 - i / 40))
            if text_side == "right":
                pd.rectangle([x0 - i, y0, x0 - i + 1, y1], fill=(15, 23, 42, alpha))
            elif text_side == "bottom":
                pd.rectangle([x0, y0 - i, x1, y0 - i + 1], fill=(15, 23, 42, alpha))
            else:
                pd.rectangle([x1 + i, y0, x1 + i + 1, y1], fill=(15, 23, 42, alpha))
        # Solid panel inside
        pd.rectangle([x0, y0, x1, y1], fill=(15, 23, 42, 170))
        bg = Image.alpha_composite(bg, panel)

        # Find the best system font available — fall back gracefully
        def _font(size: int, bold: bool = False) -> "ImageFont.FreeTypeFont":
            for fp in (
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                    else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ):
                try: return ImageFont.truetype(fp, size)
                except Exception: pass
            return ImageFont.load_default()

        draw = ImageDraw.Draw(bg)
        # Layout boundaries within the panel
        pad = int(min(W, H) * 0.04)
        tx0 = x0 + pad; tx1 = x1 - pad
        ty = y0 + pad

        # 1) Brand wordmark — real Servia teal-to-gold
        brand_font = _font(int(min(W, H) * 0.045), bold=True)
        draw.text((tx0, ty), "Servia", font=brand_font, fill=(252, 211, 77, 255))
        try:
            bbox = draw.textbbox((tx0, ty), "Servia", font=brand_font)
            ty = bbox[3] + int(min(W, H) * 0.015)
        except Exception:
            ty += int(min(W, H) * 0.06)

        # 2) Service tag
        tag_font = _font(int(min(W, H) * 0.022), bold=True)
        tag = service_pretty.upper() + " · " + area
        draw.text((tx0, ty), tag, font=tag_font, fill=(186, 230, 253, 230))
        ty += int(min(W, H) * 0.04)

        # 3) Headline — wrap to fit the panel width
        head_font_size = int(min(W, H) * 0.062)
        head_font = _font(head_font_size, bold=True)
        avail_w = tx1 - tx0
        # Greedy word-wrap
        words = (headline or "").split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            try:
                bbox = draw.textbbox((0, 0), test, font=head_font)
                if bbox[2] - bbox[0] <= avail_w:
                    cur = test
                else:
                    if cur: lines.append(cur)
                    cur = w
            except Exception:
                if len(test) * head_font_size * 0.55 <= avail_w: cur = test
                else:
                    if cur: lines.append(cur); cur = w
        if cur: lines.append(cur)
        for line in lines[:4]:
            draw.text((tx0, ty), line, font=head_font, fill=(255, 255, 255, 255))
            ty += int(head_font_size * 1.18)

        # 4) CTA button — solid teal pill near the bottom of the panel
        cta_text = (cta or "Book in 60s").upper()
        cta_font = _font(int(min(W, H) * 0.028), bold=True)
        try:
            ctx_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
            ctw = ctx_bbox[2] - ctx_bbox[0]; cth = ctx_bbox[3] - ctx_bbox[1]
        except Exception:
            ctw, cth = len(cta_text) * 14, 24
        cpad_x = int(min(W, H) * 0.025); cpad_y = int(min(W, H) * 0.018)
        cw = ctw + cpad_x * 2; chh = cth + cpad_y * 2
        cx0 = tx0
        cy0 = max(ty + int(min(W, H) * 0.025), y1 - chh - pad)
        # Pill shape via rectangles + circles
        try:
            draw.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + chh],
                                   radius=chh // 2, fill=(15, 118, 110, 255))
        except Exception:
            draw.rectangle([cx0, cy0, cx0 + cw, cy0 + chh], fill=(15, 118, 110, 255))
        draw.text((cx0 + cpad_x, cy0 + cpad_y - 2), cta_text,
                  font=cta_font, fill=(255, 255, 255, 255))

        # 5) Domain stamp under CTA
        dom_font = _font(int(min(W, H) * 0.022), bold=True)
        draw.text((cx0 + cw + int(min(W, H) * 0.015), cy0 + cpad_y + 2),
                  "servia.ae", font=dom_font, fill=(252, 211, 77, 255))

        # Save back as PNG data URL
        out = io.BytesIO()
        bg.convert("RGB").save(out, format="PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")
    except Exception as e:  # noqa: BLE001
        print(f"[social_images] overlay failed: {e}", flush=True)
        return None


# ---------------------------------------------------------------------------
# Generate one + save
# ---------------------------------------------------------------------------
async def generate_one(service_id: str, *, area: str | None = None,
                       emirate: str | None = None, aspect: str = "1x1",
                       model: str | None = None) -> dict:
    """Generate ONE social image. Returns {ok, slug, ...} or {ok:False, error}."""
    _ensure_table()
    services = {s["id"]: s for s in kb.services().get("services", [])}
    sv = services.get(service_id)
    if not sv:
        return {"ok": False, "error": f"unknown service '{service_id}'"}
    service_name = sv.get("name") or service_id
    if not area:
        em, ar = random.choice(AREA_POOL)
        emirate = emirate or em
        area = ar
    elif not emirate:
        emirate = "dubai"

    img_prompt = _build_image_prompt(service_id, service_name, emirate, area, aspect)

    # Resolve provider/model
    provider, mdl = (None, None)
    if model and "/" in model:
        provider, mdl = model.split("/", 1)
    elif model:
        # Random aesthetic if just a hint
        provider, mdl = IMAGE_PROVIDERS_BY_AESTHETIC.get(
            model, IMAGE_PROVIDERS_BY_AESTHETIC["vibrant"])
    res = await _gen_one_image(img_prompt, provider=provider, model=mdl)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "image gen failed"}
    image_data_url = res.get("image_data_url") or res.get("image_url") or ""

    # Generate SEO meta first — we use the title as the headline overlay
    meta = await _gen_seo_meta(service_name, area)

    # Headline = the AI-written title minus the brand suffix
    head = (meta["title"] or service_name).split("|")[0].split(":")[0].strip()
    if len(head) > 70:
        head = head[:70].rsplit(" ", 1)[0] + "…"
    cta = "Book in 60s →"
    text_side = random.choice(("left", "right", "bottom"))

    # Composite real branding + headline + CTA on top of the AI background.
    # Fixes 'plain AI image' problem: every post now has Servia logo + service +
    # area + headline + CTA pill + servia.ae domain stamp baked in pixel-perfect.
    branded = _overlay_branding(image_data_url, headline=head, cta=cta,
                                 service_pretty=service_name, area=area,
                                 text_side=text_side)
    if branded:
        image_data_url = branded
    slug = (
        service_id + "-" + area.lower().replace(" ", "-") + "-" + aspect + "-"
        + hashlib.sha1((service_id + area + aspect + str(_dt.datetime.utcnow().timestamp())).encode()).hexdigest()[:6]
    )[:80]
    now = _dt.datetime.utcnow().isoformat() + "Z"
    with db.connect() as c:
        c.execute(
            "INSERT INTO social_images(slug,service_id,area,emirate,aspect,"
            "prompt,model,image_data_url,title,description,alt_text,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (slug, service_id, area, emirate, aspect, img_prompt,
             f"{res.get('provider')}/{res.get('model')}", image_data_url,
             meta["title"], meta["description"], meta["alt"], now))
    db.log_event("social_image", slug, "generated", actor="admin",
                 details={"model": res.get("model"), "service": service_id, "area": area})
    return {"ok": True, "slug": slug, "title": meta["title"],
            "model": f"{res.get('provider')}/{res.get('model')}",
            "url": f"/image/{slug}"}


# ---------------------------------------------------------------------------
# Bulk generation: 100-pack at startup, 10/day on cron
# ---------------------------------------------------------------------------
_LIVE_STATUS = {"running": False, "step": "idle", "made": 0, "target": 0,
                "log": [], "errors": []}


def _push(msg: str, **kv):
    _LIVE_STATUS["log"].append({
        "ts": _dt.datetime.utcnow().isoformat() + "Z", "msg": msg,
    })
    _LIVE_STATUS["log"] = _LIVE_STATUS["log"][-100:]
    _LIVE_STATUS.update(kv)


async def generate_bulk(target: int = 100, mix_aspects: bool = True) -> dict:
    """Generate `target` social images across services / areas / aspects.
    Mixes models so the gallery has visual variety."""
    services = [s["id"] for s in kb.services().get("services", [])]
    if not services:
        return {"ok": False, "error": "no services configured"}
    aspects = ["1x1", "4x5", "9x16", "2x3"] if mix_aspects else ["1x1"]
    aesthetics = list(IMAGE_PROVIDERS_BY_AESTHETIC.keys())
    _LIVE_STATUS.update({"running": True, "step": "starting", "made": 0,
                         "target": target, "log": [], "errors": []})
    _push(f"🎨 Starting bulk gen: {target} images across {len(services)} services + {len(aspects)} aspects")
    made = 0
    for i in range(target):
        sid = services[i % len(services)]
        aspect = aspects[i % len(aspects)]
        # Cycle aesthetic so we get variety across providers
        aest_hint = aesthetics[i % len(aesthetics)]
        em, ar = random.choice(AREA_POOL)
        _push(f"  🎨 ({i+1}/{target}) {sid} · {ar} · {aspect} · {aest_hint}",
              step=f"making {i+1}/{target}")
        r = await generate_one(sid, area=ar, emirate=em, aspect=aspect, model=aest_hint)
        if r.get("ok"):
            made += 1
            _push(f"    ✓ saved as {r.get('slug')} via {r.get('model')}", made=made)
        else:
            _LIVE_STATUS["errors"].append(r.get("error", "unknown"))
            _push(f"    ✗ failed: {r.get('error')}")
        await asyncio.sleep(0.4)   # gentle pacing
    _push(f"✅ Done. {made}/{target} images created.", running=False, step="done")
    return {"ok": True, "made": made, "target": target}


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------
class GenerateOneBody(BaseModel):
    service_id: str
    area: str | None = None
    emirate: str | None = None
    aspect: str = "1x1"
    model: str | None = None


@admin_router.post("/generate")
async def admin_generate_one(body: GenerateOneBody):
    return await generate_one(body.service_id, area=body.area,
                               emirate=body.emirate, aspect=body.aspect,
                               model=body.model)


class BulkBody(BaseModel):
    target: int = 100
    mix_aspects: bool = True


@admin_router.post("/generate-bulk")
async def admin_generate_bulk(body: BulkBody):
    """100-pack starter generator. Runs in background — admin polls /status."""
    if _LIVE_STATUS.get("running"):
        raise HTTPException(409, "Another bulk gen is already running. Check /status.")
    if body.target > 200:
        raise HTTPException(400, "target capped at 200 to prevent runaway cost")
    asyncio.create_task(generate_bulk(body.target, body.mix_aspects))
    return {"ok": True, "background": True,
            "msg": f"Generating {body.target} images. Poll /api/admin/social-images/status."}


@admin_router.get("/status")
def get_status():
    return _LIVE_STATUS


@admin_router.get("/list")
def list_images(limit: int = 200, service_id: str | None = None):
    _ensure_table()
    where = []; params = []
    if service_id: where.append("service_id=?"); params.append(service_id)
    sql = ("SELECT id, slug, service_id, area, emirate, aspect, model, title, "
           "description, alt_text, prompt, view_count, created_at, "
           "posted_facebook, posted_instagram, posted_tiktok, posted_pinterest "
           "FROM social_images")
    if where: sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(min(limit, 500))
    with db.connect() as c:
        try: rows = c.execute(sql, params).fetchall()
        except Exception: rows = []
    return {"images": [db.row_to_dict(r) for r in rows], "count": len(rows)}


@admin_router.get("/get/{slug}")
def get_image(slug: str):
    """Return the full record for one image — drives the regen prompt editor."""
    _ensure_table()
    with db.connect() as c:
        try:
            r = c.execute(
                "SELECT slug, service_id, area, emirate, aspect, model, title, "
                "description, alt_text, prompt, created_at FROM social_images "
                "WHERE slug=?", (slug,)).fetchone()
        except Exception:
            r = None
    if not r: return {"ok": False, "error": "not found"}
    return {"ok": True, "image": db.row_to_dict(r)}


@admin_router.delete("/{slug}")
def delete_image(slug: str):
    _ensure_table()
    with db.connect() as c:
        n = c.execute("DELETE FROM social_images WHERE slug=?", (slug,)).rowcount
    return {"ok": True, "deleted": n}


# Prompt template editor
@admin_router.get("/prompt")
def get_prompt():
    return {
        "image_template": db.cfg_get("social_image_prompt_template", "") or "",
        "title_template": db.cfg_get("social_image_title_template", "") or "",
        "image_default": _DEFAULT_PROMPT_TEMPLATE,
        "title_default": _DEFAULT_TITLE_TEMPLATE,
        "placeholders_image": ["{service_id}", "{service_pretty}", "{area}",
                                "{emirate}", "{aspect}", "{aspect_label}", "{text_side}"],
        "placeholders_title": ["{service_pretty}", "{area}"],
    }


class PromptBody(BaseModel):
    image_template: str | None = None
    title_template: str | None = None


@admin_router.post("/prompt")
def set_prompt(body: PromptBody):
    if body.image_template is not None:
        db.cfg_set("social_image_prompt_template", body.image_template.strip())
    if body.title_template is not None:
        db.cfg_set("social_image_title_template", body.title_template.strip())
    return {"ok": True}


# Schedule toggle
@admin_router.get("/schedule")
def get_schedule():
    return {
        "enabled": bool(db.cfg_get("social_image_cron_enabled", True)),
        "daily_count": int(db.cfg_get("social_image_cron_daily", 10) or 10),
        "hour_dubai": int(db.cfg_get("social_image_cron_hour", 9) or 9),
    }


class ScheduleBody(BaseModel):
    enabled: bool | None = None
    daily_count: int | None = None
    hour_dubai: int | None = None


@admin_router.post("/schedule")
def set_schedule(body: ScheduleBody):
    if body.enabled is not None:
        db.cfg_set("social_image_cron_enabled", bool(body.enabled))
    if body.daily_count is not None:
        db.cfg_set("social_image_cron_daily", max(1, min(50, body.daily_count)))
    if body.hour_dubai is not None:
        db.cfg_set("social_image_cron_hour", max(0, min(23, body.hour_dubai)))
    return {"ok": True}


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------
@public_router.get("/list")
def public_list(limit: int = 60):
    _ensure_table()
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT slug, service_id, area, aspect, title, description, "
                "alt_text, view_count, created_at FROM social_images "
                "ORDER BY id DESC LIMIT ?", (min(limit, 200),)).fetchall()
        except Exception: rows = []
    return {"images": [db.row_to_dict(r) for r in rows]}


@public_router.get("/img/{slug}.png")
def public_image_bytes(slug: str):
    """Serve the image bytes (decoded from the data URL stored in DB)."""
    _ensure_table()
    with db.connect() as c:
        try:
            r = c.execute("SELECT image_data_url FROM social_images WHERE slug=?",
                          (slug,)).fetchone()
        except Exception: r = None
        if not r: raise HTTPException(404, "image not found")
    data_url = r["image_data_url"] or ""
    if data_url.startswith("data:"):
        try:
            import base64
            _, b64 = data_url.split(",", 1)
            png_bytes = base64.b64decode(b64)
            return Response(png_bytes, media_type="image/png",
                           headers={"Cache-Control": "public, max-age=86400"})
        except Exception:
            raise HTTPException(500, "image data corrupted")
    if data_url.startswith("http"):
        # External URL — redirect (used by some image providers)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(data_url)
    raise HTTPException(404, "no image data")


# Public per-image SEO page — title + description + image
def render_image_page(slug: str) -> str:
    _ensure_table()
    with db.connect() as c:
        try:
            r = c.execute("SELECT * FROM social_images WHERE slug=?",
                          (slug,)).fetchone()
        except Exception: r = None
        if not r: raise HTTPException(404, "image not found")
        # Bump view count
        try: c.execute("UPDATE social_images SET view_count=view_count+1 WHERE slug=?", (slug,))
        except Exception: pass
    d = dict(r)
    title = d.get("title") or "Servia social image"
    desc = d.get("description") or "UAE home services"
    alt = d.get("alt_text") or title
    sid = d.get("service_id") or ""
    area = d.get("area") or ""
    img_url = f"/api/social-images/img/{slug}.png"
    book_link = f"/book.html?service={sid}"
    import html as _h
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0F766E">
<title>{_h.escape(title)}</title>
<meta name="description" content="{_h.escape(desc)}">
<link rel="canonical" href="https://servia.ae/image/{slug}">
<meta property="og:title" content="{_h.escape(title)}">
<meta property="og:description" content="{_h.escape(desc)}">
<meta property="og:image" content="https://servia.ae{img_url}">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://servia.ae{img_url}">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"ImageObject",
"contentUrl":"https://servia.ae{img_url}",
"name":"{_h.escape(title)}",
"description":"{_h.escape(desc)}",
"caption":"{_h.escape(alt)}",
"datePublished":"{d.get('created_at','')}",
"author":{{"@type":"Organization","name":"Servia"}}}}
</script>
</head><body>
<nav class="nav"><div class="nav-inner">
  <a href="/"><img src="/logo.svg" height="36" alt="Servia"></a>
  <div class="nav-links" style="margin-inline-start:auto">
    <a href="/services.html">Services</a>
    <a href="/gallery.html">Gallery</a>
    <a href="/book.html">Book</a>
  </div>
</div></nav>
<main style="max-width:920px;margin:32px auto;padding:0 20px">
  <p style="font-size:12px;color:var(--muted)"><a href="/gallery.html" style="color:#0F766E">← back to gallery</a></p>
  <h1 style="font-size:30px;line-height:1.2;margin:8px 0 4px">{_h.escape(title)}</h1>
  <p style="color:var(--muted);font-size:14.5px;margin:0 0 16px">{_h.escape(desc)}</p>
  <img src="{img_url}" alt="{_h.escape(alt)}" loading="eager" fetchpriority="high"
    style="width:100%;height:auto;border-radius:14px;box-shadow:0 14px 40px rgba(15,23,42,.12);background:#F1F5F9">
  <div style="margin:18px 0 8px;font-size:13px;color:var(--muted)">
    <b style="color:#0F172A">{_h.escape(d.get('service_id','').replace('_',' ').title())}</b>
    · {_h.escape(area)} · {_h.escape(d.get('aspect',''))} · 👁 {d.get('view_count',0)} views
  </div>
  <a href="{book_link}" class="btn btn-primary" style="display:inline-block;padding:14px 28px;background:#0F766E;color:#fff;text-decoration:none;border-radius:999px;font-weight:700;margin-top:8px">
    Book this service in 60 seconds →
  </a>
</main>
</body></html>"""
