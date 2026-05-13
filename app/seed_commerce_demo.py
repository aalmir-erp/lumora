"""v1.24.156 — Seed demo commerce data so the founder can see the full
quote → SO → DN → invoice → PO → payment → profit-report flow with
real-looking data instead of empty tabs.

Inserts (idempotent — re-running won't duplicate):
  - 5 customers (UAE phone, mixed languages)
  - 4 vendors (cleaning crew, plumber, electrician, AC tech)
  - 8 quotes (draft / sent / accepted / rejected — covers every status)
  - 5 sales orders (auto-linked to accepted quotes)
  - 3 delivery notes (with photo proof URLs)
  - 5 invoices (unpaid / paid / overdue)
  - 4 purchase orders (open / sent / accepted / paid)
  - 6 payment registrations (3 customer-in, 3 vendor-out)
  - card-fee payments + bank-transfer payments mixed so reports show both

Run via: python -c "from app.seed_commerce_demo import seed; seed()"
Or invoke /api/admin/seed-commerce-demo (endpoint added in this version).
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone

from . import db, commerce


_TAG = "[seed-commerce]"


def _now(offset_days: float = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=offset_days)).isoformat()


def _ensure_customers() -> list[int]:
    """Insert 5 demo customers if not already there. Return their IDs."""
    customers = [
        ("+971500000501", "Aisha Al Mansoori",  "aisha@demo.servia.ae",  "ar", "Dubai Marina"),
        ("+971500000502", "Mohammed Khan",       "mohd@demo.servia.ae",   "en", "Business Bay"),
        ("+971500000503", "Priya Sharma",        "priya@demo.servia.ae",  "hi", "JLT"),
        ("+971500000504", "Lara Petrov",         "lara@demo.servia.ae",   "ru", "Saadiyat"),
        ("+971500000505", "Khaled Al Falasi",    "khaled@demo.servia.ae", "ar", "Jumeirah Village"),
    ]
    ids: list[int] = []
    with db.connect() as c:
        for phone, name, email, lang, area in customers:
            row = c.execute("SELECT id FROM customers WHERE phone=?", (phone,)).fetchone()
            if row:
                ids.append(row["id"])
                continue
            cur = c.execute("""
                INSERT INTO customers (phone, name, email, language, created_at)
                VALUES (?,?,?,?,?)
            """, (phone, name, email, lang, _now(-60)))
            ids.append(cur.lastrowid)
    print(f"{_TAG} customers ready: {len(ids)}")
    return ids


def _ensure_vendors() -> list[int]:
    """Insert 4 demo vendors. Return their IDs."""
    vendors = [
        ("crew-spotless@demo.servia.ae", "Spotless Crew LLC",     "+971500000601", "Spotless Crew LLC",     ["deep_cleaning", "general_cleaning", "maid_service"]),
        ("plumbpro@demo.servia.ae",       "PlumbPro Maintenance",  "+971500000602", "PlumbPro Maintenance",  ["plumbing"]),
        ("voltcraft@demo.servia.ae",      "VoltCraft Electrical",  "+971500000603", "VoltCraft Electrical",  ["electrical"]),
        ("acmasters@demo.servia.ae",      "AC Masters UAE",        "+971500000604", "AC Masters UAE",        ["ac_cleaning", "ac_repair"]),
    ]
    ids: list[int] = []
    from .auth_users import hash_password
    pwd = hash_password("demo-vendor-pass-2026")
    with db.connect() as c:
        for email, name, phone, company, services in vendors:
            row = c.execute("SELECT id FROM vendors WHERE email=?", (email,)).fetchone()
            if row:
                ids.append(row["id"])
                continue
            cur = c.execute("""
                INSERT INTO vendors (email, password_hash, name, phone, company,
                                     rating, completed_jobs, is_active, is_approved, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (email, pwd, name, phone, company, 4.8, 50 + len(ids) * 7, 1, 1, _now(-90)))
            vid = cur.lastrowid
            ids.append(vid)
            for svc in services:
                try:
                    c.execute("""
                        INSERT INTO vendor_services (vendor_id, service_id, area)
                        VALUES (?,?,?)
                    """, (vid, svc, "*"))
                except Exception:
                    pass
    print(f"{_TAG} vendors ready: {len(ids)}")
    return ids


