"""Tools the LLM can call. Persistent (SQLite-backed) and idempotent.

Tools:
  get_quote, check_coverage, list_slots, create_booking, lookup_booking,
  list_my_bookings, create_quote, create_invoice, sign_quote,
  update_booking_status, handoff_to_human, send_whatsapp
"""
from __future__ import annotations

def _wa() -> str:
    """v1.24.147 — current WhatsApp number from admin brand_contact config."""
    try:
        from .brand_contact import get_contact_whatsapp, get_contact_phone
        return get_contact_whatsapp() or get_contact_phone() or "see /contact"
    except Exception:
        return "see /contact"


import datetime as _dt
import json
import secrets
from typing import Any

from . import db, kb, quotes
from .config import get_settings


def _id(prefix: str = "LM") -> str:
    return f"{prefix}-" + secrets.token_hex(3).upper()


def _now() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


# ---------------------------------------------------------------------------
# get_quote — pure compute, no DB write. Persist via create_quote.
# ---------------------------------------------------------------------------
def get_quote(service_id: str, bedrooms: int | None = None,
              hours: int | None = None, units: int | None = None,
              area: str | None = None, first_time: bool = False,
              recurring: str | None = None,
              addons: list[str] | str | None = None) -> dict:
    # Defensive: accept comma-separated string from naive callers
    if isinstance(addons, str):
        addons = [a.strip() for a in addons.split(",") if a.strip()]
    p = kb.pricing()
    rules = p["rules"]
    if service_id not in rules:
        return {"ok": False, "error": f"Unknown service_id '{service_id}'. Valid: {list(rules)}"}

    rule = rules[service_id]
    breakdown: list[dict[str, Any]] = []
    subtotal = 0.0

    if "base_per_bedroom" in rule:
        if not bedrooms or bedrooms < 1:
            return {"ok": False, "error": "bedrooms is required for this service (1-7)."}
        amt = max(rule["base_per_bedroom"] * bedrooms, rule.get("min_charge", 0))
        breakdown.append({"label": f"{bedrooms}-bedroom base", "amount": amt})
        subtotal += amt

    if "hourly_rate" in rule:
        hrs = max(hours or rule.get("min_hours", 1), rule.get("min_hours", 1))
        amt = rule["hourly_rate"] * hrs
        breakdown.append({"label": f"{hrs} hours @ {rule['hourly_rate']}/hr", "amount": amt})
        subtotal += amt
        if rule.get("supplies_addon"):
            breakdown.append({"label": "Supplies (optional)", "amount": rule["supplies_addon"]})
            subtotal += rule["supplies_addon"]

    if "per_split_unit" in rule:
        n = max(units or rule.get("min_units", 1), rule.get("min_units", 1))
        amt = rule["per_split_unit"] * n
        breakdown.append({"label": f"{n} AC unit(s)", "amount": amt})
        subtotal += amt

    if "per_seat" in rule:
        n = units or 1
        amt = rule["per_seat"] * n
        breakdown.append({"label": f"{n} seat(s)", "amount": amt})
        subtotal += amt

    if "base_flat" in rule:
        amt = rule["base_flat"]
        breakdown.append({"label": "Base service", "amount": amt})
        subtotal += amt

    if "per_piece" in rule:
        n = units or 10
        amt = rule["per_piece"] * n
        breakdown.append({"label": f"{n} pieces @ {rule['per_piece']}/piece", "amount": amt})
        subtotal += amt

    if area and area.lower() in ("abu dhabi", "abu_dhabi"):
        s = p["surcharges"]["abu_dhabi"]
        breakdown.append({"label": "Abu Dhabi travel", "amount": s})
        subtotal += s

    # Addons (id list mapped against services.json addons[])
    if addons:
        svc_def = next((x for x in kb.services()["services"] if x["id"] == service_id), None)
        addon_map = {a["id"]: a for a in (svc_def.get("addons") if svc_def else [])}
        for aid in addons:
            a = addon_map.get(aid)
            if a:
                breakdown.append({"label": f"+ {a['name']}", "amount": a["price"]})
                subtotal += a["price"]

    discount = 0.0
    if first_time and not recurring:
        d = p["discounts"]["first_time"]
        discount = min(subtotal * d["pct"] / 100, d["max_aed"])
        breakdown.append({"label": f"First-time discount ({d['code']})",
                          "amount": -round(discount, 2)})
    elif recurring == "weekly":
        discount = subtotal * p["discounts"]["weekly_recurring"]["pct"] / 100
        breakdown.append({"label": "Weekly recurring discount", "amount": -round(discount, 2)})
    elif recurring == "biweekly":
        discount = subtotal * p["discounts"]["biweekly_recurring"]["pct"] / 100
        breakdown.append({"label": "Bi-weekly recurring discount", "amount": -round(discount, 2)})

    total = max(round(subtotal - discount, 2), 0)
    return {
        "ok": True, "currency": p["currency"], "service_id": service_id,
        "subtotal": round(subtotal, 2), "discount": round(discount, 2),
        "total": total, "vat_included": True, "breakdown": breakdown,
        "note": "Indicative. Final price confirmed at booking after site assessment.",
    }


