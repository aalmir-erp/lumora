"""v1.24.140 — Arabic content overlay for the Arabic landing pages.

WHY THIS EXISTS
---------------
The Arabic LPs registered in v1.24.133 (app/ar_lp_pages.py) only flipped
the HTML to lang=ar dir=rtl and translated the <title> + <meta> — but the
PAGE CONTENT is JS-rendered from services.json which is English-only.
Result: customers saw an Arabic URL load an English page with a broken
RTL-flipped layout (the existing CSS is LTR-only).

THIS MODULE FIXES THAT
----------------------
- SERVICE_AR_CONTENT: per-service Arabic translations of the visible
  fields the service.html JS renders (name, description, benefits,
  duration_label, team_label).
- UI_AR: ~30 static UI strings that appear in service.html as hardcoded
  text (Book now, Get instant quote, Why book with Servia?, etc.).

HOW IT'S APPLIED
----------------
The Arabic LP renderer (app/ar_lp_pages.py) injects:
  1. window.__SERVIA_AR_CONTENT = { service: {...}, ui: {...} }
  2. A small overlay script that, after service.html JS finishes rendering,
     traverses the DOM and swaps:
        - The H1 (#svc-name) → SERVICE_AR_CONTENT[svc_id].name
        - The lead (#svc-desc) → SERVICE_AR_CONTENT[svc_id].description
        - The benefits grid → translated benefits
        - All hardcoded UI strings via a string-replace pass

Layout: we drop dir=rtl for now — the existing CSS is LTR-only and
flipping it broke the layout (overflowing buttons, off-screen sections).
Reinstating dir=rtl requires an RTL CSS refactor (Phase 4 work).

QUALITY OF TRANSLATIONS
-----------------------
These are written in Modern Standard Arabic (MSA) using forms commonly
typed by UAE searchers in Google (no diacritics, common spellings). A
UAE-native review pass is still recommended before showing this to
paid traffic at scale — particularly to verify:
  - Service-name word choice (سباك vs سمكري vs فني سباكة)
  - Whether to use definite article ال or not
  - Tone (formal MSA vs colloquial Khaliji)
"""

