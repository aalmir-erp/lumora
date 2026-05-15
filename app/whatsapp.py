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
import os

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from . import db, demo_brain, llm, tools
from .config import get_settings
from .auth import require_admin as _require_admin_for_wa

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


def _upsert_customer_from_wa(phone: str, name: str | None) -> None:
    """v1.24.192 — Every inbound WhatsApp message upserts a customer
    record (phone is the identity). This is what makes the WA chat
    discoverable in /admin → Customers AND lets the customer's later
    web login show the same threads (cross-channel sync per founder
    request: 'match and verify in website and whatsapp also')."""
    if not phone:
        return
    now = _dt.datetime.utcnow().isoformat() + "Z"
    try:
        with db.connect() as c:
            existing = c.execute(
                "SELECT id, name FROM customers WHERE phone=?", (phone,)).fetchone()
            if existing:
                # Update last_seen_at + name if we have a better one
                if name and not existing["name"]:
                    c.execute("UPDATE customers SET name=?, last_seen_at=? WHERE id=?",
                              (name, now, existing["id"]))
                else:
                    c.execute("UPDATE customers SET last_seen_at=? WHERE id=?",
                              (now, existing["id"]))
            else:
                c.execute(
                    "INSERT INTO customers(phone, name, created_at, last_seen_at) "
                    "VALUES(?,?,?,?)", (phone, name, now, now))
    except Exception as e:  # noqa: BLE001
        print(f"[wa-webhook] customer upsert failed: {e}", flush=True)


