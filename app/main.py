"""FastAPI entrypoint."""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import admin, db, demo_brain, kb, llm, portal, portal_v2, quotes, tools, whatsapp
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

# Routers
app.include_router(admin.router)
app.include_router(portal.router)
app.include_router(portal_v2.router)
app.include_router(whatsapp.router)


# ---------- chat ----------
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    language: Optional[str] = "en"
    phone: Optional[str] = None


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


def _persist(session_id: str, role: str, content: str, *, phone: str | None,
             tool_calls: list | None = None, agent: bool = False) -> None:
    with db.connect() as c:
        c.execute(
            "INSERT INTO conversations(session_id, role, content, tool_calls_json, "
            "channel, phone, agent_handled, created_at) VALUES(?,?,?,?,?,?,?,?)",
            (session_id, role, content,
             json.dumps(tool_calls) if tool_calls else None,
             "web", phone, 1 if agent else 0,
             _dt.datetime.utcnow().isoformat() + "Z"),
        )


def _history(session_id: str, limit: int = 20) -> list[dict]:
    with db.connect() as c:
        rows = c.execute(
            "SELECT role, content FROM conversations WHERE session_id=? "
            "ORDER BY id DESC LIMIT ?", (session_id, limit)).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def _is_taken_over(session_id: str) -> bool:
    with db.connect() as c:
        r = c.execute(
            "SELECT 1 FROM agent_takeovers WHERE session_id=? AND ended_at IS NULL",
            (session_id,)).fetchone()
    return bool(r)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    sid = req.session_id or _new_sid()
    lang = (req.language or "en").lower()[:2]

    _persist(sid, "user", req.message, phone=req.phone)

    if _is_taken_over(sid):
        # Don't auto-reply. The agent's next message will appear via /api/chat/poll.
        return ChatResponse(session_id=sid, text="", tool_calls=[],
                            mode="agent_handling", usage={}, agent_handled=True)

    history = _history(sid)
    if settings.use_llm:
        try:
            result = llm.chat(history, session_id=sid, language=lang)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"LLM error: {e}") from e
        mode = "llm"
    else:
        result = demo_brain.respond(req.message, history)
        mode = "demo"

    text = result.get("text") or "(no response)"
    _persist(sid, "assistant", text, phone=req.phone, tool_calls=result.get("tool_calls"))
    return ChatResponse(session_id=sid, text=text,
                        tool_calls=result.get("tool_calls", []),
                        mode=mode, usage=result.get("usage", {}))


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
@app.get("/pay/{invoice_id}", response_class=HTMLResponse)
def pay_stub_page(invoice_id: str):
    """Tiny stub payment page when no real gateway is configured."""
    with db.connect() as c:
        r = c.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
    if not r:
        raise HTTPException(404, "invoice not found")
    inv = db.row_to_dict(r)
    paid = inv["payment_status"] == "paid"
    return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>Pay {invoice_id}</title>
<link rel='stylesheet' href='/widget/style.css'></head><body class='paystub'>
<div class='card'><h1>{settings.BRAND_NAME} • Invoice {invoice_id}</h1>
<p>Amount: <b>{inv['amount']} {inv['currency']}</b></p>
<p>Status: <b>{'PAID' if paid else 'UNPAID'}</b></p>
{'' if paid else f'''<form method='post' action='/api/portal/pay-stub'
onsubmit='event.preventDefault(); fetch("/api/portal/pay-stub",{{method:"POST",headers:{{"content-type":"application/json"}},body:JSON.stringify({{invoice_id:"{invoice_id}"}})}}).then(r=>r.json()).then(j=>{{document.body.innerHTML+="<p>"+JSON.stringify(j)+"</p>";location.reload();}});'>
<button type='submit' class='btn-primary'>Mark as paid (stub)</button></form>
<p style='color:#64748b'>Configure STRIPE_SECRET_KEY for live payments.</p>'''}
<p><a href='/account.html'>← Back to my account</a></p></div></body></html>"""


# ---------- static frontend (mounted last so /api/* take precedence) ----------
if settings.WEB_DIR.exists():
    app.mount("/widget", StaticFiles(directory=str(settings.WEB_DIR), html=False), name="widget")
    app.mount("/", StaticFiles(directory=str(settings.WEB_DIR), html=True), name="site")


# ---------- SEO / GEO endpoints ----------
@app.get("/robots.txt", response_class=HTMLResponse)
def robots_txt():
    base = f"https://{settings.BRAND_DOMAIN}"
    return (
        "User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /admin.html\n\n"
        # Allow major AI crawlers explicitly
        "User-agent: GPTBot\nAllow: /\n"
        "User-agent: ClaudeBot\nAllow: /\n"
        "User-agent: PerplexityBot\nAllow: /\n"
        "User-agent: Google-Extended\nAllow: /\n"
        "User-agent: anthropic-ai\nAllow: /\n"
        "User-agent: cohere-ai\nAllow: /\n"
        "User-agent: CCBot\nAllow: /\n"
        f"\nSitemap: {base}/sitemap.xml\n"
    )


@app.get("/sitemap.xml")
def sitemap_xml():
    base = f"https://{settings.BRAND_DOMAIN}"
    today = _dt.date.today().isoformat()
    services = kb.services()["services"]
    urls = ["/", "/services.html", "/book.html", "/account.html", "/login.html"]
    for s in services:
        urls.append(f"/services.html?service={s['id']}")
    for area in ("dubai", "sharjah", "ajman", "abu-dhabi"):
        urls.append(f"/services.html?area={area}")
    body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        priority = "1.0" if u == "/" else "0.8"
        body += (f"  <url><loc>{base}{u}</loc>"
                 f"<lastmod>{today}</lastmod><changefreq>weekly</changefreq>"
                 f"<priority>{priority}</priority></url>\n")
    body += "</urlset>\n"
    from fastapi.responses import Response
    return Response(content=body, media_type="application/xml")


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

Transparent, AED, includes 5% VAT. See https://{b['domain']}/services.html or ask Lumi (our AI assistant).

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
- POST /api/chat — Lumi the AI concierge (Claude-powered)
"""


@app.get("/__admin_token__")
def show_admin_token_in_dev(request: Request):
    """Only available when ADMIN_TOKEN env var is unset (auto-generated random)."""
    import os
    if os.getenv("ADMIN_TOKEN"):
        raise HTTPException(403, "ADMIN_TOKEN is set in env; use that instead.")
    if request.client.host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(403, "local-only")
    return {"admin_token": ADMIN_TOKEN}
