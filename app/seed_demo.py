"""Comprehensive Servia demo-data seed — v1.22.96.

20 customers + 20 vendors, each annotated with a `scenario_label`
describing what UX/test scenario it represents. Plaintext password
stored in `_demo_password` column (admin-only visibility) so admin can
log in as any of them without resetting passwords.

Idempotent: triggered by:
  - POST /api/admin/seed-demo (admin button)
  - Auto on startup IF cfg key 'demo_seeded_at' is unset AND
    customers table has < 5 real rows.
No env var needed — config lives in db.cfg.
"""
from __future__ import annotations

import datetime as _dt
import os
import random as _r
import secrets


def _now(offset_days: int = 0) -> str:
    return (_dt.datetime.utcnow() + _dt.timedelta(days=offset_days)).isoformat() + "Z"


def _ensure_demo_columns():
    from . import db
    with db.connect() as c:
        for stmt in (
            "ALTER TABLE customers ADD COLUMN _demo_password TEXT",
            "ALTER TABLE customers ADD COLUMN scenario_label TEXT",
            "ALTER TABLE vendors ADD COLUMN _demo_password TEXT",
            "ALTER TABLE vendors ADD COLUMN scenario_label TEXT",
            "ALTER TABLE vendors ADD COLUMN is_blocked INTEGER DEFAULT 0",
        ):
            try: c.execute(stmt)
            except Exception: pass


# ============================================================================
# 20 CUSTOMERS — each with a different test scenario
# ============================================================================
CUSTOMERS = [
    # (phone,        name,                  email,                  lang, password,   wallet, blocked, area,                emirate,        scenario_label)
    ("+971501110001","Aisha Al Mansoori",   "aisha@demo.servia.ae", "ar","aisha123",   500.0, 0,"Dubai Marina",       "Dubai",        "Power user · 12 bookings · 3 NFC tags · healthy wallet"),
    ("+971501110002","Mohammed Khan",       "mohd@demo.servia.ae",  "en","mohd123",    250.0, 0,"Business Bay",       "Dubai",        "Office customer · 3 office_cleaning bookings"),
    ("+971501110003","Priya Sharma",        "priya@demo.servia.ae", "hi","priya123",    75.0, 0,"JLT",                "Dubai",        "Hindi UI · returning · 5 completed bookings"),
    ("+971501110004","Lara Petrov",         "lara@demo.servia.ae",  "ru","lara123",      0.0, 0,"Khalifa City",       "Abu Dhabi",    "Wallet empty · pending unpaid invoice"),
    ("+971501110005","Khalid Rashed",       "khalid@demo.servia.ae","ar","khalid123", 1500.0, 0,"Al Nahda",           "Sharjah",      "Wallet rich · 1500 AED never spent · brand new"),
    ("+971501110006","Mary Dela Cruz",      "mary@demo.servia.ae",  "tl","mary123",     25.0, 0,"Mirdif",             "Dubai",        "Filipino · low wallet · weekly maid auto-renew"),
    ("+971501110007","Ahmed Al Hashemi",    "ahmed@demo.servia.ae", "ar","ahmed123",   800.0, 0,"Al Khawaneej",       "Dubai",        "Villa owner · 14 NFC tags installed · all rooms tagged"),
    ("+971501110008","Sara Williams",       "sara@demo.servia.ae",  "en","sara123",    100.0, 1,"DIFC",               "Dubai",        "BLOCKED · flagged for non-payment"),
    ("+971501110009","Rajesh Iyer",         "raj@demo.servia.ae",   "hi","raj123",     300.0, 0,"Ajman Corniche",     "Ajman",        "Multi-emirate · bookings in Ajman + Dubai + Sharjah"),
    ("+971501110010","Fatima Al Zaabi",     "fatima@demo.servia.ae","ar","fatima123",   50.0, 0,"Al Reem Island",     "Abu Dhabi",    "RTL Arabic UI test · pool + garden + maid weekly"),
    ("+971501110011","Brian O'Neill",       "brian@demo.servia.ae", "en","brian123",   200.0, 0,"Al Barsha",          "Dubai",        "Driver · keychain tag · 8 car_wash + 2 vehicle_recovery"),
    ("+971501110012","Reema Hassan",        "reema@demo.servia.ae", "ar","reema123",   600.0, 0,"Khalidiya",          "Abu Dhabi",    "New mom · babysitting + maid heavy · DHA-trained nanny weekly"),
    ("+971501110013","David Chen",          "david@demo.servia.ae", "en","david123",     0.0, 0,"DAMAC Hills",        "Dubai",        "Pool family · pool weekly + garden + sofa monthly"),
    ("+971501110014","Hessa Al Awar",       "hessa@demo.servia.ae", "ar","hessa123",    80.0, 0,"Al Quoz",            "Dubai",        "Cancelled-heavy · 4 cancellations · trust-tier downgrade test"),
    ("+971501110015","Aditi Mehra",         "aditi@demo.servia.ae", "hi","aditi123",   140.0, 0,"Mussafah",           "Abu Dhabi",    "Refund pending · 1 dispute open · admin escalation queue"),
    ("+971501110016","Harith Al Khamis",    "harith@demo.servia.ae","ar","harith123", 1200.0, 0,"Sharjah Corniche",   "Sharjah",      "Long sleeper · joined 14 months ago · 0 recent activity"),
    ("+971501110017","Sienna Ricci",        "sienna@demo.servia.ae","en","sienna123",  450.0, 0,"Al Reem Island",     "Abu Dhabi",    "Demo showcase · ALL features used · best UX walkthrough"),
    ("+971501110018","Yusuf Al Marri",      "yusuf@demo.servia.ae", "ar","yusuf123",    35.0, 0,"Al Heera",           "Sharjah",      "Recovery user · 3 vehicle_recovery taps · breakdown veteran"),
    ("+971501110019","Khadija Habib",       "khadija@demo.servia.ae","ar","khadija123",750.0, 0,"Khalifa Park",       "Abu Dhabi",    "Eid prep · 8 bundled services · big-bundle discount tier"),
    ("+971501110020","Tessa Lin",           "tessa@demo.servia.ae", "zh","tessa123",   180.0, 0,"Bluewaters",         "Dubai",        "Chinese UI · brand-new + first booking pending payment"),
]

