"""v1.24.143 — Unified message inbox (emails + WhatsApp + SMS, in + out).

WHY
Founder request: "All the emails and WhatsApp messages being sent from
system or being received on WhatsApp should be stored in admin side one
place. No email no booking no messages should be missed from admin panel."

WHAT
DB table `message_inbox` logs every message — email or WhatsApp, inbound
or outbound, system-sent or customer-replied. Plus an admin UI to filter
+ search + reply.

TABLE
  message_inbox
    id, direction (in/out), channel (email/whatsapp/sms),
    sender (phone or email), recipient,
    subject, body (text), attachments_json,
    related_type (booking/quote/invoice/customer), related_id,
    customer_id, status (delivered/failed/pending),
    error, raw_payload_json, created_at

HOW TO LOG A MESSAGE FROM CODE
  from .inbox import log_message
  log_message(direction="out", channel="whatsapp",
              sender="<our_phone>", recipient="+9715...",
              body="Your booking is confirmed",
              related_type="booking", related_id="LM-ABC")

EXISTING SENDERS WE WRAP
- app/whatsapp.py send_message() → wrapped with log_message(out, whatsapp)
- app/vendor_outreach.py SMTP send → wrapped with log_message(out, email)
- WhatsApp webhook handler → wrapped with log_message(in, whatsapp)
- Form-submit email handlers → wrapped with log_message(out, email)

ADMIN UI
/admin-inbox.html
  - Filters: channel (email/wa/sms), direction (in/out), date range,
    customer (search by phone/email), status
  - List view: time / channel / direction / who / preview / status
  - Click row → full message + reply button
  - Reply opens WhatsApp / mailto: link OR triggers /api/inbox/reply
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import db
from .auth import require_admin


router = APIRouter()


def _init_schema() -> None:
    with db.connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS message_inbox (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            direction       TEXT NOT NULL,             -- 'in' | 'out'
            channel         TEXT NOT NULL,             -- 'whatsapp' | 'email' | 'sms'
            sender          TEXT,
            recipient       TEXT,
            subject         TEXT,
            body            TEXT,
            attachments_json TEXT,
            related_type    TEXT,                      -- 'booking' | 'quote' | 'invoice' | 'customer' | NULL
            related_id      TEXT,
            customer_id     INTEGER,
            status          TEXT DEFAULT 'delivered',  -- delivered | failed | pending | read
            error           TEXT,
            raw_payload_json TEXT,
            replied_to_id   INTEGER,                   -- FK to parent message in same table
            created_at      TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_mi_direction ON message_inbox(direction);
        CREATE INDEX IF NOT EXISTS idx_mi_channel ON message_inbox(channel);
        CREATE INDEX IF NOT EXISTS idx_mi_customer ON message_inbox(customer_id);
        CREATE INDEX IF NOT EXISTS idx_mi_related ON message_inbox(related_type, related_id);
        CREATE INDEX IF NOT EXISTS idx_mi_created ON message_inbox(created_at);
        CREATE INDEX IF NOT EXISTS idx_mi_status ON message_inbox(status);
        """)


_init_schema()


def log_message(direction: str, channel: str,
                sender: str | None = None, recipient: str | None = None,
                subject: str | None = None, body: str | None = None,
                attachments: list | None = None,
                related_type: str | None = None, related_id: str | None = None,
                customer_id: int | None = None,
                status: str = "delivered",
                error: str | None = None,
                raw_payload: dict | None = None) -> int:
    """Log a message to the unified inbox. Returns row id.
    Never raises — failures are silently swallowed (we don't want
    inbox logging to break the actual send path)."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        with db.connect() as c:
            cur = c.execute("""
                INSERT INTO message_inbox
                  (direction, channel, sender, recipient, subject, body,
                   attachments_json, related_type, related_id, customer_id,
                   status, error, raw_payload_json, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (direction, channel, sender, recipient, subject, body,
                  json.dumps(attachments or []),
                  related_type, related_id, customer_id,
                  status, error,
                  json.dumps(raw_payload or {}), now))
            return cur.lastrowid
    except Exception as e:
        print(f"[inbox] log_message failed: {e}", flush=True)
        return 0


# ─────────────────────────────────────────────────────────────────────
# Admin endpoints
# ─────────────────────────────────────────────────────────────────────
@router.get("/api/admin/inbox", dependencies=[Depends(require_admin)])
def admin_list_inbox(channel: Optional[str] = None,
                      direction: Optional[str] = None,
                      from_date: Optional[str] = None,
                      to_date: Optional[str] = None,
                      q: Optional[str] = None,
                      customer_id: Optional[int] = None,
                      status: Optional[str] = None,
                      limit: int = 200):
    """List inbox with filters.
    ?channel=whatsapp|email|sms  ?direction=in|out
    ?q=search-in-body-or-subject ?from_date=YYYY-MM-DD ?to_date=YYYY-MM-DD
    """
    where = ["1=1"]; args: list = []
    if channel:   where.append("channel = ?");   args.append(channel)
    if direction: where.append("direction = ?"); args.append(direction)
    if status:    where.append("status = ?");    args.append(status)
    if customer_id: where.append("customer_id = ?"); args.append(customer_id)
    if from_date: where.append("created_at >= ?"); args.append(from_date)
    if to_date:   where.append("created_at <= ?"); args.append(to_date + "T23:59:59")
    if q:
        where.append("(body LIKE ? OR subject LIKE ? OR sender LIKE ? OR recipient LIKE ?)")
        args.extend([f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"])

    with db.connect() as c:
        rows = c.execute(f"""
            SELECT id, direction, channel, sender, recipient, subject,
                   substr(body, 1, 200) AS body_preview, related_type,
                   related_id, customer_id, status, created_at
            FROM message_inbox WHERE {' AND '.join(where)}
            ORDER BY created_at DESC LIMIT ?
        """, (*args, limit)).fetchall()
        return {"ok": True, "count": len(rows), "items": [dict(r) for r in rows]}


@router.get("/api/admin/inbox/stats", dependencies=[Depends(require_admin)])
def admin_inbox_stats(days: int = 7):
    """Aggregate counts for the dashboard tile."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with db.connect() as c:
        totals = c.execute("""
            SELECT direction, channel, COUNT(*) AS n FROM message_inbox
            WHERE created_at >= ? GROUP BY direction, channel
        """, (cutoff,)).fetchall()
        unread = c.execute("""
            SELECT COUNT(*) AS n FROM message_inbox
            WHERE status IN ('delivered','pending') AND direction='in'
              AND created_at >= ?
        """, (cutoff,)).fetchone()
    out = {"window_days": days, "unread_inbound": unread["n"] if unread else 0, "by_channel": {}}
    for r in totals:
        key = f"{r['direction']}_{r['channel']}"
        out["by_channel"][key] = r["n"]
    return {"ok": True, **out}


@router.get("/api/admin/inbox/{msg_id}", dependencies=[Depends(require_admin)])
def admin_get_message(msg_id: int):
    with db.connect() as c:
        row = c.execute("SELECT * FROM message_inbox WHERE id=?", (msg_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        return {"ok": True, "message": dict(row)}


class MarkReadBody(BaseModel):
    pass

@router.post("/api/admin/inbox/{msg_id}/mark-read", dependencies=[Depends(require_admin)])
def admin_mark_read(msg_id: int):
    with db.connect() as c:
        c.execute("UPDATE message_inbox SET status='read' WHERE id=?", (msg_id,))
    return {"ok": True}