# ─────────────────────────────────────────────────────────────────────
# Per-service translations.
# Keys are service IDs matching services.json.
# Fields:
#   name         — short headline form (1-3 words)
#   description  — one-sentence lead (10-20 words)
#   benefits     — 3-5 short benefit bullets (4-10 words each)
#   duration_label — duration description (replaces e.g. "3-6 hours")
#   team_label   — team description (replaces e.g. "2 trained cleaners")
# ─────────────────────────────────────────────────────────────────────
SERVICE_AR_CONTENT: dict[str, dict] = {
    "deep_cleaning": {
        "name": "تنظيف عميق للمنزل",
        "description": "تنظيف شامل من الأعلى إلى الأسفل: إزالة الدهون من المطبخ، إزالة الكلس من الحمام، تنظيف نقاط اللمس.",
        "benefits": [
            "يزيل 99٪ من حشرات الغبار والمسببات للحساسية",
            "تنظيف داخل الفرن والمطبخ بعمق",
            "تنظيف الحمامات وإزالة الترسبات الكلسية",
            "فريق محترف بأدوات احترافية",
        ],
        "duration_label": "٣-٦ ساعات",
        "team_label": "عاملا تنظيف مدربان",
    },
    "ac_cleaning": {
        "name": "تنظيف المكيفات وأنابيب التهوية",
        "description": "تنظيف المكيفات السبليت والأنظمة المركزية. غسيل الملفات، تنظيف صينية التصريف، استبدال الفلتر.",
        "benefits": [
            "يقلل فاتورة الكهرباء بنسبة ١٥-٣٠٪",
            "يزيل العفن والبكتيريا → حساسية أقل",
            "يستعيد كفاءة التبريد",
            "يطيل عمر الكومبروسر ٣-٥ سنوات",
        ],
        "duration_label": "٤٥-٩٠ دقيقة لكل وحدة",
        "team_label": "فني مكيفات معتمد",
    },
    "sofa_carpet": {
        "name": "غسيل الأرائك والسجاد بالبخار",
        "description": "غسيل احترافي بالبخار للأرائك والسجاد والمراتب والكراسي. يستخدم أجهزة كارشر صناعية.",
        "benefits": [
            "يزيل ٩٥٪ من البقع القابلة للذوبان",
            "وقت تجفيف ٣-٤ ساعات فقط",
            "علاج مجاني للعث وحشرات الغبار",
            "ضمان البقع لمدة ٣٠ يوماً",
        ],
        "duration_label": "ساعة إلى ساعتين",
        "team_label": "فني تنظيف مدرب",
    },
    "maid_service": {
        "name": "خدمة عاملة منزلية بالساعة",
        "description": "عاملات منزل متدربات بأنظمة الإمارات للزيارات الأسبوعية أو الشهرية أو لمرة واحدة.",
        "benefits": [
            "موثقة الخلفية ومؤمَّنة بالكامل",
            "نفس العاملة لكل زيارة متابعة",
            "خبرة في تنظيف العمائر والفلل",
            "أدوات تنظيف يمكن إحضارها",
        ],
        "duration_label": "ساعتان كحد أدنى",
        "team_label": "عاملة منزلية واحدة",
    },
    "plumbing": {
        "name": "خدمة سباكة معتمدة",
        "description": "تسريبات الصنابير، انسداد المصارف، ضعف الضغط، تركيب سخان الماء، إصلاح المراحيض. سباك مرخص من بلدية دبي.",
        "benefits": [
            "مرخص من بلدية دبي / DEWA",
            "قطع الغيار متوفرة - إنهاء في زيارة واحدة",
            "نفس اليوم لتسربات المياه",
            "صور مرفقة بكل عمل للتوثيق",
        ],
        "duration_label": "٣٠ دقيقة - ساعتان",
        "team_label": "سباك واحد مرخص",
    },
    "electrical": {
        "name": "خدمة كهرباء معتمدة",
        "description": "إصلاح القواطع، الدوائر القصيرة، تركيب المراوح، تركيب الثريات، أعمال لوحة الكهرباء. كهربائي مرخص من DEWA.",
        "benefits": [
            "كهربائي مرخص DEWA / SEWA",
            "أدوات قياس احترافية - تشخيص قبل الإصلاح",
            "قطع غيار متوفرة بالسيارة",
            "نفس اليوم لانقطاع الكهرباء",
        ],
        "duration_label": "٣٠ دقيقة - ساعتان",
        "team_label": "كهربائي مرخص",
    },
    "carpentry": {
        "name": "خدمة نجارة",
        "description": "تركيب الأرفف، إصلاح الأبواب والخزائن، تجميع أثاث ايكيا، تركيب الستائر، أعمال نجارة عامة.",
        "benefits": [
            "خبرة في تجميع أثاث ايكيا",
            "إصلاح الأبواب وإعادة تركيب المفصلات",
            "تركيب الأرفف بأنواع الجدران الإماراتية",
            "أدوات نجارة احترافية",
        ],
        "duration_label": "ساعة إلى ٣ ساعات",
        "team_label": "نجار مدرب",
    },
    "handyman": {
        "name": "خدمة فني صيانة عام",
        "description": "إصلاحات منزلية متنوعة، تركيبات، أعمال صيانة عامة، أقفال، أعمال صغيرة لا تستحق سباك أو كهربائي.",
        "benefits": [
            "مهارات متعددة في زيارة واحدة",
            "أدوات شاملة بالسيارة",
            "أسعار شفافة بالساعة",
            "متاح نفس اليوم",
        ],
        "duration_label": "ساعة إلى ٣ ساعات",
        "team_label": "فني صيانة مدرب",
    },
    "pest_control": {
        "name": "مكافحة الحشرات",
        "description": "مكافحة الصراصير، البق، النمل، الفئران، البعوض. مبيدات معتمدة من البلدية، فرق ISO ومرخصة.",
        "benefits": [
            "مبيدات معتمدة من بلدية دبي",
            "ضمان إعادة الرش لمدة ٩٠ يوماً",
            "ثلاث مركبات مختلفة لمنع المقاومة",
            "تقرير بالصور بعد كل علاج",
        ],
        "duration_label": "ساعتان إلى ٣ ساعات",
        "team_label": "فني مكافحة بمعدات حماية",
    },
    "mobile_repair": {
        "name": "إصلاح الجوال والموبايل",
        "description": "إصلاح شاشة، استبدال بطارية، استرداد بيانات، إصلاح زر الطاقة. آيفون، سامسونج، هواوي، أوبو وغيرها.",
        "benefits": [
            "قطع غيار أصلية أو OEM",
            "ضمان ٦٠ يوماً على الإصلاحات",
            "زيارة منزلية متاحة",
            "أسعار شفافة قبل البدء",
        ],
        "duration_label": "٣٠ دقيقة - ساعتان",
        "team_label": "فني هواتف معتمد",
    },
    "laptop_repair": {
        "name": "إصلاح اللابتوب والحاسوب",
        "description": "تنظيف ماء، استبدال البطارية، إصلاح المروحة، ترقية الذاكرة، استرداد بيانات. ماك بوك، ديل، HP، لينوفو.",
        "benefits": [
            "تخصص MacBook + لابتوبات الويندوز",
            "استرداد بيانات بنسبة نجاح ٩٢٪",
            "خدمة منزلية أو ورشة",
            "ضمان ٦٠ يوماً على الإصلاحات",
        ],
        "duration_label": "ساعة إلى يوم واحد",
        "team_label": "فني حاسوب معتمد",
    },
    "fridge_repair": {
        "name": "إصلاح الثلاجات والمجمدات",
        "description": "ثلاجات لا تبرد، تسرب الماء، إعادة تعبئة الغاز، استبدال المروحة، إصلاح صانعة الثلج. سامسونج، إل جي، بوش وغيرها.",
        "benefits": [
            "تخصص في علامات أوروبية + آسيوية",
            "إعادة تعبئة الغاز R134a / R600a",
            "زيارة منزلية لتجنب فقدان الطعام",
            "ضمان ٦٠ يوماً على الأعمال",
        ],
        "duration_label": "ساعة إلى ٣ ساعات",
        "team_label": "فني تبريد معتمد",
    },
    "washing_machine_repair": {
        "name": "إصلاح الغسالات والنشافات",
        "description": "تسربات المياه، طبل لا يدور، أكواد أخطاء، استبدال المضخة، إصلاح المحرك. غسالات أمامية + علوية.",
        "benefits": [
            "تخصص في غسالات Bosch / Samsung / LG",
            "قطع غيار شائعة متوفرة بالسيارة",
            "تشخيص رسوم زيارة فقط (١٨٠ درهم)",
            "ضمان ٦٠ يوماً على الأعمال",
        ],
        "duration_label": "ساعة إلى ٣ ساعات",
        "team_label": "فني أجهزة معتمد",
    },
    "babysitting": {
        "name": "جليسة أطفال موثوقة",
        "description": "جليسات أطفال مدربات على الإسعافات الأولية، مع شهادات حماية الطفل. متاحات بالساعة أو لزيارات منتظمة.",
        "benefits": [
            "شهادة الإسعافات الأولية CPR",
            "موثقات الخلفية + مؤمَّنات",
            "نفس الجليسة لزيارات المتابعة",
            "متخصصات من ٦ أشهر إلى ١٢ سنة",
        ],
        "duration_label": "٣ ساعات كحد أدنى",
        "team_label": "جليسة واحدة معتمدة",
    },
    "car_wash": {
        "name": "غسيل سيارات في موقعك",
        "description": "غسيل سيارات منزلي - بالماء أو بدون ماء. تنظيف داخلي، تلميع، شمع، تنظيف المقاعد بالبخار.",
        "benefits": [
            "نأتي إلى موقعك - فيلا أو موقف",
            "خيار بدون ماء (موفر للماء)",
            "خيار تلميع وشمع متاح",
            "تنظيف داخلي + خارجي شامل",
        ],
        "duration_label": "٤٥ دقيقة - ساعتان",
        "team_label": "فني تلميع سيارات",
    },
    "chauffeur": {
        "name": "سائق خاص بالساعة",
        "description": "سائقون مرخصون لاستخدامك بالساعة أو لرحلات محددة. مطار، تسوق، اجتماعات، رحلات شاملة.",
        "benefits": [
            "رخصة قيادة إماراتية + تدريب لياقة",
            "متعدد اللغات (عربي + إنجليزي + أوردو)",
            "متاح ٢٤/٧ لخدمة المطار",
            "أسعار شفافة بالساعة",
        ],
        "duration_label": "٤ ساعات كحد أدنى",
        "team_label": "سائق واحد مرخص",
    },
    "painting": {
        "name": "صباغة الجدران والديكور",
        "description": "صباغة داخلية وخارجية، تجديد كامل، لمسات صغيرة، اختيار الألوان. دهانات Jotun وMaster.",
        "benefits": [
            "دهانات Jotun منخفضة الانبعاثات",
            "تغطية الأرضيات والأثاث",
            "تنظيف كامل بعد الانتهاء",
            "ضمان جودة لمدة سنة",
        ],
        "duration_label": "يوم إلى ٣ أيام",
        "team_label": "صباغان مدربان",
    },
    "gardening": {
        "name": "بستنة وعناية بالحديقة",
        "description": "قص العشب، تقليم الأشجار، صيانة نظام الري، تصميم المناظر الطبيعية، علاج العشب.",
        "benefits": [
            "خبرة بنباتات الإمارات",
            "صيانة دورية أو زيارة واحدة",
            "تقليم احترافي للأشجار",
            "إصلاح وفحص نظام الري",
        ],
        "duration_label": "ساعتان إلى ٤ ساعات",
        "team_label": "بستاني مدرب",
    },
    "moving": {
        "name": "نقل الأثاث والعفش",
        "description": "نقل سكني وتجاري، تفكيك وتركيب الأثاث، تغليف، نقل بين الإمارات. شاحنات بالكامل أو متشاركة.",
        "benefits": [
            "تأمين شامل ضد الأضرار",
            "تفكيك وتركيب الأثاث مشمول",
            "خيارات تغليف احترافي",
            "نقل بين جميع الإمارات",
        ],
        "duration_label": "نصف يوم إلى يوم كامل",
        "team_label": "٢-٤ عمال نقل",
    },
}

