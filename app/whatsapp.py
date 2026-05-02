"""WhatsApp adapter. Inbound webhook from the Node QR-bridge → reply via the bot.

Flow:
  1. Customer messages your personal WhatsApp number (paired via QR scan in the bridge).
  2. The Node bridge forwards inbound msg to POST /api/wa/webhook here.
  3. We map phone → session_id, run the bot, push the reply back via send_whatsapp.
  4. The bridge sends it from your WhatsApp account to the customer.

The phone is BOTH the channel id and the customer identity, so multi-turn memory
works automatically.
"""
from __future__ import annotations

import datetime as _dt
import hashlib

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from . import db, demo_brain, llm, tools
from .config import get_settings

router = APIRouter(prefix="/api/wa", tags=["whatsapp"])


def require_bridge_token(x_bridge_token: str = Header(default="")) -> None:
    s = get_settings()
    if not s.WA_BRIDGE_TOKEN:
        return  # bridge not configured — accept anything (dev only)
    if x_bridge_token != s.WA_BRIDGE_TOKEN:
        raise HTTPException(status_code=401, detail="bad bridge token")


class InboundMsg(BaseModel):
    from_number: str
    text: str
    ts: str | None = None
    name: str | None = None


def _phone_to_session(phone: str) -> str:
    return "wa-" + hashlib.sha256(phone.encode()).hexdigest()[:16]


def _persist(session_id: str, role: str, content: str, *, phone: str) -> None:
    with db.connect() as c:
        c.execute(
            "INSERT INTO conversations(session_id, role, content, channel, phone, created_at) "
            "VALUES(?,?,?,?,?,?)",
            (session_id, role, content, "whatsapp", phone,
             _dt.datetime.utcnow().isoformat() + "Z"),
        )


@router.post("/webhook", dependencies=[Depends(require_bridge_token)])
def inbound(msg: InboundMsg):
    settings = get_settings()
    sid = _phone_to_session(msg.from_number)
    _persist(sid, "user", msg.text, phone=msg.from_number)

    # If a human has taken over, do not auto-reply.
    with db.connect() as c:
        t = c.execute(
            "SELECT * FROM agent_takeovers WHERE session_id=? AND ended_at IS NULL",
            (sid,)).fetchone()
    if t:
        return {"ok": True, "deferred": "agent_handling"}

    # Pull recent history (last 20 messages).
    with db.connect() as c:
        hist_rows = c.execute(
            "SELECT role, content FROM conversations WHERE session_id=? "
            "ORDER BY id DESC LIMIT 20", (sid,)).fetchall()
    history = [{"role": r["role"], "content": r["content"]} for r in reversed(hist_rows)]
    history.append({"role": "user", "content": msg.text})

    if settings.use_llm:
        try:
            result = llm.chat(history, session_id=sid, language="en")
        except Exception as e:  # noqa: BLE001
            result = {"text": f"(bot temporarily unavailable) — {e}",
                      "tool_calls": [], "usage": {}}
    else:
        result = demo_brain.respond(msg.text, history)

    text = result.get("text") or "Got it — a team member will follow up shortly."
    _persist(sid, "assistant", text, phone=msg.from_number)

    # Push reply through the bridge.
    push = tools.send_whatsapp(msg.from_number, text)
    return {"ok": True, "reply_text": text, "tool_calls": result.get("tool_calls", []),
            "bridge_send": push}


@router.get("/status")
def status():
    """Probe the Node bridge's /status endpoint and surface QR pairing state."""
    s = get_settings()
    if not s.WA_BRIDGE_URL:
        return {"configured": False, "ready": False, "note": "WA_BRIDGE_URL not set"}
    try:
        import httpx
        r = httpx.get(s.WA_BRIDGE_URL.rstrip("/") + "/status",
                      headers={"Authorization": f"Bearer {s.WA_BRIDGE_TOKEN}"},
                      timeout=5)
        return {"configured": True, "bridge": r.json() if r.ok else {"error": r.text}}
    except Exception as e:  # noqa: BLE001
        return {"configured": True, "ready": False, "error": str(e)}
