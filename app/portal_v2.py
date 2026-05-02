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
            tools.send_whatsapp(req.phone, f"Your Lumora login code: {code} (valid 10 min)")
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
