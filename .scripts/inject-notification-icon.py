#!/usr/bin/env python3
"""Generate proper ic_notification_icon.png for the TWA APK.

Bubblewrap's auto-generated notification icon uses the full app icon (the
rounded-square one), so when Android tints it to a flat white silhouette
for the status bar, the result is a solid white square — that's the
"white box" the founder kept seeing in the top bar next to the time/signal.

The fix: use the mascot source (transparent background, mascot-only shape)
and write it out as a clean white silhouette at all 5 Android drawable
densities (mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi). Android then renders the
actual mascot shape in the status bar.

Run AFTER bubblewrap init, BEFORE gradle build, against the generated
project root.

Usage:
    python3 .scripts/inject-notification-icon.py <generated_project_dir>
"""
from __future__ import annotations
import sys
from pathlib import Path
from PIL import Image

# Source: mascot (transparent BG) — NOT the icon (rounded-square BG).
ROOT = Path(__file__).resolve().parent.parent
MASCOT = ROOT / "web" / "brand" / "servia-mascot-1024x1024.png"

# Android drawable density sizes for the notification status-bar icon.
# Status bar icons are 24dp tall, so the resource is sized by density.
DENSITIES = {
    "drawable-mdpi":    24,
    "drawable-hdpi":    36,
    "drawable-xhdpi":   48,
    "drawable-xxhdpi":  72,
    "drawable-xxxhdpi": 96,
}


def make_silhouette(src: Image.Image, size: int) -> Image.Image:
    """Resize source mascot to size x size and convert every visible pixel
    to white while keeping the original alpha intact."""
    im = src.convert("RGBA").resize((size, size), Image.LANCZOS)
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            # Anywhere with any alpha → opaque white. Below 24 (very faint
            # edge) → fully transparent so the silhouette has clean edges.
            px[x, y] = (255, 255, 255, 255 if a >= 24 else 0)
    return im


def main(generated_dir: str) -> int:
    project = Path(generated_dir)
    res = project / "app" / "src" / "main" / "res"
    if not res.exists():
        print(f"ERROR: {res} not found — did bubblewrap init succeed?")
        return 2
    if not MASCOT.exists():
        print(f"ERROR: mascot source missing at {MASCOT}")
        return 2

    src = Image.open(MASCOT)
    print(f"Source: {MASCOT.name} ({src.size[0]}x{src.size[1]})")

    written = 0
    for density, size in DENSITIES.items():
        out_dir = res / density
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "ic_notification_icon.png"
        silhouette = make_silhouette(src, size)
        silhouette.save(out_path, optimize=True)
        print(f"  ✓ {density}/{out_path.name} ({size}x{size}, {out_path.stat().st_size}B)")
        written += 1

    print(f"Replaced {written} ic_notification_icon.png files with proper mascot silhouette.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: inject-notification-icon.py <generated_project_dir>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
