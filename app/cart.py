"""Multi-service cart + bulk-checkout endpoints.

Customers can add multiple services (different types, custom date/slot per
service) to a single cart, then pay ONE invoice that covers all of them.

Cart lives client-side (localStorage) — these endpoints are stateless.
The client posts the full cart payload to /api/cart/quote for a real-time
total + line breakdown, and /api/cart/checkout to create N bookings + a
single combined invoice that the customer pays once.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import db, kb, quotes, tools

router = APIRouter(prefix="/api/cart", tags=["cart"])


class CartItem(BaseModel):
    service_id: str
    target_date: Optional[str] = None
    time_slot: Optional[str] = None
    bedrooms: Optional[int] = None
    hours: Optional[int] = None
    units: Optional[int] = None
    addons: list[str] | None = None
    notes: Optional[str] = None


class CartPayload(BaseModel):
    items: list[CartItem] = Field(..., min_items=1, max_items=20)
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None       # for auto-account create / attach
    address: Optional[str] = None
    language: Optional[str] = "en"
    # v1.24.88 — when true, route through create_multi_quote → /q/<id>
    # for the unified single-payment flow (Q-XXXXXX + signature pad).
    # Otherwise legacy multi-booking + bundle invoice path is used.
    use_quote: Optional[bool] = True
    target_date: Optional[str] = None
    time_slot: Optional[str] = None
    notes: Optional[str] = None


@router.post("/quote")
def quote(cart: CartPayload):
    """Return per-line + bundle pricing for the cart. Tolerant — if a service
    can't be priced, fall back to a starting-price estimate so the cart
    never fully breaks for the customer."""
    lines = []
    subtotal = 0
    try:
        services_index = {s["id"]: s for s in kb.services()["services"]}
    except Exception:
        services_index = {}
    for it in cart.items:
        try:
            q = tools.get_quote(
                service_id=it.service_id,
                bedrooms=it.bedrooms, hours=it.hours, units=it.units,
                recurring=None,
            )
        except Exception as e:
            q = {"ok": False, "error": str(e)}
        if not q.get("ok"):
            # Soft-fallback to starting price so the cart still renders
            sp = (services_index.get(it.service_id) or {}).get("starting_price", 100)
            q = {"ok": True, "subtotal": sp, "discount": 0, "total": sp,
                 "breakdown": {"service": it.service_id, "fallback": True}}
        line_total = q.get("total") or 0
        addon_total = 0
        addon_breakdown = []
        try:
            svc = services_index.get(it.service_id) or {}
            valid_addons = {a.get("id"): a for a in (svc.get("addons") or []) if a.get("id")}
            for aid in (it.addons or []):
                ad = valid_addons.get(aid)
                if ad:
                    p = float(ad.get("price") or 0)
                    addon_total += p
                    addon_breakdown.append({"id": aid, "label": ad.get("label"), "price": p})
        except Exception: pass
        line_total += addon_total
        lines.append({
            "service_id": it.service_id,
            "service_name": (services_index.get(it.service_id) or {}).get("name") or it.service_id,
            "base": q.get("subtotal", 0),
            "discount": q.get("discount", 0),
            "addons_total": addon_total,
            "addons": addon_breakdown,
            "total": line_total,
            "target_date": it.target_date, "time_slot": it.time_slot,
        })
        subtotal += line_total

    # Bundle discount: 5% for 2 items, 10% for 3, 15% for 4+
    n = len(lines)
    bundle_pct = 0
    if   n >= 4: bundle_pct = 15
    elif n == 3: bundle_pct = 10
    elif n == 2: bundle_pct = 5
    bundle_discount = round(subtotal * bundle_pct / 100, 2)
    grand_total = round(subtotal - bundle_discount, 2)
    return {
        "ok": True, "lines": lines,
        "subtotal": round(subtotal, 2),
        "bundle_discount_pct": bundle_pct,
        "bundle_discount": bundle_discount,
        "grand_total": grand_total,
        "currency": "AED", "items_count": n,
    }


@router.post("/checkout")
def checkout(cart: CartPayload):
    """Create N bookings + a single combined invoice covering all of them.
    Customer pays once, our team dispatches N pros (or 1 visit if same date).

    Auto-account flow: if `phone` matches an existing customer, the bookings
    attach to that account silently. Otherwise we create the customer record
    on the fly. After checkout, the customer can claim the account by either
    setting a password or requesting a magic-link via email."""
    if not (cart.customer_name and cart.phone and cart.address):
        raise HTTPException(400, "customer_name, phone, address required")
    # v1.24.88 — unified flow: route through create_multi_quote so the
    # checkout, signature, and payment all happen on /q/<id> + /p/<id>
    # — same UX whether the customer started in chat, on /book, or /cart.
    if cart.use_quote:
        from .tools import create_multi_quote as _cmq
        # Pull date/time from first item if not supplied
        td = cart.target_date or (cart.items[0].target_date if cart.items else None)
        ts = cart.time_slot   or (cart.items[0].time_slot   if cart.items else None)
        if not td or not ts:
            return {"ok": False, "error": "target_date + time_slot required"}
        services_arg = []
        for it in cart.items:
            d = it.model_dump(exclude_none=True)
            d["service_id"] = d.pop("service_id", None) or d.get("id")
            services_arg.append({k: v for k, v in d.items()
                                 if k in {"service_id","bedrooms","hours",
                                          "sqm","addons","special_instructions"}})
        q = _cmq(services=services_arg,
                 customer_name=cart.customer_name, phone=cart.phone,
                 address=cart.address, target_date=td, time_slot=ts,
                 notes=cart.notes)
        if not q.get("ok"):
            return q
        return {
            "ok": True, "via": "multi_quote",
            "quote_id": q["quote_id"],
            "total_aed": q.get("total_aed"),
            "currency": "AED",
            "payment_url": q["signing_url"],  # /q/<id> — sign first, then pay
            "signing_url": q["signing_url"],
        }
    # Strict UAE-only phone validation. We auto-normalise +971 / 971 / 0X / 5X
    # forms so customers can type whichever form they're comfortable with —
    # but anything outside the UAE +971 5X mobile range is rejected up-front.
    from . import uae_phone
    cart.phone = uae_phone.normalize_or_raise(cart.phone)

    # ---- Auto-account: attach to existing OR auto-create -----------
    customer_id = None
    customer_email = (getattr(cart, "email", "") or "").strip().lower()
    norm_phone = (cart.phone or "").strip()
    try:
        with db.connect() as c:
            r = c.execute("SELECT id, email FROM customers WHERE phone=?", (norm_phone,)).fetchone()
            if r:
                customer_id = r["id"]
                # Patch missing email if we now have one
                if customer_email and not r["email"]:
                    c.execute("UPDATE customers SET email=? WHERE id=?", (customer_email, customer_id))
            elif customer_email:
                # Or maybe email matches an existing customer with a different phone
                r2 = c.execute("SELECT id FROM customers WHERE email=?", (customer_email,)).fetchone()
                if r2:
                    customer_id = r2["id"]
                    c.execute("UPDATE customers SET phone=? WHERE id=?", (norm_phone, customer_id))
            if not customer_id:
                # Auto-create
                import datetime as _dt
                cur = c.execute(
                    "INSERT INTO customers(phone, name, email, created_at) VALUES(?,?,?,?)",
                    (norm_phone, cart.customer_name, customer_email or None,
                     _dt.datetime.utcnow().isoformat() + "Z"))
                customer_id = cur.lastrowid
            # Bookings will be associated by phone (existing tools.create_booking
            # signature) — customer_id link is implicit via the unique phone.
    except Exception as e:  # noqa: BLE001
        # Account flow is best-effort; still allow booking
        print(f"[cart-checkout] auto-account skipped: {e}", flush=True)

    bid_list = []
    booked_dicts = []
    for it in cart.items:
        # Default to first available slot if not specified
        target_date = it.target_date or __import__("datetime").date.today().isoformat()
        time_slot = it.time_slot or "10:00"
        b = tools.create_booking(
            service_id=it.service_id, target_date=target_date, time_slot=time_slot,
            customer_name=cart.customer_name, phone=cart.phone, address=cart.address,
            bedrooms=it.bedrooms, hours=it.hours, units=it.units,
            notes=it.notes, language=cart.language or "en", source="cart",
        )
        if not b.get("ok"):
            raise HTTPException(400, f"Failed to book {it.service_id}: {b.get('error')}")
        bid_list.append(b["booking"]["id"])
        booked_dicts.append(b["booking"])

    # Combined invoice — sum of every booking's estimated_total minus bundle discount
    quote_resp = quote(cart)
    grand_total = quote_resp["grand_total"]

    # Use the first booking's id as the bundle-anchor so we have a record id
    anchor_bid = bid_list[0]
    try:
        # Re-issue an aggregate quote+invoice on the anchor booking
        with db.connect() as c:
            c.execute("UPDATE bookings SET estimated_total=? WHERE id=?",
                      (grand_total, anchor_bid))
            # Tag the rest as 'bundle child' so admin sees them grouped
            for child in bid_list[1:]:
                c.execute("UPDATE bookings SET notes=COALESCE(notes,'') || ?, status='bundle_child' WHERE id=?",
                          (f" [bundle-of {anchor_bid}]", child))
        # Save bundle group to a small table for admin UI
        with db.connect() as c:
            try:
                c.execute("""
                  CREATE TABLE IF NOT EXISTS booking_bundles(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    anchor_booking_id TEXT, member_ids TEXT,
                    grand_total REAL, currency TEXT,
                    created_at TEXT)""")
            except Exception: pass
            import json as _json, datetime as _dt
            c.execute(
                "INSERT INTO booking_bundles(anchor_booking_id, member_ids, grand_total, currency, created_at) "
                "VALUES(?,?,?,?,?)",
                (anchor_bid, _json.dumps(bid_list), grand_total, "AED",
                 _dt.datetime.utcnow().isoformat()+"Z"))
        # Single combined invoice
        from . import quotes as _q
        # Build a synthetic quote covering all items
        combined_breakdown = {
            "service": f"Servia bundle ({len(bid_list)} services)",
            "lines": quote_resp["lines"],
            "bundle_discount_pct": quote_resp["bundle_discount_pct"],
            "bundle_discount": quote_resp["bundle_discount"],
        }
        qr = _q.create_quote_record(
            booking_id=anchor_bid, service_id="bundle",
            breakdown=combined_breakdown,
            subtotal=quote_resp["subtotal"],
            discount=quote_resp["bundle_discount"],
            total=grand_total)
        inv = _q.create_invoice(
            quote_id=qr.get("id") or qr.get("quote_id"), booking_id=anchor_bid,
            amount=grand_total, currency="AED")
        return {"ok": True, "bundle_anchor": anchor_bid,
                "booking_ids": bid_list, "grand_total": grand_total,
                "currency": "AED", "payment_url": inv.get("payment_url"),
                "invoice_id": inv.get("id"), "items_count": len(bid_list)}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Bundle invoice failed: {e}")
