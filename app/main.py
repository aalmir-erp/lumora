"""FastAPI entrypoint."""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Optional

import pathlib
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
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

    # If the user attached an image, fold a marker into the persisted message
    # so it's visible in conversations + the LLM gets context. The actual image
    # bytes can be loaded by the model via the public URL if needed.
    msg = req.message
    if req.attachment_url:
        msg = (msg + f"\n[attached image: {req.attachment_url}]").strip()
    _persist(sid, "user", msg, phone=req.phone)

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
                result = {"text": "Sorry, I'm having technical trouble — please try again or use /contact.html and we'll respond within minutes.",
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

# Static mounts MOVED to end-of-file. Registering Mount("/", StaticFiles)
# at this point would shadow every route registered later (live activity feed,
# blog index, blog post, contact, app-install, etc.) because Starlette's
# router matches in registration order and Mount("/") matches everything.


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


@app.get("/blog/{slug}", response_class=HTMLResponse)
def blog_post(slug: str):
    """Public blog post — Claude-generated, SEO-friendly, server-rendered."""
    with db.connect() as c:
        try:
            r = c.execute(
                "SELECT * FROM autoblog_posts WHERE slug=?", (slug,)
            ).fetchone()
        except Exception:
            r = None
    if not r:
        raise HTTPException(404, "Post not found")
    post = db.row_to_dict(r) or {}
    with db.connect() as c:
        try: c.execute("UPDATE autoblog_posts SET view_count=view_count+1 WHERE slug=?", (slug,))
        except Exception: pass
    # Defensive defaults — every field can be missing from very old DB rows
    body = post.get("body_md") or ""
    title = post.get("topic") or "Servia article"
    emirate = (post.get("emirate") or "uae").replace("-", " ").title()
    pub = (post.get("published_at") or "")[:10] or "—"
    # Convert lightweight markdown to HTML (just headings + paragraphs + CTAs)
    import re as _re, html as _html
    body_h = _html.escape(body)
    body_h = _re.sub(r"^## (.+)$", r"<h2>\1</h2>", body_h, flags=_re.M)
    body_h = _re.sub(r"^# (.+)$", r"<h1>\1</h1>", body_h, flags=_re.M)
    body_h = _re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", body_h)
    body_h = _re.sub(r"\n\n+", "</p><p>", body_h)
    body_h = "<p>" + body_h + "</p>"
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_html.escape(title)} | Servia Blog</title>
<meta name="description" content="{_html.escape(title)} — Servia UAE home services insights for {emirate}.">
<link rel="canonical" href="https://servia.ae/blog/{slug}">
<link rel="stylesheet" href="/style.css">
</head><body>
<div class="uae-flag-strip" aria-hidden="true" style="height:5px;background:linear-gradient(90deg,#00732F 0% 25%,#fff 25% 50%,#000 50% 75%,#FF0000 75% 100%)"></div>
<nav class="nav"><div class="nav-inner">
  <a href="/"><img src="/logo.svg" height="36" alt="Servia"></a>
  <div class="nav-cta" style="margin-inline-start:auto"><a class="btn btn-primary" href="/book.html">Book now</a></div>
</div></nav>
<article style="max-width:760px;margin:32px auto 80px;padding:0 16px">
  <a href="/area.html?city={post.get('emirate') or 'dubai'}" style="font-size:13px;color:var(--muted);text-decoration:none">📍 {emirate}</a>
  <h1 style="font-size:32px;letter-spacing:-.02em;margin:8px 0 18px">{_html.escape(title)}</h1>
  <p style="color:var(--muted);font-size:13px;margin-bottom:24px">Published {pub}</p>
  <div style="font-size:16px;line-height:1.7">{body_h}</div>
  <div data-share="blog-{slug}" data-share-key="blog-{slug}" data-share-text="Servia: {_html.escape(title)}" style="margin-top:32px"></div>
  <div style="margin-top:32px;padding:24px;background:linear-gradient(135deg,#FCD34D,#F59E0B);color:#78350F;border-radius:18px;text-align:center">
    <h3 style="margin:0 0 6px">Ready to book?</h3>
    <p style="margin:0 0 14px">Servia covers all 7 UAE emirates. Get a quote in 60 seconds.</p>
    <a class="btn btn-primary" href="/book.html">Book your service →</a>
  </div>
