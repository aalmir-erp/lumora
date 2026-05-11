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

    db.cfg('blog_image_provider') ∈ {'pollinations', 'svg'}
      pollinations → real image
      svg          → fallback to /api/blog/hero/<slug>.svg (the old behavior)

    Default: 'pollinations' (free, no key needed).
    """
    try:
        from . import db as _db
        provider = (_db.cfg_get("blog_image_provider", "pollinations") or "pollinations").lower()
    except Exception:
        provider = "pollinations"
    slug = post.get("slug") or ""
    if provider == "svg":
        return f"/api/blog/hero/{slug}.svg"
    return hero_image_url(
        slug,
        topic=post.get("topic"),
        emirate=post.get("emirate"),
        service=post.get("service_id"),
    )
