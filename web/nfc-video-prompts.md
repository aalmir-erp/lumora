# Servia visual asset prompts — videos + still images

This file is the single source of truth for every Servia social/web/ad
asset prompt. Two sections below: **(A) STILL-IMAGE PROMPT TEMPLATE**
matched to the photo-realistic style of our hero shots in
`/web/img/recovery/` (Burj Khalifa skyline, yellow-and-teal Servia
truck, distressed driver, NFC tap close-up). Use it for Midjourney 7,
DALL-E 3, Flux 1.1 Pro, Imagen 3, Ideogram 2.0. **(B) the original
50-video script collection** for Veo 3 / Runway / Sora.

---

## A. STILL-IMAGE PROMPT TEMPLATE (use for ALL services)

### A.1 Master style block — paste at the top of EVERY image prompt

```
Photo-realistic editorial advertising photograph, shot on Canon R5 with
RF 35mm f/1.4 lens, golden-hour cinematic lighting (warm 4500K key
light + soft fill), shallow depth of field at f/2.0, ultra-detailed
skin texture, subtle film grain, high dynamic range. Setting: United
Arab Emirates — recognisable but not generic (Burj Khalifa silhouette
at distance, Sheikh Zayed Road, Marina towers, Sharjah corniche, Abu
Dhabi mosques, Al Ain palm groves — pick whichever matches the service
context). Wardrobe: respect the local culture (Emirati kandura/abaya
where appropriate, modern smart-casual for expats).

Servia brand identity (MUST appear, every shot):
  · Servia tow trucks / vans: mustard yellow #FCD34D body + deep teal
    #0F766E lower panels and hood, "servia" in lowercase teal logo on
    side, "سيرفيا" Arabic logo below it, UAE plate "12345" on the
    front, white roof beacon + LED strip, 3 wheels with chrome rims.
  · Servia uniform: teal polo shirt with mustard "servia" embroidered
    chest patch, dark slacks, white sneakers.
  · Servia phone UI: green-confirm pill "✅ Booked · AED <X> · <when>"
    bottom-third of phone screen, watch shows same on AMOLED face.
  · Optional NFC sticker visible in scene: 32×32mm yellow square with
    teal "NFC" + Servia mark + "TAP" caret.

Composition:
  · 1:1 square OR 4:5 portrait OR 9:16 reel — declare in prompt.
  · Two-panel split-frame style works great for before/after.
  · Headline-ready: leave 30 % top whitespace for the burned-in
    English+Arabic copy ("TAP ONCE. RECOVERY ON THE WAY." +
    "اضغط مرة. المساعدة في الطريق.").
  · Bottom-right: small Servia logo lockup (English + Arabic).

NEGATIVE prompts (always include): cartoonish, low-poly, illustration,
3D render, anime, plastic skin, melting, deformed wheels, distorted
hands, extra fingers, misspelled "servia", bus, taxi, Uber, blue lights,
fake blur, watermark, signature, Stock-Adobe text.
```

### A.2 Per-service variant blocks

Pick the master style block above + ONE of these scene blocks below.
Replace `<PLACEHOLDER>` brackets with concrete details.

#### Vehicle recovery (the reference set)
```
Scene: a Black/<COLOUR> <CAR_MODEL> with bonnet open at the side of
Sheikh Zayed Road / Hatta highway / Al Quoz industrial street at dusk,
hazard triangle behind it. <DRIVER_PROFILE: e.g. mid-30s Emirati man
in white kandura | South-Asian woman in modest abaya | European expat
in business shirt> looking calm but concerned, holding their phone
1m from a Servia NFC sticker on the dashboard, pre-tap moment.
Yellow-and-teal Servia tow truck approaches in the right third of
the frame, headlights on. Headline: "TAP ONCE. RECOVERY ON THE WAY."
"Servia · 18-min response · AED 250".
```

#### Chauffeur
```
Scene: front passenger door of a black Mercedes S-Class held open by
a Servia chauffeur (40s, beard, teal Servia jacket, white gloves) at
the Burj Al Arab driveway / DXB Terminal 3 kerb / Address Downtown
porte-cochère. Customer (smart-casual, mid-30s) climbing in with a
laptop bag, phone in hand showing "✅ Chauffeur · 6:30 AM Friday".
Soft warm dawn light, palm trees, subtle reflections of city lights.
Headline: "TAP ONCE. CHAUFFEUR AT YOUR DOOR."
```

