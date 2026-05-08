"""FastAPI entry point — Meta WhatsApp webhook + health check.

Two endpoints:
  GET  /webhook   Meta verification handshake (hub.challenge)
  POST /webhook   Inbound message events from Meta

The POST handler returns 200 immediately and processes the message in
the background. Meta retries aggressively on non-2xx, so we never
block on slow AI calls.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse

from .ai.base import ChatMessage
from .ai.factory import get_provider
from .config import settings
from .conversation import (
    make_store,
    record_assistant,
    record_user_and_history,
)
from .persona import build_system_prompt, needs_escalation, strip_escalate_tag
from .whatsapp import mark_read, parse_inbound, send_text, verify_signature

logging.basicConfig(level=settings.log_level.upper())
log = logging.getLogger("aalmir-bot")

app = FastAPI(title="Aalmir Plastic WhatsApp AI Bot")
_store = make_store()
_system_prompt = build_system_prompt()


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "provider": settings.ai_provider}


@app.get("/webhook")
async def verify(
    hub_mode: str | None = None,
    hub_challenge: str | None = None,
    hub_verify_token: str | None = None,
    request: Request = None,  # type: ignore[assignment]
) -> PlainTextResponse:
    # FastAPI doesn't auto-map `hub.mode` style names — read from query.
    qp = request.query_params
    mode = qp.get("hub.mode")
    challenge = qp.get("hub.challenge")
    token = qp.get("hub.verify_token")
    if mode == "subscribe" and token == settings.meta_verify_token and challenge:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="verification failed")


@app.post("/webhook")
async def inbound(
    request: Request,
    background: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, str]:
    raw = await request.body()
    if not verify_signature(settings.meta_app_secret, raw, x_hub_signature_256):
        # In production, reject. In dev (no app secret set) allow through.
        if settings.meta_app_secret:
            raise HTTPException(status_code=401, detail="bad signature")

    try:
        payload = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid json")

    messages = parse_inbound(payload)
    for msg in messages:
        if not _allowed(msg["wa_id"]):
            log.info("dropping msg from non-allowlisted wa_id=%s", msg["wa_id"])
            continue
        background.add_task(_handle_message, msg)

    # Always 200 — Meta interprets non-2xx as failure and retries.
    return {"status": "ok"}


def _allowed(wa_id: str) -> bool:
    allow = settings.allowed_number_set
    if not allow:
        return True
    return wa_id.lstrip("+") in allow


async def _handle_message(msg: dict) -> None:
    wa_id = msg["wa_id"]
    text = (msg.get("text") or "").strip()
    if not text:
        return

    log.info("inbound wa_id=%s text=%r", wa_id, text[:120])

    # Fire-and-forget read receipt — non-fatal if it fails.
    if msg.get("message_id"):
        asyncio.create_task(mark_read(msg["message_id"]))

    history_turns = await record_user_and_history(_store, wa_id, text)
    history = [ChatMessage(role=t.role, content=t.content) for t in history_turns]

    try:
        provider = get_provider()
        reply = await provider.generate(_system_prompt, history)
    except Exception as e:  # noqa: BLE001
        log.exception("AI generation failed: %s", e)
        reply = (
            "Sorry, I'm having trouble right now. The Aalmir Plastic team "
            "will get back to you shortly."
        )

    escalate = needs_escalation(reply)
    clean = strip_escalate_tag(reply) or "Thank you — our sales team will be in touch shortly."

    try:
        await send_text(wa_id, clean)
        await record_assistant(_store, wa_id, clean)
    except Exception as e:  # noqa: BLE001
        log.exception("send failed: %s", e)
        return

    if escalate:
        await _notify_handoff(wa_id, history)


async def _notify_handoff(wa_id: str, history: list[ChatMessage]) -> None:
    """Send a short summary to the handoff WhatsApp number, if configured."""
    if not settings.handoff_whatsapp:
        return
    last_user = next(
        (m.content for m in reversed(history) if m.role == "user"), ""
    )
    summary = (
        f"[handoff] Customer +{wa_id} needs human help.\n"
        f"Last message: {last_user[:300]}"
    )
    try:
        await send_text(settings.handoff_whatsapp.lstrip("+"), summary)
    except Exception as e:  # noqa: BLE001
        log.warning("handoff notify failed: %s", e)
