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

# v1.24.147 — centralize WhatsApp number references (no more hardcoding).
def _wa_block():
    """Return (display, raw) WhatsApp number from admin brand_contact config.
    Falls back to "" if not set so we don't render a stale hardcoded number."""
    try:
        from .brand_contact import get_contact_whatsapp, get_contact_phone
        wa = get_contact_whatsapp() or get_contact_phone() or ""
        raw = wa.replace(" ", "").replace("-", "").lstrip("+")
        return wa, raw
    except Exception:
        return "", ""
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


# v1.24.165 — Customer can leave remarks / change requests / reject reasons.
# Stored in a small table; surfaced in admin Quotes tab as 🔔 badge.
def _ensure_remarks_table() -> None:
    with db.connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS quote_remarks (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id      TEXT NOT NULL,
                customer_name TEXT,
                customer_phone TEXT,
                action        TEXT,
                remarks       TEXT NOT NULL,
                created_at    TEXT NOT NULL,
                admin_seen_at TEXT,
                admin_reply   TEXT
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_qr_quote ON quote_remarks(quote_id)")


try:
    _ensure_remarks_table()
except Exception as _e:
    print(f"[quote_remarks] init: {_e}", flush=True)


def _quote(quote_id: str) -> dict | None:
    """v1.24.165 — Fetch a quote from EITHER multi_quotes (bot/chat path)
    OR the admin-created quotes table (commerce admin path). Founder
    reported: 'quotation is not opening on that link' — root cause was
    admin quotes never appearing because this reader only checked
    multi_quotes. Now checks both and normalizes the field names."""
    with db.connect() as c:
        # 1) Try the bot/chat table first (existing path)
        try:
            r = c.execute(
                "SELECT * FROM multi_quotes WHERE quote_id=?",
                (quote_id,),
            ).fetchone()
            if r:
                d = dict(r)
                try: d["items"] = _json.loads(d.get("items_json") or "[]")
                except Exception: d["items"] = []
                return d
        except Exception:
            pass
        # 2) Fall back to the admin-created table (commerce flow)
        try:
            r = c.execute(
                "SELECT * FROM quotes WHERE id=? OR quote_number=?",
                (quote_id, quote_id),
            ).fetchone()
            if r:
                d = dict(r)
                # v1.24.172 — Normalize BOTH the dict fields AND each line
                # item to multi_quotes shape: items need {label, detail,
                # price_aed} instead of {name, qty, unit_price}. Without
                # this the /q/<id> page showed "AED undefined" for every
                # admin-quote line.
                try:
                    raw_items = _json.loads(d.get("line_items_json") or "[]")
                except Exception:
                    raw_items = []
                items: list = []
                for it in raw_items:
                    qty   = float(it.get("qty") or 1)
                    unit  = float(it.get("unit_price") or 0)
                    total = it.get("line_total") or round(qty * unit, 2)
                    name  = it.get("name") or it.get("svc_id") or "Service"
                    detail_parts: list[str] = []
                    if qty and qty != 1:
                        detail_parts.append(f"qty: {qty:g}")
                    if unit:
                        detail_parts.append(f"@ AED {unit:.2f}/unit")
                    items.append({
                        "label":     name,
                        "detail":    " · ".join(detail_parts),
                        "price_aed": float(total),
                        # keep originals too for any consumer that needs them
                        "name":      name,
                        "qty":       qty,
                        "unit_price": unit,
                        "line_total": float(total),
                    })
                d["items"] = items
                d["quote_id"]      = d.get("id") or quote_id
                d["phone"]         = d.get("customer_phone") or ""
                d["customer_name"] = d.get("customer_name") or ""
                d["subtotal_aed"]  = float(d.get("subtotal") or 0)
                d["vat_aed"]       = float(d.get("vat_amount") or 0)
                d["total_aed"]     = float(d.get("total") or 0)
                d["target_date"]   = d.get("valid_until") or ""
                d["time_slot"]     = d.get("time_slot") or ""
                d["address"]       = d.get("customer_address") or ""
                return d
        except Exception:
            pass
    return None


def _sign_token(quote_id: str, phone: str) -> str:
    s = get_settings()
    secret = (getattr(s, "ADMIN_TOKEN", "") or "lumora-token").encode()
    msg = f"{quote_id}|{phone}".encode()
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()[:32]


def _verify_token(token: str, quote_id: str, phone: str) -> bool:
    return hmac.compare_digest(token or "", _sign_token(quote_id, phone))


# v1.24.172 — Unguessable share token derived from quote_id alone (no phone).
# Founder: 'quotation shared URL should be encoded so anyone can't guess and
# check the quotation'. Anyone with the link is presumed authorized.
def _share_token(quote_id: str) -> str:
    s = get_settings()
    secret = (getattr(s, "ADMIN_TOKEN", "") or "lumora-token").encode()
    return hmac.new(secret, f"share|{quote_id}".encode(),
                    hashlib.sha256).hexdigest()[:16]


def _verify_share_token(token: str, quote_id: str) -> bool:
    if not token:
        return False
    return hmac.compare_digest(token, _share_token(quote_id))


# ---------------------------------------------------------------------------
@public_router.get("/q/{quote_id}", response_class=HTMLResponse)
def quote_landing(quote_id: str, request: Request = None, t: str = "") -> str:
    """v1.24.172 — `?t=<share_token>` lets the customer-with-link bypass
    the phone gate (founder ask: 'shared URL should be encoded so anyone
    can't guess and check the quotation'). Without t=, phone gate still
    applies."""
    q = _quote(quote_id)
    if not q:
        return HTMLResponse("<h1>Quote not found</h1>", status_code=404)
    # v1.24.168 — Track every page open for admin analytics overlay.
    # Founder: 'in that URL for admin maintain full analytics — which
    # customer opened, browser, location, when. Full history.'
    try:
        ua = ""
        ip = ""
        if request is not None:
            ua = (request.headers.get("user-agent") or "")[:300]
            # Railway sits behind a proxy → trust X-Forwarded-For
            ip = (request.headers.get("x-forwarded-for") or
                  (request.client.host if request.client else "")) or ""
            ip = ip.split(",")[0].strip()[:64]
        with db.connect() as c:
            c.execute(
                "INSERT INTO events (entity_type, entity_id, action, actor, details_json, created_at) "
                "VALUES ('quote', ?, 'view_open', 'customer', ?, ?)",
                (quote_id, _json.dumps({"ua": ua, "ip": ip}), _now()),
            )
    except Exception:
        pass
    # v1.24.172 — Precompute the DIRECT pay URL (skip the /p/<id>
    # intermediate page that the founder rightly called 'useless extra
    # clicks'). In GATE_BOOKINGS mode → /gate.html. In live mode → the
    # real gateway URL from quotes._make_payment_link.
    from .config import get_settings as _gs
    _amount = q.get("total_aed") or 0
    if _gs().GATE_BOOKINGS:
        direct_pay_url = f"/gate.html?inv={quote_id}&amount={_amount}"
    else:
        try:
            from . import quotes as _qs
            direct_pay_url = _qs._make_payment_link(quote_id, float(_amount), "AED")
        except Exception:
            # Final fallback — the legacy /p landing
            direct_pay_url = f"/p/{quote_id}"

    # v1.24.78 — light-theme redesign matching brand palette (teal/amber).
    # Designed per CLAUDE.md DESIGN-REVIEW gate: brand-aligned hero,
    # uniform typography, ≥44px touch targets, semantic color roles
    # (primary teal, accent amber, success green, danger red).
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Servia · Quote {quote_id}</title>
<link rel="stylesheet" href="/style.css">
<style>
:root {{ --t:#0F766E; --t2:#0D9488; --tl:#F0FDFA; --acc:#F59E0B; --bg:#F8FAFC;
         --tx:#0F172A; --mu:#64748B; --ln:#E2E8F0; --ok:#10B981; --er:#DC2626; }}
body {{ font-family: -apple-system, system-ui, sans-serif; background: var(--bg);
       color: var(--tx); padding: 0; margin: 0; min-height: 100vh; }}
.hdr {{ background: linear-gradient(135deg, var(--t) 0%, var(--t2) 100%);
       color: #fff; padding: 18px 16px; text-align: center; }}
.hdr h1 {{ margin: 0; font-size: 19px; letter-spacing: -.01em; font-weight: 800; }}
.hdr .sub {{ font-size: 12px; opacity: .9; margin-top: 4px; font-family: monospace; }}
.wrap {{ max-width: 560px; margin: 0 auto; padding: 16px; }}
.card {{ background: #fff; border: 1px solid var(--ln); border-radius: 14px;
        padding: 18px; box-shadow: 0 4px 16px rgba(15,23,42,.06); margin-bottom: 14px; }}
.gate input {{ width: 100%; padding: 12px; font-size: 15px; background: #fff;
              color: var(--tx); border: 1.5px solid var(--ln); border-radius: 9px;
              font-family: inherit; box-sizing: border-box; min-height: 44px; }}
.gate input:focus {{ outline: none; border-color: var(--t); box-shadow: 0 0 0 3px rgba(15,118,110,.15); }}
.btn {{ display: inline-flex; align-items: center; justify-content: center; gap: 6px;
       padding: 12px 16px; min-height: 44px; background: var(--t); color: #fff;
       border: none; border-radius: 9px; font-weight: 700; font-size: 14px; cursor: pointer;
       text-decoration: none; font-family: inherit; transition: background .12s, transform .08s; }}
.btn:hover {{ background: var(--t2); transform: translateY(-1px); }}
.btn.full {{ width: 100%; margin: 8px 0; }}
.btn.alt {{ background: #fff; color: var(--t); border: 1.5px solid var(--t); }}
.btn.alt:hover {{ background: var(--tl); transform: translateY(-1px); }}
.gate {{ display: block; }}
.cart {{ display: none; }}
.line {{ display: grid; grid-template-columns: 24px 1fr auto; gap: 8px;
        align-items: baseline; padding: 8px 0; border-bottom: 1px solid #F1F5F9; }}
.line .num {{ color: var(--mu); font-weight: 700; font-size: 12px; }}
.line .nm {{ font-weight: 600; color: var(--tx); }}
.line .det {{ display: block; grid-column: 2; font-size: 12px; color: var(--mu); }}
.line .pr {{ font-weight: 700; color: var(--t); }}
.totals .row {{ display: flex; justify-content: space-between; padding: 4px 0;
               font-size: 13px; color: var(--mu); }}
.totals .row.total {{ font-size: 18px; font-weight: 800; color: var(--t);
                     padding-top: 8px; border-top: 1px solid var(--ln); margin-top: 6px; }}
.meta {{ background: var(--tl); border-radius: 9px; padding: 10px 12px; margin: 12px 0;
        font-size: 13px; line-height: 1.7; }}
.feature {{ font-size: 12px; color: var(--mu); line-height: 1.55; background: #FEF3C7;
           border-left: 3px solid var(--acc); padding: 10px 12px; margin: 10px 0;
           border-radius: 0 8px 8px 0; }}
canvas {{ background: #fff; border: 1.5px dashed var(--t); border-radius: 9px;
         width: 100%; height: 140px; display: block; margin: 8px 0; cursor: crosshair;
         touch-action: none; }}
textarea {{ width: 100%; padding: 10px; background: #fff; color: var(--tx);
           border: 1.5px solid var(--ln); border-radius: 9px; font: inherit;
           margin-top: 4px; box-sizing: border-box; min-height: 60px; resize: vertical; }}
textarea:focus {{ outline: none; border-color: var(--t); }}
h3 {{ font-size: 14px; margin: 14px 0 6px; color: var(--tx); }}
.msg {{ font-size: 12px; min-height: 16px; margin-top: 8px; text-align: center; }}
.msg.err {{ color: var(--er); }}
.row-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
@media (max-width: 380px) {{ .row-2 {{ grid-template-columns: 1fr; }} }}
</style></head><body>
<div class="hdr">
  <img src="/brand/servia-logo-full.svg" alt="Servia"
       style="height:32px;margin-bottom:6px;filter:brightness(0) invert(1)"
       onerror="this.style.display='none'">
  <h1 style="margin:2px 0 4px">Your Servia Quote</h1>
  <div class="sub">{quote_id}</div>
  <div style="font-size:11px;opacity:.8;margin-top:6px">
    🛡️ 256-bit SSL · AED billed · No-show refund · 4.9★ from 2,400+ families
  </div>
</div>
<div class="wrap">
  <div class="gate card" id="gate">
    <h3 style="margin-top:0;text-align:center">View your quote</h3>
    <p style="color:var(--mu);font-size:13px;text-align:center;margin:6px 0 14px">
      Enter the phone number you used when requesting this quote.
    </p>
    <input id="phone" type="tel" placeholder="0559396459" autocomplete="tel" inputmode="tel">
    <button class="btn full" onclick="verify()">👁 View quote</button>
    <p id="msg" class="msg err"></p>
  </div>
  <div class="cart" id="cart">
    <div class="card">
      <div id="lines"></div>
      <div class="totals" style="margin-top:12px">
        <div class="row"><span>Subtotal</span><span id="sub">—</span></div>
        <div class="row"><span>VAT 5%</span><span id="vat">—</span></div>
        <div class="row total"><span>Total</span><span id="total">—</span></div>
      </div>
      <div class="meta">
        📅 <b id="date"></b><br>
        📍 <span id="addr"></span>
      </div>
    </div>
    <div class="card">
      <div class="feature">
        ✍️ <b>Sign below to approve.</b> After your service, we'll upload before/after
        photos and live status updates to this same page — view them anytime.
      </div>

      <!-- v1.24.172 — Docusign-style three-way sign: draw, type, or
           scan-on-mobile. Founder asked for 'multiple ways like DocuSign:
           dragging the pen / typing a name / signing on mobile via QR'. -->
      <div style="display:flex;gap:4px;margin-bottom:8px">
        <button type="button" id="sig-tab-draw" class="sig-tab active" onclick="setSigMode('draw')"
          style="flex:1;padding:8px 6px;border:1px solid var(--ln);background:#fff;border-radius:6px;font-size:12px;font-weight:700;cursor:pointer">
          ✍️ Draw
        </button>
        <button type="button" id="sig-tab-type" class="sig-tab" onclick="setSigMode('type')"
          style="flex:1;padding:8px 6px;border:1px solid var(--ln);background:#fff;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer">
          🅰️ Type
        </button>
        <button type="button" id="sig-tab-phone" class="sig-tab" onclick="setSigMode('phone')"
          style="flex:1;padding:8px 6px;border:1px solid var(--ln);background:#fff;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer">
          📱 Send to phone
        </button>
      </div>

      <div id="sig-pane-draw">
        <canvas id="sig" width="500" height="140"></canvas>
        <div class="row-2" style="margin-top:6px">
          <button class="btn alt" onclick="clearSig()">Clear</button>
          <button class="btn" onclick="approve()">✅ Approve &amp; sign</button>
        </div>
      </div>

      <div id="sig-pane-type" style="display:none">
        <p style="font-size:12.5px;color:var(--mu);margin:4px 0 8px">
          Type your full legal name — we'll render it in a signature font and
          treat it as a legally binding e-signature (UAE Electronic
          Transactions Law 2021).
        </p>
        <input id="sig-typed" type="text" placeholder="Your full legal name"
               oninput="renderTypedSig()"
               style="width:100%;padding:12px;border:1px solid var(--ln);border-radius:8px;font-size:15px">
        <div id="sig-typed-preview"
             style="border:1px dashed var(--ln);border-radius:8px;padding:18px;text-align:center;margin:8px 0;min-height:80px;font-family:'Brush Script MT','Lucida Handwriting',cursive;font-size:32px;color:#0F172A">
          <span style="color:var(--mu);font-family:system-ui;font-size:13px">Your typed signature will preview here</span>
        </div>
        <div class="row-2">
          <button class="btn alt" onclick="document.getElementById('sig-typed').value='';renderTypedSig()">Clear</button>
          <button class="btn" onclick="approveTyped()">✅ Approve &amp; sign</button>
        </div>
      </div>

      <div id="sig-pane-phone" style="display:none;text-align:center">
        <p style="font-size:12.5px;color:var(--mu);margin:4px 0 10px">
          Scan this QR with your phone to open the quote on your mobile and
          sign there. The link is the same URL — your signature applies here
          when you submit on your phone.
        </p>
        <img id="sig-qr" alt="Scan to sign on phone"
             style="width:200px;height:200px;background:#fff;padding:10px;border-radius:12px;border:1px solid var(--ln)"
             src="">
        <p style="font-size:11px;color:var(--mu);margin:10px 0 0">
          Or copy the link: <code id="sig-link-code" style="background:#F0FDFA;padding:3px 6px;border-radius:4px;font-size:11px">…</code>
          <button type="button" onclick="copyShareLink()" style="background:#fff;border:1px solid var(--ln);padding:3px 8px;border-radius:5px;font-size:11px;cursor:pointer;margin-left:6px">📋 Copy</button>
        </p>
      </div>

      <h3 style="margin-top:14px">💬 Add notes (optional)</h3>
      <textarea id="cnote" rows="3" placeholder="Special instructions, parking info, etc."></textarea>
    </div>

    <!-- v1.24.165 — Customer remark / change request / reject reason -->
    <div class="card" id="remark-card" style="background:#FEFCE8;border:1px solid #FDE68A">
      <h3>🗨️ Want changes or have questions?</h3>
      <p style="color:var(--mu);font-size:13px;margin:-4px 0 8px">
        Write below — our admin gets notified instantly and will reply via WhatsApp.
      </p>
      <textarea id="cremarks" rows="3" placeholder="e.g. Can we move the date to Saturday? Or only do bedrooms 1–2, skip the kitchen."></textarea>
      <div class="row-2" style="margin-top:8px">
        <button class="btn alt" onclick="sendRemark('change_request')">📝 Request changes</button>
        <button class="btn" style="background:#DC2626" onclick="sendRemark('reject')">❌ Reject with reason</button>
      </div>
      <p style="font-size:11px;color:var(--mu);margin:6px 0 0">
        You can also <a href="#" onclick="document.querySelector('.servia-chat-online,.us-launcher,.cmdk-fab')?.click();return false;" style="color:var(--t);font-weight:700">💬 chat with Servia AI</a>
        — ask anything about this quote (what's included, can you do X, when can you start, etc.).
      </p>
    </div>

    <div class="card" style="text-align:center">
      <!-- v1.24.172 — DIRECT link to gateway (gate.html in stealth mode,
           Stripe/Ziina in live). Founder demanded skipping the /p/<id>
           intermediate page that added 'useless extra clicks'. -->
      <a class="btn full alt" href="{direct_pay_url}">💳 Pay AED <span id="payAmount">{_amount}</span> securely</a>
      <p style="color:var(--mu);font-size:12px;margin:10px 0 0">
        Or pay manually via WhatsApp <b>{_wa_block()[0] or 'see /contact'}</b> with quote <code>{quote_id}</code>.
      </p>
    </div>
  </div>
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
    `<div class="line"><span class="num">${{i+1}}</span>
       <div><span class="nm">${{escapeHtml(it.label)}}</span>
            <span class="det">${{escapeHtml(it.detail||"")}}</span></div>
       <span class="pr">AED ${{it.price_aed}}</span></div>`).join("");
  document.getElementById("sub").textContent   = "AED " + j.subtotal_aed;
  document.getElementById("vat").textContent   = "AED " + j.vat_aed;
  document.getElementById("total").textContent = "AED " + j.total_aed;
  document.getElementById("date").textContent  = (j.target_date||"") + " at " + (j.time_slot||"");
  document.getElementById("addr").textContent  = j.address||"";
  const pa = document.getElementById("payAmount");
  if (pa) pa.textContent = j.total_aed;
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

// v1.24.172 — Docusign-style: switch between draw / type / phone modes.
function setSigMode(mode) {{
  ["draw","type","phone"].forEach(m => {{
    const tab = document.getElementById(`sig-tab-${{m}}`);
    const pane = document.getElementById(`sig-pane-${{m}}`);
    if (tab) {{
      tab.classList.toggle("active", m === mode);
      tab.style.background = m === mode ? "#0F766E" : "#fff";
      tab.style.color      = m === mode ? "#fff" : "#0F172A";
    }}
    if (pane) pane.style.display = m === mode ? "block" : "none";
  }});
  if (mode === "phone") {{
    const url = location.href;
    const qr = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${{encodeURIComponent(url)}}`;
    document.getElementById("sig-qr").src = qr;
    document.getElementById("sig-link-code").textContent = url.replace(/^https?:\\/\\//, "");
  }}
}}

function copyShareLink() {{
  navigator.clipboard.writeText(location.href);
  alert("✓ Link copied. Open it on your phone to sign there.");
}}

function renderTypedSig() {{
  const v = (document.getElementById("sig-typed").value || "").trim();
  const wrap = document.getElementById("sig-typed-preview");
  if (!v) {{
    wrap.innerHTML = '<span style="color:#64748B;font-family:system-ui;font-size:13px">Your typed signature will preview here</span>';
  }} else {{
    wrap.textContent = v;
  }}
}}

// Convert the typed name into a PNG dataURL (canvas → toDataURL) so it
// goes through the SAME /sign endpoint as drawn signatures. No backend
// change needed.
function _typedNameToDataUrl(name) {{
  const cnv = document.createElement("canvas");
  cnv.width = 500; cnv.height = 140;
  const ctx = cnv.getContext("2d");
  ctx.fillStyle = "#fff"; ctx.fillRect(0,0,cnv.width,cnv.height);
  ctx.fillStyle = "#0F172A";
  ctx.font = "italic 56px 'Brush Script MT', 'Lucida Handwriting', cursive";
  ctx.textBaseline = "middle";
  ctx.textAlign = "center";
  ctx.fillText(name, cnv.width/2, cnv.height/2);
  return cnv.toDataURL("image/png");
}}

async function approveTyped() {{
  const name = (document.getElementById("sig-typed").value || "").trim();
  if (!name || name.length < 2) {{
    alert("Please type your full name to sign.");
    return;
  }}
  const dataUrl = _typedNameToDataUrl(name);
  const note    = document.getElementById("cnote").value.trim();
  try {{
    const r = await fetch("/api/q/{quote_id}/sign", {{
      method:"POST", headers:{{"Content-Type":"application/json","X-Quote-Token":token}},
      body: JSON.stringify({{ signature_data_url: dataUrl,
                              customer_note: (note ? note + "\\n" : "") + `[Typed signature: ${{name}}]` }})
    }});
    const j = await r.json();
    if (j.ok) {{
      document.body.innerHTML = `<div style="background:#F8FAFC;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:16px">
        <div style="background:#fff;border:1px solid #E2E8F0;border-radius:16px;padding:32px 24px;max-width:480px;text-align:center;box-shadow:0 8px 32px rgba(15,23,42,.08)">
          <div style="background:#D1FAE5;color:#065F46;width:64px;height:64px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:32px;margin-bottom:14px">✓</div>
          <h1 style="margin:0 0 8px;font-size:22px;color:#0F172A;letter-spacing:-.01em">Signed by <i>${{name}}</i>!</h1>
          <p style="color:#64748B;font-size:14px;margin:0 0 20px;line-height:1.6">Quote <code style="background:#F0FDFA;color:#0F766E;padding:2px 6px;border-radius:4px">{quote_id}</code> is approved.<br>Our team will dispatch within 30 minutes.</p>
          <a href="/p/{quote_id}" style="display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:14px 28px;min-height:44px;background:linear-gradient(135deg,#0F766E,#0D9488);color:#fff;border-radius:9px;font-weight:700;text-decoration:none;font-size:15px">💳 Pay AED ${{j.total_aed||""}}</a>
        </div>
      </div>`;
    }} else alert("Could not sign: " + (j.error||"server error"));
  }} catch(e) {{ alert("Network error — please try again."); }}
}}

// v1.24.165 — Customer leaves a remark / change request / reject reason.
// Posts to /api/q/<id>/remark. Admin gets a 🔔 alert in /admin-commerce.
async function sendRemark(action) {{
  const txt = (document.getElementById("cremarks").value || "").trim();
  if (!txt) {{ alert("Please write what you'd like to change or ask."); return; }}
  if (action === "reject" && !confirm("Reject this quote with the reason above? Admin will be notified.")) return;
  try {{
    const r = await fetch("/api/q/{quote_id}/remark", {{
      method:"POST", headers:{{"Content-Type":"application/json","X-Quote-Token":token}},
      body: JSON.stringify({{ action, remarks: txt, session_id: new URLSearchParams(location.search).get("sid") }})
    }});
    const j = await r.json();
    if (j.ok) {{
      const card = document.getElementById("remark-card");
      card.innerHTML = `<div style="text-align:center;padding:18px 6px">
        <div style="background:#D1FAE5;color:#065F46;width:56px;height:56px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:28px;margin-bottom:10px">✓</div>
        <h3 style="margin:0 0 6px">Thanks — we've received your message.</h3>
        <p style="color:var(--mu);font-size:13px;margin:0">Our team will reply on WhatsApp within an hour. You can keep this page open to track updates.</p>
      </div>`;
    }} else alert("Could not send: " + (j.error||"server error"));
  }} catch (e) {{ alert("Network error — please try again."); }}
}}

async function approve() {{
  const dataUrl = document.getElementById("sig").toDataURL("image/png");
  const note    = document.getElementById("cnote").value.trim();
  const r = await fetch("/api/q/{quote_id}/sign", {{
    method:"POST", headers:{{"Content-Type":"application/json","X-Quote-Token":token}},
    body: JSON.stringify({{ signature_data_url: dataUrl, customer_note: note }})
  }});
  const j = await r.json();
  if (j.ok) {{
    document.body.innerHTML = `<div style="background:#F8FAFC;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:16px">
      <div style="background:#fff;border:1px solid #E2E8F0;border-radius:16px;padding:32px 24px;max-width:480px;text-align:center;box-shadow:0 8px 32px rgba(15,23,42,.08)">
        <div style="background:#D1FAE5;color:#065F46;width:64px;height:64px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:32px;margin-bottom:14px">✓</div>
        <h1 style="margin:0 0 8px;font-size:22px;color:#0F172A;letter-spacing:-.01em">Quote signed!</h1>
        <p style="color:#64748B;font-size:14px;margin:0 0 20px;line-height:1.6">Quote <code style="background:#F0FDFA;color:#0F766E;padding:2px 6px;border-radius:4px">{quote_id}</code> is approved.<br>Our team will dispatch within 30 minutes.</p>
        <a href="/p/{quote_id}" style="display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:14px 28px;min-height:44px;background:linear-gradient(135deg,#0F766E,#0D9488);color:#fff;border-radius:9px;font-weight:700;text-decoration:none;font-size:15px">💳 Pay AED ${{j.total_aed||""}}</a>
        <p style="font-size:12px;color:#94A3B8;margin:16px 0 0">Or WhatsApp <b>{_wa_block()[0] or "see /contact"}</b> with quote <code>{quote_id}</code></p>
      </div>
    </div>`;
  }} else alert("Could not sign: " + (j.error||"server error"));
}}
// v1.24.82 — if ?sid=<session_id> is in URL and matches the chat that
// created this quote, bypass the phone gate entirely. The chat session
// is already an authenticated context. Removes the "ask for phone
// twice" UX wart the customer hit when clicking View from in-chat card.
async function _trySidAuth() {{
  const u = new URL(location.href);
  const sid = u.searchParams.get("sid");
  if (!sid) return false;
  try {{
    const r = await fetch(`/api/q/{quote_id}/card?session_id=${{encodeURIComponent(sid)}}`);
    const j = await r.json();
    if (!j.ok) return false;
    // Synthesize a token that the existing showCart() flow uses
    document.getElementById("gate").style.display = "none";
    document.getElementById("cart").style.display = "block";
    document.getElementById("lines").innerHTML = (j.items||[]).map((it,i) =>
      `<div class="line"><span class="num">${{i+1}}</span>
         <div><span class="nm">${{escapeHtml(it.label)}}</span>
              <span class="det">${{escapeHtml(it.detail||"")}}</span></div>
         <span class="pr">AED ${{it.price_aed}}</span></div>`).join("");
    document.getElementById("sub").textContent   = "AED " + j.subtotal_aed;
    document.getElementById("vat").textContent   = "AED " + j.vat_aed;
    document.getElementById("total").textContent = "AED " + j.total_aed;
    document.getElementById("date").textContent  = (j.target_date||"") + " at " + (j.time_slot||"");
    document.getElementById("addr").textContent  = j.address||"";
    const pa = document.getElementById("payAmount"); if (pa) pa.textContent = j.total_aed;
    // Stash session_id so the sign POST can use it as auth
    window.__SERVIA_SID = sid;
    initSig();
    return true;
  }} catch(e) {{ return false; }}
}}
// Override approve() to use session_id auth when sid was supplied
const __origApprove = approve;
approve = async function() {{
  if (!window.__SERVIA_SID) return __origApprove();
  const dataUrl = document.getElementById("sig").toDataURL("image/png");
  const note    = document.getElementById("cnote").value.trim();
  const r = await fetch("/api/q/{quote_id}/sign", {{
    method:"POST", headers:{{"Content-Type":"application/json"}},
    body: JSON.stringify({{ signature_data_url: dataUrl, customer_note: note,
                           session_id: window.__SERVIA_SID }})
  }});
  const j = await r.json();
  if (j.ok) {{
    document.body.innerHTML = `<div style="background:#F8FAFC;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:16px">
      <div style="background:#fff;border:1px solid #E2E8F0;border-radius:16px;padding:32px 24px;max-width:480px;text-align:center;box-shadow:0 8px 32px rgba(15,23,42,.08)">
        <div style="background:#D1FAE5;color:#065F46;width:64px;height:64px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:32px;margin-bottom:14px">✓</div>
        <h1 style="margin:0 0 8px;font-size:22px;color:#0F172A">Quote signed!</h1>
        <p style="color:#64748B;font-size:14px;margin:0 0 20px;line-height:1.6">Quote <code style="background:#F0FDFA;color:#0F766E;padding:2px 6px;border-radius:4px">{quote_id}</code> is approved. <b>100% advance payment</b> applies.</p>
        <a href="/p/{quote_id}?sid=${{encodeURIComponent(window.__SERVIA_SID)}}" style="display:inline-flex;padding:14px 28px;background:linear-gradient(135deg,#0F766E,#0D9488);color:#fff;border-radius:9px;font-weight:700;text-decoration:none">💳 Pay AED ${{j.total_aed||""}}</a>
      </div>
    </div>`;
  }} else alert("Could not sign: " + (j.error||"server error"));
}};
(async () => {{
  if (await _trySidAuth()) return;  // session auth succeeded
  if (token) showCart();           // fall back to stored phone token
}})();
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
    session_id: str | None = None  # v1.24.78 — chat-session signing


# v1.24.78 — in-chat quote card endpoint. Returns the same data as
# /api/q/<id> but is gated by session_id (the chat that CREATED this
# quote) instead of the phone-typed token. Lets the widget render the
# card immediately without asking the customer to re-type their phone.
@public_router.get("/api/q/{quote_id}/card")
def get_quote_card(quote_id: str, session_id: str = "") -> dict:
    q = _quote(quote_id)
    if not q: raise HTTPException(404)
    # session_id is REQUIRED — auth must always be checked.
    if not session_id:
        return {"ok": False, "error": "session_id required"}
    with db.connect() as c:
        ev = c.execute(
            "SELECT 1 FROM events WHERE entity_type='quote' AND entity_id=? "
            "AND json_extract(details_json,'$.session_id')=? LIMIT 1",
            (quote_id, session_id),
        ).fetchone()
    if not ev:
        return {"ok": False, "error": "session does not own this quote"}
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
        "phone":         q.get("phone"),
        "signed_at":    q.get("signed_at"),
        "paid_at":      q.get("paid_at"),
        "view_url":     f"/q/{quote_id}",
        "pdf_url":      f"/i/{quote_id}.pdf",
        "print_url":    f"/i/{quote_id}",
        "pay_url":      f"/p/{quote_id}",
    }


class _RemarkBody(BaseModel):
    """v1.24.165 — Customer leaves a remark / change-request / reject reason
    from the /q/<id> page. Auth via phone-gate token (same as /sign)."""
    action:  str           # 'change_request' | 'reject' | 'question'
    remarks: str           # free-text body
    session_id: str | None = None


@public_router.post("/api/q/{quote_id}/remark")
def post_remark(quote_id: str, body: _RemarkBody, request: Request) -> dict:
    q = _quote(quote_id)
    if not q: raise HTTPException(404)
    tok = request.headers.get("X-Quote-Token", "")
    stored = "".join(ch for ch in (q.get("phone") or "") if ch.isdigit())
    auth_ok = _verify_token(tok, quote_id, stored)
    if not auth_ok and body.session_id:
        with db.connect() as c:
            ev = c.execute(
                "SELECT 1 FROM events WHERE entity_type='quote' AND entity_id=? "
                "AND json_extract(details_json,'$.session_id')=? LIMIT 1",
                (quote_id, body.session_id),
            ).fetchone()
        auth_ok = bool(ev)
    if not auth_ok:
        return {"ok": False, "error": "invalid token"}
    action = (body.action or "").strip().lower()
    if action not in ("change_request", "reject", "question", "accepted"):
        return {"ok": False, "error": "invalid action"}
    text = (body.remarks or "").strip()
    if not text:
        return {"ok": False, "error": "remarks required"}
    with db.connect() as c:
        c.execute(
            "INSERT INTO quote_remarks (quote_id, customer_name, customer_phone, "
            " action, remarks, created_at) VALUES (?,?,?,?,?,?)",
            (quote_id, q.get("customer_name"), q.get("phone"),
             action, text, _now()),
        )
        # Echo into events table so the existing admin live-feed picks it up.
        try:
            c.execute(
                "INSERT INTO events (entity_type, entity_id, action, actor, details_json, created_at) "
                "VALUES ('quote', ?, ?, 'customer', ?, ?)",
                (quote_id, f"customer_{action}", _json.dumps({
                    "remarks": text, "customer": q.get("customer_name"),
                }), _now()),
            )
        except Exception:
            pass
    return {"ok": True, "action": action}


@public_router.post("/api/q/{quote_id}/sign")
def sign(quote_id: str, body: _SignBody, request: Request) -> dict:
    q = _quote(quote_id)
    if not q: raise HTTPException(404)
    tok = request.headers.get("X-Quote-Token", "")
    stored = "".join(ch for ch in (q.get("phone") or "") if ch.isdigit())
    # v1.24.78 — accept either phone-token (page form) OR session_id
    # (in-chat card). Either is sufficient proof of ownership.
    auth_ok = _verify_token(tok, quote_id, stored)
    if not auth_ok and body.session_id:
        with db.connect() as c:
            ev = c.execute(
                "SELECT 1 FROM events WHERE entity_type='quote' AND entity_id=? "
                "AND json_extract(details_json,'$.session_id')=? LIMIT 1",
                (quote_id, body.session_id),
            ).fetchone()
        auth_ok = bool(ev)
    if not auth_ok:
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
    # v1.24.76 — honour GATE_BOOKINGS scope-of-work. The "Pay with card"
    # button must NOT actually charge during stealth-launch — it routes
    # to /gate.html where we show a friendly "your card was declined by
    # bank" message and capture the customer's interest with a 15% off
    # voucher. This was previously a javascript:alert placeholder.
    from .config import get_settings as _gs
    if _gs().GATE_BOOKINGS:
        pay_url = f"/gate.html?inv={quote_id}&amount={q.get('total_aed') or 0}"
    else:
        # In live mode, route through the proper gateway link helper.
        try:
            from . import quotes as _qs
            pay_url = _qs._make_payment_link(
                quote_id, float(q.get('total_aed') or 0), "AED")
        except Exception:
            pay_url = f"/pay/{quote_id}"
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Servia · Pay {quote_id}</title>
<style>
:root {{ --t:#0F766E; --t2:#0D9488; --bg:#F8FAFC; --tx:#0F172A; --mu:#64748B; --ln:#E2E8F0; }}
body {{ font-family: -apple-system, system-ui, sans-serif; background: var(--bg);
       color: var(--tx); padding: 16px; margin: 0; min-height: 100vh;
       display: flex; align-items: center; justify-content: center; }}
.box {{ background: #fff; border: 1px solid var(--ln); border-radius: 16px;
       padding: 32px 24px; max-width: 420px; width: 100%; text-align: center;
       box-shadow: 0 8px 32px rgba(15,23,42,.08); }}
.amount {{ font-size: 36px; color: var(--t); font-weight: 800; letter-spacing: -.02em;
          margin: 0 0 4px; }}
.amount .cur {{ font-size: 16px; color: var(--mu); font-weight: 600; vertical-align: super; margin-right: 4px; }}
.qid {{ font-family: monospace; background: #F0FDFA; color: var(--t); padding: 3px 8px;
       border-radius: 4px; font-size: 13px; }}
.cust {{ color: var(--mu); font-size: 13px; margin: 12px 0 22px; line-height: 1.6; }}
.btn {{ display: inline-flex; align-items: center; justify-content: center; gap: 6px;
       width: 100%; padding: 14px; min-height: 44px; background: linear-gradient(135deg,var(--t),var(--t2));
       color: #fff; border: none; border-radius: 11px; font-weight: 700; font-size: 15px;
       text-decoration: none; margin: 8px 0; cursor: pointer; box-sizing: border-box;
       font-family: inherit; transition: transform .08s; }}
.btn:hover {{ transform: translateY(-1px); }}
.btn.alt {{ background: #fff; color: #25D366; border: 1.5px solid #25D366; }}
.btn.alt:hover {{ background: #F0FDF4; }}
.note {{ color: var(--mu); font-size: 12px; margin-top: 16px; line-height: 1.5; }}
</style></head><body>
<div class="box">
  <p class="amount"><span class="cur">AED</span>{q.get('total_aed')}</p>
  <p class="cust">Quote <span class="qid">{quote_id}</span><br>
  {q.get('customer_name','')} · {q.get('phone','')}</p>
  <a class="btn" href="{pay_url}">💳 Pay with card</a>
  <a class="btn alt" href="https://wa.me/{_wa_block()[1]}?text=Pay%20{quote_id}">📱 WhatsApp {_wa_block()[0] or ""}</a>
  <p class="note">Pay manually via WhatsApp with the quote number for instant confirmation.</p>
</div></body></html>"""


# ---------------------------------------------------------------------------
# v1.24.57 — invoice HTML + native PDF
@public_router.get("/i/{quote_id}", response_class=HTMLResponse)
def invoice_view(quote_id: str):
    # v1.24.73 — FastAPI matches "/i/{quote_id}" before "/i/{quote_id}.pdf"
    # because of registration order, so /i/Q-XXX.pdf was being routed here
    # with quote_id="Q-XXX.pdf" and 404'ing. Detect the .pdf suffix and
    # delegate to the PDF handler.
    if quote_id.endswith(".pdf"):
        return invoice_pdf(quote_id[:-4])
    q = _quote(quote_id)
    if not q: return HTMLResponse("<h1>Invoice not found</h1>", status_code=404)
    items_html = "".join(
        f"<tr><td>{i+1}</td><td><b>{it['label']}</b><br><small>{it.get('detail','')}</small></td>"
        f"<td style='text-align:right'>AED {it['price_aed']}</td></tr>"
        for i, it in enumerate(q.get("items") or []))
    paid = bool(q.get("paid_at"))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Servia Invoice {quote_id}</title>
<style>
body{{font:14px/1.5 system-ui;background:#fff;color:#111;padding:20px;max-width:720px;margin:0 auto}}
.head{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2px solid #0D9488;padding-bottom:14px;margin-bottom:18px}}
.head .brand{{font-size:24px;font-weight:700;color:#0D9488}}
.head .meta{{text-align:right;font-size:12.5px;color:#64748B}}
table{{width:100%;border-collapse:collapse;margin:12px 0}}
table th{{background:#F1F5F9;text-align:left;padding:8px;font-size:12px;font-weight:600}}
table td{{padding:8px;border-bottom:1px solid #E2E8F0;font-size:13px;vertical-align:top}}
.totals{{margin-top:14px;float:right;width:300px}}
.totals .row{{display:flex;justify-content:space-between;padding:4px 0;font-size:13px}}
.totals .row.total{{font-size:17px;font-weight:700;border-top:2px solid #0D9488;padding-top:8px;margin-top:6px;color:#0D9488}}
.stamp{{display:inline-block;border:2px solid {('#10B981' if paid else '#DC2626')};color:{('#10B981' if paid else '#DC2626')};font-weight:700;padding:4px 12px;border-radius:6px;transform:rotate(-3deg);font-size:13px;margin-top:14px}}
.btn{{display:inline-block;padding:9px 14px;background:#0D9488;color:#fff;border-radius:6px;font-size:13px;text-decoration:none;margin:8px 4px}}
.note{{font-size:11px;color:#64748B;border-top:1px solid #E2E8F0;padding-top:10px;margin-top:24px;clear:both}}
@media print {{ body{{padding:0}} .no-print{{display:none}} }}
</style></head><body>
<div class="head">
  <div><div class="brand">Servia</div>
    <div style="font-size:11px;color:#64748B">UAE home services platform</div>
    <div style="font-size:11px;color:#64748B">Operated by Urban Services</div></div>
  <div class="meta"><div><b>INVOICE</b></div>
    <div>Quote: <code>{quote_id}</code></div>
    <div>Date: {(q.get('created_at') or '')[:10]}</div></div>
</div>
<div style="margin-bottom:14px;font-size:12.5px">
  <b>Bill to:</b><br>{q.get('customer_name','')}<br>{q.get('phone','')}<br>{q.get('address','')}
</div>
<table><thead><tr><th>#</th><th>Service</th><th style="text-align:right">Amount</th></tr></thead>
<tbody>{items_html}</tbody></table>
<div class="totals">
  <div class="row"><div>Subtotal</div><div>AED {q.get('subtotal_aed')}</div></div>
  <div class="row"><div>VAT 5%</div><div>AED {q.get('vat_aed')}</div></div>
  <div class="row total"><div>Total</div><div>AED {q.get('total_aed')}</div></div>
</div>
<div style="clear:both"></div>
<div class="stamp">{'PAID' if paid else 'PAYMENT PENDING'}</div>
<div class="no-print" style="margin-top:24px;text-align:center">
  <a class="btn" href="javascript:window.print()">Print / Save as PDF</a>
  <a class="btn" href="/i/{quote_id}.pdf">Download PDF</a>
  <a class="btn" href="/q/{quote_id}">Back to quote</a>
  {'<a class="btn" href="/p/' + quote_id + '">Pay now</a>' if not paid else ''}
</div>
<div class="note">Digitally generated invoice based on customer-signed quote {quote_id}. Real-time service status, photos, comments and invoice updates available 24/7 at servia.ae/q/{quote_id} with phone-gated access.</div>
</body></html>"""


@public_router.get("/i/{quote_id}.pdf")
def invoice_pdf(quote_id: str):
    q = _quote(quote_id)
    if not q: raise HTTPException(404)
    try:
        from fpdf import FPDF
    except Exception:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/i/{quote_id}", status_code=302)
    # v1.24.82 — pre-replace common Unicode chars with latin-1 equivalents
    # so the Helvetica core font can render them. Em/en-dash were causing
    # FPDFUnicodeEncodingException on items like "Sofa & Carpet — AED 49".
    _UNI_MAP = {
        "—": "-", "–": "-", "•": "*", "·": "-", "→": "->", "↗": "^",
        "←": "<-", "✓": "v", "✗": "x", "✅": "[OK]", "❌": "[X]",
        "•": "*", "⤷": ">", "📋": "[Q]", "📅": "", "📍": "",
        "👤": "", "✍️": "", "💳": "", "🔒": "",
        "–":"-","—":"-","‘":"'","’":"'",
        "“":'"',"”":'"',
    }
    def _safe(s):
        s = (s or "")
        for k, v in _UNI_MAP.items():
            s = s.replace(k, v)
        try: return s.encode("latin-1", "replace").decode("latin-1")
        except Exception: return s.encode("ascii", "ignore").decode("ascii")
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_fill_color(13, 148, 136); pdf.rect(0, 0, 210, 28, "F")
    pdf.set_text_color(255, 255, 255); pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(15, 8); pdf.cell(0, 8, "Servia", ln=1)
    pdf.set_font("Helvetica", "", 9); pdf.set_xy(15, 18)
    pdf.cell(0, 4, "UAE home services platform", ln=1)
    pdf.set_xy(150, 8); pdf.set_font("Helvetica", "B", 14)
    pdf.cell(45, 6, "QUOTATION & INVOICE", align="R", ln=1)
    pdf.set_font("Helvetica", "", 9); pdf.set_xy(150, 16)
    pdf.cell(45, 4, f"Ref: {quote_id}", align="R", ln=1)
    pdf.set_xy(150, 21)
    pdf.cell(45, 4, f"Issued: {(q.get('created_at') or '')[:10]}", align="R", ln=1)
    # v1.24.82 — professional invoice layout
    pdf.set_text_color(15, 23, 42); pdf.set_xy(15, 38)
    pdf.set_font("Helvetica", "B", 10); pdf.cell(0, 5, "BILL TO", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(15); pdf.cell(0, 5, _safe(q.get("customer_name") or ""), ln=1)
    pdf.set_x(15); pdf.cell(0, 5, _safe(q.get("phone") or ""), ln=1)
    pdf.set_x(15); pdf.multi_cell(120, 5, _safe(q.get("address") or ""))
    # Service date / time block
    pdf.set_y(pdf.get_y() + 4)
    pdf.set_fill_color(240, 253, 250); pdf.set_text_color(15, 118, 110)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 7, " SERVICE SCHEDULE", fill=True, ln=1)
    pdf.set_text_color(15, 23, 42); pdf.set_font("Helvetica", "", 10)
    pdf.set_x(15); pdf.cell(0, 5,
        f"Date: {q.get('target_date','')}    Time: {q.get('time_slot','')}", ln=1)
    pdf.ln(4)
    # Itemised services table
    pdf.set_fill_color(241, 245, 249); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(10, 7, "#", border=1, fill=True, align="C")
    pdf.cell(120, 7, "Service & Special Instructions", border=1, fill=True)
    pdf.cell(60, 7, "Amount (AED)", border=1, fill=True, align="R", ln=1)
    pdf.set_font("Helvetica", "", 10)
    for i, it in enumerate(q.get("items") or []):
        # Capture vertical for multi-row alignment
        y_start = pdf.get_y()
        pdf.cell(10, 7, str(i + 1), border="LR", align="C")
        # Inline service name
        pdf.cell(120, 7, _safe(it.get("label", ""))[:60], border="LR")
        pdf.cell(60, 7, f"{it.get('price_aed', 0):,.2f}", border="LR", align="R", ln=1)
        # Special instructions row (italic, smaller)
        si = (it.get("special_instructions") or "").strip()
        if si:
            pdf.set_x(20)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(100, 116, 139)
            pdf.multi_cell(170, 4, _safe("⤷ " + si)[:200], border=0)
            pdf.set_text_color(15, 23, 42); pdf.set_font("Helvetica", "", 10)
        # Bottom border for row
        pdf.set_x(15); pdf.cell(190, 0, "", border="T", ln=1)
    # Totals
    pdf.ln(4)
    sub, vat, tot = q.get("subtotal_aed") or 0, q.get("vat_aed") or 0, q.get("total_aed") or 0
    pdf.set_x(115); pdf.cell(45, 6, "Subtotal", align="R")
    pdf.cell(35, 6, f"AED {sub:,.2f}", align="R", ln=1)
    pdf.set_x(115); pdf.cell(45, 6, "VAT 5%", align="R")
    pdf.cell(35, 6, f"AED {vat:,.2f}", align="R", ln=1)
    pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(13, 148, 136)
    pdf.set_x(115); pdf.cell(45, 8, "TOTAL", align="R")
    pdf.cell(35, 8, f"AED {tot:,.2f}", align="R", ln=1)
    # Payment status banner
    pdf.ln(6); pdf.set_font("Helvetica", "B", 11)
    paid = bool(q.get("paid_at"))
    if paid:
        pdf.set_fill_color(209, 250, 229); pdf.set_text_color(6, 95, 70)
        pdf.cell(0, 9, _safe(f"  PAID  -  {(q.get('paid_at') or '')[:19]}"), fill=True, ln=1)
    else:
        pdf.set_fill_color(254, 243, 199); pdf.set_text_color(146, 64, 14)
        pdf.cell(0, 9, "  PAYMENT PENDING - 100% advance required to dispatch crew", fill=True, ln=1)
    # General special instructions
    notes = (q.get("notes") or "").strip()
    if notes:
        pdf.ln(4); pdf.set_text_color(15, 23, 42); pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, "GENERAL INSTRUCTIONS", ln=1)
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(0, 4.5, _safe(notes)[:1500])
    # Customer satisfaction block
    pdf.ln(3); pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, "CUSTOMER SATISFACTION", ln=1)
    pdf.set_font("Helvetica", "", 8); pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 4,
        f"If you are not satisfied with the service delivered, contact us "
        f"within 24 hours of completion via WhatsApp {_wa_block()[0] or 'see /contact'} or "
        f"support@servia.ae and we will arrange a free re-do or escalate "
        f"to our quality team. Photos and live status of your service are "
        f"available 24/7 at https://{get_settings().brand().get('domain','servia.ae')}/q/{quote_id}")
    # ──────────────────────────────────────────────────────────
    # Customer Portal & Modern Features section (v1.24.82)
    # — beats every UAE competitor's static PDF with live links +
    # PWA install + smartwatch + NFC unlock + booking AI assistant.
    # ──────────────────────────────────────────────────────────
    domain = get_settings().brand().get("domain","servia.ae")
    pdf.ln(3); pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, "YOUR CUSTOMER PORTAL", ln=1)
    pdf.set_font("Helvetica", "", 8); pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 4,
        f"Live status + photos + invoices + signature record:  https://{domain}/q/{quote_id}\n"
        f"All your bookings (phone-gated):     https://{domain}/me\n"
        f"Need to talk to a human?            https://{domain}/contact   |   WhatsApp {_wa_block()[0]}\n"
        f"Refund policy:                       https://{domain}/refund")
    pdf.ln(2); pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, _safe("BUILT FOR THE UAE - FEATURES YOU WILL NOT FIND ELSEWHERE"), ln=1)
    pdf.set_font("Helvetica", "", 8); pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 4,
        f"Mobile app (Android + iOS)   - one-tap rebook, push alerts, app-only deals.  https://{domain}/install\n"
        f"Wear OS / smartwatch         - 'Crew arriving' on your wrist, no phone needed.  https://{domain}/wearos\n"
        f"NFC tap (villa & vehicle)    - tap a Servia tag to call the right specialist instantly.  https://{domain}/nfc\n"
        f"24/7 AI Concierge            - 15 languages, books in 60 seconds, lives at every page.\n"
        f"Live tracking                - watch the crew approach your address in real time.\n"
        f"Digital signature            - sign quotes from your phone, no paperwork.\n"
        f"Ambassador rewards           - refer friends, earn discounts on every future booking.")
    # Terms & Conditions
    pdf.ln(3); pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, "TERMS & CONDITIONS", ln=1)
    pdf.set_font("Helvetica", "", 7.5); pdf.set_text_color(71, 85, 105)
    tnc = (
        "1. PAYMENT: 100% advance payment is strictly required to lock the "
        "scheduled slot. We do not offer cash on delivery, partial payment, "
        "or credit terms.\n"
        "2. CANCELLATION: Full refund if Servia cancels. Customer "
        "cancellations within 4 hours of dispatch are non-refundable; "
        "earlier cancellations incur a 25% admin fee.\n"
        "3. LIABILITY: Servia is not liable for any damage to property, "
        "loss of valuables, or personal items during or after the service. "
        "Customer is responsible for securing valuables, jewellery, cash, "
        "documents, and electronics before crew arrival.\n"
        "4. SCOPE: Service is limited to what is itemised above. Additional "
        "work outside the listed scope requires a separate quote.\n"
        "5. ACCESS: Customer must ensure unobstructed access to the "
        "premises at the scheduled time. Failure to grant access is a "
        "no-show and is non-refundable.\n"
        "6. INSURANCE: All staff are background-checked. Major-incident "
        "insurance is provided up to AED 5,000 per booking; this excludes "
        "ordinary wear and consequential losses.\n"
        "7. DISPUTES: Any dispute must be raised within 48 hours of service "
        "completion. Decisions of the Servia quality team are final.\n"
        "8. COMMUNICATION: SMS and WhatsApp notifications are sent to the "
        "phone number on file. Customer is responsible for keeping it "
        "current.\n"
        "By signing the digital quote you accept these terms."
    )
    pdf.multi_cell(0, 3.6, _safe(tnc))
    # Footer
    pdf.ln(2); pdf.set_font("Helvetica", "I", 7); pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 4, _safe(f"Servia - {get_settings().brand().get('domain','servia.ae')} - WhatsApp {_wa_block()[0]} - Issued {_now()[:19]}"), align="C", ln=1)
    out = pdf.output(dest="S")
    if isinstance(out, str): out = out.encode("latin-1")
    from fastapi.responses import Response
    return Response(content=bytes(out), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="invoice-{quote_id}.pdf"'})
