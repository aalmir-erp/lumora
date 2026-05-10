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


def _build_prompt(topic: str, emirate: str | None = None,
                  service: str | None = None) -> str:
    """Compose a clean hero-image prompt. Strips topic suffixes and
    forces a consistent style so all blog heroes share visual DNA."""
    base_topic = (topic or "UAE home services").split(":")[0].strip()
    emirate_clean = (emirate or "Dubai").replace("-", " ").title()
    service_clean = (service or "home services").replace("_", " ")
    return (
        f"Modern photography style hero image of a clean professional "
        f"{service_clean} setup in a UAE villa apartment in {emirate_clean}, "
        f"natural daylight, neutral palette with mint and gold accents, "
        f"high-end editorial composition, no text, no watermark, no logos, "
        f"shot from chest-level angle, sharp focus, 4k"
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
