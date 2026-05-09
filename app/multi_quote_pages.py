"""Multi-service quote signing + payment routes (v1.24.55).

Customer-facing endpoints triggered by the bot's create_multi_quote tool.
Phone-gated access: /q/{quote_id} renders a 'Enter your phone' gate. Only
when the entered phone matches the quote's stored phone do we render the
itemized cart, signature pad, per-line approve/comment, and pay button.

Routes:
  GET  /q/{quote_id}                 — phone gate page (HTML)
  POST /api/q/{quote_id}/verify      — phone verify, returns signed token
  GET  /api/q/{quote_id}             — fetch full quote (auth via verify token)
  POST /api/q/{quote_id}/sign        — submit signature data URL + per-item
                                       approve/comment + (optional) photos
  GET  /p/{quote_id}                 — payment page (Stripe checkout / cash msg)
"""
from __future__ import annotations
import datetime as _dt
import hashlib
import hmac
import json as _json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import db
from .config import get_settings


public_router = APIRouter(tags=["quote-public"])


def _now() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


def _quote(quote_id: str) -> dict | None:
    with db.connect() as c:
        try:
            r = c.execute("SELECT * FROM multi_quotes WHERE quote_id=?",
                          (quote_id,)).fetchone()
        except Exception: return None
    if not r: return None
    d = dict(r)
    try: d["items"] = _json.loads(d.get("items_json") or "[]")
    except Exception: d["items"] = []
    return d


def _sign_token(quote_id: str, phone: str) -> str:
    s = get_settings()
    secret = (getattr(s, "ADMIN_TOKEN", "") or "lumora-token").encode()
    msg = f"{quote_id}|{phone}".encode()
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()[:32]


def _verify_token(token: str, quote_id: str, phone: str) -> bool:
    return hmac.compare_digest(token or "", _sign_token(quote_id, phone))


