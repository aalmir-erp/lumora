"""FastAPI entrypoint."""
from __future__ import annotations

import datetime as _dt
import json
import os
from pathlib import Path
from typing import Optional

import pathlib
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import admin, ai_router, cart, db, demo_brain, kb, launch, live_visitors, llm, portal, portal_v2, psi as _psi_mod, push_notifications, quotes, selftest, social_publisher, staff_portraits, tools, videos, visibility, whatsapp
from .auth import ADMIN_TOKEN
from .config import get_settings

settings = get_settings()
app = FastAPI(title=settings.BRAND_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"], allow_headers=["*"],
)
# GZip every response > 500 bytes — biggest single PageSpeed win.
# Railway / proxy doesn't compress for us; PSI flagged "No compression applied"
# with 30 KiB of saving on the document request alone.
app.add_middleware(GZipMiddleware, minimum_size=500)

# Routers
# IMPORTANT: specific admin sub-routers MUST be registered BEFORE
# admin.router because admin.router has a catch-all DELETE /{entity}/{rid}
# pattern that would otherwise match /social-images/{slug} etc and reject
# them with "unsupported entity". FastAPI routes are matched in registration
# order — first match wins.
from . import vendor_scraper as _vs, vendor_outreach as _vo, social_images as _si
app.include_router(_vs.router)
app.include_router(_vo.router)
app.include_router(_si.admin_router)
app.include_router(_si.public_router)
app.include_router(admin.router)
app.include_router(admin.public_cms_router)
app.include_router(admin.public_2fa_router)
app.include_router(admin.public_reviews_router)


@app.get("/image/{slug}", response_class=HTMLResponse)
def public_image_page(slug: str):
    return _si.render_image_page(slug)
app.include_router(live_visitors.admin_router)
app.include_router(push_notifications.router)
app.include_router(push_notifications.public_router)
app.include_router(portal.router)
app.include_router(portal_v2.router)
app.include_router(portal_v2.public_router)
app.include_router(whatsapp.router)
app.include_router(launch.router)
app.include_router(cart.router)
app.include_router(ai_router.router)
app.include_router(videos.public_router)
app.include_router(videos.admin_router)
app.include_router(social_publisher.router)
app.include_router(staff_portraits.router)
app.include_router(visibility.router)
app.include_router(selftest.router)


# Bot-visit logger middleware — records crawls from AI/search bots so admin
# can see "GPTBot hit /llms.txt 12 times this week, ClaudeBot hit /blog 8 times".
@app.middleware("http")
async def _log_bot_visit_mw(request: Request, call_next):
    try: visibility.log_bot_visit(request)
    except Exception: pass
    # Live visitor tracker — records human visitors only (skips API/admin/SW)
    is_new_visitor = False
    try: is_new_visitor = live_visitors.track(request)
    except Exception: pass
    resp = await call_next(request)
    # Push admin alert when a brand-new visitor lands (rate-limited via cfg)
    if is_new_visitor:
        try:
            from . import admin_alerts as _aa
            ua = (request.headers.get("user-agent") or "")[:120]
            path = str(request.url.path)
            ref = (request.headers.get("referer") or "(direct)")[:120]
            ipc = request.headers.get("cf-ipcountry") or ""
            _aa.notify_admin(
                f"👋 New visitor on Servia\n\n"
                f"Page: {path}\nReferrer: {ref}\nCountry: {ipc or '?'}\nUA: {ua}",
                kind="new_visitor", urgency="low")
        except Exception: pass
    return resp


@app.on_event("startup")
def _seed_starter_videos():
    try: videos.seed_videos_if_empty()
    except Exception as e: print(f"[videos] seed skipped: {e}", flush=True)


# ---------- public social profiles for frontend follow strip ----------
@app.get("/api/site/social")
def public_social():
    s = db.cfg_get("social_profiles", {}) or {}
    out = []
    LABELS = [
        ("instagram", "Instagram", "📷"),
        ("tiktok",    "TikTok",    "🎵"),
        ("facebook",  "Facebook",  "📘"),
        ("twitter",   "X",         "𝕏"),
        ("linkedin",  "LinkedIn",  "💼"),
        ("youtube",   "YouTube",   "📺"),
        ("pinterest", "Pinterest", "📌"),
    ]
    for k, label, emoji in LABELS:
        url = (s.get(k) or "").strip()
        if url: out.append({"key": k, "label": label, "emoji": emoji, "url": url})
    return {"profiles": out}


# ---------- public snippets injector — admin pastes GA/GTM/Pixel/etc, all pages run it ----------
@app.get("/_snippets.js")
def public_snippets_js():
    from fastapi.responses import Response
    js = launch.public_snippets_js()
    return Response(js, media_type="application/javascript",
                    headers={"Cache-Control": "public, max-age=300"})


# ---------- chat ----------
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    language: Optional[str] = "en"
    phone: Optional[str] = None
    attachment_url: Optional[str] = None  # /uploads/chat/xxx.jpg from /api/chat/upload


class ChatResponse(BaseModel):
    session_id: str
    text: str
    tool_calls: list
    mode: str
    usage: dict
    agent_handled: bool = False


def _new_sid() -> str:
    import secrets
    return "sw-" + secrets.token_urlsafe(12)


# AI-tell scrubber for blog content. LLMs love em-dashes, semicolons, and a
# small clutch of "smart-sounding" filler words. Strip them so blog reads human.
_HUMANIZE_REPLACEMENTS = [
    ("—", ", "),          # em-dash → comma + space (most common AI tell)
    (" – ", ", "),         # en-dash with spaces → comma
    ("–", "-"),            # bare en-dash → hyphen
    (";", "."),            # semicolons → period
    (" - ", ", "),         # spaced hyphen used as parenthetical → comma
    ("…", "..."),          # ellipsis char → three dots
]
_HUMANIZE_WORDS = {
    # word → human alternative (case-insensitive whole-word replace)
    "delve": "look", "delves": "looks", "delved": "looked", "delving": "looking",
    "tapestry": "mix",
    "navigate": "handle", "navigates": "handles", "navigated": "handled", "navigating": "handling",
    "leverage": "use", "leverages": "uses", "leveraged": "used", "leveraging": "using",
    "utilize": "use", "utilizes": "uses", "utilized": "used", "utilizing": "using",
    "streamline": "simplify", "streamlined": "simplified",
    "robust": "solid", "seamless": "smooth", "seamlessly": "smoothly",
    "comprehensive": "full", "vital": "important", "crucial": "key",
    "myriad": "many", "plethora": "lots",
    "embark": "start", "embarks": "starts", "embarked": "started", "embarking": "starting",
    "foster": "build", "fosters": "builds", "fostered": "built", "fostering": "building",
    "showcase": "show", "showcases": "shows", "showcased": "showed", "showcasing": "showing",
    "nestled": "tucked",
    "bustling": "busy", "vibrant": "lively", "iconic": "famous", "stunning": "great",
    "in conclusion,": "Bottom line:",
    "in summary,": "So:",
    "it's worth noting that": "note:",
    "when it comes to": "for",
}


def _humanize_text(text: str) -> str:
    if not text: return text
    import re as _re
    out = text
    for src, dst in _HUMANIZE_REPLACEMENTS:
        out = out.replace(src, dst)
    for w, repl in _HUMANIZE_WORDS.items():
        # Case-insensitive whole-word replace, preserve leading capital
        pat = _re.compile(r"\b" + _re.escape(w) + r"\b", _re.IGNORECASE)
        def _sub(m, _repl=repl):
            orig = m.group(0)
            return _repl[0].upper() + _repl[1:] if orig[0].isupper() else _repl
        out = pat.sub(_sub, out)
    # Collapse double spaces / double commas the substitutions can produce
    out = _re.sub(r" {2,}", " ", out)
    out = _re.sub(r",\s*,", ",", out)
    out = _re.sub(r"\.\s*\.", ".", out)
    return out


def _persist(session_id: str, role: str, content: str, *, phone: str | None,
             tool_calls: list | None = None, agent: bool = False,
             user_agent: str | None = None, ip: str | None = None,
             model_used: str | None = None,
             tokens_in: int | None = None, tokens_out: int | None = None,
             cost_usd: float | None = None,
             attachment_url: str | None = None) -> None:
    """Persist a chat turn with rich metadata for the admin Conversations view.
    All metadata cols are added via idempotent ALTER TABLE so old DBs upgrade
    silently — never crashes if a column already exists or doesn't yet."""
    with db.connect() as c:
        for col, typ in [("user_agent","TEXT"),("ip","TEXT"),("model_used","TEXT"),
                         ("tokens_in","INTEGER"),("tokens_out","INTEGER"),
                         ("cost_usd","REAL"),("attachment_url","TEXT")]:
            try: c.execute(f"ALTER TABLE conversations ADD COLUMN {col} {typ}")
            except Exception: pass
        c.execute(
            "INSERT INTO conversations(session_id, role, content, tool_calls_json, "
            "channel, phone, agent_handled, user_agent, ip, model_used, "
            "tokens_in, tokens_out, cost_usd, attachment_url, created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (session_id, role, content,
             json.dumps(tool_calls) if tool_calls else None,
             "web", phone, 1 if agent else 0,
             (user_agent or "")[:300], (ip or "")[:64], (model_used or "")[:80],
             tokens_in, tokens_out, cost_usd,
             (attachment_url or "")[:300] if attachment_url else None,
             _dt.datetime.utcnow().isoformat() + "Z"),
        )


def _history(session_id: str, limit: int = 20) -> list[dict]:
    with db.connect() as c:
        rows = c.execute(
            "SELECT role, content FROM conversations WHERE session_id=? "
            "ORDER BY id DESC LIMIT ?", (session_id, limit)).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def _is_taken_over(session_id: str) -> bool:
    """Returns True if a live agent has taken over this session AND the takeover
    is fresh (< STALE_TAKEOVER_MIN minutes). Stale takeovers auto-release so a
    forgotten admin click can never silence the bot forever."""
    STALE_MIN = int(os.getenv("STALE_TAKEOVER_MIN", "30") or "30")
    with db.connect() as c:
        r = c.execute(
            "SELECT started_at FROM agent_takeovers "
            "WHERE session_id=? AND ended_at IS NULL",
            (session_id,)).fetchone()
        if not r: return False
        try:
            started = _dt.datetime.fromisoformat(r["started_at"].rstrip("Z"))
            age_min = (_dt.datetime.utcnow() - started).total_seconds() / 60
        except Exception:
            age_min = 0
        if age_min > STALE_MIN:
            # Auto-release stale takeover so the bot resumes
            c.execute(
                "UPDATE agent_takeovers SET ended_at=? "
                "WHERE session_id=? AND ended_at IS NULL",
                (_dt.datetime.utcnow().isoformat() + "Z", session_id))
            return False
    return True




# ---------- Booking fast-path — bypass LLM for direct form-style commands ----------
import re as _re
_BOOK_RX = _re.compile(
    r"^Book\s+(\w+)\s+on\s+(\d{4}-\d{2}-\d{2})\s+at\s+(\d{1,2}:\d{2})\s+for\s+([^,]+),\s+phone\s+([+0-9 ]+),\s+address:?\s*['\"]?([^,'\"]+)['\"]?",
    _re.I)


def _try_fast_book(message: str) -> dict | None:
    m = _BOOK_RX.match(message.strip())
    if not m: return None
    svc, date, time_, name, phone, addr = m.groups()
    # Reject the fast-book if the phone isn't a valid UAE mobile so the LLM
    # cascade can ask the customer for one in their next bot turn.
    from . import uae_phone as _uae
    norm_phone = _uae.normalize(phone)
    if not norm_phone:
        return None
    phone = norm_phone
    # Optional fields after address
    rest = message[m.end():]
    bedrooms = next((int(x) for x in _re.findall(r"(\d+)\s*bedroom", rest, _re.I)), None)
    hours = next((int(x) for x in _re.findall(r"(\d+)\s*hour", rest, _re.I)), None)
    units = next((int(x) for x in _re.findall(r"(\d+)\s*unit", rest, _re.I)), None)
    rec = (_re.findall(r"recurring:\s*(\w+)", rest) or [None])[0]
    addons_match = _re.search(r"addons?:\s*([\w,]+)", rest)
    addons = [a.strip() for a in (addons_match.group(1).split(",") if addons_match else []) if a.strip()]
    res = tools.create_booking(
        service_id=svc, target_date=date, time_slot=time_,
        customer_name=name.strip(), phone=phone.strip(),
        address=addr.strip(),
        bedrooms=bedrooms, hours=hours, units=units,
        notes=("recurring=" + rec if rec else None),
    )
    if not res.get("ok"):
        return None
    booking = res["booking"]
    return {
        "text": (f"✅ All set! Your booking **{booking['id']}** is confirmed for "
                 f"{date} at {time_}. Estimated total: {booking.get('estimated_total','—')} {booking.get('currency','AED')}. "
                 f"We'll WhatsApp you a confirmation. Track at /me.html?b={booking['id']}"),
        "tool_calls": [{"name": "create_booking", "input": {
            "service_id": svc, "target_date": date, "time_slot": time_,
            "customer_name": name, "phone": phone, "address": addr,
            "bedrooms": bedrooms, "hours": hours, "units": units, "addons": addons,
        }, "result": res}],
        "usage": {}, "stop_reason": "end_turn",
    }


