"""Admin panel API. All endpoints require Bearer ADMIN_TOKEN."""
from __future__ import annotations

import asyncio
import json
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import db, kb, quotes, tools
from .auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ---------- Dashboard ----------
@router.get("/stats")
def stats():
    with db.connect() as c:
        b_total = c.execute("SELECT COUNT(*) AS n FROM bookings").fetchone()["n"]
        b_today = c.execute("SELECT COUNT(*) AS n FROM bookings WHERE date(created_at)=date('now')").fetchone()["n"]
        i_total = c.execute("SELECT COUNT(*) AS n FROM invoices").fetchone()["n"]
        i_paid = c.execute("SELECT COUNT(*) AS n FROM invoices WHERE payment_status='paid'").fetchone()["n"]
        rev = c.execute("SELECT COALESCE(SUM(amount),0) AS s FROM invoices WHERE payment_status='paid'").fetchone()["s"]
        by_status = c.execute("SELECT status, COUNT(*) AS n FROM bookings GROUP BY status").fetchall()
        active_takeovers = c.execute("SELECT COUNT(*) AS n FROM agent_takeovers WHERE ended_at IS NULL").fetchone()["n"]
    return {
        "bookings_total": b_total, "bookings_today": b_today,
        "invoices_total": i_total, "invoices_paid": i_paid,
        "revenue_aed": rev, "active_handoffs": active_takeovers,
        "by_status": [dict(r) for r in by_status],
    }


# ---------- Bookings ----------
@router.get("/bookings")
def list_bookings(status: str | None = None, q: str | None = None, limit: int = 100):
    sql = "SELECT * FROM bookings"
    params: list = []
    where = []
    if status:
        where.append("status=?"); params.append(status)
    if q:
        where.append("(customer_name LIKE ? OR phone LIKE ? OR address LIKE ? OR id LIKE ?)")
        params.extend([f"%{q}%"] * 4)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with db.connect() as c:
        rows = c.execute(sql, params).fetchall()
    return {"bookings": db.rows_to_dicts(rows)}


class StatusUpdate(BaseModel):
    status: str


@router.post("/bookings/{bid}/status")
def update_status(bid: str, body: StatusUpdate):
    return tools.update_booking_status(bid, body.status, actor="admin")


@router.post("/bookings/{bid}/invoice")
def make_invoice(bid: str):
    return tools.create_invoice_for_booking(bid)


# ---------- Services + pricing (config-overridable) ----------
class PricingPatch(BaseModel):
    rules: dict | None = None
    surcharges: dict | None = None
    discounts: dict | None = None


@router.get("/pricing")
def get_pricing():
    return kb.pricing()


@router.post("/pricing")
def patch_pricing(body: PricingPatch):
    overrides = db.cfg_get("pricing_overrides", {}) or {}
    payload = body.model_dump(exclude_none=True)
    for k, v in payload.items():
        overrides[k] = {**overrides.get(k, {}), **v}
    db.cfg_set("pricing_overrides", overrides)
    kb._pricing_file.cache_clear()  # noqa: SLF001  pylint: disable=protected-access
    return {"ok": True, "pricing": kb.pricing()}


@router.get("/services")
def get_services():
    return kb.services()


class ServicePatch(BaseModel):
    service_id: str
    patch: dict


@router.post("/services")
def patch_service(body: ServicePatch):
    overrides = db.cfg_get("services_overrides", {}) or {}
    overrides[body.service_id] = {**overrides.get(body.service_id, {}), **body.patch}
    db.cfg_set("services_overrides", overrides)
    return {"ok": True, "services": kb.services()}


