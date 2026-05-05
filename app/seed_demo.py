"""Seed comprehensive demo data for Servia: customers, vendors, bookings,
invoices, NFC tags, wallet entries — all in various transaction states.

Idempotent: only seeds when ADMIN_SEED_DEMO_DATA=1 AND the demo customers
don't already exist (matched by phone number).

Each demo customer is bound to:
- 1+ saved address with map pin
- 0–4 bookings in different statuses (pending, confirmed, in_progress,
  completed, cancelled)
- 0–2 invoices (paid + unpaid)
- 0–3 NFC tags
- A wallet balance (some empty, some healthy)
"""
from __future__ import annotations

import datetime as _dt
import os
import random as _r
import secrets


def _now(offset_days: int = 0) -> str:
    return (_dt.datetime.utcnow() + _dt.timedelta(days=offset_days)).isoformat() + "Z"


def seed_demo_data():
    if os.getenv("ADMIN_SEED_DEMO_DATA", "0") != "1":
        return
    print("[seed-demo] starting comprehensive seed…", flush=True)
    from . import db
    from . import auth_users as _au

    customers = [
        # (phone, name, email, lang, password, wallet_aed, blocked, address_alias, area, emirate)
        ("+971501110001", "Aisha Al Mansoori",  "aisha@example.ae",   "ar", "demo123",  500.0, 0, "🏠 Home",     "Dubai Marina",        "Dubai"),
        ("+971501110002", "Mohammed Khan",       "mohd@example.ae",     "en", "demo123",  250.0, 0, "🏢 Office",   "Business Bay",        "Dubai"),
        ("+971501110003", "Priya Sharma",        "priya@example.ae",    "hi", "demo123",   75.0, 0, "🏠 Home",     "JLT",                  "Dubai"),
        ("+971501110004", "Lara Petrov",         "lara@example.ae",     "ru", "demo123",    0.0, 0, "🏡 Villa",    "Khalifa City",        "Abu Dhabi"),
        ("+971501110005", "Khalid Rashed",       "khalid@example.ae",   "ar", "demo123", 1500.0, 0, "🏠 Home",     "Al Nahda",             "Sharjah"),
        ("+971501110006", "Mary Dela Cruz",      "mary@example.ae",     "tl", "demo123",   25.0, 0, "🏠 Home",     "Mirdif",               "Dubai"),
        ("+971501110007", "Ahmed Al Hashemi",    "ahmed@example.ae",    "ar", "demo123",  800.0, 0, "🏡 Villa",    "Al Khawaneej",        "Dubai"),
        ("+971501110008", "Sara Williams",       "sara@example.ae",     "en", "demo123",  100.0, 1, "🏢 Office",   "DIFC",                 "Dubai"),  # blocked
        ("+971501110009", "Rajesh Iyer",         "raj@example.ae",      "hi", "demo123",  300.0, 0, "🏠 Home",     "Ajman Corniche",      "Ajman"),
        ("+971501110010", "Fatima Al Zaabi",     "fatima@example.ae",   "ar", "demo123",   50.0, 0, "🏡 Villa",    "Al Reem Island",      "Abu Dhabi"),
    ]
    vendors = [
        # (email, password, name, phone, company, services, rating, jobs)
        ("crew@a1clean.ae",      "demo123", "A1 Clean UAE",          "+971500000201", "A1 Clean LLC",            ["deep_cleaning","maid_service","sofa_carpet","window_cleaning"], 4.9, 142),
        ("crew@servia-ac.ae",    "demo123", "Servia AC Pros",        "+971500000202", "Servia AC FZ-LLC",        ["ac_cleaning","handyman"],                                       4.8,  87),
        ("hello@dubaipest.ae",   "demo123", "Dubai Pest & Termite",  "+971500000203", "DPT Pest Co.",            ["pest_control"],                                                   4.7,  65),
        ("nani@helping-hands.ae","demo123", "Helping Hands Nanny",   "+971500000204", "Helping Hands LLC",       ["babysitting","maid_service"],                                    5.0,  34),
        ("info@green-villa.ae",  "demo123", "Green Villa Garden",    "+971500000205", "Green Villa Garden LLC",  ["garden","pool"],                                                  4.6,  21),
        ("ops@fastrecovery.ae",  "demo123", "Fast Recovery 24/7",    "+971500000206", "Fast Recovery LLC",       ["vehicle_recovery","car_wash"],                                   4.9,  98),
        ("paint@cleanwalls.ae",  "demo123", "Clean Walls Painting",  "+971500000207", "Clean Walls LLC",         ["painting","handyman"],                                          4.5,  44),
    ]

    cust_ids: dict[str, int] = {}
    with db.connect() as c:
        # Customers
        for (phone, name, email, lang, pwd, wallet, blocked, alias, area, emirate) in customers:
            try:
                c.execute(
                    "INSERT OR IGNORE INTO customers(phone, name, email, language, password_hash, "
                    "is_active, is_blocked, created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (phone, name, email, lang, _au.hash_password(pwd), 1, blocked, _now(-_r.randint(1, 90))),
                )
                row = c.execute("SELECT id FROM customers WHERE phone=?", (phone,)).fetchone()
                cid = row["id"] if row else None
                cust_ids[phone] = cid
                if not cid: continue
                # Saved address
                c.execute(
                    "INSERT OR IGNORE INTO saved_addresses(customer_id, label, address, area, "
                    "emirate, contact_name, contact_phone, tag, is_default, created_at, updated_at) "
                    "VALUES(?,?,?,?,?,?,?,?,1,?,?)",
                    (cid, alias.split(" ")[1] if " " in alias else alias,
                      f"Tower 7, Apt {1000+cid}, {area}", area, emirate,
                      name, phone, alias, _now(), _now()),
                )
                # Wallet seed
                if wallet > 0:
                    c.execute(
                        "INSERT OR IGNORE INTO customer_wallet(customer_id, balance_aed, updated_at) "
                        "VALUES(?,?,?)", (cid, wallet, _now()),
                    )
                    c.execute(
                        "INSERT INTO wallet_ledger(customer_id, delta_aed, kind, ref, note, ts) "
                        "VALUES(?,?,?,?,?,?)",
                        (cid, wallet, "topup", f"DEMO-SEED-{cid}",
                          f"Demo seed top-up", _now(-_r.randint(1, 30))),
                    )
            except Exception as e:
                print(f"[seed-demo] customer {phone} error: {e}", flush=True)

        # Vendors
        for (email, pwd, name, phone, company, services, rating, jobs) in vendors:
            try:
                c.execute(
                    "INSERT OR IGNORE INTO vendors(email, password_hash, name, phone, company, "
                    "rating, completed_jobs, is_active, is_approved, created_at) "
                    "VALUES(?,?,?,?,?,?,?,1,1,?)",
                    (email, _au.hash_password(pwd), name, phone, company, rating, jobs, _now(-_r.randint(20, 120))),
                )
                vrow = c.execute("SELECT id FROM vendors WHERE email=?", (email,)).fetchone()
                vid = vrow["id"] if vrow else None
                if vid:
                    for svc in services:
                        c.execute(
                            "INSERT OR IGNORE INTO vendor_services(vendor_id, service_id, area, active) "
                            "VALUES(?,?,'*',1)", (vid, svc),
                        )
            except Exception as e:
                print(f"[seed-demo] vendor {email} error: {e}", flush=True)

        # Bookings in various states
        STATES = [("pending",-1),("confirmed",2),("in_progress",0),("completed",-7),("completed",-14),("cancelled",-3)]
        SVC = ["deep_cleaning","ac_cleaning","maid_service","handyman","pest_control",
                "sofa_carpet","window_cleaning","painting","laundry","garden","pool","car_wash"]
        for (phone, cid) in cust_ids.items():
            if not cid: continue
            n_bookings = _r.choice([0,1,2,3,4])
            for _ in range(n_bookings):
                state, days_off = _r.choice(STATES)
                svc = _r.choice(SVC)
                try:
                    c.execute(
                        "INSERT INTO bookings(customer_id, phone, service_id, area, address, "
                        "scheduled_for, status, notes, language, created_at) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (cid, phone, svc, "Dubai Marina",
                          f"Tower 7, Apt {1000+cid}",
                          _now(days_off), state,
                          f"Demo {svc} booking ({state})",
                          "en", _now(days_off-1)),
                    )
                except Exception as e:
                    print(f"[seed-demo] booking error: {e}", flush=True)

        # Invoices in various payment states
        for (phone, cid) in cust_ids.items():
            if not cid: continue
            for _ in range(_r.choice([0,1,2])):
                amt = _r.choice([150, 250, 350, 500, 800, 1200])
                status = _r.choice(["paid","paid","paid","unpaid","unpaid"])
                try:
                    c.execute(
                        "INSERT OR IGNORE INTO invoices(id, customer_id, amount_aed, "
                        "status, description, created_at) VALUES(?,?,?,?,?,?)",
                        (f"DEMO-{cid:03d}-{secrets.token_hex(2).upper()}", cid, amt,
                          status, f"Demo invoice — AED {amt}",
                          _now(-_r.randint(1, 60))),
                    )
                except Exception as e:
                    print(f"[seed-demo] invoice error: {e}", flush=True)

        # NFC tags — 0-3 per customer with various tap counts
        from . import nfc as _nfc_mod
        _nfc_mod._ensure_schema()
        ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"
        for (phone, cid) in cust_ids.items():
            if not cid: continue
            n = _r.choice([0,0,1,2,3])
            for _ in range(n):
                slug = "".join(_r.choices(ALPHABET, k=10))
                svc = _r.choice(SVC)
                taps = _r.choice([0,1,2,5,12,28])
                bookings_via_tap = min(taps, _r.randint(0, taps))
                try:
                    c.execute(
                        "INSERT OR IGNORE INTO nfc_tags(slug, owner_customer_id, service_id, "
                        "alias, location_label, size, is_active, tap_count, booking_count, "
                        "created_at) VALUES(?,?,?,?,?,?,1,?,?,?)",
                        (slug, cid, svc,
                          f"{svc.replace('_',' ').title()} tag",
                          _r.choice(["Kitchen","Living room","Car dashboard","AC unit","Pool tile","Garage"]),
                          _r.choice(["sticker","card","keychain"]),
                          taps, bookings_via_tap, _now(-_r.randint(1, 60))),
                    )
                except Exception as e:
                    print(f"[seed-demo] nfc tag error: {e}", flush=True)

    print(f"[seed-demo] DONE — {len(cust_ids)} customers, {len(vendors)} vendors, "
          f"plus bookings/invoices/wallet/nfc.", flush=True)