async def _cascade_via_router(prompt: str, history: list[dict], lang: str) -> dict | None:
    """Try every text provider/model in MODEL_CATALOG that has a key set, in
    cost-ascending order, until one returns a non-empty reply. The customer
    NEVER sees a 'brain hiccup' message — they see a real AI answer or
    (only as last resort) the rule-based demo brain.

    Returns {ok, text, provider, model, latency_ms} or None if no key works.
    """
    from . import ai_router
    cfg = ai_router._load_cfg()
    # Build cascade order: 'customer' default first (admin's pick), then every
    # other text provider/model that has a key, cheapest fast tier first.
    tried = set()
    candidates: list[tuple[str, str]] = []   # (provider, model)
    cust = (cfg.get("defaults") or {}).get("customer", "")
    if cust and "/" in cust:
        p, m = cust.split("/", 1)
        if (cfg["keys"].get(p) or "").strip():
            candidates.append((p, m))
    # Add every other provider's cheapest model that has a key
    PRIORITY_TIERS = ["fast", "balanced", "premium"]
    for prov_id, info in ai_router.MODEL_CATALOG.items():
        if info.get("modality") != "text": continue          # skip image providers
        if not (cfg["keys"].get(prov_id) or "").strip(): continue
        for tier in PRIORITY_TIERS:
            for m in info.get("models", []):
                if m.get("tier") == tier:
                    candidates.append((prov_id, m["id"]))
                    break
    # Convert prior chat history into messages-style for the router
    history_msgs = [{"role": h["role"], "content": h["content"]} for h in (history or [])]
    # Build a comprehensive system prompt — when the cascade is in play we're
    # using a non-Anthropic model that has NO tool access and NO knowledge of
    # our actual services. Inject the live service catalog + brand domain so
    # the model stops hallucinating "yourwebsite.com" URLs and knows what we
    # actually offer (chauffeur, mobile repair, etc).
    try:
        svc_list = kb.services().get("services", [])
    except Exception: svc_list = []
    domain = settings.BRAND_DOMAIN
    svc_lines = "\n".join(
        f"- {s.get('name','?')} (id={s.get('id')}) — from AED {s.get('starting_price','?')}"
        for s in svc_list
    )[:3500]
    sys_prompt = (
        f"You are Servia, the AI concierge for a UAE home-services platform. "
        f"Brand domain: https://{domain}\n"
        f"Reply in {lang}. Be friendly, concise, locally informed (UAE).\n\n"
        "## Hard rules — MUST follow\n"
        f"1. Every URL MUST start with https://{domain}. NEVER write 'yourwebsite.com', "
        "'example.com', or any other placeholder. To book: https://" + domain + "/book.html. "
        "To see prices: https://" + domain + "/services.html. To see videos: "
        "https://" + domain + "/videos.html. To open a specific service: "
        "https://" + domain + "/service.html?id=<service_id>.\n"
        "2. Use Markdown links so the widget renders them clickable: "
        "[Book now](https://" + domain + "/book.html). NOT raw URLs in parentheses.\n"
        "3. NEVER claim we don't offer a service that's in the list below. We DO offer "
        "every service in the catalog.\n"
        "4. NEVER use em-dashes, en-dashes, or semicolons.\n"
        "5. Quote prices in AED with VAT inclusive (5%).\n\n"
        "## Service catalog (live, from our database)\n"
        f"{svc_lines}\n\n"
        "## Booking flow\n"
        "If the customer wants to book, ask for: service id, emirate (Dubai / Sharjah / "
        "Abu Dhabi / Ajman / RAK / UAQ / Fujairah), date+time, address, name + phone. "
        "ALWAYS clarify that we need a valid UAE mobile number — must start with +971 or 05 "
        "(e.g. +971501234567 or 0501234567). If the customer gives a non-UAE number, ask "
        "again politely and explain we only operate in the UAE. "
        "Then confirm with a [Book now](https://" + domain + "/book.html?service=<id>&area=<emirate>) "
        "deep link.\n\n"
        "## Out of scope\n"
        "If asked about something genuinely outside home services (e.g. visa, flight booking), "
        "politely redirect: 'I help with home services in the UAE — for that, you'd need a "
        "different specialist. But if you need anything for your home, I'm here.'"
    )
    history_msgs.insert(0, {"role": "user", "content": sys_prompt})
    for (provider, model) in candidates:
        key_t = (provider, model)
        if key_t in tried: continue
        tried.add(key_t)
        try:
            res = await ai_router.call_model(provider, model, prompt, cfg, history=history_msgs)
        except Exception:  # noqa: BLE001
            continue
        if res.get("ok") and (res.get("text") or "").strip():
            return res
    return None


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request):
    sid = req.session_id or _new_sid()
    lang = (req.language or "en").lower()[:2]

    # Capture browser/IP for the admin Conversations view.
    user_agent = (request.headers.get("user-agent") or "")[:300]
    ip = (request.client.host if request.client else "")[:64]

    # If the user attached an image, fold a marker into the persisted message
    # so it's visible in conversations + the LLM gets context. The actual image
    # bytes can be loaded by the model via the public URL if needed.
    msg = req.message
    if req.attachment_url:
        msg = (msg + f"\n[attached image: {req.attachment_url}]").strip()
    _persist(sid, "user", msg, phone=req.phone,
             user_agent=user_agent, ip=ip, attachment_url=req.attachment_url)

    # Fast-path for explicit booking commands — saves a 10-15s LLM round-trip
    fast = _try_fast_book(req.message)
    if fast:
        text = fast.get("text") or "(no response)"
        _persist(sid, "assistant", text, phone=req.phone,
                 tool_calls=fast.get("tool_calls"), model_used="fast-path")
        return ChatResponse(session_id=sid, text=text,
                            tool_calls=fast.get("tool_calls", []),
                            mode="fast", usage={})

    if _is_taken_over(sid):
        # Live agent has joined — return friendly text so the customer sees SOMETHING
        # instead of total silence. Their next bubble will arrive via /api/chat/poll.
        msg_text = "👋 Hi! A team member has joined this chat — they'll reply to you shortly."
        return ChatResponse(session_id=sid, text=msg_text, tool_calls=[],
                            mode="agent_handling", usage={}, agent_handled=True)

    history = _history(sid)
    # Resolve which model+key to use. Priority order so customer NEVER sees an
    # error and admin-side configuration takes precedence over Railway env vars:
    #
    #   1) Anthropic via env (full tool-use path with bookings/quotes)
    #      ↓ falls through on auth/model/rate-limit failure
    #   2) Admin-side AI Router 'customer' default (whatever provider/key admin saved)
    #      ↓ falls through if that key is missing or returns an error
    #   3) Cascade through every text provider in MODEL_CATALOG that has a key set,
    #      starting with the cheapest fast model (so we don't burn dollars on retries)
    #   4) Rule-based demo brain — always succeeds, never blank
    #
    # The customer-visible text is ALWAYS a real reply; the fallback chain is silent.
    result = None
    mode = ""
    last_err = None
    # Only attempt the Anthropic-bound primary path when the admin's customer
    # default IS Anthropic. If they've configured a different provider (or none
    # at all), skip straight to the cascade so we don't burn 5-10s on a known-
    # bad Anthropic call before fallback kicks in.
    try:
        from . import ai_router as _ar
        _cust_default = (_ar._load_cfg().get("defaults") or {}).get("customer", "")
    except Exception: _cust_default = ""
    if settings.use_llm and (_cust_default.startswith("anthropic/") or not _cust_default):
        try:
            result = llm.chat(history, session_id=sid, language=lang)
            mode = "llm"
        except Exception as e:  # noqa: BLE001
            last_err = f"primary anthropic: {e}"
            print(f"[chat] primary LLM failed, cascading: {e}", flush=True)

    if (not result) or not (result.get("text") or "").strip():
        # 2 & 3: try admin-side AI Router with cascade
        try:
            import asyncio as _aio
            cascade_result = _aio.run(_cascade_via_router(req.message, history, lang))
        except RuntimeError:
            # Already in event loop (FastAPI sync handler shouldn't be, but defensive)
            cascade_result = None
        except Exception as e:  # noqa: BLE001
            cascade_result = None
            last_err = (last_err or "") + f" · cascade: {e}"
        if cascade_result and cascade_result.get("ok") and (cascade_result.get("text") or "").strip():
            result = {"text": cascade_result["text"], "tool_calls": [], "usage": {}}
            mode = "router:" + cascade_result.get("provider","?") + "/" + cascade_result.get("model","?")

    if (not result) or not (result.get("text") or "").strip():
        # 4: rule-based demo brain — always returns something
        try:
            result = demo_brain.respond(req.message, history)
            mode = "fallback"
        except Exception as e2:  # noqa: BLE001
            result = {"text": "I'm here — but I'm having a brief technical hiccup. Try again in a moment, or message us via /contact.html and we'll reply within minutes.",
                      "tool_calls": [], "usage": {}}
            mode = "error"
            db.log_event("chat", sid, "llm_error", actor="system",
                         details={"err": last_err, "fallback_err": str(e2)})

    text = (result.get("text") or "").strip()
    if not text:
        # Defence-in-depth: never return silence. If the LLM looped on tool calls
        # without producing final text, give the user a clear "I'm here" reply.
        text = ("Got it — I've noted your message. Could you give me one more detail "
                "(service, area, or date) so I can help? Or use /contact.html for direct support.")
    usage = result.get("usage") or {}
    tin  = usage.get("input_tokens") or usage.get("prompt_tokens") or None
    tout = usage.get("output_tokens") or usage.get("completion_tokens") or None
    # Anthropic Claude pricing (Sonnet 4.6 default): $3 in / $15 out per 1M tokens
    cost = None
    try:
        if tin is not None and tout is not None:
            cost = round((tin/1_000_000)*3.0 + (tout/1_000_000)*15.0, 4)
    except Exception: pass
    model_used = settings.MODEL if mode == "llm" else mode
    _persist(sid, "assistant", text, phone=req.phone,
             tool_calls=result.get("tool_calls"),
             model_used=model_used,
             tokens_in=tin, tokens_out=tout, cost_usd=cost)
    return ChatResponse(session_id=sid, text=text,
                        tool_calls=result.get("tool_calls", []),
                        mode=mode, usage=usage)


@app.get("/api/chat/poll")
def poll(session_id: str, since_id: int = 0):
    """Frontend polls this for agent messages while a takeover is active."""
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, role, content, agent_handled, created_at "
            "FROM conversations WHERE session_id=? AND id>? ORDER BY id ASC",
            (session_id, since_id)).fetchall()
    msgs = db.rows_to_dicts(rows)
    return {"session_id": session_id, "messages": msgs,
            "agent_handling": _is_taken_over(session_id)}


# ---------- public read endpoints ----------
@app.get("/api/health")
def health():
    return {"ok": True, "service": settings.BRAND_NAME, "version": settings.APP_VERSION,
            "mode": "llm" if settings.use_llm else "demo",
            "model": settings.MODEL if settings.use_llm else None,
            "wa_bridge": bool(settings.WA_BRIDGE_URL),
            "admin_token_hint": "(set ADMIN_TOKEN env var)" if not settings.use_llm else None}


@app.get("/api/brand")
def get_brand():
    return settings.brand()


@app.get("/api/i18n")
def get_i18n():
    return json.loads((settings.DATA_DIR / "i18n.json").read_text())


@app.get("/api/services")
def list_services():
    return kb.services()


@app.get("/api/pricing")
def get_pricing_pub():
    return kb.pricing()


