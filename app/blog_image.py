"""v1.24.98 — Auto-generated hero images for autoblog posts.

Founder reported "we decided automatically image generation will also be
happening when none of these are working". Previously /api/blog/hero/{slug}.svg
returned a static SVG mascot scene, not a real image.

This module returns a Pollinations.ai URL — free, no API key, generates
1024×768 images on-demand from a prompt derived from the blog topic.
Fallback to the existing SVG mascot if Pollinations rate-limits or the
admin sets `blog_image_provider` to "svg".

Why Pollinations:
  - Zero cost, zero auth (genuine no-key API)
  - Cached at the edge by Pollinations
  - Stable Diffusion XL backend, decent quality for blog heroes
  - Switchable: when DALL-E 3 / Stability AI keys are available the
    admin can flip blog_image_provider via /admin → AI Arena

What this is NOT:
  - A magic high-quality designer. Pollinations output is good-enough
    for SEO blog heroes, not Times-of-India quality.
  - On-server image storage. Images live at Pollinations CDN. If they
    delete cached versions, our /blog/{slug} page just regenerates by
    re-fetching the same URL (deterministic seed).

W8 audit: existing /api/blog/hero/{slug}.svg endpoint returns SVG via
blog_render.hero_svg_for_slug(). This module provides a parallel
hero_image_url(slug, topic) that returns a real-image URL. Caller
(blog_render or template) decides which to embed based on
db.cfg('blog_image_provider').
"""
from __future__ import annotations

import urllib.parse


# Pollinations.ai endpoint. Format:
#   https://image.pollinations.ai/prompt/<url-encoded-prompt>?width=W&height=H&nologo=true&seed=N
# Deterministic seed = hash(slug) so the same article always gets the
# same image (good for caching + branding consistency).
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"


# v1.24.103 — service-specific prompt vocab so the hero image actually
# shows uniformed workers doing THE WORK, not generic interiors.
# Founder: "use real images of services being performed along with
# our employees doing that service professionally".
_SERVICE_VERBS = {
    "deep_cleaning":     "professional cleaner in mint-green branded uniform wiping down a kitchen counter with microfiber cloth and spray bottle, before-and-after spotless surface",
    "general_cleaning":  "uniformed home cleaner mopping a marble floor in a modern UAE living room",
    "ac_cleaning":       "HVAC technician in mint uniform on a step-ladder unscrewing a split AC unit cover, vacuum hose and spray bottle visible, ladder, professional tool kit on floor",
    "pest_control":      "pest-control technician in protective gear with backpack sprayer treating skirting boards in a UAE villa kitchen, professional tool belt",
    "sofa_carpet":       "uniformed cleaner using a steam-cleaning machine on a fabric sofa in a UAE living room, foam visible, mint-branded equipment",
    "maid_service":      "smiling housekeeper in mint uniform folding fresh laundry in a sunlit UAE bedroom",
    "laundry":           "delivery rider in mint uniform handing a sealed laundry bag to a customer at a UAE villa door",
    "handyman":          "handyman in mint branded uniform installing a wall shelf with a power drill in a modern UAE apartment",
    "plumbing":          "plumber in mint uniform under a kitchen sink with pipe wrench and torch, organized tool kit on tile floor",
    "ac_repair":         "AC technician in mint uniform with multimeter checking outdoor compressor unit on a UAE villa balcony",
    "ac_installation":   "two AC technicians in mint uniforms mounting a split AC indoor unit on a wall, ladder, drill, tool kit",
    "marble_polish":     "floor specialist with rotary polisher buffing a marble floor in a UAE villa hallway",
    "curtain_cleaning":  "uniformed worker steaming long curtains hanging in a UAE living room with floor-to-ceiling windows",
    "car_wash":          "car-wash technician in mint uniform foaming a luxury sedan in a UAE villa driveway, microfiber cloths, professional pressure washer",
    "swimming_pool":     "pool-service technician in mint uniform skimming a sparkling private pool in a UAE villa, test kit and pole on poolside",
    "gardening":         "gardener in mint uniform pruning hedges in a UAE villa garden, wheelbarrow with tools",
    "painting":          "painter in mint uniform on a step-ladder rolling fresh white paint on a UAE living-room wall, drop cloth on floor",
    "window_cleaning":   "window-cleaner in mint uniform squeegeeing a tall floor-to-ceiling window in a UAE apartment, bucket and microfiber visible",
    "babysitting":       "smiling certified nanny reading a picture book to two children on a UAE living-room rug",
    "smart_home":        "smart-home installer in mint uniform mounting a smart switch on a UAE wall, tablet showing app on coffee table",
    "move_in_out":       "two cleaners in mint uniforms with industrial steam cleaners doing move-out clean of empty UAE apartment",
    "villa_deep":        "team of three cleaners in mint uniforms scrubbing a UAE villa kitchen and bathrooms",
    "kitchen_deep":      "cleaner in mint uniform degreasing a UAE kitchen extractor hood with foam and brush",
    "gym_deep_cleaning": "industrial cleaner in mint uniform sanitising gym equipment in a UAE residential gym",
    "school_deep_cleaning": "cleaning crew in mint uniforms disinfecting a UAE school classroom",
    "commercial_cleaning": "commercial cleaning crew in mint uniforms vacuuming and wiping a Dubai office reception",
}


