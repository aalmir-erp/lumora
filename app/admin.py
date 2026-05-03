"""Admin panel API. All endpoints require Bearer ADMIN_TOKEN."""
from __future__ import annotations

import asyncio
import json
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import auth_users, db, kb, quotes, tools
from .auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ---------- Dashboard ----------
@router.get("/stats")
def stats():
    with db.connect() as c:
        b_total = c.execute("SELECT COUNT(*) AS n FROM bookings").fetchone()["n"]
        b_today = c.execute("SELECT COUNT(*) AS n FROM bookings WHERE date(created_at)=date('now')").fetchone()["n"]
        i_total = c.execute("SELECT COUNT(*) AS n FROM invoices").fetchone()["n"]
        i_paid = c.execute("SELECT COUNT(*) AS n FROM invoices WHERE payment_status='paid'").fetchone()["n"]
        rev = c.execute("SELECT COALESCE(SUM(amount),0) AS s FROM invoices WHERE payment_status='paid'").fetchone()["s"]
        by_status = c.execute("SELECT status, COUNT(*) AS n FROM bookings GROUP BY status").fetchall()
        active_takeovers = c.execute("SELECT COUNT(*) AS n FROM agent_takeovers WHERE ended_at IS NULL").fetchone()["n"]
    return {
        "bookings_total": b_total, "bookings_today": b_today,
        "invoices_total": i_total, "invoices_paid": i_paid,
        "revenue_aed": rev, "active_handoffs": active_takeovers,
        "by_status": [dict(r) for r in by_status],
    }


# ---------- Bookings ----------
@router.get("/bookings")
def list_bookings(status: str | None = None, q: str | None = None, limit: int = 100):
    # Join customers on phone so admin can impersonate by customer_id even when
    # the booking row itself doesn't carry a foreign key.
    sql = ("SELECT b.*, c.id AS customer_id FROM bookings b "
           "LEFT JOIN customers c ON c.phone = b.phone")
    params: list = []
    where = []
    if status:
        where.append("b.status=?"); params.append(status)
    if q:
        where.append("(b.customer_name LIKE ? OR b.phone LIKE ? OR b.address LIKE ? OR b.id LIKE ?)")
        params.extend([f"%{q}%"] * 4)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY b.created_at DESC LIMIT ?"
    params.append(limit)
    with db.connect() as c:
        rows = c.execute(sql, params).fetchall()
    return {"bookings": db.rows_to_dicts(rows)}


class StatusUpdate(BaseModel):
    status: str


@router.post("/bookings/{bid}/status")
def update_status(bid: str, body: StatusUpdate):
    return tools.update_booking_status(bid, body.status, actor="admin")


@router.post("/bookings/{bid}/invoice")
def make_invoice(bid: str):
    return tools.create_invoice_for_booking(bid)


# ---------- Services + pricing (config-overridable) ----------
class PricingPatch(BaseModel):
    rules: dict | None = None
    surcharges: dict | None = None
    discounts: dict | None = None


@router.get("/pricing")
def get_pricing():
    return kb.pricing()


@router.post("/pricing")
def patch_pricing(body: PricingPatch):
    overrides = db.cfg_get("pricing_overrides", {}) or {}
    payload = body.model_dump(exclude_none=True)
    for k, v in payload.items():
        overrides[k] = {**overrides.get(k, {}), **v}
    db.cfg_set("pricing_overrides", overrides)
    kb._pricing_file.cache_clear()  # noqa: SLF001  pylint: disable=protected-access
    return {"ok": True, "pricing": kb.pricing()}


@router.get("/services")
def get_services():
    return kb.services()


class ServicePatch(BaseModel):
    service_id: str
    patch: dict


@router.post("/services")
def patch_service(body: ServicePatch):
    overrides = db.cfg_get("services_overrides", {}) or {}
    overrides[body.service_id] = {**overrides.get(body.service_id, {}), **body.patch}
    db.cfg_set("services_overrides", overrides)
    return {"ok": True, "services": kb.services()}