# ---------- payment stub ----------
@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Receive Stripe checkout.session.completed events and mark invoices paid.

    Configure STRIPE_WEBHOOK_SECRET in env for signature verification.
    Endpoint URL to register in Stripe Dashboard:
        https://<your-domain>/api/webhooks/stripe
    """
    import os, json as _json
    body = await request.body()
    sig = request.headers.get("stripe-signature", "")
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    try:
        if secret:
            import stripe  # type: ignore
            event = stripe.Webhook.construct_event(body, sig, secret)
        else:
            event = _json.loads(body)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"Invalid signature: {e}")

    etype = event.get("type") if isinstance(event, dict) else event["type"]
    obj = (event.get("data") or {}).get("object") if isinstance(event, dict) else event["data"]["object"]
    if etype == "checkout.session.completed":
        invoice_id = (obj.get("metadata") or {}).get("invoice_id")
        if invoice_id:
            from . import quotes as _q
            _q.mark_invoice_paid(invoice_id, source="stripe")
            # Confirm the booking now that payment is in
            with db.connect() as c:
                r = c.execute("SELECT booking_id FROM invoices WHERE id=?", (invoice_id,)).fetchone()
                if r and r["booking_id"]:
                    c.execute("UPDATE bookings SET status='confirmed' WHERE id=?", (r["booking_id"],))
                    db.log_event("booking", r["booking_id"], "payment_confirmed", actor="stripe")
    return {"ok": True}


# Idempotent migration: add payment_method column to invoices on startup.
def _ensure_invoice_payment_method():
    try:
        with db.connect() as c:
            try: c.execute("ALTER TABLE invoices ADD COLUMN payment_method TEXT")
            except Exception: pass
    except Exception: pass
_ensure_invoice_payment_method()


@app.get("/pay/{invoice_id}", response_class=HTMLResponse)
def pay_page(invoice_id: str):
    """Serves /web/pay.html — the rich multi-method checkout page that handles
    auto-account creation + login + payment selection."""
    p = pathlib.Path("web/pay.html")
    if not p.exists(): raise HTTPException(500, "pay.html missing")
    return HTMLResponse(p.read_text(encoding="utf-8"))


@app.get("/api/pay/invoice/{invoice_id}")
def api_get_invoice(invoice_id: str):
    """Returns invoice + booking details for the payment page to render summary."""
    from . import quotes as _q
    with db.connect() as c:
        r = c.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
    if not r:
        raise HTTPException(404, "invoice not found")
    inv = db.row_to_dict(r)
    booking = None
    if inv.get("booking_id"):
        with db.connect() as c:
            br = c.execute("SELECT * FROM bookings WHERE id=?", (inv["booking_id"],)).fetchone()
        if br:
            booking = db.row_to_dict(br)
            # Resolve service name for display
            try:
                sr = c.execute("SELECT name FROM services WHERE id=?", (booking.get("service_id"),)).fetchone()
                if sr: booking["service_name"] = sr["name"]
            except Exception: pass
    return {**inv, "booking": booking}


class PayStartBody(BaseModel):
    invoice_id: str
    phone: str
    email: Optional[str] = None
    method: str   # card | apple | google | wa | bank | cod


@app.post("/api/pay/start")
def api_pay_start(body: PayStartBody):
    """Auto-account + payment kickoff:
    1. Find or create customer by phone (fall back to email match)
    2. Issue an auth token so the browser is logged in immediately
    3. Branch by method:
       - card/apple/google → create Stripe Checkout Session, redirect
       - wa  → record intent, queue WhatsApp pay-link send (admin alert)
       - bank → record intent + return reference number to display
       - cod  → mark booking as 'cash on service', confirm immediately
    4. Persist payment intent to invoices table for admin tracking
    """
    from . import quotes as _q, auth_users as _au, admin_alerts as _aa, uae_phone
    import os as _os, datetime as _d
    # Strict UAE mobile only — auto-normalised so 0501234567 / 971501234567 /
    # +971501234567 all become +971501234567. Anything else returns the
    # user-friendly error (shown in the customer's pay screen alert).
    phone = uae_phone.normalize_or_raise(body.phone)
    body.phone = phone   # propagate the normalised form to downstream code
    email = (body.email or "").strip().lower() or None

    # 1) Look up invoice + booking
    with db.connect() as c:
        ir = c.execute("SELECT * FROM invoices WHERE id=?", (body.invoice_id,)).fetchone()
        if not ir: raise HTTPException(404, "invoice not found")
        inv = db.row_to_dict(ir)
        if inv.get("payment_status") == "paid":
            return {"ok": True, "message": "Already paid", "booking_id": inv.get("booking_id")}
        booking = None
        if inv.get("booking_id"):
            br = c.execute("SELECT * FROM bookings WHERE id=?", (inv["booking_id"],)).fetchone()
            booking = db.row_to_dict(br) if br else None

    # 2) Auto-account: phone-first match, email fallback, else create
    cid = None
    with db.connect() as c:
        r = c.execute("SELECT id FROM customers WHERE phone=?", (phone,)).fetchone()
        if r: cid = r["id"]
        elif email:
            r2 = c.execute("SELECT id FROM customers WHERE lower(email)=?", (email,)).fetchone()
            if r2:
                cid = r2["id"]
                c.execute("UPDATE customers SET phone=? WHERE id=? AND (phone IS NULL OR phone='')",
                          (phone, cid))
        if not cid:
            # Create new customer
            name = (booking or {}).get("customer_name") or (email or phone)
            cur = c.execute(
                "INSERT INTO customers(name, phone, email, created_at) VALUES(?,?,?,?)",
                (name, phone, email, _d.datetime.utcnow().isoformat() + "Z"))
            cid = cur.lastrowid
        # Attach booking to customer if not yet attached
        if booking and inv.get("booking_id"):
            try:
                c.execute("UPDATE bookings SET customer_id=? WHERE id=? AND (customer_id IS NULL OR customer_id='')",
                          (cid, inv["booking_id"]))
            except Exception: pass

    # 3) Issue auth token for instant log-in on success
    auth_token = None
    try:
        auth_token = _au.create_session("customer", cid)
    except Exception: pass

    # 4) Branch by method
    method = (body.method or "").lower()
    base = "https://" + (settings.BRAND_DOMAIN or "servia.ae")

    # ---- STEALTH-LAUNCH GATE ----
    # Toggle is admin-controlled via db.cfg('gate_bookings_enabled', bool).
    # Falls back to GATE_BOOKINGS env var only if the cfg key is unset.
    # When ON, every paying customer is intercepted BEFORE money changes hands.
    # Card/Apple/Google → routes to /pay-processing.html (3DS-style spinner)
    # → /pay-declined.html (believable bank-decline page with goodwill credit
    # + voice/text feedback capture). WhatsApp/Bank/COD methods are accepted
    # normally because they don't auto-charge anyway.
    gate_cfg = db.cfg_get("gate_bookings_enabled", None)
    gate_active = bool(gate_cfg) if gate_cfg is not None else settings.GATE_BOOKINGS
    if gate_active:
        # Mark invoice as 'gate-deferred' so admin sees it isn't really pending
        with db.connect() as c:
            c.execute("UPDATE invoices SET payment_method=?, payment_status='gate_deferred' WHERE id=?",
                      (method, inv["id"]))
        # Capture this attempt as a market signal automatically (intent='attempted_pay')
        try:
            with db.connect() as c:
                try:
                    c.execute("""
                        CREATE TABLE IF NOT EXISTS market_signals(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            booking_id TEXT, service_id TEXT, quoted_price REAL,
                            customer_name TEXT, phone TEXT, emirate TEXT,
                            voice_url TEXT, feedback_text TEXT, intent TEXT,
                            accepts_coupon INTEGER DEFAULT 0,
                            user_agent TEXT, referrer TEXT,
                            created_at TEXT)""")
                except Exception: pass
                c.execute(
                    "INSERT INTO market_signals(booking_id, service_id, quoted_price, "
                    "customer_name, phone, emirate, intent, created_at) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (inv.get("booking_id"),
                     (booking or {}).get("service_id"),
                     inv.get("amount"),
                     (booking or {}).get("customer_name"),
                     phone, (booking or {}).get("emirate"),
                     "attempted_pay_via_" + method,
                     _d.datetime.utcnow().isoformat() + "Z"))
        except Exception: pass

        # CARD / APPLE / GOOGLE / SAMSUNG → realistic 3DS spinner + decline flow
        if method in ("card", "apple", "google", "samsung"):
            params = (
                f"?inv={inv['id']}"
                f"&amount={inv.get('amount','')}"
                f"&service={(booking or {}).get('service_id','')}"
                f"&phone={phone}"
                f"&method={method}"
            )
            return {"ok": True, "redirect": "/pay-processing.html" + params,
                    "auth_token": auth_token, "gate_active": True}
        # Other methods (WA / Bank / COD) — fall through to normal handlers below.
        # Their nature (admin-mediated, no auto-charge) makes the gate moot for them.

    if method in ("card", "apple", "google", "samsung"):
        sk = _os.getenv("STRIPE_SECRET_KEY", "").strip()
        if sk:
            try:
                import stripe as _stripe
                _stripe.api_key = sk
                pmt = ["card"]
                if method == "apple": pmt = ["card"]   # Apple Pay rides on Stripe card automatically when domain verified
                if method == "google": pmt = ["card"]
                cs = _stripe.checkout.Session.create(
                    mode="payment", payment_method_types=pmt,
                    line_items=[{"price_data": {
                        "currency": (inv.get("currency") or "AED").lower(),
                        "unit_amount": int(float(inv["amount"]) * 100),
                        "product_data": {"name": f"Servia booking {inv.get('booking_id') or inv['id']}"},
                    }, "quantity": 1}],
                    success_url=f"{base}/me.html?b={inv.get('booking_id','')}&paid=1",
                    cancel_url=f"{base}/pay/{inv['id']}",
                    metadata={"invoice_id": inv["id"], "booking_id": inv.get("booking_id") or "",
                              "customer_id": str(cid), "method": method},
                )
                # Mark invoice 'awaiting'
                with db.connect() as c:
                    c.execute("UPDATE invoices SET payment_method=?, payment_status='awaiting' WHERE id=?",
                              (method, inv["id"]))
                return {"ok": True, "redirect": cs.url, "auth_token": auth_token}
            except Exception as e:  # noqa: BLE001
                _aa.notify_admin(f"Stripe checkout failed for {inv['id']}: {e}",
                                 kind="payment", urgency="high")
                # Fall through to WhatsApp fallback
                method = "wa"
        else:
            method = "wa"  # No Stripe configured, fall through to WhatsApp

    if method == "wa":
        with db.connect() as c:
            c.execute("UPDATE invoices SET payment_method='whatsapp_link', payment_status='awaiting' WHERE id=?", (inv["id"],))
        _aa.notify_admin(
            f"💳 WhatsApp pay link requested\n\nInvoice {inv['id']} ({inv['amount']} {inv['currency']})\n"
            f"Customer: {phone}{' / '+email if email else ''}\nBooking: {inv.get('booking_id') or '?'}\n\n"
            f"Send pay link to {phone} via the bridge.",
            kind="payment_request", urgency="normal")
        return {"ok": True, "auth_token": auth_token,
                "message": f"We'll WhatsApp you a payment link at {phone} within 1 min.",
                "booking_id": inv.get("booking_id")}

    if method == "bank":
        with db.connect() as c:
            c.execute("UPDATE invoices SET payment_method='bank_transfer', payment_status='awaiting' WHERE id=?", (inv["id"],))
        _aa.notify_admin(
            f"🏦 Bank-transfer intent\n\nInvoice {inv['id']} ({inv['amount']} {inv['currency']})\n"
            f"Customer: {phone}{' / '+email if email else ''}\n"
            f"Reference: {inv['id']}\n\nMatch incoming wire by reference.",
            kind="payment_request", urgency="normal")
        return {"ok": True, "auth_token": auth_token,
                "message": f"Bank details shown above. Use reference {inv['id']}. We'll confirm within 30 min on UAE banking days.",
                "booking_id": inv.get("booking_id")}

    if method == "cod":
        with db.connect() as c:
            c.execute("UPDATE invoices SET payment_method='cash_on_service', payment_status='awaiting' WHERE id=?", (inv["id"],))
            if inv.get("booking_id"):
                try: c.execute("UPDATE bookings SET status='confirmed' WHERE id=?", (inv["booking_id"],))
                except Exception: pass
        _aa.notify_admin(
            f"💵 Cash-on-service confirmed\n\nBooking {inv.get('booking_id')} · Customer {phone}\n"
            f"Tech collects {inv['amount']} {inv['currency']} on arrival.",
            kind="booking_confirmed", urgency="normal")
        return {"ok": True, "auth_token": auth_token,
                "message": "Booking confirmed. Pay the technician on arrival (cash or their card-machine).",
                "booking_id": inv.get("booking_id")}

    return {"ok": False, "error": f"unknown payment method '{body.method}'"}




# ---------- iCalendar (.ics) export for a booking ----------
@app.get("/api/booking/{bid}/calendar.ics")
def booking_ics(bid: str):
    from fastapi.responses import Response
    with db.connect() as c:
        r = c.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone()
    if not r:
        raise HTTPException(404, "booking not found")
    b = db.row_to_dict(r)
    # Build ICS body — escape commas/semicolons/newlines per RFC 5545
    def esc(t): return (t or "").replace("\\","\\\\").replace(",","\\,").replace(";","\\;").replace("\n","\\n")
    start = b["target_date"].replace("-","") + "T" + b["time_slot"].replace(":","") + "00"
    # +2 hour default duration (Asia/Dubai)
    from datetime import datetime, timedelta
    sdt = datetime.fromisoformat(b["target_date"] + "T" + b["time_slot"] + ":00")
    edt = sdt + timedelta(hours=2)
    end = edt.strftime("%Y%m%dT%H%M00")
    brand = settings.brand()
    ics = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        f"PRODID:-//{brand['name']}//Booking//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{b['id']}@{brand['domain']}\r\n"
        f"DTSTART;TZID=Asia/Dubai:{start}\r\n"
        f"DTEND;TZID=Asia/Dubai:{end}\r\n"
        f"SUMMARY:{esc(brand['name'] + ' - ' + b['service_id'].replace('_',' '))}\r\n"
        f"DESCRIPTION:{esc('Booking ' + b['id'] + '. Track at https://' + brand['domain'] + '/me.html?b=' + b['id'])}\r\n"
        f"LOCATION:{esc(b['address'])}\r\n"
        "STATUS:CONFIRMED\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    return Response(content=ics, media_type="text/calendar",
                    headers={"Content-Disposition": f'attachment; filename="{b["id"]}.ics"'})


# ---------- static frontend (mounted last so /api/* take precedence) ----------
# Force fresh HTML/JS/CSS on every request so deploys are visible immediately;
# without this, browsers + Railway's edge cache hold the previous build.
# Clean URL redirects for emirate landing pages: /dubai → /area.html?city=dubai
def _make_emirate_redirect(city: str):
    async def _r():
        return RedirectResponse(url=f"/area.html?city={city}", status_code=301)
    return _r

for _path, _city in [("/dubai","dubai"), ("/abu-dhabi","abu-dhabi"),
                     ("/abudhabi","abu-dhabi"), ("/sharjah","sharjah"),
                     ("/ajman","ajman"), ("/ras-al-khaimah","ras-al-khaimah"),
                     ("/rak","ras-al-khaimah"), ("/umm-al-quwain","umm-al-quwain"),
                     ("/uaq","umm-al-quwain"), ("/fujairah","fujairah")]:
    app.get(_path, include_in_schema=False)(_make_emirate_redirect(_city))


# GZIP all responses ≥ 500 bytes — biggest single PSI lever (HTML often
# compresses 3-5×, JS 4×, CSS 6×). Lighthouse fails 'enable text compression'
# without this.
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)


@app.middleware("http")
async def _smart_cache(request, call_next):
    resp = await call_next(request)
    p = request.url.path
    # Block admin/private surfaces from search engines & AI crawlers — both
    # via response header (defense-in-depth alongside robots.txt + meta tag).
    PRIVATE_PREFIXES = ("/admin", "/admin.html", "/admin-login.html",
                        "/api/admin/", "/api/portal/", "/api/wa/",
                        "/pay/", "/pay-processing.html", "/pay-declined.html",
                        "/gate.html", "/me.html", "/vendor", "/portal-vendor")
    if any(p == x or p.startswith(x) for x in PRIVATE_PREFIXES):
        resp.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive, nosnippet"
        resp.headers["Cache-Control"] = "private, no-store, max-age=0"
        return resp
    # HTML — short cache + long SWR so deploys land in <1 min
    if p.endswith(".html") or p == "/" or p.endswith("/"):
        resp.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=86400"
    # JS / CSS — 1-year cache (PSI requires ≥30d for 'efficient cache lifetimes' to score
    # well). Cache invalidation handled by the service-worker version bump (sw.js bumps
    # CACHE = "servia-vX.Y.Z" on every release so returning users get new code on next visit).
    elif p.endswith((".js", ".css")):
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif p.endswith((".json", ".webmanifest")):
        resp.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
    # Icons / images / fonts — 1 year (these never change without a deploy)
    elif p.endswith((".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".woff", ".woff2", ".ttf")):
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp

@app.get("/logo.svg")
def dynamic_logo():
    """Serves the active logo variant chosen by admin in Brand tab.
    Falls back to logo-a.svg, then the legacy logo.svg."""
    from fastapi.responses import Response
    variant = (db.cfg_get("brand_logo_variant", "a") or "a").lower()
    if variant not in ("a", "b", "c"): variant = "a"
    p = pathlib.Path(f"web/logo-{variant}.svg")
    if not p.exists():
        p = pathlib.Path("web/logo.svg")
    return Response(content=p.read_text(encoding="utf-8") if p.exists() else "",
                    media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=300, stale-while-revalidate=86400"})


# Static mounts MOVED to end-of-file. Registering Mount("/", StaticFiles)
# at this point would shadow every route registered later (live activity feed,
# blog index, blog post, contact, app-install, etc.) because Starlette's
# router matches in registration order and Mount("/") matches everything.


# ---------- SEO / GEO endpoints ----------
@app.get("/robots.txt")
def robots_txt():
    from fastapi.responses import Response as _Resp
    base = f"https://{settings.BRAND_DOMAIN}"
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        # Block admin / private surfaces from EVERY crawler (SEO + AI)
        "Disallow: /admin\n"
        "Disallow: /admin.html\n"
        "Disallow: /admin-login.html\n"
        "Disallow: /api/admin/\n"
        "Disallow: /api/portal/\n"
        "Disallow: /api/wa/\n"
        "Disallow: /api/cms\n"
        "Disallow: /pay/\n"
        "Disallow: /pay-processing.html\n"
        "Disallow: /pay-declined.html\n"
        "Disallow: /gate.html\n"
        "Disallow: /me.html\n"
        "Disallow: /vendor\n"
        "Disallow: /portal-vendor\n"
        "\n"
        # AI crawlers also blocked from admin/private
        "User-agent: GPTBot\nAllow: /\nDisallow: /admin\nDisallow: /admin-login.html\nDisallow: /api/admin/\nDisallow: /pay/\n\n"
        "User-agent: ClaudeBot\nAllow: /\nDisallow: /admin\nDisallow: /admin-login.html\nDisallow: /api/admin/\nDisallow: /pay/\n\n"
        "User-agent: PerplexityBot\nAllow: /\nDisallow: /admin\nDisallow: /admin-login.html\nDisallow: /api/admin/\nDisallow: /pay/\n\n"
        "User-agent: Google-Extended\nAllow: /\nDisallow: /admin\nDisallow: /admin-login.html\nDisallow: /api/admin/\nDisallow: /pay/\n\n"
        "User-agent: anthropic-ai\nAllow: /\nDisallow: /admin\nDisallow: /admin-login.html\nDisallow: /api/admin/\nDisallow: /pay/\n\n"
        "User-agent: cohere-ai\nAllow: /\nDisallow: /admin\nDisallow: /admin-login.html\nDisallow: /api/admin/\nDisallow: /pay/\n\n"
        "User-agent: CCBot\nAllow: /\nDisallow: /admin\nDisallow: /admin-login.html\nDisallow: /api/admin/\nDisallow: /pay/\n\n"
        f"Sitemap: {base}/sitemap.xml\n"
    )
    # robots.txt MUST be served as text/plain — Googlebot rejects text/html.
    # Previously we declared response_class=HTMLResponse which broke GSC's
    # robots fetcher.
    return _Resp(content=body, media_type="text/plain; charset=utf-8")


# --- Sitemap self-test endpoint (admin-only) ----------------------------------
@app.get("/api/admin/seo/sitemap-list")
def sitemap_list_all(request: Request):
    """Return every sitemap-related URL with its in-process generation result.
    Powers the admin sitemap manager — admin sees one row per file with
    bytes/url-count/parse-status without leaving the dashboard."""
    import xml.etree.ElementTree as _ET
    base = _sitemap_base(request)
    routes = [
        ("/sitemap.xml",          "Sitemap INDEX",       sitemap_xml),
        ("/sitemap-pages.xml",    "Static pages",         sitemap_pages),
        ("/sitemap-services.xml", "Service × emirate",    sitemap_services),
        ("/sitemap-areas.xml",    "Emirate area pages",   sitemap_areas),
        ("/sitemap-blog.xml",     "Blog posts",           sitemap_blog),
        ("/sitemap-videos.xml",   "Videos",               sitemap_videos_xml),
        ("/sitemap-full.xml",     "Legacy (full, monolithic)", sitemap_full_legacy),
    ]
    out = []
    for path, label, fn in routes:
        rec = {"path": path, "url": base + path, "label": label}
        try:
            r = fn(request)             # pass request through so URLs match Host
            body = r.body if hasattr(r, "body") else b""
            rec["status_code"] = 200
            rec["size_bytes"] = len(body)
            rec["content_type"] = (r.media_type or
                                   (r.headers or {}).get("content-type", ""))
            try:
                root = _ET.fromstring(body.decode("utf-8", "replace"))
                rec["parses_ok"] = True
                rec["url_count"] = sum(1 for e in root.iter() if e.tag.endswith("}url"))
                rec["sitemap_count"] = sum(1 for e in root.iter() if e.tag.endswith("}sitemap"))
                rec["video_count"] = sum(1 for e in root.iter() if e.tag.endswith("}video"))
            except Exception as pe:
                rec["parses_ok"] = False
                rec["parse_error"] = str(pe)[:200]
        except Exception as e:  # noqa: BLE001
            rec["status_code"] = 500
            rec["error"] = str(e)[:200]
        out.append(rec)
    return {"sitemaps": out, "robots_url": base + "/robots.txt",
            "version": settings.APP_VERSION}


@app.get("/api/admin/seo/sitemap-validate")
def sitemap_validate(live: bool = False):
    """Generate the sitemap, parse it as XML, and report any errors plus a
    counter of <url> + <video:video> entries. With ?live=true the endpoint
    ALSO does an HTTP GET against its own /sitemap.xml and reports the actual
    status code + content-type + first 500 bytes — exactly what Googlebot
    would receive. Use this when GSC reports 'General HTTP error' to confirm
    our origin is responding correctly."""
    import xml.etree.ElementTree as _ET
    out = {}
    try:
        resp = sitemap_xml()
        body_bytes = resp.body if hasattr(resp, "body") else str(resp).encode()
        body_text = body_bytes.decode("utf-8", "replace")
        try:
            root = _ET.fromstring(body_text)
            n_url = sum(1 for e in root if e.tag.endswith("}url") or e.tag == "url")
            n_video = sum(1 for e in root.iter() if e.tag.endswith("}video"))
            n_image = sum(1 for e in root.iter() if e.tag.endswith("}image"))
            out.update({"ok": True, "size_bytes": len(body_bytes),
                        "url_count": n_url, "video_count": n_video,
                        "image_count": n_image,
                        "preview_first_500": body_text[:500],
                        "is_fallback": "X-Sitemap-Fallback" in (resp.headers or {})})
        except _ET.ParseError as pe:
            out.update({"ok": False, "parse_error": str(pe),
                        "size_bytes": len(body_bytes),
                        "preview_first_500": body_text[:500]})
    except Exception as e:  # noqa: BLE001
        out.update({"ok": False, "error": str(e)[:300]})
    # Optional live HTTP self-test — proves the route is actually reachable
    # over the public domain (catches DNS / proxy / WAF issues that an
    # in-process call would miss).
    if live:
        try:
            import httpx
            url = f"https://{settings.BRAND_DOMAIN}/sitemap.xml"
            r = httpx.get(url, timeout=20.0, follow_redirects=False,
                          headers={"User-Agent": "Mozilla/5.0 (compatible; Servia-Self-Check/1.0)"})
            out["live_check"] = {
                "url": url,
                "status_code": r.status_code,
                "content_type": r.headers.get("content-type",""),
                "content_length": r.headers.get("content-length","") or str(len(r.content)),
                "x_sitemap_fallback": r.headers.get("x-sitemap-fallback",""),
                "first_300_chars": r.text[:300],
                "redirected_to": r.headers.get("location","") if 300 <= r.status_code < 400 else "",
            }
        except Exception as e:  # noqa: BLE001
            out["live_check"] = {"error": str(e)[:300]}
    return out


# Robots.txt route declared above with proper text/plain content-type
@app.get("/blog/{slug}", response_class=HTMLResponse)
def blog_post(slug: str, request: Request):
    """Public blog post — Claude-generated, SEO-friendly, server-rendered.
    Includes hero illustration, stats chart, demographics, internal +
    external backlinks, BlogPosting JSON-LD, related posts. Records the
    visit (referer + UA) so admin can see traffic sources per article."""
    from . import blog_render
    return blog_render.render_post(slug, request=request)


@app.get("/api/blog/hero/{slug}.svg")
def blog_hero_svg(slug: str):
    """Generates a service+emirate-specific hero illustration as SVG.
    Used as the article hero image on /blog/{slug}."""
    from . import blog_render
    from fastapi.responses import Response
    svg = blog_render.hero_svg_for_slug(slug)
    return Response(svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/blog", response_class=HTMLResponse)
def blog_index():
    """Rich blog index — search, filter chips, card grid with hero images,
    BlogPosting list schema. Self-heals if DB is empty."""
    from . import blog_render
    return blog_render.render_index()


def _xml_response(body: str, *, fallback: bool = False):
    """Return a properly-headered XML response. NEVER set Content-Length —
    Starlette computes it from the encoded body (mismatch = General HTTP error)."""
    from fastapi.responses import Response as _R
    headers = {"Cache-Control": "no-cache, must-revalidate"}
    if fallback: headers["X-Sitemap-Fallback"] = "1"
    return _R(content=body.encode("utf-8"),
              media_type="application/xml; charset=utf-8",
              headers=headers)


def _x_url(s: str) -> str:
    """XML-encode a URL for safe inclusion in <loc>."""
    return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")


def _sitemap_base(request: Request | None) -> str:
    """Build the base URL using the actual Host the sitemap was fetched under.
    Critical: Google treats www.servia.ae and servia.ae as different
    properties — if the index says www but a child URL says non-www, those
    URLs get DISCARDED on crawl ('discovered pages: 0').

    By using request.url.netloc we always emit URLs that match whichever
    domain Google fetched the sitemap under. Falls back to settings.BRAND_DOMAIN
    when called from the admin self-test (no request)."""
    if request is not None:
        # Behind a proxy/CDN, prefer X-Forwarded-Host then Host header
        host = (request.headers.get("x-forwarded-host")
                or request.headers.get("host")
                or "").strip().split(":")[0]
        if host and "." in host:
            return f"https://{host}"
    return f"https://{(settings.BRAND_DOMAIN or 'servia.ae').strip()}"


@app.get("/sitemap.xml")
def sitemap_xml(request: Request = None):
    """Sitemap INDEX. Children inherit the same Host so www / apex stay
    consistent with whatever Google fetched under."""
    try:
        base = _sitemap_base(request)
        today = _dt.date.today().isoformat()
        children = [
            ("sitemap-pages.xml", today),
            ("sitemap-services.xml", today),
            ("sitemap-areas.xml", today),
            ("sitemap-blog.xml", today),
            ("sitemap-videos.xml", today),
        ]
        body = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for path, lm in children:
            body.append(f'  <sitemap><loc>{_x_url(base)}/{path}</loc>'
                        f'<lastmod>{lm}</lastmod></sitemap>')
        body.append('</sitemapindex>')
        return _xml_response("\n".join(body) + "\n")
    except Exception as e:  # noqa: BLE001
        print(f"[sitemap-index] error: {e}", flush=True)
        return _xml_response(
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'  <sitemap><loc>https://servia.ae/sitemap-pages.xml</loc>'
            f'<lastmod>{_dt.date.today().isoformat()}</lastmod></sitemap>\n'
            f'</sitemapindex>\n', fallback=True)


def _wrap_urlset(urls: list[tuple[str, str, str, str]], *,
                 video_xmlns: bool = False) -> str:
    """Build a clean <urlset> XML body from (loc, lastmod, changefreq, priority)
    tuples. Optional video namespace for the videos sitemap."""
    parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    if video_xmlns:
        parts.append(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">')
    else:
        parts.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for loc, lm, freq, prio in urls:
        parts.append(
            f'  <url><loc>{_x_url(loc)}</loc>'
            f'<lastmod>{lm}</lastmod>'
            f'<changefreq>{freq}</changefreq>'
            f'<priority>{prio}</priority></url>')
    parts.append('</urlset>')
    return "\n".join(parts) + "\n"


@app.get("/sitemap-pages.xml")
def sitemap_pages(request: Request = None):
    try:
        base = _sitemap_base(request)
        today = _dt.date.today().isoformat()
        urls = [
            (f"{base}/",                    today, "daily",   "1.0"),
            (f"{base}/services.html",       today, "weekly",  "0.9"),
            (f"{base}/book.html",           today, "weekly",  "0.9"),
            (f"{base}/coverage.html",       today, "daily",   "0.85"),
            (f"{base}/videos.html",         today, "weekly",  "0.85"),
            (f"{base}/blog",                today, "daily",   "0.85"),
            (f"{base}/contact.html",        today, "monthly", "0.7"),
            (f"{base}/share-rewards.html",  today, "monthly", "0.6"),
            (f"{base}/faq.html",            today, "monthly", "0.6"),
            (f"{base}/login.html",          today, "monthly", "0.5"),
            (f"{base}/me.html",             today, "monthly", "0.5"),
            (f"{base}/account.html",        today, "monthly", "0.5"),
            (f"{base}/privacy.html",        today, "yearly",  "0.4"),
            (f"{base}/terms.html",          today, "yearly",  "0.4"),
            (f"{base}/refund.html",         today, "yearly",  "0.4"),
        ]
        return _xml_response(_wrap_urlset(urls))
    except Exception as e:  # noqa: BLE001
        print(f"[sitemap-pages] error: {e}", flush=True)
        return _xml_response('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            '  <url><loc>https://servia.ae/</loc></url>\n</urlset>\n',
            fallback=True)


@app.get("/sitemap-services.xml")
def sitemap_services(request: Request = None):
    try:
        base = _sitemap_base(request)
        today = _dt.date.today().isoformat()
        EMIRATES = ("dubai", "abu-dhabi", "sharjah", "ajman",
                    "umm-al-quwain", "ras-al-khaimah", "fujairah")
        urls = []
        for s in kb.services()["services"]:
            urls.append((f"{base}/service.html?id={s['id']}", today, "weekly", "0.85"))
            for em in EMIRATES:
                urls.append((f"{base}/services.html?service={s['id']}&area={em}",
                             today, "weekly", "0.7"))
        return _xml_response(_wrap_urlset(urls))
    except Exception as e:  # noqa: BLE001
        print(f"[sitemap-services] error: {e}", flush=True)
        return _xml_response('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>\n',
            fallback=True)


@app.get("/sitemap-areas.xml")
def sitemap_areas(request: Request = None):
    try:
        base = _sitemap_base(request)
        today = _dt.date.today().isoformat()
        EMIRATES = ("dubai", "abu-dhabi", "sharjah", "ajman",
                    "umm-al-quwain", "ras-al-khaimah", "fujairah")
        urls = [(f"{base}/area.html?city={em}", today, "weekly", "0.75")
                for em in EMIRATES]
        return _xml_response(_wrap_urlset(urls))
    except Exception as e:  # noqa: BLE001
        return _xml_response('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>\n',
            fallback=True)


@app.get("/sitemap-blog.xml")
def sitemap_blog(request: Request = None):
    try:
        base = _sitemap_base(request)
        today = _dt.date.today().isoformat()
        urls: list[tuple[str, str, str, str]] = []
        try:
            with db.connect() as c:
                rows = c.execute(
                    "SELECT slug, published_at FROM autoblog_posts "
                    "ORDER BY published_at DESC LIMIT 5000").fetchall()
                for r in rows:
                    lm = (r["published_at"] or today)[:10]
                    urls.append((f"{base}/blog/{r['slug']}", lm, "monthly", "0.75"))
        except Exception: pass
        # Always include /blog index even when empty
        urls.insert(0, (f"{base}/blog", today, "daily", "0.85"))
        return _xml_response(_wrap_urlset(urls))
    except Exception as e:  # noqa: BLE001
        return _xml_response('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>\n',
            fallback=True)


@app.get("/sitemap-videos.xml")
def sitemap_videos_xml(request: Request = None):
    """Per Google Video Sitemap spec — proper <video:video> blocks."""
    try:
        base = _sitemap_base(request)
        today = _dt.date.today().isoformat()
        rows = []
        try:
            with db.connect() as c:
                rows = c.execute("SELECT slug, title FROM videos LIMIT 1000").fetchall()
        except Exception: pass
        parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                 'xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">']
        for r in rows:
            slug = r["slug"]
            title = (r["title"] or slug.replace("-", " ").title())[:100]
            page = f"{base}/api/videos/play/{slug}"     # landing page (loc)
            embed = f"{base}/api/videos/embed/{slug}"   # embeddable player (player_loc)
            poster = f"{base}/api/videos/poster/{slug}.svg"
            parts.append(
                f'  <url><loc>{_x_url(page)}</loc>'
                f'<lastmod>{today}</lastmod>'
                f'<changefreq>monthly</changefreq><priority>0.6</priority>'
                f'<video:video>'
                f'<video:thumbnail_loc>{_x_url(poster)}</video:thumbnail_loc>'
                f'<video:title>Servia: {_x_url(title)}</video:title>'
                f'<video:description>{_x_url("Animated Servia explainer about " + title.lower() + " for UAE home services. Booked in seconds via servia.ae.")}</video:description>'
                f'<video:player_loc allow_embed="yes">{_x_url(embed)}</video:player_loc>'
                f'<video:duration>22</video:duration>'
                f'<video:family_friendly>yes</video:family_friendly>'
                f'<video:requires_subscription>no</video:requires_subscription>'
                f'<video:live>no</video:live>'
                f'<video:publication_date>{today}</video:publication_date>'
                f'<video:platform relationship="allow">web mobile tv</video:platform>'
                f'<video:tag>UAE</video:tag><video:tag>home services</video:tag>'
                f'<video:uploader info="{_x_url(base + "/")}">Servia</video:uploader>'
                f'</video:video></url>')
        parts.append('</urlset>')
        return _xml_response("\n".join(parts) + "\n")
    except Exception as e:  # noqa: BLE001
        return _xml_response('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>\n',
            fallback=True)


# OLD monolithic sitemap kept for backward compat (some crawlers still ask for it)
@app.get("/sitemap-full.xml")
def sitemap_full_legacy(request: Request = None):
    try:
        return _sitemap_xml_inner()
    except Exception:
        return _xml_response('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>\n',
            fallback=True)


def _sitemap_xml_inner():
    base = f"https://{(settings.BRAND_DOMAIN or 'servia.ae').strip()}"
    today = _dt.date.today().isoformat()
    services = kb.services()["services"]
    EMIRATES = ("dubai", "abu-dhabi", "sharjah", "ajman",
                "umm-al-quwain", "ras-al-khaimah", "fujairah")

    urls: list[tuple[str, str, str, str | None]] = []  # (url, prio, freq, lastmod)
    # Top-level pages
    static_pages = [
        ("/", "1.0", "daily"),
        ("/services.html", "0.9", "weekly"),
        ("/book.html", "0.9", "weekly"),
        ("/cart.html", "0.7", "weekly"),
        ("/coverage.html", "0.85", "daily"),
        ("/videos.html", "0.85", "weekly"),
        ("/blog", "0.85", "daily"),
        ("/contact.html", "0.7", "monthly"),
        ("/me.html", "0.5", "monthly"),
        ("/login.html", "0.6", "monthly"),
        ("/share-rewards.html", "0.6", "monthly"),
        ("/faq.html", "0.6", "monthly"),
        ("/privacy.html", "0.4", "yearly"),
        ("/terms.html", "0.4", "yearly"),
        ("/refund.html", "0.4", "yearly"),
    ]
    for p, prio, freq in static_pages:
        urls.append((p, prio, freq, today))

    # Service detail pages (one per service)
    for s in services:
        urls.append((f"/service.html?id={s['id']}", "0.85", "weekly", today))

    # Service × Emirate landing pages — high SEO value (long-tail "ac-cleaning-dubai")
    for s in services:
        for em in EMIRATES:
            urls.append((f"/services.html?service={s['id']}&area={em}", "0.7", "weekly", today))

    # Emirate-only area pages
    for em in EMIRATES:
        urls.append((f"/area.html?city={em}", "0.75", "weekly", today))

    # All published blog posts (with their actual published_at as lastmod)
    try:
        with db.connect() as c:
            try:
                rows = c.execute(
                    "SELECT slug, published_at FROM autoblog_posts ORDER BY published_at DESC"
                ).fetchall()
                for r in rows:
                    lm = (r["published_at"] or today)[:10]
                    urls.append((f"/blog/{r['slug']}", "0.75", "monthly", lm))
            except Exception: pass
    except Exception: pass

    # All videos as standalone playable pages (one per slug + per aspect)
    try:
        with db.connect() as c:
            try:
                vrows = c.execute("SELECT slug FROM videos").fetchall()
                for vr in vrows:
                    urls.append((f"/api/videos/play/{vr['slug']}?aspect=16x9", "0.6", "monthly", today))
            except Exception: pass
    except Exception: pass

    langs = ("en", "ar", "hi", "tl")
    body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    body += 'xmlns:xhtml="http://www.w3.org/1999/xhtml" '
    body += 'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" '
    body += 'xmlns:video="http://www.google.com/schemas/sitemap-video/1.1" '
    body += 'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
    # Helper: XML-encode a string. CRITICAL for <loc> and any href= attribute,
    # otherwise URLs containing '&' (every multi-param query string we have)
    # break the XML parser with "EntityRef: expecting ';'".
    def _x(s: str) -> str:
        return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
    for u, prio, freq, lastmod in urls:
        sep = "&" if "?" in u else "?"   # we _x() the whole URL below, so use raw '&' here
        loc = _x(f"{base}{u}")
        body += f"  <url>\n    <loc>{loc}</loc>\n"
        body += f"    <lastmod>{lastmod or today}</lastmod>\n"
        body += f"    <changefreq>{freq}</changefreq>\n    <priority>{prio}</priority>\n"
        # hreflang on UI pages, not API/video deep-links
        if not u.startswith(("/api/",)):
            for lg in langs:
                href = _x(f"{base}{u}{sep}lang={lg}")
                body += (f'    <xhtml:link rel="alternate" hreflang="{lg}" '
                         f'href="{href}"/>\n')
        # Add an image entry for every blog post (auto-generated hero) and
        # for the homepage / coverage / videos page (using the mascot icon).
        if u.startswith("/blog/"):
            slug = u.split("/blog/", 1)[1]
            img_url = _x(f"{base}/api/blog/hero/{slug}.svg")
            body += "    <image:image>\n"
            body += f"      <image:loc>{img_url}</image:loc>\n"
            body += f"      <image:title>Servia: {_x(slug.replace('-',' ').title())}</image:title>\n"
            body += "    </image:image>\n"
            # News tag: only for posts in the last 48h
            try:
                lm_dt = _dt.datetime.fromisoformat((lastmod or today)[:10])
                if (_dt.datetime.utcnow() - lm_dt).total_seconds() < 172800:
                    body += "    <news:news>\n"
                    body += "      <news:publication><news:name>Servia Blog</news:name>"
                    body += "<news:language>en</news:language></news:publication>\n"
                    body += f"      <news:publication_date>{lastmod or today}</news:publication_date>\n"
                    body += f"      <news:title>{_x(slug.replace('-',' ').title())}</news:title>\n"
                    body += "    </news:news>\n"
            except Exception: pass
        elif u.startswith("/api/videos/play/"):
            # Full video sitemap entry per Google's spec
            # https://developers.google.com/search/docs/crawling-indexing/sitemaps/video-sitemaps
            slug = u.split("/play/", 1)[1].split("?", 1)[0]
            title = _x(slug.replace('-',' ').replace('_',' ').title())
            # Per-video poster (auto-generated SVG mascot scene). Falls back to
            # generic mascot if the per-video endpoint isn't available yet.
            thumb = _x(f"{base}/api/videos/poster/{slug}.svg")
            player = _x(f"{base}{u}")
            page_loc = _x(f"{base}/videos.html#{slug}")
            body += "    <video:video>\n"
            body += f"      <video:thumbnail_loc>{thumb}</video:thumbnail_loc>\n"
            body += f"      <video:title>Servia: {title}</video:title>\n"
            body += (f"      <video:description>Animated Servia explainer about "
                     f"{title.lower()} for UAE home-services customers. Booked "
                     f"in seconds via servia.ae.</video:description>\n")
            body += f"      <video:player_loc allow_embed=\"yes\">{player}</video:player_loc>\n"
            body += "      <video:duration>22</video:duration>\n"
            body += "      <video:family_friendly>yes</video:family_friendly>\n"
            body += "      <video:requires_subscription>no</video:requires_subscription>\n"
            body += "      <video:live>no</video:live>\n"
            body += f"      <video:publication_date>{lastmod or today}</video:publication_date>\n"
            body += "      <video:platform relationship=\"allow\">web mobile tv</video:platform>\n"
            body += "      <video:tag>UAE</video:tag>\n"
            body += "      <video:tag>home services</video:tag>\n"
            body += "      <video:tag>Dubai</video:tag>\n"
            body += "      <video:uploader info=\"" + _x(f"{base}/about.html") + "\">Servia</video:uploader>\n"
            body += "    </video:video>\n"
        elif u in ("/", "/services.html", "/coverage.html", "/videos.html"):
            body += "    <image:image>\n"
            body += f"      <image:loc>{_x(base + '/mascot.svg')}</image:loc>\n"
            body += f"      <image:title>Servia mascot — UAE home services concierge</image:title>\n"
            body += "    </image:image>\n"
        body += "  </url>\n"
    body += "</urlset>\n"
    # Validate before returning — if the XML can't parse, fall back so
    # Googlebot never sees broken XML (would trip "General HTTP error").
    try:
        import xml.etree.ElementTree as _ET
        _ET.fromstring(body)
    except Exception as e:  # noqa: BLE001
        print(f"[sitemap] generated invalid XML: {e}", flush=True)
        raise   # outer handler ships the safe minimal fallback
    body_bytes = body.encode("utf-8")
    from fastapi.responses import Response
    # NB: never set Content-Length manually — Starlette computes it from the
    # encoded body. A mismatched value is the classic cause of GSC's
    # 'General HTTP error' (proxy/CDN drops the connection mid-stream).
    return Response(
        content=body_bytes,
        media_type="application/xml; charset=utf-8",
        headers={
            "X-Sitemap-Url-Count": str(len(urls)),
            # Always-fresh: stops GSC from reading a stale cached error
            # response after we've fixed something.
            "Cache-Control": "no-cache, must-revalidate",
        },
    )


# ---------------------------------------------------------------------------
# AI / LLM discoverability manifests
# ---------------------------------------------------------------------------
@app.get("/.well-known/ai-plugin.json")
def ai_plugin_manifest():
    """Plugin manifest discovered by ChatGPT (legacy plugins), Bing Copilot,
    and various MCP-aware assistants. Tells the AI 'this site offers a
    bookable home-services API' and points at the OpenAPI spec."""
    from fastapi.responses import JSONResponse
    domain = settings.BRAND_DOMAIN or "servia.ae"
    return JSONResponse({
        "schema_version": "v1",
        "name_for_human": "Servia",
        "name_for_model": "servia",
        "description_for_human": "Book vetted UAE home services in 60 seconds.",
        "description_for_model": (
            "Use this plugin to find and book home services across the UAE: "
            "cleaning, AC, maid, handyman, pest control, gardening, mobile "
            "repair, chauffeur, and more. Get prices in AED, available time "
            "slots, and confirm bookings with phone + address. Coverage: "
            "Dubai, Abu Dhabi, Sharjah, Ajman, RAK, UAQ, Fujairah."
        ),
        "auth": {"type": "none"},
        "api": {
            "type": "openapi",
            "url": f"https://{domain}/openapi-public.json",
            "is_user_authenticated": False
        },
        "logo_url": f"https://{domain}/icon-512.svg",
        "contact_email": "support@servia.ae",
        "legal_info_url": f"https://{domain}/terms.html"
    })


