#!/usr/bin/env python3
"""Generate an informative 1024×500 Play Store feature graphic for Servia.

Matches the brand "Ziina avatar v4" style — mascot ball on a teal gradient
with white kandura silhouette, plus 4 quick-value icons + tagline +
trust badges. Output: web/brand/play-assets/feature-graphic-1024x500.png

Usage:
    python3 .scripts/generate-play-feature-graphic.py
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "web" / "brand"
OUT = BRAND / "play-assets"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1024, 500


def font(size, bold=False):
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    try:
        return ImageFont.truetype(p, size)
    except Exception:
        return ImageFont.load_default()


def efont(size):
    """Unifont — supports emoji glyphs that DejaVu lacks."""
    try:
        return ImageFont.truetype("/usr/share/fonts/opentype/unifont/unifont_upper.otf", size)
    except Exception:
        return font(size)


def gradient_bg(w, h, start=(15, 118, 110), end=(20, 184, 166)):
    """Vertical teal gradient (servia brand)."""
    bg = Image.new("RGB", (w, h), start)
    d = ImageDraw.Draw(bg)
    for y in range(h):
        t = y / h
        r = int(start[0] + (end[0] - start[0]) * t)
        g = int(start[1] + (end[1] - start[1]) * t)
        b = int(start[2] + (end[2] - start[2]) * t)
        d.line([(0, y), (w, y)], fill=(r, g, b))
    return bg


def text_with_shadow(d, xy, text, fill, fnt, anchor="lm", shadow=(0, 0, 0, 180), offset=2):
    sx, sy = xy[0] + offset, xy[1] + offset
    d.text((sx, sy), text, fill=shadow, font=fnt, anchor=anchor)
    d.text(xy, text, fill=fill, font=fnt, anchor=anchor)


def draw_card_chip(d, x, y, w, h, icon, text, sub):
    """Rounded card with emoji icon + title + subtitle."""
    # Rounded rect background (frosted glass effect with alpha)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle((0, 0, w - 1, h - 1), radius=18,
                         fill=(255, 255, 255, 60),
                         outline=(255, 255, 255, 120), width=2)
    return overlay  # caller alpha-composites onto bg


def build():
    bg = gradient_bg(W, H).convert("RGBA")

    # Decorative dots (UAE-flag yellow + white)
    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    for cx, cy, r, fill in [
        (210,  72, 10, (252, 211, 77, 180)),
        (480, 380, 8,  (252, 211, 77, 120)),
        (720,  50, 7,  (255, 255, 255, 140)),
        (60,  300, 12, (255, 255, 255, 80)),
        (920, 200, 8,  (252, 211, 77, 160)),
        (340, 460, 6,  (255, 255, 255, 100)),
    ]:
        dd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)
    bg = Image.alpha_composite(bg, deco)

    # --- Mascot ball (left side) ---
    try:
        mascot = Image.open(BRAND / "servia-icon-1024x1024.png").convert("RGBA")
        # Crop the central circle out of the rounded square icon
        mw, mh = mascot.size
        # The mascot icon already has its own background; we shrink + place on left
        # Resize to ~320px ball
        ball = mascot.resize((320, 320), Image.LANCZOS)
        bg.paste(ball, (40, 90), ball)
    except Exception as e:
        print(f"(no mascot found: {e})")

    d = ImageDraw.Draw(bg)

    # --- Main title (center-right) ---
    title_x = 400
    text_with_shadow(d, (title_x, 60),
                     "Servia", (255, 255, 255), font(72, True))
    text_with_shadow(d, (title_x, 130),
                     "UAE home services", (252, 211, 77), font(34, True))
    text_with_shadow(d, (title_x, 168),
                     "in 60 seconds.", (252, 211, 77), font(34, True))

    # --- Service chips (2x2 grid) ---
    chips = [
        ("🧹", "Deep Cleaning",   "from AED 290"),
        ("🔧", "Plumber + AC",    "24/7 booking"),
        ("🆘", "SOS Recovery",    "18-min response"),
        ("📲", "Tap NFC + Watch", "one-touch booking"),
    ]
    cx, cy = title_x, 230
    cw, ch = 290, 78
    gap = 16
    for i, (icon, title, sub) in enumerate(chips):
        row, col = i // 2, i % 2
        x = cx + col * (cw + gap)
        y = cy + row * (ch + 14)
        # Rounded glass background
        overlay = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=14,
                             fill=(15, 23, 42, 90),
                             outline=(252, 211, 77, 160), width=2)
        bg.paste(overlay, (x, y), overlay)
        # Icon
        od2 = ImageDraw.Draw(bg)
        od2.text((x + 16, y + ch // 2), icon, fill=(252, 211, 77, 255),
                 font=efont(34), anchor="lm")
        # Title + sub
        od2.text((x + 64, y + 18), title, fill=(255, 255, 255), font=font(20, True))
        od2.text((x + 64, y + 46), sub,   fill=(226, 232, 240), font=font(15))

    # --- Bottom contact strip ---
    strip = Image.new("RGBA", (W, 36), (15, 23, 42, 200))
    sd = ImageDraw.Draw(strip)
    sd.text((W // 2, 18),
            "servia.ae  ·  WhatsApp  ·  hello@servia.ae",
            fill=(252, 211, 77), font=font(18, True), anchor="mm")
    bg.paste(strip, (0, H - 36), strip)

    # --- UAE flag accent bar (3px under the strip) ---
    flag = Image.new("RGBA", (W, 3), (0, 0, 0, 0))
    fd = ImageDraw.Draw(flag)
    seg = W // 4
    fd.rectangle((0,         0, seg,       3), fill=(0, 115, 47, 255))   # green
    fd.rectangle((seg,       0, 2 * seg,   3), fill=(255, 255, 255, 255))# white
    fd.rectangle((2 * seg,   0, 3 * seg,   3), fill=(0, 0, 0, 255))      # black
    fd.rectangle((3 * seg,   0, W,         3), fill=(255, 0, 0, 255))    # red
    bg.paste(flag, (0, H - 3), flag)

    # Save final
    bg.convert("RGB").save(OUT / "feature-graphic-1024x500.png",
                            optimize=True, quality=92)
    print(f"✓ wrote {OUT / 'feature-graphic-1024x500.png'} "
          f"({(OUT / 'feature-graphic-1024x500.png').stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