# ---------- Conversations + live-agent takeover ----------
@router.get("/conversations")
def list_conversations(session_id: str | None = None, limit: int = 200):
    sql = "SELECT * FROM conversations"
    params: list = []
    if session_id:
        sql += " WHERE session_id=?"; params.append(session_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with db.connect() as c:
        rows = c.execute(sql, params).fetchall()
    return {"messages": db.rows_to_dicts(list(reversed(rows)))}


@router.get("/sessions")
def list_sessions(limit: int = 50):
    with db.connect() as c:
        rows = c.execute(
            "SELECT session_id, COUNT(*) AS msgs, MAX(created_at) AS last_msg, "
            "MAX(channel) AS channel, MAX(phone) AS phone "
            "FROM conversations GROUP BY session_id ORDER BY last_msg DESC LIMIT ?",
            (limit,)).fetchall()
        takeovers = {r["session_id"]: dict(r) for r in c.execute(
            "SELECT session_id, agent_id, started_at, ended_at FROM agent_takeovers"
        ).fetchall()}
    sessions = [dict(r) | {"takeover": takeovers.get(r["session_id"])} for r in rows]
    return {"sessions": sessions}


class TakeoverBody(BaseModel):
    session_id: str
    agent_id: str = "admin"


@router.post("/takeover")
def take_over(body: TakeoverBody):
    import datetime as _dt
    with db.connect() as c:
        c.execute(
            "INSERT INTO agent_takeovers(session_id, agent_id, started_at) VALUES(?,?,?) "
            "ON CONFLICT(session_id) DO UPDATE SET agent_id=excluded.agent_id, "
            "started_at=excluded.started_at, ended_at=NULL",
            (body.session_id, body.agent_id, _dt.datetime.utcnow().isoformat() + "Z"),
        )
    db.log_event("conversation", body.session_id, "takeover_started", actor=body.agent_id)
    return {"ok": True}


class ReleaseBody(BaseModel):
    session_id: str


@router.post("/release")
def release(body: ReleaseBody):
    import datetime as _dt
    with db.connect() as c:
        c.execute(
            "UPDATE agent_takeovers SET ended_at=? WHERE session_id=? AND ended_at IS NULL",
            (_dt.datetime.utcnow().isoformat() + "Z", body.session_id),
        )
    db.log_event("conversation", body.session_id, "takeover_ended", actor="admin")
    return {"ok": True}


class AgentReply(BaseModel):
    session_id: str
    text: str
    agent_id: str = "admin"


@router.post("/reply")
def agent_reply(body: AgentReply):
    """Inject an agent message into the conversation. Frontend polls /messages."""
    import datetime as _dt
    with db.connect() as c:
        c.execute(
            "INSERT INTO conversations(session_id, role, content, agent_handled, created_at) "
            "VALUES(?,?,?,1,?)",
            (body.session_id, "assistant", body.text,
             _dt.datetime.utcnow().isoformat() + "Z"),
        )
    db.log_event("conversation", body.session_id, "agent_reply", actor=body.agent_id)
    return {"ok": True}


# ---------- SSE event stream for the admin panel ----------
@router.get("/stream")
async def admin_stream(request: Request):
    """Server-sent events. Pushes new conversation lines + booking changes."""
    last_id = 0
    last_event = 0

    async def gen():
        nonlocal last_id, last_event
        with db.connect() as c:
            r = c.execute("SELECT MAX(id) AS m FROM conversations").fetchone()
            last_id = r["m"] or 0
            r = c.execute("SELECT MAX(id) AS m FROM events").fetchone()
            last_event = r["m"] or 0
        while True:
            if await request.is_disconnected():
                break
            with db.connect() as c:
                msgs = c.execute(
                    "SELECT * FROM conversations WHERE id>? ORDER BY id ASC LIMIT 50",
                    (last_id,)).fetchall()
                evts = c.execute(
                    "SELECT * FROM events WHERE id>? ORDER BY id ASC LIMIT 50",
                    (last_event,)).fetchall()
            for m in msgs:
                last_id = max(last_id, m["id"])
                yield f"event: message\ndata: {json.dumps(dict(m), ensure_ascii=False)}\n\n"
            for e in evts:
                last_event = max(last_event, e["id"])
                yield f"event: log\ndata: {json.dumps(dict(e), ensure_ascii=False)}\n\n"
            yield f": ping {int(time.time())}\n\n"
            await asyncio.sleep(2.0)

    return StreamingResponse(gen(), media_type="text/event-stream")


# ---------- Vendors ----------
@router.get("/vendors")
def list_vendors():
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, email, name, phone, company, rating, completed_jobs, "
            "is_active, is_approved, created_at FROM vendors ORDER BY created_at DESC"
        ).fetchall()
        for_each = []
        for r in rows:
            d = dict(r)
            svcs = [x["service_id"] for x in c.execute(
                "SELECT service_id FROM vendor_services WHERE vendor_id=?",
                (r["id"],)).fetchall()]
            d["services"] = svcs
            for_each.append(d)
    return {"vendors": for_each}


class CreateVendorBody(BaseModel):
    email: str
    password: str
    name: str
    phone: str | None = None
    company: str | None = None
    services: list[str] = []
    is_approved: bool = True


@router.post("/vendors")
def create_vendor(body: CreateVendorBody):
    pwhash = auth_users.hash_password(body.password)
    import datetime as _dt
    with db.connect() as c:
        try:
            cur = c.execute(
                "INSERT INTO vendors(email, password_hash, name, phone, company, "
                "is_approved, created_at) VALUES(?,?,?,?,?,?,?)",
                (body.email.lower(), pwhash, body.name, body.phone, body.company,
                 1 if body.is_approved else 0,
                 _dt.datetime.utcnow().isoformat() + "Z"),
            )
            vid = cur.lastrowid
            for sid in body.services:
                c.execute("INSERT OR IGNORE INTO vendor_services(vendor_id, service_id, area) "
                          "VALUES(?,?, '*')", (vid, sid))
        except Exception as e:  # noqa: BLE001
            raise HTTPException(400, f"create failed: {e}")
    return {"ok": True, "vendor_id": vid}


class VendorPatchBody(BaseModel):
    is_approved: bool | None = None
    is_active: bool | None = None
    services: list[str] | None = None


@router.post("/vendors/{vid}")
def update_vendor(vid: int, body: VendorPatchBody):
    with db.connect() as c:
        if body.is_approved is not None:
            c.execute("UPDATE vendors SET is_approved=? WHERE id=?",
                      (1 if body.is_approved else 0, vid))
        if body.is_active is not None:
            c.execute("UPDATE vendors SET is_active=? WHERE id=?",
                      (1 if body.is_active else 0, vid))
        if body.services is not None:
            c.execute("DELETE FROM vendor_services WHERE vendor_id=?", (vid,))
            for sid in body.services:
                c.execute("INSERT INTO vendor_services(vendor_id, service_id, area) "
                          "VALUES(?,?, '*')", (vid, sid))
    return {"ok": True}


class AssignBody(BaseModel):
    booking_id: str
    vendor_id: int


@router.post("/assign")
def assign(body: AssignBody):
    """Admin manual assignment (overrides marketplace)."""
    import datetime as _dt
    with db.connect() as c:
        existing = c.execute("SELECT id FROM assignments WHERE booking_id=?",
                             (body.booking_id,)).fetchone()
        if existing:
            raise HTTPException(409, "already assigned; release first")
        b = c.execute("SELECT estimated_total FROM bookings WHERE id=?",
                      (body.booking_id,)).fetchone()
        if not b:
            raise HTTPException(404, "booking not found")
        import os
        pct = float(os.getenv("VENDOR_PAYOUT_PCT", "0.8"))
        payout = round((b["estimated_total"] or 0) * pct, 2)
        cur = c.execute(
            "INSERT INTO assignments(booking_id, vendor_id, status, payout_amount, claimed_at) "
            "VALUES(?,?,?,?,?)",
            (body.booking_id, body.vendor_id, "assigned", payout,
             _dt.datetime.utcnow().isoformat() + "Z"))
    db.log_event("booking", body.booking_id, "admin_assigned",
                 actor="admin", details={"vendor_id": body.vendor_id})
    return {"ok": True, "assignment_id": cur.lastrowid, "payout": payout}


