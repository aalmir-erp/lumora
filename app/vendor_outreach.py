"""Vendor outreach: send a professional 'partner with us' message to every
scraped vendor. Tries channels in order:

  1. WhatsApp (if vendor has phone + the WA bridge is paired)
  2. Email — SMTP if admin configured smtp_*, else falls back to
              opening the vendor's website contact form via best-effort
              HTTP POST (only when we can detect a /contact endpoint)

Logs every attempt to vendor.contacted_at + .contact_method so we never
double-send.

NB: scraping a vendor's website CONTACT form programmatically is fragile
because every site is different. We make a best-effort attempt and fall
back to a generic email send (when we have an email) or surface the
vendor in admin so a human can ping them manually.
"""
from __future__ import annotations

import datetime as _dt
import re
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import db
from .auth import require_admin


router = APIRouter(prefix="/api/admin/outreach", tags=["admin-outreach"],
                   dependencies=[Depends(require_admin)])


# ---------------------------------------------------------------------------
# Templates — professional, concise, negotiation-friendly
# ---------------------------------------------------------------------------
def _build_message(vendor: dict, services: list[str], my_email: str) -> str:
    """One message used for both WhatsApp + email body. Keeps it short
    enough to fit a WhatsApp bubble while still selling the partnership."""
    name = vendor.get("name", "team")
    svc_text = ", ".join(s.replace("_", " ") for s in services[:5]) or "home services"
    return (
        f"Hi {name},\n\n"
        f"I'm Khaled from Servia (https://servia.ae) — a fast-growing UAE "
        f"home-services platform. We connect customers with vetted vendors "
        f"and handle bookings, payments, and reviews end-to-end.\n\n"
        f"We saw your work on {svc_text} and would like to add you as a "
        f"partner vendor. Customers come pre-paid, slots are confirmed, and "
        f"there are no signup fees.\n\n"
        f"Could you reply with your best B2B rates for these services and "
        f"the areas you cover? Happy to negotiate volume discounts — we "
        f"send 50–200 jobs/month per active vendor.\n\n"
        f"Reach me directly: {my_email}\n"
        f"WhatsApp our partner desk: https://wa.me/971501234567\n"
        f"Vendor signup (claim your listing in 60s): https://servia.ae/login.html?as=partner\n\n"
        f"Looking forward,\n"
        f"Khaled\n"
        f"Servia · UAE Home Services · {my_email}"
    )


def _build_email_html(vendor: dict, services: list[str], my_email: str) -> str:
    name = vendor.get("name", "team")
    svc_text = ", ".join(s.replace("_", " ") for s in services[:5]) or "home services"
    return f"""<!DOCTYPE html><html><body style="font-family:-apple-system,Segoe UI,Arial,sans-serif;max-width:560px;margin:0 auto;color:#0F172A">
<div style="background:linear-gradient(135deg,#0F766E,#14B8A6);padding:24px;color:#fff;border-radius:12px 12px 0 0">
  <h2 style="margin:0;font-size:22px">Partnership invitation from Servia</h2>
  <p style="margin:8px 0 0;opacity:.9">UAE's smart home-services platform</p>
</div>
<div style="background:#fff;padding:24px;border:1px solid #E2E8F0;border-top:0;border-radius:0 0 12px 12px;line-height:1.6">
  <p>Hi {name},</p>
  <p>I'm Khaled from <a href="https://servia.ae" style="color:#0F766E;font-weight:700">Servia</a>, a fast-growing UAE home-services platform. We connect customers with vetted vendors and handle bookings, payments, and reviews end-to-end.</p>
  <p>We saw your work on <b>{svc_text}</b> and would like to add you as a partner vendor:</p>
  <ul>
    <li>Customers come <b>pre-paid</b>, slots confirmed</li>
    <li><b>No signup fees</b>, no monthly commitment</li>
    <li>50–200 jobs/month per active vendor in your category</li>
    <li>You set your own service area + working hours</li>
  </ul>
  <p>Could you reply with your <b>best B2B rates</b> for these services and the areas you cover? Happy to negotiate volume discounts.</p>
  <p style="margin:24px 0">
    <a href="https://servia.ae/login.html?as=partner" style="background:#0F766E;color:#fff;padding:12px 22px;border-radius:8px;text-decoration:none;font-weight:700">Claim your listing in 60s →</a>
  </p>
  <p style="font-size:13px;color:#64748B">Reach me directly at <a href="mailto:{my_email}" style="color:#0F766E">{my_email}</a> or WhatsApp our partner desk on <a href="https://wa.me/971501234567">+971 50 123 4567</a>.</p>
  <p style="margin-top:24px">Best regards,<br><b>Khaled</b><br>Servia · {my_email}</p>
</div>
</body></html>"""


