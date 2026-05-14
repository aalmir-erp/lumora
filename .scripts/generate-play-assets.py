#!/usr/bin/env python3
"""Generate Play Store assets (feature graphic, screenshots, Wear OS round
images) from existing brand + recovery photos.

Outputs to web/brand/play-assets/ — consumed when uploading to Google Play
Console.

Usage:
    python3 .scripts/generate-play-assets.py
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "web" / "brand"
RECOVERY = ROOT / "web" / "img" / "recovery"
OUT = BRAND / "play-assets"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "phone").mkdir(exist_ok=True)
(OUT / "wear").mkdir(exist_ok=True)

# -- Helper: load fonts (DejaVu is shipped with Linux) -----------------------
def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def text_with_shadow(d, xy, text, fill, fnt, anchor="lm", shadow=(0, 0, 0, 180), offset=2):
    sx, sy = xy[0] + offset, xy[1] + offset
    d.text((sx, sy), text, fill=shadow, font=fnt, anchor=anchor)
    d.text(xy, text, fill=fill, font=fnt, anchor=anchor)


# ============================================================================
# 1. Feature graphic — 1024×500 (mandatory for Play Store)
# ============================================================================
def feature_graphic():
    out = OUT / "feature-graphic-1024x500.png"
    burj = Image.open(RECOVERY / "burj-tap.png").convert("RGB")
    # Crop the photo to a 1024x500 section (top-left band has the truck)
    w, h = burj.size
    target_aspect = 1024 / 500
    src_aspect = w / h
    if src_aspect > target_aspect:
        new_w = int(h * target_aspect)
        off = (w - new_w) // 2
        crop = burj.crop((off, 0, off + new_w, h))
    else:
        new_h = int(w / target_aspect)
        off = (h - new_h) // 2
        crop = burj.crop((0, off, w, off + new_h))
    crop = crop.resize((1024, 500), Image.LANCZOS)

    # Darken left side for headline space
    overlay = Image.new("RGBA", (1024, 500), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(0, 580):
        alpha = int(180 * (1 - x / 580))
        od.line([(x, 0), (x, 500)], fill=(15, 23, 42, alpha))
    img = crop.convert("RGBA")
    img = Image.alpha_composite(img, overlay).convert("RGB")

    d = ImageDraw.Draw(img)
    text_with_shadow(d, (40, 70),  "SERVIA", (252, 211, 77), font(60, True))
    text_with_shadow(d, (40, 150), "UAE home services", (255, 255, 255), font(38, True))
    text_with_shadow(d, (40, 200), "in 60 seconds", (255, 255, 255), font(38, True))
    text_with_shadow(d, (40, 280), "🆘  ONE-TAP RECOVERY", (252, 211, 77), font(28, True))
    text_with_shadow(d, (40, 320), "Tap once · GPS sent · Truck on the way", (226, 232, 240), font(22))
    text_with_shadow(d, (40, 360), "AED 250 · 18-min response · 24/7 UAE-wide", (226, 232, 240), font(22))
    text_with_shadow(d, (40, 440), "servia.ae · +971 52 363 3995", (252, 211, 77), font(20, True))

    img.save(out, optimize=True, quality=92)
    print(f"✓ {out.name}")


# ============================================================================
# 2. App icon variants (already exist as 512/1024/2048; just copy 512 over)
# ============================================================================
def app_icon():
    src = BRAND / "servia-icon-512x512.png"
    if src.exists():
        out = OUT / "app-icon-512x512.png"
        Image.open(src).save(out)
        print(f"✓ {out.name}")


# ============================================================================
# 3. Phone screenshots — 1080×1920 portrait (8 frames)
#    We use the recovery photos + add a phone-frame overlay style.
# ============================================================================
def phone_screenshots():
    frames = [
        ("01-hero",      "Tap once. Recovery on the way.",       "AED 250 · 18-min UAE response", RECOVERY / "burj-tap.png"),
        ("02-truck",     "Yellow Servia truck dispatched.",      "Vendor name + phone instantly", RECOVERY / "scene-mercedes.png"),
        ("03-split",     "Stranded? Servia closes the gap.",     "GPS auto-sent · WhatsApp ETA",   RECOVERY / "hero-split.png"),
        ("04-multi",     "8 services · one tap.",                 "Recovery · Chauffeur · Plumber · Electrician · AC · Handyman · Cleaning · Furniture", RECOVERY / "campaign-grid.png"),
        ("05-panic",     "Step-by-step in any emergency.",       "Panic + tap → fast arrival",     RECOVERY / "panic-ad.png"),
    ]
    for stem, head, sub, src in frames:
        out = OUT / "phone" / f"{stem}.png"
        if not src.exists(): continue
        bg = Image.open(src).convert("RGB")
        # Resize to fill 1080x1920
        bw, bh = bg.size
        ratio = max(1080 / bw, 1920 / bh)
        bg = bg.resize((int(bw * ratio), int(bh * ratio)), Image.LANCZOS)
        ox = (bg.size[0] - 1080) // 2
        oy = (bg.size[1] - 1920) // 2
        bg = bg.crop((ox, oy, ox + 1080, oy + 1920))
        # Top dark gradient for headline
        ov = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for y in range(0, 480):
            a = int(200 * (1 - y / 480))
            od.line([(0, y), (1080, y)], fill=(15, 23, 42, a))
        # Bottom dark band
        for y in range(1500, 1920):
            a = int(200 * ((y - 1500) / 420))
            od.line([(0, y), (1080, y)], fill=(15, 23, 42, a))
        img = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
        d = ImageDraw.Draw(img)
        text_with_shadow(d, (54, 100),  "SERVIA", (252, 211, 77), font(58, True))
        # Headline (wrap)
        max_w = 980
        words = head.split()
        line, y = "", 200
        for w in words:
            t = (line + " " + w).strip()
            bbox = d.textbbox((0, 0), t, font=font(60, True))
            if bbox[2] - bbox[0] > max_w:
                text_with_shadow(d, (54, y), line, (255, 255, 255), font(60, True))
                y += 70
                line = w
            else:
                line = t
        if line:
            text_with_shadow(d, (54, y), line, (255, 255, 255), font(60, True))
        # Sub
        sub_y = 1700
        text_with_shadow(d, (54, sub_y), sub, (252, 211, 77), font(34, True))
        text_with_shadow(d, (54, sub_y + 60), "servia.ae · 24/7 UAE-wide", (226, 232, 240), font(28))
        img.save(out, optimize=True, quality=88)
        print(f"✓ {out.relative_to(OUT)}")


# ============================================================================
# 4. Wear OS round screenshots — 384×384 (1 frame per tile)
# ============================================================================
def wear_screenshots():
    tiles = [
        ("01-voice",     (245, 158, 11), "🎙",  "TALK", "Speak: book / quote / SOS"),
        ("02-sos",       (220, 38, 38),  "🆘",  "SOS",  "Vehicle recovery · GPS sent"),
        ("03-furniture", (124, 58, 237), "📦",  "MOVE", "Furniture · 1 tap"),
        ("04-electric",  (251, 191, 36), "🔌",  "POWER", "Electrician on the way"),
        ("05-plumber",   (14, 165, 233), "🚿",  "PLUMB", "Plumber dispatched"),
        ("06-ac",        (6, 182, 212),  "❄️",  "COOL", "AC technician on the way"),
        ("07-handyman",  (22, 163, 74),  "🔧",  "FIX",  "Handyman dispatched"),
        ("08-quickbook", (15, 118, 110), "📋",  "BOOK", "Deep clean · AC · Maid"),
    ]
    for stem, color, emoji, big, sub in tiles:
        out = OUT / "wear" / f"{stem}.png"
        img = Image.new("RGB", (384, 384), (15, 23, 42))
        d = ImageDraw.Draw(img)
        # Round colored center
        d.ellipse([(20, 20), (364, 364)], fill=color)
        # SERVIA on top (small)
        text_with_shadow(d, (192, 70), "SERVIA", (252, 211, 77), font(20, True), anchor="mm")
        # Big text
        text_with_shadow(d, (192, 170), big, (255, 255, 255), font(60, True), anchor="mm")
        # Sub
        text_with_shadow(d, (192, 250), sub, (15, 23, 42), font(18, True), anchor="mm")
        # Emoji watermark (top-left small)
        d.text((192, 120), emoji, fill=(255, 255, 255), font=font(36, True), anchor="mm")
        img.save(out, optimize=True)
        print(f"✓ {out.relative_to(OUT)}")


# ============================================================================
# 5. Listing copy
# ============================================================================
def listing_copy():
    short = "Servia · UAE home services in 60 seconds · 24/7 SOS recovery"
    full = """Servia is the UAE's first one-tap home-services platform. From a stranded car to a leaking sink to a maid who shows up on time, Servia connects you to vetted local pros in seconds — across all 7 emirates.