#### Furniture move / assembly
```
Scene: the doorway of a Marina Pinnacle apartment with two Servia
movers (teal polo, kneepads) carrying a wrapped 3-seater sofa. Yellow-
and-teal Servia 3.5-tonne moving van parked behind, ramp down.
Customer (woman, 30s, yoga pants) on the apartment side smiling with
phone displaying "✅ 2-bedroom move · AED 750 · today 11 AM". Cardboard
boxes labelled "BEDROOM 2", "KITCHEN" stacked neatly. Light grey marble
floor, sunshine through the corridor windows.
Headline: "TAP ONCE. FURNITURE MOVED."
```

#### Handyman
```
Scene: a Servia handyman (40s, beard, teal Servia polo, leather tool
belt) on a step-ladder filling a nail hole in a freshly painted off-
white wall, fresh paint roller and putty knife in hand. Living-room
context, Burj Khalifa visible through floor-to-ceiling window. Customer
in soft focus on the sofa, watching, phone face-up showing
"✅ Handyman · 1 hr · AED 100 · arriving 14:20". Servia van roof visible
in window reflection.
Headline: "TAP ONCE. WE HANDLE IT."
```

#### Plumber
```
Scene: under-sink kitchen close-up. A Servia plumber (50s, friendly
face, teal Servia polo, latex gloves) tightening a chrome pipe joint
with a wrench. Tools spread on a teal Servia floor mat protecting the
hardwood. Customer (mid-30s mum) in soft focus rinsing fruit at the
counter, smiling, phone clipped to her apron showing "✅ Plumber · AED
180 · job done". Warm afternoon UAE sunlight through the kitchen window.
Headline: "TAP ONCE. LEAK FIXED."
```

#### Electrician
```
Scene: a Servia electrician (mid-30s, teal Servia polo, hard hat,
voltage tester in hand) standing on a small ladder, cleanly installing
a brushed-nickel ceiling pendant in a Downtown Dubai apartment. Power-
off lockout tag visible on the breaker panel in background. Customer
(expat couple, mid-40s) admiring from the kitchen island, phone showing
"✅ Electrician · AED 220 · safety-certified".
Headline: "TAP ONCE. POWER ON."
```

#### AC service / clean
```
Scene: a Servia HVAC tech (mid-30s, teal Servia polo, dust mask
hanging on neck) cleaning a wall-mount split AC's evaporator coils
with a foaming cleaner spray, drip-tray protected with Servia teal
sheet on the floor below. Customer (Emirati lady in modern abaya) in
soft focus reading on the sofa, baby napping in the cool room. Phone
on the side table: "✅ AC clean · 3 units · AED 225 · 30-min service".
Headline: "TAP ONCE. COOL ALL DAY."
```

#### General cleaning / maid
```
Scene: a bright JLT apartment with a Servia maid (30s, teal Servia
polo + mustard apron, hair tied back, friendly smile) wiping the
marble kitchen counter to a polished shine, microfibre cloth in hand.
Sunlight streaming in. Hostess (working mum, 30s, in workout gear)
sips coffee at the breakfast bar, phone showing "✅ Maid · 4 hr · AED
100 · today 10 AM". Subtle Servia van outside in the parking visible
through the window.
Headline: "TAP ONCE. SPARKLE."
```

#### Pest control
```
Scene: a Servia pest-control specialist (40s, teal Servia polo,
respirator pulled down to neck, certified-technician ID lanyard)
spraying a clear, low-toxicity treatment along the kitchen baseboards.
Discreet, family-friendly mood. Customer (dad, 40s) in foreground
watches calmly, kids' toys in soft-focus background. Phone displays
"✅ Pest control · AED 200 · 30-day warranty · MOH-approved".
Headline: "TAP ONCE. PESTS GONE."
```

#### Pool service
```
Scene: drone view zooming in to a private villa pool in Arabian Ranches
at golden hour. A Servia pool tech (30s, teal Servia polo + matching
shorts, brimmed hat) using a long-handled net and chemical-test kit
poolside. Pool water crystal-clear turquoise. Owner (Emirati man in
kandura) in shaded majlis area, watch on wrist showing
"✅ Pool · AED 250 · weekly maintenance".
Headline: "TAP ONCE. POOL PERFECT."
```

### A.3 Output sizes — generate ALL of these for each service

