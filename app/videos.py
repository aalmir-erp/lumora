"""Servia mascot videos.

These are HTML5 'videos' — standalone pages with the Servia mascot SVG +
CSS keyframe animations + voiceover text overlay. They look like motion-
graphic explainer videos, no ffmpeg or external API needed.

Admin can:
  - View all videos in /admin (👀 Videos tab)
  - Generate new ones from a script via /api/admin/videos/generate (uses
    selected AI model from ai_router for the script)
  - Schedule auto-daily-video like the daily blog
"""
from __future__ import annotations

import datetime as _dt
import json as _json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import db
from .auth import require_admin


public_router = APIRouter(prefix="/api/videos", tags=["videos"])
admin_router = APIRouter(prefix="/api/admin/videos", tags=["admin-videos"],
                         dependencies=[Depends(require_admin)])


def _ensure_table():
    with db.connect() as c:
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS videos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE, title TEXT, mascot TEXT,
                tone TEXT, scenes_json TEXT,
                duration_sec INTEGER, view_count INTEGER DEFAULT 0,
                created_at TEXT)""")
        except Exception: pass


# ---------- 5 hand-crafted starter videos shipped with first deploy ----------
STARTER_VIDEOS = [
    {
        "slug": "welcome-to-servia",
        "title": "Hi 👋 — meet Servia",
        "mascot": "default",
        "tone": "teal",
        "duration_sec": 18,
        "scenes": [
            {"text": "Hi, I'm Servia 👋", "sub": "Your UAE concierge",       "anim": "wave"},
            {"text": "Need a service?",   "sub": "I've got 32 of them",       "anim": "point"},
            {"text": "Booked in 60s",     "sub": "Same-day across UAE",       "anim": "bounce"},
            {"text": "Pay only when slot is locked.", "sub": "Apple Pay · Google Pay · Card", "anim": "shake"},
            {"text": "Tap. Book. Done.",  "sub": "Try me on servia.ae",       "anim": "wave"},
        ],
    },
    {
        "slug": "book-in-60-seconds",
        "title": "How to book in 60 seconds",
        "mascot": "ac",
        "tone": "amber",
        "duration_sec": 22,
        "scenes": [
            {"text": "Step 1 · Pick a service", "sub": "AC · cleaning · pest · handyman", "anim": "point"},
            {"text": "Step 2 · Pick a slot",    "sub": "Same-day if booked before 11am", "anim": "bounce"},
            {"text": "Step 3 · Pay to confirm", "sub": "Apple Pay · Google Pay · Card · Tabby", "anim": "shake"},
            {"text": "Step 4 · Pro on the way", "sub": "Live ETA on WhatsApp every 5 min", "anim": "wave"},
            {"text": "Step 5 · All done.",      "sub": "Photos · invoice · 7-day re-do guarantee", "anim": "wave"},
        ],
    },
    {
        "slug": "ac-pre-summer-prep",
        "title": "AC pre-summer prep — Servia",
        "mascot": "ac",
        "tone": "purple",
        "duration_sec": 16,
        "scenes": [
            {"text": "UAE summer = 45°C", "sub": "Your AC runs 14h a day",       "anim": "shake"},
            {"text": "Skip a service?",   "sub": "Compressor failure costs AED 1,200+", "anim": "point"},
            {"text": "Servia AC service", "sub": "from AED 75 / unit · 90 min",   "anim": "bounce"},
            {"text": "Book this week",    "sub": "Slots disappearing fast",       "anim": "wave"},
        ],
    },
    {
        "slug": "deep-clean-feel",
        "title": "Deep cleaning that just works",
        "mascot": "cleaning",
        "tone": "green",
        "duration_sec": 20,
        "scenes": [
            {"text": "✨ Top-to-bottom deep clean", "sub": "Bathrooms · kitchens · floors · windows", "anim": "wave"},
            {"text": "2 cleaners · 4-6 hours",      "sub": "Supplies + equipment included", "anim": "point"},
            {"text": "from AED 350",                "sub": "Studio – 4 BR · transparent pricing", "anim": "bounce"},
            {"text": "AED 25,000 damage cover",     "sub": "Background-checked · insured", "anim": "shake"},
            {"text": "7-day re-do guarantee.",      "sub": "Not happy? We come back free.", "anim": "wave"},
        ],
    },
    {
        "slug": "ambassador-tier-ladder",
        "title": "Refer & climb — Servia Ambassador",
        "mascot": "default",
        "tone": "rose",
        "duration_sec": 18,
        "scenes": [
            {"text": "Refer a friend",        "sub": "They both get a discount",       "anim": "point"},
            {"text": "🥉 Bronze · 5% off",     "sub": "0–2 referrals",                 "anim": "bounce"},
            {"text": "🥈 Silver · 10% off",   "sub": "3–5 referrals",                 "anim": "bounce"},
            {"text": "🥇 Gold · 15% off",      "sub": "6–10 referrals",                "anim": "bounce"},
            {"text": "💎 Platinum · 20% off",  "sub": "11+ referrals · forever",       "anim": "wave"},
        ],
    },
]


def _service_video(sid: str, sname: str, emoji: str, mascot: str, tone: str) -> dict:
    return {
        "slug": f"svc-{sid.replace('_','-')}",
        "title": f"{sname} — Servia UAE",
        "mascot": mascot, "tone": tone, "duration_sec": 18,
        "scenes": [
            {"text": f"{emoji} {sname}", "sub": "Across all 7 UAE emirates", "anim": "wave"},
            {"text": "Vetted pros · same-day", "sub": "Background-checked + insured", "anim": "point"},
            {"text": "Transparent fixed price", "sub": "AED 25,000 damage cover", "anim": "bounce"},
            {"text": "7-day re-do guarantee", "sub": "Not happy? We come back free.", "anim": "shake"},
            {"text": "Tap. Book. Done.", "sub": "60 seconds at servia.ae", "anim": "wave"},
        ],
        "service_id": sid, "kind": "service",
    }


def _emirate_video(em_id: str, em_name: str, tone: str) -> dict:
    return {
        "slug": f"em-{em_id}",
        "title": f"Servia in {em_name}",
        "mascot": "default", "tone": tone, "duration_sec": 16,
        "scenes": [
            {"text": f"📍 Servia in {em_name}", "sub": "Daily coverage · all neighbourhoods", "anim": "wave"},
            {"text": "Local crews · local prices", "sub": "No premium for your area", "anim": "point"},
            {"text": "Same-day if booked by 11am", "sub": "Real-time tracking on WhatsApp", "anim": "bounce"},
            {"text": f"Book in {em_name} →", "sub": "servia.ae/book", "anim": "wave"},
        ],
        "emirate": em_id, "kind": "emirate",
    }


LONG_FORM_VIDEOS = [
    {"slug":"long-ac-pre-summer", "title":"AC pre-summer guide — Servia explainer (60s)",
     "mascot":"ac","tone":"amber","duration_sec":60, "kind":"long",
     "scenes":[
       {"text":"☀️ UAE summer hits 45°C", "sub":"Your AC works 14h/day in July", "anim":"shake"},
       {"text":"❌ Why people skip service","sub":"'It's still cold' isn't enough","anim":"point"},
       {"text":"⚠️ What happens then","sub":"Compressor fails · AED 1,200+ repair","anim":"shake"},
       {"text":"✅ Servia AC service","sub":"From AED 75/unit · 90 min visit","anim":"bounce"},
       {"text":"📅 Best time = April-May","sub":"Slots fill 2-3 weeks ahead","anim":"point"},
       {"text":"📲 Book in 60 seconds","sub":"servia.ae/book?service=ac_service","anim":"wave"},
       {"text":"💎 7-day re-do guarantee","sub":"AED 25k damage cover","anim":"wave"},
     ]},
    {"slug":"long-deep-clean-truth", "title":"Deep cleaning — what people don't tell you (60s)",
     "mascot":"cleaning","tone":"teal","duration_sec":60, "kind":"long",
     "scenes":[
       {"text":"✨ Deep clean ≠ general clean","sub":"Top-to-bottom · 4-6 hours","anim":"point"},
       {"text":"❌ Why DIY fails","sub":"Wrong tools · wrong products","anim":"shake"},
       {"text":"⚠️ Hidden grime damages","sub":"Tile grout · oven · AC vents","anim":"shake"},
       {"text":"✅ Servia 2-pro crew","sub":"Supplies + equipment included","anim":"bounce"},
       {"text":"💰 From AED 350 · transparent","sub":"All sizes · all emirates","anim":"point"},
       {"text":"🛡 AED 25k damage cover","sub":"7-day re-do guarantee","anim":"wave"},
       {"text":"📲 Book your deep clean","sub":"servia.ae/book?service=deep_cleaning","anim":"wave"},
     ]},
    {"slug":"long-pest-truth", "title":"Pest control — what sprays don't tell you (60s)",
     "mascot":"pest","tone":"green","duration_sec":60, "kind":"long",
     "scenes":[
       {"text":"🪲 Cockroaches in UAE","sub":"American + German species","anim":"point"},
       {"text":"❌ Sprays = surface-only","sub":"Eggs survive · come back in 6 wks","anim":"shake"},
       {"text":"⚠️ DIY costs AED 200+/yr","sub":"Buying sprays that don't work","anim":"shake"},
       {"text":"✅ Servia residual treatment","sub":"Gel baits + IGR · kills lifecycle","anim":"bounce"},
       {"text":"📅 90-day warranty","sub":"Free re-treat if pests return","anim":"point"},
       {"text":"💰 From AED 200 · 1 visit","sub":"Pet-safe + child-safe options","anim":"point"},
       {"text":"📲 Book pest control","sub":"servia.ae/book?service=pest_control","anim":"wave"},
     ]},
    {"slug":"long-handyman-saves", "title":"How a handyman visit saves AED 1000+ (60s)",
     "mascot":"handyman","tone":"rose","duration_sec":60, "kind":"long",
     "scenes":[
       {"text":"🔧 Small problem today","sub":"Big bill tomorrow","anim":"point"},
       {"text":"❌ Dripping tap = water bill spike","sub":"Loose socket = fire risk","anim":"shake"},
       {"text":"⚠️ Postponing = compounding cost","sub":"AED 50 fix becomes AED 800+","anim":"shake"},
       {"text":"✅ Servia hourly handyman","sub":"From AED 100/hr · 1-2h jobs","anim":"bounce"},
       {"text":"🛠 Plumb · electric · paint","sub":"All-in-one visit · transparent","anim":"point"},
       {"text":"📲 Book a handyman","sub":"servia.ae/book?service=handyman","anim":"wave"},
     ]},
    {"slug":"long-move-out", "title":"Move-out cleaning saves your deposit (60s)",
     "mascot":"cleaning","tone":"indigo","duration_sec":60, "kind":"long",
     "scenes":[
       {"text":"📦 Moving out?","sub":"Landlord deposit on the line","anim":"point"},
       {"text":"❌ Rushing the clean = loss","sub":"AED 800-3000 deposits kept","anim":"shake"},
       {"text":"⚠️ Common cuts","sub":"AC filters · oven · grout · grates","anim":"shake"},
       {"text":"✅ Servia move-out package","sub":"From AED 400 · 5h crew","anim":"bounce"},
       {"text":"📋 Handover checklist","sub":"We document with photos","anim":"point"},
       {"text":"📲 Book before handover day","sub":"servia.ae/book?service=move_in_out","anim":"wave"},
     ]},
    {"slug":"long-sofa-renew", "title":"Sofa shampoo brings back 'new' (60s)",
     "mascot":"cleaning","tone":"blue","duration_sec":60, "kind":"long",
     "scenes":[
       {"text":"🛋 Tired-looking sofa?","sub":"Don't replace · restore","anim":"point"},
       {"text":"❌ Why DIY fails","sub":"Wrong shampoo = water rings","anim":"shake"},
       {"text":"⚠️ Stains set permanently","sub":"After 2-3 months they bond","anim":"shake"},
       {"text":"✅ Servia steam shampoo","sub":"Pro extractor · safe foam","anim":"bounce"},
       {"text":"💰 AED 120/seater · 2h","sub":"Looks + smells new","anim":"point"},
       {"text":"📲 Book sofa cleaning","sub":"servia.ae/book?service=sofa_carpet","anim":"wave"},
     ]},
    {"slug":"long-villa-deep", "title":"Villa deep clean — full reset (60s)",
     "mascot":"cleaning","tone":"green","duration_sec":60, "kind":"long",
     "scenes":[
       {"text":"🏡 Villa = bigger crew","sub":"5-7 hour full reset","anim":"bounce"},
       {"text":"✅ Indoor + outdoor","sub":"Garden, pool deck, garage","anim":"point"},
       {"text":"✨ Top-to-bottom","sub":"Every BR · BA · kitchen · majlis","anim":"wave"},
       {"text":"💰 From AED 700","sub":"Transparent · no hidden fees","anim":"point"},
       {"text":"🛡 AED 25k damage cover","sub":"7-day re-do guarantee","anim":"wave"},
       {"text":"📲 Book villa deep clean","sub":"servia.ae/book?service=villa_deep","anim":"wave"},
     ]},
    {"slug":"long-bundle-savings", "title":"Bundle services — save up to 15% (60s)",
     "mascot":"default","tone":"amber","duration_sec":60, "kind":"long",
     "scenes":[
       {"text":"📦 Need 2+ services?","sub":"Stack them in your cart","anim":"point"},
       {"text":"💰 Auto bundle discount","sub":"2 = 5% · 3 = 10% · 4+ = 15% off","anim":"bounce"},
       {"text":"📅 Same day or different days","sub":"You decide per line","anim":"point"},
       {"text":"💳 ONE payment · ONE invoice","sub":"Apple Pay · Google Pay · Card","anim":"wave"},
       {"text":"📲 Build your bundle","sub":"servia.ae/cart","anim":"wave"},
     ]},
]


GENERIC_VIDEOS = [
    {"slug":"why-servia",       "title":"Why 2,400+ UAE families pick Servia",     "mascot":"default","tone":"teal",
     "scenes":[{"text":"4.9★ from 2,400+","sub":"Real verified reviews","anim":"wave"},
               {"text":"Vetted pros only","sub":"Background-checked + insured","anim":"point"},
               {"text":"Pay only when satisfied","sub":"7-day re-do guarantee","anim":"bounce"},
               {"text":"AED 25,000 damage cover","sub":"On every visit","anim":"shake"}]},
    {"slug":"summer-prep",      "title":"UAE summer prep — book before June",      "mascot":"ac","tone":"amber",
     "scenes":[{"text":"☀️ 45°C is coming","sub":"AC failures spike June-Aug","anim":"shake"},
               {"text":"Pre-summer check","sub":"AED 75/unit · 90 min","anim":"point"},
               {"text":"Book by May","sub":"Slots disappearing fast","anim":"wave"}]},
    {"slug":"deposit-saving",   "title":"Move-out cleaning saves your deposit",    "mascot":"cleaning","tone":"green",
     "scenes":[{"text":"📦 Moving out?","sub":"Landlords keep AED 800-3000 deposits","anim":"shake"},
               {"text":"Deposit-saving deep clean","sub":"From AED 400 · 5h crew","anim":"bounce"},
               {"text":"Be present at handover","sub":"We document everything","anim":"wave"}]},
    {"slug":"pest-truth",       "title":"What pest sprays don't tell you",         "mascot":"pest","tone":"green",
     "scenes":[{"text":"🪲 Sprays = quick fix","sub":"Pests come back in 6 weeks","anim":"shake"},
               {"text":"Servia residual treatment","sub":"90-day warranty","anim":"point"},
               {"text":"Book pest control →","sub":"From AED 200","anim":"wave"}]},
    {"slug":"handyman-saves",   "title":"Handyman saves you AED 500+",             "mascot":"handyman","tone":"rose",
     "scenes":[{"text":"🔧 Small fix or full job?","sub":"Most jobs done in 1-2h","anim":"wave"},
               {"text":"Hourly · transparent","sub":"From AED 100 / hour","anim":"point"},
               {"text":"Plumbing · electric · paint","sub":"All in one visit","anim":"bounce"}]},
    {"slug":"sofa-renew",       "title":"Sofa shampoo brings back 'new'",          "mascot":"cleaning","tone":"blue",
     "scenes":[{"text":"🛋️ Tired sofa?","sub":"Don't replace — restore","anim":"point"},
               {"text":"Steam shampoo","sub":"AED 120 / seater · 2h","anim":"bounce"},
               {"text":"Stains gone · smell gone","sub":"Like new again","anim":"wave"}]},
    {"slug":"car-at-home",      "title":"Car wash at YOUR home",                   "mascot":"car","tone":"blue",
     "scenes":[{"text":"🚗 Skip the queue","sub":"We come to you","anim":"wave"},
               {"text":"Inside + outside","sub":"From AED 60","anim":"point"},
               {"text":"Book your time","sub":"Daily slots open","anim":"bounce"}]},
    {"slug":"ramadan-clean",    "title":"Ramadan kitchen reset",                   "mascot":"cleaning","tone":"purple",
     "scenes":[{"text":"🌙 Ramadan = heavy cooking","sub":"Grease + spice = stuck","anim":"point"},
               {"text":"Kitchen deep clean","sub":"Oven · hood · cabinets","anim":"bounce"},
               {"text":"Book between iftars","sub":"We work around you","anim":"wave"}]},
    {"slug":"baby-safe",        "title":"Babysitter-safe disinfection",            "mascot":"maid","tone":"purple",
     "scenes":[{"text":"👶 New baby coming?","sub":"Hospital-grade disinfection","anim":"wave"},
               {"text":"Servia pre-arrival deep clean","sub":"Safe for newborns","anim":"point"},
               {"text":"Book before the due date","sub":"Peace of mind","anim":"bounce"}]},
    {"slug":"refer-rewards",    "title":"Refer = climb tier ladder",               "mascot":"default","tone":"amber",
     "scenes":[{"text":"🎁 Refer one friend","sub":"You both get a discount","anim":"point"},
               {"text":"3 = Silver · 10% off","sub":"Every booking forever","anim":"bounce"},
               {"text":"11+ = Platinum 20% off","sub":"Highest tier","anim":"wave"}]},
    {"slug":"creator-program",  "title":"Make a video, climb tiers",               "mascot":"default","tone":"rose",
     "scenes":[{"text":"🎬 Tag @servia.ae","sub":"On Instagram / TikTok / YouTube","anim":"point"},
               {"text":"Length × followers × platform","sub":"= creator points","anim":"bounce"},
               {"text":"5,000 pts = Elite track","sub":"Custom perks · revenue share","anim":"wave"}]},
    {"slug":"emergency-tonight","title":"Emergency tonight? Same-day Servia",      "mascot":"handyman","tone":"rose",
     "scenes":[{"text":"🚨 Burst pipe?","sub":"AC down? Lock broken?","anim":"shake"},
               {"text":"Same-day pros","sub":"Most slots within 2h","anim":"point"},
               {"text":"Book → pay → done","sub":"60 seconds total","anim":"wave"}]},
    {"slug":"villa-deep",       "title":"Villa deep clean — full reset",           "mascot":"cleaning","tone":"green",
     "scenes":[{"text":"🏡 Bigger crew · 5-7h","sub":"Indoor + outdoor","anim":"bounce"},
               {"text":"Garden · pool deck · windows","sub":"All included","anim":"point"},
               {"text":"From AED 700","sub":"Transparent pricing","anim":"wave"}]},
    {"slug":"office-clean",     "title":"Office cleaning — day OR night",          "mascot":"cleaning","tone":"indigo",
     "scenes":[{"text":"🏢 Out-of-hours?","sub":"Our crews work nights","anim":"point"},
               {"text":"Per square foot","sub":"Daily / weekly / monthly","anim":"bounce"},
               {"text":"Quiet · efficient · vetted","sub":"Trust badges + IDs","anim":"wave"}]},
    {"slug":"smart-home",       "title":"Smart home setup in 3 hours",             "mascot":"handyman","tone":"indigo",
     "scenes":[{"text":"💡 Alexa · Google Home","sub":"Smart locks · cameras","anim":"point"},
               {"text":"Install + configure","sub":"From AED 250","anim":"bounce"},
               {"text":"Pro shows you everything","sub":"You're up & running","anim":"wave"}]},
    {"slug":"weekend-saver",    "title":"Save your weekend with Servia",           "mascot":"default","tone":"teal",
     "scenes":[{"text":"⏱ 4-6h cleaning yourself?","sub":"Or 2 cleaners doing it","anim":"point"},
               {"text":"Servia takes 3 hours","sub":"You get the weekend back","anim":"bounce"},
               {"text":"From AED 350","sub":"Worth every dirham","anim":"wave"}]},
    {"slug":"bundle-discount",  "title":"Bundle 2+ services — save up to 15%",     "mascot":"default","tone":"amber",
     "scenes":[{"text":"📦 Need 2+ services?","sub":"Stack them in your cart","anim":"point"},
               {"text":"2 = 5% off · 3 = 10%","sub":"4+ = 15% off bundle","anim":"bounce"},
               {"text":"One payment · one invoice","sub":"servia.ae/cart","anim":"wave"}]},
    {"slug":"tabby-pay",        "title":"Pay with Tabby — split into 4",           "mascot":"default","tone":"purple",
     "scenes":[{"text":"💳 Big service?","sub":"Pay over 4 weeks","anim":"point"},
               {"text":"Tabby · 0% interest","sub":"No fees · instant","anim":"bounce"},
               {"text":"Available at checkout","sub":"For all UAE bookings","anim":"wave"}]},
    {"slug":"woman-only",       "title":"Female-only crews on request",            "mascot":"maid","tone":"purple",
     "scenes":[{"text":"👩 Need female crew?","sub":"Just tick the box","anim":"point"},
               {"text":"Vetted female pros","sub":"Same price · same standards","anim":"bounce"},
               {"text":"Book in privacy","sub":"servia.ae","anim":"wave"}]},
    {"slug":"app-install",      "title":"Install the Servia app — free",           "mascot":"default","tone":"teal",
     "scenes":[{"text":"📲 Mobile app","sub":"60-second install · no app store","anim":"wave"},
               {"text":"Real-time tracking","sub":"Push alerts on arrival","anim":"point"},
               {"text":"App-only deals","sub":"Exclusive perks","anim":"bounce"}]},
]


# Service catalogue used to bulk-generate per-service videos
ALL_SERVICES = [
    ("ac_service",          "AC Service",            "❄️", "ac",       "amber"),
    ("ac_cleaning",         "AC Cleaning",           "❄️", "ac",       "amber"),
    ("deep_cleaning",       "Deep Cleaning",         "✨", "cleaning", "teal"),
    ("general_cleaning",    "General Cleaning",      "🧹", "cleaning", "teal"),
    ("villa_deep",          "Villa Deep Clean",      "🏡", "cleaning", "green"),
    ("kitchen_deep_clean",  "Kitchen Deep Clean",    "👨‍🍳", "cleaning", "orange"),
    ("kitchen_deep",        "Kitchen Deep Clean",    "👨‍🍳", "cleaning", "orange"),
    ("move_in_out_cleaning","Move-in/Move-out Clean","📦", "cleaning", "indigo"),
    ("move_in_out",         "Move-in/Move-out Clean","📦", "cleaning", "indigo"),
    ("office_cleaning",     "Office Cleaning",       "🏢", "cleaning", "indigo"),
    ("post_construction",   "Post-Construction Clean","🏗", "cleaning","rose"),
    ("disinfection",        "Disinfection",          "🧴", "cleaning", "green"),
    ("maid_service",        "Maid Service",          "👤", "maid",     "purple"),
    ("babysitting",         "Babysitter / Nanny",    "👶", "maid",     "purple"),
    ("handyman",            "Handyman",              "🔧", "handyman", "rose"),
    ("painting",            "Painting",              "🎨", "handyman", "rose"),
    ("pest_control",        "Pest Control",          "🪲", "pest",     "green"),
    ("sofa_carpet",         "Sofa & Carpet Clean",   "🛋️","cleaning", "blue"),
    ("carpet_cleaning",     "Carpet Cleaning",       "🧼", "cleaning", "blue"),
    ("window_cleaning",     "Window Cleaning",       "🪟", "cleaning", "blue"),
    ("curtain_cleaning",    "Curtain Cleaning",      "🪟", "cleaning", "blue"),
    ("marble_polish",       "Marble Polishing",      "💎", "cleaning", "amber"),
    ("car_wash",            "Car Wash",              "🚗", "car",      "blue"),
    ("swimming_pool",       "Pool Maintenance",      "🏊", "pool",     "blue"),
    ("gardening",           "Gardening",             "🌿", "garden",   "green"),
    ("smart_home",          "Smart Home Setup",      "💡", "handyman", "indigo"),
    ("laundry",             "Laundry & Ironing",     "👕", "maid",     "purple"),
]

ALL_EMIRATES = [
    ("dubai",          "Dubai",          "teal"),
    ("abu-dhabi",      "Abu Dhabi",      "green"),
    ("sharjah",        "Sharjah",        "amber"),
    ("ajman",          "Ajman",          "purple"),
    ("ras-al-khaimah", "Ras Al Khaimah", "rose"),
    ("umm-al-quwain",  "Umm Al Quwain",  "blue"),
    ("fujairah",       "Fujairah",       "indigo"),
]


def _ensure_extra_columns():
    with db.connect() as c:
        try: c.execute("ALTER TABLE videos ADD COLUMN service_id TEXT")
        except Exception: pass
        try: c.execute("ALTER TABLE videos ADD COLUMN emirate TEXT")
        except Exception: pass
        try: c.execute("ALTER TABLE videos ADD COLUMN kind TEXT")
        except Exception: pass


_SEEDED = False


def seed_videos_if_empty():
    """Bulk seed: 5 hand-crafted starter + 8 long-form + 20 generic + 1 per
    service + 1 per emirate. Idempotent via INSERT OR IGNORE. Cached after
    first run so /list calls don't re-walk 67 inserts every request."""
    global _SEEDED
    if _SEEDED: return
    _ensure_table()
    _ensure_extra_columns()
    now = _dt.datetime.utcnow().isoformat() + "Z"
    inserts = []
    for v in STARTER_VIDEOS:
        inserts.append((v["slug"], v["title"], v["mascot"], v["tone"],
                        _json.dumps(v["scenes"]), v["duration_sec"], now,
                        None, None, "starter"))
    for v in LONG_FORM_VIDEOS:
        inserts.append((v["slug"], v["title"], v["mascot"], v["tone"],
                        _json.dumps(v["scenes"]), v["duration_sec"], now,
                        None, None, "long"))
    for v in GENERIC_VIDEOS:
        inserts.append((v["slug"], v["title"], v["mascot"], v["tone"],
                        _json.dumps(v["scenes"]), 18, now,
                        None, None, "generic"))
    for sid, name, emoji, mascot, tone in ALL_SERVICES:
        v = _service_video(sid, name, emoji, mascot, tone)
        inserts.append((v["slug"], v["title"], v["mascot"], v["tone"],
                        _json.dumps(v["scenes"]), v["duration_sec"], now,
                        sid, None, "service"))
    for em_id, em_name, tone in ALL_EMIRATES:
        v = _emirate_video(em_id, em_name, tone)
        inserts.append((v["slug"], v["title"], v["mascot"], v["tone"],
                        _json.dumps(v["scenes"]), v["duration_sec"], now,
                        None, em_id, "emirate"))
    with db.connect() as c:
        for row in inserts:
            try:
                c.execute(
                    "INSERT OR IGNORE INTO videos(slug, title, mascot, tone, scenes_json, "
                    "duration_sec, created_at, service_id, emirate, kind) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?)", row)
            except Exception: pass
    _SEEDED = True