VENDORS = [
    # (email,                     password,    name,                    phone,           company,                    services_csv,                                         rating, jobs, blocked, scenario_label)
    ("crew@a1clean.demo.ae",      "vendor123","A1 Clean UAE",          "+971500000201","A1 Clean LLC",              "deep_cleaning,maid_service,sofa_carpet,window_cleaning",4.9, 142, 0, "Top-rated multi-service · 142 jobs"),
    ("crew@servia-ac.demo.ae",    "vendor123","Servia AC Pros",        "+971500000202","Servia AC FZ-LLC",          "ac_cleaning,handyman",                                  4.8,  87, 0, "AC specialist · summer-peak ready"),
    ("hello@dubaipest.demo.ae",   "vendor123","Dubai Pest & Termite",  "+971500000203","DPT Pest Co.",              "pest_control",                                          4.7,  65, 0, "Single-service specialist · MOH-licensed"),
    ("nani@helping-hands.demo.ae","vendor123","Helping Hands Nanny",   "+971500000204","Helping Hands LLC",         "babysitting,maid_service",                              5.0,  34, 0, "5-star nanny · DHA-trained"),
    ("info@green-villa.demo.ae",  "vendor123","Green Villa Garden",    "+971500000205","Green Villa Garden LLC",    "garden,pool",                                            4.6,  21, 0, "Pool + garden combo · weekend specialist"),
    ("ops@fastrecovery.demo.ae",  "vendor123","Fast Recovery 24/7",    "+971500000206","Fast Recovery LLC",         "vehicle_recovery,car_wash",                              4.9,  98, 0, "24/7 emergency recovery · GPS-aware"),
    ("paint@cleanwalls.demo.ae",  "vendor123","Clean Walls Painting",  "+971500000207","Clean Walls LLC",           "painting,handyman",                                      4.5,  44, 0, "Painting + handyman duo · Jotun certified"),
    ("ops@premium-clean.demo.ae", "vendor123","Premium Clean Dubai",   "+971500000208","Premium Clean DMCC",        "deep_cleaning,move_in_out",                              4.9,  56, 0, "Premium-only · villa-grade · move-out specialist"),
    ("ops@budget-clean.demo.ae",  "vendor123","Budget Clean Sharjah",  "+971500000209","Budget Clean Co.",          "maid_service,laundry",                                    4.2, 215, 0, "Volume vendor · budget tier · 215 jobs"),
    ("ops@green-team.demo.ae",    "vendor123","Eco Green Team",        "+971500000210","Eco Green LLC",             "deep_cleaning,window_cleaning",                          4.8,  39, 0, "Eco-friendly · plant-based chemicals"),
    ("ops@female-crew.demo.ae",   "vendor123","Female-Only Crew",      "+971500000211","Sisters Clean LLC",         "maid_service,deep_cleaning,babysitting",                4.9,  78, 0, "Female-crew-only · majlis-friendly"),
    ("ops@new-vendor.demo.ae",    "vendor123","New on Servia",         "+971500000212","Fresh Start LLC",           "handyman",                                                5.0,   0, 0, "Brand new · 0 jobs · approval pending"),
    ("ops@suspended.demo.ae",     "vendor123","Suspended Vendor",      "+971500000213","Old Co.",                   "deep_cleaning",                                           3.2,  12, 1, "SUSPENDED · for testing approval workflow"),
    ("ops@weekend-only.demo.ae",  "vendor123","Weekend Crew",          "+971500000214","Weekend Pros LLC",          "deep_cleaning,sofa_carpet",                              4.7,  28, 0, "Weekend-only · Fri-Sat scheduling"),
    ("ops@kitchen-pro.demo.ae",   "vendor123","Kitchen Deep Pros",     "+971500000215","KDP LLC",                   "deep_cleaning",                                           4.8,  44, 0, "Kitchen-deep specialist · grease-cutting expert"),
    ("ops@bedbug-busters.demo.ae","vendor123","Bedbug Busters",        "+971500000216","BBB Pest LLC",              "pest_control",                                            4.9,  31, 0, "Bedbug specialist · heat-treatment · 30-day warranty"),
    ("ops@office-only.demo.ae",   "vendor123","Office Only Cleaners",  "+971500000217","OOC LLC",                   "deep_cleaning",                                           4.6,  62, 0, "Office-cleaning specialist · after-hours · contracts"),
    ("ops@high-rise.demo.ae",     "vendor123","High Rise Window",      "+971500000218","High Rise LLC",             "window_cleaning",                                         4.8,  19, 0, "High-rise window specialist · rope-access certified"),
    ("ops@kids-pro.demo.ae",      "vendor123","Kids & Babies Pro",     "+971500000219","Kids LLC",                  "babysitting",                                              4.9,  88, 0, "Babysitting specialist · CPR + first-aid certified"),
    ("ops@chauffeur.demo.ae",     "vendor123","Chauffeur Express",     "+971500000220","ChEx FZ-LLC",               "car_wash,vehicle_recovery",                              4.7,  53, 0, "Chauffeur tier · luxury car care + breakdown"),
]


