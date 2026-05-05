"""Customer + vendor portal endpoints, plus auth API."""
from __future__ import annotations

import datetime as _dt
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import auth_users as a
from . import db, kb, quotes, tools
from .config import get_settings


router = APIRouter(prefix="/api", tags=["auth-portal"])


# ============================================================
# AUTH endpoints
# ============================================================

@router.post("/auth/customer/start")
def customer_start(req: a.OtpStartReq):
    """Issue an OTP for the given phone. In production OTP is sent via WhatsApp.

    Demo mode: OTP returned in response (only when DEMO_MODE=on or no WA bridge).
    """
    settings = get_settings()
    code = a.issue_otp(req.phone)

    # Try push via WhatsApp bridge
    delivered_via = None
    if settings.WA_BRIDGE_URL:
        try:
            tools.send_whatsapp(req.phone, f"Your Servia login code: {code} (valid 10 min)")
            delivered_via = "whatsapp"
        except Exception:  # noqa: BLE001
            pass

    payload = {"ok": True, "delivered_via": delivered_via or "none"}
    # Expose OTP in response only when no real channel is wired up — for demo/testing.
    if not delivered_via:
        payload["dev_otp"] = code  # ⚠️ remove or gate in production
    return payload


@router.post("/auth/customer/verify")
def customer_verify(req: a.OtpVerifyReq):
    if not a.verify_otp(req.phone, req.code):
        raise HTTPException(status_code=401, detail="invalid or expired OTP")

    # Find or create customer
    with db.connect() as c:
        row = c.execute("SELECT id FROM customers WHERE phone=?", (req.phone,)).fetchone()
        if row:
            cid = row["id"]
            c.execute("UPDATE customers SET last_seen_at=? WHERE id=?",
                      (_dt.datetime.utcnow().isoformat() + "Z", cid))
        else:
            cur = c.execute(
                "INSERT INTO customers(phone, created_at, last_seen_at) VALUES(?,?,?)",
                (req.phone, _dt.datetime.utcnow().isoformat() + "Z",
                 _dt.datetime.utcnow().isoformat() + "Z"),
            )
            cid = cur.lastrowid

    token = a.create_session("customer", cid)
    return {"ok": True, "token": token, "customer_id": cid}


# --- Customer's ambassador tier (for the dashboard overview) ---
@router.get("/me/tier")
def me_tier(user: a.AuthedUser = Depends(a.current_customer)):
    """Returns the logged-in customer's Ambassador tier + discount + counts."""
    try:
        from . import tools as _t
        with db.connect() as c:
            r = c.execute("SELECT phone FROM customers WHERE id=?", (user.user_id,)).fetchone()
        phone = r["phone"] if r else ""
        return _t.get_my_tier(phone)
    except Exception as e:
        return {"ok": False, "error": str(e), "tier": "🥉 Bronze",
                "discount_pct": 5, "referrals": 0, "reviews": 0,
                "next_step": "Refer 3 friends to reach Silver (10%)"}


# --- Magic-link login (for the auto-account flow on cart checkout) ---
class MagicLinkReq(BaseModel):
    email: str