When commissioning images for the website, generate the same scene at:
  1. **1200×1200 1:1** — square card (homepage / blog)
  2. **1080×1350 4:5** — Instagram feed
  3. **1080×1920 9:16** — story / Reel
  4. **1920×1080 16:9** — landing-page hero / YouTube
  5. **2400×1260 1.9:1** — open-graph card (link previews)
  6. **800×600 4:3** — small thumbnail / email

### A.4 Where these images get used in code

| Service | File path | Used by |
|---|---|---|
| recovery | `/web/img/recovery/burj-tap.png` | `/nfc-vehicle-recovery.html` hero, `/sos.html` thumb, homepage SOS strip |
| recovery | `/web/img/recovery/scene-mercedes.png` | recovery page strip |
| recovery | `/web/img/recovery/hero-split.png` | recovery page strip |
| recovery | `/web/img/recovery/panic-ad.png` | recovery page strip |
| recovery | `/web/img/recovery/campaign-grid.png` | recovery page footer |
| recovery | `/web/img/recovery/carousel-9.png` | recovery page section divider |
| chauffeur | `/web/img/services/chauffeur-hero.png` | future `/services/chauffeur.html` |
| furniture | `/web/img/services/move-hero.png` | future `/services/move.html` |
| handyman | `/web/img/services/handyman-hero.png` | `/services.html` cards |
| plumber | `/web/img/services/plumber-hero.png` | `/services.html` cards |
| electrician | `/web/img/services/electrician-hero.png` | `/services.html` cards |
| ac | `/web/img/services/ac-hero.png` | `/services.html` cards |
| cleaning | `/web/img/services/cleaning-hero.png` | `/services.html` cards |
| pest | `/web/img/services/pest-hero.png` | `/services.html` cards |
| pool | `/web/img/services/pool-hero.png` | `/services.html` cards |

After generating: drop the file at the path, no code changes required —
the page references the file by path and falls back gracefully if absent.

---

## B. ORIGINAL 50-VIDEO PROMPT COLLECTION

Each prompt is ready to paste into Veo 3 / Runway Gen-4 / Sora / Luma Dream Machine. Output spec: 9:16 vertical · 6–10 seconds · UAE setting · UAE actor (50% Emirati, 30% expat South-Asian, 20% expat European/Filipino) · cinematic lighting · phone always shown front-on with the green Servia confirm pill animating over it for last 1.5 s.

## Format used in every prompt

> [SCENE] · [ACTION the human takes] · [TAP MOMENT] · [PHONE-SCREEN OVERLAY: "✅ Booked. AED X. Tomorrow Y AM."] · [LAST FRAME: Servia logo + "Tap once. Booked. servia.ae/nfc"]

---

### 1. Kitchen — sauce splatter
A 30-something Emirati woman in modest home wear stirs a tagine on the cooktop. Sauce splashes onto the cabinet door. She sighs, taps her phone to a Servia sticker on the cabinet. Phone shows "✅ Maid · 4hrs · tomorrow 10AM · AED 300". She smiles, returns to cooking.

### 2. Car — rain mud
Heavy rain in Sharjah. A man in business attire steps out of a muddy white Land Cruiser at his tower lobby. He frowns at the car, taps his phone on a Servia sticker on the dashboard through the open window. Phone shows "✅ Mobile car wash · same day 3PM · AED 65". He walks into the lobby relaxed.

### 3. AC — first hot day
A young Filipino mother holds her baby in front of a wall AC unit blowing weakly. Sweat on her brow. She pulls her phone from her pocket, taps a Servia tag on the AC's right corner. Phone shows "✅ AC service · today 2PM · AED 75/unit". She fans the baby with relief.

### 4. Pool — green water
Drone shot of a private villa pool turning slightly green. The owner, an Emirati man in white kandura by the pool tile, taps his phone to a Servia tag stuck on the equipment-pad cover. Phone: "✅ Pool clean + chemical balance · tomorrow 9AM · AED 250".

### 5. Sofa — child grape juice
Living room. A toddler spills purple grape juice on a cream sofa. Mom (South-Asian, 30s) gasps then laughs, lifts the cushion to reveal a Servia sticker on the underside. Tap. Phone: "✅ Sofa shampoo · this Friday 11AM · AED 180".