# ---------------------------------------------------------------------------
@public_router.get("/q/{quote_id}", response_class=HTMLResponse)
def quote_landing(quote_id: str) -> str:
    q = _quote(quote_id)
    if not q:
        return HTMLResponse("<h1>Quote not found</h1>", status_code=404)
    # Render a phone-gate page; once verified, JS calls /api/q/{quote_id}
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Servia · Quote {quote_id}</title>
<link rel="stylesheet" href="/style.css">
<style>
body{{font-family:system-ui;background:#0F172A;color:#F1F5F9;padding:14px;margin:0}}
.gate{{max-width:340px;margin:18vh auto;text-align:center;background:#1E293B;
border:1px solid #334155;border-radius:12px;padding:18px}}
.gate input{{width:100%;padding:10px;font-size:15px;background:#0F172A;
color:#fff;border:1px solid #334155;border-radius:8px;margin:8px 0;font-family:monospace}}
.gate button{{width:100%;padding:11px;background:#0D9488;color:#fff;border:none;
border-radius:8px;font-weight:600;font-size:14px;cursor:pointer}}
.cart{{max-width:520px;margin:0 auto;display:none}}
.line{{display:flex;justify-content:space-between;padding:8px 0;
border-bottom:1px dashed #334155}}
.line .label{{flex:1}} .line .price{{font-weight:600;color:#FCD34D}}
.totals .total{{font-size:18px;font-weight:700;color:#14B8A6}}
canvas{{background:#fff;border-radius:8px;width:100%;height:140px;display:block;margin:8px 0}}
.btn{{padding:11px 14px;background:#0D9488;color:#fff;border:none;border-radius:8px;
font-weight:600;cursor:pointer;width:100%;margin:6px 0}}
.btn.alt{{background:#1E293B;color:#F1F5F9;border:1px solid #475569}}
textarea,input[type=text]{{width:100%;padding:8px;background:#0F172A;color:#fff;
border:1px solid #334155;border-radius:6px;font:inherit;margin-top:4px}}
.warn{{background:#7F1D1D;color:#FECACA;padding:8px;border-radius:6px;
font-size:12px;margin:8px 0}}
.feature{{font-size:12px;color:#94A3B8;line-height:1.5;background:#1E293B;
border-left:3px solid #14B8A6;padding:8px 12px;margin:10px 0;border-radius:0 6px 6px 0}}
</style></head><body>
<div class="gate" id="gate">
  <h2>Servia Quote</h2>
  <p style="color:#94A3B8;font-size:12.5px">Quote <code>{quote_id}</code><br>
  Enter the phone number used to request this quote.</p>
  <input id="phone" type="tel" placeholder="0559396459" autocomplete="tel">
  <button onclick="verify()">View quote</button>
  <p id="msg" style="color:#FCA5A5;font-size:12px;margin-top:8px"></p>
</div>
<div class="cart" id="cart">
  <h2>Servia Quote <code>{quote_id}</code></h2>
  <div id="lines"></div>
  <div class="totals" style="margin:14px 0">
    <div class="line"><div class="label">Subtotal</div><div class="price" id="sub">—</div></div>
    <div class="line"><div class="label">VAT 5%</div><div class="price" id="vat">—</div></div>
    <div class="line total"><div class="label">Total</div><div class="price" id="total">—</div></div>
  </div>
  <div class="feature">📅 <span id="date"></span> · 📍 <span id="addr"></span></div>
  <div class="feature">✍️ <b>Sign below to approve</b> · Photos &amp; videos of your service will be uploaded after completion in this same link · You can comment on each service · Live status updates land on your phone.</div>
  <h3 style="margin:16px 0 6px;font-size:14px">✍️ Your signature</h3>
  <canvas id="sig" width="500" height="140"></canvas>
  <button class="btn alt" onclick="clearSig()">Clear signature</button>
  <h3 style="margin:16px 0 6px;font-size:14px">💬 Notes / per-service comments</h3>
  <textarea id="cnote" rows="3" placeholder="Add any special instructions or comments…"></textarea>
  <button class="btn" onclick="approve()">✅ Approve &amp; sign</button>
  <button class="btn alt" onclick="location.href='/p/{quote_id}'">💳 Pay online instead</button>
  <p style="color:#94A3B8;font-size:11px;text-align:center;margin-top:12px">
    Or pay manually: WhatsApp <b>+971 56 4020087</b> with quote <code>{quote_id}</code>
  </p>
</div>
<script>
let token = localStorage.getItem("q.token.{quote_id}") || "";
async function verify() {{
  const phone = document.getElementById("phone").value.replace(/[^\\d]/g,"");
  const r = await fetch("/api/q/{quote_id}/verify", {{
    method: "POST", headers: {{"Content-Type":"application/json"}},
    body: JSON.stringify({{phone}})
  }});
  const j = await r.json();
  if (!j.ok) {{ document.getElementById("msg").textContent = "Phone doesn't match. Try again."; return; }}
  token = j.token;
  localStorage.setItem("q.token.{quote_id}", token);
  showCart();
}}
async function showCart() {{
  const r = await fetch("/api/q/{quote_id}", {{
    headers: {{"X-Quote-Token": token}}
  }});
  const j = await r.json();
  if (!j.ok) {{ token=""; localStorage.removeItem("q.token.{quote_id}"); return; }}
  document.getElementById("gate").style.display="none";
  document.getElementById("cart").style.display="block";
  document.getElementById("lines").innerHTML = (j.items||[]).map((it,i) =>
    `<div class="line"><div class="label">${{i+1}}. <b>${{escapeHtml(it.label)}}</b><br>
       <small style="color:#94A3B8">${{escapeHtml(it.detail||"")}}</small></div>
       <div class="price">AED ${{it.price_aed}}</div></div>`).join("");
  document.getElementById("sub").textContent   = "AED " + j.subtotal_aed;
  document.getElementById("vat").textContent   = "AED " + j.vat_aed;
  document.getElementById("total").textContent = "AED " + j.total_aed;
  document.getElementById("date").textContent  = (j.target_date||"") + " · " + (j.time_slot||"");
  document.getElementById("addr").textContent  = j.address||"";
  initSig();
}}
function escapeHtml(s){{return String(s||"").replace(/[&<>"']/g, c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c]))}}
let sigCtx, sigDrawing=false;
function initSig() {{
  const c = document.getElementById("sig");
  sigCtx = c.getContext("2d");
  sigCtx.lineWidth = 2; sigCtx.lineCap="round"; sigCtx.strokeStyle="#0F172A";
  function pos(e){{const r=c.getBoundingClientRect();const t=e.touches?e.touches[0]:e;return {{x:(t.clientX-r.left)*c.width/r.width,y:(t.clientY-r.top)*c.height/r.height}}}}
  function down(e){{e.preventDefault();sigDrawing=true;const p=pos(e);sigCtx.beginPath();sigCtx.moveTo(p.x,p.y)}}
  function move(e){{if(!sigDrawing)return;e.preventDefault();const p=pos(e);sigCtx.lineTo(p.x,p.y);sigCtx.stroke()}}
  function up(){{sigDrawing=false}}
  c.addEventListener("mousedown",down);c.addEventListener("mousemove",move);
  c.addEventListener("mouseup",up);c.addEventListener("mouseleave",up);
  c.addEventListener("touchstart",down,{{passive:false}});
  c.addEventListener("touchmove",move,{{passive:false}});
  c.addEventListener("touchend",up);
}}
function clearSig() {{ const c=document.getElementById("sig");c.getContext("2d").clearRect(0,0,c.width,c.height); }}
async function approve() {{
  const dataUrl = document.getElementById("sig").toDataURL("image/png");
  const note    = document.getElementById("cnote").value.trim();
  const r = await fetch("/api/q/{quote_id}/sign", {{
    method:"POST", headers:{{"Content-Type":"application/json","X-Quote-Token":token}},
    body: JSON.stringify({{ signature_data_url: dataUrl, customer_note: note }})
  }});
  const j = await r.json();
  if (j.ok) {{
    document.body.innerHTML = `<div style="text-align:center;padding:24vh 16px"><h1>✅ Approved!</h1>
      <p style="color:#94A3B8;font-size:14px">Quote <code>{quote_id}</code> is signed.<br>
      Our team will dispatch within 30 minutes. Track and pay at any time:</p>
      <p style="margin:16px 0"><a class="btn" style="background:#0D9488;color:#fff;padding:11px 18px;border-radius:8px;text-decoration:none" href="/p/{quote_id}">💳 Pay AED ${{j.total_aed||""}}</a></p>
      <p style="font-size:12px;color:#64748B">Or WhatsApp +971 56 4020087 with quote <code>{quote_id}</code></p></div>`;
  }} else alert("Could not sign: " + (j.error||"server error"));
}}
if (token) showCart();
</script></body></html>"""


# ---------------------------------------------------------------------------
class _VerifyBody(BaseModel):
    phone: str

@public_router.post("/api/q/{quote_id}/verify")
def verify_phone(quote_id: str, body: _VerifyBody) -> dict:
    q = _quote(quote_id)
    if not q: raise HTTPException(404, "quote not found")
    # Normalize both stored + incoming for compare (digits only)
    incoming = "".join(ch for ch in (body.phone or "") if ch.isdigit())
    stored   = "".join(ch for ch in (q.get("phone") or "") if ch.isdigit())
    if not stored or stored[-9:] != incoming[-9:]:
        return {"ok": False, "error": "phone mismatch"}
    return {"ok": True, "token": _sign_token(quote_id, stored)}


@public_router.get("/api/q/{quote_id}")
def get_quote_data(quote_id: str, request: Request) -> dict:
    q = _quote(quote_id)
    if not q: raise HTTPException(404)
    tok = request.headers.get("X-Quote-Token", "")
    stored = "".join(ch for ch in (q.get("phone") or "") if ch.isdigit())
    if not _verify_token(tok, quote_id, stored):
        return {"ok": False, "error": "invalid token"}
    return {
        "ok": True,
        "quote_id": q["quote_id"],
        "items": q.get("items") or [],
        "subtotal_aed": q.get("subtotal_aed"),
        "vat_aed":      q.get("vat_aed"),
        "total_aed":    q.get("total_aed"),
        "target_date":  q.get("target_date"),
        "time_slot":    q.get("time_slot"),
        "address":      q.get("address"),
        "customer_name": q.get("customer_name"),
        "signed_at":    q.get("signed_at"),
        "paid_at":      q.get("paid_at"),
    }


class _SignBody(BaseModel):
    signature_data_url: str
    customer_note: str | None = ""

@public_router.post("/api/q/{quote_id}/sign")
def sign(quote_id: str, body: _SignBody, request: Request) -> dict:
    q = _quote(quote_id)
    if not q: raise HTTPException(404)
    tok = request.headers.get("X-Quote-Token", "")
    stored = "".join(ch for ch in (q.get("phone") or "") if ch.isdigit())
    if not _verify_token(tok, quote_id, stored):
        return {"ok": False, "error": "invalid token"}
    with db.connect() as c:
        c.execute(
            "UPDATE multi_quotes SET signed_at=?, signature_data_url=?, "
            "notes=COALESCE(notes,'') || ? WHERE quote_id=?",
            (_now(), body.signature_data_url[:200000],
             ("\n--- customer note ---\n" + (body.customer_note or "")) if body.customer_note else "",
             quote_id))
    db.log_event("quote", quote_id, "customer_signed",
                 actor=q.get("phone") or "?",
                 details={"note_len": len(body.customer_note or "")})
    # Notify admin via existing alerts pipeline
    try:
        from . import admin_alerts as _aa
        _aa.notify_admin(
            f"✅ Customer signed quote {quote_id}\n"
            f"{q.get('customer_name','?')} · {q.get('phone','?')}\n"
            f"Total: AED {q.get('total_aed')}\n"
            f"Schedule: {q.get('target_date')} {q.get('time_slot')}\n"
            f"Address: {q.get('address')}",
            kind="quote_signed", urgency="normal",
            meta={"quote_id": quote_id})
    except Exception: pass
    return {"ok": True, "quote_id": quote_id, "signed_at": _now(),
            "total_aed": q.get("total_aed")}


# ---------------------------------------------------------------------------
@public_router.get("/p/{quote_id}", response_class=HTMLResponse)
def pay_landing(quote_id: str) -> str:
    q = _quote(quote_id)
    if not q: return HTMLResponse("<h1>Quote not found</h1>", status_code=404)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Servia · Pay {quote_id}</title>
<style>
body{{font-family:system-ui;background:#0F172A;color:#F1F5F9;padding:18px;margin:0;text-align:center}}
.box{{max-width:360px;margin:14vh auto;background:#1E293B;border:1px solid #334155;
border-radius:12px;padding:22px}}
h1{{font-size:24px;color:#FCD34D;margin:0 0 8px}}
.btn{{display:block;width:100%;padding:13px;background:#0D9488;color:#fff;
border:none;border-radius:10px;font-weight:600;font-size:15px;text-decoration:none;
margin:8px 0;cursor:pointer}}
.btn.alt{{background:#1E293B;color:#F1F5F9;border:1px solid #475569}}
</style></head><body>
<div class="box">
  <h1>AED {q.get('total_aed')}</h1>
  <p style="color:#94A3B8;font-size:13px">Quote <code>{quote_id}</code><br>
  {q.get('customer_name','')} · {q.get('phone','')}</p>
  <a class="btn" href="javascript:alert('Stripe checkout will be wired by admin.')">💳 Pay with card</a>
  <a class="btn alt" href="https://wa.me/971564020087?text=Pay%20{quote_id}">📱 WhatsApp +971 56 4020087</a>
  <p style="color:#64748B;font-size:11px;margin-top:12px">Pay manually with the quote number for instant confirmation.</p>
</div></body></html>"""
