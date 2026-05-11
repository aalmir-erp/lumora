# Servia brand reference

**Authority:** Founder-supplied screenshots stored in `web/brand/reference/`.
Anyone editing Servia visual assets MUST review these before changing the
logo, colour palette, mascot, or hero treatment. See CLAUDE.md **rule W15**.

## Reference files (do not delete)

| File | What it shows |
|---|---|
| `reference/logo-canonical-1-with-blessing.jpg` | Full logo with Arabic blessing + tagline |
| `reference/logo-canonical-2-with-blessing-star.jpg` | Full logo with star accent above "i" |
| `reference/logo-canonical-3-with-blessing-no-tagline.jpg` | Compact logo with Arabic blessing only |
| `reference/homepage-mobile.jpg` | Live mobile homepage hero design |
| `reference/homepage-desktop.jpg` | Live desktop homepage hero design |

## Canonical logo elements

```
1. Icon (rounded gradient square)
   - Soft UAE-flag halo ribbon on the LEFT edge (green / white / black / red)
   - Mint→deeper-teal gradient body
   - Inner teal circle frame
   - White "S" letterform, geometric, centred
   - Small gold sparkle at the upper-right of the icon

2. Arabic blessing "إن شاء الله" (Insha'Allah)
   - Colour: brand gold (#F59E0B)
   - Position: centred ABOVE the wordmark
   - Optional on very-compact versions (header logo at < 120px wide)

3. Wordmark "Servia"
   - "Serv" in brand TEAL (#0F766E)
   - "ia"   in brand GOLD (#F59E0B)
   - Small gold star/dot above the "i" of "ia"
   - Gold underline-curl flourish below the wordmark

4. Tagline "YOUR UAE FIX-IT IN 60 SECONDS"
   - Colour: dark teal (#134E4A)
   - Letter-spacing: wide
   - Optional on very-compact versions
```

## Brand colour palette

| Role | Hex | Notes |
|---|---|---|
| Primary teal | `#0F766E` | "Serv" wordmark, primary buttons, dark backgrounds |
| Deeper teal | `#134E4A` | Tagline, dark hero |
| Mint teal | `#14B8A6` | Gradient endpoint, lighter accents |
| Soft mint | `#5EEAD4` | Light backgrounds |
| Brand gold | `#F59E0B` | "ia" wordmark, Arabic blessing, CTAs |
| Light gold | `#FCD34D` | Sparkles, hover states |
| UAE green | `#00732F` | Flag accents |
| UAE red | `#EF4444` / `#FF0000` | Flag accents |
| Slate dark | `#0F172A` | Body text on light backgrounds |

## Canonical SVG files

| File | Use case |
|---|---|
| `servia-logo-full.svg` | Marketing / Ziina / large brand placements (with Arabic + tagline) |
| `../logo.svg` | Compact header nav (no Arabic blessing, smaller footprint) |
| `../mascot.svg` | Mascot character (waving, with cap and apron) |
| `../avatar.svg` | Smaller avatar variant |

## Mascot

The Servia mascot is a friendly round-faced character with:
- Yellow / cream face
- White service-cap
- White apron / coat with a "SERVIA" name badge
- Both hands visible (one waving)
- Always rendered on a teal circular background

When the mascot is rasterised, **strip the multilingual speech bubble** —
the rotating "Hi / مرحبا / السلام / नमस्ते / Kumusta" cycle in mascot.svg
flattens to overlapping gibberish in static images.

## Pre-shaping Arabic for non-shaping renderers (cairosvg, PIL)

cairosvg and PIL do not perform Arabic letter shaping. When embedding
Arabic text in a rasterised brand asset, pre-shape it first:

```python
import arabic_reshaper
from bidi.algorithm import get_display
from arabic_reshaper.reshaper_config import auto_config

cfg = auto_config(configuration={"support_ligatures": False})
reshaper = arabic_reshaper.ArabicReshaper(configuration=cfg)
shaped = reshaper.reshape("إن شاء الله")
display = get_display(shaped)
# display is now 'ﻪﻠﻟﺍ ﺀﺎﺷ ﻥﺇ' — paste this into the SVG <text> directly
```

Setting `support_ligatures=False` avoids the Allah-ligature glyph
(U+FDF2) that's missing from cairosvg's default font.