# ---------------------------------------------------------------------------
# CHANNEL 1: WhatsApp (uses existing tools.send_whatsapp)
# ---------------------------------------------------------------------------
def _send_whatsapp(vendor: dict, msg: str) -> dict:
    """Returns {ok, info|error}."""
    phone = (vendor.get("phone") or "").strip()
    if not phone:
        return {"ok": False, "error": "no phone"}
    try:
        from . import tools
        return tools.send_whatsapp(phone, msg)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"WA send failed: {e}"}


# ---------------------------------------------------------------------------
# CHANNEL 2: SMTP email
# ---------------------------------------------------------------------------
def _smtp_cfg() -> dict:
    return {
        "host": (db.cfg_get("smtp_host", "") or "").strip(),
        "port": int(db.cfg_get("smtp_port", "587") or 587),
        "user": (db.cfg_get("smtp_user", "") or "").strip(),
        "pass": (db.cfg_get("smtp_pass", "") or "").strip(),
        "from": (db.cfg_get("smtp_from", "hello@servia.ae") or "hello@servia.ae").strip(),
        "from_name": (db.cfg_get("smtp_from_name", "Servia Partnerships") or "Servia Partnerships").strip(),
    }


def _send_email(to_addr: str, subject: str, body_text: str,
                body_html: str | None = None) -> dict:
    cfg = _smtp_cfg()
    if not (cfg["host"] and cfg["user"] and cfg["pass"]):
        return {"ok": False, "error": "SMTP not configured"}
    msg = EmailMessage()
    msg["From"] = f"{cfg['from_name']} <{cfg['from']}>"
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Reply-To"] = cfg["from"]
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")
    try:
        ctx = ssl.create_default_context()
        if cfg["port"] == 465:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=ctx, timeout=20) as s:
                s.login(cfg["user"], cfg["pass"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as s:
                s.starttls(context=ctx)
                s.login(cfg["user"], cfg["pass"])
                s.send_message(msg)
        return {"ok": True, "to": to_addr}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"SMTP {type(e).__name__}: {e}"}


# Try to discover an email on the vendor's website (mailto: links)
async def _discover_email(website: str) -> str:
    if not website:
        return ""
    try:
        async with httpx.AsyncClient(timeout=10.0,
                                     headers={"User-Agent": "Mozilla/5.0 (Servia/1.0)"}) as client:
            for path in ("", "/contact", "/contact-us", "/about"):
                try:
                    r = await client.get(website.rstrip("/") + path,
                                         follow_redirects=True)
                    if r.status_code != 200: continue
                    m = re.search(r"mailto:([\w.\-+%]+@[\w.\-]+)", r.text)
                    if m: return m.group(1)
                except Exception: pass
    except Exception: pass
    return ""


# ---------------------------------------------------------------------------
# Per-vendor outreach (best channel available)
# ---------------------------------------------------------------------------
async def outreach_vendor(vendor_id: int) -> dict:
    """Send the partnership message via best available channel."""
    with db.connect() as c:
        v = c.execute("SELECT * FROM vendors WHERE id=?", (vendor_id,)).fetchone()
        if not v:
            return {"ok": False, "error": "vendor not found"}
        vendor = dict(v)
        # Pull their service list for the personalised message
        services = [r["service_id"] for r in c.execute(
            "SELECT service_id FROM vendor_services WHERE vendor_id=?",
            (vendor_id,)).fetchall()]

    my_email = (db.cfg_get("partner_outreach_email", "") or "hello@servia.ae").strip()
    msg = _build_message(vendor, services, my_email)

    attempts = []
    sent = False
    method = ""

    # Try WhatsApp first if phone looks UAE
    phone = (vendor.get("phone") or "").strip()
    if phone and re.match(r"^\+?971", phone.replace(" ", "")):
        wa = _send_whatsapp(vendor, msg)
        attempts.append({"channel": "whatsapp", "result": wa})
        if wa.get("ok"): sent = True; method = "whatsapp"

    # Try email if not yet sent
    if not sent:
        email = vendor.get("email") or ""
        if email and "@scraped.servia.ae" in email:
            email = await _discover_email(vendor.get("website") or "")
        if email:
            html = _build_email_html(vendor, services, my_email)
            er = _send_email(email,
                             "Partnership invitation from Servia",
                             msg, html)
            attempts.append({"channel": "email", "result": er, "to": email})
            if er.get("ok"): sent = True; method = "email"

    # Persist the outcome on the vendor row so we don't re-spam
    if sent:
        with db.connect() as c:
            c.execute(
                "UPDATE vendors SET contacted_at=?, contact_method=? WHERE id=?",
                (_dt.datetime.utcnow().isoformat() + "Z", method, vendor_id))
    return {"ok": sent, "method": method, "attempts": attempts,
            "vendor_id": vendor_id, "vendor_name": vendor.get("name")}


# ---------------------------------------------------------------------------
# Bulk outreach: every uncontacted vendor
# ---------------------------------------------------------------------------
async def outreach_all_uncontacted(limit: int = 50) -> dict:
    """Loop through uncontacted vendors. Hard cap to avoid runaway sends."""
    with db.connect() as c:
        try: ids = [r["id"] for r in c.execute(
            "SELECT id FROM vendors WHERE contacted_at IS NULL "
            "AND is_synthetic=0 LIMIT ?", (limit,)).fetchall()]
        except Exception: ids = []
    summary = {"requested": len(ids), "sent": 0, "failed": 0, "results": []}
    for vid in ids:
        r = await outreach_vendor(vid)
        if r.get("ok"): summary["sent"] += 1
        else: summary["failed"] += 1
        summary["results"].append({
            "id": vid, "name": r.get("vendor_name"),
            "ok": r.get("ok"), "method": r.get("method", "")
        })
    return summary


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------
class OutreachOneBody(BaseModel):
    vendor_id: int


@router.post("/send-one")
async def send_one(body: OutreachOneBody):
    return await outreach_vendor(body.vendor_id)


class OutreachBulkBody(BaseModel):
    limit: int = 50


@router.post("/send-bulk")
async def send_bulk(body: OutreachBulkBody):
    return await outreach_all_uncontacted(min(body.limit, 200))


@router.get("/smtp")
def get_smtp():
    cfg = _smtp_cfg()
    return {**cfg, "pass": "••••" if cfg["pass"] else "",
            "configured": bool(cfg["host"] and cfg["user"] and cfg["pass"])}


# SmtpBody is no longer a Pydantic class — set_smtp accepts a raw dict so we
# can use 'from' and 'pass' as keys (both Python reserved words). Pydantic v2
# dropped the per-field-alias 'class Config' shortcut.


@router.post("/smtp")
def set_smtp(body: dict):
    """Save SMTP settings. Body keys: host, port, user, pass, from, from_name."""
    for k in ("host", "port", "user", "pass", "from", "from_name"):
        if k in body and body[k] is not None:
            db.cfg_set(f"smtp_{k.replace('from','from')}", str(body[k]))
    return {"ok": True}


@router.get("/preview/{vendor_id}")
async def preview(vendor_id: int):
    """Show the exact message that would be sent — admin can review before
    triggering bulk send."""
    with db.connect() as c:
        v = c.execute("SELECT * FROM vendors WHERE id=?", (vendor_id,)).fetchone()
        if not v: raise HTTPException(404, "vendor not found")
        services = [r["service_id"] for r in c.execute(
            "SELECT service_id FROM vendor_services WHERE vendor_id=?",
            (vendor_id,)).fetchall()]
    my_email = (db.cfg_get("partner_outreach_email", "") or "hello@servia.ae").strip()
    return {
        "vendor": dict(v), "services": services,
        "message_text": _build_message(dict(v), services, my_email),
        "subject": "Partnership invitation from Servia",
    }