# ---------- HTML/SVG video player ----------
TONE_GRADIENTS = {
    "teal":   ("#0F766E", "#14B8A6"),
    "amber":  ("#B45309", "#F59E0B"),
    "purple": ("#5B21B6", "#7C3AED"),
    "rose":   ("#9F1239", "#E11D48"),
    "green":  ("#065F46", "#15803D"),
    "blue":   ("#1E40AF", "#3B82F6"),
}


# Friendly CTA bank — randomly chosen per render so each video looks fresh
_CTA_LINES = [
    ("👉 Book on servia.ae",                "https://servia.ae/book.html"),
    ("Get your slot — servia.ae",            "https://servia.ae/book.html"),
    ("Tap to book in 60s",                   "https://servia.ae/book.html"),
    ("Bundle 2+ services, save 15%",         "https://servia.ae/cart.html"),
    ("Same-day pros · servia.ae",            "https://servia.ae/services.html"),
    ("Need help? Chat with Servia",          "https://servia.ae/?chat=1"),
    ("Watch more videos",                    "https://servia.ae/videos.html"),
    ("See live coverage map",                "https://servia.ae/coverage.html"),
    ("Refer + climb · 20% off forever",      "https://servia.ae/share-rewards.html"),
    ("Get instant quote",                    "https://servia.ae/book.html"),
]


