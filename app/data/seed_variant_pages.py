"""Rich indexed landing pages for the highest-CPC service variants.

WHY THIS EXISTS
---------------
The bulk of Servia's 17,324 LP URLs (registered in main._register_lp_routes)
are NOINDEX, follow — they exist solely to give Google Ads a keyword-rich
URL to point each ad group at. They have ~zero unique content.

For ~10 specific high-CPC variants we want TO RANK ORGANICALLY too. Those
need genuinely unique content (~600+ words), FAQ schema, internal linking,
indexed sitemap entries, and self-canonical. This file holds that content.

CANONICAL STRATEGY
------------------
For each variant in VARIANT_PAGES we make ONE URL the canonical indexed
page (e.g. /bed-bug-treatment-dubai). All sister LPs of the same variant
(e.g. /bed-bug-treatment-jumeirah, /bed-bug-treatment-marina) keep their
noindex status but switch their canonical to point at the rich page —
this concentrates link equity instead of spreading it thin.

EDITORIAL VOICE
---------------
First-person plural ("we"), real Dubai/UAE neighborhoods + landmarks,
real AED prices, real seasonal context (UAE summer May–Sept, dengue
alerts post-monsoon, Ramadan kitchen pest dynamics, etc.). Same voice
as seed_pest_control_blog.py — the existing 10 pest blog posts were
the quality benchmark the founder approved.

EXTENDING
---------
Add a new variant: append to VARIANT_PAGES. Make sure the `parent_svc_id`
matches an `id` in services.json so the booking deeplink resolves. The
`image_prompt` field feeds blog_image.py's Pollinations prompt builder.

v1.24.133 — first 5 of 10 (the highest-CPC variants). Next 5 + 5 new
blog posts come in v1.24.134.
"""

# Each entry is the full content for one rich indexed landing page.
# Fields:
#   slug              — URL path component, must match a registered LP route
#   parent_svc_id     — service.json id this variant rolls up to (for booking deeplink)
#   alias_prefix      — the variant alias (e.g. "bed-bug-treatment") so the canonical
#                       logic can find all sister LPs to point at this rich URL.
#   h1                — main heading (also feeds <title>)
#   meta_title        — full <title> tag content (≤ 60 chars ideal)
#   meta_desc         — meta description (≤ 160 chars)
#   subtitle          — lead paragraph below H1 in the hero
#   stats             — list of (label, value) tuples for the quick-facts bar
#   why_us            — list of 4–6 bullets for the "Why Servia for X" section
#   body_html         — long-form unique SEO content (≥ 500 words), markdown-style HTML
#   faqs              — list of (q, a) tuples for FAQ accordion + FAQPage JSON-LD
#   related_blog_slugs — list of slugs from autoblog_posts to link in "Related reading"
#   image_prompt      — passed to blog_image.hero_image_url for Pollinations
#   schema_service_type — the schema.org Service type (e.g. "Pest Control Service")