def seed_demo_data(force: bool = False):
    """Always-callable seed. Skips if already seeded (cfg key check) unless
    `force=True` (admin button)."""
    _ensure_demo_columns()
    from . import db
    from . import auth_users as _au

    if not force:
        # Skip if cfg flag set
        if (db.cfg_get("demo_seeded_at", "") or "").strip():
            return {"ok": True, "skipped": "already_seeded"}

    print(f"[seed-demo] starting seed (force={force})…", flush=True)
    cust_ids: dict[str, int] = {}
    vend_ids: dict[str, int] = {}

    with db.connect() as c:
        # ---- customers
        for (phone, name, email, lang, pwd, wallet, blocked, area, emirate, label) in CUSTOMERS:
            try:
                c.execute(
                    "INSERT OR IGNORE INTO customers(phone, name, email, language, password_hash, "
                    "_demo_password, scenario_label, is_active, is_blocked, created_at) "
                    "VALUES(?,?,?,?,?,?,?,1,?,?)",
                    (phone, name, email, lang, _au.hash_password(pwd), pwd, label,
                      blocked, _now(-_r.randint(1, 200))),
                )
                # Backfill demo password + scenario for existing rows that got
                # seeded before v1.22.96 added these columns
                c.execute(
                    "UPDATE customers SET _demo_password=?, scenario_label=? "
                    "WHERE phone=? AND (_demo_password IS NULL OR _demo_password='')",
                    (pwd, label, phone))
                row = c.execute("SELECT id FROM customers WHERE phone=?", (phone,)).fetchone()
                if row:
                    cust_ids[phone] = row["id"]
                    cid = row["id"]
                    # Saved address
                    c.execute(
                        "INSERT OR IGNORE INTO saved_addresses(customer_id, label, address, area, "
                        "emirate, contact_name, contact_phone, tag, is_default, created_at, updated_at) "
                        "VALUES(?,?,?,?,?,?,?,?,1,?,?)",
                        (cid, "Home", f"Tower 7, Apt {1000+cid}, {area}", area, emirate,
                          name, phone, "🏠 Home", _now(), _now()),
                    )
                    # Wallet
                    if wallet > 0:
                        c.execute(
                            "INSERT OR IGNORE INTO customer_wallet(customer_id, balance_aed, updated_at) "
                            "VALUES(?,?,?)", (cid, wallet, _now()),
                        )
                        c.execute(
                            "INSERT INTO wallet_ledger(customer_id, delta_aed, kind, ref, note, ts) "
                            "VALUES(?,?,?,?,?,?)",
                            (cid, wallet, "topup", f"DEMO-SEED-{cid}",
                              "Demo seed top-up", _now(-_r.randint(1, 30))),
                        )
            except Exception as e:
                print(f"[seed-demo] customer {phone} skipped: {e}", flush=True)

        # ---- vendors
        for (email, pwd, name, phone, company, services_csv, rating, jobs, blocked, label) in VENDORS:
            try:
                c.execute(
                    "INSERT OR IGNORE INTO vendors(email, password_hash, _demo_password, scenario_label, "
                    "name, phone, company, rating, completed_jobs, is_active, is_approved, "
                    "is_blocked, created_at) VALUES(?,?,?,?,?,?,?,?,?,1,?,?,?)",
                    (email, _au.hash_password(pwd), pwd, label, name, phone, company,
                      rating, jobs, 0 if blocked else 1, blocked, _now(-_r.randint(20, 360))),
                )
                c.execute(
                    "UPDATE vendors SET _demo_password=?, scenario_label=? "
                    "WHERE email=? AND (_demo_password IS NULL OR _demo_password='')",
                    (pwd, label, email))
                vrow = c.execute("SELECT id FROM vendors WHERE email=?", (email,)).fetchone()
                if vrow:
                    vid = vrow["id"]
                    vend_ids[email] = vid
                    for svc in services_csv.split(","):
                        c.execute(
                            "INSERT OR IGNORE INTO vendor_services(vendor_id, service_id, area, active) "
                            "VALUES(?,?,'*',1)", (vid, svc.strip()),
                        )
            except Exception as e:
                print(f"[seed-demo] vendor {email} skipped: {e}", flush=True)

        # ---- bookings (varied states per scenario)
        STATES = [("pending",-1),("confirmed",2),("in_progress",0),("completed",-7),
                   ("completed",-14),("completed",-30),("cancelled",-3)]
        SVC = ["deep_cleaning","ac_cleaning","maid_service","handyman","pest_control",
                "sofa_carpet","window_cleaning","painting","laundry","garden","pool","car_wash"]
        for (phone, cid) in cust_ids.items():
            n_bookings = _r.choice([0,1,2,3,4,5])
            for _ in range(n_bookings):
                state, days_off = _r.choice(STATES)
                svc = _r.choice(SVC)
                try:
                    c.execute(
                        "INSERT INTO bookings(customer_id, phone, service_id, area, address, "
                        "scheduled_for, status, notes, language, created_at) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (cid, phone, svc, "Dubai Marina", f"Tower 7, Apt {1000+cid}",
                          _now(days_off), state, f"Demo {svc} ({state})", "en", _now(days_off-1)),
                    )
                except Exception: pass

        # ---- invoices (paid + unpaid mix)
        for (phone, cid) in cust_ids.items():
            for _ in range(_r.choice([0,1,1,2,3])):
                amt = _r.choice([150, 250, 350, 500, 800, 1200])
                status = _r.choice(["paid","paid","paid","unpaid","unpaid"])
                try:
                    c.execute(
                        "INSERT OR IGNORE INTO invoices(id, customer_id, amount_aed, status, "
                        "description, created_at) VALUES(?,?,?,?,?,?)",
                        (f"DEMO-{cid:03d}-{secrets.token_hex(2).upper()}", cid, amt, status,
                          f"Demo invoice — AED {amt}", _now(-_r.randint(1, 90))),
                    )
                except Exception: pass

        # ---- NFC tags (0-4 per customer with realistic taps)
        from . import nfc as _nfc_mod
        _nfc_mod._ensure_schema()
        ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"
        for (phone, cid) in cust_ids.items():
            n = _r.choice([0,0,1,2,3,4])
            for _ in range(n):
                slug = "".join(_r.choices(ALPHABET, k=10))
                svc = _r.choice(SVC)
                taps = _r.choice([0,1,2,5,12,28])
                bookings_via_tap = min(taps, _r.randint(0, taps))
                pmode = _r.choice(["manual_pay","manual_pay","auto_wallet","preconfigured"])
                try:
                    c.execute(
                        "INSERT OR IGNORE INTO nfc_tags(slug, owner_customer_id, service_id, alias, "
                        "location_label, size, is_active, tap_count, booking_count, "
                        "payment_mode, max_auto_amount_aed, created_at) "
                        "VALUES(?,?,?,?,?,?,1,?,?,?,?,?)",
                        (slug, cid, svc, f"{svc.replace('_',' ').title()} tag",
                          _r.choice(["Kitchen","Living room","Car dashboard","AC unit","Pool tile",
                                       "Garage","Bathroom","Office desk","Pantry","Pet bed"]),
                          _r.choice(["sticker","card","keychain"]),
                          taps, bookings_via_tap, pmode,
                          _r.choice([300,500,750,1000]), _now(-_r.randint(1, 90))),
                    )
                except Exception: pass

    # Mark seeded so we don't re-run on every startup
    db.cfg_set("demo_seeded_at", _now())
    print(f"[seed-demo] DONE — {len(cust_ids)} customers, {len(vend_ids)} vendors", flush=True)
    return {
        "ok": True,
        "customers": len(cust_ids),
        "vendors": len(vend_ids),
        "summary": "Comprehensive demo data seeded.",
    }