def _normalize_phone(p: str) -> str:
    """Strip everything that isn't a digit, then drop a leading 00 / + so
    971523633995, +971 52 363 3995, 00971523633995 all normalize to the
    same string for membership checks."""
    digits = "".join(ch for ch in (p or "") if ch.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    return digits


def _trial_allowlist_active() -> bool:
    """Returns True when the trial-mode allowlist is enabled. Toggle via
    admin Mobile-App tab OR by setting WA_TRIAL_ALLOWLIST=1 env var."""
    try:
        if os.getenv("WA_TRIAL_ALLOWLIST", "").strip() in ("1", "true", "on", "yes"):
            return True
        v = db.cfg_get("wa_trial_allowlist_active", False)
        return bool(v)
    except Exception:
        return False


def _trial_allowlist_numbers() -> set[str]:
    """Set of normalized phone digits allowed to receive auto-bot replies
    during the trial. Admin number is ALWAYS included so the founder can
    still test from their own phone. Reads from db.cfg key
    'wa_trial_allowlist' (admin-editable) + the ADMIN_WA_NUMBER env."""
    out: set[str] = set()
    try:
        raw = db.cfg_get("wa_trial_allowlist", []) or []
        if isinstance(raw, list):
            for p in raw:
                n = _normalize_phone(str(p))
                if n: out.add(n)
        elif isinstance(raw, str):
            for p in raw.replace(",", " ").split():
                n = _normalize_phone(p)
                if n: out.add(n)
    except Exception: pass
    admin = _normalize_phone(os.getenv("ADMIN_WA_NUMBER", "971523633995"))
    if admin: out.add(admin)
    return out


@router.post("/webhook", dependencies=[Depends(require_bridge_token)])
def inbound(msg: InboundMsg):
    settings = get_settings()
    sid = _phone_to_session(msg.from_number)
    _upsert_customer_from_wa(msg.from_number, msg.name)
    _persist(sid, "user", msg.text, phone=msg.from_number)

    # v1.24.221 — Trial allowlist gate. When enabled, only whitelisted
    # numbers get auto-bot replies. Everyone else gets a polite "we're in
    # private trial" notice and the conversation lands in admin inbox for
    # manual takeover. Founder wants to limit who gets to test the bot
    # during early rollout to avoid bad WhatsApp experiences with random
    # contacts before the bot is fully tuned.
    if _trial_allowlist_active():
        allowed = _trial_allowlist_numbers()
        from_norm = _normalize_phone(msg.from_number)
        if from_norm and from_norm not in allowed:
            holding_reply = (
                "Hi! Servia is in private trial right now — we'll be in "
                "touch as soon as it's live for everyone. Meanwhile if "
                "you need a home service urgently you can WhatsApp our "
                "team directly at +971 52 363 3995. Thanks for reaching "
                "out! 🙏"
            )
            _persist(sid, "assistant", holding_reply, phone=msg.from_number)
            try:
                from .whatsapp_bridge import send_message  # type: ignore
                send_message(msg.from_number, holding_reply)
            except Exception: pass
            print(f"[wa-allowlist] blocked auto-reply for {from_norm} "
                  f"(allowlist has {len(allowed)} entries)", flush=True)
            return {"ok": True, "trial_blocked": True}

    # v1.24.143 — Log inbound WhatsApp to unified inbox so admin can review
    # everything in one place. Never raises.
    try:
        from . import inbox as _ix
        _ix.log_message(direction="in", channel="whatsapp",
                         sender=msg.from_number, recipient="us",
                         body=msg.text, status="delivered")
    except Exception: pass

    # v1.22.93 — short-circuit NFC tap-confirm codes ("NFCABCD …") BEFORE
    # invoking LLM / agent routing. The customer just hit Send on the
    # pre-filled WhatsApp message → we deduct the wallet, confirm booking,
    # and reply with a confirmation. Saves LLM tokens + is deterministic.
    import re as _re
    if _re.search(r"\bNFC[A-Z0-9]{4}\b", (msg.text or "").upper()):
        try:
            from . import nfc as _nfc_mod
            class _MockBody:
                pass
            body = _MockBody()
            body.from_phone = msg.from_number
            body.text = msg.text
            result = _nfc_mod.wa_code_inbound(body)
            reply = (result.get("message") or
                     "✅ Your Servia tap booking is confirmed.")
            _persist(sid, "assistant", reply, phone=msg.from_number)
            # Send the reply back via the WA bridge if configured
            try:
                from .whatsapp_bridge import send_message  # type: ignore
                send_message(msg.from_number, reply)
            except Exception:
                pass
            return {"ok": True, "handled": "nfc_wallet_confirm",
                    "deducted_aed": result.get("deducted_aed")}
        except HTTPException as e:
            err = f"⚠ Servia: {e.detail}"
            _persist(sid, "assistant", err, phone=msg.from_number)
            try:
                from .whatsapp_bridge import send_message  # type: ignore
                send_message(msg.from_number, err)
            except Exception: pass
            return {"ok": True, "error": e.detail}
        except Exception as e:  # noqa: BLE001
            print(f"[wa nfc-confirm] failed: {e}", flush=True)
            # Fall through to normal LLM routing if NFC handler crashed

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

    # Persona routing:
    #   - admin number → 'admin' (operations Q&A, stats, control)
    #   - known outreach lead → 'vendor' (Sara onboarding)
    #   - everyone else → 'customer'
    persona = "customer"
    import os as _os
    admin_num = _os.getenv("ADMIN_WA_NUMBER", "971523633995").strip().lstrip("+")
    if admin_num and msg.from_number.lstrip("+").replace(" ", "") == admin_num:
        persona = "admin"
    else:
        try:
            with db.connect() as c:
                r = c.execute("SELECT id FROM outreach_leads WHERE phone=?",
                              (msg.from_number,)).fetchone()
            if r:
                persona = "vendor"
        except Exception:  # noqa: BLE001
            pass

    if settings.use_llm:
        try:
            result = llm.chat(history, session_id=sid, language="en", persona=persona)
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


class AllowlistBody(BaseModel):
    active: bool | None = None
    numbers: list[str] | None = None  # full list to replace; or null = no change


@router.get("/trial-allowlist", dependencies=[Depends(_require_admin_for_wa)])
def get_trial_allowlist():
    """Admin: return the current trial-allowlist state (active flag + the
    full list of normalized phone numbers that are allowed to receive
    auto-bot replies during the trial)."""
    nums = sorted(_trial_allowlist_numbers())
    return {
        "active": _trial_allowlist_active(),
        "numbers": nums,
        "count": len(nums),
        "admin_always_allowed": _normalize_phone(os.getenv("ADMIN_WA_NUMBER", "971523633995")),
    }


@router.post("/trial-allowlist", dependencies=[Depends(_require_admin_for_wa)])
def set_trial_allowlist(body: AllowlistBody):
    """Admin: toggle the trial-mode allowlist on/off, or replace the
    allowed-numbers list. Both fields are optional — passing one
    without the other updates only that one."""
    if body.active is not None:
        db.cfg_set("wa_trial_allowlist_active", bool(body.active))
    if body.numbers is not None:
        normalized = []
        seen: set[str] = set()
        for raw in body.numbers:
            n = _normalize_phone(str(raw))
            if n and n not in seen:
                seen.add(n)
                normalized.append(n)
        db.cfg_set("wa_trial_allowlist", normalized)
    return get_trial_allowlist()


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
        return {"configured": True, "bridge": r.json() if r.is_success else {"error": r.text}}
    except Exception as e:  # noqa: BLE001
        return {"configured": True, "ready": False, "error": str(e)}