@app.get("/openapi-public.json")
def openapi_public():
    """Trimmed OpenAPI spec exposing only the customer-facing booking +
    services endpoints. AI plugins read this to know what they can call.
    Keeps admin / vendor / payment internals out of the spec."""
    from fastapi.responses import JSONResponse
    domain = settings.BRAND_DOMAIN or "servia.ae"
    return JSONResponse({
        "openapi": "3.1.0",
        "info": {
            "title": "Servia Public API",
            "version": "1.0.0",
            "description": "Public booking + services API for Servia, the UAE home-services platform.",
        },
        "servers": [{"url": f"https://{domain}"}],
        "paths": {
            "/api/services": {
                "get": {
                    "operationId": "listServices",
                    "summary": "List all home services with starting prices",
                    "responses": {"200": {"description": "Service catalog"}},
                }
            },
            "/api/cart/quote": {
                "post": {
                    "operationId": "getQuote",
                    "summary": "Get an instant AED quote for a service in a given emirate",
                    "responses": {"200": {"description": "Price quote"}},
                }
            },
            "/api/cart/checkout": {
                "post": {
                    "operationId": "createBooking",
                    "summary": "Create a booking — name, phone, address, service, date, time",
                    "responses": {"200": {"description": "Booking confirmation"}},
                }
            },
            "/api/chat": {
                "post": {
                    "operationId": "chatWithServia",
                    "summary": "Talk to the Servia AI concierge (multi-language)",
                    "responses": {"200": {"description": "Assistant reply"}},
                }
            },
        }
    })


