"""Quote → invoice → payment-link → e-signature flow.

create_quote_record    — persist a quote in the DB, return id + portal URL
create_invoice         — once quote signed, mint an invoice + payment URL
sign_quote             — store the customer's signature data URL
mark_invoice_paid      — Stripe (or other) webhook will call this

All payment integrations are pluggable. The default `payment_url` is a stub
('Pay-by-link unavailable'); set STRIPE_SECRET_KEY to switch to live Stripe Checkout.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import secrets

from . import db


def _id(prefix: str) -> str:
    return f"{prefix}-" + secrets.token_hex(3).upper()


def _now() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


def create_quote_record(*, booking_id: str | None, service_id: str,
                        breakdown: list[dict], subtotal: float,
                        discount: float, total: float,
                        currency: str = "AED", valid_days: int = 7) -> dict:
    qid = _id("Q")
    valid_until = (_dt.datetime.utcnow() + _dt.timedelta(days=valid_days)).date().isoformat()
    with db.connect() as c:
        c.execute(
            "INSERT INTO quotes(id, booking_id, service_id, breakdown_json, "
            "subtotal, discount, total, currency, valid_until, status, created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (qid, booking_id, service_id, json.dumps(breakdown),
             subtotal, discount, total, currency, valid_until, "sent", _now()),
        )
    db.log_event("quote", qid, "created", actor="bot",
                 details={"booking_id": booking_id, "total": total})
    return {"id": qid, "valid_until": valid_until, "total": total, "currency": currency,
            "view_url": f"/quote/{qid}"}


def get_quote(quote_id: str) -> dict | None:
    with db.connect() as c:
        r = c.execute("SELECT * FROM quotes WHERE id=?", (quote_id,)).fetchone()
    return db.row_to_dict(r)


def sign_quote(quote_id: str, signature_data_url: str) -> dict:
    with db.connect() as c:
        c.execute(
            "UPDATE quotes SET signature_data_url=?, signed_at=?, status='signed' WHERE id=?",
            (signature_data_url, _now(), quote_id),
        )
    db.log_event("quote", quote_id, "signed", actor="customer")
    return {"ok": True, "quote_id": quote_id}


def create_invoice(*, booking_id: str | None, quote_id: str | None,
                   amount: float, currency: str = "AED") -> dict:
    iid = _id("INV")
    payment_url = _make_payment_link(iid, amount, currency)
    with db.connect() as c:
        c.execute(
            "INSERT INTO invoices(id, booking_id, quote_id, amount, currency, "
            "payment_status, payment_url, created_at) VALUES(?,?,?,?,?,?,?,?)",
            (iid, booking_id, quote_id, amount, currency, "unpaid", payment_url, _now()),
        )
    db.log_event("invoice", iid, "created", actor="system",
                 details={"amount": amount, "booking_id": booking_id})
    return {"id": iid, "amount": amount, "currency": currency,
            "payment_url": payment_url, "view_url": f"/invoice/{iid}"}


def _make_payment_link(invoice_id: str, amount: float, currency: str) -> str:
    """Return a payment URL. Priority order:
       1. GATE_BOOKINGS=1 → /gate.html (stealth-launch)
       2. Ziina (UAE-local) if API key configured via admin panel
       3. Stripe if STRIPE_SECRET_KEY env var set
       4. Local /pay stub fallback

    v1.24.175 — Founder said: 'I gave clear Ziina key, why not
    implemented?'. Root cause: this function ignored Ziina entirely.
    Now we try Ziina FIRST since it's UAE-local + founder's primary
    gateway.
    """
    from .config import get_settings as _gs
    if _gs().GATE_BOOKINGS:
        return f"/gate.html?inv={invoice_id}&amount={amount}"

    # 1) Ziina — try first (UAE-local, founder's primary gateway)
    try:
        from . import ziina as _ziina
        if _ziina.is_configured():
            import asyncio
            domain = _gs().brand().get('domain', 'servia.ae')
            success_url = os.getenv("PAYMENT_SUCCESS_URL",
                                     f"https://{domain}/account.html")
            cancel_url  = os.getenv("PAYMENT_CANCEL_URL",
                                     f"https://{domain}/q/{invoice_id}")
            try:
                loop = asyncio.new_event_loop()
                try:
                    res = loop.run_until_complete(_ziina.create_payment_intent(
                        amount_minor=int(round(amount * 100)),
                        currency_code=(currency or "AED").upper(),
                        success_url=success_url,
                        cancel_url=cancel_url,
                        failure_url=cancel_url,
                        message=f"Servia invoice {invoice_id}",
                    ))
                finally:
                    loop.close()
                if res.get("ok") and res.get("redirect_url"):
                    return res["redirect_url"]
                print(f"[pay-link] Ziina failed: {res.get('error')!r}", flush=True)
            except Exception as e:
                print(f"[pay-link] Ziina exception: {e}", flush=True)
    except Exception as e:
        print(f"[pay-link] Ziina import failed: {e}", flush=True)

    # 2) Stripe
    sk = os.getenv("STRIPE_SECRET_KEY")
    if sk:
        try:
            import stripe  # type: ignore[import]
            stripe.api_key = sk
            sess = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {"name": f"Servia invoice {invoice_id}"},
                        "unit_amount": int(round(amount * 100)),
                    },
                    "quantity": 1,
                }],
                success_url=os.getenv("PAYMENT_SUCCESS_URL", "https://servia.ae/account.html"),
                cancel_url=os.getenv("PAYMENT_CANCEL_URL", "https://servia.ae/account.html"),
                metadata={"invoice_id": invoice_id},
            )
            return sess.url
        except Exception as e:  # noqa: BLE001
            print(f"[pay-link] Stripe failed: {e}", flush=True)

    # 3) Local stub fallback
    return f"/pay/{invoice_id}"


def mark_invoice_paid(invoice_id: str, source: str = "manual") -> dict:
    with db.connect() as c:
        c.execute(
            "UPDATE invoices SET payment_status='paid', paid_at=? WHERE id=?",
            (_now(), invoice_id),
        )
    db.log_event("invoice", invoice_id, "paid", actor=source)
    return {"ok": True, "invoice_id": invoice_id}


def list_for_booking(booking_id: str) -> dict:
    with db.connect() as c:
        qs = c.execute("SELECT * FROM quotes WHERE booking_id=? ORDER BY created_at DESC",
                       (booking_id,)).fetchall()
        ivs = c.execute("SELECT * FROM invoices WHERE booking_id=? ORDER BY created_at DESC",
                        (booking_id,)).fetchall()
    return {"quotes": db.rows_to_dicts(qs), "invoices": db.rows_to_dicts(ivs)}