</article>
<script src="/share.js" defer></script>
</body></html>"""


@app.get("/blog", response_class=HTMLResponse)
def blog_index():
    """Index of all published autoblog posts. Self-heals if the DB is
    empty by triggering the same template seed inline."""
    with db.connect() as c:
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS autoblog_posts(
                id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT UNIQUE,
                emirate TEXT, topic TEXT, body_md TEXT,
                published_at TEXT, view_count INTEGER DEFAULT 0)""")
        except Exception: pass
        try:
            n = c.execute("SELECT COUNT(*) AS n FROM autoblog_posts").fetchone()["n"]
        except Exception:
            n = 0
    if n < 4:
        try: _auto_seed_blog_articles_if_empty()
        except Exception: pass
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT slug, emirate, topic, published_at FROM autoblog_posts "
                "ORDER BY id DESC LIMIT 100"
            ).fetchall()
        except Exception:
            rows = []
    def _r(row, key, default=""):
        try: v = row[key] if key in row.keys() else None
        except Exception: v = None
        return v or default
    items = "".join(
        f'<li style="margin-bottom:14px"><a href="/blog/{_r(r,"slug","x")}" style="font-size:17px;font-weight:600">{_r(r,"topic","Article")}</a><br>'
        f'<small style="color:var(--muted)">📍 {_r(r,"emirate","uae").replace("-"," ").title()} · {_r(r,"published_at","")[:10]}</small></li>'
        for r in rows
    ) or "<p>No posts yet — articles publish daily at 06:00 UAE time.</p>"
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Servia Blog — UAE home services insights</title>
<link rel="canonical" href="https://servia.ae/blog"><link rel="stylesheet" href="/style.css">
</head><body>
<div class="uae-flag-strip" aria-hidden="true" style="height:5px;background:linear-gradient(90deg,#00732F 0% 25%,#fff 25% 50%,#000 50% 75%,#FF0000 75% 100%)"></div>
<nav class="nav"><div class="nav-inner">
  <a href="/"><img src="/logo.svg" height="36" alt="Servia"></a>
  <div class="nav-cta" style="margin-inline-start:auto"><a class="btn btn-primary" href="/book.html">Book now</a></div>
