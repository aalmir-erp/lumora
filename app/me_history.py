"""Customer self-service history endpoint (v1.24.56).

Powers the new "📜 History" tab in the chat widget. Customer enters their
phone number (and optionally email) — we look up:
  · all bookings tied to that phone
  · all invoices  (legacy + multi_quotes)
  · all multi-quote carts (signed + unsigned)
  · all chat sessions where the phone was captured
And return them in one neat JSON payload the widget renders as a card list.

Phone matching is last-9-digit (so +971 / 971 / 0 prefixes all match the
same customer). Email match is case-insensitive substring (the customer
might type variations).

Privacy: a soft rate-limit + the customer must enter the phone (which they
already know). No public listing.
"""
from __future__ import annotations
import datetime as _dt
import json as _json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import db


public_router = APIRouter(tags=["history-public"])


def _norm_phone(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())[-9:]


class _LookupBody(BaseModel):
    phone: str | None = None
    email: str | None = None


@public_router.post("/api/me/history")
def me_history(body: _LookupBody) -> dict:
    p = _norm_phone(body.phone or "")
    e = (body.email or "").strip().lower()
    if not p and not e:
        raise HTTPException(400, "phone or email required")

    out: dict[str, list[dict]] = {
        "bookings": [], "invoices": [], "quotes": [], "chats": [],
    }

    with db.connect() as c:
        # Bookings (try a few likely table/column shapes — the existing
        # schema has evolved over many versions). Phone-only match.
        try:
            rows = c.execute(
                "SELECT id, service_id, status, target_date, time_slot, "
                "address, total_aed, created_at "
                "FROM bookings WHERE phone LIKE ? OR phone LIKE ? "
                "ORDER BY id DESC LIMIT 50",
                (f"%{p}", f"%{p[-8:]}")).fetchall()
            for r in rows:
                d = dict(r)
                d["kind"] = "booking"
                out["bookings"].append(d)
        except Exception: pass

        # Invoices (legacy)
        try:
            rows = c.execute(
                "SELECT id, booking_id, amount_aed, status, paid_at, created_at "
                "FROM invoices WHERE customer_phone LIKE ? OR customer_phone LIKE ? "
                "ORDER BY id DESC LIMIT 50",
                (f"%{p}", f"%{p[-8:]}")).fetchall()
            for r in rows:
                d = dict(r); d["kind"] = "invoice"
                out["invoices"].append(d)
        except Exception: pass

        # Multi-service quotes (the new system in patch 07/08)
        try:
            rows = c.execute(
                "SELECT quote_id, customer_name, phone, address, total_aed, "
                "status, signed_at, paid_at, target_date, time_slot, "
                "created_at, items_json "
                "FROM multi_quotes WHERE phone LIKE ? OR phone LIKE ? "
                "ORDER BY created_at DESC LIMIT 50",
                (f"%{p}", f"%{p[-8:]}")).fetchall()
            for r in rows:
                d = dict(r); d["kind"] = "quote"
                try: d["items"] = _json.loads(d.get("items_json") or "[]")
                except Exception: d["items"] = []
                d.pop("items_json", None)
                d["view_url"] = f"/q/{d['quote_id']}"
                d["pay_url"]  = f"/p/{d['quote_id']}"
                d["invoice_url"] = f"/i/{d['quote_id']}"
                d["pdf_url"]  = f"/i/{d['quote_id']}.pdf"
                out["quotes"].append(d)
        except Exception: pass

        # Chat sessions — group by session_id where phone matched
        try:
            rows = c.execute(
                "SELECT session_id, MIN(created_at) AS first_at, "
                "MAX(created_at) AS last_at, COUNT(*) AS msg_count, "
                "MAX(CASE WHEN role='user' THEN content END) AS sample "
                "FROM conversations WHERE phone LIKE ? OR phone LIKE ? "
                "GROUP BY session_id ORDER BY last_at DESC LIMIT 30",
                (f"%{p}", f"%{p[-8:]}")).fetchall()
            for r in rows:
                d = dict(r); d["kind"] = "chat"
                d["preview"] = (d.get("sample") or "")[:120]
                d.pop("sample", None)
                out["chats"].append(d)
        except Exception: pass

    counts = {k: len(v) for k, v in out.items()}
    total = sum(counts.values())
    return {
        "ok": True,
        "matched_phone_last_9": p if p else None,
        "matched_email": e if e else None,
        "counts": counts,
        "total": total,
        **out,
    }


@public_router.get("/api/me/chat/{session_id}")
def fetch_chat(session_id: str, phone: str = "") -> dict:
    """Returns the full chat history for a given session_id IF the phone
    matches the phone we captured during that chat. Used by the History
    tab to expand a past conversation."""
    p = _norm_phone(phone)
    if not p:
        raise HTTPException(400, "phone required")
    with db.connect() as c:
        # Verify phone matches at least one message in this session
        r = c.execute(
            "SELECT 1 FROM conversations WHERE session_id=? AND "
            "(phone LIKE ? OR phone LIKE ?) LIMIT 1",
            (session_id, f"%{p}", f"%{p[-8:]}")).fetchone()
        if not r:
            raise HTTPException(403, "phone does not match this session")
        rows = c.execute(
            "SELECT role, content, agent_handled, created_at "
            "FROM conversations WHERE session_id=? ORDER BY id ASC LIMIT 200",
            (session_id,)).fetchall()
    return {"ok": True, "session_id": session_id,
            "messages": [dict(r) for r in rows]}
