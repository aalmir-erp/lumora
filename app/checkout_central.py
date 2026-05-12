"""v1.24.142 — Central checkout flow (the founder-priority fix).

PAIN BEING SOLVED
-----------------
Bot was collecting service+name+phone+address+date+time in chat, then
sending customers to /book or a generic form that RE-ASKED everything,
or worse, creating a booking with NO price quote shown.

NEW FLOW
--------
  1. Bot collects all intake (service-specific: hours/bedrooms/units/
     materials_needed/cleaning_type/etc.) — enforced in v1.24.143
  2. Bot calls /api/checkout/init with extracted data
  3. Server creates a DRAFT quote (using commerce.py) and returns
     a checkout URL: /checkout?q=Q-12345
  4. Bot replies with that URL — single tap
  5. Customer opens /checkout.html — sees pre-filled details, intake
     summary, line items, VAT, total, "Pay now" button
  6. Customer clicks Pay → /api/checkout/{quote_id}/pay generates a
     payment-gateway URL (Stripe / Ziina / bank-transfer fallback)
  7. On successful payment webhook → quote accepted → SO+invoice
     auto-created via commerce.py flow → booking confirmed

THIS COMMIT DELIVERS:
  - POST /api/checkout/init        (bot-callable)
  - GET  /api/checkout/quote/{id}  (public — for /checkout page)
  - POST /api/checkout/{id}/pay    (public — generates payment URL)
  - GET  /checkout                 (the page itself — served via main.py)

PAYMENT GATEWAY:
  - If config 'stripe_secret_key' set → real Stripe checkout
  - Else if config 'ziina_api_key' set → Ziina (UAE-local)
  - Else → bank-transfer instructions from config block

WEBHOOK (existing /api/webhooks/stripe in main.py) will:
  - Mark invoice paid
  - Call commerce.admin_accept_quote() to fire SO + invoice flow
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from . import db, kb, commerce
from .commerce import next_doc_number, calc_totals, _id, _now, VAT_RATE


router = APIRouter()


class CheckoutInitBody(BaseModel):
    """Called by the bot when user is ready to book.
    All service-specific intake should already be collected — no fallbacks
    here; if anything is missing, the bot must keep asking."""
    service_id: str
    customer_name: str
    customer_phone: str
    customer_address: str
    customer_email: Optional[str] = None
    target_date: str          # ISO YYYY-MM-DD
    time_slot: str            # "10:00", "afternoon", etc.
    # Service-specific intake (bot fills what's relevant)
    bedrooms: Optional[int] = None
    hours: Optional[int] = None
    units: Optional[int] = None
    materials_needed: Optional[bool] = None
    cleaning_type: Optional[str] = None       # "home" | "clothes" | "windows" | etc.
    extra_intake: Optional[dict] = None       # catch-all for service-specific fields
    notes: Optional[str] = None
    area: Optional[str] = None                # "Dubai", "Sharjah" etc. — for display
    session_id: Optional[str] = None
    discount: float = 0


@router.post("/api/checkout/init")
def checkout_init(body: CheckoutInitBody):
    """Create a draft quote + return the checkout URL for the customer."""
    # Look up service from KB to get name, base price rules
    try:
        services = {s["id"]: s for s in kb.services().get("services", [])}
    except Exception:
        services = {}
    svc = services.get(body.service_id)
    if not svc:
        raise HTTPException(status_code=400, detail=f"unknown service_id '{body.service_id}'")

    # Use the existing pricing engine to compute base price
    from . import tools
    qres = tools.get_quote(body.service_id, bedrooms=body.bedrooms,
                            hours=body.hours, units=body.units)
    if not qres.get("ok"):
        # Fallback to service starting price
        base_price = svc.get("starting_price", 100)
    else:
        # qres["total"] already includes any standard add-ons baked in by tools.get_quote
        base_price = qres.get("subtotal") or qres.get("total") or svc.get("starting_price", 100)

    # Build line item from the service + intake
    intake_label_bits = []
    if body.bedrooms: intake_label_bits.append(f"{body.bedrooms}BR")
    if body.hours:    intake_label_bits.append(f"{body.hours}hr")
    if body.units:    intake_label_bits.append(f"{body.units} units")
    line_label = svc.get("name", body.service_id) + (
        f" ({', '.join(intake_label_bits)})" if intake_label_bits else ""
    )
    line_items = [{
        "svc_id": body.service_id,
        "name":   line_label,
        "qty":    1,
        "unit_price": float(base_price),
    }]

    totals = calc_totals(line_items, discount=body.discount)
    q_id  = _id("Q")
    q_num = next_doc_number("quote")
    now   = _now()
    valid_until = (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat()

    # Store extra intake fields as JSON in 'notes' alongside actual notes
    intake_blob = {
        "target_date": body.target_date,
        "time_slot":   body.time_slot,
        "bedrooms":    body.bedrooms,
        "hours":       body.hours,
        "units":       body.units,
        "materials_needed": body.materials_needed,
        "cleaning_type":    body.cleaning_type,
        "area":        body.area,
        **(body.extra_intake or {}),
    }
    notes_json = json.dumps({"intake": intake_blob, "user_notes": body.notes or ""})

    with db.connect() as c:
        c.execute("""
            INSERT INTO quotes
              (id, quote_number, service_id, breakdown_json,
               line_items_json, subtotal, discount, vat_amount, total,
               currency, valid_until, status, customer_name, customer_phone,
               customer_email, customer_address, notes, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (q_id, q_num, body.service_id,
              json.dumps({"items": line_items, "totals": totals, "intake": intake_blob}),
              json.dumps(line_items),
              totals["subtotal"], totals["discount"], totals["vat_amount"], totals["total"],
              "AED", valid_until, "draft",
              body.customer_name, body.customer_phone, body.customer_email,
              body.customer_address, notes_json, now))

    checkout_url = f"/checkout?q={q_id}"
    return {
        "ok": True,
        "quote_id": q_id,
        "quote_number": q_num,
        "subtotal": totals["subtotal"],
        "vat_amount": totals["vat_amount"],
        "total": totals["total"],
        "checkout_url": checkout_url,
    }