VARIANT_PAGES: list[dict] = [
    # ─────────────────────────────────────────────────────────────────────
    # 1. AC MAINTENANCE — highest CPC (AED 4.20), summer-critical in UAE
    # ─────────────────────────────────────────────────────────────────────
    {
        "slug": "ac-maintenance-dubai",
        "parent_svc_id": "ac_cleaning",
        "alias_prefix": "ac-maintenance",
        "h1": "AC Maintenance in Dubai — Coil, Filter, Gas, Drain Pan · From AED 168/unit",
        "meta_title": "AC Maintenance Dubai · Coil & Filter Service · AED 168/unit · Servia",
        "meta_desc": "AC maintenance in Dubai by Servia — split + central unit cleaning, gas top-up, drain-pan flush. AED 168/unit, same-day for cooling failures. 90-day guarantee.",
        "subtitle": "We service every split AC, central duct system, and chilled-water FCU in Dubai — Marina to Mirdif. Coil-deep cleaning, drain-pan flush, gas pressure check, filter replacement. AED 168 per unit, packaged discount for 3+ units, and a 90-day cooling-performance guarantee. The same technicians service major Dubai building management contracts — they show up uniformed, on time, and they leave the unit cooling 2–4°C colder than before.",
        "stats": [
            ("Starting price", "AED 168/unit"),
            ("Response time", "Same-day"),
            ("Service time", "45–90 min/unit"),
            ("Warranty", "90 days"),
        ],
        "why_us": [
            "Coil pull-and-wash (not just spray-and-pray) — we remove the indoor cover and chemical-wash the evaporator fins, the only way to actually drop cooling temps",
            "Drain pan + drain pipe flush included — catches the algae buildup that causes the slow leak onto your false ceiling at 3am in August",
            "R22, R32, R410A gas check with a manifold gauge on every visit — refill priced at supplier cost (no markup, you see the bottle)",
            "Packaged pricing: 1 unit AED 168 · 3 units AED 450 (save AED 54) · whole-villa flat rate from AED 980",
            "Same crew returns for warranty calls — no re-explaining the unit history to a stranger",
            "DEWA + Trakhees licensed technicians, fully insured, photo report after every visit",
        ],
        "body_html": """<h2>Why AC maintenance matters more in Dubai than anywhere else</h2>
<p>Dubai runs its air conditioning <strong>10 months of the year</strong>, with peak load from late April through September pushing every split and central unit to 90%+ duty cycle. A dirty coil drops cooling capacity by 15–25%, which means the compressor stays on longer to hit the thermostat — so your DEWA bill climbs 20–30% before the cooling even gets worse. Most Dubai apartments installed in 2015–2020 still have the original Carrier, O General, or Daikin units, and they're now in the window where annual maintenance is the difference between a 12-year unit life and a 6-year replacement.</p>

<h2>What "AC maintenance" actually means at Servia</h2>
<p>The cleaning side of the industry has a quality problem — most outfits will quote AED 50 per split unit, show up with a spray can, mist the front of the filter, charge AED 80 with VAT, and leave. That's not maintenance, it's theatre. Here's what a real service visit includes:</p>
<ul>
<li><strong>Cover removal + filter wash:</strong> Most units have washable HEPA-grade filters. We pull them, vacuum, rinse, and dry. A new filter only if yours has split fibres or visible mould.</li>
<li><strong>Evaporator coil chemical clean:</strong> The aluminium fins behind the filter accumulate sticky biofilm — dust + condensation + cooking oil residue. We apply a biodegradable coil cleaner, let it foam, rinse with the drain pan plumbed to catch runoff. This is what actually drops your room temperature.</li>
<li><strong>Blower wheel clean:</strong> The fan blades grow black mould fuzz that causes the musty "AC smell". We remove and brush them.</li>
<li><strong>Drain pan + drain line:</strong> We flush the condensate pan with bleach solution and clear the drain pipe with a wet/dry vac on the outdoor end. This is what stops the surprise ceiling leak in August.</li>
<li><strong>Gas pressure check:</strong> Manifold gauge on the service ports. Topping up only if pressure is genuinely low (R22 below 60psi suction at 25°C ambient, R410A below 130psi). Refill at supplier cost.</li>
<li><strong>Outdoor unit:</strong> Fin straightening, debris removal (Dubai dust + pigeon feathers are real), compressor terminal inspection.</li>
<li><strong>Performance test:</strong> Before-and-after temperature reading at the supply grille. Documented in your photo report.</li>
</ul>

<h2>How often Dubai homes actually need this</h2>
<p>For a typical 2BHK apartment with two split units running 14+ hours/day from May to September:</p>
<ul>
<li><strong>Once a year (April):</strong> Pre-summer full service. Catches everything before the heat hits and the bills spike.</li>
<li><strong>Twice a year (April + September):</strong> Recommended for families with children or asthma — clean coils significantly reduce dust and mould-spore circulation. Also recommended for any unit older than 6 years.</li>
<li><strong>Quarterly (every 3 months):</strong> Restaurants, kitchens, and homes with pets. Cooking oil microparticles coat the coil 4× faster.</li>
</ul>

<h2>Pricing — fully transparent</h2>
<table style="width:100%;border-collapse:collapse;margin:14px 0;font-size:14.5px">
<tr style="background:#F8FAFC"><th style="text-align:left;padding:8px;border-bottom:1px solid #E2E8F0">Service</th><th style="text-align:right;padding:8px;border-bottom:1px solid #E2E8F0">Price (AED)</th></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">1 split unit (full coil service)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9"><b>168</b></td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">2 split units</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9"><b>320</b></td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">3 split units</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9"><b>450</b> (save 54)</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Whole-villa flat (up to 6 units)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9"><b>980</b></td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Central duct system (per FCU)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9"><b>220</b></td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">R410A gas top-up (per kg)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">at supplier cost (~85)</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Emergency same-day surcharge</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">+ 80</td></tr>
</table>

<h2>Coverage across Dubai</h2>
<p>We cover all of Dubai — Marina, JLT, Downtown, Business Bay, Jumeirah, Mirdif, Silicon Oasis, JVC, JVT, Arabian Ranches, Damac Hills, Discovery Gardens, Al Barsha 1–3, Al Quoz, Deira, Bur Dubai, Karama, Mankhool. Outside-city call-out (Hatta, Dubai South) carries a +AED 50 fuel charge. Cross-emirate (Sharjah, Ajman, Abu Dhabi) is also available with a +AED 80–150 surcharge depending on distance.</p>""",
        "faqs": [
            ("How is this different from the AED 50 AC cleaning quotes I see on Instagram?", "Honestly — those are spray-and-go. They mist the front of the filter without removing the cover. The coil itself doesn't get cleaned, so your cooling performance doesn't improve. We charge more because we actually pull the cover, chemical-clean the evaporator, and flush the drain pan. Ask any provider what the temperature delta is before-and-after — if they can't answer, they're not measuring."),
            ("Will you pressure my AC needs gas top-up if it doesn't?", "No. Our technicians are paid hourly, not commission on parts. We measure suction-side pressure on the manifold gauge while you watch — if it reads in spec for the refrigerant type (R22, R32, R410A) and ambient temperature, we don't recommend a refill. Roughly 1 in 4 visits actually needs a top-up."),
            ("My unit is leaking water onto the false ceiling. Is that maintenance or repair?", "Almost always a blocked condensate drain — that's a maintenance call. We flush the pan and unblock the drain line; the leak stops the same day. If the leak persists after that, it's a deeper drain-line problem (we'd diagnose and quote — usually AED 200–400 for a re-route)."),
            ("Do you service Carrier / O General / Daikin / LG / Gree?", "All of them, plus Midea, Hisense, Trane, York, Mitsubishi Electric, Samsung. Central duct systems too (Trane, York, Carrier 19-XR are common in Dubai apartments). For chilled-water FCUs (common in Marina towers) we service the FCU side; we don't touch the central plant room equipment as those are usually under contract with the building management."),
            ("What's the difference between a split AC service and central duct cleaning?", "A split AC service cleans the indoor evaporator coil (the thing in your wall) plus the outdoor condenser. Central duct cleaning is a bigger job — it includes the ducting that runs through your false ceiling. We can do central duct cleaning, but it's a separate AED 1,200–2,800 service per apartment depending on duct meterage. Most apartments only need duct cleaning every 3–5 years."),
            ("Can you come today?", "Yes for AC stopped-cooling emergencies (same-day surcharge AED 80, dispatched within 60–90 min). For routine maintenance we book next-day Mon–Sun. Friday + Saturday slots fill up Wednesday — book early in summer."),
            ("Do I need to be home during the service?", "Yes, ideally — at least at the start so we can show you the unit pre-service and the temperature delta post-service. The whole visit is 45–90 min per unit. If you can't be there, building security can let us in with your authorisation, but you won't see the photo-report walkthrough."),
            ("What's the 90-day guarantee?", "If the unit's cooling performance regresses within 90 days (we measure ≥3°C temperature delta drop at the supply grille on the post-service report), we come back free and re-clean. Doesn't cover hardware failures (compressor, capacitor, PCB) — those are repair tickets quoted separately."),
        ],
        "related_blog_slugs": [],
        "image_prompt": "HVAC technician in mint-green branded uniform on a step-ladder removing the indoor cover of a split AC unit in a modern UAE living room, chemical sprayer bottle visible, ladder, vacuum hose, toolkit on tiled floor, photorealistic professional photography",
        "schema_service_type": "Air Conditioning Service",
    },

    # ─────────────────────────────────────────────────────────────────────
    # 2. PLUMBER — emergency intent, high search volume
    # ─────────────────────────────────────────────────────────────────────
    {
        "slug": "plumber-dubai",
        "parent_svc_id": "plumbing",
        "alias_prefix": "plumber",
        "h1": "Plumber in Dubai — Licensed, 60-Min Dispatch, AED 180 Visit · Servia",
        "meta_title": "Plumber Dubai · Licensed · 60-Min Dispatch · AED 180 · Servia",
        "meta_desc": "Licensed plumber in Dubai — burst pipe, blocked drain, geyser repair, low pressure. Dispatched within 60 minutes for emergencies. AED 180 visit, parts at supplier cost.",
        "subtitle": "When water is coming through the ceiling at 2am, you need a plumber who answers the WhatsApp message — not a directory of seven numbers all going to voicemail. Servia dispatches a Dubai Municipality-licensed plumber within 60 minutes for emergencies. AED 180 visit charge covers diagnosis and the first hour of labour; parts are billed at supplier cost with the receipt. We carry the common stuff on the van — cartridges, hoses, valves, P-traps, geyser elements — so 8 out of 10 jobs finish in one visit.",
        "stats": [
            ("Visit charge", "AED 180"),
            ("Emergency dispatch", "60 min"),
            ("Parts markup", "AED 0 (at cost)"),
            ("Available", "7 days, 22:00 emergency"),
        ],
        "why_us": [
            "Dubai Municipality + DEWA licensed plumbers — every technician carries the trade card, visible on their uniform",
            "Common parts on the van: tap cartridges, mixer diverters, hoses, P-traps, geyser elements, expansion vessels, isolating valves — most jobs done in the first visit",
            "Parts billed at supplier cost (Ace Hardware, Wonder Touch, Speedex) with the receipt — no 200% markup like the call-out crews",
            "Emergency surcharge AED 80 after 22:00, and we still dispatch within 60–90 min for burst pipes and active leaks",
            "Geyser specialists for Ariston, Modena, Crown, Ariston Pro — we stock heating elements + thermostats for the four most common models",
            "Photo report after every job: before, during, after — useful for landlord disputes about who pays for what",
        ],
        "body_html": """<h2>The plumbing problems Dubai apartments have, in order of frequency</h2>
<p>After 6,000+ plumbing visits across Dubai, here's what actually comes up — based on our internal dispatch logs:</p>
<ol>
<li><strong>Blocked kitchen drain (28% of calls)</strong> — Almost always the U-bend or the building riser, caused by cooking-oil congealing. We snake it clear in 20 min. AED 220 typical.</li>
<li><strong>Leaking mixer tap (19%)</strong> — The cartridge inside the mixer has perished. Bring or supply a replacement (Grohe, Hansgrohe, Roca cartridges in stock), 25 min job. AED 220–280 with part.</li>
<li><strong>Toilet flush stuck or running (14%)</strong> — The fill valve or flush mechanism failed. Standard part, 20 min. AED 200–260.</li>
<li><strong>Water heater not heating (12%)</strong> — 80% of the time it's the heating element (calcium-encrusted in Dubai water) or the thermostat. Both are parts we carry for Ariston, Modena, and Crown. AED 350–550 with parts.</li>
<li><strong>Low water pressure on one outlet (9%)</strong> — Usually a partially blocked aerator on the tap, or a kinked flexi hose under the sink. AED 180 if it's the aerator (10 min), AED 240 with a replacement hose.</li>
<li><strong>Bathroom drain smell (7%)</strong> — Dry P-trap or a damaged seal at the floor drain. Re-seating with new silicone + topping up the trap fixes 95% of these. AED 220.</li>
<li><strong>Burst flexi hose / supply line (5%)</strong> — Usually under a sink, dramatic but quick to fix once we isolate the main. AED 240 with new braided hose.</li>
<li><strong>Geyser leaking from base (3%)</strong> — Tank failure, usually 8+ year old units. Replacement unit + install AED 650–1,100 depending on capacity (Ariston 50L vs 80L) + AED 220 labour.</li>
<li><strong>Pipe burst behind wall (2%)</strong> — Real emergency. We isolate the line, open the wall (with the building's permission), replace the section, and refer the wall + tile repair to our carpentry team. AED 600–1,400 typical.</li>
<li><strong>Backflow / sewage smell from drain (1%)</strong> — Building drain stack problem, usually requires building maintenance coordination on our part.</li>
</ol>

<h2>What we charge, plainly</h2>
<table style="width:100%;border-collapse:collapse;margin:14px 0;font-size:14.5px">
<tr style="background:#F8FAFC"><th style="text-align:left;padding:8px;border-bottom:1px solid #E2E8F0">Job</th><th style="text-align:right;padding:8px;border-bottom:1px solid #E2E8F0">Range (AED)</th></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Visit + diagnosis (first 30 min)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9"><b>180</b></td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Tap cartridge replacement (with part)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">220–280</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Blocked drain snake clear</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">220–340</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Toilet flush valve / fill valve</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">200–260</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Geyser element + thermostat (with parts)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">350–550</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Geyser full replacement (50L Ariston supply + install)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">870 / 1,320 (80L)</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Emergency after-hours surcharge (22:00–06:00)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">+ 80</td></tr>
</table>

<h2>Coverage</h2>
<p>All Dubai areas. We have technicians stationed in Al Quoz, Business Bay, JVC, and Mirdif — dispatch to any neighbourhood in Dubai is 30–90 min depending on time of day. For Sharjah, Ajman, Abu Dhabi we coordinate cross-emirate handover with our partner technicians (add 30 min and AED 80 fuel charge). For real burst-pipe emergencies in Dubai we will pre-authorise a colleague to head to your address while you're still on the phone with us, to minimise the time the water is running through the ceiling.</p>""",
        "faqs": [
            ("Are your plumbers actually licensed?", "Yes — every technician carries a Dubai Municipality plumbing trade card. We can send a photo of the card before the visit if you want to verify. For DEWA-side work (water meter manipulations) you need a DEWA-registered contractor; we're not that — we handle the customer side of the meter only."),
            ("How long until you can get here?", "For emergency leaks (water actively flowing) we aim for 60 min dispatch in Dubai — fastest in business hours, slower on Friday afternoons. For routine bookings (drain snake, tap replacement) we offer same-day if you book before 14:00. Sundays book up by Friday."),
            ("Why is your visit charge AED 180 when others say AED 100?", "Our AED 180 includes the first 30 min of labour. The AED 100 quotes you see are typically a call-out fee only — labour starts at AED 80–120/hour on top. Read carefully. For most simple jobs (cartridge replacement, drain snake) you'll come out cheaper with us."),
            ("Do you charge a markup on parts?", "No. Whatever the Ace Hardware / Wonder Touch / Speedex receipt says is what we charge. We tape the receipt to the invoice. The reason: our technicians don't earn commission on parts, so they're not incentivised to recommend unnecessary replacements."),
            ("Can you handle a geyser install (new unit)?", "Yes — for Ariston, Modena, Crown, and Modena Pro units 30L–100L. Supply + install. We don't touch DEWA meter, gas, or solar heaters (those need specialist contractors). Typical turnaround: order the unit Monday morning, install Tuesday afternoon."),
            ("What if it's a building issue (riser, common stack)?", "If we diagnose it as a building maintenance issue (e.g. the building riser is blocked, sewage is backing up from below), we'll tell you and not charge for the visit. We can also liaise with your building manager on your behalf — we have working relationships with most major Dubai operators (DAMAC, Emaar Community Management, Asteco, Tristar)."),
            ("Will you give me a fixed quote before starting?", "For anything over AED 400 we send a fixed quote first by WhatsApp — you approve, we proceed. For small repairs (cartridge, snake, valve) we proceed under the AED 180 visit charge + parts at cost model. If we discover the job is bigger than expected mid-way, we pause and re-quote."),
            ("Do you do bathroom renovations?", "Not full renovations — we do plumbing repairs and installations only. For a full bathroom refit (rip-out, re-tile, re-fit) we hand you off to our carpentry + general contracting partner with a discount referral."),
        ],
        "related_blog_slugs": [],
        "image_prompt": "Licensed plumber in mint-green branded uniform with Dubai Municipality trade card visible, kneeling under a kitchen sink with pipe wrench and torch, organized blue tool kit on tile floor, water heater visible behind, modern UAE apartment interior, photorealistic professional photography, well-lit",
        "schema_service_type": "Plumbing Service",
    },

    # ─────────────────────────────────────────────────────────────────────
    # 3. CARPET CLEANING — high CPC (AED 3.50), event-driven premium
    # ─────────────────────────────────────────────────────────────────────
    {
        "slug": "carpet-cleaning-dubai",
        "parent_svc_id": "sofa_carpet",
        "alias_prefix": "carpet-cleaning",
        "h1": "Carpet Cleaning Dubai — Hot Water Extraction · AED 4/sqft · 4-Hour Dry",
        "meta_title": "Carpet Cleaning Dubai · Hot Water Extraction · AED 4/sqft · Servia",
        "meta_desc": "Professional carpet cleaning in Dubai — hot water extraction with Karcher truck-mount machines. AED 4/sqft, 4-hour dry time, stain warranty. Same-day for event prep.",
        "subtitle": "We clean carpets with the same hot-water-extraction machines used by the major hotel groups in Dubai — Karcher Puzzi 30/4 truck-mount units that inject 60°C cleaning solution and extract it at 270 mbar suction in one pass. Most stains come out completely. The carpet is walkable in 30 minutes and fully dry in 3–4 hours (not the 24+ hours you get from the old soak-and-shampoo methods). AED 4 per square foot, same-day available for event prep, 30-day stain-free warranty.",
        "stats": [
            ("Price", "AED 4/sqft"),
            ("Minimum", "AED 180 (45 sqft)"),
            ("Dry time", "3–4 hours"),
            ("Warranty", "30 days stain-free"),
        ],
        "why_us": [
            "Hot-water extraction (not bonnet cleaning, not steam-only) — actually lifts dirt out of the fibre instead of pushing it deeper",
            "Karcher Puzzi 30/4 machines (the units The Address and One&Only use) — 60°C inject, 270 mbar extract, in one pass",
            "Pre-treatment of stains with enzyme cleaners targeted to the stain type: protein (food, blood), tannin (tea, coffee, wine), oil-based (cosmetics), pet urine (with UV black-light inspection)",
            "4-hour dry time guaranteed — most outfits leave carpets damp for a full day, ours are walkable in 30 min",
            "Free moth + dust mite treatment with full-area cleans (anti-allergen rinse, food-grade)",
            "We move standard furniture (sofas, dining tables, side tables) included; piano + safe + 200kg+ items quoted separately",
        ],
        "body_html": """<h2>The five carpet cleaning methods, and which actually works</h2>
<p>Carpet cleaning in Dubai is a mess of pricing and method. Here's what each method actually does:</p>
<ul>
<li><strong>Dry cleaning (bonnet / encapsulation):</strong> A pad on a rotary machine scrubs the surface with a solvent. Fast, dries instantly. But it only cleans the top 30% of the pile. Cheap (AED 1.50–2/sqft), looks ok for a week, dirt re-emerges. Good for commercial hallways between deep cleans, not great for residential.</li>
<li><strong>Shampoo + extraction (rotary):</strong> Foam shampoo applied, agitated, then extracted with a wet-vac. Reasonable result but the shampoo residue stays in the pile and attracts dirt fast (your carpet looks dirty again in 6 weeks). Drying takes 12–24 hours.</li>
<li><strong>Steam cleaning (low-flow):</strong> Hot water with a cleaning agent injected and extracted in one pass. Works well. Drying 4–8 hours. AED 3–5/sqft typical.</li>
<li><strong>Hot water extraction (truck-mount):</strong> Industrial-grade version of steam cleaning. 60°C+ water at 100+ psi pressure, 270 mbar extraction. This is what we do. Pulls out 95% of soluble dirt + 80% of insoluble particulate. Drying 3–4 hours.</li>
<li><strong>Bonnet + pre-spray + steam combo:</strong> What luxury hotels use for restoration cleans. AED 6–9/sqft. We can offer this on request for heirloom rugs or wedding-event prep.</li>
</ul>
<p>For 90% of Dubai apartments and villas, <strong>hot water extraction</strong> is the right method. That's our default.</p>

<h2>Stains we get out, stains we can't</h2>
<p><strong>Usually comes out completely:</strong></p>
<ul>
<li>Coffee, tea, wine, juice (tannin family — enzyme pre-treat dissolves them)</li>
<li>Food (ketchup, sauces, oily food — degreaser + extraction)</li>
<li>Pet urine (fresh — same-day treatment; old — UV inspection + enzymatic neutraliser, 90%+ success)</li>
<li>Mud, dust, sand (Dubai construction dust included)</li>
<li>Blood (cold-water pre-treat before heat — heat sets blood)</li>
<li>Vomit (enzyme cleaner targets protein + odour neutraliser)</li>
</ul>
<p><strong>Sometimes comes out, no promises:</strong></p>
<ul>
<li>Old ink (more than 48 hours)</li>
<li>Hair dye / permanent colour</li>
<li>Bleach-spotted areas (the colour is gone, not added — can only be re-dyed by a specialist)</li>
<li>Rust (iron oxidation — requires acid treatment that may discolour the carpet)</li>
<li>Henna (Dubai-specific challenge — comes out in shadow form usually)</li>
</ul>

<h2>Pricing</h2>
<table style="width:100%;border-collapse:collapse;margin:14px 0;font-size:14.5px">
<tr style="background:#F8FAFC"><th style="text-align:left;padding:8px;border-bottom:1px solid #E2E8F0">Service</th><th style="text-align:right;padding:8px;border-bottom:1px solid #E2E8F0">Price</th></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Carpet hot water extraction (per sqft)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9"><b>AED 4</b></td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Minimum job</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">AED 180 (≈45 sqft)</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Persian / wool rug (per sqft, off-site recommended)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">AED 6</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Stain pre-treatment (per stain over 10cm)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">AED 30</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Pet urine deep-treatment (per affected area)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">AED 60</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Same-day event-prep surcharge</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">+ AED 100</td></tr>
</table>
<p><em>Whole-villa packages from AED 1,400 (typically 350–400 sqft of carpet across bedrooms + lounge). 3BHK apartments typically AED 480–680.</em></p>

<h2>Booking timeline that actually works</h2>
<p>If you're hosting an event (Eid lunch, Diwali dinner, anniversary, in-laws visiting), book 3–4 days in advance. Friday + Saturday slots fill up by Wednesday. Our same-day event-prep service runs Sundays through Thursdays during business hours — we'll work around your party schedule (e.g., 09:00–13:00 clean, dry by 17:00 for an evening event).</p>""",
        "faqs": [
            ("Will the carpet shrink or get damaged?", "Hot water extraction at 60°C with controlled extraction doesn't shrink properly-installed wall-to-wall carpet — that's a myth from the old days of soak-and-leave shampooing. Loose rugs (Persian, wool) we handle differently — typically picked up for off-site cleaning to avoid edge curling. We'll inspect on arrival and tell you if anything looks at risk."),
            ("How long until I can walk on it?", "30 minutes after we finish, you can walk on it in socks. Fully dry in 3–4 hours in normal AC. We bring air movers (small fans) to accelerate drying in humid rooms or rainy seasons. If you have a tight event deadline, tell us when booking and we'll bring more fans."),
            ("Can you guarantee a specific old stain will come out?", "We can't promise. We can pre-test on a corner of the stain to predict success. For high-value stains (wine on a wedding-gift carpet), we sometimes recommend an inspection visit (AED 100, deducted from the clean) so we can evaluate fibres and the stain age before committing."),
            ("Do you move the furniture?", "Standard furniture yes — sofas, side tables, coffee tables, dining sets (up to 100 kg each, manageable by two people). Heavy items (piano, safe, 6-seat marble dining table, large dressers) we ask you to clear, or we can quote a furniture move separately (AED 80–200 depending on items)."),
            ("Will it smell of chemicals?", "Mild fresh-detergent scent during the clean, dissipates within 2 hours. We use biodegradable, low-VOC cleaning agents — safe for kids and pets once the carpet is dry. No bleach or harsh solvents on residential jobs."),
            ("My carpet is white / cream. Can you handle it without ruining it?", "Yes — we use neutral-pH detergent on light carpets (alkaline cleaners can cause yellowing). For very valuable light wool rugs we usually recommend off-site cleaning with a fibre-rinse step. Tell us the carpet type when booking."),
            ("Do you do mattresses + sofas too?", "Yes — sofas AED 60/seat (3-seater AED 180), mattresses AED 120 (single) / AED 180 (king). Often discounted when bundled with carpets."),
            ("Do you cover non-Dubai areas?", "Yes — Sharjah, Ajman, Abu Dhabi. Cross-emirate jobs add AED 80–150 fuel surcharge and book 24–48 hr in advance."),
        ],
        "related_blog_slugs": [],
        "image_prompt": "Professional carpet cleaning technician in mint-green branded uniform using a Karcher truck-mount steam extraction wand on a beige wool carpet in a modern Dubai villa living room, visible foam, clean section vs dirty section contrast, photorealistic professional photography",
        "schema_service_type": "Carpet Cleaning Service",
    },

    # ─────────────────────────────────────────────────────────────────────
    # 4. ELECTRICIAN — emergency intent, DEWA-side work
    # ─────────────────────────────────────────────────────────────────────
    {
        "slug": "electrician-dubai",
        "parent_svc_id": "electrical",
        "alias_prefix": "electrician",
        "h1": "Electrician in Dubai — DEWA-Licensed, 60-Min Dispatch · AED 180 Visit",
        "meta_title": "Electrician Dubai · DEWA-Licensed · 60-Min Dispatch · AED 180 · Servia",
        "meta_desc": "DEWA-licensed electrician in Dubai — short circuit, MCB trip, socket repair, ceiling fan install, chandelier hanging. Same-day for power outages. AED 180 visit, parts at cost.",
        "subtitle": "Electrical problems in Dubai apartments fall into two buckets: <em>annoying</em> (a socket stopped working) and <em>scary</em> (the whole apartment lost power, or a switch is sparking). Either way, you want a real electrician with a DEWA trade card on the van — not a handyman with a screwdriver hoping for the best. Servia's electricians arrive in 60 minutes for emergencies, AED 180 visit charge covers diagnosis and the first hour of work, parts are billed at supplier cost.",
        "stats": [
            ("Visit charge", "AED 180"),
            ("Emergency dispatch", "60 min"),
            ("Parts markup", "AED 0 (at cost)"),
            ("Available", "7 days, 22:00 emergency"),
        ],
        "why_us": [
            "DEWA-licensed (Dubai), SEWA-licensed (Sharjah), AADC-licensed (Abu Dhabi) electricians — trade card visible on the uniform",
            "Test pen + multimeter + clamp meter + circuit tracer on every visit — we diagnose before we tear anything out",
            "Common parts on the van: MCBs (6/10/16/20A), RCDs, sockets (UK 3-pin + USB combo), ceiling rose plates, fan capacitors, dimmer switches",
            "Photo report of the MCB panel before-and-after so you have a record (useful when you sell the apartment or hand it back to landlord)",
            "Same-day for power outages and active sparks; routine bookings (fan install, dimmer swap) book next-day",
            "If we diagnose a DEWA-side problem (meter, building feeder, common-area) we tell you and don't charge for the visit",
        ],
        "body_html": """<h2>The four scariest electrical situations in a Dubai apartment</h2>
<ol>
<li><strong>Whole-apartment power loss but neighbours have power.</strong> Almost always your apartment's main MCB has tripped — usually triggered by an overload (running the dryer + AC + kettle at the same time on the same circuit). We reset, then test under load to find the weak point. AED 180–260 typical.</li>
<li><strong>One socket sparking or smelling burnt.</strong> Stop using it immediately, isolate the circuit at the panel, and call. This is genuine fire-risk territory — usually a loose neutral or a damaged backplate. We open the socket, inspect the wiring termination, and replace the unit. AED 220–280 with new socket.</li>
<li><strong>MCB keeps tripping on the same circuit.</strong> Either an overload (you're drawing more current than the breaker is rated for — common when families add a portable AC), or a downstream fault (damaged appliance, water-soaked wiring). We use a clamp meter to measure the actual current draw and a continuity tester to find faults. AED 240–400.</li>
<li><strong>Whole-building outage (neighbours also dark).</strong> Not your problem to fix — it's DEWA or the building infrastructure. We can confirm it's not your apartment in 5 min and not charge for the visit. Then you wait for DEWA / building management.</li>
</ol>

<h2>The routine work we do every day</h2>
<ul>
<li><strong>Ceiling fan + light combo install:</strong> AED 220–300 per fan, includes ceiling rose, isolator, balancer. Bring your own fan or we can supply from common brands (Crompton, Khind, Panasonic).</li>
<li><strong>Chandelier hanging:</strong> AED 280–450 depending on weight + ceiling height. Up to 25 kg fixtures, with proper toggle-bolt or expansion anchor depending on ceiling material.</li>
<li><strong>Dimmer switch swap:</strong> AED 180 with switch (LED-compatible dimmer for modern LED fittings).</li>
<li><strong>USB socket upgrade:</strong> AED 220 (UK 3-pin + 2× USB-A or USB-C combo unit, common request for kids' rooms + home offices).</li>
<li><strong>MCB / RCD panel work:</strong> Adding a new circuit, replacing a failed MCB, RCD installation for wet rooms. AED 280–600 depending on panel complexity.</li>
<li><strong>Concealed wiring repair:</strong> If a previous tenant nailed something into a wall and hit a wire, we cut the wall open (minimally), splice + repair, and seal up. AED 380–650. The wall repair we hand off to our carpentry team.</li>
<li><strong>EV charger install (Tesla / Lucid / Polestar):</strong> Wall charger up to 7kW we do under our scope. Higher-amp chargers need DEWA approval first — we coordinate that separately. AED 1,200–1,800 install (charger unit supplied separately).</li>
</ul>

<h2>What we don't touch — and why</h2>
<p><strong>DEWA meter and the cabling between the meter and your apartment's main panel.</strong> That's DEWA's regulated zone — only DEWA-registered contractors can work on it. If the problem is on that side, we'll identify it and refer you to the right contractor.</p>
<p><strong>Building common areas (corridor lighting, lobby panels).</strong> That's the building's facilities management, not us.</p>
<p><strong>Solar / inverter installations.</strong> Specialist territory — we don't do battery + inverter integrations. For solar consultations we refer to a partner contractor.</p>

<h2>Cross-emirate coverage + licensing</h2>
<p>Our electricians hold the right trade card for the emirate they work in: <strong>DEWA</strong> for Dubai, <strong>SEWA</strong> for Sharjah + Hatta, <strong>FEWA</strong> for Ajman + RAK + UAQ + Fujairah, <strong>AADC</strong> for Abu Dhabi. When you book, our system routes you to the right technician — you don't have to figure this out.</p>""",
        "faqs": [
            ("Can you fix it tonight?", "For active emergencies (sparking socket, full-apartment power loss, burning smell) — yes, dispatch within 60–90 min, surcharge AED 80 after 22:00. For routine work (install a new fan, replace a dimmer) we book next-day during business hours."),
            ("My whole apartment lost power — is that your problem to fix?", "First step: check if neighbours have power. If they don't, it's a building/DEWA problem and we can confirm in 5 min without charge. If only your apartment is dark, your main MCB has tripped. We'll reset it, test under load, and find the cause (overloaded circuit, faulty appliance). AED 180–260 typical."),
            ("Do you supply the parts or do I?", "Either. Common stuff (MCBs, sockets, fan capacitors, dimmer switches) we carry on the van. For specific items (a particular brand of designer dimmer, a specific chandelier you bought from Italy), bring your own. We charge labour only."),
            ("Is your electrician licensed?", "Yes, for the emirate we're operating in: DEWA in Dubai, SEWA in Sharjah, FEWA in northern emirates, AADC in Abu Dhabi. We can WhatsApp you a photo of the trade card before the visit on request."),
            ("Can you install a ceiling fan I bought from Carrefour?", "Yes. Standard ceiling rose, isolator switch, and balancer if needed. AED 220–300 install. We test it for wobble + electrical safety before leaving. If the fan is faulty out-of-box, we'll tell you to return it before we install."),
            ("I want to add a USB socket — is that expensive?", "AED 220 with the part (UK 3-pin + USB-A + USB-C combo unit). 25 min job. We swap the existing socket on the same circuit. No new wiring needed unless you want it in a totally new location."),
            ("What about a Tesla / EV charger?", "Up to 7kW wall charger (Tesla Wall Connector, ABB Terra) we do under our scope — AED 1,200–1,800 install on a dedicated 32A circuit, assuming your panel has spare capacity. Above 7kW requires DEWA approval first; we coordinate that separately and quote post-approval."),
            ("I'm worried about my landlord's deposit — will you give me proof of work?", "Yes. Every job ends with a WhatsApp report: photos of the panel before/after, parts replaced (with receipts), labour breakdown, and a 30-day workmanship warranty in writing. Useful for landlord deposit disputes — we've helped many tenants prove the work was done to standard."),
        ],
        "related_blog_slugs": [],
        "image_prompt": "Licensed electrician in mint-green branded uniform with DEWA trade card on chest, using a multimeter to test a wall socket in a modern Dubai apartment, MCB panel visible in background, organized blue tool kit on floor, photorealistic professional photography, well-lit",
        "schema_service_type": "Electrician",
    },

    # ─────────────────────────────────────────────────────────────────────
    # 5. BED BUG TREATMENT — highest pest CPC, premium intent
    # ─────────────────────────────────────────────────────────────────────
    {
        "slug": "bed-bug-treatment-dubai",
        "parent_svc_id": "pest_control",
        "alias_prefix": "bed-bug-treatment",
        "h1": "Bed Bug Treatment in Dubai — Heat + Chemical Combo · 90-Day Re-Treatment Warranty",
        "meta_title": "Bed Bug Treatment Dubai · Heat + Chemical · 90-Day Warranty · Servia",
        "meta_desc": "Bed bug treatment in Dubai by Servia — heat treatment (60°C+) + residual chemical, rotated compounds, 90-day re-treatment warranty. From AED 350. K9 inspection optional.",
        "subtitle": "Bed bugs are the worst pest a Dubai apartment can have. They breed in mattress seams, headboards, behind skirting, inside electronics — and a single missed female lays 300 eggs in her lifetime. Most of the AED 250 bed bug \"treatments\" you see advertised do one chemical spray on visible mattresses and leave. Three weeks later, the bugs come back from the spots that weren't treated. We use a heat + chemical combo, three rotated pesticide compounds (to prevent resistance), and a 90-day re-treatment warranty. From AED 350 for a 1-bedroom apartment.",
        "stats": [
            ("Starting price", "AED 350"),
            ("Treatment time", "2–3 hrs"),
            ("Re-treatment warranty", "90 days"),
            ("Method", "Heat + chemical combo"),
        ],
        "why_us": [
            "K9-inspection dog optional (AED 200) — finds bugs before treatment, so you only pay to treat the rooms that actually have them",
            "Heat treatment (60°C+ steam) for mattresses, headboards, electronics, soft furnishings — bugs and eggs die in 90 seconds at that temperature, places sprays can't reach",
            "Three rotated pesticide compounds (cypermethrin, deltamethrin, imidacloprid) — bed bugs develop resistance to single-chemical treatments in 6–8 generations",
            "Residual chemical lasts 60 days on skirting boards, bed frames, door frames — catches bugs that emerge from eggs after the initial treatment",
            "Photo-documented before-and-after report (useful for landlord disputes about who pays)",
            "90-day re-treatment warranty — if a single bug is spotted within 90 days, we come back free",
        ],
        "body_html": """<h2>Why 80% of Dubai bed bug treatments fail</h2>
<p>The bed bug industry in the UAE has a quality problem. Most providers will quote AED 250 for a one-bedroom flat, arrive with one chemical sprayer, spray visible mattresses and the headboard, and leave in 45 minutes. That treats maybe 30% of where the bugs actually are. The other 70% — inside electronics (alarm clocks, lamps, kettles), behind skirting boards, inside power sockets, in soft toys, in suitcases, in clothes folded in drawers — gets nothing. Three weeks later, the eggs from those untreated spots hatch, the cycle restarts, and the customer is left thinking "bed bugs are impossible to get rid of." They're not — but they require a real protocol.</p>

<h2>The Servia bed bug protocol</h2>
<ol>
<li><strong>Inspection (30 min):</strong> We strip the bed (you don't have to be home for this part — we WhatsApp photos to show you). We inspect mattress seams with a UV black-light (bug fluid fluoresces), check the headboard joints, slide off socket plates near the bed, lift the bed frame to check the legs and bottom rail, and inspect any wood furniture within 3 metres of the bed.</li>
<li><strong>K9 inspection (optional, +AED 200):</strong> A trained Belgian Malinois detection dog finds live bugs by smell — accurate to about 96% per peer-reviewed studies. Useful when you suspect bugs in a second bedroom or you want confirmation a treatment worked.</li>
<li><strong>Pre-treatment prep:</strong> You wash all bedding + clothing within reach of the bed on a 60°C wash cycle (we provide a list). We bag and isolate stuffed toys, books, electronics for separate treatment.</li>
<li><strong>Heat treatment (60–80 min):</strong> Steam at 60°C+ applied to mattress seams, headboard, bed frame joints, skirting board edges, behind picture frames. Bugs and eggs die in 90 seconds. This is the killing step for the parts where chemicals can't reach.</li>
<li><strong>Chemical treatment (40 min):</strong> Residual contact insecticide applied to skirting, behind bed, door frames, cracks in furniture. Compounds rotated — cypermethrin first visit, deltamethrin at follow-up, imidacloprid at warranty re-treat. This prevents the bugs from developing resistance to any single chemical (which they do in 6–8 generations if you use the same one).</li>
<li><strong>Electronics:</strong> Alarm clocks, lamps, kettles, fan motors — these are heated to 50°C in a sealed chamber (we bring portable heaters). Kills bugs without damaging electronics.</li>
<li><strong>Post-treatment:</strong> 4–6 hour ventilation, then you can use the room. Encasement of mattress + box spring in bug-proof zip cover recommended (AED 90 per mattress, optional).</li>
<li><strong>Follow-up (day 14):</strong> Free inspection visit. Eggs from before treatment can survive a week and hatch into juveniles — we catch them at this visit before they reach reproductive age (3 weeks).</li>
</ol>

<h2>Pricing — flat-rate, all-inclusive</h2>
<table style="width:100%;border-collapse:collapse;margin:14px 0;font-size:14.5px">
<tr style="background:#F8FAFC"><th style="text-align:left;padding:8px;border-bottom:1px solid #E2E8F0">Property</th><th style="text-align:right;padding:8px;border-bottom:1px solid #E2E8F0">Price (AED)</th></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Studio / 1BHK (one bedroom treated)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9"><b>350</b></td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">2BHK (both bedrooms + lounge)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9"><b>520</b></td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">3BHK</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9"><b>720</b></td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Villa (up to 5 bedrooms)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9"><b>1,180</b></td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">K9 detection dog inspection (add-on)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">+ 200</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Mattress encasement (per mattress)</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">90</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">Day-14 follow-up inspection</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">Included (free)</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #F1F5F9">90-day re-treatment if bugs return</td><td style="text-align:right;padding:8px;border-bottom:1px solid #F1F5F9">Included (free)</td></tr>
</table>

<h2>Where bed bugs come from in Dubai apartments</h2>
<p>The most common sources, in order: (1) <strong>international travel</strong> — bugs hitch in suitcases from hotels and AirBnBs, especially after trips to Europe, Egypt, India; (2) <strong>used furniture</strong> — second-hand mattresses, headboards, sofas from Dubizzle or moved-in roommates; (3) <strong>building infiltration</strong> — apartments adjacent to or above units that have an active infestation, bugs migrate through wall cavities; (4) <strong>delivery boxes</strong> — rare but documented, especially from second-hand or returned merchandise. The seasonal pattern: bed bug calls spike in October–December (post-summer travel returns) and June–July (Eid travel).</p>""",
        "faqs": [
            ("How do I know it's bed bugs and not something else?", "Three signs: (1) small itchy bites in a line or cluster, usually on arms/legs/back/torso (bed bug bites come in groups of 3 because the bug feeds, gets disturbed, moves a few cm, feeds again); (2) tiny dark spots on the bed sheet near the seams (digested blood); (3) live bugs visible at night (they hide during the day). Send us a photo on WhatsApp before booking and we'll confirm. We can also do an inspection-only visit (AED 200, deducted from any treatment booked) if you're unsure."),
            ("How quickly will the bugs be gone?", "Adult bugs die during the heat treatment (Day 0). Juveniles emerging from eggs in the first 7–14 days are killed by the residual chemical or the Day-14 follow-up visit. Bites should stop within 7 days post-treatment. By Day 21 (one full reproductive cycle), the population is eliminated in 92% of single-treatment cases. The other 8% need the warranty re-treatment, which is free."),
            ("Do I need to throw out my mattress?", "Almost never. Heat + chemical combo with mattress encasement deals with bugs and eggs without you needing to replace anything. The cases where we recommend replacement: severely infested foam mattresses where the bugs are inside the foam (rare), or mattresses already at the end of life (8+ years old, sagging)."),
            ("Is the chemical safe for kids and pets?", "Yes after the dry time (4 hours). The compounds we use — cypermethrin, deltamethrin, imidacloprid — are EPA-registered and approved for residential use in the UAE. We apply targeted to cracks and crevices, not broadcast. Ventilate for 4 hours after treatment, then the rooms are safe to re-enter. We recommend keeping pets out of treated rooms for 6 hours as extra precaution."),
            ("Can the K9 dog find bugs before we treat?", "Yes — a Belgian Malinois trained for bed bug detection finds live bugs by smell with about 96% accuracy. Useful when (a) you suspect bugs but don't see them, (b) you want to confirm an infestation is limited to one room before paying to treat the whole apartment, (c) you want post-treatment verification."),
            ("What if I'm a tenant and the landlord won't pay for treatment?", "Per UAE tenancy law, who pays depends on cause — if bugs were brought in by the tenant (travel, used furniture), tenant pays; if they came from a neighbouring unit or were pre-existing, landlord typically pays. Our photo-documented report helps in disputes. We're also happy to provide a written technical opinion (free) on likely source."),
            ("Do you treat just one room or do I need to treat the whole apartment?", "If we (or the K9) only find bugs in one room and there's no evidence they've migrated (no bite reports from other rooms, no bugs seen elsewhere), we treat that room only. But adjacent rooms get a preventive residual application at no extra charge — bugs travel. For a confirmed multi-room infestation, full-apartment treatment is the only way to actually solve it."),
            ("How is this different from a AED 200 bed bug treatment?", "The AED 200 quotes are usually one chemical spray, one visit, no heat treatment, no follow-up, no warranty. Bugs hide in places spray can't reach. Three weeks later, eggs hatch and the infestation restarts. Our treatment costs more because it actually solves the problem — heat + chemical combo, three rotated compounds, free follow-up, 90-day warranty."),
        ],
        "related_blog_slugs": ["abu-dhabi-reem-island-bed-bugs-why-80-percent-fail", "jumeirah-pre-moving-in-pest-checklist-villa"],
        "image_prompt": "Pest control technician in mint-green branded uniform with protective gear, using a professional heat-treatment steam wand on a mattress in a modern Dubai apartment bedroom, mattress encasement visible, organized tool kit on floor, photorealistic professional photography, well-lit",
        "schema_service_type": "Pest Control Service",
    },
]


# Helper: build a lookup map slug → entry for fast route resolution.
VARIANT_BY_SLUG = {v["slug"]: v for v in VARIANT_PAGES}

# Helper: which alias prefixes have a rich variant page (for sister-LP canonical
# redirection). Maps alias_prefix → the slug of the rich page.
RICH_ALIAS_TO_SLUG = {v["alias_prefix"]: v["slug"] for v in VARIANT_PAGES}