# ---------------------------------------------------------------------------
def check_coverage(area: str) -> dict:
    a = area.strip().lower()
    served = [x.lower() for x in kb.services()["areas_served"]]
    covered = any(a in entry or entry.split(" ")[0] in a for entry in served)
    surcharge = kb.pricing()["surcharges"].get("abu_dhabi", 0) if "abu" in a else 0
    return {"area": area, "covered": covered, "surcharge_aed": surcharge}


# ---------------------------------------------------------------------------
def list_slots(target_date: str, service_id: str = "deep_cleaning") -> dict:
    try:
        d = _dt.datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        return {"ok": False, "error": "target_date must be YYYY-MM-DD"}
    if d < _dt.date.today():
        return {"ok": False, "error": "Date is in the past."}
    weekday = d.weekday()
    base = ["09:00", "11:00", "13:00", "15:00"] if weekday == 4 else \
           ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00"]
    seed = sum(d.timetuple()[:3])
    available = [t for i, t in enumerate(base) if (seed + i) % 3 != 0]
    return {"ok": True, "date": target_date, "service_id": service_id, "slots": available}


# ---------------------------------------------------------------------------
def create_booking(service_id: str, target_date: str, time_slot: str,
                   customer_name: str, phone: str, address: str,
                   bedrooms: int | None = None, hours: int | None = None,
                   units: int | None = None, notes: str | None = None,
                   language: str = "en", source: str = "web",
                   session_id: str | None = None) -> dict:
    if service_id not in kb.pricing()["rules"]:
        return {"ok": False, "error": f"Unknown service_id '{service_id}'."}
    bid = _id("LM")
    quote = get_quote(service_id, bedrooms=bedrooms, hours=hours, units=units)
    total = quote.get("total")
    with db.connect() as c:
        c.execute(
            "INSERT INTO bookings(id, service_id, target_date, time_slot, customer_name, phone, "
            "address, bedrooms, hours, units, notes, status, estimated_total, currency, "
            "language, source, session_id, created_at, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (bid, service_id, target_date, time_slot, customer_name, phone, address,
             bedrooms, hours, units, notes, "confirmed", total, "AED",
             language, source, session_id, _now(), _now()),
        )
    db.log_event("booking", bid, "created", actor=source, details={"phone": phone})
    try:
        from . import admin_alerts as _aa
        _aa.notify_admin(
            f"🛎 New booking *{bid}*\n"
            f"Service: {service_id}\nCustomer: {customer_name} ({phone})\n"
            f"Slot: {target_date} {time_slot}\nAddress: {address[:120]}\n"
            f"Total: AED {total}",
            kind="new_booking", urgency="normal",
            meta={"booking_id": bid, "service_id": service_id, "total": total})
    except Exception: pass

    # Auto-create a sent quote linked to the booking.
    inv_payment_url = None
    if quote.get("ok"):
        q = quotes.create_quote_record(
            booking_id=bid, service_id=service_id, breakdown=quote["breakdown"],
            subtotal=quote["subtotal"], discount=quote["discount"], total=quote["total"])
        # Auto-issue invoice + payment link so customer pays NOW (advance-payment policy)
        try:
            inv = quotes.create_invoice(quote_id=q["quote_id"], booking_id=bid,
                                        amount=total, currency="AED")
            inv_payment_url = inv.get("payment_url")
            # Move booking to pending_payment until webhook marks paid
            with db.connect() as c:
                c.execute("UPDATE bookings SET status='pending_payment' WHERE id=?", (bid,))
        except Exception as e:  # noqa: BLE001
            db.log_event("booking", bid, "invoice_create_failed", details={"err": str(e)})

    booking = _booking_dict(bid)
    if inv_payment_url:
        booking["payment_url"] = inv_payment_url
    return {"ok": True, "booking": booking, "track_url": f"/account.html?b={bid}",
            "payment_url": inv_payment_url,
            "payment_required_message": (
                "✅ Booking received. Please pay AED " + str(total) +
                " to confirm your slot: " + (inv_payment_url or "(payment link pending)")
            )}


