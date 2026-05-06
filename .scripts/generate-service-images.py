#!/usr/bin/env python3
"""Generate one photo-realistic Servia-branded hero image per service.

Reads app/data/services.json, builds a prompt from the master style block
in web/nfc-video-prompts.md, calls DALL-E 3 (or Imagen 3 if configured),
saves PNGs to web/img/services/<id>-hero.png.

Usage:
    OPENAI_API_KEY=sk-...  python3 .scripts/generate-service-images.py
    # Optional: --only deep_cleaning,ac_cleaning   skip everything else
    # Optional: --force                             regenerate even if file exists
    # Optional: --variants 2                       generate N variants per service

Idempotent: skips services where /web/img/services/<id>-hero.png already exists
unless --force is set.

Cost: DALL-E 3 standard quality is $0.04/image; 32 services + 6 SOS = 38 images
≈ $1.52 for the full set.
"""
from __future__ import annotations
import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICES_JSON = ROOT / "app" / "data" / "services.json"
OUT_DIR = ROOT / "web" / "img" / "services"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============ Master style block (matches nfc-video-prompts.md A.1) ============
MASTER_STYLE = """Photo-realistic editorial advertising photograph, shot on Canon R5
with RF 35mm f/1.4 lens, golden-hour cinematic lighting, shallow depth
of field at f/2.0, ultra-detailed skin texture, subtle film grain, high
dynamic range. United Arab Emirates setting. Servia brand: yellow #FCD34D
cab + deep teal #0F766E lower panels and hood, lowercase "servia" logo
in teal on side, and "سيرفيا" Arabic logo below. Servia uniform: teal
polo shirt with mustard "servia" embroidered chest patch. Optional
phone in scene shows green-confirm pill "✅ Booked · AED [price] ·
[when]". 1:1 square framing, 30 percent top whitespace for headline."""

NEGATIVE = ("Negative: cartoonish, low-poly, illustration, 3D render, anime, "
            "plastic skin, melting, deformed wheels, distorted hands, "
            "extra fingers, misspelled servia, bus, taxi, Uber, blue lights, "
            "watermark, signature, Stock-Adobe text.")