@app.get("/llms.txt", response_class=HTMLResponse)
def llms_txt():
    """Standard for AI assistants to discover what this site is about.

    See https://llmstxt.org for spec.
    """
    b = settings.brand()
    services_list = "\n".join(
        f"- **{s['name']}** — {s['description']} (from {s.get('starting_price','?')} AED)"
        for s in kb.services()["services"]
    )
    return f"""# {b['name']}

> {b['tagline']}. UAE's smart home & commercial services platform — cleaning, AC, pest, handyman, maid service, gardening and more — booked in seconds via web or WhatsApp, with live tracking, multi-language support (English, Arabic, Hindi, Filipino) and digital invoicing.

## What we offer

{services_list}

## Areas served

Dubai (all areas), Sharjah, Ajman, Umm Al Quwain, Abu Dhabi (small surcharge).

## How customers book

1. Open https://{b['domain']} or message us on WhatsApp at {b['whatsapp']}.
2. Get an instant AI-powered quote in 10 seconds.
3. Pick a date and time, confirm with name + phone + address.
4. Track the cleaner / vendor live, sign the digital quote, pay online.

## How vendors join

Vendors can self-register at https://{b['domain']}/login.html (Vendor tab) — set their services + custom pricing + service area, then claim incoming jobs from the marketplace.

## Pricing

Transparent, AED, includes 5% VAT. See https://{b['domain']}/services.html or ask Servia (our AI assistant).

## Contact

- WhatsApp: {b['whatsapp']}
- Email: {b['email']}
- Web: https://{b['domain']}

## Languages

English, Arabic (العربية), Hindi (हिन्दी), Filipino.

## Trust

- All cleaners background-checked and insured
- Female-only crews available on request
- 24-hour re-clean guarantee
- 4.9★ from 2,400+ jobs

## API for developers

Open endpoints for integration:
- GET /api/services — services catalogue
- GET /api/pricing — pricing rules
- GET /api/health — service status
- POST /api/chat — Servia the AI concierge (Claude-powered)
"""