def _build_prompt(topic: str, emirate: str | None = None,
                  service: str | None = None) -> str:
    """Compose a service-specific documentary-realism prompt.

    v1.24.108 — founder feedback: previous output looked too magazine-shoot,
    too polished, obviously AI-generated. Rewrote to push SD-XL hard toward
    candid documentary photography:
      - "shot on iPhone 15 Pro" tames the SD-XL polish bias
      - "amateur photography" + "candid" reduces composed-looking poses
      - "no makeup, natural skin texture, slight wear on uniform"
        breaks the uncanny-perfect-skin SD-XL tell
      - "fluorescent indoor light" + "no bokeh" kills the cinematic look
      - "real product brands visible (generic spray bottle, plastic bucket)"
        anchors the scene in reality
    NOTE: Pollinations.ai is still SD-XL and will sometimes produce
    AI-looking results no matter what we prompt. For truly realistic
    images, install a Pexels API key (Bug 35 fix in v1.24.109).
    """
    emirate_clean = (emirate or "Dubai").replace("-", " ").title()
    sid = (service or "deep_cleaning").lower()
    verb = _SERVICE_VERBS.get(sid, _SERVICE_VERBS["deep_cleaning"])
    return (
        f"Candid documentary photograph, {verb}, "
        f"shot on iPhone 15 Pro by someone walking past, "
        f"caught mid-action not posed, "
        f"natural fluorescent indoor lighting (no bokeh, no soft golden hour), "
        f"slight motion blur, "
        f"realistic skin texture with normal pores, no makeup, "
        f"uniform shows light wear (slight wrinkles, real fabric), "
        f"generic mass-market tools and spray bottles (no fancy brands), "
        f"UAE residential apartment in {emirate_clean}, "
        f"unstaged, looks like a quick photo for a WhatsApp status update, "
        f"no text, no watermark, no logos, no brand names, "
        f"amateur photography, slightly off-centre composition, 35mm"
    )


def _seed_from_slug(slug: str) -> int:
    """Stable 32-bit seed from slug. Same slug → same image forever."""
    h = 0
    for ch in (slug or "default"):
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h


def hero_image_url(slug: str, topic: str | None = None,
                   emirate: str | None = None,
                   service: str | None = None,
                   width: int = 1024, height: int = 768) -> str:
    """Return a Pollinations.ai URL for the hero image of this post.
    Direct embed in <img src=...> — Pollinations renders + serves."""
    prompt = _build_prompt(topic or slug.replace("-", " "), emirate, service)
    encoded = urllib.parse.quote(prompt, safe="")
    seed = _seed_from_slug(slug)
    qs = f"?width={width}&height={height}&nologo=true&seed={seed}"
    return f"{POLLINATIONS_BASE}{encoded}{qs}"


def hero_url_for_post(post: dict) -> str:
    """Convenience: takes a post dict (slug, topic, emirate, service_id)
    and returns the right URL based on admin config.

    Precedence:
      1. If admin has generated a real hero via /admin → Auto-blog →
         Regen hero (stored in autoblog_hero_images table), serve THAT
         from /api/blog/hero-png/<slug>.png. Best quality — uses the
         user's own Gemini/OpenAI keys via the social-image cascade.
      2. Else `blog_image_provider` cfg:
           pollinations → free SD-XL via Pollinations (default)
           svg          → static SVG mascot scene
    """
    slug = post.get("slug") or ""
    # Check for an admin-generated stored hero first
    try:
        from . import db as _db
        with _db.connect() as c:
            row = c.execute(
                "SELECT 1 FROM autoblog_hero_images WHERE slug=? LIMIT 1",
                (slug,)).fetchone()
            if row:
                return f"/api/blog/hero-png/{slug}.png"
    except Exception:
        pass
    try:
        from . import db as _db
        provider = (_db.cfg_get("blog_image_provider", "pollinations") or "pollinations").lower()
    except Exception:
        provider = "pollinations"
    if provider == "svg":
        return f"/api/blog/hero/{slug}.svg"
    return hero_image_url(
        slug,
        topic=post.get("topic"),
        emirate=post.get("emirate"),
        service=post.get("service_id"),
    )