# ============ Per-service scene prompts ============
SCENES = {
    # --- core cleaning ---
    "deep_cleaning":   "Bright JLT apartment kitchen with a Servia maid (30s, teal Servia polo + mustard apron, hair tied back, friendly smile) wiping the marble counter to a polished shine, microfibre cloth in hand. Sunlight streaming in. Hostess (working mum) sips coffee at the breakfast bar.",
    "general_cleaning":"Modern Marina apartment living room with a Servia cleaner (early 30s, teal Servia polo) vacuuming a rug. Floor-to-ceiling windows showing Marina skyline.",
    "maid_service":    "Family kitchen in Al Ain with a Servia maid (30s, teal polo + mustard apron) helping the family while the mum reads to her toddler.",
    "move_in_out":     "Doorway of a Marina Pinnacle apartment with two Servia movers (teal polo, kneepads) carrying a wrapped 3-seater sofa. Yellow-and-teal Servia 3.5-tonne moving van parked behind, ramp down. Customer (woman, 30s) on the apartment side smiling with phone.",
    "office_cleaning": "Servia office cleaner (40s, teal polo) wiping a glass conference table inside a Downtown Dubai corporate boardroom at dawn, before the team arrives.",
    "post_construction":"Servia post-construction crew (teal polo + N95 masks) cleaning a freshly-built villa in Saadiyat with extending dust mops and a HEPA vacuum.",
    "sofa_carpet":     "Servia sofa-cleaning specialist (mid-30s, teal polo, latex gloves) shampooing a cream sofa in a Mirdif living room with a foaming wand. Cream sofa half-cleaned showing the contrast.",
    "ac_cleaning":     "Servia HVAC tech (mid-30s, teal Servia polo, dust mask hanging on neck) cleaning a wall-mount split AC's evaporator coils with a foaming spray. Customer in soft focus, baby napping in the cool room.",
    "disinfection":    "Servia disinfection tech in teal polo + full PPE spraying low-toxicity MOH-approved fog through a Sharjah office. Children's classroom desks visible.",
    "window_cleaning": "Servia window cleaner on a high-rise rope-access cradle wiping outside the JBR tower windows. Beach in background.",
    "pest_control":    "Servia pest-control specialist (40s, teal polo, respirator pulled to neck, certified-technician ID lanyard) discreetly spraying along kitchen baseboards. Family-friendly mood.",
    "laundry":         "Servia laundry van and a smiling driver handing back a fresh-pressed dishdasha in a sealed garment bag at a villa doorway in Al Barsha.",
    "babysitting":     "Servia babysitter (mid-20s, teal polo, friendly) reading to two children on a play mat in a sunlit Downtown apartment.",
    "gardening":       "Servia gardener (40s, teal polo + brimmed hat) trimming a Bougainvillea hedge at a Jumeirah villa entrance. Manicured lawn.",
    "handyman":        "Servia handyman (40s, beard, teal polo, leather tool belt) on a step-ladder filling a nail hole in a freshly painted off-white wall, fresh paint roller and putty knife. Burj Khalifa visible through window.",
    "kitchen_deep":    "Servia kitchen-deep team (teal polo + mustard apron) scrubbing oven grills in a Tecom apartment kitchen. Cleaning chemicals on a teal Servia floor mat.",
    "villa_deep":      "Aerial-style wide shot of a Servia 6-person crew tackling a 5-bedroom Emirates Hills villa in coordinated zones — kitchen, living, master bedroom visible simultaneously.",
    "car_wash":        "Servia car-wash tech (20s, teal polo + waterproof apron, brimmed hat) hand-washing a black Range Rover at the customer's villa driveway in Mirdif. Mobile water tank in Servia van.",
    "swimming_pool":   "Drone view of a private villa pool in Arabian Ranches at golden hour. A Servia pool tech (30s, teal polo + matching shorts) using a long-handled net poolside. Pool water crystal-clear turquoise.",
    "marble_polish":   "Servia marble specialist polishing a beige marble entrance hallway in a Palm villa with a low-RPM polishing machine. Mirror-like finish forming.",
    "curtain_cleaning":"Servia curtain specialist taking down floor-to-ceiling Dubai Marina curtains for off-site steam cleaning. Yellow Servia van outside.",
    "smart_home":      "Servia smart-home installer (20s, teal polo) setting up a Hue/Aqara hub on a Downtown Dubai console table. Customer holds phone showing the app.",
    "painting":        "Servia painter (mid-30s, teal polo + drop cloth) rolling Benjamin Moore off-white onto a feature wall of a 2-bedroom Sharjah apartment. Tape edges crisp.",
    # --- repair ---
    "mobile_repair":     "Close-up of Servia mobile-repair tech (20s, teal polo, magnifier loupe) replacing an iPhone screen at a clean home workbench. Customer's phone next to the box.",
    "laptop_repair":     "Servia laptop-repair tech (mid-20s, teal polo, anti-static wrist strap) cleaning a MacBook Pro internal fan at a customer's home in Arabian Ranches.",
    "washing_machine_repair":"Servia appliance tech kneeling to fix a Bosch front-load washing machine in a Dubai laundry room, multimeter in hand.",
    "fridge_repair":      "Servia tech checking the compressor of a Samsung side-by-side fridge in a Marina apartment kitchen, multimeter visible.",
    "dishwasher_repair":  "Servia tech repairing a Bosch under-counter dishwasher, drainage pipe in hand, customer's kitchen island visible in soft focus.",
    "oven_microwave_repair":"Servia tech with a multimeter testing an oven element in an open Whirlpool built-in oven, customer kitchen background.",
    "water_heater_repair":"Servia tech bleeding air from an Ariston water heater in a villa utility cupboard. Headlamp on, focus shot.",
    "tv_setup":           "Servia AV tech wall-mounting a 65-inch Samsung QLED TV in a Downtown apartment. Cable management drawn taut with Velcro.",
    "chauffeur":          "Front passenger door of a black Mercedes S-Class held open by a Servia chauffeur (40s, teal Servia jacket, white gloves) at the Address Downtown porte-cochère. Customer climbing in with a laptop bag.",
    # --- SOS-only categories (not in services.json yet) ---
    "vehicle_recovery": "Black SUV stalled at the side of Sheikh Zayed Road at golden hour with bonnet open and hazard triangle behind. Distressed driver looking concerned. Yellow-and-teal Servia tow truck approaching in the right third of the frame.",
    "plumber":          "Servia plumber (50s, friendly face, teal polo, latex gloves) tightening a chrome pipe joint under a Dubai kitchen sink with a wrench. Tools on a teal Servia floor mat.",
    "electrician":      "Servia electrician (mid-30s, teal polo, hard hat, voltage tester in hand) on a small ladder cleanly installing a brushed-nickel ceiling pendant in a Downtown apartment.",
    "furniture_move":   "Two Servia movers wheeling a wrapped wardrobe down a corridor towards a yellow-and-teal Servia moving van. Customer's apartment door visible.",
}