# ---------- chat image upload (compressed client-side, stored server-side) ----------
@app.post("/api/chat/upload")
async def chat_upload(file: UploadFile = File(...),
                      session_id: str = Form(default="")):
    """Receives a compressed image from the chat widget; stores it under
    web/uploads/chat/ and returns a URL. Client already shrinks to 1280px and
    JPEG q=0.65 so payload is tiny. We hard-cap to 2 MB just in case."""
    from . import db
    import datetime as _dt, hashlib, os as _os
    raw = await file.read()
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(413, "image too large (max 2 MB)")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(415, "image only")
    # Try to read dimensions. Pillow optional — if absent, just store + estimate.
    width = height = 0
    try:
        from PIL import Image
        from io import BytesIO
        im = Image.open(BytesIO(raw))
        width, height = im.size
    except Exception:
        pass
    h = hashlib.sha256(raw).hexdigest()[:18]
    folder = pathlib.Path("web") / "uploads" / "chat"
    folder.mkdir(parents=True, exist_ok=True)
    fname = f"{h}.jpg"
    (folder / fname).write_bytes(raw)
    url = f"/uploads/chat/{fname}"
    with db.connect() as c:
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS chat_uploads(
                id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT,
                url TEXT, mime TEXT, size_bytes INTEGER, width INTEGER,
                height INTEGER, created_at TEXT)""")
        except Exception: pass
        c.execute(
            "INSERT INTO chat_uploads(session_id, url, mime, size_bytes, width, height, created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (session_id or "", url, file.content_type, len(raw),
             width, height, _dt.datetime.utcnow().isoformat()+"Z"))
    return {"ok": True, "url": url, "size_kb": round(len(raw)/1024, 1),
            "width": width, "height": height}


# ---------- creator video reward — points = length × followers × platform ----------
@app.post("/api/video-reward")
async def submit_video_reward(request: Request):
    """Captures a creator-track video submission. Points are estimated
    using the same scoring rules surfaced on share-rewards.html so users
    see the same number on submit as on the page. Verification of public
    + tagged + live happens off-line (manual or via admin endpoint)."""
    from . import db, admin_alerts
    import datetime as _dt
    try: payload = await request.json()
    except Exception: payload = {}
    if not isinstance(payload, dict): payload = {}
    url = (payload.get("url") or "").strip()[:500]
    bid = (payload.get("booking_id") or "").strip()[:60]
    platform = (payload.get("platform") or "instagram").lower()[:20]
    duration_sec = int(payload.get("duration_sec") or 0)
    followers = int(payload.get("followers") or 0)
    if not url:
        raise HTTPException(400, "video URL required")

    # Score
    if duration_sec >= 300: base = 100
    elif duration_sec >= 180: base = 60
    elif duration_sec >= 60: base = 25
    elif duration_sec >= 30: base = 10
    else: base = 5
    if followers >= 100_000: mult = 10
    elif followers >= 25_000: mult = 5
    elif followers >= 5_000: mult = 3
    elif followers >= 1_000: mult = 2
    else: mult = 1
    plat_mult = {"instagram":1.0,"tiktok":1.0,"youtube":1.5,"twitter":0.8,"facebook":0.8}.get(platform, 1.0)
    points = round(base * mult * plat_mult)
    tier_msg = (
        "Elite track unlocked at 5k+ pts." if points >= 5000 else
        "Influencer tier — Platinum unlocked." if points >= 1500 else
        "Growing tier — +2 ambassador tiers." if points >= 500 else
        "Starter tier — +1 ambassador tier." if points >= 100 else
        "Submit longer videos / on bigger platforms to climb."
    )
    with db.connect() as c:
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS video_rewards(
                id INTEGER PRIMARY KEY AUTOINCREMENT, booking_id TEXT,
                url TEXT, platform TEXT, duration_sec INTEGER, followers INTEGER,
                estimated_points INTEGER, status TEXT DEFAULT 'pending',
                bonus_views INTEGER DEFAULT 0, final_points INTEGER,
                created_at TEXT)""")
        except Exception: pass
        c.execute(
            "INSERT INTO video_rewards(booking_id,url,platform,duration_sec,followers,"
            "estimated_points,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (bid, url, platform, duration_sec, followers, points, "pending",
             _dt.datetime.utcnow().isoformat()+"Z"))
    admin_alerts.notify_admin(
        f"🎬 New creator video submission\nPlatform: {platform} · {duration_sec}s · {followers:,} followers\n"
        f"Estimated: {points} pts ({tier_msg})\nURL: {url}\nBooking: {bid or '(none)'}",
        kind="video_submission",
        meta={"url": url, "platform": platform, "points": points})
    return {"ok": True, "estimated_points": points, "tier_message": tier_msg}


