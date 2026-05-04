"""Branded staff portraits — generate friendly stylised SVG illustrations of
Servia staff in branded uniform + cap, performing service-specific actions.

Each portrait shows a smiling staff member doing the relevant work, with
the Servia branding (teal/amber colours + 'SERVIA' chest patch + cap).
Several skin tones / face shapes / accessories rotated by deterministic
seed so each service / area / page combo gets a different person.
"""
from __future__ import annotations

import hashlib
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()


# Colour palettes (skin, hair, uniform) — diverse cast representing UAE workforce
SKINS = ["#FCD34D", "#F4A460", "#D2A37D", "#A0786C", "#8B5A3C", "#FBBF77", "#E1B589"]
HAIRS = ["#1F2937", "#3B2519", "#5C2E0F", "#0F172A", "#2D1B0E"]
CAPS  = ["#0F766E", "#0D9488", "#115E59", "#1D4ED8"]
APRONS= ["#0F766E", "#F59E0B", "#7C3AED", "#0EA5E9", "#15803D", "#E11D48"]


# Per-service action overlay — what the staff is doing
SERVICE_ACTIONS = {
    "ac_service":         "ac",
    "ac_cleaning":        "ac",
    "deep_cleaning":      "cleaning",
    "general_cleaning":   "cleaning",
    "villa_deep":         "cleaning",
    "kitchen_deep":       "cleaning",
    "kitchen_deep_clean": "cleaning",
    "move_in_out":        "cleaning",
    "move_in_out_cleaning":"cleaning",
    "office_cleaning":    "cleaning",
    "post_construction":  "cleaning",
    "disinfection":       "cleaning",
    "maid_service":       "maid",
    "babysitting":        "maid",
    "handyman":           "handyman",
    "smart_home":         "handyman",
    "painting":           "handyman",
    "pest_control":       "pest",
    "sofa_carpet":        "cleaning",
    "carpet_cleaning":    "cleaning",
    "window_cleaning":    "cleaning",
    "curtain_cleaning":   "cleaning",
    "marble_polish":      "cleaning",
    "swimming_pool":      "pool",
    "car_wash":           "car",
    "gardening":          "garden",
    "laundry":            "maid",
}


def _seed(s: str) -> int:
    return int(hashlib.md5((s or "default").encode()).hexdigest()[:8], 16)