### 6. Garden — overgrown
A villa in Jumeirah. Father in polo shirt walks the garden with morning coffee, sees overgrown hedges. He taps his phone on a Servia tag at the garden gate post. Phone: "✅ Gardener · Saturday 7AM · AED 120".

### 7. Pest — cockroach reveal
Late night kitchen, dim warm light. A roach scurries across the counter. The owner (Emirati man) calmly opens the pantry, taps a Servia tag inside. Phone: "✅ Pest control · tomorrow 9AM · AED 200 · 30-day warranty".

### 8. Office — Monday morning
Open-plan office in Dubai's DIFC, pre-9AM. The manager arrives, sees coffee rings on every desk. Walks to her desk, taps phone to a Servia tag stuck under the desk lip. Phone: "✅ Office cleaning · tonight 8PM · AED 150".

### 9. Move-out — last week
Empty boxes in a 2BR apartment. A young couple high-fives. He walks to the front door where a Servia move-out tag is stuck on the inside. Tap. Phone: "✅ Move-out clean + photos for landlord · Sunday 8AM · AED 550".

### 10. Babysitter — date night
Couple dressed for dinner standing in the foyer. Wife realises babysitter cancelled. Husband taps Servia tag on the nursery door frame. Phone: "✅ DHA-trained nanny · tonight 7PM-11PM · AED 280". Both relax.

### 11. Vehicle recovery — desert breakdown
Wide shot of a Toyota Yaris stopped on Hatta Road, hazards on. Driver steps out, taps the Servia tag on the dashboard. Phone shows GPS pin with "✅ Roadside recovery dispatched · ETA 18 min · AED 250 · live tracking on WhatsApp".

### 12. Window — sandstorm aftermath
Apartment balcony covered in fine yellow dust. Resident slides door open, taps a Servia tag on the window frame. Phone: "✅ Window cleaning + frames · tomorrow 4PM · AED 150".

### 13. Painting — toddler scribbles
A toddler proudly stands beside a long crayon line on the white wall. Mom fights a smile, taps a Servia tag on the back of the bedroom door. Phone: "✅ Wall touch-up paint · Sunday 9AM · AED 350".

### 14. Laundry — overflowing basket
Dad walks into laundry room. Mountain of clothes. Taps a Servia tag on the side of the washing machine. Phone: "✅ Laundry pickup · today 6PM · 24h turnaround · AED 60".

### 15. Handyman — leaking faucet
Bathroom. Single drip from the basin tap leaving a brown streak. Roommate enters, taps a Servia tag on the back of the bathroom door. Phone: "✅ Handyman · tomorrow 11AM · AED 100 visit fee".

### 16. Car wash 2 — grocery run
Mom unloads groceries in a tower car park, sees crusted bird droppings on the car roof. Taps Servia tag on the dashboard. Phone: "✅ Car wash at parking · tomorrow 10AM · AED 50".

### 17. Pool 2 — birthday party tomorrow
Gilded balloons being inflated by the pool. Host realises pool needs a quick clean. Taps a Servia tag on the wall by the pool gate. Phone: "✅ Express pool service · tomorrow 7AM · AED 250".

### 18. Sofa 2 — pet hair build-up
Golden retriever shedding on a velvet sofa. Owner laughs, taps a Servia tag on the side of the coffee table. Phone: "✅ Sofa & rug deep clean · Saturday 2PM · AED 220".

### 19. Garden 2 — Eid prep
Family preparing for Eid. Garden looks tired. Grandmother taps the Servia tag on the garden gate. Phone: "✅ Pre-Eid garden makeover · Thursday 6AM · AED 180".

### 20. Pest 2 — bedbug bite
Person scratches a red welt on their arm in bed. Sits up, taps the Servia tag on the bedside lamp. Phone: "✅ Bedbug specialist · tomorrow 8AM · AED 450 · 30-day warranty".

### 21. Office 2 — investor visit
CEO at his standing desk gets a calendar ping "Investors at 3PM". Taps Servia tag on the back of his monitor. Phone: "✅ Express office clean · today 1PM · AED 180".

### 22. Move-in — keys-day
Young woman walks into an empty studio apartment, drops her suitcase. Walks to the front door, taps the previous tenant's Servia tag (which she'll repurpose). Phone: "✅ Move-in deep clean · today 6PM · AED 400".