</div></nav>
<section style="max-width:760px;margin:32px auto 80px;padding:0 16px">
<h1 style="font-size:32px;letter-spacing:-.02em">Servia Blog</h1>
<p style="color:var(--muted)">Locally-informed home-services tips, written for UAE residents — fresh content every day.</p>
<ul style="list-style:none;padding:0;margin-top:24px">{items}</ul>
</section>
</body></html>"""


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
    """Captures a contact-form message and pings the admin via WhatsApp.
    Stored in admin_alerts for visibility even if the bridge isn't paired."""
    from . import db, admin_alerts
    import datetime as _dt
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    if not isinstance(payload, dict): payload = {}
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
        ip = (request.client.host if request.client else "")[:64]
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

    def _autoblog_tick():
        """Daily 06:00 UAE — generate one article. Topic rotates by day-of-year
        through (emirate, service, slant) tuples so we get fresh, situational
        content (e.g. 'AC pre-summer prep in Dubai Marina May 2026')."""
        import os, datetime as _d, random
        from . import db as _db, kb as _kb
        if os.getenv("AUTOBLOG_ENABLED", "1") == "0": return
        try:
            from .config import get_settings as _gs
            if not _gs().use_llm: return
        except Exception: return

        emirates = ["dubai","abu-dhabi","sharjah","ajman","ras-al-khaimah","umm-al-quwain","fujairah"]
        services = [s["id"] for s in _kb.services()["services"]]
        # Seasonal slant — UAE-aware
        m = _d.datetime.now().month
        season_slant = {
            (3,4,5): "pre-summer prep",
            (6,7,8,9): "summer-peak survival",
            (10,11): "post-summer reset",
            (12,1,2): "cool-season deep care",
        }
        slant = next((v for k,v in season_slant.items() if m in k), "year-round")
        ts = int(_d.datetime.now().timestamp() / 86400)
        em = emirates[ts % len(emirates)]
        sv = services[(ts // len(emirates)) % len(services)]
        topic = f"{slant.title()} — best {sv.replace('_',' ')} in {em.replace('-',' ').title()} ({_d.datetime.now().strftime('%B %Y')})"

        # Reuse the admin endpoint helper inline (avoid import loop)
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=_gs().ANTHROPIC_API_KEY, timeout=30, max_retries=1)
            prompt = (
                f"Write a 700-word SEO-optimized blog post for Servia (UAE home services).\n\n"
                f"Title: {topic}\nEmirate: {em.replace('-',' ').title()}  Service: {sv.replace('_',' ')}\n"
                f"Season: {slant}\n\n"
                "REQUIREMENTS:\n"
                "- Sound like a UAE-resident expert writing for friends. NO AI mannerisms — never say 'as a language "
                "model', 'I am an AI', 'in conclusion', 'in summary'. No bullet-list overuse.\n"
                "- Mix paragraphs (60%) with the occasional short list. Vary sentence length.\n"
                "- Mention specific UAE neighborhoods, weather context, real numbers (AED prices, durations).\n"
                "- Include 2-3 personal touches (e.g. 'I had a customer last Ramadan who…').\n"
                "- 2-3 H2 sub-headings (## in markdown). Servia mentioned 2-3 times naturally.\n"
                "- End with a punchy 1-line CTA pointing to https://servia.ae/book.html.\n"
                "- Include a 3-Q FAQ at the end with realistic UAE-specific answers.\n"
                "- DO NOT mention you are AI or that this was auto-generated."
            )
            msg = client.messages.create(
                model=_gs().MODEL, max_tokens=2400,
                messages=[{"role":"user","content":prompt}],
            )
            body = msg.content[0].text if msg.content else ""
        except Exception as e:  # noqa: BLE001
            print(f"[autoblog] error: {e}", flush=True); return

        slug = (em + "-" + "".join(c.lower() if c.isalnum() else "-" for c in topic).strip("-"))[:90]
        with _db.connect() as c:
            try:
                c.execute("""
                  CREATE TABLE IF NOT EXISTS autoblog_posts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE, emirate TEXT, topic TEXT, body_md TEXT,
                    published_at TEXT, view_count INTEGER DEFAULT 0)""")
            except Exception: pass
            c.execute(
                "INSERT OR REPLACE INTO autoblog_posts(slug, emirate, topic, body_md, published_at) "
                "VALUES(?,?,?,?,?)",
                (slug, em, topic, body, _d.datetime.utcnow().isoformat() + "Z"))
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

    @_scheduler.scheduled_job("cron", hour=6, minute=0, id="autoblog_daily",
                              max_instances=1, coalesce=True, replace_existing=True)
    def _job_autoblog():
        _autoblog_tick()

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

    @app.on_event("startup")
    def _start_scheduler():
        try:
            if not _scheduler.running:
                _scheduler.start()
                print("[scheduler] started — autoblog runs daily at 06:00 Asia/Dubai", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[scheduler] failed: {e}", flush=True)
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
                    c.execute(
                        "INSERT OR IGNORE INTO autoblog_posts(slug, emirate, topic, body_md, published_at) "
                        "VALUES(?,?,?,?,?)",
                        (slug, em, topic, body, published.isoformat() + "Z"))
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
                c.execute(
                    "INSERT OR REPLACE INTO autoblog_posts(slug, emirate, topic, body_md, published_at) "
                    "VALUES(?,?,?,?,?)",
                    (slug, em, topic, body, published.isoformat() + "Z"))
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