def _action_overlay(action: str) -> str:
    """SVG overlay showing the service-specific tool/object the staff holds."""
    OVR = {
        "ac": '''
  <!-- AC unit being serviced -->
  <rect x="290" y="80" width="180" height="44" rx="6" fill="#fff" stroke="#94A3B8" stroke-width="2"/>
  <line x1="298" y1="92"  x2="462" y2="92"  stroke="#94A3B8" stroke-width="1.5"/>
  <line x1="298" y1="100" x2="462" y2="100" stroke="#94A3B8" stroke-width="1.5"/>
  <line x1="298" y1="108" x2="462" y2="108" stroke="#94A3B8" stroke-width="1.5"/>
  <text x="380" y="160" text-anchor="middle" font-size="22">❄️</text>
  <text x="350" y="170" font-size="18">❄️</text>
  <text x="410" y="170" font-size="18">❄️</text>
  <!-- screwdriver in hand -->
  <rect x="330" y="290" width="6" height="36" rx="2" fill="#475569"/>
  <rect x="328" y="282" width="10" height="12" rx="2" fill="#FCD34D"/>''',
        "cleaning": '''
  <!-- spray bottle + cloth -->
  <rect x="430" y="270" width="22" height="34" rx="4" fill="#0EA5E9"/>
  <rect x="436" y="262" width="10" height="10" rx="2" fill="#475569"/>
  <text x="395" y="270" font-size="18">✨</text>
  <text x="450" y="245" font-size="14">💧</text>
  <text x="380" y="240" font-size="14">💧</text>
  <!-- mop in left hand -->
  <line x1="190" y1="280" x2="160" y2="350" stroke="#92400E" stroke-width="4" stroke-linecap="round"/>
  <ellipse cx="155" cy="356" rx="20" ry="6" fill="#FCD34D"/>''',
        "maid": '''
  <!-- folded laundry basket -->
  <rect x="370" y="320" width="120" height="60" rx="6" fill="#FCD34D" stroke="#92400E" stroke-width="2"/>
  <rect x="380" y="306" width="100" height="14" rx="3" fill="#7C3AED"/>
  <rect x="386" y="294" width="88" height="12" rx="3" fill="#0EA5E9"/>
  <text x="430" y="290" text-anchor="middle" font-size="22">👕</text>''',
        "handyman": '''
  <!-- toolbox + wrench -->
  <rect x="340" y="320" width="120" height="50" rx="6" fill="#475569"/>
  <rect x="380" y="306" width="40" height="18" rx="4" fill="#1F2937"/>
  <text x="400" y="356" text-anchor="middle" font-size="22" fill="#FCD34D">🔧</text>
  <!-- wrench in hand -->
  <line x1="180" y1="280" x2="220" y2="240" stroke="#1F2937" stroke-width="5" stroke-linecap="round"/>
  <circle cx="220" cy="240" r="8" fill="#475569"/>''',
        "pest": '''
  <!-- spray pack on back + nozzle -->
  <rect x="170" y="180" width="40" height="60" rx="6" fill="#15803D"/>
  <rect x="178" y="195" width="24" height="16" rx="2" fill="#fff"/>
  <line x1="210" y1="200" x2="280" y2="180" stroke="#0F172A" stroke-width="3"/>
  <text x="285" y="180" font-size="14">💨</text>
  <text x="320" y="170" font-size="12" opacity=".7">💨</text>''',
        "pool": '''
  <!-- pool net handle in hand -->
  <line x1="190" y1="280" x2="280" y2="160" stroke="#92400E" stroke-width="4" stroke-linecap="round"/>
  <ellipse cx="296" cy="148" rx="22" ry="8" fill="rgba(255,255,255,.6)" stroke="#1F2937" stroke-width="2"/>
  <!-- pool water at base -->
  <rect x="0" y="380" width="800" height="40" fill="#3B82F6" opacity=".55"/>''',
        "car": '''
  <!-- car body -->
  <rect x="380" y="260" width="240" height="70" rx="14" fill="#F59E0B"/>
  <rect x="400" y="220" width="170" height="50" rx="8" fill="#FCD34D"/>
  <circle cx="430" cy="350" r="20" fill="#1F2937"/><circle cx="430" cy="350" r="8" fill="#94A3B8"/>
  <circle cx="580" cy="350" r="20" fill="#1F2937"/><circle cx="580" cy="350" r="8" fill="#94A3B8"/>
  <!-- bubbles -->
  <circle cx="500" cy="240" r="8" fill="rgba(255,255,255,.7)"/>
  <circle cx="540" cy="220" r="6" fill="rgba(255,255,255,.6)"/>''',
        "garden": '''
  <!-- shears + plant -->
  <line x1="190" y1="280" x2="240" y2="220" stroke="#475569" stroke-width="3"/>
  <line x1="190" y1="290" x2="240" y2="230" stroke="#475569" stroke-width="3"/>
  <circle cx="245" cy="225" r="6" fill="#1F2937"/>
  <ellipse cx="500" cy="350" rx="80" ry="20" fill="#15803D"/>
  <text x="490" y="320" font-size="32">🌳</text>''',
    }
    return OVR.get(action, "")


def _portrait_svg(seed_str: str, action: str) -> str:
    s = _seed(seed_str)
    skin = SKINS[s % len(SKINS)]
    hair = HAIRS[(s >> 4) % len(HAIRS)]
    cap  = CAPS[(s >> 8) % len(CAPS)]
    apron= APRONS[(s >> 12) % len(APRONS)]
    is_woman = (s % 3) == 0  # rotate genders for realistic mix
    has_beard = (not is_woman) and ((s % 5) == 1)
    has_glasses = (s % 7) == 0
    accent = APRONS[(s >> 16) % len(APRONS)]

    # Hair styling
    if is_woman:
        hair_path = f'<path d="M 360 130 Q 320 100 280 140 Q 270 180 290 200 Q 280 240 320 260 L 440 260 Q 480 240 470 200 Q 490 180 480 140 Q 440 100 400 110 Q 380 105 360 130" fill="{hair}"/>'
        accessory = f'<path d="M 280 200 Q 250 250 240 320 L 270 320 Q 280 240 295 210" fill="{hair}"/>'  # long hair
    else:
        hair_path = f'<path d="M 290 145 Q 320 110 380 105 Q 440 105 470 145 Q 478 165 470 175 L 290 175 Q 282 165 290 145" fill="{hair}"/>'
        accessory = ""

    facial_hair = ""
    if has_beard:
        facial_hair = '<path d="M 320 250 Q 380 290 440 250 Q 430 280 380 290 Q 330 280 320 250" fill="' + hair + '"/>'

    glasses = ""
    if has_glasses:
        glasses = '<circle cx="345" cy="220" r="20" fill="none" stroke="#1F2937" stroke-width="3"/><circle cx="415" cy="220" r="20" fill="none" stroke="#1F2937" stroke-width="3"/><line x1="365" y1="220" x2="395" y2="220" stroke="#1F2937" stroke-width="3"/>'

    overlay = _action_overlay(action)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 460" width="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Servia branded staff illustration">