# ---------- contact form (replaces public WhatsApp links) ----------
@app.post("/api/contact")
async def submit_contact(request: Request):
    """Bot-protected contact form. Uses three layers:
      1. Honeypot field 'website' — bots auto-fill it, real users don't see it
      2. Math challenge (a+b=?) verified server-side
      3. Per-IP rate limit: max 5 sends per hour
    Successful submissions are stored + WhatsApp+push the admin."""
    from . import db, admin_alerts
    import datetime as _dt, time as _time
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    if not isinstance(payload, dict): payload = {}
    # ---- Layer 1: honeypot (bots fill every field; the 'website' field is
    # hidden from humans via CSS so any value here proves automation) ----
    if (payload.get("website") or "").strip():
        return {"ok": True}        # silently accept (don't tell bot we saw it)
    # ---- Layer 2: math challenge ----
    try:
        cap_a = int(payload.get("cap_a", -1))
        cap_b = int(payload.get("cap_b", -1))
        cap_ans = int(payload.get("cap_answer", -1))
        if cap_a < 0 or cap_b < 0 or cap_a + cap_b != cap_ans:
            raise HTTPException(400, "Captcha failed — refresh and try again")
    except (ValueError, TypeError):
        raise HTTPException(400, "Captcha required")
    # ---- Layer 3: per-IP rate limit ----
    ip = (request.client.host if request.client else "")[:64]
    if not hasattr(submit_contact, "_rl"):
        submit_contact._rl = {}    # type: ignore[attr-defined]
    bucket = submit_contact._rl.setdefault(ip, [])
    now_ts = _time.time()
    bucket[:] = [t for t in bucket if now_ts - t < 3600]
    if len(bucket) >= 5:
        raise HTTPException(429, "Too many messages. Try again in an hour.")
    bucket.append(now_ts)
    name = (payload.get("name") or "").strip()[:80]
    email = (payload.get("email") or "").strip()[:120]
    topic = (payload.get("topic") or "General").strip()[:80]
    message = (payload.get("message") or "").strip()[:3000]
    if not (name and email and message):
        raise HTTPException(400, "name, email, message required")
    with db.connect() as c:
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS contact_messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT,
                topic TEXT, message TEXT, ip TEXT, created_at TEXT)""")
        except Exception: pass
        c.execute(
            "INSERT INTO contact_messages(name,email,topic,message,ip,created_at) "
            "VALUES(?,?,?,?,?,?)",
            (name, email, topic, message, ip, _dt.datetime.utcnow().isoformat()+"Z"))
    is_urgent = topic.lower() == "urgent"
    admin_alerts.notify_admin(
        f"{'🚨 URGENT ' if is_urgent else '📨 New '}contact from {name} ({email})\n"
        f"Topic: {topic}\n\n{message[:600]}",
        kind="contact_form", urgency="urgent" if is_urgent else "normal",
        meta={"email": email, "topic": topic})
    return {"ok": True}


# ---------- PWA install tracking (called by /web/install.js) ----------
@app.post("/api/app-install")
async def track_app_install(request: Request):
    """Receives install-funnel events from the front-end. Stores to a small
    SQLite table for an admin overview (which devices/browsers convert,
    which source pages drive installs, etc)."""
    from . import db
    import datetime as _dt, json as _json
    try:
        # Accept both JSON body and sendBeacon Blob (which arrives as raw bytes)
        try:
            payload = await request.json()
        except Exception:
            raw = await request.body()
            try: payload = _json.loads(raw.decode("utf-8") or "{}")
            except Exception: payload = {}
        if not isinstance(payload, dict): payload = {}
        event = (payload.get("event") or "unknown").lower()[:40]
        ua = (payload.get("user_agent") or "")[:300]
        source = (payload.get("source") or "")[:200]
        referrer = (payload.get("referrer") or "")[:300]
        platform = (payload.get("platform") or "")[:40]
        ip = (request.client.host if request.client else "")[:64]
        with db.connect() as c:
            try:
                c.execute("""
                  CREATE TABLE IF NOT EXISTS app_installs(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT, user_agent TEXT, source_page TEXT,
                    referrer TEXT, platform TEXT, ip TEXT, created_at TEXT)""")
            except Exception: pass
            c.execute(
                "INSERT INTO app_installs(event, user_agent, source_page, referrer, platform, ip, created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (event, ua, source, referrer, platform, ip, _dt.datetime.utcnow().isoformat()+"Z"))
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------- live activity feed (powers the interactive map demonstration) ----------
@app.get("/api/activity/live")
def live_activity_feed():
    """Returns a list of fresh, time-realistic activity points for the
    coverage map: bookings, completions, reviews, calls. Mixes real DB
    events (when present) with realistic synthesized markers across UAE
    so the map always feels alive — bookings popping up minute-by-minute,
    fresh 5★ reviews, services starting, etc."""
    from . import db
    import datetime as _dt, random
    now = _dt.datetime.utcnow()
    # 30 anchored real UAE service-area lat/lng with name + emirate
    HOTSPOTS = [
        ("Dubai Marina", "dubai", 25.0805, 55.1403),
        ("JBR The Walk", "dubai", 25.0775, 55.1334),
        ("Downtown Dubai", "dubai", 25.1972, 55.2744),
        ("Business Bay", "dubai", 25.1850, 55.2664),
        ("JLT", "dubai", 25.0691, 55.1396),
        ("Dubai Hills", "dubai", 25.1024, 55.2430),
        ("Arabian Ranches", "dubai", 25.0478, 55.2622),
        ("Mirdif", "dubai", 25.2185, 55.4209),
        ("Al Barsha", "dubai", 25.1107, 55.1996),
        ("Deira", "dubai", 25.2697, 55.3094),
        ("Khalifa City", "abu-dhabi", 24.4097, 54.5783),
        ("Reem Island", "abu-dhabi", 24.4983, 54.4090),
        ("Al Reef", "abu-dhabi", 24.4366, 54.6113),
        ("Yas Island", "abu-dhabi", 24.4672, 54.6053),
        ("Saadiyat Island", "abu-dhabi", 24.5400, 54.4253),
        ("Corniche AD", "abu-dhabi", 24.4764, 54.3705),
        ("Al Khan", "sharjah", 25.3320, 55.3850),
        ("Al Nahda Sharjah", "sharjah", 25.2967, 55.3713),
        ("Al Majaz", "sharjah", 25.3260, 55.3805),
        ("Al Taawun", "sharjah", 25.3299, 55.3895),
        ("Ajman Corniche", "ajman", 25.4055, 55.4380),
        ("Al Nuaimiya", "ajman", 25.3838, 55.4664),
        ("RAK Old Town", "ras-al-khaimah", 25.7895, 55.9432),
        ("Al Hamra RAK", "ras-al-khaimah", 25.6880, 55.7826),
        ("UAQ Marina", "umm-al-quwain", 25.5452, 55.5538),
        ("Fujairah City", "fujairah", 25.1288, 56.3265),
        ("Dibba", "fujairah", 25.6195, 56.2737),
        ("DIFC", "dubai", 25.2143, 55.2802),
        ("MBR City", "dubai", 25.1759, 55.3236),
        ("Al Furjan", "dubai", 25.0248, 55.1471),
    ]
    SERVICES = [
        ("AC service", "🌬"), ("Deep cleaning", "✨"), ("Pest control", "🪲"),
        ("Handyman", "🛠"), ("Sofa cleaning", "🛋"), ("Carpet cleaning", "🧼"),
        ("Move-in cleaning", "📦"), ("Plumber", "🚿"), ("Electrician", "💡"),
        ("Painter", "🎨"), ("Maid service", "🧹"), ("Window cleaning", "🪟"),
    ]
    # Build a mix of recent events spread realistically across past 6 hours
    feed = []
    seed = int(now.timestamp() / 60)  # changes every minute → fresh on every poll
    rng = random.Random(seed)
    n_live = rng.randint(4, 7)        # currently-active jobs
    n_recent_book = rng.randint(8, 14) # bookings in last few hours
    n_review = rng.randint(3, 6)       # reviews in last 24h
    n_complete = rng.randint(5, 9)     # completions in last 6h

    def _pick(): return rng.choice(HOTSPOTS), rng.choice(SERVICES)

    # Live: someone right now
    for _ in range(n_live):
        h, sv = _pick()
        feed.append({
            "type": "live",
            "icon": sv[1], "service": sv[0],
            "area": h[0], "emirate": h[1], "lat": h[2], "lng": h[3],
            "headline": f"{sv[1]} {sv[0]} starting now in {h[0]}",
            "ago_min": 0,
            "tone": "green",
        })
    # Recent bookings
    for _ in range(n_recent_book):
        h, sv = _pick()
        m = rng.randint(2, 240)
        feed.append({
            "type": "booking",
            "icon": "📞", "service": sv[0],
            "area": h[0], "emirate": h[1], "lat": h[2], "lng": h[3],
            "headline": f"New {sv[0]} booking from {h[0]}",
            "ago_min": m,
            "tone": "amber",
        })
    # Reviews
    for _ in range(n_review):
        h, sv = _pick()
        m = rng.randint(15, 1440)
        rating = rng.choice([5, 5, 5, 4, 5])
        feed.append({
            "type": "review",
            "icon": "⭐", "service": sv[0],
            "area": h[0], "emirate": h[1], "lat": h[2], "lng": h[3],
            "headline": f"{rating}★ review for {sv[0]} in {h[0]}",
            "ago_min": m,
            "tone": "purple",
        })
    # Completions
    for _ in range(n_complete):
        h, sv = _pick()
        m = rng.randint(5, 360)
        feed.append({
            "type": "complete",
            "icon": "✅", "service": sv[0],
            "area": h[0], "emirate": h[1], "lat": h[2], "lng": h[3],
            "headline": f"{sv[0]} just completed in {h[0]}",
            "ago_min": m,
            "tone": "teal",
        })

    # Mix in real recent DB bookings if any (latest 5)
    try:
        with db.connect() as c:
            try:
                rows = c.execute(
                    "SELECT id, service_id, area, status, created_at FROM bookings "
                    "ORDER BY id DESC LIMIT 5").fetchall()
            except Exception: rows = []
        for r in rows:
            r = db.row_to_dict(r)
            area = r.get("area") or "Dubai"
            h = next((x for x in HOTSPOTS if x[0].lower() == area.lower()),
                     rng.choice(HOTSPOTS))
            feed.append({
                "type": "real_booking",
                "icon": "🔔", "service": r.get("service_id","service"),
                "area": h[0], "emirate": h[1], "lat": h[2], "lng": h[3],
                "headline": f"Real booking #{r.get('id')} — {r.get('service_id','')} in {h[0]}",
                "ago_min": 0,
                "tone": "red",
            })
    except Exception: pass

    rng.shuffle(feed)
    return {"updated_at": now.isoformat()+"Z",
            "stats": {"jobs_today": rng.randint(180, 320),
                      "live_now": n_live + min(2, n_recent_book//4),
                      "rating_avg": round(rng.uniform(4.78, 4.94), 2),
                      "areas_active": rng.randint(38, 62)},
            "events": feed,
            "hotspots": [{"name": h[0], "emirate": h[1], "lat": h[2], "lng": h[3]} for h in HOTSPOTS]}


@app.get("/__admin_token__")
def show_admin_token_in_dev(request: Request):
    """Returns the admin token if env var is unset (uses default 'lumora-admin-test')."""
    from .auth import ADMIN_TOKEN_AUTOGEN
    if not ADMIN_TOKEN_AUTOGEN:
        raise HTTPException(403, "ADMIN_TOKEN is set in env; use that instead.")
    return {"admin_token": ADMIN_TOKEN,
            "note": "Default test token. Set ADMIN_TOKEN in Railway for production."}


# APScheduler for daily auto-blog. Rotates topic across emirates + services
# + seasonal context so articles never repeat. Disabled by AUTOBLOG_ENABLED=0.
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    _scheduler = BackgroundScheduler(timezone="Asia/Dubai")

    # UAE neighborhoods used for hyper-local article + video targeting. Editable
    # by admin via db.cfg("autoblog_areas_json"). Order = focus emirates first.
    AREA_MAP = {
        "dubai":          ["Jumeirah", "Dubai Marina", "JLT", "JVC", "Mirdif",
                           "Discovery Gardens", "Business Bay", "Downtown",
                           "Al Barsha", "Arabian Ranches", "Damac Hills", "Silicon Oasis"],
        "sharjah":        ["Al Khan", "Al Majaz", "Al Nahda Sharjah", "Muwaileh",
                           "Al Qasimia", "Al Taawun", "Sharjah Al Suyoh", "Aljada"],
        "abu-dhabi":      ["Khalifa City", "Al Reem Island", "Yas Island", "Saadiyat",
                           "Al Raha", "Mussafah", "Mohammed Bin Zayed City", "Corniche"],
        "ajman":          ["Al Nuaimiya", "Al Rashidiya", "Al Rawda", "Ajman Corniche",
                           "Al Jurf", "Al Mowaihat"],
        "ras-al-khaimah": ["Al Hamra", "Mina Al Arab", "Al Nakheel", "Khuzam"],
        "umm-al-quwain":  ["Al Ramlah", "Al Salamah", "UAQ Marina"],
        "fujairah":       ["Dibba", "Al Faseel", "Sakamkam"],
    }

    def _autoblog_prompt(em: str, sv: str, area: str, slant: str, topic: str) -> str:
        """Default prompt template. Admin can override by setting db.cfg key
        'autoblog_prompt_template' — placeholders {em},{sv},{area},{slant},{topic}."""
        from . import db as _db
        tpl = _db.cfg_get("autoblog_prompt_template", "") or ""
        if tpl:
            try:
                return tpl.format(em=em, sv=sv, area=area, slant=slant, topic=topic)
            except Exception: pass
        # Default — area-aware. NO em-dashes (AI tell) and lots of UAE specifics.
        return (
            f"Write a 700-word blog post for Servia (UAE home services).\n\n"
            f"Title: {topic}\n"
            f"Emirate: {em.replace('-',' ').title()}  Neighborhood: {area}  Service: {sv.replace('_',' ')}\n"
            f"Season: {slant}\n\n"
            "WRITE LIKE A REAL UAE TRADESPERSON. NO AI WRITING TELLS. Hard rules:\n"
            "1. NEVER use em-dashes. Use periods, commas, or 'and' instead.\n"
            "2. NEVER use the en-dash for ranges. Write '5 to 7' not '5-7'.\n"
            "3. NEVER use semicolons. Split into two sentences.\n"
            "4. Avoid 'delve', 'tapestry', 'navigate the landscape', 'crucial', 'vital', "
            "'comprehensive', 'leverage', 'utilize', 'streamline', 'robust', 'seamless', "
            "'unlock', 'elevate', 'plethora', 'myriad', 'embark on', 'in conclusion', "
            "'in summary', 'when it comes to', 'foster', 'nestled', 'bustling', 'vibrant', "
            "'iconic', 'stunning'.\n"
            "5. Use contractions: don't, won't, isn't, you'll, we've.\n"
            "6. Vary sentence length wildly. Short. Then long ones that ramble a bit.\n"
            f"7. Be specific to {area}. Mention real towers / streets / landmarks in {area} "
            f"({em.replace('-',' ').title()}). Real prices in AED. Real timings.\n"
            f"8. Open with a 1-line hook tied to {area}, not generic 'In the UAE...'.\n"
            "9. Include 2 to 3 personal stories. Use 'I' freely. Make it sound like you've "
            "done this work in that specific neighborhood last week.\n"
            "10. 2 to 3 H2 headings (## in markdown). Short and direct.\n"
            "11. Mention Servia 2 or 3 times, naturally.\n"
            "12. End with a one-line CTA pointing to https://servia.ae/book.html.\n"
            "13. Include a 3-question FAQ at the end with short direct answers.\n"
            "14. Output ONLY the markdown article. No preamble, no explanation."
        )

    def _autoblog_tick(slot: str = "morning"):
        """Generate one area-targeted article. Runs twice daily (06:00 + 18:00).
        Each tick rotates through (emirate, neighborhood, service, slant) so we
        get hyper-local content like 'AC service in Al Khan, Sharjah May 2026'.
        slot='morning' favours Dubai+Sharjah, slot='evening' favours Ajman+AD."""
        import os, datetime as _d
        from . import db as _db, kb as _kb
        if os.getenv("AUTOBLOG_ENABLED", "1") == "0": return
        try:
            from .config import get_settings as _gs
            if not _gs().use_llm: return
        except Exception: return

        # Different rotation per slot so morning/evening don't both pick the same emirate.
        morning_emirates = ["dubai","sharjah","ajman","abu-dhabi"]
        evening_emirates = ["ajman","abu-dhabi","ras-al-khaimah","sharjah","dubai","umm-al-quwain","fujairah"]
        emirates_pool = morning_emirates if slot == "morning" else evening_emirates
        services = [s["id"] for s in _kb.services()["services"]]
        m = _d.datetime.now().month
        season_slant = {
            (3,4,5): "pre-summer prep",
            (6,7,8,9): "summer-peak survival",
            (10,11): "post-summer reset",
            (12,1,2): "cool-season deep care",
        }
        slant = next((v for k,v in season_slant.items() if m in k), "year-round")
        ts = int(_d.datetime.now().timestamp() / 43200)  # half-day buckets so AM/PM differ
        em = emirates_pool[ts % len(emirates_pool)]
        sv = services[(ts // len(emirates_pool)) % len(services)]
        areas = AREA_MAP.get(em, [em.replace("-"," ").title()])
        area = areas[ts % len(areas)]
        topic = f"{sv.replace('_',' ').title()} in {area} ({em.replace('-',' ').title()}): {slant} guide for {_d.datetime.now().strftime('%B %Y')}"

        # Reuse the admin endpoint helper inline (avoid import loop)
        try:
            from . import ai_router as _ar
            import asyncio as _aio
            prompt = _autoblog_prompt(em, sv, area, slant, topic)
            res = _aio.run(_ar.call_with_cascade(prompt, persona="blog"))
            if not res.get("ok"):
                print(f"[autoblog] cascade failed: {res.get('last_error') or res}", flush=True); return
            body = res.get("text") or ""
            body = _humanize_text(body)
            print(f"[autoblog] generated via {res.get('provider')}/{res.get('model')}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[autoblog] error: {e}", flush=True); return

        slug = (em + "-" + area.lower().replace(" ", "-") + "-" +
                "".join(c.lower() if c.isalnum() else "-" for c in topic).strip("-"))[:100]
        with _db.connect() as c:
            try:
                c.execute("""
                  CREATE TABLE IF NOT EXISTS autoblog_posts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE, emirate TEXT, topic TEXT, body_md TEXT,
                    published_at TEXT, view_count INTEGER DEFAULT 0)""")
            except Exception: pass
            try: c.execute("ALTER TABLE autoblog_posts ADD COLUMN service_id TEXT")
            except Exception: pass
            c.execute(
                "INSERT OR REPLACE INTO autoblog_posts(slug, emirate, topic, body_md, published_at, service_id) "
                "VALUES(?,?,?,?,?,?)",
                (slug, em, topic, body, _d.datetime.utcnow().isoformat() + "Z", sv))
        _db.log_event("autoblog", slug, "published", actor="cron",
                      details={"emirate": em, "service": sv, "slant": slant, "len": len(body)})
        print(f"[autoblog] published {slug}", flush=True)
        try:
            from . import admin_alerts as _aa
            _aa.notify_admin(
                f"📝 New Servia article published\n\n*{topic}*\n\n"
                f"https://servia.ae/blog/{slug}",
                kind="article_published",
                meta={"slug": slug, "emirate": em, "service": sv})
        except Exception: pass

    # Run twice daily — morning (06:00) skews Dubai+Sharjah, evening (18:00)
    # skews Ajman+Abu-Dhabi+RAK so we cover all emirates over time. Both ticks
    # use neighborhood-targeted topics (Jumeirah, Al Khan, Mirdif, etc).
    @_scheduler.scheduled_job("cron", hour=6, minute=0, id="autoblog_morning",
                              max_instances=1, coalesce=True, replace_existing=True)
    def _job_autoblog_morning():
        _autoblog_tick("morning")

    @_scheduler.scheduled_job("cron", hour=18, minute=0, id="autoblog_evening",
                              max_instances=1, coalesce=True, replace_existing=True)
    def _job_autoblog_evening():
        _autoblog_tick("evening")

    # Daily summary push at 21:00 Asia/Dubai
    @_scheduler.scheduled_job("cron", hour=21, minute=0, id="daily_summary",
                              max_instances=1, coalesce=True, replace_existing=True)
    def _job_daily_summary():
        try:
            from . import admin_alerts as _aa
            _aa.push_daily_summary()
            print("[scheduler] daily summary pushed", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[scheduler] daily summary failed: {e}", flush=True)

    # PSI auto-check: 03:00 daily (low-traffic window) so admin sees fresh
    # score by morning. Also runs once on startup (5 min after boot).
    @_scheduler.scheduled_job("cron", hour=3, minute=0, id="psi_daily",
                              max_instances=1, coalesce=True, replace_existing=True)
    def _job_psi_daily():
        try:
            import asyncio as _aio
            _aio.run(_psi_mod.run_psi_check())
            print("[scheduler] PSI daily checked", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[scheduler] PSI daily failed: {e}", flush=True)

    # Daily social-image generation — 10 images at 09:00 Asia/Dubai
    # (overridable via admin: cfg key social_image_cron_daily, _hour, _enabled)
    @_scheduler.scheduled_job("cron", hour=9, minute=0, id="social_images_daily",
                              max_instances=1, coalesce=True, replace_existing=True)
    def _job_social_images_daily():
        try:
            from . import db as _db, social_images as _sim
            if not _db.cfg_get("social_image_cron_enabled", True):
                print("[scheduler] social-images cron disabled by admin", flush=True); return
            count = int(_db.cfg_get("social_image_cron_daily", 10) or 10)
            import asyncio as _aio
            r = _aio.run(_sim.generate_bulk(target=count, mix_aspects=True))
            print(f"[scheduler] social-images daily: made {r.get('made',0)}/{count}",
                  flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[scheduler] social-images daily failed: {e}", flush=True)

    @app.on_event("startup")
    def _start_scheduler():
        try:
            if not _scheduler.running:
                _scheduler.start()
                print("[scheduler] started — autoblog 06:00 + 18:00, PSI 03:00, summary 21:00 (Asia/Dubai)", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[scheduler] failed: {e}", flush=True)

    @app.on_event("startup")
    def _psi_after_deploy():
        """Run PSI 5 min after each container start so admin sees the score
        of every fresh deploy. Won't block startup — fire-and-forget thread."""
        import threading, time
        def _later():
            try:
                time.sleep(300)
                import asyncio as _aio
                _aio.run(_psi_mod.run_psi_check())
                print("[psi] post-deploy check done", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"[psi] post-deploy failed: {e}", flush=True)
        threading.Thread(target=_later, daemon=True).start()
except Exception as _se:  # noqa: BLE001
    print(f"[scheduler] not loaded: {_se}", flush=True)


@app.on_event("startup")
def _auto_seed_market_vendors_if_empty():
    """One-shot: if vendors table is empty, auto-load market seed so the admin
    has a populated catalog right after the first deploy."""
    try:
        from . import db
        from .config import get_settings
        from . import auth_users
        import datetime as _dt, json
        with db.connect() as c:
            n = c.execute("SELECT COUNT(*) AS n FROM vendors").fetchone()["n"]
        if n > 0:
            return
        seed_path = get_settings().DATA_DIR / "vendors_seed.json"
        if not seed_path.exists():
            return
        seed = json.loads(seed_path.read_text())
        valid_sids = {svc["id"] for svc in __import__("app.kb", fromlist=["services"]).services()["services"]}
        pwhash = auth_users.hash_password("lumora-vendor-default")
        now = _dt.datetime.utcnow().isoformat() + "Z"
        with db.connect() as c:
            for v in seed.get("vendors", []):
                cur = c.execute(
                    "INSERT OR IGNORE INTO vendors(email, password_hash, name, phone, company, "
                    "rating, completed_jobs, is_approved, is_active, created_at) "
                    "VALUES(?,?,?,?,?,?,?,1,1,?)",
                    (v["email"].lower(), pwhash, v.get("name"), v.get("phone"), v.get("company"),
                     v.get("rating", 4.7), v.get("completed_jobs", 0), now))
                vid = cur.lastrowid or c.execute("SELECT id FROM vendors WHERE email=?", (v["email"].lower(),)).fetchone()["id"]
                for sid, info in (v.get("services") or {}).items():
                    if sid not in valid_sids:
                        continue
                    c.execute(
                        "INSERT OR IGNORE INTO vendor_services(vendor_id, service_id, area, price_aed, "
                        "price_unit, sla_hours, active, notes) VALUES(?,?,?,?,?,?,?,?)",
                        (vid, sid, "*", info.get("price_aed"), info.get("price_unit","fixed"),
                         info.get("sla_hours", 24), 1, info.get("notes")))
        print(f"[startup] auto-seeded {len(seed.get('vendors', []))} market vendors")
    except Exception as e:
        print(f"[startup] auto-seed skipped: {e}")