def prepare_checkout(service_id: str, customer_name: str, phone: str, address: str,
                     target_date: str, time_slot: str,
                     bedrooms: int | None = None, hours: int | None = None,
                     units: int | None = None, materials_needed: bool | None = None,
                     cleaning_type: str | None = None,
                     customer_email: str | None = None, area: str | None = None,
                     notes: str | None = None, session_id: str | None = None) -> dict:
    """v1.24.142 — RECOMMENDED tool when customer is ready to book.

    Creates a DRAFT quote (NOT a booking yet) and returns a checkout_url that
    the customer opens to review the price + pay. This replaces calling
    create_booking directly — calling create_booking without taking the
    customer through /checkout means they never see a quote, never agree
    to a price, and never pay. Use prepare_checkout for every booking
    intent EXCEPT the legacy /book.html form submissions.

    Service-specific intake parameters that the bot MUST collect BEFORE
    calling this tool:
      - bedrooms (for deep/general cleaning, maid service)
      - hours (for hourly maid, handyman, babysitter, chauffeur)
      - units (for AC cleaning, fridge/laptop/mobile repair)
      - materials_needed (for maid/cleaning — yes/no)
      - cleaning_type (for cleaning — home/clothes/windows/etc)
      - area (the emirate or neighbourhood for routing)
    """
    from . import checkout_central
    from pydantic import BaseModel
    body = checkout_central.CheckoutInitBody(
        service_id=service_id,
        customer_name=customer_name,
        customer_phone=phone,
        customer_address=address,
        customer_email=customer_email,
        target_date=target_date,
        time_slot=time_slot,
        bedrooms=bedrooms, hours=hours, units=units,
        materials_needed=materials_needed,
        cleaning_type=cleaning_type,
        area=area,
        notes=notes,
        session_id=session_id,
    )
    try:
        out = checkout_central.checkout_init(body)
        # v1.24.229 — Return BOTH a 'pay now' shortcut URL and the full
        # review URL so the bot can offer two CTAs (the founder asked
        # for the sales.mir.ae UX: two buttons in the reply, one
        # direct-to-payment, one for review-first).
        review_url = f"https://servia.ae{out['checkout_url']}"
        pay_now_url = f"https://servia.ae/pay-now/{out['quote_id']}"
        return {
            "ok": True,
            "quote_id": out["quote_id"],
            "quote_number": out["quote_number"],
            "subtotal": out["subtotal"],
            "vat_amount": out["vat_amount"],
            "total": out["total"],
            "checkout_url": out["checkout_url"],
            "pay_now_url": pay_now_url,
            "review_url": review_url,
            "customer_message": (
                f"✅ Your quote *{out['quote_number']}* is ready:\n"
                f"• Subtotal: AED {out['subtotal']:.2f}\n"
                f"• UAE VAT 5%: AED {out['vat_amount']:.2f}\n"
                f"• Total: AED {out['total']:.2f}\n\n"
                f"💳 Pay now: {pay_now_url}\n"
                f"📋 Review details first: {review_url}\n\n"
                f"Your slot locks the moment payment clears (usually 30 sec)."
            ),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _booking_dict(bid: str) -> dict | None:
    with db.connect() as c:
        r = c.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone()
    return db.row_to_dict(r)


# ---------------------------------------------------------------------------
def repeat_last_booking(phone: str, target_date: str | None = None,
                         time_slot: str | None = None) -> dict:
    """Re-creates the customer's most recent booking with a fresh date/time
    so they can rebook with one tap. If date/slot omitted, uses tomorrow 10:00."""
    import datetime as _dt
    with db.connect() as c:
        r = c.execute(
            "SELECT * FROM bookings WHERE phone=? ORDER BY id DESC LIMIT 1",
            (phone,)).fetchone()
    if not r:
        return {"ok": False, "error": "No previous bookings found for this phone."}
    last = db.row_to_dict(r)
    if not target_date:
        target_date = (_dt.date.today() + _dt.timedelta(days=1)).isoformat()
    if not time_slot:
        time_slot = "10:00"
    return create_booking(
        service_id=last.get("service_id"),
        target_date=target_date, time_slot=time_slot,
        customer_name=last.get("customer_name") or "Customer",
        phone=phone, address=last.get("address") or "",
        bedrooms=last.get("bedrooms"), hours=last.get("hours"),
        units=last.get("units"), notes=last.get("notes"),
        language=last.get("language", "en"), source="bot_repeat",
    )


def get_live_status(booking_id: str) -> dict:
    """Customer-friendly tracker view: stage, ETA, next-update.
    Maps internal status → human-readable journey stage."""
    with db.connect() as c:
        r = c.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if not r:
        return {"ok": False, "error": f"No booking with id {booking_id}"}
    b = db.row_to_dict(r)
    status = (b.get("status") or "").lower()
    stage_map = {
        "confirmed":         {"stage": "✅ Confirmed", "next": "Pro will be assigned shortly."},
        "pending_payment":   {"stage": "💳 Payment pending", "next": "Pay to lock the slot."},
        "paid":              {"stage": "💎 Slot locked", "next": "Pro assignment within 30 min."},
        "assigned":          {"stage": "👨‍🔧 Pro assigned", "next": "ETA on WhatsApp 30 min before arrival."},
        "en_route":          {"stage": "🚐 On the way", "next": "Live ETA every 5 min."},
        "in_progress":       {"stage": "✨ Service in progress", "next": "Photo updates as work happens."},
        "completed":         {"stage": "⭐ Done", "next": "Photos + invoice + review request."},
        "cancelled":         {"stage": "❌ Cancelled", "next": "Refund 1-3 business days."},
    }
    info = stage_map.get(status, {"stage": status or "Unknown", "next": ""})
    return {"ok": True, "booking_id": booking_id, "stage": info["stage"],
            "next_update": info["next"], "service": b.get("service_id"),
            "date": b.get("target_date"), "slot": b.get("time_slot")}


def get_my_tier(phone: str) -> dict:
    """Returns the customer's current Ambassador tier + discount % they get
    on every booking. Driven by the referrals + reviews counts."""
    counts = {"refs": 0, "reviews": 0, "videos": 0}
    with db.connect() as c:
        try:
            counts["refs"] = c.execute(
                "SELECT COUNT(*) AS n FROM referrals WHERE referrer_phone=? AND status='converted'",
                (phone,)).fetchone()["n"]
        except Exception: pass
        try:
            counts["reviews"] = c.execute(
                "SELECT COUNT(*) AS n FROM reviews WHERE phone=? AND rating>=4",
                (phone,)).fetchone()["n"]
        except Exception: pass
    refs = counts["refs"]
    if refs >= 11: tier, pct = "💎 Platinum", 20
    elif refs >= 6: tier, pct = "🥇 Gold", 15
    elif refs >= 3: tier, pct = "🥈 Silver", 10
    else:           tier, pct = "🥉 Bronze", 5
    boost = (counts["reviews"] // 2) * 1
    pct = min(20, pct + boost)
    return {"ok": True, "tier": tier, "discount_pct": pct,
            "referrals": refs, "reviews": counts["reviews"],
            "next_step": (
                f"Refer {3 - refs} more friends to reach Silver (10%)." if refs < 3 else
                f"Refer {6 - refs} more friends to reach Gold (15%)." if refs < 6 else
                f"Refer {11 - refs} more friends to reach Platinum (20%)." if refs < 11 else
                "You're at the top tier — keep referring for Creator-Elite perks."
            )}


def list_areas_in_emirate(emirate: str) -> dict:
    """Returns the recognized neighbourhoods we serve in that emirate."""
    AREAS = {
        "dubai": ["Marina","JBR","Downtown","Business Bay","JLT","JVC","Jumeirah","Al Barsha","DIFC","Palm Jumeirah","Arabian Ranches","Mirdif","Al Quoz","Deira","Bur Dubai","Damac Hills","Dubai Hills","Dubai Creek Harbour","Discovery Gardens","International City","Silicon Oasis","Sports City","Motor City","Al Furjan","City Walk","MBR City"],
        "abu-dhabi": ["Khalifa City","Reem Island","Yas Island","Saadiyat","Al Reef","Al Raha","Mohammed Bin Zayed City","Corniche","Mussafah","Al Bateen","Al Mushrif","Khalidiyah"],
        "sharjah": ["Al Khan","Al Majaz","Al Nahda","Al Taawun","Al Qasimia","Al Mamzar Sharjah","Muweilah"],
        "ajman": ["Al Nuaimiya","Al Rashidiya","Al Rumaila","Ajman Corniche"],
        "ras-al-khaimah": ["RAK Old Town","Al Hamra","Mina Al Arab","Al Marjan Island"],
        "umm-al-quwain": ["UAQ Marina","Al Salamah","Al Aahad"],
        "fujairah": ["Fujairah City","Dibba","Al Faseel"],
    }
    em = emirate.lower().replace(" ", "-")
    return {"ok": True, "emirate": em.replace("-", " ").title(),
            "areas": AREAS.get(em, []),
            "count": len(AREAS.get(em, []))}


def lookup_booking(booking_id: str) -> dict:
    rec = _booking_dict(booking_id.strip().upper())
    if not rec:
        return {"ok": False, "error": "Booking not found."}
    rec.update(quotes.list_for_booking(rec["id"]))
    return {"ok": True, "booking": rec}


def list_my_bookings(phone: str) -> dict:
    """Customer portal: bookings by phone."""
    phone = phone.strip()
    with db.connect() as c:
        rows = c.execute(
            "SELECT * FROM bookings WHERE phone=? ORDER BY created_at DESC LIMIT 20",
            (phone,)).fetchall()
    out = db.rows_to_dicts(rows)
    for b in out:
        b.update(quotes.list_for_booking(b["id"]))
    return {"ok": True, "phone": phone, "count": len(out), "bookings": out}


# ---------------------------------------------------------------------------
def create_quote(service_id: str, bedrooms: int | None = None,
                 hours: int | None = None, units: int | None = None,
                 area: str | None = None, first_time: bool = False,
                 booking_id: str | None = None) -> dict:
    q = get_quote(service_id, bedrooms=bedrooms, hours=hours, units=units,
                  area=area, first_time=first_time)
    if not q.get("ok"):
        return q
    rec = quotes.create_quote_record(
        booking_id=booking_id, service_id=service_id, breakdown=q["breakdown"],
        subtotal=q["subtotal"], discount=q["discount"], total=q["total"])
    return {"ok": True, "quote": rec, "summary": q}


def create_invoice_for_booking(booking_id: str) -> dict:
    rec = _booking_dict(booking_id)
    if not rec:
        return {"ok": False, "error": "Booking not found."}
    inv = quotes.create_invoice(
        booking_id=booking_id, quote_id=None,
        amount=rec["estimated_total"] or 0, currency=rec["currency"] or "AED")
    return {"ok": True, "invoice": inv}


def sign_quote_tool(quote_id: str, signature_data_url: str) -> dict:
    return quotes.sign_quote(quote_id, signature_data_url)


def update_booking_status(booking_id: str, status: str, actor: str = "agent") -> dict:
    valid = {"pending", "confirmed", "in_progress", "completed", "cancelled", "rescheduled"}
    if status not in valid:
        return {"ok": False, "error": f"status must be one of {valid}"}
    with db.connect() as c:
        c.execute("UPDATE bookings SET status=?, updated_at=? WHERE id=?",
                  (status, _now(), booking_id))
    db.log_event("booking", booking_id, f"status:{status}", actor=actor)
    return {"ok": True, "booking_id": booking_id, "status": status}


# ---------------------------------------------------------------------------
def create_multi_quote(services: list, customer_name: str, phone: str,
                       address: str, target_date: str, time_slot: str,
                       notes: str | None = None,
                       session_id: str | None = None,
                       revise_of: str | None = None) -> dict:
    """Bundle multiple services into a single Quote + Invoice + signing/pay
    links. Each service is computed via get_quote then aggregated.

    services is a list of dicts: [{service_id: 'deep_cleaning', bedrooms: 1},
                                  {service_id: 'pest_control'}, ...]

    Returns:
      quote_id, signing_url, pay_url, items (list of {service_id, label,
      detail, price}), subtotal, vat, total, fallback_pay_contact.
    """
    from . import quotes as _q, kb as _kb
    s = get_settings()
    items = []
    subtotal = 0.0
    # v1.24.71 — when sizing fields are absent (e.g. auto-quote from chat
    # post-processor), fall back to the service's `starting_price` from
    # services.json so we never persist a 0 AED quote.
    try:
        from . import kb as _kb_fallback
        _starting = {sv.get("id"): float(sv.get("starting_price") or 0)
                     for sv in _kb_fallback.services().get("services", [])
                     if sv.get("id")}
    except Exception:
        _starting = {}
    for svc in services or []:
        sid = svc.get("service_id") or svc.get("id")
        if not sid: continue
        # Compute price for this line
        try:
            line_q = get_quote(service_id=sid,
                               bedrooms=svc.get("bedrooms"),
                               hours=svc.get("hours"),
                               sqm=svc.get("sqm") or svc.get("size_sqm"),
                               area=None, addons=svc.get("addons") or [])
            line_price = float(line_q.get("subtotal_aed") or line_q.get("total_aed") or 0)
        except Exception:
            line_price = 0.0
        if line_price <= 0:
            line_price = _starting.get(sid, 0.0)
        # Pretty detail line
        detail_bits = []
        if svc.get("bedrooms"): detail_bits.append(f"{svc['bedrooms']} BR")
        if svc.get("hours"):    detail_bits.append(f"{svc['hours']} hr")
        if svc.get("sqm") or svc.get("size_sqm"):
            detail_bits.append(f"{svc.get('sqm') or svc['size_sqm']} sqm")
        if svc.get("addons"): detail_bits.append("+" + ", ".join(svc["addons"]))
        detail = " · ".join(detail_bits) or "standard"
        # Service label from KB
        label = sid.replace("_"," ").title()
        try:
            for s_ in _kb.services().get("services", []):
                if s_.get("id") == sid:
                    label = s_.get("name") or label
                    break
        except Exception: pass
        items.append({"service_id": sid, "label": label,
                      "detail": detail, "price_aed": round(line_price, 2),
                      "special_instructions": (svc.get("special_instructions") or "").strip()})
        subtotal += line_price

    vat_pct = s.brand().get("vat_pct", 5)
    vat = round(subtotal * vat_pct / 100, 2)
    total = round(subtotal + vat, 2)

    # Persist a single quote record with items_json for the customer signing page
    from . import db as _db, quotes as _q
    import uuid as _u, json as _json
    # v1.24.82 — quote versioning. If `revise_of=Q-BASE` is supplied,
    # derive the new quote_id by extending the base with -1, -2, …
    # (or extending an existing -N to -N+1). Customer can track
    # revisions to the same booking via a stable "Q-BASE" prefix.
    # v1.24.82 — three-state change policy:
    #   PRE-SIGN  → MODIFY IN PLACE (same quote_id, no version bump)
    #   POST-SIGN, PRE-PAY → REVISE (new id with -N suffix, parent stays)
    #   POST-PAY  → REJECT with handoff_to_human ("contact specialist")
    quote_id = None
    modify_in_place = False
    if revise_of:
        base = revise_of.strip().upper()
        import re as _re
        with _db.connect() as c:
            cur = c.execute(
                "SELECT quote_id, signed_at, paid_at FROM multi_quotes WHERE quote_id=?",
                (base,)).fetchone()
        if not cur:
            return {"ok": False,
                    "error": f"Quote {revise_of} not found.",
                    "action": "ask_for_quote_id"}
        # POST-PAY → can't self-serve
        if cur["paid_at"]:
            return {"ok": False,
                    "error": ("This quote is already paid. Changes after "
                              "payment require contacting a specialist."),
                    "action": "handoff_to_human",
                    "quote_id": base,
                    "contact": "WhatsApp " + _wa()}
        # POST-SIGN → version bump
        if cur["signed_at"]:
            mm = _re.match(r"^(Q-[A-Z0-9]+?)(?:-(\d+))?$", base)
            true_base = mm.group(1) if mm else base
            with _db.connect() as c:
                rows = c.execute(
                    "SELECT quote_id FROM multi_quotes "
                    "WHERE quote_id = ? OR quote_id LIKE ?",
                    (true_base, f"{true_base}-%"),
                ).fetchall()
            versions = []
            for r in rows:
                qid = r["quote_id"]
                if qid == true_base:
                    versions.append(0)
                else:
                    sm = _re.match(rf"^{true_base}-(\d+)$", qid)
                    if sm: versions.append(int(sm.group(1)))
            next_v = (max(versions) + 1) if versions else 1
            quote_id = f"{true_base}-{next_v}"
        else:
            # PRE-SIGN → modify in place
            modify_in_place = True
            quote_id = base
    if not quote_id:
        quote_id = "Q-" + _u.uuid4().hex[:6].upper()
    invoice_id = "INV-" + _u.uuid4().hex[:6].upper()
    with _db.connect() as c:
        try:
            c.execute("""CREATE TABLE IF NOT EXISTS multi_quotes (
                quote_id TEXT PRIMARY KEY,
                items_json TEXT,
                subtotal_aed REAL,
                vat_aed REAL,
                total_aed REAL,
                customer_name TEXT,
                phone TEXT,
                address TEXT,
                target_date TEXT,
                time_slot TEXT,
                notes TEXT,
                signed_at TEXT,
                signature_data_url TEXT,
                paid_at TEXT,
                created_at TEXT
            )""")
        except Exception: pass
        if modify_in_place:
            # v1.24.82 — pre-sign edit: same quote_id, refreshed fields
            c.execute(
                "UPDATE multi_quotes SET items_json=?, subtotal_aed=?, "
                "vat_aed=?, total_aed=?, customer_name=?, phone=?, "
                "address=?, target_date=?, time_slot=?, notes=? "
                "WHERE quote_id=?",
                (_json.dumps(items), subtotal, vat, total, customer_name,
                 phone, address, target_date, time_slot,
                 notes or "", quote_id))
        else:
            c.execute(
                "INSERT INTO multi_quotes(quote_id, items_json, subtotal_aed, vat_aed, "
                "total_aed, customer_name, phone, address, target_date, time_slot, "
                "notes, created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (quote_id, _json.dumps(items), subtotal, vat, total, customer_name,
                 phone, address, target_date, time_slot, notes or "", _now()))
    db.log_event(
        "quote", quote_id,
        "multi_quote_modified" if modify_in_place else "multi_quote_created",
        actor="bot",
        details={"phone": phone, "items": len(items), "total": total,
                 "session_id": session_id,
                 "revise_of": revise_of if revise_of else None})
    # v1.24.83 — auto-create or attach customer profile from chat phone
    try:
        from . import customer_profile as _cp
        _cp.ensure_customer(phone, name=customer_name)
    except Exception: pass

    domain = s.brand().get("domain", "servia.ae")
    return {
        "ok": True,
        "quote_id": quote_id,
        "invoice_id": invoice_id,
        "items": items,
        "subtotal_aed": round(subtotal, 2),
        "vat_aed": vat,
        "total_aed": total,
        "currency": "AED",
        "signing_url": f"https://{domain}/q/{quote_id}",
        "pay_url":     f"https://{domain}/p/{quote_id}",
        "fallback_pay_contact": "WhatsApp " + _wa(),
        "scheduled": {"date": target_date, "time": time_slot},
        "delivery": {"name": customer_name, "phone": phone, "address": address},
    }


# ---------------------------------------------------------------------------
def handoff_to_human(reason: str, customer_name: str | None = None,
                     phone: str | None = None, summary: str | None = None,
                     session_id: str | None = None) -> dict:
    s = get_settings()
    if session_id:
        with db.connect() as c:
            c.execute(
                "INSERT OR REPLACE INTO agent_takeovers(session_id, agent_id, started_at) "
                "VALUES(?,?,?)", (session_id, "queued", _now()))
        db.log_event("conversation", session_id, "handoff_requested",
                     actor="bot", details={"reason": reason, "summary": summary})
    try:
        from . import admin_alerts as _aa
        _aa.notify_admin(
            f"🚨 URGENT — bot escalation\n"
            f"Customer: {customer_name or '(unknown)'} {phone or ''}\n"
            f"Reason: {reason}\n"
            f"Summary: {summary or '(none)'}\n"
            f"Session: {session_id or '?'}",
            kind="urgent_handoff", urgency="urgent",
            meta={"session_id": session_id, "phone": phone})
    except Exception: pass
    return {
        "ok": True, "channel": "internal",
        "message": ("A live agent will reach out shortly through this chat. "
                    "If you'd like to leave additional details, you can also fill out "
                    "/contact.html and we'll be in touch within minutes."),
        "context_logged": {"reason": reason, "customer_name": customer_name,
                           "phone": phone, "summary": summary},
    }


def send_whatsapp(phone: str, message: str) -> dict:
    """Push a message via the WhatsApp bridge (Node service). No-op if unconfigured.
    v1.24.143: also logs every outbound message to the unified inbox so admin
    can see what we sent."""
    s = get_settings()
    if not s.WA_BRIDGE_URL:
        result = {"ok": False, "error": "WhatsApp bridge not configured (WA_BRIDGE_URL unset)."}
        try:
            from . import inbox as _ix
            _ix.log_message(direction="out", channel="whatsapp",
                             sender="us", recipient=phone, body=message,
                             status="failed", error="bridge not configured")
        except Exception: pass
        return result
    try:
        import httpx
        r = httpx.post(
            s.WA_BRIDGE_URL.rstrip("/") + "/send",
            headers={"Authorization": f"Bearer {s.WA_BRIDGE_TOKEN}"},
            json={"to": phone, "text": message}, timeout=10,
        )
        r.raise_for_status()
        try:
            from . import inbox as _ix
            _ix.log_message(direction="out", channel="whatsapp",
                             sender="us", recipient=phone, body=message,
                             status="delivered")
        except Exception: pass
        return {"ok": True, "bridge_status": r.json()}
    except Exception as e:  # noqa: BLE001
        try:
            from . import inbox as _ix
            _ix.log_message(direction="out", channel="whatsapp",
                             sender="us", recipient=phone, body=message,
                             status="failed", error=str(e)[:200])
        except Exception: pass
        return {"ok": False, "error": f"Bridge error: {e}"}


# ---------------------------------------------------------------------------
TOOL_SCHEMAS: list[dict] = [
    {"name": "get_quote",
     "description": "Compute an indicative price quote. Use whenever the customer asks 'how much' or wants pricing.",
     "input_schema": {"type": "object", "properties": {
         "service_id": {"type": "string", "description": "deep_cleaning, general_cleaning, maid_service, move_in_out, office_cleaning, post_construction, sofa_carpet, ac_cleaning, disinfection, window_cleaning, pest_control, laundry, babysitting, gardening, handyman, kitchen_deep, villa_deep, car_wash, swimming_pool, marble_polish, curtain_cleaning, smart_home, painting"},
         "bedrooms": {"type": "integer"}, "hours": {"type": "integer"},
         "units": {"type": "integer"}, "area": {"type": "string"},
         "first_time": {"type": "boolean"},
         "recurring": {"type": "string", "enum": ["weekly", "biweekly", "monthly"]},
         "addons": {"type": "array", "items": {"type": "string"},
                    "description": "Addon ids from the service's addons list (e.g. 'oven', 'fridge', 'sofa3'). Look up valid ids in the KB before passing."}},
         "required": ["service_id"]}},
    {"name": "check_coverage",
     "description": "Check whether we cover a given area or emirate.",
     "input_schema": {"type": "object", "properties": {"area": {"type": "string"}}, "required": ["area"]}},
    {"name": "list_slots",
     "description": "List available time slots for a date (YYYY-MM-DD).",
     "input_schema": {"type": "object", "properties": {
         "target_date": {"type": "string"}, "service_id": {"type": "string"}},
         "required": ["target_date"]}},
    {"name": "prepare_checkout",
     "description": ("PREFERRED tool when customer is ready to book a single service. "
                     "Creates a DRAFT quote + returns checkout_url. Customer opens the "
                     "URL to see price + UAE VAT 5% + pay via Stripe/Ziina/bank. "
                     "After payment, booking is auto-confirmed via webhook. NEVER use "
                     "create_booking directly — it bypasses the customer-facing quote "
                     "review + payment step which is mandatory per company policy. "
                     "Returns: {quote_id, quote_number, subtotal, vat_amount, total, "
                     "checkout_url, customer_message — share the customer_message verbatim}."),
     "input_schema": {"type": "object", "properties": {
         "service_id": {"type": "string"}, "target_date": {"type": "string"},
         "time_slot": {"type": "string"}, "customer_name": {"type": "string"},
         "phone": {"type": "string"}, "address": {"type": "string"},
         "bedrooms": {"type": "integer", "description": "Cleaning services: bedroom count"},
         "hours": {"type": "integer", "description": "Hourly services: estimated hours"},
         "units": {"type": "integer", "description": "AC/appliance services: unit count"},
         "materials_needed": {"type": "boolean", "description": "Maid/cleaning: cleaning materials needed yes/no"},
         "cleaning_type": {"type": "string", "description": "Cleaning: home/clothes/windows/both"},
         "customer_email": {"type": "string"},
         "area": {"type": "string", "description": "Emirate or neighbourhood for routing"},
         "notes": {"type": "string"}},
         "required": ["service_id", "target_date", "time_slot",
                      "customer_name", "phone", "address"]}},
    {"name": "create_booking",
     "description": "LEGACY — do not use for new customer-facing bookings. Use prepare_checkout instead. Only retained for /book.html form submissions.",
     "input_schema": {"type": "object", "properties": {
         "service_id": {"type": "string"}, "target_date": {"type": "string"},
         "time_slot": {"type": "string"}, "customer_name": {"type": "string"},
         "phone": {"type": "string"}, "address": {"type": "string"},
         "bedrooms": {"type": "integer"}, "hours": {"type": "integer"},
         "units": {"type": "integer"}, "notes": {"type": "string"},
         "language": {"type": "string"}},
         "required": ["service_id", "target_date", "time_slot",
                      "customer_name", "phone", "address"]}},
    {"name": "lookup_booking",
     "description": "Look up a booking by id (e.g. LM-A1B2C3).",
     "input_schema": {"type": "object", "properties": {"booking_id": {"type": "string"}}, "required": ["booking_id"]}},
    {"name": "list_my_bookings",
     "description": "Find all bookings linked to a phone number.",
     "input_schema": {"type": "object", "properties": {"phone": {"type": "string"}}, "required": ["phone"]}},
    {"name": "repeat_last_booking",
     "description": "One-tap re-book of the customer's most recent service. Use when the customer says 'rebook', 'same as last time', 'repeat my last', etc. If date/slot omitted defaults to tomorrow 10:00.",
     "input_schema": {"type": "object", "properties": {
         "phone": {"type": "string"},
         "target_date": {"type": "string"},
         "time_slot": {"type": "string"}},
         "required": ["phone"]}},
    {"name": "get_live_status",
     "description": "Customer-friendly tracker for an in-flight booking — current stage (confirmed / pro assigned / on the way / in progress / done) plus next update.",
     "input_schema": {"type": "object", "properties": {"booking_id": {"type": "string"}}, "required": ["booking_id"]}},
    {"name": "get_my_tier",
     "description": "Returns the customer's current Ambassador tier + discount % on every booking, with next-step suggestions to climb.",
     "input_schema": {"type": "object", "properties": {"phone": {"type": "string"}}, "required": ["phone"]}},
    {"name": "list_areas_in_emirate",
     "description": "Returns the neighbourhoods we serve in a given emirate (dubai/abu-dhabi/sharjah/ajman/ras-al-khaimah/umm-al-quwain/fujairah).",
     "input_schema": {"type": "object", "properties": {"emirate": {"type": "string"}}, "required": ["emirate"]}},
    {"name": "create_invoice_for_booking",
     "description": "Create an invoice + payment link for a confirmed booking.",
     "input_schema": {"type": "object", "properties": {"booking_id": {"type": "string"}}, "required": ["booking_id"]}},
    {"name": "send_whatsapp",
     "description": "Send a WhatsApp message to a phone via the bridge. Use to push booking confirmations or quotes.",
     "input_schema": {"type": "object", "properties": {
         "phone": {"type": "string"}, "message": {"type": "string"}},
         "required": ["phone", "message"]}},
    {"name": "handoff_to_human",
     "description": "Escalate to a human agent. Use when the customer asks for a person, complains, or it's outside scope.",
     "input_schema": {"type": "object", "properties": {
         "reason": {"type": "string"}, "customer_name": {"type": "string"},
         "phone": {"type": "string"}, "summary": {"type": "string"}},
         "required": ["reason"]}},
    {"name": "create_multi_quote",
     "description": ("Bundle 2 or more services into a single Quote with a "
                     "shared scheduled date, address, and customer. Returns "
                     "quote_id, signing_url, pay_url, line items with prices, "
                     "subtotal, VAT and total. ALWAYS use this when the "
                     "customer mentions multiple services in one chat — "
                     "do NOT call create_booking once per service."),
     "input_schema": {"type": "object", "properties": {
         "services": {"type": "array", "items": {"type": "object", "properties": {
             "service_id": {"type": "string", "description": "e.g. deep_cleaning, pest_control"},
             "bedrooms":   {"type": "number"}, "hours": {"type": "number"},
             "sqm":        {"type": "number"},
             "addons":     {"type": "array", "items": {"type": "string"}},
             "special_instructions": {"type": "string", "description": "Per-service instructions from the customer (e.g. 'no chemicals on marble', 'allergy-safe products only'). Renders on the line in the quote + invoice PDF."},
         }, "required": ["service_id"]}},
         "customer_name": {"type": "string"},
         "phone":         {"type": "string"},
         "address":       {"type": "string"},
         "target_date":   {"type": "string", "description": "YYYY-MM-DD"},
         "time_slot":     {"type": "string", "description": "e.g. 08:00 or '8 AM'"},
         "notes":         {"type": "string", "description": "General special instructions for the whole booking (e.g. 'Bring own water', 'Park at gate B', 'Code 1234'). These render on the quote and the printed invoice."},
         "revise_of":     {"type": "string",
                           "description": "If editing/revising an existing quote, pass its quote_id. PRE-SIGN edits update the same quote_id in place. POST-SIGN edits issue Q-XXX-1, -2, … (versioned). POST-PAY changes are blocked — call handoff_to_human instead."}},
         "required": ["services", "customer_name", "phone", "address",
                      "target_date", "time_slot"]}},
]


TOOL_DISPATCH = {
    "get_quote": get_quote, "check_coverage": check_coverage,
    "list_slots": list_slots, "create_booking": create_booking,
    "prepare_checkout": prepare_checkout,   # v1.24.142 PREFERRED
    "lookup_booking": lookup_booking, "list_my_bookings": list_my_bookings,
    "repeat_last_booking": repeat_last_booking,
    "get_live_status": get_live_status,
    "get_my_tier": get_my_tier,
    "list_areas_in_emirate": list_areas_in_emirate,
    "create_invoice_for_booking": create_invoice_for_booking,
    "create_multi_quote": create_multi_quote,
    "send_whatsapp": send_whatsapp, "handoff_to_human": handoff_to_human,
}


def run_tool(name: str, arguments: dict, *, session_id: str | None = None) -> dict:
    fn = TOOL_DISPATCH.get(name)
    if not fn:
        return {"ok": False, "error": f"Unknown tool '{name}'."}
    try:
        # Inject session_id where supported.
        if name in ("create_booking", "handoff_to_human", "create_multi_quote"):
            arguments.setdefault("session_id", session_id)
        return fn(**arguments)
    except TypeError as e:
        return {"ok": False, "error": f"Bad arguments for {name}: {e}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"Tool error: {e}"}
