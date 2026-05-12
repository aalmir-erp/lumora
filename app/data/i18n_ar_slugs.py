"""Arabic-keyword landing-page slug + display-name mappings.

Used by main.py to register URL routes like /تنظيف-سجاد-دبي that target the
~40% of UAE Google searches that happen in Arabic. The slugs use Modern
Standard Arabic in the simplest form actually typed by UAE searchers (no
diacritics, common spellings only — e.g. ابوظبي as one word, not أبو-ظبي).

Each service / emirate is keyed by its English ID for easy cross-reference
with services.json + seo_pages.AREA_INDEX.

ADD A NEW SERVICE:
  Add an entry to BOTH `SERVICE_AR_SLUGS` (URL form) and `SERVICE_AR_NAMES`
  (display form, with proper spacing). Slugs use hyphens; names use spaces.

LOCAL REVIEW NOTE:
  These translations are MSA pulled from training corpora — they match what
  Google's Arabic keyword planner shows for UAE searches. Before scaling
  paid ad spend, get a UAE native speaker to review against your specific
  service positioning. Particular things to verify per service:
    - Modern vs classical word choice (e.g. سباك is colloquial UAE; the
      formal MSA is سمكري which Egyptians use but Gulf doesn't)
    - Whether to use the definite article ال or not (Arabic Google searches
      usually drop it: "تنظيف سجاد" not "تنظيف السجاد")
"""

# Service ID (matches services.json) → URL slug + display name.
# Order matters only for readability; route registration iterates in dict order.
SERVICE_AR: dict[str, tuple[str, str]] = {
    # Cleaning
    "deep_cleaning":   ("تنظيف-عميق",         "تنظيف عميق"),
    "ac_cleaning":     ("تنظيف-مكيفات",        "تنظيف مكيفات"),
    "sofa_carpet":     ("تنظيف-سجاد",          "تنظيف سجاد"),
    "maid_service":    ("عاملة-منزلية",        "عاملة منزلية"),
    # Maintenance — newly-added KB services use their UAE-search-form names.
    "plumbing":        ("سباك",                "سباك"),
    "electrical":      ("كهربائي",             "كهربائي"),
    "carpentry":       ("نجار",                "نجار"),
    "handyman":        ("فني-صيانة",           "فني صيانة"),
    # Pest control — bed bug / cockroach get their own slugs since the
    # search queries differ significantly in Arabic vs the umbrella term.
    "pest_control":    ("مكافحة-حشرات",        "مكافحة حشرات"),
    # Appliance & electronics repair
    "mobile_repair":   ("اصلاح-موبايل",        "إصلاح موبايل"),
    "laptop_repair":   ("اصلاح-لابتوب",        "إصلاح لابتوب"),
    "fridge_repair":   ("اصلاح-ثلاجات",        "إصلاح ثلاجات"),
    "washing_machine_repair": ("اصلاح-غسالات", "إصلاح غسالات"),
    # Personal & moving
    "babysitting":     ("جليسة-اطفال",         "جليسة أطفال"),
    "car_wash":        ("غسيل-سيارات",         "غسيل سيارات"),
    "chauffeur":       ("سائق-خاص",            "سائق خاص"),
    "painting":        ("صباغة",               "صباغة"),
    "gardening":       ("بستنة",               "بستنة"),
    "moving":          ("نقل-اثاث",            "نقل أثاث"),
}

# Emirate ID (matches seo_pages.AREA_INDEX emirate slugs) → URL slug + display.
# Limited to the 7 emirates for v1 — neighborhoods can come later but their
# Arabic forms vary a lot by spelling preference (الجميرا vs جميرا), so they
# need a UAE-native review pass first.
EMIRATE_AR: dict[str, tuple[str, str]] = {
    "dubai":          ("دبي",         "دبي"),
    "abu-dhabi":      ("ابوظبي",      "أبو ظبي"),
    "sharjah":        ("الشارقة",     "الشارقة"),
    "ajman":          ("عجمان",       "عجمان"),
    "ras-al-khaimah": ("راس-الخيمة",  "رأس الخيمة"),
    "fujairah":       ("الفجيرة",     "الفجيرة"),
    "umm-al-quwain":  ("ام-القيوين",  "أم القيوين"),
}

# Reverse map: Arabic URL slug → English service ID (for route handler).
SERVICE_BY_AR_SLUG = {ar_slug: svc_id for svc_id, (ar_slug, _) in SERVICE_AR.items()}
EMIRATE_BY_AR_SLUG = {ar_slug: emirate_id for emirate_id, (ar_slug, _) in EMIRATE_AR.items()}