### 23. Babysitter 2 — last-minute meeting
Mom pacing during a Zoom call as toddler whines. She taps the Servia tag on the kitchen wall. Phone: "✅ Nanny · today 1PM-6PM · AED 175".

### 24. Recovery 2 — flat tyre on E11
Car parked on the shoulder of Sheikh Zayed Road, hazards. Driver taps phone to dashboard tag. Phone: "✅ Tyre + tow service · ETA 22 min · AED 280 · live ETA on WhatsApp".

### 25. Window 2 — ocean spray (JBR)
JBR apartment with sea-spray-streaked windows. Resident steps onto balcony, taps Servia tag on glass frame. Phone: "✅ Salt-spray window service · tomorrow 5PM · AED 130".

### 26. Painting 2 — buying a new rental
Landlord with key chain unlocking a flat. Walls scuffed. Taps Servia tag on door jamb. Phone: "✅ Full repaint 1BR · 4 days · AED 1100 · matching Jotun".

### 27. Laundry 2 — business trip
Suit jacket hanging in cupboard with coffee stain on lapel. Owner taps Servia tag inside the cupboard door. Phone: "✅ Dry-clean rush · pickup today 7PM · ready Saturday · AED 60".

### 28. Handyman 2 — IKEA assembly
Half-built BILLY bookshelf, scattered Allen keys. Husband sighs, taps Servia tag on the toolbox lid. Phone: "✅ IKEA assembly handyman · today 4PM · AED 100 + 80/hr".

### 29. Garden 3 — date palm trim
Villa with a tall date palm casting shadows on solar panels. Owner taps Servia tag on the garden water-tap pillar. Phone: "✅ Date palm trim + climber · Saturday 6AM · AED 220".

### 30. Pest 3 — pantry moths
Grandfather opens the rice container, sees moths fly out. Taps Servia tag on inside of pantry door. Phone: "✅ Pantry pest treatment · tomorrow 9AM · AED 200".

### 31. Maid 2 — week from hell
Open-plan flat, dishes piled, laundry on the sofa, toys scattered. Single mom collapses, taps Servia tag on the coat rack. Phone: "✅ Full reset · maid 3hrs · today 6PM · AED 90 (subsidised)".

### 32. AC 2 — burning smell
Office AC making a clicking sound + faint burning smell. Receptionist taps Servia tag on the AC vent grille. Phone: "✅ Emergency AC · within 90 min · AED 150 callout".

### 33. Car wash 3 — premium detail
Car owner standing back from his black BMW, comparing it to a friend's gleaming one. Taps Servia tag on dashboard. Phone: "✅ Full premium detail · 4hrs · AED 250 · ceramic optional".

### 34. Pool 3 — family weekend
Children eager to swim. Dad checks pool: cloudy. Taps Servia tag on a poolside tile. Phone: "✅ Same-day pool clean · today 4PM · AED 250".

### 35. Sofa 3 — couples vlog
Couple recording a sofa unboxing for Instagram, then realise the existing sofa looks dirty in comparison. Wife taps Servia tag on the side of the new sofa. Phone: "✅ Pre-shoot sofa clean · today 2PM · AED 180".

### 36. Window 3 — kid handprints
Floor-to-ceiling glass with toddler handprints all over. Mom taps Servia tag on the window-frame edge. Phone: "✅ Window cleaning · this Friday · AED 80".

### 37. Painting 3 — colour change
Empty bedroom. Roller in hand, woman about to paint. Stops. Taps Servia tag on the inside of the bedroom door. Phone: "✅ Pro repaint · day-after-tomorrow · AED 800 · 2-coat".

### 38. Laundry 3 — silk dress
Bride-to-be holds up an off-white silk dress with a tea stain. Taps Servia tag on her wardrobe door. Phone: "✅ Specialty silk dry-clean · 48h · AED 95".

### 39. Babysitter 3 — date anniversary
Husband ties his tie. Wife behind him on phone — taps the Servia nursery tag. Phone: "✅ Nanny · tonight 7PM · AED 280".

### 40. Recovery 3 — battery dead in mall parking
Driver in 5th-floor mall car park presses ignition — nothing. Taps Servia tag on dashboard. Phone: "✅ Jump-start service · ETA 15 min · AED 150".

### 41. Office 3 — startup pivot
WeWork-style space. Founder paces, taps Servia tag on his Mac. Phone: "✅ Office deep clean · tomorrow 7AM · AED 150".