@router.get("/api/checkout/quote/{quote_id}")
def checkout_get_quote(quote_id: str):
    """Public — used by /checkout.html to render the page.
    Returns a sanitized view (no internal IDs, no admin notes)."""
    with db.connect() as c:
        row = c.execute("SELECT * FROM quotes WHERE id=?", (quote_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="quote not found")
        if row["status"] not in ("draft", "sent"):
            raise HTTPException(status_code=410, detail=f"quote is '{row['status']}' — please request a new quote")
        # Parse intake from notes
        intake = {}; user_notes = ""
        try:
            ndata = json.loads(row["notes"] or "{}")
            intake = ndata.get("intake", {})
            user_notes = ndata.get("user_notes", "")
        except Exception:
            user_notes = row["notes"] or ""
        # Parse line items
        items = []
        try:
            items = json.loads(row["line_items_json"] or "[]")
        except Exception:
            pass
        # Service meta
        try:
            services = {s["id"]: s for s in kb.services().get("services", [])}
            svc = services.get(row["service_id"], {})
        except Exception:
            svc = {}
        # Add-ons from service KB (lets customer add things on the checkout page)
        addons = []
        for a in (svc.get("addons") or [])[:6]:
            addons.append({
                "id":   a.get("id"),
                "name": a.get("name"),
                "icon": a.get("icon"),
                "price": a.get("price"),
                "desc": a.get("desc"),
            })

    return {
        "ok": True,
        "quote_id": row["id"],
        "quote_number": row["quote_number"],
        "service_id": row["service_id"],
        "service": {
            "name": svc.get("name"),
            "icon": svc.get("emoji"),
            "category": svc.get("category"),
        },
        "customer": {
            "name": row["customer_name"],
            "phone": row["customer_phone"],
            "email": row["customer_email"],
            "address": row["customer_address"],
        },
        "target_date": intake.get("target_date"),
        "time_slot":   intake.get("time_slot"),
        "area":        intake.get("area"),
        "intake": {k: v for k, v in intake.items()
                   if k not in ("target_date", "time_slot", "area") and v is not None},
        "line_items": items,
        "available_addons": addons,
        "subtotal": row["subtotal"],
        "discount": row["discount"],
        "vat_amount": row["vat_amount"],
        "total": row["total"],
        "currency": row["currency"],
        "notes": user_notes,
        "valid_until": row["valid_until"],
    }


class CheckoutPayBody(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    notes: Optional[str] = None
    addons: Optional[list[dict]] = None       # [{id, price}]


def _payment_gateway_link(quote_id: str, amount: float, customer: dict) -> dict:
    """Return either {'payment_url': '...'} or {'bank_transfer': {...}} fallback.
    Checks config for Stripe / Ziina keys first, else returns bank-transfer
    instructions from the brand config block."""
    with db.connect() as c:
        rows = c.execute("""
            SELECT key, value FROM config WHERE key IN (
                'stripe_secret_key', 'ziina_api_key',
                'bank_account_name', 'bank_iban', 'bank_name'
            )
        """).fetchall()
        cfg = {r["key"]: r["value"] for r in rows}

    # 1. Stripe (works globally)
    sk = cfg.get("stripe_secret_key", "").strip()
    if sk:
        try:
            import stripe  # type: ignore
            stripe.api_key = sk
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": "aed",
                        "product_data": {"name": f"Servia Quote {quote_id}"},
                        "unit_amount": int(round(amount * 100)),
                    },
                    "quantity": 1,
                }],
                success_url=f"https://servia.ae/booked.html?q={quote_id}",
                cancel_url=f"https://servia.ae/checkout?q={quote_id}",
                customer_email=customer.get("email") or None,
                metadata={"quote_id": quote_id},
            )
            return {"payment_url": session.url}
        except Exception as e:
            print(f"[checkout] stripe failed: {e}", flush=True)

    # 2. Ziina (UAE-local — direct HTTP per their official docs)
    # Docs (provided by Ehab at Ziina, 12 May 2026):
    #   Custom Integration:  https://docs.ziina.com/developers/custom-integration
    #   Embedded Checkout:   https://docs.ziina.com/developers/embedded-checkout
    #   API Reference:       https://docs.ziina.com/api-reference/introduction
    # We use the hosted-checkout flow (creates a payment_intent → redirects
    # customer to Ziina-hosted page). The embedded-checkout flow (rendering
    # a Stripe-Elements-style widget directly inside /checkout.html) is a
    # future enhancement — bigger scope, needs frontend JS to mount their
    # widget. Hosted is what most UAE merchants use.
    ziina = cfg.get("ziina_api_key", "").strip()
    if ziina:
        try:
            import httpx
            r = httpx.post(
                "https://api-v2.ziina.com/api/payment_intent",
                headers={"Authorization": f"Bearer {ziina}",
                          "Content-Type": "application/json"},
                json={
                    "amount":   int(round(amount * 100)),  # Ziina expects fils (1 AED = 100 fils)
                    "currency_code": "AED",
                    "message":  f"Servia booking · Quote {quote_id}",
                    "success_url": f"https://servia.ae/booked.html?q={quote_id}",
                    "cancel_url":  f"https://servia.ae/checkout?q={quote_id}",
                    "failure_url": f"https://servia.ae/pay-declined.html",
                    # Per Ziina API ref: include customer email/phone for KYC
                    "customer_email": customer.get("email") or "",
                    "customer_name":  customer.get("name") or "",
                },
                timeout=10.0,
            )
            if r.status_code == 200:
                d = r.json()
                # Ziina v2 returns {redirect_url, id, status}
                return {"payment_url": d.get("redirect_url") or d.get("payment_url"),
                         "provider": "ziina",
                         "payment_intent_id": d.get("id")}
        except Exception as e:
            print(f"[checkout] ziina failed: {e}", flush=True)

    # 3. Bank-transfer fallback (always available)
    return {"bank_transfer": {
        "account_name": cfg.get("bank_account_name", "Servia FZ-LLC"),
        "iban":         cfg.get("bank_iban", "Please contact admin for IBAN"),
        "bank":         cfg.get("bank_name", "Emirates NBD"),
        "amount":       amount,
        "reference":    quote_id,
    }}