def _pick_cta(slug: str) -> tuple[str, str]:
    # Deterministic pick per slug so the same video always shows the same CTA
    # but the catalogue overall has variety
    idx = sum(ord(c) for c in (slug or "x")) % len(_CTA_LINES)
    return _CTA_LINES[idx]


def render_video_html(v: dict) -> str:
    a, b = TONE_GRADIENTS.get(v.get("tone") or "teal", TONE_GRADIENTS["teal"])
    scenes = v["scenes"]
    n = len(scenes)
    per = max(2.5, v.get("duration_sec", 18) / n)
    total = per * n
    aspect = v.get("aspect") or "16x9"
    aspect_css = {"16x9": "16/9", "9x16": "9/16", "1x1": "1/1"}.get(aspect, "16/9")
    is_vertical = aspect == "9x16"
    is_square = aspect == "1x1"
    cta_text, cta_href = _pick_cta(v.get("slug") or v.get("title") or "x")
    # Build N scene divs with staggered animation-delay
    scene_html = []
    for i, s in enumerate(scenes):
        anim = s.get("anim") or "wave"
        scene_html.append(
            f'<div class="scene scene-{anim}" style="animation-delay:{i*per:.2f}s">'
            f'  <div class="scene-text">{s["text"]}</div>'
            f'  <div class="scene-sub">{s["sub"]}</div>'
            f'</div>')
    mascot_src = "/mascot.svg" if v.get("mascot","default") == "default" else f"/mascots/{v['mascot']}.svg"
    title = v.get("title", "Servia")
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Servia video</title>
<style>
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:#0F172A; min-height:100vh; display:flex; align-items:center; justify-content:center; }}
.video {{ position:relative; width:min({"360px" if is_vertical else "640px" if is_square else "720px"}, 95vw); aspect-ratio: {aspect_css};
  background:linear-gradient(135deg,{a},{b}); border-radius:14px;
  box-shadow:0 24px 60px rgba(0,0,0,.4); overflow:hidden; color:#fff; }}
.video::before {{ content:""; position:absolute; inset:0;
  background-image: radial-gradient(circle at 20% 30%, rgba(255,255,255,.18) 0%, transparent 30%),
                    radial-gradient(circle at 80% 70%, rgba(255,255,255,.10) 0%, transparent 30%);
  pointer-events:none; }}
.brand {{ position:absolute; top:18px; left:20px; font-weight:800; font-size:14px;
  letter-spacing:.2em; text-transform:uppercase; opacity:.85; z-index:2; }}
.duration {{ position:absolute; top:18px; right:20px; font-size:11px;
  background:rgba(0,0,0,.18); padding:4px 8px; border-radius:999px; z-index:2; }}

.mascot-wrap {{ position:absolute; left:6%; bottom:8%; width:42%; height:80%;
  display:flex; align-items:flex-end; justify-content:center; z-index:2; }}
.mascot {{ width:100%; height:100%; object-fit:contain;
  filter: drop-shadow(0 8px 18px rgba(0,0,0,.35));
  animation: mascot-bob 3.4s ease-in-out infinite; }}
@keyframes mascot-bob {{ 0%,100% {{ transform: translateY(0) }} 50% {{ transform: translateY(-12px) }} }}

.scene-stack {{ position:absolute; right:6%; top:50%; transform:translateY(-50%);
  width:46%; max-width:420px; z-index:2; }}
.scene {{ position:absolute; left:0; right:0; top:0;
  opacity:0; transform:translateY(16px);
  animation: scene-fade {total}s linear infinite; }}
.scene-text {{ font-size:28px; font-weight:800; letter-spacing:-.01em;
  line-height:1.15; margin-bottom:8px; text-shadow:0 2px 6px rgba(0,0,0,.25); }}
.scene-sub {{ font-size:14px; opacity:.92; line-height:1.4;
  background:rgba(0,0,0,.18); display:inline-block; padding:5px 10px;
  border-radius:999px; backdrop-filter:blur(4px); }}

@keyframes scene-fade {{
  0%   {{ opacity:0; transform:translateY(16px) }}
  {(per*0.18/total*100):.1f}% {{ opacity:1; transform:translateY(0) }}
  {(per*0.85/total*100):.1f}% {{ opacity:1; transform:translateY(0) }}
  {(per/total*100):.1f}% {{ opacity:0; transform:translateY(-16px) }}
  100% {{ opacity:0; transform:translateY(-16px) }}
}}

/* Per-anim mascot flourishes */
.scene-wave   ~ .mascot-wrap .mascot {{ animation-name: mascot-bob }}
.scene-bounce ~ .mascot-wrap .mascot {{ animation: mascot-bounce 1.2s ease-in-out infinite }}
.scene-shake  ~ .mascot-wrap .mascot {{ animation: mascot-shake .8s ease-in-out infinite }}
.scene-point  ~ .mascot-wrap .mascot {{ animation: mascot-tilt 2.4s ease-in-out infinite }}
@keyframes mascot-bounce {{ 0%,100% {{ transform: translateY(0) scale(1) }} 50% {{ transform: translateY(-22px) scale(1.04) }} }}
@keyframes mascot-shake  {{ 0%,100% {{ transform: rotate(0) }} 25% {{ transform: rotate(-3deg) }} 75% {{ transform: rotate(3deg) }} }}
@keyframes mascot-tilt   {{ 0%,100% {{ transform: rotate(0) }} 50% {{ transform: rotate(8deg) translateX(8px) }} }}

.cta {{ position:absolute; bottom:14px; right:20px;
  background:#FCD34D; color:#7C2D12; padding:8px 16px; border-radius:999px;
  font-weight:800; font-size:13px; text-decoration:none;
  box-shadow:0 6px 18px rgba(0,0,0,.25); z-index:3; }}
.progress {{ position:absolute; left:0; bottom:0; right:0; height:3px;
  background:rgba(0,0,0,.18); z-index:3; }}
.progress::after {{ content:""; display:block; height:100%; width:0;
  background:#FCD34D; animation: progress {total}s linear infinite; }}
@keyframes progress {{ 0% {{ width:0 }} 100% {{ width:100% }} }}

@media (max-width:560px) {{
  .scene-stack {{ width:48%; max-width:none }}
  .scene-text {{ font-size:20px }}
  .scene-sub {{ font-size:12px }}
}}
</style>
</head>
<style>
.rich-scene-wrap{{position:absolute;inset:0;z-index:1;display:flex;align-items:center;justify-content:center;padding:0 4%;pointer-events:none}}
.rich-scene{{width:100%;height:auto;max-width:680px;max-height:65%;filter:drop-shadow(0 6px 14px rgba(0,0,0,.18))}}
.ironing-iron{{animation:iron-slide 2.4s ease-in-out infinite}}
@keyframes iron-slide{{0%,100%{{transform:translate(-30px,55px)}}50%{{transform:translate(30px,55px)}}}}
.ironing-steam{{animation:steam-rise 2s ease-in-out infinite;transform-origin:30px 40px}}
@keyframes steam-rise{{0%{{opacity:.8;transform:translateY(0) scale(1)}}100%{{opacity:0;transform:translateY(-30px) scale(1.3)}}}}
.ac-stream path{{animation:ac-blow 1.6s ease-in-out infinite;transform-origin:0 50px}}
@keyframes ac-blow{{0%,100%{{opacity:.3}}50%{{opacity:1;transform:translateY(8px)}}}}
.clean-sparkles text{{animation:sparkle 1.6s ease-in-out infinite;transform-origin:center}}
.clean-sparkles text:nth-child(1){{animation-delay:0s}}
.clean-sparkles text:nth-child(2){{animation-delay:.4s}}
.clean-sparkles text:nth-child(3){{animation-delay:.8s}}
.clean-sparkles text:nth-child(4){{animation-delay:.2s}}
.clean-sparkles text:nth-child(5){{animation-delay:.6s}}
@keyframes sparkle{{0%,100%{{opacity:.3;transform:scale(.8)}}50%{{opacity:1;transform:scale(1.2)}}}}
.mopping{{animation:mop-sweep 1.4s ease-in-out infinite;transform-origin:10px -10px}}
@keyframes mop-sweep{{0%,100%{{transform:rotate(-15deg)}}50%{{transform:rotate(15deg)}}}}
.wrench-anim{{animation:wrench-turn 1s linear infinite;transform-origin:0 0}}
@keyframes wrench-turn{{0%{{transform:rotate(0deg)}}100%{{transform:rotate(360deg)}}}}
.drip-stop{{animation:drip-fade 3s ease-in-out infinite}}
@keyframes drip-fade{{0%{{opacity:1}}80%,100%{{opacity:0}}}}
.car-bubbles circle{{animation:bubble-rise 2s ease-out infinite}}
.car-bubbles circle:nth-child(1){{animation-delay:0s}}
.car-bubbles circle:nth-child(2){{animation-delay:.5s}}
.car-bubbles circle:nth-child(3){{animation-delay:1s}}
.car-bubbles circle:nth-child(4){{animation-delay:1.5s}}
@keyframes bubble-rise{{0%{{transform:translateY(0);opacity:.7}}100%{{transform:translateY(-50px);opacity:0}}}}
.sponge-anim{{animation:sponge-scrub 1.2s ease-in-out infinite;transform-origin:32px 27px}}
@keyframes sponge-scrub{{0%,100%{{transform:translateX(0)}}50%{{transform:translateX(40px)}}}}
.pool-water{{animation:water-shimmer 3s ease-in-out infinite}}
@keyframes water-shimmer{{0%,100%{{filter:brightness(1)}}50%{{filter:brightness(1.2)}}}}
.net-anim{{animation:net-skim 2s ease-in-out infinite;transform-origin:90px 48px}}
@keyframes net-skim{{0%,100%{{transform:translateX(0)}}50%{{transform:translateX(80px)}}}}
.grass-anim path{{animation:grass-sway 2s ease-in-out infinite}}
.grass-anim path:nth-child(2){{animation-delay:.3s}}
.grass-anim path:nth-child(3){{animation-delay:.6s}}
.grass-anim path:nth-child(4){{animation-delay:.9s}}
@keyframes grass-sway{{0%,100%{{transform:rotate(-3deg)}}50%{{transform:rotate(3deg)}}}}
.trim-anim{{animation:trim-snip .6s ease-in-out infinite;transform-origin:20px 0}}
@keyframes trim-snip{{0%,100%{{transform:rotate(0)}}50%{{transform:rotate(-15deg)}}}}
.spray-anim ellipse{{animation:spray-burst 1.2s ease-out infinite}}
@keyframes spray-burst{{0%{{transform:translateX(0);opacity:1}}100%{{transform:translateX(30px);opacity:0}}}}
.pest-out text{{animation:pest-flee 3s ease-out infinite}}
@keyframes pest-flee{{0%,80%{{opacity:.5;transform:translateX(0)}}100%{{opacity:0;transform:translateX(150px) rotate(45deg)}}}}
.default-sparkle text{{animation:sparkle 1.8s ease-in-out infinite}}
.default-sparkle text:nth-child(2){{animation-delay:.4s}}
.default-sparkle text:nth-child(3){{animation-delay:.8s}}
.default-sparkle text:nth-child(4){{animation-delay:1.2s}}
@media(max-width:560px){{.rich-scene{{max-height:55%}}}}
</style>
</head>
<body>
<div class="video" role="img" aria-label="{title}">
  <div class="brand">SERVIA</div>
  <div class="duration">{int(v.get('duration_sec',18))}s · loop · 🔊</div>
  <div class="rich-scene-wrap">{_scene_composition(v.get('mascot') or 'default', v.get('slug',''))}</div>
  <div class="scene-stack">
    {''.join(scene_html)}
  </div>
  <a class="cta" href="{cta_href}">{cta_text} →</a>
  <div class="progress"></div>
</div>
<!-- Optional ambient chime via Web Audio (free, generated, no external file).
     Triggered ONLY on user interaction to comply with autoplay policies. -->
<script>
(function(){{
  let played=false;
  function chime(){{
    if(played)return;played=true;
    try{{
      const ctx=new(window.AudioContext||window.webkitAudioContext)();
      const notes=[523.25,659.25,783.99]; // C5 E5 G5 — bright major chord
      const now=ctx.currentTime;
      notes.forEach((f,i)=>{{
        const o=ctx.createOscillator(),g=ctx.createGain();
        o.type="sine";o.frequency.value=f;
        g.gain.setValueAtTime(0,now+i*0.1);g.gain.linearRampToValueAtTime(0.08,now+i*0.1+0.05);
        g.gain.exponentialRampToValueAtTime(0.001,now+i*0.1+0.6);
        o.connect(g);g.connect(ctx.destination);o.start(now+i*0.1);o.stop(now+i*0.1+0.7);
      }});
    }}catch(_){{}}
  }}
  document.addEventListener("click",chime,{{once:true}});
  document.addEventListener("touchstart",chime,{{once:true,passive:true}});
}})();
</script>
</body></html>"""


def _scene_composition(mascot: str, slug: str) -> str:
    """Rich multi-character scene per service — mascot WITH a customer figure +
    contextual props + animated foreground (e.g. Servia ironing while customer
    sits happy on sofa, Servia AC tech repairing unit while customer relaxes)."""
    SCENES = {
        "maid": '''
<svg class="rich-scene" viewBox="0 0 720 320" preserveAspectRatio="xMidYMid meet">
  <!-- Customer (happy on couch) -->
  <g transform="translate(560,160)">
    <ellipse cx="0" cy="80" rx="60" ry="14" fill="rgba(0,0,0,.12)"/>
    <rect x="-46" y="20" width="92" height="50" rx="14" fill="#7C3AED"/>
    <rect x="-50" y="50" width="100" height="22" rx="6" fill="#5B21B6"/>
    <circle cx="0" cy="0" r="22" fill="#FCD34D"/>
    <circle cx="-6" cy="-3" r="2" fill="#0F172A"/><circle cx="6" cy="-3" r="2" fill="#0F172A"/>
    <path d="M -8 6 Q 0 12 8 6" stroke="#0F172A" stroke-width="2" fill="none" stroke-linecap="round"/>
    <text x="-30" y="-30" font-size="20">😊</text>
  </g>
  <!-- Servia mascot ironing -->
  <g transform="translate(180,150)">
    <!-- Ironing board -->
    <rect x="-90" y="60" width="180" height="14" rx="6" fill="#fff" stroke="#94A3B8" stroke-width="2"/>
    <rect x="-70" y="74" width="6" height="50" fill="#94A3B8"/>
    <rect x="64" y="74" width="6" height="50" fill="#94A3B8"/>
    <!-- Steam from iron, animated -->
    <g class="ironing-steam">
      <ellipse cx="20" cy="40" rx="6" ry="10" fill="rgba(255,255,255,.7)"/>
      <ellipse cx="34" cy="32" rx="5" ry="8" fill="rgba(255,255,255,.6)"/>
      <ellipse cx="48" cy="40" rx="4" ry="7" fill="rgba(255,255,255,.5)"/>
    </g>
    <!-- Iron, moving back-and-forth -->
    <g class="ironing-iron" transform="translate(0,55)">
      <rect x="-18" y="-8" width="36" height="14" rx="4" fill="#475569"/>
      <rect x="-22" y="3" width="44" height="8" rx="3" fill="#1F2937"/>
    </g>
    <!-- Mascot body (Servia) -->
    <ellipse cx="-50" cy="40" rx="34" ry="42" fill="#F472B6"/>
    <circle cx="-50" cy="-10" r="28" fill="#FCD34D"/>
    <rect x="-65" y="-30" width="30" height="14" rx="3" fill="#fff"/>
    <text x="-58" y="-19" font-size="9" font-weight="800" fill="#0F766E">SERVIA</text>
    <circle cx="-58" cy="-15" r="2" fill="#0F172A"/><circle cx="-44" cy="-15" r="2" fill="#0F172A"/>
    <path d="M -56 -5 Q -50 0 -44 -5" stroke="#0F172A" stroke-width="2" fill="none" stroke-linecap="round"/>
  </g>
</svg>''',
        "ac": '''
<svg class="rich-scene" viewBox="0 0 720 320" preserveAspectRatio="xMidYMid meet">
  <!-- Customer relaxing -->
  <g transform="translate(560,180)">
    <ellipse cx="0" cy="70" rx="50" ry="12" fill="rgba(0,0,0,.12)"/>
    <rect x="-36" y="20" width="72" height="44" rx="14" fill="#0EA5E9"/>
    <circle cx="0" cy="-2" r="20" fill="#FCD34D"/>
    <text x="-12" y="-18" font-size="18">🥶</text>
    <text x="-30" y="50" font-size="11" fill="#fff" font-weight="700">"So cold!"</text>
  </g>
  <!-- AC unit on wall, mascot servicing -->
  <g transform="translate(160,80)">
    <rect x="-70" y="0" width="140" height="48" rx="8" fill="#fff" stroke="#94A3B8" stroke-width="2"/>
    <line x1="-60" y1="14" x2="60" y2="14" stroke="#94A3B8" stroke-width="2"/>
    <line x1="-60" y1="22" x2="60" y2="22" stroke="#94A3B8" stroke-width="2"/>
    <line x1="-60" y1="30" x2="60" y2="30" stroke="#94A3B8" stroke-width="2"/>
    <!-- Frost streams animated -->
    <g class="ac-stream">
      <path d="M -50 50 L -55 80" stroke="#06B6D4" stroke-width="3" stroke-linecap="round"/>
      <path d="M -20 50 L -25 90" stroke="#06B6D4" stroke-width="3" stroke-linecap="round"/>
      <path d="M  10 50 L   5 95" stroke="#06B6D4" stroke-width="3" stroke-linecap="round"/>
      <path d="M  40 50 L  35 85" stroke="#06B6D4" stroke-width="3" stroke-linecap="round"/>
    </g>
  </g>
  <!-- Mascot AC tech with ladder -->
  <g transform="translate(220,180)">
    <line x1="-30" y1="0" x2="-30" y2="80" stroke="#94A3B8" stroke-width="3"/>
    <line x1="10" y1="0" x2="10" y2="80" stroke="#94A3B8" stroke-width="3"/>
    <line x1="-30" y1="20" x2="10" y2="20" stroke="#94A3B8" stroke-width="3"/>
    <line x1="-30" y1="40" x2="10" y2="40" stroke="#94A3B8" stroke-width="3"/>
    <ellipse cx="-10" cy="-10" rx="22" ry="28" fill="#0F766E"/>
    <circle cx="-10" cy="-40" r="18" fill="#FCD34D"/>
    <rect x="-22" y="-58" width="24" height="10" rx="3" fill="#1F2937"/>
    <text x="-17" y="-50" font-size="8" font-weight="800" fill="#fff">AC PRO</text>
  </g>
</svg>''',
        "cleaning": '''
<svg class="rich-scene" viewBox="0 0 720 320" preserveAspectRatio="xMidYMid meet">
  <!-- Sparkle background animated -->
  <g class="clean-sparkles">
    <text x="100" y="80" font-size="28">✨</text>
    <text x="280" y="100" font-size="22">✨</text>
    <text x="500" y="60" font-size="26">✨</text>
    <text x="380" y="180" font-size="20">💧</text>
    <text x="150" y="240" font-size="22">💧</text>
  </g>
  <!-- Customer admiring clean room -->
  <g transform="translate(560,170)">
    <ellipse cx="0" cy="80" rx="55" ry="13" fill="rgba(0,0,0,.12)"/>
    <rect x="-36" y="20" width="72" height="60" rx="14" fill="#0F766E"/>
    <circle cx="0" cy="-2" r="22" fill="#FCD34D"/>
    <circle cx="-7" cy="-5" r="2" fill="#0F172A"/><circle cx="7" cy="-5" r="2" fill="#0F172A"/>
    <path d="M -8 6 Q 0 14 8 6" stroke="#0F172A" stroke-width="2" fill="none"/>
    <text x="-15" y="-30" font-size="18">😍</text>
  </g>
  <!-- Mascot mopping, mop animated -->
  <g transform="translate(220,190)">
    <ellipse cx="0" cy="50" rx="60" ry="10" fill="rgba(0,0,0,.10)"/>
    <ellipse cx="-20" cy="0" rx="26" ry="34" fill="#14B8A6"/>
    <circle cx="-20" cy="-36" r="20" fill="#FCD34D"/>
    <rect x="-32" y="-50" width="24" height="10" rx="3" fill="#fff"/>
    <text x="-30" y="-43" font-size="8" font-weight="800" fill="#0F766E">SERVIA</text>
    <!-- Mop -->
    <g class="mopping">
      <line x1="10" y1="-10" x2="55" y2="50" stroke="#92400E" stroke-width="4" stroke-linecap="round"/>
      <ellipse cx="60" cy="56" rx="18" ry="6" fill="#FCD34D"/>
    </g>
  </g>
</svg>''',
        "handyman": '''
<svg class="rich-scene" viewBox="0 0 720 320" preserveAspectRatio="xMidYMid meet">
  <!-- Customer waiting -->
  <g transform="translate(560,180)">
    <ellipse cx="0" cy="70" rx="50" ry="12" fill="rgba(0,0,0,.12)"/>
    <rect x="-32" y="20" width="64" height="50" rx="12" fill="#E11D48"/>
    <circle cx="0" cy="-2" r="20" fill="#FCD34D"/>
    <text x="-10" y="-22" font-size="16">🙌</text>
    <text x="-26" y="50" font-size="10" fill="#fff" font-weight="700">"Thanks!"</text>
  </g>
  <!-- Mascot fixing pipe with wrench -->
  <g transform="translate(200,170)">
    <!-- Pipe -->
    <rect x="-80" y="-10" width="160" height="20" rx="4" fill="#94A3B8"/>
    <circle cx="-30" cy="0" r="8" fill="#475569"/>
    <!-- Water drop fixed (animated drying) -->
    <text class="drip-stop" x="-32" y="20" font-size="14">💧</text>
    <!-- Mascot -->
    <ellipse cx="20" cy="50" rx="26" ry="34" fill="#E11D48"/>
    <circle cx="20" cy="14" r="20" fill="#FCD34D"/>
    <rect x="8" y="-6" width="24" height="10" rx="3" fill="#fff"/>
    <text x="10" y="2" font-size="8" font-weight="800" fill="#E11D48">SERVIA</text>
    <!-- Wrench animated -->
    <g class="wrench-anim" transform="translate(-25,0)">
      <line x1="0" y1="0" x2="-30" y2="-30" stroke="#1F2937" stroke-width="6" stroke-linecap="round"/>
      <circle cx="-30" cy="-30" r="8" fill="#475569"/>
    </g>
  </g>
</svg>''',
        "car": '''
<svg class="rich-scene" viewBox="0 0 720 320" preserveAspectRatio="xMidYMid meet">
  <!-- Customer, satisfied next to clean car -->
  <g transform="translate(580,200)">
    <ellipse cx="0" cy="50" rx="40" ry="10" fill="rgba(0,0,0,.10)"/>
    <rect x="-26" y="0" width="52" height="40" rx="10" fill="#3B82F6"/>
    <circle cx="0" cy="-18" r="18" fill="#FCD34D"/>
    <text x="-12" y="-32" font-size="16">😎</text>
  </g>
  <!-- Car with bubbles + sponge -->
  <g transform="translate(280,200)">
    <ellipse cx="0" cy="60" rx="120" ry="14" fill="rgba(0,0,0,.14)"/>
    <rect x="-100" y="-10" width="200" height="40" rx="14" fill="#F59E0B"/>
    <rect x="-80" y="-40" width="140" height="32" rx="8" fill="#FCD34D"/>
    <circle cx="-70" cy="40" r="14" fill="#1F2937"/><circle cx="-70" cy="40" r="6" fill="#94A3B8"/>
    <circle cx="60" cy="40" r="14" fill="#1F2937"/><circle cx="60" cy="40" r="6" fill="#94A3B8"/>
    <!-- Bubbles animated -->
    <g class="car-bubbles">
      <circle cx="0" cy="-30" r="8" fill="rgba(255,255,255,.7)"/>
      <circle cx="-40" cy="-50" r="6" fill="rgba(255,255,255,.6)"/>
      <circle cx="50" cy="-55" r="7" fill="rgba(255,255,255,.65)"/>
      <circle cx="20" cy="-70" r="5" fill="rgba(255,255,255,.5)"/>
    </g>
  </g>
  <!-- Mascot in cap, sponge -->
  <g transform="translate(140,180)">
    <ellipse cx="0" cy="40" rx="22" ry="30" fill="#0EA5E9"/>
    <circle cx="0" cy="0" r="20" fill="#FCD34D"/>
    <path d="M -22 -8 Q 0 -22 22 -8 L 22 0 L -22 0 Z" fill="#1F2937"/>
    <text x="-12" y="-3" font-size="8" font-weight="800" fill="#fff">SERVIA</text>
    <!-- Sponge -->
    <rect class="sponge-anim" x="22" y="20" width="20" height="14" rx="3" fill="#FCD34D"/>
  </g>
</svg>''',
        "pool": '''
<svg class="rich-scene" viewBox="0 0 720 320" preserveAspectRatio="xMidYMid meet">
  <!-- Pool water animated -->
  <g class="pool-water">
    <rect x="40" y="180" width="640" height="100" rx="10" fill="#3B82F6"/>
    <ellipse cx="200" cy="200" rx="60" ry="10" fill="rgba(255,255,255,.3)"/>
    <ellipse cx="450" cy="220" rx="80" ry="12" fill="rgba(255,255,255,.25)"/>
  </g>
  <!-- Customer floating happily -->
  <g transform="translate(560,200)">
    <ellipse cx="0" cy="0" rx="40" ry="14" fill="#FCD34D"/>
    <circle cx="0" cy="-10" r="14" fill="#FCD34D"/>
    <text x="-10" y="-20" font-size="16">🏖️</text>
  </g>
  <!-- Mascot with pool net -->
  <g transform="translate(150,160)">
    <ellipse cx="0" cy="30" rx="22" ry="28" fill="#0EA5E9"/>
    <circle cx="0" cy="-4" r="20" fill="#FCD34D"/>
    <line x1="20" y1="0" x2="80" y2="40" stroke="#92400E" stroke-width="4" stroke-linecap="round"/>
    <ellipse class="net-anim" cx="90" cy="48" rx="20" ry="6" fill="rgba(255,255,255,.6)" stroke="#1F2937" stroke-width="2"/>
  </g>
</svg>''',
        "garden": '''
<svg class="rich-scene" viewBox="0 0 720 320" preserveAspectRatio="xMidYMid meet">
  <rect x="0" y="220" width="720" height="100" fill="#15803D"/>
  <g class="grass-anim">
    <path d="M 100 220 q 4 -20 8 0" stroke="#0F766E" stroke-width="3" fill="none"/>
    <path d="M 200 220 q 4 -25 8 0" stroke="#0F766E" stroke-width="3" fill="none"/>
    <path d="M 320 220 q 4 -22 8 0" stroke="#0F766E" stroke-width="3" fill="none"/>
    <path d="M 460 220 q 4 -24 8 0" stroke="#0F766E" stroke-width="3" fill="none"/>
  </g>
  <!-- Customer enjoying tea -->
  <g transform="translate(580,180)">
    <rect x="-30" y="0" width="60" height="44" rx="10" fill="#0F766E"/>
    <circle cx="0" cy="-20" r="20" fill="#FCD34D"/>
    <text x="-12" y="-26" font-size="14">☕</text>
  </g>
  <!-- Mascot trimming hedge -->
  <g transform="translate(200,180)">
    <ellipse cx="0" cy="30" rx="22" ry="28" fill="#15803D"/>
    <circle cx="0" cy="-4" r="20" fill="#FCD34D"/>
    <g class="trim-anim">
      <line x1="20" y1="-5" x2="50" y2="-25" stroke="#475569" stroke-width="3"/>
      <line x1="20" y1="0"  x2="50" y2="-15" stroke="#475569" stroke-width="3"/>
    </g>
    <!-- Hedge -->
    <ellipse cx="100" cy="20" rx="40" ry="22" fill="#15803D"/>
  </g>
</svg>''',
        "pest": '''
<svg class="rich-scene" viewBox="0 0 720 320" preserveAspectRatio="xMidYMid meet">
  <g class="pest-out">
    <text x="500" y="100" font-size="22" opacity=".5">🪲</text>
    <text x="540" y="80"  font-size="20" opacity=".5">🐛</text>
    <text x="600" y="140" font-size="18" opacity=".5">🪳</text>
  </g>
  <!-- Customer relaxing pest-free -->
  <g transform="translate(560,200)">
    <rect x="-30" y="0" width="60" height="40" rx="10" fill="#15803D"/>
    <circle cx="0" cy="-20" r="20" fill="#FCD34D"/>
    <text x="-12" y="-30" font-size="16">😌</text>
  </g>
  <!-- Mascot with sprayer -->
  <g transform="translate(200,180)">
    <ellipse cx="0" cy="30" rx="22" ry="28" fill="#15803D"/>
    <circle cx="0" cy="-4" r="20" fill="#FCD34D"/>
    <rect x="22" y="0" width="14" height="22" rx="3" fill="#1F2937"/>
    <g class="spray-anim">
      <ellipse cx="50" cy="6" rx="5" ry="3" fill="rgba(150,150,150,.5)"/>
      <ellipse cx="60" cy="3" rx="4" ry="2" fill="rgba(150,150,150,.4)"/>
      <ellipse cx="70" cy="0" rx="3" ry="2" fill="rgba(150,150,150,.3)"/>
    </g>
  </g>
</svg>''',
        "default": '''
<svg class="rich-scene" viewBox="0 0 720 320" preserveAspectRatio="xMidYMid meet">
  <g class="default-sparkle">
    <text x="120" y="100" font-size="32">✨</text>
    <text x="280" y="80"  font-size="28">⭐</text>
    <text x="500" y="100" font-size="30">✨</text>
    <text x="600" y="60"  font-size="24">⭐</text>
  </g>
  <g transform="translate(360,200)">
    <ellipse cx="0" cy="60" rx="80" ry="14" fill="rgba(0,0,0,.18)"/>
    <ellipse cx="0" cy="0" rx="50" ry="62" fill="#0F766E"/>
    <circle cx="0" cy="-50" r="36" fill="#FCD34D"/>
    <rect x="-20" y="-78" width="40" height="14" rx="3" fill="#fff"/>
    <text x="-15" y="-67" font-size="9" font-weight="800" fill="#0F766E">SERVIA</text>
    <circle cx="-12" cy="-55" r="3" fill="#0F172A"/><circle cx="12" cy="-55" r="3" fill="#0F172A"/>
    <path d="M -10 -42 Q 0 -34 10 -42" stroke="#0F172A" stroke-width="3" fill="none" stroke-linecap="round"/>
  </g>
</svg>''',
    }
    return SCENES.get(mascot, SCENES["default"])


def _scene_prop_svg(mascot: str) -> str:
    """Animated SVG prop next to the mascot — gives each video its own
    visual context (car for chauffeur, steam for cleaning, AC unit for AC,
    tools for handyman, etc) instead of always plain text+mascot."""
    PROPS = {
        "car": (
            '<svg class="scene-prop car-anim" viewBox="0 0 200 120" '
            'style="position:absolute;right:-20%;bottom:0;width:80%;height:auto;opacity:.85;pointer-events:none">'
            '<rect x="20" y="60" width="160" height="40" rx="14" fill="#F59E0B"/>'
            '<rect x="40" y="35" width="110" height="30" rx="8" fill="#FCD34D"/>'
            '<circle cx="55" cy="100" r="14" fill="#1F2937"/>'
            '<circle cx="55" cy="100" r="6" fill="#94A3B8"/>'
            '<circle cx="155" cy="100" r="14" fill="#1F2937"/>'
            '<circle cx="155" cy="100" r="6" fill="#94A3B8"/>'
            '<rect x="170" y="68" width="14" height="6" fill="#fff" opacity=".7"/>'
            '</svg>'),
        "ac": (
            '<svg class="scene-prop steam-anim" viewBox="0 0 100 100" '
            'style="position:absolute;right:-10%;top:-10%;width:60%;height:auto;opacity:.85;pointer-events:none">'
            '<rect x="10" y="10" width="80" height="40" rx="6" fill="#fff" stroke="#94A3B8" stroke-width="2"/>'
            '<line x1="20" y1="22" x2="80" y2="22" stroke="#94A3B8" stroke-width="2"/>'
            '<line x1="20" y1="30" x2="80" y2="30" stroke="#94A3B8" stroke-width="2"/>'
            '<line x1="20" y1="38" x2="80" y2="38" stroke="#94A3B8" stroke-width="2"/>'
            '<text x="30" y="65" font-size="14" fill="#fff">❄️ ❄️ ❄️</text>'
            '</svg>'),
        "cleaning": (
            '<svg class="scene-prop steam-anim" viewBox="0 0 100 100" '
            'style="position:absolute;right:-5%;top:-5%;width:55%;height:auto;opacity:.7;pointer-events:none">'
            '<text x="20" y="40" font-size="44">✨</text>'
            '<text x="50" y="70" font-size="32">🧼</text>'
            '<text x="20" y="90" font-size="28">💧</text>'
            '</svg>'),
        "handyman": (
            '<svg class="scene-prop tool-anim" viewBox="0 0 100 100" '
            'style="position:absolute;right:-5%;top:-10%;width:55%;height:auto;opacity:.85;pointer-events:none">'
            '<text x="10" y="50" font-size="46">🔧</text>'
            '<text x="50" y="80" font-size="36">🔩</text>'
            '</svg>'),
        "pool": (
            '<svg class="scene-prop water-anim" viewBox="0 0 100 100" '
            'style="position:absolute;right:-10%;bottom:0;width:65%;height:auto;opacity:.7;pointer-events:none">'
            '<ellipse cx="50" cy="80" rx="42" ry="14" fill="#3B82F6" opacity=".5"/>'
            '<text x="35" y="60" font-size="36">🏊</text>'
            '</svg>'),
        "garden": (
            '<svg class="scene-prop tool-anim" viewBox="0 0 100 100" '
            'style="position:absolute;right:0;bottom:0;width:55%;height:auto;opacity:.85;pointer-events:none">'
            '<text x="20" y="60" font-size="42">🌿</text>'
            '<text x="55" y="85" font-size="32">🌳</text>'
            '</svg>'),
        "pest": (
            '<svg class="scene-prop tool-anim" viewBox="0 0 100 100" '
            'style="position:absolute;right:0;top:5%;width:55%;height:auto;opacity:.7;pointer-events:none">'
            '<text x="20" y="50" font-size="40">🪲</text>'
            '<text x="60" y="80" font-size="32">🚫</text>'
            '</svg>'),
        "maid": (
            '<svg class="scene-prop steam-anim" viewBox="0 0 100 100" '
            'style="position:absolute;right:0;top:5%;width:50%;height:auto;opacity:.7;pointer-events:none">'
            '<text x="30" y="60" font-size="40">🧹</text>'
            '</svg>'),
        "default": "",
    }
    return PROPS.get(mascot, "")


# ---------- public endpoints ----------
@public_router.get("/list")
def list_videos_public(service_id: str | None = None, emirate: str | None = None,
                       kind: str | None = None, limit: int = 100):
    seed_videos_if_empty()
    where, params = [], []
    if service_id: where.append("service_id = ?"); params.append(service_id)
    if emirate:    where.append("emirate = ?");    params.append(emirate)
    if kind:       where.append("kind = ?");       params.append(kind)
    sql = ("SELECT slug, title, mascot, tone, duration_sec, view_count, "
           "service_id, emirate, kind FROM videos")
    if where: sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(max(1, min(limit, 200)))
    with db.connect() as c:
        try: rows = c.execute(sql, params).fetchall()
        except Exception: rows = []
    return {"videos": [db.row_to_dict(r) for r in rows], "count": len(rows)}


@public_router.get("/play/{slug}", response_class=HTMLResponse)
def play_video(slug: str, aspect: str = "16x9"):
    """`?aspect=` accepts 16x9 (default · landscape · YouTube/Insta feed),
    9x16 (vertical · TikTok/Reels/Shorts), or 1x1 (square · Insta feed/post)."""
    seed_videos_if_empty()
    with db.connect() as c:
        try:
            r = c.execute("SELECT * FROM videos WHERE slug=?", (slug,)).fetchone()
        except Exception: r = None
    if not r:
        raise HTTPException(404, "Video not found")
    v = db.row_to_dict(r) or {}
    try: v["scenes"] = _json.loads(v.get("scenes_json") or "[]")
    except Exception: v["scenes"] = []
    v["aspect"] = aspect if aspect in ("16x9", "9x16", "1x1") else "16x9"
    with db.connect() as c:
        try: c.execute("UPDATE videos SET view_count=view_count+1 WHERE slug=?", (slug,))
        except Exception: pass
    return HTMLResponse(render_video_html(v))


# ---------- admin endpoints ----------
class GenerateBody(BaseModel):
    topic: str
    mascot: Optional[str] = "default"
    tone: Optional[str] = "teal"
    target_seconds: Optional[int] = 18


@admin_router.get("/list")
def list_videos_admin():
    seed_videos_if_empty()
    return list_videos_public()


@admin_router.post("/generate")
async def generate_video(body: GenerateBody):
    """Use the configured AI router to script a new mascot video.
    The model returns 4-6 scenes as JSON, we save it."""
    from . import ai_router
    cfg = ai_router._load_cfg()
    target = (cfg.get("defaults") or {}).get("video", "anthropic/claude-opus-4-7")
    if "/" not in target:
        target = "anthropic/" + target
    provider, model = target.split("/", 1)
    prompt = (
        "You write Servia mascot-video scripts. Servia is a UAE home-services platform.\n"
        f"Topic: {body.topic}\n"
        "Output a JSON array of 4 to 5 scenes. Each scene has: 'text' (max 36 chars, "
        "punchy headline), 'sub' (max 60 chars, supporting line), 'anim' (one of "
        "'wave', 'bounce', 'shake', 'point').\n"
        "Style: friendly, concrete UAE context, real numbers, no AI mannerisms. "
        "Use AED prices if relevant. End with a CTA-style scene.\n"
        "Output ONLY the JSON array, no markdown, no commentary."
    )
    res = await ai_router.call_model(provider, model, prompt, cfg)
    if not res.get("ok"):
        raise HTTPException(400, res.get("error") or "model call failed")
    txt = (res.get("text") or "").strip()
    # Extract JSON
    if "```" in txt:
        import re as _re
        m = _re.search(r"```(?:json)?\s*(\[.*?\])\s*```", txt, _re.S)
        if m: txt = m.group(1)
    if "[" in txt and "]" in txt:
        txt = txt[txt.index("["): txt.rindex("]") + 1]
    try:
        scenes = _json.loads(txt)
        assert isinstance(scenes, list) and len(scenes) >= 3
    except Exception:
        raise HTTPException(500, f"Could not parse model output: {txt[:200]}")

    slug = "ai-" + "".join(c.lower() if c.isalnum() else "-" for c in body.topic).strip("-")[:80]
    slug = slug + "-" + _dt.datetime.utcnow().strftime("%H%M%S")
    title = body.topic[:120]
    duration = body.target_seconds or 18
    seed_videos_if_empty()
    with db.connect() as c:
        try:
            c.execute(
                "INSERT INTO videos(slug, title, mascot, tone, scenes_json, duration_sec, created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (slug, title, body.mascot or "default", body.tone or "teal",
                 _json.dumps(scenes), duration,
                 _dt.datetime.utcnow().isoformat() + "Z"))
        except Exception as e:
            raise HTTPException(500, f"db insert failed: {e}")
    return {"ok": True, "slug": slug, "title": title, "scenes": scenes,
            "model": target, "url": f"/api/videos/play/{slug}"}


@admin_router.delete("/{slug}")
def delete_video(slug: str):
    with db.connect() as c:
        c.execute("DELETE FROM videos WHERE slug=?", (slug,))
    return {"ok": True}