@router.post("/auth/magic-link")
def request_magic_link(req: MagicLinkReq):
    """Send the customer a 1-time login token by email. Same OTP plumbing
    re-used: token = sha256(email + secret + 5-min bucket). Customer clicks
    https://servia.ae/me.html?login=<email>&t=<token> → we verify + auto-login.
    For now we record an admin alert (admin can paste token into the email
    or we wire SMTP/Postmark in a later pass)."""
    import datetime as _dt, hashlib, secrets
    email = (req.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "valid email required")
    with db.connect() as c:
        r = c.execute("SELECT id, name FROM customers WHERE email=?", (email,)).fetchone()
        if not r:
            return {"ok": True, "sent": False,
                    "msg": "If an account exists for that email, we've sent a login link."}
        cid = r["id"]
    # 30-min token
    salt = os.getenv("MAGIC_LINK_SALT", "servia-magic-default")
    bucket = int(_dt.datetime.utcnow().timestamp() // 1800)
    token = hashlib.sha256(f"{email}|{salt}|{bucket}".encode()).hexdigest()[:24]
    link = f"/me.html?login={email}&t={token}"
    full_link = f"https://servia.ae{link}"

    # 1) Try SMTP delivery first if configured
    delivered_via_smtp = False
    try:
        from . import mail
        if mail.configured():
            customer_name = (r["name"] or "").strip() or "there"
            text = (
                f"Hi {customer_name},\n\n"
                f"Click the link below to log in to your Servia account:\n\n"
                f"{full_link}\n\n"
                f"This link expires in 30 minutes. If you didn't request it, "
                f"you can safely ignore this email.\n\n"
                f"— Servia"
            )
            html = (
                f"<div style='font-family:-apple-system,Arial,sans-serif;max-width:480px;"
                f"margin:0 auto;padding:24px'>"
                f"<h2 style='color:#0F766E;margin:0 0 12px'>Sign in to Servia</h2>"
                f"<p>Hi {customer_name}, tap the button below to log in:</p>"
                f"<p style='margin:24px 0'><a href='{full_link}' "
                f"style='background:#0D9488;color:#fff;padding:12px 22px;"
                f"border-radius:999px;text-decoration:none;font-weight:700'>"
                f"Log in to Servia</a></p>"
                f"<p style='color:#64748B;font-size:13px'>"
                f"Or copy this link: <code>{full_link}</code><br>"
                f"This link expires in 30 minutes.</p></div>"
            )
            delivered_via_smtp = mail.send(email, "Your Servia login link", text, html)
    except Exception:
        delivered_via_smtp = False

    # 2) Always record an admin alert so a human can intervene if SMTP isn't set up
    try:
        from . import admin_alerts
        admin_alerts.notify_admin(
            f"📧 Magic-link login {'sent' if delivered_via_smtp else 'requested'}\n\n"
            f"Customer: {email} (id {cid})\n"
            f"Link: {full_link}\n"
            f"SMTP delivered: {'YES' if delivered_via_smtp else 'NO — wire SMTP env vars'}",
            kind="magic_link", urgency="normal")
    except Exception: pass

    return {"ok": True, "sent": True, "delivered": delivered_via_smtp,
            "debug_link": link if os.getenv("DEBUG_MAGIC", "") == "1" else None,
            "msg": "Login link sent — check your email."}


class MagicLinkVerifyReq(BaseModel):
    email: str
    token: str

@router.post("/auth/magic-link/verify")
def verify_magic_link(req: MagicLinkVerifyReq):
    import datetime as _dt, hashlib, os as _os
    email = (req.email or "").strip().lower()
    salt = _os.getenv("MAGIC_LINK_SALT", "servia-magic-default")
    now_b = int(_dt.datetime.utcnow().timestamp() // 1800)
    # Accept current + previous bucket so the token has a 30-60min window
    for b in (now_b, now_b - 1):
        expected = hashlib.sha256(f"{email}|{salt}|{b}".encode()).hexdigest()[:24]
        if expected == (req.token or ""):
            with db.connect() as c:
                r = c.execute("SELECT id FROM customers WHERE email=?", (email,)).fetchone()
                if not r: raise HTTPException(404, "no account")
                cid = r["id"]
            tok = a.create_session("customer", cid)
            return {"ok": True, "token": tok, "customer_id": cid}
    raise HTTPException(401, "invalid or expired magic link")


# --- Set/change password for customer (post-checkout claim) ---
class SetPasswordReq(BaseModel):
    phone: str
    password: str

@router.post("/auth/customer/set-password")
def set_customer_password(req: SetPasswordReq):
    """Allows a customer who just placed an order to set a password so they
    can log in directly next time (OTP no longer required)."""
    if not req.password or len(req.password) < 6:
        raise HTTPException(400, "password must be 6+ chars")
    pw = a.hash_password(req.password)
    with db.connect() as c:
        r = c.execute("SELECT id FROM customers WHERE phone=?", (req.phone or "")).fetchone()
        if not r: raise HTTPException(404, "no account for that phone")
        try: c.execute("ALTER TABLE customers ADD COLUMN password_hash TEXT")
        except Exception: pass
        c.execute("UPDATE customers SET password_hash=? WHERE id=?", (pw, r["id"]))
    return {"ok": True}


@router.post("/auth/vendor/register")
def vendor_register(req: a.VendorRegisterReq):
    """Self-registration. New vendors are approved by default unless ADMIN_VENDOR_APPROVAL=on."""
    needs_approval = os.getenv("ADMIN_VENDOR_APPROVAL", "off").lower() == "on"
    pwhash = a.hash_password(req.password)
    with db.connect() as c:
        try:
            cur = c.execute(
                "INSERT INTO vendors(email, password_hash, name, phone, company, "
                "is_approved, created_at) VALUES(?,?,?,?,?,?,?)",
                (req.email.lower(), pwhash, req.name, req.phone, req.company,
                 0 if needs_approval else 1,
                 _dt.datetime.utcnow().isoformat() + "Z"),
            )
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"registration failed: {e}")
        vid = cur.lastrowid
        # services
        for sid in req.services:
            c.execute("INSERT OR IGNORE INTO vendor_services(vendor_id, service_id, area) "
                      "VALUES(?,?, '*')", (vid, sid))
    db.log_event("vendor", str(vid), "registered", actor=req.email)
    return {"ok": True, "vendor_id": vid, "approval_required": needs_approval}


@router.post("/auth/vendor/login")
def vendor_login(req: a.VendorLoginReq):
    with db.connect() as c:
        r = c.execute("SELECT * FROM vendors WHERE email=?", (req.email.lower(),)).fetchone()
    if not r:
        raise HTTPException(status_code=401, detail="bad credentials")
    if not a.verify_password(req.password, r["password_hash"]):
        raise HTTPException(status_code=401, detail="bad credentials")
    if not r["is_active"]:
        raise HTTPException(status_code=403, detail="vendor account disabled")
    token = a.create_session("vendor", r["id"])
    return {"ok": True, "token": token, "vendor_id": r["id"],
            "approved": bool(r["is_approved"])}


@router.post("/auth/logout")
def logout(authorization: str = ""):
    if authorization.lower().startswith("bearer "):
        a.revoke_session(authorization[7:].strip())
    return {"ok": True}


@router.get("/me")
def me(user: a.AuthedUser = Depends(a.current_user)):
    rec = dict(user.record)
    rec.pop("password_hash", None)
    return {"user_type": user.user_type, "user": rec}


# ============================================================
# CUSTOMER portal
# ============================================================

@router.get("/me/bookings")
def my_bookings(user: a.AuthedUser = Depends(a.current_customer)):
    phone = user.record["phone"]
    with db.connect() as c:
        rows = c.execute(
            "SELECT * FROM bookings WHERE phone=? ORDER BY created_at DESC LIMIT 50",
            (phone,),
        ).fetchall()
    out = db.rows_to_dicts(rows)
    for b in out:
        b.update(quotes.list_for_booking(b["id"]))
        # Attached vendor (if any)
        with db.connect() as c:
            asn = c.execute(
                "SELECT a.*, v.name AS vendor_name, v.rating AS vendor_rating "
                "FROM assignments a LEFT JOIN vendors v ON v.id=a.vendor_id "
                "WHERE booking_id=? ORDER BY a.id DESC LIMIT 1",
                (b["id"],)).fetchone()
        b["assignment"] = db.row_to_dict(asn)
    return {"bookings": out}


@router.get("/me/booking/{bid}")
def my_booking(bid: str, user: a.AuthedUser = Depends(a.current_customer)):
    rec = tools.lookup_booking(bid)
    if not rec.get("ok"):
        raise HTTPException(404, "booking not found")
    b = rec["booking"]
    if b["phone"] != user.record["phone"]:
        raise HTTPException(403, "not your booking")
    return rec


class RatingBody(BaseModel):
    stars: int
    comment: str | None = None


@router.post("/me/booking/{bid}/rate")
def rate_booking(bid: str, body: RatingBody,
                 user: a.AuthedUser = Depends(a.current_customer)):
    if body.stars < 1 or body.stars > 5:
        raise HTTPException(400, "stars must be 1-5")
    # Find vendor + update rating with naive averaging
    with db.connect() as c:
        b = c.execute("SELECT phone FROM bookings WHERE id=?", (bid,)).fetchone()
        if not b or b["phone"] != user.record["phone"]:
            raise HTTPException(403, "not your booking")
        asn = c.execute("SELECT vendor_id FROM assignments WHERE booking_id=?",
                        (bid,)).fetchone()
        if not asn:
            raise HTTPException(404, "no vendor assigned")
        vid = asn["vendor_id"]
        v = c.execute("SELECT rating, completed_jobs FROM vendors WHERE id=?",
                      (vid,)).fetchone()
        # Weighted average
        n = max(1, v["completed_jobs"])
        new = ((v["rating"] or 5.0) * n + body.stars) / (n + 1)
        c.execute("UPDATE vendors SET rating=? WHERE id=?", (round(new, 2), vid))
    db.log_event("booking", bid, f"rated:{body.stars}", actor=f"customer:{user.user_id}",
                 details={"comment": body.comment})
    return {"ok": True, "vendor_id": vid, "new_avg": round(new, 2)}


# ============================================================
# VENDOR portal
# ============================================================

@router.get("/vendor/me")
def vendor_me(user: a.AuthedUser = Depends(a.current_vendor)):
    rec = dict(user.record); rec.pop("password_hash", None)
    with db.connect() as c:
        services = [dict(r) for r in c.execute(
            "SELECT service_id, area FROM vendor_services WHERE vendor_id=?",
            (user.user_id,)).fetchall()]
    return {"vendor": rec, "services": services}


class VendorServicesBody(BaseModel):
    services: list[str]
    areas: list[str] | None = None  # default: ['*']


@router.post("/vendor/me/services")
def update_services(body: VendorServicesBody,
                    user: a.AuthedUser = Depends(a.current_vendor)):
    valid_ids = {s["id"] for s in kb.services()["services"]}
    bad = [s for s in body.services if s not in valid_ids]
    if bad:
        raise HTTPException(400, f"unknown service ids: {bad}")
    areas = body.areas or ["*"]
    with db.connect() as c:
        c.execute("DELETE FROM vendor_services WHERE vendor_id=?", (user.user_id,))
        for sid in body.services:
            for area in areas:
                c.execute("INSERT INTO vendor_services(vendor_id, service_id, area) "
                          "VALUES(?,?,?)", (user.user_id, sid, area))
    return {"ok": True, "services": body.services, "areas": areas}


@router.get("/vendor/jobs/available")
def available_jobs(user: a.AuthedUser = Depends(a.current_vendor)):
    """Bookings not yet claimed, that match this vendor's services."""
    with db.connect() as c:
        my_services = [r["service_id"] for r in c.execute(
            "SELECT DISTINCT service_id FROM vendor_services WHERE vendor_id=?",
            (user.user_id,)).fetchall()]
        if not my_services:
            return {"jobs": [], "note": "Add at least one service in your profile to see jobs."}
        placeholders = ",".join("?" * len(my_services))
        rows = c.execute(
            f"""
            SELECT b.* FROM bookings b
            LEFT JOIN assignments a ON a.booking_id = b.id
            WHERE a.id IS NULL
              AND b.status IN ('pending','confirmed')
              AND b.service_id IN ({placeholders})
            ORDER BY b.created_at DESC
            LIMIT 50
            """,
            my_services,
        ).fetchall()
    return {"jobs": db.rows_to_dicts(rows)}


@router.get("/vendor/jobs/mine")
def my_jobs(user: a.AuthedUser = Depends(a.current_vendor),
            status: str | None = None):
    sql = (
        "SELECT a.*, b.service_id, b.target_date, b.time_slot, b.address, "
        "b.customer_name, b.phone, b.bedrooms, b.hours, b.units, b.notes, "
        "b.estimated_total, b.currency, b.status AS booking_status "
        "FROM assignments a JOIN bookings b ON b.id = a.booking_id "
        "WHERE a.vendor_id=?"
    )
    params: list = [user.user_id]
    if status:
        sql += " AND a.status=?"; params.append(status)
    sql += " ORDER BY a.id DESC LIMIT 50"
    with db.connect() as c:
        rows = c.execute(sql, params).fetchall()
    return {"jobs": db.rows_to_dicts(rows)}


class ClaimBody(BaseModel):
    booking_id: str


@router.post("/vendor/jobs/claim")
def claim_job(body: ClaimBody, user: a.AuthedUser = Depends(a.current_vendor)):
    with db.connect() as c:
        # Atomic claim: only first vendor wins
        existing = c.execute("SELECT id FROM assignments WHERE booking_id=?",
                             (body.booking_id,)).fetchone()
        if existing:
            raise HTTPException(409, "already claimed by another vendor")
        b = c.execute("SELECT estimated_total, service_id FROM bookings WHERE id=?",
                      (body.booking_id,)).fetchone()
        if not b:
            raise HTTPException(404, "booking not found")
        # Verify vendor offers this service
        ok = c.execute(
            "SELECT 1 FROM vendor_services WHERE vendor_id=? AND service_id=? LIMIT 1",
            (user.user_id, b["service_id"])).fetchone()
        if not ok:
            raise HTTPException(403, "you don't offer this service")
        # 80% payout to vendor by default (configurable)
        pct = float(os.getenv("VENDOR_PAYOUT_PCT", "0.8"))
        payout = round((b["estimated_total"] or 0) * pct, 2)
        cur = c.execute(
            "INSERT INTO assignments(booking_id, vendor_id, status, payout_amount, claimed_at) "
            "VALUES(?,?,?,?,?)",
            (body.booking_id, user.user_id, "accepted", payout,
             _dt.datetime.utcnow().isoformat() + "Z"),
        )
        c.execute("UPDATE bookings SET status='confirmed', updated_at=? WHERE id=?",
                  (_dt.datetime.utcnow().isoformat() + "Z", body.booking_id))
    db.log_event("booking", body.booking_id, "claimed",
                 actor=f"vendor:{user.user_id}", details={"payout": payout})
    return {"ok": True, "assignment_id": cur.lastrowid, "payout_amount": payout}


class JobStatusBody(BaseModel):
    booking_id: str
    status: str  # in_progress | completed | cancelled


@router.post("/vendor/jobs/status")
def update_job_status(body: JobStatusBody,
                      user: a.AuthedUser = Depends(a.current_vendor)):
    valid = {"in_progress", "completed", "cancelled"}
    if body.status not in valid:
        raise HTTPException(400, f"status must be one of {valid}")
    with db.connect() as c:
        a_row = c.execute(
            "SELECT id FROM assignments WHERE booking_id=? AND vendor_id=?",
            (body.booking_id, user.user_id),
        ).fetchone()
        if not a_row:
            raise HTTPException(404, "no assignment for you on this booking")
        ts_field = {"in_progress": "started_at", "completed": "completed_at"}.get(body.status)
        sets = ["status=?"]
        vals: list = [body.status]
        if ts_field:
            sets.append(f"{ts_field}=?")
            vals.append(_dt.datetime.utcnow().isoformat() + "Z")
        c.execute(f"UPDATE assignments SET {', '.join(sets)} WHERE id=?",
                  (*vals, a_row["id"]))
        c.execute("UPDATE bookings SET status=?, updated_at=? WHERE id=?",
                  (body.status, _dt.datetime.utcnow().isoformat() + "Z", body.booking_id))
        if body.status == "completed":
            c.execute(
                "UPDATE vendors SET completed_jobs = completed_jobs + 1 WHERE id=?",
                (user.user_id,))
    db.log_event("booking", body.booking_id, f"vendor:{body.status}",
                 actor=f"vendor:{user.user_id}")
    return {"ok": True, "status": body.status}


@router.get("/vendor/earnings")
def vendor_earnings(user: a.AuthedUser = Depends(a.current_vendor)):
    with db.connect() as c:
        completed_total = c.execute(
            "SELECT COALESCE(SUM(payout_amount),0) AS s FROM assignments "
            "WHERE vendor_id=? AND status='completed'", (user.user_id,)).fetchone()["s"]
        pending_total = c.execute(
            "SELECT COALESCE(SUM(payout_amount),0) AS s FROM assignments "
            "WHERE vendor_id=? AND status IN ('accepted','in_progress')",
            (user.user_id,)).fetchone()["s"]
        by_month = c.execute(
            "SELECT substr(completed_at,1,7) AS m, SUM(payout_amount) AS total "
            "FROM assignments WHERE vendor_id=? AND status='completed' "
            "GROUP BY m ORDER BY m DESC LIMIT 12",
            (user.user_id,)).fetchall()
    return {
        "completed_total_aed": round(completed_total, 2),
        "pending_total_aed": round(pending_total, 2),
        "by_month": [dict(r) for r in by_month],
    }


# ============================================================
# CUSTOMER profile + saved addresses + cancel/reschedule
# ============================================================

class ProfilePatch(BaseModel):
    name: str | None = None
    email: str | None = None
    language: str | None = None


@router.post("/me/profile")
def update_profile(body: ProfilePatch, user: a.AuthedUser = Depends(a.current_customer)):
    fields, vals = [], []
    for k, v in body.model_dump(exclude_none=True).items():
        if v is not None:
            fields.append(f"{k}=?"); vals.append(v)
    if not fields:
        return {"ok": True, "noop": True}
    vals.append(user.user_id)
    with db.connect() as c:
        c.execute(f"UPDATE customers SET {', '.join(fields)} WHERE id=?", vals)
    return {"ok": True}


@router.get("/me/addresses")
def list_addresses(user: a.AuthedUser = Depends(a.current_customer)):
    with db.connect() as c:
        rows = c.execute(
            "SELECT * FROM saved_addresses WHERE customer_id=? ORDER BY is_default DESC, id DESC",
            (user.user_id,)).fetchall()
    return {"addresses": db.rows_to_dicts(rows)}


class SavedAddress(BaseModel):
    # Required: a single human-readable address line (full free-text).
    address: str
    # Optional structured / display fields. None of these are required so old
    # clients sending just `address` keep working.
    label: str | None = None        # "Home" / "Office" / "Mom's place"
    area: str | None = None         # "Dubai Marina", "JVC", "Tecom"…
    building: str | None = None     # tower / villa name
    apartment: str | None = None    # apt / unit no.
    street: str | None = None
    city: str | None = None
    emirate: str | None = None      # "Dubai", "Sharjah", "Abu Dhabi", …
    contact_name: str | None = None
    contact_phone: str | None = None
    notes: str | None = None        # gate code, "ring once", parking spot, etc.
    lat: float | None = None
    lng: float | None = None
    is_default: bool = False


@router.post("/me/addresses")
def add_address(body: SavedAddress, user: a.AuthedUser = Depends(a.current_customer)):
    now = _dt.datetime.utcnow().isoformat() + "Z"
    with db.connect() as c:
        if body.is_default:
            c.execute("UPDATE saved_addresses SET is_default=0 WHERE customer_id=?",
                      (user.user_id,))
        cur = c.execute(
            """INSERT INTO saved_addresses(
                customer_id, label, address, area, building, apartment, street,
                city, emirate, contact_name, contact_phone, notes, lat, lng,
                is_default, created_at, updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (user.user_id, body.label, body.address, body.area, body.building,
             body.apartment, body.street, body.city, body.emirate,
             body.contact_name, body.contact_phone, body.notes,
             body.lat, body.lng, 1 if body.is_default else 0, now, now))
    return {"ok": True, "id": cur.lastrowid}


class AddressPatch(BaseModel):
    # Same shape as SavedAddress but every field optional, so the UI can do
    # partial updates ("just toggle default", "update phone only", …).
    label: str | None = None
    address: str | None = None
    area: str | None = None
    building: str | None = None
    apartment: str | None = None
    street: str | None = None
    city: str | None = None
    emirate: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    notes: str | None = None
    lat: float | None = None
    lng: float | None = None
    is_default: bool | None = None


@router.patch("/me/addresses/{aid}")
def update_address(aid: int, body: AddressPatch,
                   user: a.AuthedUser = Depends(a.current_customer)):
    fields, vals = [], []
    payload = body.model_dump(exclude_none=True)
    if not payload:
        return {"ok": True, "noop": True}
    with db.connect() as c:
        if payload.pop("is_default", False):
            c.execute("UPDATE saved_addresses SET is_default=0 WHERE customer_id=?",
                      (user.user_id,))
            fields.append("is_default=?"); vals.append(1)
        for k, v in payload.items():
            fields.append(f"{k}=?"); vals.append(v)
        fields.append("updated_at=?"); vals.append(_dt.datetime.utcnow().isoformat() + "Z")
        vals.extend([aid, user.user_id])
        c.execute(f"UPDATE saved_addresses SET {', '.join(fields)} "
                  f"WHERE id=? AND customer_id=?", vals)
    return {"ok": True}


@router.delete("/me/addresses/{aid}")
def delete_address(aid: int, user: a.AuthedUser = Depends(a.current_customer)):
    with db.connect() as c:
        c.execute("DELETE FROM saved_addresses WHERE id=? AND customer_id=?",
                  (aid, user.user_id))
    return {"ok": True}


# ============================================================
# CUSTOMER payment methods
#
# We store ONLY display metadata (brand + last4 + expiry) plus an opaque
# Stripe payment-method ID. Full PANs / CVVs never touch our database — this
# avoids dragging us into PCI-DSS scope. Charging happens via Stripe
# (stripe.PaymentIntent.create with payment_method=stripe_pm_id), or via
# alternative method types like cash-on-delivery or WhatsApp pay.
# ============================================================

ALLOWED_METHOD_TYPES = {"card", "cod", "whatsapp_pay", "apple_pay", "google_pay", "bank"}


@router.get("/me/payment-methods")
def list_payment_methods(user: a.AuthedUser = Depends(a.current_customer)):
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, method_type, label, card_brand, card_last4, card_expiry, "
            "holder_name, is_default, created_at "
            "FROM customer_payment_methods WHERE customer_id=? "
            "ORDER BY is_default DESC, id DESC",
            (user.user_id,)).fetchall()
    return {"payment_methods": db.rows_to_dicts(rows)}


class SavedPaymentMethod(BaseModel):
    method_type: str  # one of ALLOWED_METHOD_TYPES
    label: str | None = None
    # Card-only display metadata (never the full PAN). UI sends these from
    # whatever Stripe Elements / collected card form returns.
    card_brand: str | None = None  # "visa" | "mastercard" | "amex" | "discover"
    card_last4: str | None = None  # 4-digit string
    card_expiry: str | None = None # "MM/YY"
    holder_name: str | None = None
    stripe_pm_id: str | None = None
    is_default: bool = False


@router.post("/me/payment-methods")
def add_payment_method(body: SavedPaymentMethod,
                       user: a.AuthedUser = Depends(a.current_customer)):
    if body.method_type not in ALLOWED_METHOD_TYPES:
        raise HTTPException(400, f"method_type must be one of {sorted(ALLOWED_METHOD_TYPES)}")
    if body.method_type == "card":
        if not (body.card_last4 and len(body.card_last4) == 4 and body.card_last4.isdigit()):
            raise HTTPException(400, "card_last4 must be 4 digits")
        if not body.card_brand:
            raise HTTPException(400, "card_brand required for cards")
    now = _dt.datetime.utcnow().isoformat() + "Z"
    with db.connect() as c:
        if body.is_default:
            c.execute("UPDATE customer_payment_methods SET is_default=0 WHERE customer_id=?",
                      (user.user_id,))
        cur = c.execute(
            """INSERT INTO customer_payment_methods(
                customer_id, method_type, label, card_brand, card_last4,
                card_expiry, holder_name, stripe_pm_id, is_default, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (user.user_id, body.method_type, body.label, body.card_brand,
             body.card_last4, body.card_expiry, body.holder_name,
             body.stripe_pm_id, 1 if body.is_default else 0, now))
    return {"ok": True, "id": cur.lastrowid}


@router.post("/me/payment-methods/{pid}/default")
def set_default_payment_method(pid: int,
                               user: a.AuthedUser = Depends(a.current_customer)):
    with db.connect() as c:
        # Verify ownership before flipping defaults
        row = c.execute(
            "SELECT id FROM customer_payment_methods WHERE id=? AND customer_id=?",
            (pid, user.user_id)).fetchone()
        if not row:
            raise HTTPException(404, "payment method not found")
        c.execute("UPDATE customer_payment_methods SET is_default=0 WHERE customer_id=?",
                  (user.user_id,))
        c.execute("UPDATE customer_payment_methods SET is_default=1 WHERE id=?", (pid,))
    return {"ok": True}


@router.delete("/me/payment-methods/{pid}")
def delete_payment_method(pid: int,
                          user: a.AuthedUser = Depends(a.current_customer)):
    with db.connect() as c:
        c.execute("DELETE FROM customer_payment_methods WHERE id=? AND customer_id=?",
                  (pid, user.user_id))
    return {"ok": True}


class CancelBody(BaseModel):
    reason: str | None = None


@router.post("/me/booking/{bid}/cancel")
def cancel_booking(bid: str, body: CancelBody,
                   user: a.AuthedUser = Depends(a.current_customer)):
    with db.connect() as c:
        b = c.execute("SELECT phone, status FROM bookings WHERE id=?", (bid,)).fetchone()
        if not b or b["phone"] != user.record["phone"]:
            raise HTTPException(403, "not your booking")
        if b["status"] in ("completed", "cancelled"):
            raise HTTPException(400, f"cannot cancel a {b['status']} booking")
        c.execute(
            "UPDATE bookings SET status='cancelled', cancelled_at=?, "
            "cancellation_reason=?, updated_at=? WHERE id=?",
            (_dt.datetime.utcnow().isoformat() + "Z", body.reason,
             _dt.datetime.utcnow().isoformat() + "Z", bid))
    db.log_event("booking", bid, "customer_cancelled",
                 actor=f"customer:{user.user_id}", details={"reason": body.reason})
    return {"ok": True}


class RescheduleBody(BaseModel):
    target_date: str
    time_slot: str


@router.post("/me/booking/{bid}/reschedule")
def reschedule_booking(bid: str, body: RescheduleBody,
                       user: a.AuthedUser = Depends(a.current_customer)):
    with db.connect() as c:
        b = c.execute("SELECT phone, status FROM bookings WHERE id=?", (bid,)).fetchone()
        if not b or b["phone"] != user.record["phone"]:
            raise HTTPException(403, "not your booking")
        if b["status"] in ("completed", "cancelled"):
            raise HTTPException(400, "cannot reschedule")
        c.execute(
            "UPDATE bookings SET target_date=?, time_slot=?, status='rescheduled', updated_at=? WHERE id=?",
            (body.target_date, body.time_slot,
             _dt.datetime.utcnow().isoformat() + "Z", bid))
    db.log_event("booking", bid, "customer_rescheduled",
                 actor=f"customer:{user.user_id}",
                 details={"to": f"{body.target_date} {body.time_slot}"})
    return {"ok": True, "new_date": body.target_date, "new_time": body.time_slot}


# ============================================================
# REVIEWS (per-service public, written by customers)
# ============================================================

class ReviewBody(BaseModel):
    booking_id: str
    stars: int
    comment: str | None = None


@router.post("/me/review")
def submit_review(body: ReviewBody, user: a.AuthedUser = Depends(a.current_customer)):
    if body.stars < 1 or body.stars > 5:
        raise HTTPException(400, "stars 1-5")
    with db.connect() as c:
        b = c.execute("SELECT phone, service_id FROM bookings WHERE id=?",
                      (body.booking_id,)).fetchone()
        if not b or b["phone"] != user.record["phone"]:
            raise HTTPException(403, "not your booking")
        asn = c.execute("SELECT vendor_id FROM assignments WHERE booking_id=?",
                        (body.booking_id,)).fetchone()
        c.execute(
            "INSERT INTO reviews(booking_id, customer_id, vendor_id, service_id, "
            "stars, comment, created_at) VALUES(?,?,?,?,?,?,?)",
            (body.booking_id, user.user_id, asn["vendor_id"] if asn else None,
             b["service_id"], body.stars, body.comment,
             _dt.datetime.utcnow().isoformat() + "Z"))
        # Update vendor running average
        if asn:
            v = c.execute("SELECT rating, completed_jobs FROM vendors WHERE id=?",
                          (asn["vendor_id"],)).fetchone()
            n = max(1, v["completed_jobs"])
            new = ((v["rating"] or 5.0) * n + body.stars) / (n + 1)
            c.execute("UPDATE vendors SET rating=? WHERE id=?",
                      (round(new, 2), asn["vendor_id"]))
    return {"ok": True}


# Public — list recent reviews for a service (no auth)
public_router = APIRouter(prefix="/api", tags=["reviews"])


@public_router.get("/reviews/{service_id}")
def list_reviews(service_id: str, limit: int = 20):
    with db.connect() as c:
        rows = c.execute(
            "SELECT r.stars, r.comment, r.created_at, c.name AS customer_name "
            "FROM reviews r LEFT JOIN customers c ON c.id = r.customer_id "
            "WHERE r.service_id=? AND r.comment IS NOT NULL "
            "ORDER BY r.id DESC LIMIT ?",
            (service_id, limit)).fetchall()
        # Aggregate stats
        agg = c.execute(
            "SELECT COUNT(*) AS n, AVG(stars) AS avg FROM reviews WHERE service_id=?",
            (service_id,)).fetchone()
    return {
        "reviews": [dict(r) for r in rows],
        "count": agg["n"] or 0,
        "avg": round(agg["avg"] or 0, 2) if agg["avg"] else None
    }


# ---------- public review submission (used by /delivered.html) ----------
class PublicReviewBody(BaseModel):
    booking_id: str
    rating: int
    text: str | None = None
    tags: list[str] = []


@public_router.post("/reviews")
def submit_public_review(body: PublicReviewBody):
    """Public review endpoint — no auth needed; verifies the booking exists.
    Used by /delivered.html immediately after the crew finishes a job."""
    if body.rating < 1 or body.rating > 5:
        raise HTTPException(400, "rating must be 1-5")
    with db.connect() as c:
        b = c.execute("SELECT id, phone, service_id FROM bookings WHERE id=?",
                      (body.booking_id,)).fetchone()
        if not b:
            raise HTTPException(404, "booking not found")
        cust = c.execute("SELECT id FROM customers WHERE phone=?",
                         (b["phone"],)).fetchone()
        asn = c.execute("SELECT vendor_id FROM assignments WHERE booking_id=?",
                        (body.booking_id,)).fetchone()
        comment = body.text or ""
        if body.tags:
            comment = " · ".join(body.tags) + ("\n" + comment if comment else "")
        c.execute(
            "INSERT INTO reviews(booking_id, customer_id, vendor_id, service_id, "
            "stars, comment, created_at) VALUES(?,?,?,?,?,?,?)",
            (body.booking_id, cust["id"] if cust else None,
             asn["vendor_id"] if asn else None,
             b["service_id"], body.rating, comment,
             _dt.datetime.utcnow().isoformat() + "Z"))
        # Update vendor rolling average
        if asn:
            v = c.execute("SELECT rating, completed_jobs FROM vendors WHERE id=?",
                          (asn["vendor_id"],)).fetchone()
            n = (v["completed_jobs"] or 0) + 1
            new_avg = ((v["rating"] or 5) * (n - 1) + body.rating) / n
            c.execute("UPDATE vendors SET rating=?, completed_jobs=? WHERE id=?",
                      (round(new_avg, 2), n, asn["vendor_id"]))
    db.log_event("review", body.booking_id, "submitted",
                 details={"rating": body.rating, "tags": body.tags})
    return {"ok": True}


# ---------- public market-validation signal capture (no auth) ----------
class MarketSignalPublic(BaseModel):
    booking_id: str | None = None
    service_id: str | None = None
    quoted_price: float | None = None
    customer_name: str | None = None
    phone: str | None = None
    emirate: str | None = None
    voice_url: str | None = None
    feedback_text: str | None = None
    intent: str | None = None
    accepts_coupon: bool = False


@public_router.post("/market-signal")
def public_market_signal(body: MarketSignalPublic, request: Request):
    """Public endpoint — captures real demand intent during stealth-launch
    when GATE_BOOKINGS=1 and we ethically deny payment with a 'gateway error'."""
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
                    created_at TEXT
                )""")
        except Exception: pass
        c.execute(
            "INSERT INTO market_signals(booking_id, service_id, quoted_price, "
            "customer_name, phone, emirate, voice_url, feedback_text, intent, "
            "accepts_coupon, user_agent, referrer, created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (body.booking_id, body.service_id, body.quoted_price,
             body.customer_name, body.phone, body.emirate,
             body.voice_url, body.feedback_text, body.intent,
             1 if body.accepts_coupon else 0,
             request.headers.get("user-agent",""),
             request.headers.get("referer",""),
             _dt.datetime.utcnow().isoformat() + "Z"))
    return {"ok": True}


# ---------- referral / rewards system ----------
@public_router.get("/referral/{code}")
def referral_landing(code: str):
    """Public referral lookup — track click + return basic info for the landing page."""
    with db.connect() as c:
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS referrals(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_phone TEXT, referrer_name TEXT,
                code TEXT UNIQUE, click_count INTEGER DEFAULT 0,
                signup_count INTEGER DEFAULT 0, completed_count INTEGER DEFAULT 0,
                total_earned_aed REAL DEFAULT 0, created_at TEXT)""")
        except Exception: pass
        r = c.execute("SELECT * FROM referrals WHERE code=?", (code,)).fetchone()
        if r:
            c.execute("UPDATE referrals SET click_count=click_count+1 WHERE code=?", (code,))
            return {"valid": True, "referrer_name": r["referrer_name"]}
    return {"valid": False}