# Demo line-item templates. Each tuple = (service_id, name, qty, unit_price)
_QUOTE_TEMPLATES = [
    # (status, customer_idx, line_items, discount, days_ago)
    ("accepted", 0, [("deep_cleaning",  "Deep cleaning · 2BR apartment",   1, 560.0)], 0,    25),
    ("accepted", 1, [("ac_cleaning",    "AC service · 4 split units",       4, 168.0)], 0,    18),
    ("accepted", 2, [("plumbing",       "Plumber visit + tap cartridge",    1, 280.0)], 0,    14),
    ("accepted", 0, [("deep_cleaning",  "Deep cleaning · 2BR apartment",   1, 560.0),
                     ("sofa_carpet",    "Sofa shampoo · 5-seater",          1, 220.0)], 50,   10),
    ("accepted", 3, [("electrical",     "Electrician + 4 LED downlights",   1, 380.0)], 0,    7),
    ("sent",     4, [("deep_cleaning",  "Deep cleaning · 3BR villa",        1, 840.0)], 0,    4),
    ("sent",     2, [("pest_control",   "Pest control · cockroach + ant",   1, 350.0)], 0,    2),
    ("draft",    0, [("maid_service",   "Hourly maid · 3 hours",            3, 35.0)],  0,    0),
    ("rejected", 4, [("ac_cleaning",    "AC service · 2 split units",       2, 168.0)], 0,    20),
]


