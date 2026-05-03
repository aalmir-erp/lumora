"""FastAPI entrypoint."""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
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
# GZip every response > 500 bytes — biggest single PageSpeed win.
# Railway / proxy doesn't compress for us; PSI flagged "No compression applied"
# with 30 KiB of saving on the document request alone.
app.add_middleware(GZipMiddleware, minimum_size=500)

# Routers
app.include_router(admin.router)
app.include_router(portal.router)
app.include_router(portal_v2.router)
app.include_router(portal_v2.public_router)
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




# ---------- Booking fast-path — bypass LLM for direct form-style commands ----------
import re as _re
_BOOK_RX = _re.compile(
    r"^Book\s+(\w+)\s+on\s+(\d{4}-\d{2}-\d{2})\s+at\s+(\d{1,2}:\d{2})\s+for\s+([^,]+),\s+phone\s+([+0-9 ]+),\s+address:?\s*['\"]?([^,'\"]+)['\"]?",
    _re.I)


def _try_fast_book(message: str) -> dict | None:
    m = _BOOK_RX.match(message.strip())
    if not m: return None
    svc, date, time_, name, phone, addr = m.groups()
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


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    sid = req.session_id or _new_sid()
    lang = (req.language or "en").lower()[:2]

    _persist(sid, "user", req.message, phone=req.phone)

    # Fast-path for explicit booking commands — saves a 10-15s LLM round-trip
    fast = _try_fast_book(req.message)
    if fast:
        text = fast.get("text") or "(no response)"
        _persist(sid, "assistant", text, phone=req.phone, tool_calls=fast.get("tool_calls"))
        return ChatResponse(session_id=sid, text=text,
                            tool_calls=fast.get("tool_calls", []),
                            mode="fast", usage={})

    if _is_taken_over(sid):
        # Don't auto-reply. The agent's next message will appear via /api/chat/poll.
        return ChatResponse(session_id=sid, text="", tool_calls=[],
                            mode="agent_handling", usage={}, agent_handled=True)

    history = _history(sid)
    if settings.use_llm:
        try:
            result = llm.chat(history, session_id=sid, language=lang)
            mode = "llm"
        except Exception as e:  # noqa: BLE001
            # Fall back to the rule-based brain so the UX never 502s on a transient LLM blip
            print(f"[chat] LLM error, falling back to demo: {e}", flush=True)
            try:
                result = demo_brain.respond(req.message, history)
                result["text"] = (
                    "I'm having a brief hiccup with my AI brain — let me try a quick reply: "
                    + (result.get("text") or "")
                )
                mode = "fallback"
            except Exception as e2:  # noqa: BLE001
                result = {"text": f"Sorry, I'm having technical trouble. WhatsApp us at +971 56 4020087.",
                          "tool_calls": [], "usage": {}}
                mode = "error"
                db.log_event("chat", sid, "llm_error", actor="system",
                             details={"err": str(e), "fallback_err": str(e2)})
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
@app.middleware("http")
async def _smart_cache(request, call_next):
    resp = await call_next(request)
    p = request.url.path
    # Code (HTML / JS / CSS / JSON / manifest) — always fresh so deploys land instantly.
    if (p.endswith((".html", ".js", ".css", ".json", ".webmanifest")) or p == "/" or p.endswith("/")):
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    # Icons / images / fonts — long cache + stale-while-revalidate so PageSpeed
    # gives full marks on repeat visits without blocking new deploys.
    elif p.endswith((".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".woff", ".woff2", ".ttf")):
        # 30 days + 7 days stale-while-revalidate for branding/icon assets.
        resp.headers["Cache-Control"] = "public, max-age=2592000, stale-while-revalidate=604800"
    return resp

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
    urls = [("/", "1.0", "daily"),
            ("/services.html", "0.9", "weekly"),
            ("/book.html", "0.9", "weekly"),
            ("/login.html", "0.7", "monthly")]
    for s in services:
        urls.append((f"/service.html?id={s['id']}", "0.85", "weekly"))
    for area in ("dubai", "sharjah", "ajman", "abu-dhabi", "ras-al-khaimah"):
        urls.append((f"/services.html?area={area}", "0.7", "weekly"))
    langs = ("en", "ar", "hi", "tl")
    body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    body += 'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    for u, prio, freq in urls:
        sep = "&amp;" if "?" in u else "?"
        body += f"  <url><loc>{base}{u}</loc>"
        body += f"<lastmod>{today}</lastmod><changefreq>{freq}</changefreq><priority>{prio}</priority>"
        for lg in langs:
            body += (f'<xhtml:link rel="alternate" hreflang="{lg}" '
                     f'href="{base}{u}{sep}lang={lg}"/>')
        body += "</url>\n"
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
    """Returns the admin token if env var is unset (uses default 'lumora-admin-test')."""
    from .auth import ADMIN_TOKEN_AUTOGEN
    if not ADMIN_TOKEN_AUTOGEN:
        raise HTTPException(403, "ADMIN_TOKEN is set in env; use that instead.")
    return {"admin_token": ADMIN_TOKEN,
            "note": "Default test token. Set ADMIN_TOKEN in Railway for production."}


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
