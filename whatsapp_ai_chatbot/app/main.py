"""FastAPI entry point — Meta WhatsApp webhook + admin panel.

Routes:
  GET  /                health redirect to /admin
  GET  /healthz         liveness probe
  GET  /webhook         Meta verification handshake
  POST /webhook         Inbound WhatsApp messages
  /admin/*              Admin panel (auth-protected)
"""
from __future__ import annotations

import asyncio
import logging
import os
import secrets
import time

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import db, orders, settings_store
from .admin import router as admin_router
from .ai.base import ChatMessage
from .ai.factory import get_provider
from .config import settings
from .conversation import (
    Turn,
    make_store,
    record_assistant,
    record_user_and_history,
)
from .persona import build_system_prompt, needs_escalation, strip_control_tags
from .whatsapp import mark_read, parse_inbound, send_text, verify_signature

logging.basicConfig(level=settings.log_level.upper())
log = logging.getLogger("aalmir-bot")


def _session_secret() -> str:
    """Get or auto-generate the session signing secret.

    Prefers env. If absent, persist a random one into the DB so it
    survives restarts on the same volume.
    """
    s = os.environ.get("SESSION_SECRET")
    if s:
        return s
    db.init()
    existing = settings_store.get("SESSION_SECRET")
    if existing:
        return existing
    new = secrets.token_urlsafe(48)
    settings_store.set_value("SESSION_SECRET", new)
    return new


app = FastAPI(title="Aalmir Plastic WhatsApp AI Bot")
app.add_middleware(SessionMiddleware, secret_key=_session_secret(), max_age=60 * 60 * 24 * 14)
app.include_router(admin_router)

_static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

_conv_store = make_store()


@app.on_event("startup")
async def _startup() -> None:
    db.init()
    log.info("DB initialized at %s", db.DB_PATH)
    if not settings_store.get("ADMIN_PASSWORD_HASH"):
        log.warning(
            "Admin password not set. Visit /admin/setup to configure. "
            "Bootstrap token (env ADMIN_BOOTSTRAP_TOKEN) is required."
        )


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/admin", status_code=302)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {
        "status": "ok",
        "provider": settings_store.ai_provider(),
        "bot_enabled": str(settings_store.bot_enabled()).lower(),
    }


@app.get("/webhook")
async def verify(request: Request) -> PlainTextResponse:
    qp = request.query_params
    mode = qp.get("hub.mode")
    challenge = qp.get("hub.challenge")
    token = qp.get("hub.verify_token")
    expected = settings_store.meta_verify_token()
    if mode == "subscribe" and token and expected and token == expected and challenge:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="verification failed")


@app.post("/webhook")
async def inbound(
    request: Request,
    background: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, str]:
    raw = await request.body()
    app_secret = settings_store.meta_app_secret()
    if app_secret:
        if not verify_signature(app_secret, raw, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="bad signature")
    else:
        log.warning("META_APP_SECRET unset — accepting unsigned webhook (dev mode)")

    try:
        payload = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid json")

    if not settings_store.bot_enabled():
        log.info("Bot disabled — dropping payload")
        return {"status": "ok", "skipped": "bot_disabled"}

    messages = parse_inbound(payload)
    for msg in messages:
        if _is_paused(msg["wa_id"]):
            log.info("conversation paused — skipping wa_id=%s", msg["wa_id"])
            continue
        background.add_task(_handle_message, msg)

    return {"status": "ok"}


def _is_paused(wa_id: str) -> bool:
    with db.connect() as c:
        row = c.execute(
            "SELECT until_ts FROM pause_flags WHERE wa_id = ?", (wa_id,)
        ).fetchone()
        if not row:
            return False
        if row["until_ts"] < time.time():
            c.execute("DELETE FROM pause_flags WHERE wa_id = ?", (wa_id,))
            return False
        return True


def _pause_conversation(wa_id: str, hours: int = 4, reason: str = "escalated") -> None:
    until = time.time() + hours * 3600
    with db.connect() as c:
        c.execute(
            "INSERT INTO pause_flags(wa_id, until_ts, reason) VALUES(?, ?, ?) "
            "ON CONFLICT(wa_id) DO UPDATE SET until_ts=excluded.until_ts, reason=excluded.reason",
            (wa_id, until, reason),
        )


async def _handle_message(msg: dict) -> None:
    wa_id = msg["wa_id"]
    text = (msg.get("text") or "").strip()
    if not text:
        return

    log.info("inbound wa_id=%s text=%r", wa_id, text[:120])

    if msg.get("message_id"):
        asyncio.create_task(mark_read(msg["message_id"]))

    history_turns = await record_user_and_history(_conv_store, wa_id, text)
    history = [ChatMessage(role=t.role, content=t.content) for t in history_turns]

    # Persist to DB for the admin conversations viewer
    _persist_message(wa_id, "user", text)

    try:
        provider = get_provider()
        system_prompt = build_system_prompt()
        reply = await provider.generate(system_prompt, history)
    except Exception as e:  # noqa: BLE001
        log.exception("AI generation failed: %s", e)
        reply = (
            "Sorry, I'm having trouble right now. The Aalmir Plastic team "
            "will get back to you shortly."
        )

    # Extract order block, then strip control tags from customer-facing text
    clean, extracted = orders.extract_and_strip(reply)
    escalate = needs_escalation(clean)
    clean = strip_control_tags(clean)
    if not clean:
        clean = "Thank you — our sales team will be in touch shortly."

    try:
        await send_text(wa_id, clean)
        await record_assistant(_conv_store, wa_id, clean)
        _persist_message(wa_id, "assistant", clean)
    except Exception as e:  # noqa: BLE001
        log.exception("send failed: %s", e)
        return

    if extracted:
        try:
            order_id = orders.save(wa_id, extracted, raw_summary=clean)
            log.info("order saved id=%s wa_id=%s", order_id, wa_id)
        except Exception:
            log.exception("failed to save extracted order")

    if escalate:
        _pause_conversation(wa_id, hours=4, reason="escalated")
        await _notify_handoff(wa_id, history, extracted, clean)


def _persist_message(wa_id: str, role: str, content: str) -> None:
    try:
        with db.connect() as c:
            c.execute(
                "INSERT INTO conversations(wa_id, role, content, created_at) VALUES(?, ?, ?, ?)",
                (wa_id, role, content, time.time()),
            )
    except Exception:
        log.debug("conv persist failed (non-fatal)", exc_info=True)


async def _notify_handoff(
    wa_id: str,
    history: list[ChatMessage],
    extracted: orders.ExtractedOrder | None,
    last_reply: str,
) -> None:
    target = settings_store.handoff_whatsapp()
    if not target:
        return
    last_user = next((m.content for m in reversed(history) if m.role == "user"), "")
    if extracted:
        body = (
            f"[Aalmir Bot] New order intake from +{wa_id}\n"
            f"Name: {extracted.customer_name}  Co: {extracted.company}  Phone: {extracted.phone}\n"
            f"Product: {extracted.product} ({extracted.grade})\n"
            f"Specs: {extracted.dimensions}  Qty: {extracted.quantity}\n"
            f"Delivery: {extracted.delivery}\n"
            f"Notes: {extracted.notes}"
        )
    else:
        body = (
            f"[Aalmir Bot] Customer +{wa_id} needs human help.\n"
            f"Last message: {last_user[:300]}"
        )
    try:
        await send_text(target.lstrip("+"), body)
    except Exception as e:  # noqa: BLE001
        log.warning("handoff notify failed: %s", e)