def _ensure_hero_table():
    """Stores admin-regenerated blog hero images (PNG bytes) so we can
    serve them at /api/blog/hero-png/<slug>.png without external deps."""
    try:
        from . import db as _db
        with _db.connect() as c:
            c.execute("""
              CREATE TABLE IF NOT EXISTS autoblog_hero_images(
                slug         TEXT PRIMARY KEY,
                prompt       TEXT,
                image_bytes  BLOB,
                provider     TEXT,
                model        TEXT,
                created_at   TEXT
              )""")
    except Exception:
        pass


def get_default_prompt_for_post(post: dict) -> str:
    """Return the prompt we would use by default — admin can edit and
    submit a custom one via /api/admin/blog/<slug>/regenerate-hero."""
    return _build_prompt(
        topic=post.get("topic") or (post.get("slug") or "").replace("-", " "),
        emirate=post.get("emirate"),
        service=post.get("service_id"),
    )


async def regenerate_hero(slug: str, *, prompt: str | None = None,
                          post: dict | None = None) -> dict:
    """Generate a real AI hero image using the same cascade as social images
    (Google AI / OpenAI / fal.ai / xAI / Stability — whichever keys admin set).

    On success: stores PNG bytes in autoblog_hero_images so
    hero_url_for_post() will return /api/blog/hero-png/<slug>.png going
    forward. Returns {ok, provider, model, prompt} on success or
    {ok:false, error} on failure.

    Falls back to nothing (admin gets the error). The post will keep
    using Pollinations until a regen succeeds.
    """
    _ensure_hero_table()
    from . import social_images as _si, db as _db
    import base64, io, datetime as _dt
    if not prompt:
        if post is None:
            try:
                with _db.connect() as c:
                    row = c.execute(
                        "SELECT slug, topic, emirate, service_id "
                        "FROM autoblog_posts WHERE slug=?",
                        (slug,)).fetchone()
                    post = dict(row) if row else {"slug": slug}
            except Exception:
                post = {"slug": slug}
        prompt = get_default_prompt_for_post(post)
    res = await _si._gen_one_image(prompt)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "image cascade failed"}
    data_url = res.get("image_data_url") or ""
    image_url = res.get("image_url") or ""
    img_bytes: bytes | None = None
    if data_url.startswith("data:image"):
        try:
            img_bytes = base64.b64decode(data_url.split(",", 1)[1])
        except Exception:
            img_bytes = None
    elif image_url:
        # Some providers (e.g. fal.ai) return a URL — fetch the bytes
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as cx:
                r = await cx.get(image_url)
                if r.status_code == 200:
                    img_bytes = r.content
        except Exception:
            img_bytes = None
    if not img_bytes:
        return {"ok": False, "error": "image generated but bytes unavailable"}
    # Re-encode to PNG (some providers return JPEG) so /hero-png/*.png is honest
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        buf = io.BytesIO(); im.save(buf, format="PNG"); img_bytes = buf.getvalue()
    except Exception:
        pass  # Keep original bytes if Pillow misbehaves
    try:
        with _db.connect() as c:
            c.execute(
                "INSERT OR REPLACE INTO autoblog_hero_images"
                "(slug, prompt, image_bytes, provider, model, created_at) "
                "VALUES(?,?,?,?,?,?)",
                (slug, prompt, img_bytes,
                 res.get("provider") or "?", res.get("model") or "?",
                 _dt.datetime.utcnow().isoformat() + "Z"))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"db write failed: {e}"}
    return {"ok": True, "provider": res.get("provider"),
            "model": res.get("model"), "prompt": prompt,
            "url": f"/api/blog/hero-png/{slug}.png"}


def get_hero_bytes(slug: str) -> tuple[bytes, str] | None:
    """Return (bytes, content_type) for a stored hero, or None if missing."""
    _ensure_hero_table()
    try:
        from . import db as _db
        with _db.connect() as c:
            row = c.execute(
                "SELECT image_bytes FROM autoblog_hero_images WHERE slug=?",
                (slug,)).fetchone()
            if row and row["image_bytes"]:
                return bytes(row["image_bytes"]), "image/png"
    except Exception:
        pass
    return None


def get_hero_meta(slug: str) -> dict | None:
    """Return prompt / provider / model / created_at for a stored hero."""
    _ensure_hero_table()
    try:
        from . import db as _db
        with _db.connect() as c:
            row = c.execute(
                "SELECT prompt, provider, model, created_at "
                "FROM autoblog_hero_images WHERE slug=?",
                (slug,)).fetchone()
            return dict(row) if row else None
    except Exception:
        return None