# ─────────────────────────────────────────────────────────────────────
# Static UI strings — used in service.html as hardcoded English text.
# The overlay JS does a string-replace pass to swap these.
#
# Key = English source string (must match exactly, case-sensitive)
# Value = Arabic translation
# ─────────────────────────────────────────────────────────────────────
UI_AR: dict[str, str] = {
    # Header / nav
    "Services":          "الخدمات",
    "Coverage":          "المناطق المغطاة",
    "Blog":              "المدونة",
    "My account":        "حسابي",
    "Install":           "تثبيت التطبيق",
    "Book now":          "احجز الآن",
    # Primary CTAs in hero
    "Get instant quote →":    "احصل على سعر فوري ←",
    "Get instant quote":      "احصل على سعر فوري",
    "WhatsApp us":            "راسلنا واتساب",
    "WhatsApp":               "واتساب",
    "Add to bundle":          "أضف إلى الباقة",
    "Chat with me":           "دردش معي",
    "Book →":                 "احجز ←",
    # Hero subtitle
    "Hi, I'm Servia 👋":          "مرحباً، أنا سيرفيا 👋",
    "Tell me your size + location and I'll quote in 5 seconds.":
        "أخبرني بالحجم والموقع وسأعطيك سعراً في ٥ ثوانٍ.",
    # Badges
    "Insured":             "مؤمَّن",
    "Background-checked":  "موثَّق الخلفية",
    "✓ Insured":           "✓ مؤمَّن",
    "✓ Background-checked": "✓ موثَّق الخلفية",
    "🛡️ Insured":         "🛡️ مؤمَّن",
    # Categories
    "Maintenance":         "صيانة",
    "Residential":         "خدمات سكنية",
    "Cleaning":            "تنظيف",
    "Repair":              "إصلاحات",
    "Outdoor":             "خدمات خارجية",
    "Personal":            "خدمات شخصية",
    # Section headers
    "Why book with Servia?":          "لماذا تختار سيرفيا؟",
    "How it works":                   "كيف تعمل الخدمة",
    "Boost your service with add-ons": "عزّز خدمتك بإضافات",
    "Meet your pro":                  "تعرّف على فني الخدمة",
    "Vetted, uniformed, on-brand":    "موثوق، بزي رسمي، احترافي",
    "Frequently asked":               "الأسئلة الشائعة",
    "FAQs":                           "الأسئلة الشائعة",
    "What's included":                "ما هو مشمول",
    "What's not included":            "ما هو غير مشمول",
    "When to book":                   "متى تحجز",
    # Stats line
    "rating":              "تقييم",
    "jobs done":           "مهمة منجزة",
    "trained professionals": "محترفين مدربين",
    # Urgency / slot
    "specialists available in your area · next slot in":
        "اختصاصيين متاحين في منطقتك · الموعد التالي بعد",
    # Price prefix
    "from":                "ابتداءً من",
    "AED":                 "درهم",
    # Process / steps headers
    "You book in 30 seconds":   "تحجز في ٣٠ ثانية",
    "Pro confirms":              "الفني يؤكد",
    "Vetted pro assigned":       "تعيين فني موثوق",
    "Job done":                  "إنجاز المهمة",
    # Misc
    "Get instant price (no signup)":  "احصل على السعر فوراً (بدون تسجيل)",
    "incl. 5% VAT":                    "يشمل ٥٪ ضريبة القيمة المضافة",
    "Same-day":                        "نفس اليوم",
    "Available today":                 "متاح اليوم",
    "Available this week":             "متاح هذا الأسبوع",
    # Banner/CTA
    "→ Allow location for area-specific prices & arrival ETAs":
        "← السماح بالموقع للحصول على أسعار خاصة بمنطقتك ووقت وصول الفني",
    "Allow location":      "السماح بالموقع",
    "Set manually":        "تحديد يدوي",
    # Mascot label
    "Servia the Cleaner": "سيرفيا · المنظف",
    "Servia the AC Pro":  "سيرفيا · فني المكيفات",
    "Servia the Plumber": "سيرفيا · السباك",
    "Servia the Electrician": "سيرفيا · الكهربائي",

    # v1.24.161 — strings caught from live screenshot. Founder demanded
    # we improve translation coverage, not strip the pages.
    # Header right-side category pills
    "Tech & Appliance":        "إلكترونيات وأجهزة",
    "Mobile & Phone Repair":   "إصلاح موبايل وهاتف",
    # Stats line variants (whole text + word fragments for safety)
    "★ rating":                "★ تقييم",
    "+ jobs done":             "+ مهمة منجزة",
    "+ trained professionals": "+ محترفين مدربين",
    "180+ trained professionals": "+180 محترفين مدربين",
    "2,400+ jobs done":        "+2,400 مهمة منجزة",
    "4.9★ rating":             "4.9★ تقييم",
    # Pro section subhead + body
    "👋 MEET YOUR PRO":         "👋 تعرّف على فني الخدمة",
    "MEET YOUR PRO":           "تعرّف على فني الخدمة",
    "Every Servia pro arrives in branded uniform with a printed Servia cap and ID badge. Background-checked, insured, with photo + name pre-shared on WhatsApp before they arrive.":
        "يصل فني سيرفيا بزي رسمي مع قبعة وبطاقة هوية مطبوعة. موثَّق الخلفية، مؤمَّن، مع مشاركة الصورة والاسم على واتساب قبل وصوله.",
    "Background-checked + insured":              "موثَّق الخلفية + مؤمَّن",
    "Branded cap + apron with name tag":         "قبعة وملابس رسمية مع بطاقة الاسم",
    "Photo + ID shared 30 min before arrival":    "الصورة والهوية تُشارك قبل الوصول بـ ٣٠ دقيقة",
    "Same pro returns for follow-up visits":     "نفس الفني يعود للزيارات اللاحقة",
    # Hero chips
    "1 certified technician": "فني معتمد",
    "30-90 minutes":          "٣٠-٩٠ دقيقة",
    # How-it-works steps + descriptions
    "1 · Tell us about it":   "١ · أخبرنا عن الطلب",
    "Pick size + date in 30s. Fixed price quoted instantly.":
        "اختر الحجم والتاريخ في ٣٠ ثانية. سعر ثابت فوراً.",
    "2 · Pay to confirm":     "٢ · ادفع للتأكيد",
    "Apple Pay · Google Pay · Card · Tabby. Slot locked.":
        "آبل باي · جوجل باي · بطاقة · تابي. الموعد محجوز.",
    "3 · Vetted pro assigned": "٣ · تعيين فني موثوق",
    "You get the pro's photo + name on WhatsApp.":
        "تستلم صورة واسم الفني على واتساب.",
    "4 · Live ETA on arrival": "٤ · وقت الوصول مباشر",
    "Track them in real time. Updates every 5 min.":
        "تتبع وقت الوصول مباشرة. تحديثات كل ٥ دقائق.",
    "5 · Service done right":  "٥ · إنجاز الخدمة باحترافية",
    "Photos, invoice, 7-day re-do guarantee.":
        "صور، فاتورة، ضمان إعادة المهمة لـ ٧ أيام.",
    # Service feature checklists
    "✓ Same-day available":           "✓ متاح في نفس اليوم",
    "✓ Background-checked + insured": "✓ موثَّق الخلفية + مؤمَّن",
    "✓ Fixed price · no surprises":   "✓ سعر ثابت · بدون مفاجآت",
    "✓ 7-day re-do guarantee":        "✓ ضمان إعادة لـ ٧ أيام",
    # Coverage / area phrases that show in the urgency banner
    "specialists available in your area":  "اختصاصيين متاحين في منطقتك",
    "next slot in":                         "الموعد التالي بعد",
}


def get_service_ar(service_id: str) -> dict | None:
    """Return Arabic content blob for a service_id, or None if not translated."""
    return SERVICE_AR_CONTENT.get(service_id)