🆘 ONE-TAP SOS DISPATCH
• Vehicle recovery — battery, tyre, fuel, lock-out, tow
• Chauffeur — airport, hotel, late-night
• Furniture move + assembly — small van or full truck
• Handyman — wall paint, door, curtains, TV mount
• Plumber — leaks, clogs, water heater
• Electrician — no power, breakers, sockets, fans
• AC fix + clean — gas top-up, deep service, leak fix
• Cleaning — deep clean, maid hourly, sofa & carpet

⚡ HOW IT WORKS
1. Pick a service · 2. We send your real GPS · 3. Closest Servia partner is dispatched · 4. You see vendor name + phone instantly · 5. WhatsApp tracking link · 6. Pay only when satisfied (7-day re-do guarantee).

📲 NFC TAGS
Stick a Servia NFC sticker on your dashboard, kitchen, AC unit, or front door. Tap once → Servia opens with the right service pre-filled.

⌚ WEAR OS COMPANION
Servia for Wear OS lets you book by voice from your wrist:
• Mic-first chat with text-to-speech replies
• 6 SOS tiles (vehicle, furniture, electrician, plumber, AC, handyman) — tap once, GPS sent, vendor in seconds
• Real bookings linked to your Servia account so they appear in /account.html

🛡 TRUSTED ACROSS THE UAE
• 4.9★ from 2,400+ UAE families
• Vetted, insured, English-speaking pros
• AED 25,000 damage cover on every service
• 7-day re-do guarantee — pay only when satisfied
• Apple Pay · Google Pay · Card · Tabby · Wallet

🇦🇪 UAE-WIDE COVERAGE
Dubai (200+ areas), Abu Dhabi (80+), Sharjah (60+), Ajman, RAK, UAQ, Fujairah, Al Ain.

🔒 PRIVACY-FIRST
Servia uses your precise GPS only when you tap SOS or Book. No background tracking, no resale, no third-party ads. The NFC tag is passive — no battery, no GPS, no broadcast — your phone shares its location only when you actively tap.

🌐 servia.ae · 💬 WhatsApp · 📧 hello@servia.ae"""

    (OUT / "short-description.txt").write_text(short)
    (OUT / "full-description.txt").write_text(full)
    print("✓ short-description.txt + full-description.txt")


if __name__ == "__main__":
    feature_graphic()
    app_icon()
    phone_screenshots()
    wear_screenshots()
    listing_copy()
    print("\nAll Play Store assets generated to web/brand/play-assets/")