class ReferralCreate(BaseModel):
    referrer_phone: str
    referrer_name: str | None = None


@router.post("/me/referral", dependencies=[Depends(a.current_customer)])
def create_referral_code(body: ReferralCreate):
    """Generate a unique referral code for this customer."""
    import secrets
    code = secrets.token_urlsafe(5).replace("_","").replace("-","")[:7].upper()
    now = _dt.datetime.utcnow().isoformat() + "Z"
    with db.connect() as c:
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS referrals(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_phone TEXT, referrer_name TEXT,
                code TEXT UNIQUE, click_count INTEGER DEFAULT 0,
                signup_count INTEGER DEFAULT 0, completed_count INTEGER DEFAULT 0,
                total_earned_aed REAL DEFAULT 0, created_at TEXT)""")
        except Exception: pass
        c.execute("INSERT OR IGNORE INTO referrals(referrer_phone, referrer_name, code, created_at) "
                  "VALUES(?,?,?,?)", (body.referrer_phone, body.referrer_name, code, now))
    return {"code": code, "share_url": f"https://servia.ae/r/{code}"}


# ---------- 5-star Google review reward ----------
class ReviewProofBody(BaseModel):
    booking_id: str
    google_review_url: str | None = None       # link to their Google review
    social_post_url: str | None = None         # link to Instagram/TikTok/Twitter post
    platform: str | None = None                # 'google' | 'instagram' | 'tiktok' | 'facebook'
    screenshot_data_url: str | None = None     # optional screenshot upload (base64)


@public_router.post("/review-reward")
def claim_review_reward(body: ReviewProofBody, request: Request):
    """Customer submits proof of 5-star review or social-share post; admin
    approves to release cashback / discount coupon."""
    with db.connect() as c:
        try:
            c.execute("""
              CREATE TABLE IF NOT EXISTS review_rewards(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id TEXT, platform TEXT,
                google_review_url TEXT, social_post_url TEXT,
                screenshot_data_url TEXT, status TEXT DEFAULT 'pending',
                reward_aed REAL DEFAULT 25, payout_method TEXT,
                approved_by TEXT, created_at TEXT)""")
        except Exception: pass
        c.execute("INSERT INTO review_rewards(booking_id, platform, google_review_url, "
                  "social_post_url, screenshot_data_url, created_at) VALUES(?,?,?,?,?,?)",
                  (body.booking_id, body.platform, body.google_review_url,
                   body.social_post_url, body.screenshot_data_url,
                   _dt.datetime.utcnow().isoformat() + "Z"))
    return {"ok": True, "message": "Thanks! We'll verify and send your reward via WhatsApp within 24h."}


# ---------- public latest-blog endpoint (homepage cards) ----------
# Self-healing: if the DB has fewer than 4 articles, this endpoint seeds 10
# template articles inline before responding. So even if the startup hook
# was skipped or the DB was wiped, the homepage cards always populate.
@public_router.get("/blog/latest")
def latest_blog(limit: int = 4):
    import datetime as _dt, random as _r
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

    # Self-heal: seed templates if empty
    if n < 4:
        try:
            from .main import _seed_template_article  # uses the same template body
        except Exception:
            _seed_template_article = None
        SEED = [
            ("dubai", "ac_service", "AC pre-summer prep in Dubai Marina — what to demand from a technician", "pre-summer prep"),
            ("abu-dhabi", "deep_cleaning", "Deep cleaning a Khalifa City villa after sandstorm season — a checklist", "post-summer reset"),
            ("sharjah", "pest_control", "Cockroach control in Al Nahda Sharjah — why DIY sprays don't last past June", "summer-peak survival"),
            ("dubai", "handyman", "Same-day handyman in Downtown Dubai — what AED 150 actually buys you", "year-round"),
            ("ajman", "move_in_out_cleaning", "Moving out of an Ajman apartment? The deposit-saving deep clean nobody tells you about", "year-round"),
            ("ras-al-khaimah", "ac_service", "RAK AC service tips — coastal humidity is killing your compressor faster than you think", "pre-summer prep"),
            ("dubai", "kitchen_deep_clean", "Kitchen deep clean in JLT — the ramadan grease problem and how pros solve it", "post-summer reset"),
            ("abu-dhabi", "pest_control", "Bed bugs on Reem Island — why 80% of treatments fail and what works in 2026", "year-round"),
            ("sharjah", "carpet_cleaning", "Carpet cleaning in Al Khan Sharjah — sand, oil, kid spills and what AED 80 covers", "cool-season deep care"),
            ("fujairah", "deep_cleaning", "Holiday-home deep cleaning in Fujairah — the airbnb host's 4-hour reset routine", "year-round"),
        ]
        now = _dt.datetime.utcnow()
        with db.connect() as c:
            for i, (em, sv, topic, slant) in enumerate(SEED):
                slug = (em + "-" + "".join(c2.lower() if c2.isalnum() else "-" for c2 in topic).strip("-"))[:90]
                published = (now - _dt.timedelta(days=i+1)).replace(
                    hour=_r.choice([8,10,14,17,19]), minute=_r.randint(0,59),
                    second=_r.randint(0,59), microsecond=0)
                if _seed_template_article:
                    body = _seed_template_article(em, sv, slant, topic)
                else:
                    body = (
                        f"Servia covers {em.replace('-',' ').title()} fully — including {sv.replace('_',' ')} bookings.\n\n"
                        f"## Why this matters in {em.replace('-',' ').title()}\n\n"
                        f"Local conditions (heat, humidity, dust) impact services more than most providers admit. "
                        f"Our crews adapt their checklist to the {slant} window so the work actually lasts.\n\n"
                        f"## What you get with Servia\n\n"
                        f"- Background-checked, insured pros\n"
                        f"- Transparent fixed pricing — no surprise charges\n"
                        f"- 7-day re-do guarantee + AED 25,000 damage cover\n"
                        f"- Same-day slots if booked before 11am\n\n"
                        f"Book at https://servia.ae/book.html — 60 seconds, no phone calls.")
                try:
                    c.execute(
                        "INSERT OR IGNORE INTO autoblog_posts(slug, emirate, topic, body_md, published_at) "
                        "VALUES(?,?,?,?,?)",
                        (slug, em, topic, body, published.isoformat() + "Z"))
                except Exception: pass

    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT slug, emirate, topic, published_at FROM autoblog_posts "
                "ORDER BY id DESC LIMIT ?", (max(1, min(limit, 50)),)).fetchall()
        except Exception:
            rows = []
    return {"posts": [db.row_to_dict(r) for r in rows]}