@router.delete("/assignments/{aid}")
def unassign(aid: int):
    with db.connect() as c:
        c.execute("DELETE FROM assignments WHERE id=?", (aid,))
    return {"ok": True}


# ---------- Service detail (services × vendors × pricing) ----------
@router.get("/service/{sid}")
def service_detail(sid: str):
    """Full service detail: definition + pricing rule + vendors offering it (with price)."""
    s = next((x for x in kb.services()["services"] if x["id"] == sid), None)
    if not s:
        raise HTTPException(404, "service not found")
    rule = kb.pricing()["rules"].get(sid, {})
    with db.connect() as c:
        rows = c.execute(
            "SELECT vs.vendor_id, vs.area, vs.price_aed, vs.price_unit, "
            "vs.sla_hours, vs.active, vs.notes, "
            "v.name, v.email, v.phone, v.company, v.rating, v.completed_jobs, "
            "v.is_approved, v.is_active "
            "FROM vendor_services vs JOIN vendors v ON v.id = vs.vendor_id "
            "WHERE vs.service_id=? ORDER BY vs.price_aed IS NULL, vs.price_aed",
            (sid,),
        ).fetchall()
    vendors = [dict(r) for r in rows]
    # Stats for the summary card
    summary = {
        "vendor_count": len(vendors),
        "active_vendor_count": sum(1 for v in vendors if v["active"] and v["is_active"]),
        "min_price_aed": min((v["price_aed"] for v in vendors if v["price_aed"]), default=None),
        "avg_rating": (round(sum(v["rating"] or 5 for v in vendors) / len(vendors), 2)
                       if vendors else None),
    }
    return {"service": s, "rule": rule, "vendors": vendors, "summary": summary}