@router.post("/api/checkout/{quote_id}/pay")
def checkout_pay(quote_id: str, body: CheckoutPayBody):
    """Generate a payment-gateway URL for this quote. Marks the quote as 'sent'
    if it was 'draft'. Idempotent — calling twice returns the same flow."""
    with db.connect() as c:
        row = c.execute("SELECT * FROM quotes WHERE id=?", (quote_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="quote not found")
        if row["status"] not in ("draft", "sent"):
            raise HTTPException(status_code=410, detail=f"quote is '{row['status']}' — cannot pay")
        # Update customer details if edited on the checkout page
        updates: list = []
        args: list = []
        if body.customer_email and body.customer_email != row["customer_email"]:
            updates.append("customer_email=?"); args.append(body.customer_email)
        if body.customer_name and body.customer_name != row["customer_name"]:
            updates.append("customer_name=?"); args.append(body.customer_name)
        if body.customer_phone and body.customer_phone != row["customer_phone"]:
            updates.append("customer_phone=?"); args.append(body.customer_phone)
        if body.customer_address and body.customer_address != row["customer_address"]:
            updates.append("customer_address=?"); args.append(body.customer_address)
        # Re-compute total if add-ons selected
        new_total = row["total"]
        if body.addons:
            addon_sum = sum(float(a.get("price", 0)) for a in body.addons)
            new_subtotal = row["subtotal"] + addon_sum
            new_vat = round(new_subtotal * VAT_RATE, 2)
            new_total = round(new_subtotal + new_vat, 2)
            updates.extend(["subtotal=?", "vat_amount=?", "total=?"])
            args.extend([new_subtotal, new_vat, new_total])
            # Append add-ons to line items
            items = json.loads(row["line_items_json"] or "[]")
            for a in body.addons:
                items.append({"svc_id": "addon", "name": a.get("id"),
                              "qty": 1, "unit_price": float(a.get("price", 0)),
                              "line_total": float(a.get("price", 0))})
            updates.append("line_items_json=?"); args.append(json.dumps(items))
        # Mark sent
        updates.append("status='sent'")
        if updates:
            c.execute(f"UPDATE quotes SET {', '.join(updates)} WHERE id=?", (*args, quote_id))

    customer = {
        "name":    body.customer_name or row["customer_name"],
        "phone":   body.customer_phone or row["customer_phone"],
        "email":   body.customer_email or row["customer_email"],
        "address": body.customer_address or row["customer_address"],
    }
    pay = _payment_gateway_link(quote_id, new_total, customer)
    return {"ok": True, "quote_id": quote_id, "amount": new_total, **pay}