# ---------- Conversations + live-agent takeover ----------
@router.get("/conversations")
def list_conversations(session_id: str | None = None, limit: int = 200):
    sql = "SELECT * FROM conversations"
    params: list = []
    if session_id:
        sql += " WHERE session_id=?"; params.append(session_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with db.connect() as c:
        rows = c.execute(sql, params).fetchall()
    return {"messages": db.rows_to_dicts(list(reversed(rows)))}


@router.get("/sessions")
def list_sessions(limit: int = 50):
    with db.connect() as c:
        rows = c.execute(
            "SELECT session_id, COUNT(*) AS msgs, MAX(created_at) AS last_msg, "
            "MAX(channel) AS channel, MAX(phone) AS phone "
            "FROM conversations GROUP BY session_id ORDER BY last_msg DESC LIMIT ?",
            (limit,)).fetchall()
        takeovers = {r["session_id"]: dict(r) for r in c.execute(
            "SELECT session_id, agent_id, started_at, ended_at FROM agent_takeovers"
        ).fetchall()}
    sessions = [dict(r) | {"takeover": takeovers.get(r["session_id"])} for r in rows]
    return {"sessions": sessions}


class TakeoverBody(BaseModel):
    session_id: str
    agent_id: str = "admin"


@router.post("/takeover")
def take_over(body: TakeoverBody):
    import datetime as _dt
    with db.connect() as c:
        c.execute(
            "INSERT INTO agent_takeovers(session_id, agent_id, started_at) VALUES(?,?,?) "
            "ON CONFLICT(session_id) DO UPDATE SET agent_id=excluded.agent_id, "
            "started_at=excluded.started_at, ended_at=NULL",
            (body.session_id, body.agent_id, _dt.datetime.utcnow().isoformat() + "Z"),
        )
    db.log_event("conversation", body.session_id, "takeover_started", actor=body.agent_id)
    return {"ok": True}


class ReleaseBody(BaseModel):
    session_id: str


@router.post("/release")
def release(body: ReleaseBody):
    import datetime as _dt
    with db.connect() as c:
        c.execute(
            "UPDATE agent_takeovers SET ended_at=? WHERE session_id=? AND ended_at IS NULL",
            (_dt.datetime.utcnow().isoformat() + "Z", body.session_id),
        )
    db.log_event("conversation", body.session_id, "takeover_ended", actor="admin")
    return {"ok": True}


class AgentReply(BaseModel):
    session_id: str
    text: str
    agent_id: str = "admin"


@router.post("/reply")
def agent_reply(body: AgentReply):
    """Inject an agent message into the conversation. Frontend polls /messages."""
    import datetime as _dt
    with db.connect() as c:
        c.execute(
            "INSERT INTO conversations(session_id, role, content, agent_handled, created_at) "
            "VALUES(?,?,?,1,?)",
            (body.session_id, "assistant", body.text,
             _dt.datetime.utcnow().isoformat() + "Z"),
        )
    db.log_event("conversation", body.session_id, "agent_reply", actor=body.agent_id)
    return {"ok": True}


# ---------- SSE event stream for the admin panel ----------
@router.get("/stream")
async def admin_stream(request: Request):
    """Server-sent events. Pushes new conversation lines + booking changes."""
    last_id = 0
    last_event = 0

    async def gen():
        nonlocal last_id, last_event
        with db.connect() as c:
            r = c.execute("SELECT MAX(id) AS m FROM conversations").fetchone()
            last_id = r["m"] or 0
            r = c.execute("SELECT MAX(id) AS m FROM events").fetchone()
            last_event = r["m"] or 0
        while True:
            if await request.is_disconnected():
                break
            with db.connect() as c:
                msgs = c.execute(
                    "SELECT * FROM conversations WHERE id>? ORDER BY id ASC LIMIT 50",
                    (last_id,)).fetchall()
                evts = c.execute(
                    "SELECT * FROM events WHERE id>? ORDER BY id ASC LIMIT 50",
                    (last_event,)).fetchall()
            for m in msgs:
                last_id = max(last_id, m["id"])
                yield f"event: message\ndata: {json.dumps(dict(m), ensure_ascii=False)}\n\n"
            for e in evts:
                last_event = max(last_event, e["id"])
                yield f"event: log\ndata: {json.dumps(dict(e), ensure_ascii=False)}\n\n"
            yield f": ping {int(time.time())}\n\n"
            await asyncio.sleep(2.0)

    return StreamingResponse(gen(), media_type="text/event-stream")