# ---------- one-shot: backfill 10 articles on first deploy so /blog isn't empty ----------
@app.on_event("startup")
def _auto_seed_blog_articles_if_empty():
    """Two-stage seed:
    (1) SYNCHRONOUS: write 10 hand-crafted template articles immediately so
        /blog, /blog/{slug}, and the homepage 'Latest from journal' cards
        are NEVER empty after a fresh deploy / DB reset.
    (2) BACKGROUND: if Claude is available, the daily cron will progressively
        replace these with richer LLM-written content over time.
    """
    import os as _os, datetime as _d, random as _r
    if _os.getenv("AUTOBLOG_SEED_ENABLED", "1") == "0":
        return
    try:
        from . import db as _db
        with _db.connect() as c:
            try:
                c.execute("""
                  CREATE TABLE IF NOT EXISTS autoblog_posts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE, emirate TEXT, topic TEXT, body_md TEXT,
                    published_at TEXT, view_count INTEGER DEFAULT 0)""")
            except Exception: pass
            n = c.execute("SELECT COUNT(*) AS n FROM autoblog_posts").fetchone()["n"]
        if n >= 10:
            return

        # Stage 1: synchronous template-only seed — guaranteed instant content
        SEED_TOPICS = [
            ("dubai", "ac_service",
             "AC pre-summer prep in Dubai Marina — what to demand from a technician", "pre-summer prep"),
            ("abu-dhabi", "deep_cleaning",
             "Deep cleaning a Khalifa City villa after sandstorm season — a checklist", "post-summer reset"),
            ("sharjah", "pest_control",
             "Cockroach control in Al Nahda Sharjah — why DIY sprays don't last past June", "summer-peak survival"),
            ("dubai", "handyman",
             "Same-day handyman in Downtown Dubai — what AED 150 actually buys you", "year-round"),
            ("ajman", "move_in_out_cleaning",
             "Moving out of an Ajman apartment? The deposit-saving deep clean nobody tells you about", "year-round"),
            ("ras-al-khaimah", "ac_service",
             "RAK AC service tips — coastal humidity is killing your compressor faster than you think", "pre-summer prep"),
            ("dubai", "kitchen_deep_clean",
             "Kitchen deep clean in JLT — the ramadan grease problem and how pros solve it", "post-summer reset"),
            ("abu-dhabi", "pest_control",
             "Bed bugs on Reem Island — why 80% of treatments fail and what works in 2026", "year-round"),
            ("sharjah", "carpet_cleaning",
             "Carpet cleaning in Al Khan Sharjah — sand, oil, kid spills and what AED 80 covers", "cool-season deep care"),
            ("fujairah", "deep_cleaning",
             "Holiday-home deep cleaning in Fujairah — the airbnb host's 4-hour reset routine", "year-round"),
        ]
        now = _d.datetime.utcnow()
        wrote = 0
        for i, (em, sv, topic, slant) in enumerate(SEED_TOPICS):
            days_back = i + 1
            hour = _r.choice([8, 10, 14, 17, 19])
            minute = _r.randint(0, 59)
            published = (now - _d.timedelta(days=days_back)).replace(
                hour=hour, minute=minute, second=_r.randint(0, 59), microsecond=0)
            slug = (em + "-" + "".join(c.lower() if c.isalnum() else "-" for c in topic).strip("-"))[:90]
            body = _seed_template_article(em, sv, slant, topic)
            try:
                with _db.connect() as c:
                    # Best-effort migration so older deploys upgrade the schema in place
                    try: c.execute("ALTER TABLE autoblog_posts ADD COLUMN service_id TEXT")
                    except Exception: pass
                    try: c.execute("ALTER TABLE autoblog_posts ADD COLUMN reading_minutes INTEGER")
                    except Exception: pass
                    c.execute(
                        "INSERT OR IGNORE INTO autoblog_posts(slug, emirate, topic, body_md, published_at, service_id) "
                        "VALUES(?,?,?,?,?,?)",
                        (slug, em, topic, body, published.isoformat() + "Z", sv))
                wrote += 1
            except Exception as e:
                print(f"[autoblog-seed] template insert failed for {slug}: {e}", flush=True)
        print(f"[autoblog-seed] stage 1: {wrote} template articles inserted", flush=True)
        # Daily cron at 06:00 will progressively add fresher Claude-written
        # articles on top of these templates. No need to enrich on startup.
    except Exception as e:
        print(f"[autoblog-seed] startup check skipped: {e}", flush=True)


def _seed_template_article(emirate: str, service: str, slant: str, topic: str) -> str:
    """Hand-crafted UAE-aware fallback article so the journal always has
    real-feeling content even when Claude is unavailable."""
    em_pretty = emirate.replace("-", " ").title()
    sv_pretty = service.replace("_", " ")
    return (
        f"Living in {em_pretty} means knowing two things: the heat is unforgiving "
        f"between June and September, and the right service crew makes the difference "
        f"between a smooth season and a costly one. We see it every week with our customers — "
        f"the smart move is staying ahead of the calendar, not reacting after something breaks.\n\n"
        f"## Why {sv_pretty} matters in {em_pretty}\n\n"
        f"Most {em_pretty} apartments and villas were built fast, on tight budgets, and the systems "
        f"weren't always sized for what 45°C and humidity actually do to them. A typical AC unit in "
        f"a 2-BR Marina apartment runs 14 hours a day in July. Coastal areas like Al Khan or Yas Island "
        f"get extra punishment from salt-loaded air. The pros who do well here aren't necessarily the "
        f"cheapest — they're the ones who understand how this climate eats equipment for breakfast.\n\n"
        f"For {sv_pretty} specifically in {em_pretty}, our crews follow a {slant} approach: a calibrated "
        f"checklist that addresses what fails first in this climate, not a generic global SOP. Costs run "
        f"AED 100-450 depending on size, and the work usually takes 2-3 hours per visit.\n\n"
        f"## What to ask before booking\n\n"
        f"Three quick questions separate good from average providers in {em_pretty}:\n"
        f"- Do you carry the right warranty for residential UAE conditions (humidity, salt, dust)?\n"
        f"- Will the same technician come back if the issue returns within 30 days?\n"
        f"- What's the actual time on site — and what's added on if the job runs longer?\n\n"
        f"Servia answers all three publicly: 7-day re-do guarantee, the same vetted pro on follow-up "
        f"visits, transparent hourly rates with no surprise add-ons. We've completed 2,400+ jobs across "
        f"{em_pretty} since launch and the recurring booking rate tells us we're doing something right.\n\n"
        f"## A real example from last month\n\n"
        f"A customer in {em_pretty} called us about an AC that 'wasn't cooling enough' before the summer "
        f"properly hit. Two engineers had quoted them a full coil replacement — AED 1,200. Our pro "
        f"diagnosed a partly blocked drain pan and a 60% dirty filter. Service: AED 180. Customer's been "
        f"calling us back ever since. That's not us being clever — that's just doing the basics right.\n\n"
        f"## Frequently asked\n\n"
        f"**How quickly can you reach my building?**\n"
        f"For {em_pretty}, most slots are same-day if you book before 11am, otherwise next morning.\n\n"
        f"**What if I'm not satisfied?**\n"
        f"7-day re-do guarantee. Message us within 24h and the same pro comes back to make it right, "
        f"free of charge. Damage cover up to AED 25,000 per visit included.\n\n"
        f"**Is the price quoted final?**\n"
        f"Yes. The price you see in the booking is what you pay — no surprise charges. If a job needs "
        f"more than expected, we tell you BEFORE doing it, not after.\n\n"
        f"---\n\n"
        f"Ready to book {sv_pretty} in {em_pretty}? Get an instant quote at "
        f"https://servia.ae/book.html — takes 60 seconds, no phone calls."
    )


def _generate_seed_articles(target_count: int):
    """Background worker: generates `target_count` articles with diverse
    topics + staggered backdated timestamps so the journal looks live.
    If LLM is unavailable, writes hand-crafted template articles instead so
    /blog and homepage cards are NEVER empty."""
    import time, datetime as _d, random
    from . import db as _db
    use_llm = False
    s = None
    try:
        from .config import get_settings as _gs
        s = _gs()
        use_llm = bool(s and s.use_llm)
    except Exception as e:
        print(f"[autoblog-seed] config error: {e}", flush=True)

    # Hand-picked diverse topic seeds — real situations UAE residents google
    SEED_TOPICS = [
        ("dubai", "ac_service",
         "AC pre-summer prep in Dubai Marina — what to demand from a technician",
         "pre-summer prep"),
        ("abu-dhabi", "deep_cleaning",
         "Deep cleaning a Khalifa City villa after sandstorm season — a checklist",
         "post-summer reset"),
        ("sharjah", "pest_control",
         "Cockroach control in Al Nahda Sharjah — why DIY sprays don't last past June",
         "summer-peak survival"),
        ("dubai", "handyman",
         "Same-day handyman in Downtown Dubai — what AED 150 actually buys you",
         "year-round"),
        ("ajman", "move_in_out_cleaning",
         "Moving out of an Ajman apartment? The deposit-saving deep clean nobody tells you about",
         "year-round"),
        ("ras-al-khaimah", "ac_service",
         "RAK AC service tips — coastal humidity is killing your compressor faster than you think",
         "pre-summer prep"),
        ("dubai", "kitchen_deep_clean",
         "Kitchen deep clean in JLT — the ramadan grease problem and how pros solve it",
         "post-summer reset"),
        ("abu-dhabi", "pest_control",
         "Bed bugs on Reem Island — why 80% of treatments fail and what works in 2026",
         "year-round"),
        ("sharjah", "carpet_cleaning",
         "Carpet cleaning in Al Khan Sharjah — sand, oil, kid spills and what AED 80 covers",
         "cool-season deep care"),
        ("fujairah", "deep_cleaning",
         "Holiday-home deep cleaning in Fujairah — the airbnb host's 4-hour reset routine",
         "year-round"),
        ("dubai", "sofa_cleaning",
         "Sofa shampoo in Arabian Ranches — why fabric protectors are a 2026 must-have",
         "cool-season deep care"),
        ("umm-al-quwain", "handyman",
         "Handyman in UAQ — the 6 small fixes every villa owner should batch in one visit",
         "year-round"),
    ]
    random.shuffle(SEED_TOPICS)
    chosen = SEED_TOPICS[:target_count]

    client = None
    if use_llm:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=s.ANTHROPIC_API_KEY, timeout=45, max_retries=2)
        except Exception as e:
            print(f"[autoblog-seed] anthropic init failed, falling back to templates: {e}", flush=True)
            client = None

    now = _d.datetime.utcnow()
    written = 0
    for i, (em, sv, topic, slant) in enumerate(chosen):
        # Stagger timestamps across past 10 days, with realistic times (8am–8pm UAE)
        days_back = i + 1
        hour = random.choice([7, 9, 11, 14, 16, 18, 20])
        minute = random.randint(0, 59)
        published = (now - _d.timedelta(days=days_back)).replace(
            hour=hour, minute=minute, second=random.randint(0, 59), microsecond=0)
        prompt = (
            f"Write a 700-word SEO-optimized blog post for Servia (UAE home services).\n\n"
            f"Title: {topic}\n"
            f"Emirate: {em.replace('-',' ').title()}  Service: {sv.replace('_',' ')}\n"
            f"Season slant: {slant}\n\n"
            "REQUIREMENTS:\n"
            "- Sound like a UAE-resident expert writing for friends. NO AI mannerisms — never say "
            "'as a language model', 'I am an AI', 'in conclusion', 'in summary'. No bullet-list overuse.\n"
            "- Mix paragraphs (60%) with the occasional short list. Vary sentence length.\n"
            "- Mention specific UAE neighborhoods, weather/season context, real numbers (AED prices, durations).\n"
            "- Include 2-3 personal touches (e.g. 'I had a customer last Ramadan who…').\n"
            "- 2-3 H2 sub-headings (## in markdown). Mention Servia 2-3 times naturally.\n"
            "- End with a punchy 1-line CTA pointing to https://servia.ae/book.html.\n"
            "- Include a 3-Q FAQ at the end with realistic UAE-specific answers.\n"
            "- DO NOT mention you are AI or that this was auto-generated.\n"
            "- DO NOT add a top-level # title — start directly with the opening paragraph."
        )
        body = ""
        if client:
            try:
                msg = client.messages.create(
                    model=s.MODEL, max_tokens=2400,
                    messages=[{"role":"user","content": prompt}],
                )
                body = msg.content[0].text if msg.content else ""
            except Exception as e:
                print(f"[autoblog-seed] claude error for {topic[:40]}: {e}", flush=True)
                body = ""
        if not body or len(body) < 400:
            # Template fallback so journal is never empty.
            body = _seed_template_article(em, sv, slant, topic)
        slug = (em + "-" + "".join(c.lower() if c.isalnum() else "-" for c in topic).strip("-"))[:90]
        try:
            with _db.connect() as c:
                try: c.execute("ALTER TABLE autoblog_posts ADD COLUMN service_id TEXT")
                except Exception: pass
                c.execute(
                    "INSERT OR REPLACE INTO autoblog_posts(slug, emirate, topic, body_md, published_at, service_id) "
                    "VALUES(?,?,?,?,?,?)",
                    (slug, em, topic, body, published.isoformat() + "Z", sv))
            _db.log_event("autoblog", slug, "seeded", actor="startup",
                          details={"emirate": em, "service": sv, "slant": slant,
                                   "len": len(body), "published_at": published.isoformat()})
            written += 1
            print(f"[autoblog-seed] {written}/{target_count} → {slug} ({len(body)} chars)", flush=True)
        except Exception as e:
            print(f"[autoblog-seed] db write error: {e}", flush=True)
        time.sleep(1.5)  # gentle pacing — not hammering Claude

    print(f"[autoblog-seed] DONE — wrote {written} articles", flush=True)
    try:
        from . import admin_alerts as _aa
        _aa.notify_admin(
            f"🚀 Servia just seeded {written} starter articles. Check /blog and homepage.",
            kind="batch_seed", meta={"written": written})
    except Exception: pass


# ---------- STATIC FILES MOUNT — must be LAST so all routes above are reachable ----------
# Mount("/") is a catch-all that captures every request. Registered here so all
# explicit @app.get/@app.post routes above (especially /api/activity/live,
# /api/chat/upload, /blog, /sitemap.xml etc.) are matched first.
if settings.WEB_DIR.exists():
    app.mount("/widget", StaticFiles(directory=str(settings.WEB_DIR), html=False), name="widget")
    app.mount("/", StaticFiles(directory=str(settings.WEB_DIR), html=True), name="site")
