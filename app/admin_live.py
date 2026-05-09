"""Admin Live PWA — backend endpoints (v1.24.55).

Powers the standalone /admin-live.html mini-app. Designed to mirror the
WhatsApp UX:
  - Phone gets a Web Push notification when something happens
  - Wear OS auto-mirrors phone notifications (no separate watch APK)
  - Notification has a Reply action → admin types/voices a reply
  - Reply hits POST /api/admin/live/chat/{sid}/reply → posted to chat

Endpoints (all require Bearer ADMIN_TOKEN):
  GET  /api/admin/live/active-chats     — list open chat sessions in last 30 min
  GET  /api/admin/live/chat/{sid}       — full message history of a session
  POST /api/admin/live/chat/{sid}/reply — admin sends a reply to the session
  POST /api/admin/live/chat/{sid}/take  — mark session as taken-over (silences bot)
  POST /api/admin/live/chat/{sid}/release — release back to bot
  GET  /api/admin/live/feed             — combined feed (new visitors + new chats)
                                          since a `since` timestamp; powers the
                                          live polling UI

The polling endpoint /api/admin/live/feed is the heart of the PWA. UI
hits it every 4 seconds with the last-seen ID; server returns deltas only.
This keeps server load tiny even with one always-open admin PWA.
"""
from __future__ import annotations
import datetime as _dt
import json as _json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import db
from .auth import require_admin


admin_router = APIRouter(prefix="/api/admin/live", tags=["admin-live-pwa"],
                         dependencies=[Depends(require_admin)])


def _now() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


# ---------------------------------------------------------------------------
@admin_router.get("/active-chats")
def active_chats(minutes: int = 30) -> dict:
    """Sessions with at least one message in the last N minutes."""
    cutoff = (_dt.datetime.utcnow() - _dt.timedelta(minutes=max(1, minutes))).isoformat() + "Z"
    with db.connect() as c:
        rows = c.execute(
            """
            SELECT
              session_id,
              MAX(created_at)            AS last_at,
              COUNT(*)                   AS msg_count,
              SUM(CASE WHEN role='user' THEN 1 ELSE 0 END) AS user_msg_count,
              MAX(CASE WHEN role='user' THEN content END)  AS last_user_msg,
              MAX(phone)                 AS phone
            FROM conversations
            WHERE created_at > ?
            GROUP BY session_id
            ORDER BY last_at DESC
            LIMIT 50
            """, (cutoff,)).fetchall()

        # Fetch which sessions have an active agent takeover
        takeover_rows = c.execute(
            "SELECT session_id, started_at, ended_at FROM agent_takeovers "
            "WHERE ended_at IS NULL OR ended_at = ''"
        ).fetchall()
    taken = {r["session_id"]: dict(r) for r in takeover_rows}

    out = []
    for r in rows:
        d = dict(r)
        d["taken_over"] = bool(taken.get(d["session_id"]))
        d["preview"] = (d.get("last_user_msg") or "")[:140]
        out.append(d)
    return {"chats": out, "count": len(out), "fetched_at": _now()}


# ---------------------------------------------------------------------------
@admin_router.get("/chat/{sid}")
def chat_messages(sid: str, limit: int = 100) -> dict:
    with db.connect() as c:
        rows = c.execute(
            "SELECT role, content, created_at, phone, model_used "
            "FROM conversations WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (sid, limit)).fetchall()
    msgs = [dict(r) for r in reversed(rows)]
    return {"session_id": sid, "messages": msgs}


# ---------------------------------------------------------------------------
class _ReplyBody(BaseModel):
    text: str

@admin_router.post("/chat/{sid}/reply")
def admin_reply(sid: str, body: _ReplyBody) -> dict:
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty reply")
    with db.connect() as c:
        # Mark session as taken-over (silences bot for new turns)
        c.execute(
            "INSERT OR REPLACE INTO agent_takeovers(session_id, agent_id, started_at) "
            "VALUES(?,?,?)",
            (sid, "admin", _now()))
        c.execute(
            "INSERT INTO conversations(session_id, role, content, tool_calls_json, "
            "created_at, phone, model_used) "
            "VALUES(?,?,?,?,?,?,?)",
            (sid, "assistant", text, "[]", _now(), None, "agent:admin"))
    db.log_event("conversation", sid, "agent_reply", actor="admin",
                 details={"text_preview": text[:80]})
    return {"ok": True, "session_id": sid, "delivered_at": _now()}


# ---------------------------------------------------------------------------
@admin_router.post("/chat/{sid}/take")
def take_over(sid: str) -> dict:
    with db.connect() as c:
        c.execute(
            "INSERT OR REPLACE INTO agent_takeovers(session_id, agent_id, started_at) "
            "VALUES(?,?,?)", (sid, "admin", _now()))
    return {"ok": True, "session_id": sid, "taken_at": _now()}


@admin_router.post("/chat/{sid}/release")
def release(sid: str) -> dict:
    with db.connect() as c:
        c.execute(
            "UPDATE agent_takeovers SET ended_at=? "
            "WHERE session_id=? AND (ended_at IS NULL OR ended_at='')",
            (_now(), sid))
    return {"ok": True, "session_id": sid, "released_at": _now()}


# ---------------------------------------------------------------------------
@admin_router.get("/feed")
def live_feed(since: str | None = None) -> dict:
    """Combined feed of recent events for the polling PWA. Returns:
       - new_chats:     sessions with first message after `since`
       - new_messages:  any user messages after `since` in already-active sessions
       - new_visitors:  brand-new visitor IDs in the last 5 min
    The PWA passes its last 'until' timestamp as `since` next call so the
    server only sends deltas. Default since = 60 seconds ago.
    """
    if not since:
        since = (_dt.datetime.utcnow() - _dt.timedelta(seconds=60)).isoformat() + "Z"
    with db.connect() as c:
        new_msgs = [dict(r) for r in c.execute(
            "SELECT session_id, role, content, created_at, phone "
            "FROM conversations WHERE created_at > ? AND role='user' "
            "ORDER BY created_at DESC LIMIT 50",
            (since,)).fetchall()]
        new_visitors = [dict(r) for r in c.execute(
            "SELECT visitor_id, last_seen, last_path, country, referrer "
            "FROM live_visitors WHERE first_seen > ? "
            "ORDER BY first_seen DESC LIMIT 20",
            (since,)).fetchall()]
    return {
        "until": _now(),
        "new_messages": new_msgs,
        "new_visitors": new_visitors,
    }
