#!/usr/bin/env python3
"""Generate proper 384×384 PNG tile previews for the Wear OS tile picker.

Samsung's Galaxy Watch picker (and Wear OS 5 in general) silently filters
out tiles whose `androidx.wear.tiles.PREVIEW` metadata points at a drawable
XML — only PNG/JPEG bitmaps are accepted. We generate one PNG per tile,
each ~6 KB, then drop them into twa/android/wear/res-drawable/.

Output: tile_preview_<id>.png at 384×384.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "twa" / "android" / "wear" / "res-drawable"
OUT.mkdir(parents=True, exist_ok=True)

TILES = [
    # (filename_id, bg_color_rgb, label_top, label_big, label_sub, accent_rgb)
    ("tile_preview_voice",       (245, 158,  11),  "🎙 SERVIA",      "TALK",       "Speak to book",       (15, 23, 42)),
    ("tile_preview_sos",         (220,  38,  38),  "🆘 SERVIA SOS",  "TAP",        "8 services",          (252, 211, 77)),
    ("tile_preview_book",        ( 15, 118, 110),  "📋 SERVIA",      "BOOK",       "Quick services",      (252, 211, 77)),
    ("tile_preview_furniture",   (124,  58, 237),  "📦 FURNITURE",   "MOVE",       "Movers · fixers",     (252, 211, 77)),
    ("tile_preview_electrician", (251, 191,  36),  "🔌 ELECTRIC",    "POWER",      "Servia electrician",  (15, 23, 42)),
    ("tile_preview_plumber",     ( 14, 165, 233),  "🚿 PLUMBER",     "FIX",        "Leak · clog",         (255, 255, 255)),
    ("tile_preview_ac",          (  6, 182, 212),  "❄️ SERVIA AC",   "COOL",       "Not cooling",         (15, 23, 42)),
    ("tile_preview_handyman",    ( 22, 163,  74),  "🔧 HANDYMAN",    "FIX IT",     "Paint · door",        (255, 255, 255)),
]


def font_at(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    for p in candidates:
        try: return ImageFont.truetype(p, size)
        except Exception: pass
    return ImageFont.load_default()


def make_tile(filename, bg, top, big, sub, accent):
    out = OUT / f"{filename}.png"
    img = Image.new("RGBA", (384, 384), bg + (255,))
    d = ImageDraw.Draw(img)
    # Subtle vignette
    vignette = Image.new("L", (384, 384), 0)
    vd = ImageDraw.Draw(vignette)
    for r in range(380, 200, -2):
        a = int(60 * (1 - (r - 200) / 180))
        vd.ellipse([(192-r//2, 192-r//2), (192+r//2, 192+r//2)], fill=255-a)
    img.putalpha(vignette)
    img2 = Image.new("RGB", (384, 384), bg)
    img2.paste(img.convert("RGB"), mask=img.split()[3])
    d = ImageDraw.Draw(img2)
    # Top label
    d.text((192, 80), top, fill=accent, font=font_at(22, True), anchor="mm")
    # Big text
    d.text((192, 192), big, fill=accent, font=font_at(58, True), anchor="mm")
    # Sub text
    d.text((192, 280), sub, fill=accent, font=font_at(20, False), anchor="mm")
    # Bottom-right "Servia" lockup
    d.text((192, 340), "servia", fill=accent, font=font_at(16, True), anchor="mm")
    img2.save(out, optimize=True)
    print(f"  ✓ {out.name}  ({out.stat().st_size} bytes)")


def main():
    print(f"Generating tile previews into {OUT}")
    for t in TILES:
        make_tile(*t)
    # Also generate a generic launcher icon variant the manifest can use as
    # android:icon for each service (must be a small bitmap-style icon, not
    # a coloured circle XML).
    base = Image.open(ROOT / "web" / "brand" / "servia-icon-512x512.png").convert("RGBA")
    for size in (96, 144, 192):
        out = OUT / f"wear_tile_icon_{size}.png"
        base.resize((size, size), Image.LANCZOS).save(out, optimize=True)
        print(f"  ✓ {out.name}  ({size}×{size}, {out.stat().st_size}B)")
    print("\nDone. Re-build the Wear APK to include these in res/drawable/.")


if __name__ == "__main__":
    main()