<defs>
  <linearGradient id="bg" x1="0" x2="0" y1="0" y2="1">
    <stop offset="0%" stop-color="#FFFBEB"/>
    <stop offset="100%" stop-color="#F8FAFC"/>
  </linearGradient>
</defs>
<rect width="760" height="460" fill="url(#bg)"/>

<!-- Body / apron / uniform -->
<ellipse cx="380" cy="430" rx="160" ry="20" fill="rgba(0,0,0,.10)"/>
<rect x="280" y="280" width="200" height="160" rx="20" fill="#fff"/>
<!-- Branded apron -->
<path d="M 300 280 L 460 280 L 470 440 L 290 440 Z" fill="{apron}"/>
<rect x="335" y="340" width="90" height="22" rx="4" fill="#fff"/>
<text x="380" y="357" text-anchor="middle" font-size="16" font-weight="800" fill="{apron}" letter-spacing="1">SERVIA</text>

<!-- Neck -->
<rect x="350" y="250" width="60" height="36" rx="6" fill="{skin}"/>

<!-- Face -->
<ellipse cx="380" cy="200" rx="80" ry="92" fill="{skin}"/>
{hair_path}
{accessory}

<!-- Eyes -->
<circle cx="345" cy="220" r="6" fill="#fff"/>
<circle cx="345" cy="220" r="3" fill="#0F172A"/>
<circle cx="415" cy="220" r="6" fill="#fff"/>
<circle cx="415" cy="220" r="3" fill="#0F172A"/>
<!-- Brows -->
<path d="M 332 200 Q 345 195 358 200" stroke="#0F172A" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<path d="M 402 200 Q 415 195 428 200" stroke="#0F172A" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<!-- Nose -->
<path d="M 378 235 Q 376 248 384 252" stroke="#0F172A" stroke-width="1.5" fill="none" stroke-linecap="round" opacity=".6"/>
<!-- Smile -->
<path d="M 350 260 Q 380 285 410 260" stroke="#0F172A" stroke-width="3" fill="none" stroke-linecap="round"/>
<!-- Cheeks -->
<circle cx="318" cy="245" r="10" fill="#F87171" opacity=".4"/>
<circle cx="442" cy="245" r="10" fill="#F87171" opacity=".4"/>

{facial_hair}
{glasses}

<!-- Branded cap -->
<ellipse cx="380" cy="130" rx="92" ry="22" fill="{cap}"/>
<path d="M 290 130 Q 380 70 470 130 L 470 142 Q 380 132 290 142 Z" fill="{cap}"/>
<rect x="350" y="100" width="60" height="14" rx="3" fill="#fff"/>
<text x="380" y="111" text-anchor="middle" font-size="11" font-weight="800" fill="{cap}" letter-spacing="1">SERVIA</text>

<!-- Arms with hands -->
<rect x="245" y="290" width="50" height="100" rx="20" fill="#fff"/>
<rect x="465" y="290" width="50" height="100" rx="20" fill="#fff"/>
<circle cx="270" cy="395" r="20" fill="{skin}"/>
<circle cx="490" cy="395" r="20" fill="{skin}"/>

<!-- Action overlay -->
{overlay}

<!-- Brand badge bottom right -->
<g transform="translate(640,420)">
  <rect x="-50" y="-22" width="100" height="36" rx="18" fill="{accent}" opacity=".9"/>
  <text x="0" y="2" text-anchor="middle" font-size="13" font-weight="800" fill="#fff" letter-spacing="1">SERVIA</text>
</g>
</svg>'''


@router.get("/api/staff/{slug}.svg")
def staff_portrait(slug: str, service: str = "deep_cleaning"):
    """Returns a branded SVG portrait for the given (slug, service).
    Slug seeds the random palette so each emirate / page gets a different look.
    Service controls the action overlay (mop, AC, wrench, etc.)."""
    action = SERVICE_ACTIONS.get(service, "cleaning")
    svg = _portrait_svg(slug, action)
    return Response(svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})