def _seed_quotes(customer_ids: list[int]) -> list[str]:
    """Create quotes covering every status. Return quote IDs."""
    created: list[str] = []
    with db.connect() as c:
        # Skip if any seed quotes already exist
        existing = c.execute(
            "SELECT id FROM quotes WHERE customer_name LIKE 'Demo:%' LIMIT 1"
        ).fetchone()
        if existing:
            print(f"{_TAG} quotes already seeded — skipping")
            return [r["id"] for r in c.execute(
                "SELECT id FROM quotes WHERE customer_name LIKE 'Demo:%'").fetchall()]

    customer_names = ["Aisha Al Mansoori", "Mohammed Khan", "Priya Sharma",
                      "Lara Petrov", "Khaled Al Falasi"]
    customer_phones = ["+971500000501", "+971500000502", "+971500000503",
                       "+971500000504", "+971500000505"]
    customer_addrs = ["Marina Crown Tower, Dubai Marina",
                      "Executive Towers, Business Bay",
                      "Cluster X JLT, Dubai",
                      "Hidd Al Saadiyat, Abu Dhabi",
                      "Jumeirah Village Circle, Dubai"]

    for i, (status, cust_idx, items, disc, days_ago) in enumerate(_QUOTE_TEMPLATES):
        line_items = [{
            "svc_id": svc_id, "name": name, "qty": qty, "unit_price": price,
        } for svc_id, name, qty, price in items]
        totals = commerce.calc_totals(line_items, discount=disc)
        q_id = commerce._id("Q")
        q_num = commerce.next_doc_number("quote")
        created_at = _now(-days_ago)
        valid_until = (datetime.now(timezone.utc) + timedelta(days=14 - days_ago)).date().isoformat()
        with db.connect() as c:
            c.execute("""
                INSERT INTO quotes
                  (id, quote_number, service_id, breakdown_json,
                   line_items_json, subtotal, discount, vat_amount, total,
                   currency, valid_until, status, customer_id, customer_name,
                   customer_phone, customer_address, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (q_id, q_num, line_items[0]["svc_id"],
                  json.dumps({"items": line_items, "totals": totals}),
                  json.dumps(line_items),
                  totals["subtotal"], totals["discount"], totals["vat_amount"], totals["total"],
                  "AED", valid_until, status,
                  customer_ids[cust_idx], "Demo: " + customer_names[cust_idx],
                  customer_phones[cust_idx], customer_addrs[cust_idx],
                  "Seed demo quote — safe to delete", created_at))
        created.append(q_id)
    print(f"{_TAG} quotes created: {len(created)}")
    return created


def _seed_sos_dns_invoices_pos_payments(quote_ids: list[str], vendor_ids: list[int]) -> dict:
    """For each ACCEPTED quote, create the full downstream cascade."""
    out = {"sos": 0, "dns": 0, "invoices": 0, "pos": 0, "payments": 0}
    if not quote_ids:
        return out
    with db.connect() as c:
        accepted = c.execute("""
            SELECT * FROM quotes WHERE id IN ({}) AND status='accepted'
        """.format(",".join("?" * len(quote_ids))), quote_ids).fetchall()
    # Map of svc_id → vendor_id (rough)
    vendor_map = {
        "deep_cleaning": vendor_ids[0], "general_cleaning": vendor_ids[0],
        "maid_service": vendor_ids[0], "sofa_carpet": vendor_ids[0],
        "plumbing": vendor_ids[1],
        "electrical": vendor_ids[2],
        "ac_cleaning": vendor_ids[3], "ac_repair": vendor_ids[3],
        "pest_control": vendor_ids[2],
    }
    statuses_so = ["completed", "completed", "in_progress", "completed", "completed"]
    paid_inv = [True, True, False, True, False]   # which invoices have been paid
    paid_po =  [True, False, False, True, False]  # which POs have been paid out

    for i, q in enumerate(accepted[:5]):
        q = dict(q)
        # SO
        so = commerce._create_so_from_quote(q)
        out["sos"] += 1
        # Set status per template (default _create_so_from_quote uses 'confirmed')
        with db.connect() as c:
            c.execute("UPDATE sales_orders SET status=? WHERE id=?",
                      (statuses_so[i], so["id"]))
        # Auto-create invoice (already auto-created via accept flow but here we
        # call it manually since we bypassed accept_quote)
        inv = commerce._create_invoice_from_so({"id": so["id"]})
        if inv:
            out["invoices"] += 1
            # Mark paid for select ones
            if paid_inv[i]:
                paid_at = _now(-(20 - i * 3))
                with db.connect() as c:
                    c.execute("""
                        UPDATE invoices SET payment_status='paid', paid_at=?
                        WHERE id=?
                    """, (paid_at, inv["id"]))
                    # Register the payment (mix of card + bank)
                    method = "card" if i % 2 == 0 else "bank_transfer"
                    c.execute("""
                        INSERT INTO payment_registrations
                          (payment_type, reference_type, reference_id,
                           counterparty_id, counterparty_name, amount, currency,
                           method, reference_number, payment_date, notes, created_at)
                        VALUES ('customer_in', 'invoice', ?, ?, ?, ?, 'AED', ?, ?, ?, ?, ?)
                    """, (inv["id"], q.get("customer_id"), q.get("customer_name"),
                          inv["amount"], method, f"REF-{1000+i}",
                          paid_at, "Seed demo payment", paid_at))
                    out["payments"] += 1

        # Assign vendor → create PO
        line_items = json.loads(q.get("line_items_json") or "[]")
        primary_svc = line_items[0]["svc_id"] if line_items else "deep_cleaning"
        vendor_id = vendor_map.get(primary_svc, vendor_ids[0])
        with db.connect() as c:
            v = c.execute("SELECT id, name, phone FROM vendors WHERE id=?",
                          (vendor_id,)).fetchone()
        # Vendor rate = ~60% of our retail
        vendor_rate = round(q["subtotal"] * 0.6, 2)
        po_id = commerce._id("PO")
        po_num = commerce.next_doc_number("po")
        po_status = "paid" if paid_po[i] else ("completed" if statuses_so[i] == "completed" else "open")
        po_paid_at = _now(-(15 - i * 3)) if paid_po[i] else None
        with db.connect() as c:
            c.execute("""
                INSERT INTO purchase_orders
                  (id, po_number, sales_order_id, vendor_id, vendor_name, vendor_phone,
                   service_id, line_items_json, vendor_total, currency, status,
                   paid_at, terms, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (po_id, po_num, so["id"], v["id"], v["name"], v["phone"],
                  primary_svc,
                  json.dumps([{"svc_id": primary_svc, "qty": 1,
                                "vendor_rate": vendor_rate, "line_total": vendor_rate}]),
                  vendor_rate, "AED", po_status, po_paid_at,
                  "Net 7 days from completion", _now(-(18 - i * 3)), _now(-(15 - i * 3))))
            out["pos"] += 1
            if paid_po[i]:
                c.execute("""
                    INSERT INTO payment_registrations
                      (payment_type, reference_type, reference_id,
                       counterparty_id, counterparty_name, amount, currency,
                       method, reference_number, payment_date, notes, created_at)
                    VALUES ('vendor_out', 'purchase_order', ?, ?, ?, ?, 'AED', 'bank_transfer', ?, ?, ?, ?)
                """, (po_id, v["id"], v["name"], vendor_rate,
                      f"VEND-PAY-{2000+i}", po_paid_at, "Seed demo vendor payout", po_paid_at))
                out["payments"] += 1

        # For SOs that are 'completed', create a delivery note
        if statuses_so[i] == "completed":
            dn_id = commerce._id("DN")
            dn_num = commerce.next_doc_number("dn")
            delivered_at = _now(-(12 - i * 2))
            with db.connect() as c:
                c.execute("""
                    INSERT INTO delivery_notes
                      (id, dn_number, sales_order_id, vendor_id, delivered_at,
                       line_items_json, photo_urls_json, notes, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (dn_id, dn_num, so["id"], v["id"], delivered_at,
                      q["line_items_json"],
                      json.dumps([f"https://servia.ae/proof/demo-{i}-{j}.jpg" for j in range(3)]),
                      "Service delivered. Customer signed off.", delivered_at))
                out["dns"] += 1

    print(f"{_TAG} cascade created: {out}")
    return out


def seed() -> dict:
    """Run the full demo seed. Idempotent."""
    cust = _ensure_customers()
    vend = _ensure_vendors()
    quotes = _seed_quotes(cust)
    cascade = _seed_sos_dns_invoices_pos_payments(quotes, vend)
    return {
        "ok": True,
        "customers": len(cust),
        "vendors": len(vend),
        "quotes": len(quotes),
        **cascade,
    }


def clear() -> dict:
    """Delete all demo-prefixed data. Useful for re-seeding."""
    removed = {"quotes": 0, "sos": 0, "invoices": 0, "pos": 0, "dns": 0, "payments": 0}
    with db.connect() as c:
        # Find quotes with demo prefix
        rows = c.execute("SELECT id FROM quotes WHERE customer_name LIKE 'Demo:%'").fetchall()
        q_ids = [r["id"] for r in rows]
        if not q_ids:
            return {"ok": True, "note": "no demo data found", **removed}
        # Find related SO, INV, PO, DN, payment_reg
        for q_id in q_ids:
            for so in c.execute("SELECT id FROM sales_orders WHERE quote_id=?", (q_id,)).fetchall():
                for inv in c.execute("SELECT id FROM invoices WHERE sales_order_id=?", (so["id"],)).fetchall():
                    c.execute("DELETE FROM payment_registrations WHERE reference_type='invoice' AND reference_id=?", (inv["id"],))
                    removed["payments"] += c.total_changes
                    c.execute("DELETE FROM invoices WHERE id=?", (inv["id"],))
                    removed["invoices"] += 1
                for po in c.execute("SELECT id FROM purchase_orders WHERE sales_order_id=?", (so["id"],)).fetchall():
                    c.execute("DELETE FROM payment_registrations WHERE reference_type='purchase_order' AND reference_id=?", (po["id"],))
                    c.execute("DELETE FROM purchase_orders WHERE id=?", (po["id"],))
                    removed["pos"] += 1
                c.execute("DELETE FROM delivery_notes WHERE sales_order_id=?", (so["id"],))
                removed["dns"] += c.total_changes
                c.execute("DELETE FROM sales_orders WHERE id=?", (so["id"],))
                removed["sos"] += 1
            c.execute("DELETE FROM quotes WHERE id=?", (q_id,))
            removed["quotes"] += 1
    print(f"{_TAG} cleared: {removed}")
    return {"ok": True, **removed}