### 42. Move-out 2 — rental return
Maid hands keys to the owner who taps the Servia tag in the entryway one last time. Phone: "✅ Final clean + photos · this Sunday · AED 500".

### 43. Garden 4 — automatic irrigation broken
Spotty patches in lawn. Father kneels, taps Servia tag on irrigation manifold. Phone: "✅ Irrigation diagnostic + fix · tomorrow · AED 150 callout".

### 44. Pest 4 — termite trail
Emirati grandfather points to small mud trail on baseboard. Taps Servia tag on the closest cabinet. Phone: "✅ Termite specialist · tomorrow 9AM · AED 350".

### 45. Maid 3 — cleaner away on holiday
Standing maid uniform on coat rack with a "back in 2 weeks" note. Owner taps Servia tag on the kitchen wall. Phone: "✅ Backup maid 4hrs · daily this fortnight · AED 100/visit".

### 46. AC 3 — duct cleaning villa
Villa hallway with ceiling vents. Owner taps Servia tag at the thermostat. Phone: "✅ Whole-villa duct clean · 1-day job · AED 1100".

### 47. Car wash 4 — wedding-day detail
Bride and groom emerge in white. Driver waiting by the car taps Servia tag on dashboard. Phone: "✅ Pre-wedding detail · this Thursday 6AM · AED 250".

### 48. Pool 4 — safety check before kids' party
Mom inspects pool ahead of party. Taps Servia tag on equipment pad. Phone: "✅ Pool safety inspection · today 3PM · AED 250".

### 49. Sofa 4 — Eid prep
Family preparing majlis for Eid guests. Father taps Servia tag on majlis side-table leg. Phone: "✅ Majlis sofa + carpet steam · tomorrow 7AM · AED 350".

### 50. Window 4 — high-rise inside
Apartment owner watching a window cleaner outside on a rope. Says "I forgot to book the inside!". Walks to window, taps Servia tag on inside of frame. Phone: "✅ Inside window service · adds to outside slot · AED 80".

---

## Storyboard pattern

Each clip:
- 0.0–1.5s: scene setup (the trigger moment — mess, breakdown, sudden need)
- 1.5–3.5s: actor pulls phone, walks/turns toward the tag
- 3.5–4.5s: TAP — close-up of phone meeting tag, tiny haptic-flash
- 4.5–6.5s: phone-screen close-up showing the green confirm pill (animated): "✅ <service> · <when> · AED <amount>"
- 6.5–8.0s: actor's relieved smile / thumbs-up / returns-to-life
- 8.0–10.0s: end card "Servia · Tap once. Booked. · servia.ae/nfc"

## Voice-over (optional, EN/AR rotating)

- EN: "When life gets messy, just tap." / "Servia. Tap once. Booked."
- AR: "حياتك مزدحمة. فقط المسة. سيرفيا، اطلب بضغطة." / "بإيماءة من هاتفك… مرتبة."
- HI: "तपकाओ। बुक हो गया।"
- TL: "I-tap mo lang. Tapos na."

## Hashtag set (UAE-focused)

`#Servia #ServiaTap #UAEHomeServices #Dubai #MyDubai #DubaiLife #SharjahMoments #AbuDhabiLife #ServiaAE #TapToBook #NFCMagic #UAEMoms #DubaiHome #ServiceMadeSimple`

## Music direction

Use UAE-Arabic-modern-pop royalty-free beds (find on Epidemic Sound or Artlist):
- Driving / busy moments: drums-led 110bpm, oud accent
- Calm/relief moments: warm 80bpm with light hand-percussion
- Hero clips (1, 11, 24, 31, 49): swelling cinematic with strings final 2 seconds

## Captions (burned in)

Always burn into video, 80% width, top-third, with a 4px solid teal stroke + drop-shadow. Fonts: Inter SemiBold (English) + Tajawal SemiBold (Arabic).

## Posting schedule (output of all 50)

- 5 clips/week × 10 weeks
- Mondays: kitchen/sofa moms (#1, #5, #18, #31, #45)
- Tuesdays: car/recovery (#2, #11, #24, #40, #47)
- Wednesdays: AC/pool (#3, #4, #17, #32, #46)
- Thursdays: pest/garden (#6, #19, #29, #44, #43)
- Fridays / weekends: family / events (#10, #16, #34, #39, #49)
- Repeat 6 weeks later with localised AR voice-over swap.