HEADLINES = {
    # Optional headline burned in by the generator's text rendering ability
    "vehicle_recovery": "TAP ONCE. RECOVERY ON THE WAY.",
    "ac_cleaning":      "TAP ONCE. COOL ALL DAY.",
    "deep_cleaning":    "TAP ONCE. SPARKLE.",
    "handyman":         "TAP ONCE. WE HANDLE IT.",
    "plumber":          "TAP ONCE. LEAK FIXED.",
    "electrician":      "TAP ONCE. POWER ON.",
    "chauffeur":        "TAP ONCE. CHAUFFEUR AT YOUR DOOR.",
    "furniture_move":   "TAP ONCE. FURNITURE MOVED.",
    "swimming_pool":    "TAP ONCE. POOL PERFECT.",
    "pest_control":     "TAP ONCE. PESTS GONE.",
}


def build_prompt(svc_id: str) -> str:
    scene = SCENES.get(svc_id)
    if not scene:
        # Generic fallback for any service not in SCENES
        scene = (f"Servia tradesperson in teal Servia polo professionally completing "
                 f"a {svc_id.replace('_', ' ')} service at a UAE customer's home or office.")
    headline = HEADLINES.get(svc_id, "")
    head_line = f' Burn-in headline at top: "{headline}".' if headline else ""
    return f"{MASTER_STYLE}\n\nScene: {scene}{head_line}\n\n{NEGATIVE}"


def call_dalle3(prompt: str, api_key: str, size: str = "1024x1024") -> bytes:
    """Call OpenAI DALL-E 3 and return PNG bytes. Raises on failure."""
    body = json.dumps({
        "model": "dall-e-3",
        "prompt": prompt[:4000],     # API limit
        "n": 1,
        "size": size,
        "quality": "standard",
        "response_format": "b64_json",
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        j = json.loads(r.read())
    b64 = j["data"][0]["b64_json"]
    return base64.b64decode(b64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only",     default="", help="Comma-separated service ids (default: ALL)")
    ap.add_argument("--force",    action="store_true", help="Regenerate even if file exists")
    ap.add_argument("--variants", type=int, default=1, help="N variants per service")
    args = ap.parse_args()

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("ERROR: set OPENAI_API_KEY env var", file=sys.stderr)
        sys.exit(2)

    # Build target list
    svc_data = json.loads(SERVICES_JSON.read_text())
    all_ids = [s["id"] for s in svc_data.get("services", [])]
    # Add SOS-only categories that aren't yet in services.json
    for extra in ("vehicle_recovery", "plumber", "electrician", "furniture_move"):
        if extra not in all_ids:
            all_ids.append(extra)

    targets = (args.only.split(",") if args.only
               else all_ids)
    targets = [t.strip() for t in targets if t.strip()]
    print(f"Generating images for {len(targets)} services × {args.variants} variants")
    print(f"Output: {OUT_DIR}")
    print(f"Cost estimate: ~${len(targets) * args.variants * 0.04:.2f} (DALL-E 3 standard)")
    print()

    done, skipped, failed = 0, 0, 0
    for sid in targets:
        for v in range(args.variants):
            suffix = "" if args.variants == 1 else f"-{v+1}"
            out = OUT_DIR / f"{sid}-hero{suffix}.png"
            if out.exists() and not args.force:
                print(f"  ↷ {sid}{suffix}  (already exists, skip)")
                skipped += 1
                continue
            prompt = build_prompt(sid)
            try:
                print(f"  ⏳ {sid}{suffix}  generating…", flush=True)
                t0 = time.time()
                png = call_dalle3(prompt, api_key)
                out.write_bytes(png)
                print(f"  ✓ {sid}{suffix}  ({len(png)//1024}KB, {time.time()-t0:.1f}s)")
                done += 1
                # Rate-limit to ~1 image / 4 sec to stay well under tier 1 quota
                time.sleep(3)
            except Exception as e:
                print(f"  ✗ {sid}{suffix}  FAILED: {e}", file=sys.stderr)
                failed += 1
    print()
    print(f"Done: {done} generated · {skipped} skipped · {failed} failed")


if __name__ == "__main__":
    main()
