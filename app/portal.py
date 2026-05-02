"""Customer-facing portal API. No auth — light identity via phone + booking_id."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import db, quotes, tools

router = APIRouter(prefix="/api/portal", tags=["portal"])


@router.get("/bookings")
def my_bookings(phone: str):
    return tools.list_my_bookings(phone)


@router.get("/booking/{bid}")
def one_booking(bid: str):
    r = tools.lookup_booking(bid)
    if not r.get("ok"):
        raise HTTPException(status_code=404, detail=r.get("error"))
    # Recent events
    with db.connect() as c:
        evts = c.execute(
            "SELECT * FROM events WHERE entity_type='booking' AND entity_id=? "
            "ORDER BY id DESC LIMIT 20", (bid,)).fetchall()
    return {**r, "history": db.rows_to_dicts(evts)}


@router.get("/quote/{qid}")
def one_quote(qid: str):
    q = quotes.get_quote(qid)
    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")
    return q


class SignBody(BaseModel):
    quote_id: str
    signature_data_url: str


@router.post("/quote/sign")
def sign_quote(body: SignBody):
    q = quotes.get_quote(body.quote_id)
    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")
    if q.get("status") == "signed":
        return {"ok": True, "already_signed": True}
    quotes.sign_quote(body.quote_id, body.signature_data_url)
    # Auto-mint invoice on signature
    if q.get("booking_id"):
        inv = quotes.create_invoice(
            booking_id=q["booking_id"], quote_id=body.quote_id,
            amount=q["total"], currency=q.get("currency", "AED"))
        return {"ok": True, "invoice": inv}
    return {"ok": True}


@router.get("/invoice/{iid}")
def one_invoice(iid: str):
    with db.connect() as c:
        r = c.execute("SELECT * FROM invoices WHERE id=?", (iid,)).fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db.row_to_dict(r)


class PayStubBody(BaseModel):
    invoice_id: str


@router.post("/pay-stub")
def pay_stub(body: PayStubBody):
    """Demo: mark an invoice as paid without a real gateway. For tests."""
    return quotes.mark_invoice_paid(body.invoice_id, source="demo-stub")