class ServiceInfoBody(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    icon: str | None = None
    starting_price: float | None = None
    includes: list[str] | None = None
    excludes: list[str] | None = None
    intake: list[str] | None = None


@router.post("/service/{sid}/info")
def update_service_info(sid: str, body: ServiceInfoBody):
    overrides = db.cfg_get("services_overrides", {}) or {}
    patch = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    overrides[sid] = {**overrides.get(sid, {}), **patch}
    db.cfg_set("services_overrides", overrides)
    return {"ok": True, "service": next((x for x in kb.services()["services"]
                                          if x["id"] == sid), None)}


class ServiceRuleBody(BaseModel):
    rule: dict


@router.post("/service/{sid}/rule")
def update_service_rule(sid: str, body: ServiceRuleBody):
    overrides = db.cfg_get("pricing_overrides", {}) or {}
    overrides.setdefault("rules", {})[sid] = body.rule
    db.cfg_set("pricing_overrides", overrides)
    return {"ok": True, "rule": kb.pricing()["rules"].get(sid)}


class VendorPricingBody(BaseModel):
    vendor_id: int
    price_aed: float | None = None
    price_unit: str | None = "fixed"   # fixed | per_bedroom | per_hour | per_unit
    sla_hours: int | None = 24
    active: bool = True
    area: str = "*"
    notes: str | None = None


@router.post("/service/{sid}/vendor")
def assign_or_update_vendor(sid: str, body: VendorPricingBody):
    """Add a vendor to this service or update their pricing/SLA/active flag."""
    valid_units = {"fixed", "per_bedroom", "per_hour", "per_unit"}
    if body.price_unit not in valid_units:
        raise HTTPException(400, f"price_unit must be one of {valid_units}")
    with db.connect() as c:
        # Check vendor exists
        v = c.execute("SELECT id FROM vendors WHERE id=?", (body.vendor_id,)).fetchone()
        if not v:
            raise HTTPException(404, "vendor not found")
        c.execute(
            "INSERT INTO vendor_services(vendor_id, service_id, area, price_aed, "
            "price_unit, sla_hours, active, notes) VALUES(?,?,?,?,?,?,?,?) "
            "ON CONFLICT(vendor_id, service_id, area) DO UPDATE SET "
            "price_aed=excluded.price_aed, price_unit=excluded.price_unit, "
            "sla_hours=excluded.sla_hours, active=excluded.active, notes=excluded.notes",
            (body.vendor_id, sid, body.area, body.price_aed, body.price_unit,
             body.sla_hours, 1 if body.active else 0, body.notes),
        )
    db.log_event("service", sid, "vendor_pricing_set", actor="admin",
                 details={"vendor_id": body.vendor_id, "price": body.price_aed})
    return {"ok": True}


@router.delete("/service/{sid}/vendor/{vid}")
def remove_vendor_from_service(sid: str, vid: int):
    with db.connect() as c:
        c.execute("DELETE FROM vendor_services WHERE service_id=? AND vendor_id=?",
                  (sid, vid))
    return {"ok": True}


@router.get("/services-summary")
def services_summary():
    """Lightweight list of services with vendor counts, for the admin grid."""
    services = kb.services()["services"]
    rules = kb.pricing()["rules"]
    with db.connect() as c:
        counts = {r["service_id"]: dict(r) for r in c.execute(
            "SELECT service_id, COUNT(*) AS vendor_count, "
            "MIN(price_aed) AS min_price, AVG(price_aed) AS avg_price "
            "FROM vendor_services GROUP BY service_id").fetchall()}
    out = []
    for s in services:
        c2 = counts.get(s["id"], {})
        out.append({
            **s,
            "rule": rules.get(s["id"], {}),
            "vendor_count": c2.get("vendor_count", 0),
            "min_price_aed": c2.get("min_price"),
            "avg_price_aed": c2.get("avg_price"),
        })
    return {"services": out}


# ---------- Brand settings (runtime editable) ----------
class BrandPatch(BaseModel):
    name: str | None = None
    tagline: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    address: str | None = None
    primary_color: str | None = None
    accent_color: str | None = None
    legal_owner: str | None = None
    vat_trn: str | None = None
    domain: str | None = None


@router.get("/brand")
def get_brand_admin():
    from .config import get_settings
    return get_settings().brand()


@router.post("/brand")
def patch_brand(body: BrandPatch):
    from .config import get_settings
    overrides = db.cfg_get("brand_overrides", {}) or {}
    payload = body.model_dump(exclude_none=True)
    overrides.update({k: v for k, v in payload.items() if v not in (None, "")})
    db.cfg_set("brand_overrides", overrides)
    db.log_event("brand", "global", "updated", actor="admin",
                 details={"keys": list(payload)})
    return {"ok": True, "brand": get_settings().brand()}


# ---------- CSV exports ----------
@router.get("/export/bookings.csv")
def export_bookings_csv():
    from fastapi.responses import Response
    import csv, io
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, service_id, target_date, time_slot, customer_name, phone, "
            "address, status, estimated_total, currency, created_at "
            "FROM bookings ORDER BY created_at DESC"
        ).fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id","service","date","time","customer","phone","address",
                "status","total","currency","created_at"])
    for r in rows:
        w.writerow([r[k] for k in ("id","service_id","target_date","time_slot",
                    "customer_name","phone","address","status",
                    "estimated_total","currency","created_at")])
    return Response(content=buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=lumora-bookings.csv"})


# ---------- Seed market vendors (idempotent bulk-load) ----------
@router.post("/seed/vendors")
def seed_market_vendors():
    """Load app/data/vendors_seed.json and upsert vendors + per-service pricing.
    Re-running this endpoint updates prices but never duplicates."""
    import datetime as _dt, json
    from .config import get_settings
    from . import auth_users
    settings = get_settings()
    seed_path = settings.DATA_DIR / "vendors_seed.json"
    if not seed_path.exists():
        raise HTTPException(404, "vendors_seed.json not found")
    seed = json.loads(seed_path.read_text())
    vendors = seed.get("vendors", [])
    valid_sids = {s["id"] for s in kb.services()["services"]}
    created = updated = svc_links = 0
    default_pw = "lumora-vendor-default"
    pwhash = auth_users.hash_password(default_pw)
    now = _dt.datetime.utcnow().isoformat() + "Z"
    with db.connect() as c:
        for v in vendors:
            email = v["email"].lower().strip()
            existing = c.execute("SELECT id FROM vendors WHERE email=?", (email,)).fetchone()
            if existing:
                vid = existing["id"]
                c.execute(
                    "UPDATE vendors SET name=?, phone=?, company=?, rating=?, "
                    "completed_jobs=?, is_approved=1, is_active=1 WHERE id=?",
                    (v.get("name"), v.get("phone"), v.get("company"),
                     v.get("rating", 4.7), v.get("completed_jobs", 0), vid))
                updated += 1
            else:
                cur = c.execute(
                    "INSERT INTO vendors(email, password_hash, name, phone, company, "
                    "rating, completed_jobs, is_approved, is_active, created_at) "
                    "VALUES(?,?,?,?,?,?,?,1,1,?)",
                    (email, pwhash, v.get("name"), v.get("phone"), v.get("company"),
                     v.get("rating", 4.7), v.get("completed_jobs", 0), now))
                vid = cur.lastrowid
                created += 1
            for sid, info in (v.get("services") or {}).items():
                if sid not in valid_sids:
                    continue
                c.execute(
                    "INSERT INTO vendor_services(vendor_id, service_id, area, price_aed, "
                    "price_unit, sla_hours, active, notes) VALUES(?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(vendor_id, service_id, area) DO UPDATE SET "
                    "price_aed=excluded.price_aed, price_unit=excluded.price_unit, "
                    "sla_hours=excluded.sla_hours, active=excluded.active, notes=excluded.notes",
                    (vid, sid, "*",
                     info.get("price_aed"),
                     info.get("price_unit", "fixed"),
                     info.get("sla_hours", 24),
                     1, info.get("notes")))
                svc_links += 1
    db.log_event("seed", "vendors", "executed", actor="admin",
                 details={"created": created, "updated": updated, "svc_links": svc_links})
    return {"ok": True, "created": created, "updated": updated,
            "service_offerings": svc_links,
            "default_password_hint": "Vendors can sign in with the email above and password 'lumora-vendor-default' — change on first login."}


# ---------- impersonation ("login as customer/vendor") ----------
class ImpersonateBody(BaseModel):
    user_type: str   # 'customer' or 'vendor'
    user_id: int


@router.post("/impersonate", dependencies=[Depends(require_admin)])
def impersonate(body: ImpersonateBody):
    if body.user_type not in ("customer", "vendor"):
        raise HTTPException(400, "user_type must be 'customer' or 'vendor'")
    table = "customers" if body.user_type == "customer" else "vendors"
    with db.connect() as c:
        row = c.execute(f"SELECT * FROM {table} WHERE id=?", (body.user_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"{body.user_type} not found")
    rec = db.row_to_dict(row)
    token = auth_users.create_session(body.user_type, body.user_id)
    db.log_event("admin", "impersonate", body.user_type, actor="admin",
                 details={"user_id": body.user_id, "name": rec.get("name") or rec.get("email")})
    return {"ok": True, "token": token, "user_type": body.user_type,
            "user": {"id": body.user_id,
                     "name": rec.get("name"),
                     "email": rec.get("email"),
                     "phone": rec.get("phone")},
            "redirect": "/me.html" if body.user_type == "customer" else "/vendor.html"}


@router.get("/customers", dependencies=[Depends(require_admin)])
def list_customers():
    """Lightweight customer list for the admin 'login as' picker."""
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, name, phone, email, created_at, "
            "(SELECT COUNT(*) FROM bookings WHERE customer_phone=customers.phone) AS bookings "
            "FROM customers ORDER BY id DESC LIMIT 200"
        ).fetchall()
    return {"customers": [db.row_to_dict(r) for r in rows]}


# ---------- vendor outreach / onboarding ----------
class OutreachLead(BaseModel):
    name: str
    phone: str               # E.164 like +9715xxxxxxxx
    company: str | None = None
    services: list[str] = []  # service IDs to pre-check on the signup form
    email: str | None = None
    notes: str | None = None


@router.post("/outreach/invite", dependencies=[Depends(require_admin)])
def send_outreach_invite(body: OutreachLead, request: Request):
    """Send a WhatsApp invite to a prospective vendor with a personalised signup
    link. Records the lead so we can track conversions."""
    from . import tools as _tools
    from .config import get_settings as _gs
    b = _gs().brand()
    # Build prefilled signup URL
    base = str(request.base_url).rstrip("/")
    qs = {"as": "partner", "ref": "outreach"}
    if body.name: qs["name"] = body.name
    if body.email: qs["email"] = body.email
    if body.company: qs["company"] = body.company
    if body.services: qs["services"] = ",".join(body.services)
    from urllib.parse import urlencode
    signup_url = f"{base}/login.html?{urlencode(qs)}"

    msg = (
        f"السلام عليكم {body.name},\n\n"
        f"This is {b['name']} — UAE's home services platform. We send 1000s of bookings/month "
        f"to vetted partners across {', '.join((body.services or [])[:3]) or 'cleaning, AC, handyman & more'}.\n\n"
        f"We'd like to invite you to join our partner network:\n"
        f"✓ 80% payout on every job (we keep 20% platform fee)\n"
        f"✓ Set your own pricing per service\n"
        f"✓ Weekly bank transfer\n"
        f"✓ Free customer acquisition + marketing\n"
        f"✓ No listing or monthly fees\n\n"
        f"Sign up in 2 minutes (services pre-selected for you):\n{signup_url}\n\n"
        f"Or reply YES and our team will set you up.\n\n"
        f"— {b['name']} Partner Onboarding\n{b.get('whatsapp', '')}"
    )

    push = _tools.send_whatsapp(body.phone, msg)
    db.log_event("admin", "outreach_invite", "sent", actor="admin",
                 details={"phone": body.phone, "name": body.name,
                          "services": body.services, "ok": push.get("ok"),
                          "signup_url": signup_url})
    # Persist the lead so we can show it in the outreach tab
    _record_outreach_lead(body, signup_url, push.get("ok", False))
    return {"ok": True, "wa_send": push, "signup_url": signup_url}


def _record_outreach_lead(b: OutreachLead, url: str, sent: bool) -> None:
    with db.connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS outreach_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, phone TEXT UNIQUE, company TEXT, email TEXT,
                services TEXT, notes TEXT, signup_url TEXT,
                wa_sent INTEGER DEFAULT 0, status TEXT DEFAULT 'invited',
                created_at TEXT, updated_at TEXT)
        """)
        now = __import__("datetime").datetime.utcnow().isoformat() + "Z"
        c.execute(
            "INSERT INTO outreach_leads(name,phone,company,email,services,notes,signup_url,wa_sent,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(phone) DO UPDATE SET name=excluded.name, company=excluded.company, "
            "email=excluded.email, services=excluded.services, notes=excluded.notes, "
            "signup_url=excluded.signup_url, wa_sent=excluded.wa_sent, updated_at=excluded.updated_at",
            (b.name, b.phone, b.company, b.email, ",".join(b.services or []),
             b.notes, url, 1 if sent else 0, now, now))


@router.get("/outreach/leads", dependencies=[Depends(require_admin)])
def list_outreach_leads():
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT * FROM outreach_leads ORDER BY id DESC LIMIT 500"
            ).fetchall()
        except Exception:
            return {"leads": []}
    return {"leads": [db.row_to_dict(r) for r in rows]}


class BulkLeadsBody(BaseModel):
    leads: list[OutreachLead]


@router.post("/outreach/bulk", dependencies=[Depends(require_admin)])
def bulk_invite(body: BulkLeadsBody, request: Request):
    sent = 0
    failed = 0
    results = []
    for lead in body.leads:
        try:
            r = send_outreach_invite(lead, request)
            results.append({"phone": lead.phone, "ok": r.get("ok"), "wa": r.get("wa_send", {}).get("ok")})
            if r.get("wa_send", {}).get("ok"):
                sent += 1
            else:
                failed += 1
        except Exception as e:  # noqa: BLE001
            failed += 1
            results.append({"phone": lead.phone, "ok": False, "error": str(e)})
    return {"ok": True, "sent": sent, "failed": failed, "results": results}


# ---------- bot prompts (admin-editable) ----------
@router.get("/prompts", dependencies=[Depends(require_admin)])
def get_prompts():
    """Return current prompts (overrides or defaults) for both personas."""
    from .llm import VENDOR_PERSONA_DEFAULT
    p = db.cfg_get("llm_prompts", {}) or {}
    # The customer default is rendered inside _system_blocks; for admin display
    # we just show the override and the default-template note.
    return {
        "customer": p.get("customer", ""),
        "customer_default_note": "If empty, the built-in customer concierge prompt is used.",
        "vendor": p.get("vendor", VENDOR_PERSONA_DEFAULT),
        "vendor_default": VENDOR_PERSONA_DEFAULT,
        "available_vars": ["{brand}", "{domain}", "{legal_owner}", "{tagline}", "{language}"],
    }


class PromptsBody(BaseModel):
    customer: str | None = None
    vendor: str | None = None


@router.post("/prompts", dependencies=[Depends(require_admin)])
def save_prompts(body: PromptsBody):
    cur = db.cfg_get("llm_prompts", {}) or {}
    if body.customer is not None: cur["customer"] = body.customer
    if body.vendor is not None: cur["vendor"] = body.vendor
    db.cfg_set("llm_prompts", cur)
    db.log_event("admin", "prompts", "saved", actor="admin",
                 details={"customer_len": len(cur.get("customer", "")),
                          "vendor_len": len(cur.get("vendor", ""))})
    return {"ok": True, "saved": list(cur.keys())}


# ---------- in-place CMS overrides (page content overrides) ----------
@router.get("/cms")
def cms_get_all():
    """Return all CMS overrides — public (no auth) so each page can apply them on load."""
    return db.cfg_get("cms_overrides", {}) or {}


class CmsBody(BaseModel):
    key: str          # data-cms-key value
    html: str         # new innerHTML
    page: str | None = None  # optional page path for organisation


@router.post("/cms", dependencies=[Depends(require_admin)])
def cms_save(body: CmsBody):
    cur = db.cfg_get("cms_overrides", {}) or {}
    cur[body.key] = body.html
    db.cfg_set("cms_overrides", cur)
    db.log_event("admin", "cms", "saved", actor="admin",
                 details={"key": body.key, "page": body.page})
    return {"ok": True}


@router.delete("/cms/{key}", dependencies=[Depends(require_admin)])
def cms_delete(key: str):
    cur = db.cfg_get("cms_overrides", {}) or {}
    cur.pop(key, None)
    db.cfg_set("cms_overrides", cur)
    return {"ok": True}


# ---------- payment provider config ----------
@router.get("/payments/status", dependencies=[Depends(require_admin)])
def payments_status():
    import os
    return {
        "stripe": {
            "enabled": bool(os.getenv("STRIPE_SECRET_KEY")),
            "webhook_secret": bool(os.getenv("STRIPE_WEBHOOK_SECRET")),
            "webhook_endpoint": "/api/webhooks/stripe",
        },
        "telr": {"enabled": bool(os.getenv("TELR_STORE_ID")), "note": "UAE-local"},
        "paytabs": {"enabled": bool(os.getenv("PAYTABS_PROFILE_ID")), "note": "UAE-local"},
        "tap": {"enabled": bool(os.getenv("TAP_API_KEY")), "note": "GCC"},
    }


# ---------- service-delivery completion + automated followups ----------
class CompleteJobBody(BaseModel):
    notes: str | None = None
    photos: list[str] = []   # URLs of completion photos uploaded externally


@router.post("/jobs/{bid}/complete", dependencies=[Depends(require_admin)])
def complete_job(bid: str, body: CompleteJobBody):
    """Mark a booking complete + send the customer the review link via WhatsApp.

    The bot will WhatsApp again 7 days later for retention follow-up.
    """
    from . import tools as _t
    with db.connect() as c:
        b = c.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone()
        if not b:
            raise HTTPException(404, "booking not found")
        # Add delivery metadata column if missing (safe migration)
        try:
            c.execute("ALTER TABLE bookings ADD COLUMN delivery_notes TEXT")
        except Exception: pass
        try:
            c.execute("ALTER TABLE bookings ADD COLUMN delivery_photos TEXT")
        except Exception: pass
        c.execute("UPDATE bookings SET status='completed', delivery_notes=?, "
                  "delivery_photos=?, completed_at=? WHERE id=?",
                  (body.notes, ",".join(body.photos),
                   __import__("datetime").datetime.utcnow().isoformat() + "Z", bid))
    db.log_event("booking", bid, "completed", actor="admin",
                 details={"photos": len(body.photos)})

    # Send delivery + review-request WhatsApp to customer
    from .config import get_settings
    base = "https://" + get_settings().BRAND_DOMAIN
    review_url = f"{base}/delivered.html?b={bid}"
    msg = (
        f"✅ Your Servia service is complete (booking {bid}).\n\n"
        f"How did it go? Tap to review (30 seconds): {review_url}\n\n"
        f"5★? We'll send your invoice to WhatsApp + email shortly. "
        f"Need anything else? Reply to this message and we'll help."
    )
    push = _t.send_whatsapp(b["phone"], msg) if b["phone"] else {"ok": False, "error": "no phone"}
    return {"ok": True, "review_url": review_url, "wa_send": push}


@router.get("/jobs/pending-followup", dependencies=[Depends(require_admin)])
def list_pending_followups():
    """Bookings completed 6-8 days ago without a 7-day follow-up sent yet.
    Cron job (or admin manual click) calls /jobs/{bid}/followup."""
    import datetime as _dt
    cutoff_old = (_dt.datetime.utcnow() - _dt.timedelta(days=8)).isoformat() + "Z"
    cutoff_new = (_dt.datetime.utcnow() - _dt.timedelta(days=6)).isoformat() + "Z"
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT id, customer_name, phone, service_id, completed_at "
                "FROM bookings WHERE status='completed' "
                "AND completed_at BETWEEN ? AND ? "
                "AND COALESCE(followup_sent_at,'') = '' "
                "ORDER BY completed_at",
                (cutoff_old, cutoff_new)).fetchall()
        except Exception:
            # followup_sent_at column may not exist — try to add
            try: c.execute("ALTER TABLE bookings ADD COLUMN followup_sent_at TEXT")
            except Exception: pass
            try: c.execute("ALTER TABLE bookings ADD COLUMN completed_at TEXT")
            except Exception: pass
            rows = []
    return {"pending": [db.row_to_dict(r) for r in rows]}


@router.post("/jobs/{bid}/followup", dependencies=[Depends(require_admin)])
def send_followup(bid: str):
    from . import tools as _t
    with db.connect() as c:
        b = c.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone()
        if not b:
            raise HTTPException(404, "booking not found")
        c.execute("UPDATE bookings SET followup_sent_at=? WHERE id=?",
                  (__import__("datetime").datetime.utcnow().isoformat() + "Z", bid))
    msg = (
        f"Hi {b['customer_name']}, hope everything's still great after your Servia "
        f"{b['service_id'].replace('_',' ')} last week. Want to book the same crew "
        f"again? Reply with the day + time and we'll lock it in. — Servia"
    )
    return _t.send_whatsapp(b["phone"], msg)


# ---------- stealth-launch market signals ----------
class MarketSignalBody(BaseModel):
    booking_id: str | None = None
    service_id: str | None = None
    quoted_price: float | None = None
    customer_name: str | None = None
    phone: str | None = None
    emirate: str | None = None
    voice_url: str | None = None        # uploaded voice memo (optional)
    feedback_text: str | None = None    # what they typed
    intent: str | None = None           # 'would_book' | 'too_expensive' | 'comparing' | 'other'
    accepts_coupon: bool = False        # opted into 15% launch coupon
    user_agent: str | None = None
    referrer: str | None = None




@router.get("/market-signals", dependencies=[Depends(require_admin)])
def list_market_signals(limit: int = 200):
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT * FROM market_signals ORDER BY id DESC LIMIT ?",
                (limit,)).fetchall()
        except Exception: rows = []
        # Aggregates
        try:
            stats = {
                "total": c.execute("SELECT COUNT(*) AS n FROM market_signals").fetchone()["n"] or 0,
                "would_book": c.execute("SELECT COUNT(*) AS n FROM market_signals WHERE intent='would_book'").fetchone()["n"] or 0,
                "too_expensive": c.execute("SELECT COUNT(*) AS n FROM market_signals WHERE intent='too_expensive'").fetchone()["n"] or 0,
                "avg_quoted": c.execute("SELECT AVG(quoted_price) AS a FROM market_signals WHERE quoted_price IS NOT NULL").fetchone()["a"] or 0,
                "by_service": [dict(r) for r in c.execute(
                    "SELECT service_id, COUNT(*) AS n, AVG(quoted_price) AS avg "
                    "FROM market_signals WHERE service_id IS NOT NULL "
                    "GROUP BY service_id ORDER BY n DESC LIMIT 20").fetchall()],
                "by_emirate": [dict(r) for r in c.execute(
                    "SELECT emirate, COUNT(*) AS n FROM market_signals "
                    "WHERE emirate IS NOT NULL GROUP BY emirate ORDER BY n DESC").fetchall()]
            }
        except Exception: stats = {}
    return {"signals": [db.row_to_dict(r) for r in rows], "stats": stats}


# ---------- analytics deep-dive ----------
@router.get("/analytics", dependencies=[Depends(require_admin)])
def analytics_overview():
    """One-shot analytics endpoint that aggregates funnel + sources + sentiment."""
    with db.connect() as c:
        # Booking funnel
        funnel = {
            "visited": c.execute("SELECT COUNT(*) AS n FROM conversations WHERE role='user'").fetchone()["n"] or 0,
            "quoted": c.execute("SELECT COUNT(DISTINCT booking_id) AS n FROM quotes").fetchone()["n"] or 0,
            "booked": c.execute("SELECT COUNT(*) AS n FROM bookings").fetchone()["n"] or 0,
            "paid": c.execute("SELECT COUNT(*) AS n FROM invoices WHERE payment_status='paid'").fetchone()["n"] or 0,
            "completed": c.execute("SELECT COUNT(*) AS n FROM bookings WHERE status='completed'").fetchone()["n"] or 0,
            "reviewed": c.execute("SELECT COUNT(*) AS n FROM reviews").fetchone()["n"] or 0,
        }
        # Top sources (from booking source field)
        try:
            sources = [dict(r) for r in c.execute(
                "SELECT source, COUNT(*) AS n FROM bookings GROUP BY source ORDER BY n DESC LIMIT 10"
            ).fetchall()]
        except Exception: sources = []
        # Top services
        try:
            services = [dict(r) for r in c.execute(
                "SELECT service_id, COUNT(*) AS n, AVG(estimated_total) AS avg "
                "FROM bookings GROUP BY service_id ORDER BY n DESC LIMIT 15"
            ).fetchall()]
        except Exception: services = []
        # Sentiment from review stars
        try:
            sentiment = dict(c.execute(
                "SELECT AVG(stars) AS avg_stars, COUNT(*) AS total, "
                "SUM(CASE WHEN stars=5 THEN 1 ELSE 0 END) AS five_star, "
                "SUM(CASE WHEN stars<=2 THEN 1 ELSE 0 END) AS low_star "
                "FROM reviews"
            ).fetchone() or {})
        except Exception: sentiment = {}
        # Vendor performance leaderboard
        try:
            vendors = [dict(r) for r in c.execute(
                "SELECT v.id, v.name, v.rating, v.completed_jobs, "
                "COUNT(a.id) AS active_jobs FROM vendors v "
                "LEFT JOIN assignments a ON a.vendor_id=v.id "
                "GROUP BY v.id ORDER BY v.rating DESC, v.completed_jobs DESC LIMIT 15"
            ).fetchall()]
        except Exception: vendors = []
        # Recent market signals (gate captures)
        try:
            signals_count = c.execute("SELECT COUNT(*) AS n FROM market_signals").fetchone()["n"] or 0
            referrals_count = c.execute("SELECT COUNT(*) AS n FROM referrals").fetchone()["n"] or 0
        except Exception:
            signals_count = 0; referrals_count = 0
    return {
        "funnel": funnel, "sources": sources, "services": services,
        "sentiment": sentiment, "vendors": vendors,
        "market_signals_count": signals_count,
        "referrals_count": referrals_count,
    }


# ---------- auto-blog (Claude-generated daily article per emirate) ----------
@router.post("/autoblog/run", dependencies=[Depends(require_admin)])
def autoblog_run(emirate: str = "dubai", topic: str | None = None):
    """Generate one Servia-branded article for the given emirate using Claude.
    Cron-friendly: schedule a daily POST with a different emirate to maintain
    fresh content for SEO + AI engines. Articles stored in 'autoblog_posts'
    table with slug + content + metadata."""
    import os as _os
    from .config import get_settings
    s = get_settings()
    if not s.use_llm:
        return {"ok": False, "error": "LLM disabled (set ANTHROPIC_API_KEY)"}

    # Topic rotation if not specified
    DEFAULT_TOPICS = [
        "Best deep cleaning checklist for {emirate} apartments",
        "How to choose AC service in {emirate} — what to ask",
        "Seasonal maintenance tips for {emirate} villas",
        "Pest control done right in {emirate}",
        "Move-in / move-out cleaning guide for {emirate}",
        "Top 5 home services every {emirate} family needs",
        "Why pre-paid bookings beat cash-on-completion in {emirate}",
        "Same-day handyman in {emirate} — how Servia delivers in hours",
    ]
    if not topic:
        import random
        topic = random.choice(DEFAULT_TOPICS).format(emirate=emirate.replace("-"," ").title())

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=s.ANTHROPIC_API_KEY, timeout=30, max_retries=1)
        msg = client.messages.create(
            model=s.MODEL,
            max_tokens=2000,
            messages=[{"role":"user","content":(
                f"Write a 600-word SEO-optimized article for Servia (UAE home services platform).\n\n"
                f"Title: {topic}\n"
                f"Emirate: {emirate.replace('-',' ').title()}\n\n"
                "Style: Helpful, locally-informed, mention specific neighborhoods, include 1-2 actionable tips, "
                "include a clear CTA at the end pointing to https://servia.ae/book.html. "
                "Use H2 subheadings (markdown ##) for structure. Mention Servia naturally 2-3 times — "
                "not spammy. End with a short FAQ (2-3 Qs).")}],
        )
        body = msg.content[0].text if msg.content else ""
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"Claude call failed: {e}"}

    import datetime as _dtm
    slug = (
        emirate + "-" +
        "".join(c.lower() if c.isalnum() else "-" for c in topic).strip("-")
    )[:80]
    with db.connect() as c:
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
            (slug, emirate, topic, body,
             _dtm.datetime.utcnow().isoformat() + "Z"))
    db.log_event("autoblog", slug, "published", actor="admin",
                 details={"emirate": emirate, "topic": topic, "len": len(body)})
    return {"ok": True, "slug": slug, "topic": topic, "len": len(body),
            "url": f"/blog/{slug}"}


@router.get("/autoblog", dependencies=[Depends(require_admin)])
def autoblog_list():
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT slug, emirate, topic, published_at, view_count "
                "FROM autoblog_posts ORDER BY id DESC LIMIT 200"
            ).fetchall()
        except Exception: rows = []
    return {"posts": [db.row_to_dict(r) for r in rows]}


# ---------- WhatsApp admin pairing + alerts ----------
@router.get("/whatsapp/qr")
def whatsapp_qr():
    """Proxies the bridge's /qr page so admin can scan inline. Returns
    {ready, paired_number, qr_data_url} JSON for the admin UI to render."""
    from .config import get_settings
    s = get_settings()
    if not s.WA_BRIDGE_URL:
        return {"configured": False, "error":
                "WA_BRIDGE_URL not set. Deploy whatsapp_bridge/ as a separate "
                "Railway service and set WA_BRIDGE_URL + WA_BRIDGE_TOKEN."}
    import httpx, base64
    try:
        # Status check
        r = httpx.get(s.WA_BRIDGE_URL.rstrip("/") + "/status",
                      headers={"Authorization": f"Bearer {s.WA_BRIDGE_TOKEN}"},
                      timeout=5)
        info = r.json() if r.ok else {"error": r.text}
        if info.get("ready"):
            return {"configured": True, "ready": True,
                    "paired_number": info.get("paired_number")}
        # Fetch QR page
        rq = httpx.get(s.WA_BRIDGE_URL.rstrip("/") + "/qr",
                       headers={"Authorization": f"Bearer {s.WA_BRIDGE_TOKEN}"},
                       timeout=8)
        return {"configured": True, "ready": False,
                "qr_html": rq.text if rq.ok else None,
                "bridge_url": s.WA_BRIDGE_URL.rstrip("/")}
    except Exception as e:
        return {"configured": True, "ready": False, "error": str(e)}


class WaSendBody(BaseModel):
    to: str | None = None  # default: admin number
    text: str


@router.post("/whatsapp/send")
def whatsapp_send(body: WaSendBody):
    from . import admin_alerts
    # If `to` is omitted, send to admin
    if body.to:
        # Direct send via bridge
        from .config import get_settings
        import httpx
        s = get_settings()
        if not s.WA_BRIDGE_URL:
            return {"ok": False, "error": "bridge not configured"}
        try:
            r = httpx.post(
                s.WA_BRIDGE_URL.rstrip("/") + "/send",
                headers={"Authorization": f"Bearer {s.WA_BRIDGE_TOKEN}",
                         "content-type": "application/json"},
                json={"to": body.to, "text": body.text}, timeout=8)
            return r.json() if r.ok else {"ok": False, "error": r.text}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return admin_alerts.notify_admin_sync(body.text, kind="manual_test")


@router.get("/alerts")
def list_alerts(limit: int = 50):
    """Last N admin alerts — for visibility even when WA bridge not paired."""
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT id, kind, urgency, text, delivered, delivery_error, created_at "
                "FROM admin_alerts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        except Exception:
            rows = []
    return {"alerts": [db.row_to_dict(r) for r in rows]}


@router.post("/alerts/daily-summary")
def fire_daily_summary():
    from . import admin_alerts
    return admin_alerts.push_daily_summary()
