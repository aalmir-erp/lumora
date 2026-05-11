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


@router.get("/bookings/{bid}/detail")
def booking_detail(bid: str):
    """v1.24.15 — full join across customer + vendor + assignment +
    recovery dispatch + invoice + reviews + photos + events for the
    admin booking-detail modal."""
    with db.connect() as c:
        b = c.execute(
            "SELECT b.*, c.id AS customer_id, c.name AS c_name, c.email AS c_email, "
            "       c.created_at AS c_created_at, c.last_seen_at AS c_last_seen_at "
            "FROM bookings b LEFT JOIN customers c ON c.phone = b.phone "
            "WHERE b.id = ?", (bid,)
        ).fetchone()
        if not b:
            raise HTTPException(404, "booking not found")
        b = dict(b)
        rec = c.execute(
            "SELECT * FROM recovery_dispatches WHERE booking_id=?", (bid,)
        ).fetchone()
        rec = dict(rec) if rec else None
        a = c.execute(
            "SELECT a.*, v.name AS v_name, v.phone AS v_phone, v.email AS v_email, "
            "       v.company AS v_company, v.rating AS v_rating, "
            "       v.completed_jobs AS v_jobs "
            "FROM assignments a LEFT JOIN vendors v ON v.id = a.vendor_id "
            "WHERE a.booking_id=? ORDER BY a.id DESC LIMIT 1",
            (bid,)
        ).fetchone()
        a = dict(a) if a else None
        invs = [dict(r) for r in c.execute(
            "SELECT * FROM invoices WHERE booking_id=? ORDER BY id DESC", (bid,)
        ).fetchall()]
        rev = c.execute(
            "SELECT * FROM reviews WHERE booking_id=? ORDER BY id DESC LIMIT 1",
            (bid,)
        ).fetchone()
        rev = dict(rev) if rev else None
        evs = [dict(r) for r in c.execute(
            "SELECT * FROM events WHERE entity_type IN ('booking','recovery','assignment','invoice') "
            "  AND (entity_id=? OR entity_id=?) "
            "ORDER BY id ASC",
            (bid, str(rec["id"]) if rec else "__none__")
        ).fetchall()]
    photos = []
    if b.get("notes"):
        for line in (b["notes"] or "").splitlines():
            for tok in line.split():
                if tok.startswith("/uploads/") or (tok.startswith("http") and ("/uploads/" in tok or ".jpg" in tok or ".png" in tok)):
                    photos.append(tok.rstrip(",.;"))
    if rec and rec.get("photo_url") and rec["photo_url"] not in photos:
        photos.append(rec["photo_url"])
    return {
        "ok": True,
        "booking": b,
        "recovery_dispatch": rec,
        "assignment": a,
        "invoices": invs,
        "review": rev,
        "events": evs,
        "photos": photos,
    }


@router.post("/bookings/{bid}/status")
def update_status(bid: str, body: StatusUpdate):
    return tools.update_booking_status(bid, body.status, actor="admin")


# v1.24.19 — one-click curated vendor import (no scraping, no API keys).
# Loads app/data/vendors_recovery_uae_curated.json (~108 real UAE recovery
# brands across all 7 emirates, 8 categories). Each vendor row carries
# verified=false until admin confirms the phone — clicking the source_url
# opens Yellow Pages / Google Maps so admin pastes the real phone in.
@router.post("/vendors/import-recovery-curated")
def import_recovery_curated():
    import json as _j, datetime as _d, pathlib as _p
    from . import auth_users as _au
    p = _p.Path("app/data/vendors_recovery_uae_curated.json")
    if not p.exists():
        raise HTTPException(404, "vendors_recovery_uae_curated.json not found")
    data = _j.loads(p.read_text())
    now = _d.datetime.utcnow().isoformat() + "Z"
    pwhash = _au.hash_password("servia-recovery-vendor-default")
    imported = updated = skipped = 0
    with db.connect() as c:
        # Idempotent — additive columns for category + verified flag
        for ddl in (
            "ALTER TABLE vendors ADD COLUMN categories TEXT",
            "ALTER TABLE vendors ADD COLUMN emirate TEXT",
            "ALTER TABLE vendors ADD COLUMN area TEXT",
            "ALTER TABLE vendors ADD COLUMN website TEXT",
            "ALTER TABLE vendors ADD COLUMN source_url TEXT",
            "ALTER TABLE vendors ADD COLUMN verified INTEGER DEFAULT 0",
            "ALTER TABLE vendors ADD COLUMN needs_verification INTEGER DEFAULT 1",
        ):
            try: c.execute(ddl)
            except Exception: pass
        for v in data.get("vendors", []):
            email = (v["name"].lower()
                     .replace(" ", ".").replace("&", "and")
                     .replace("/", "-")
                     .replace("(", "").replace(")", ""))[:60] + "@servia-vendors.lumora"
            row = c.execute("SELECT id FROM vendors WHERE email=?", (email,)).fetchone()
            cats = ",".join(v.get("categories", []))
            verified = 1 if v.get("verified") else 0
            needs_v = 0 if verified else 1
            phone_raw = v.get("phone") or ""
            if row:
                c.execute(
                    "UPDATE vendors SET name=?, phone=?, rating=?, "
                    "categories=?, emirate=?, area=?, website=?, source_url=?, "
                    "verified=?, needs_verification=? WHERE id=?",
                    (v["name"], phone_raw, float(v.get("rating") or 4.5),
                     cats, v.get("emirate"), v.get("area"),
                     v.get("website"), v.get("source_url"),
                     verified, needs_v, row["id"])
                )
                vid = row["id"]
                updated += 1
            else:
                cur = c.execute(
                    "INSERT INTO vendors(email, password_hash, name, phone, company, "
                    "rating, completed_jobs, is_active, is_approved, created_at, "
                    "categories, emirate, area, website, source_url, verified, needs_verification) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (email, pwhash, v["name"], phone_raw, v["name"],
                     float(v.get("rating") or 4.5), 0,
                     1 if verified else 0,    # don't auto-activate unverified
                     1 if verified else 0,    # don't auto-approve unverified
                     now, cats, v.get("emirate"), v.get("area"),
                     v.get("website"), v.get("source_url"),
                     verified, needs_v)
                )
                vid = cur.lastrowid
                imported += 1
            # Add vehicle_recovery service_id binding for ALL of them
            for sid in ("vehicle_recovery",):
                try:
                    c.execute(
                        "INSERT OR IGNORE INTO vendor_services(vendor_id, service_id, "
                        "area, price_aed, active) VALUES(?,?,?,?,?)",
                        (vid, sid, v.get("area") or "*", 250.0, 1 if verified else 0)
                    )
                except Exception: pass
    db.log_event("admin", "vendors", "import_recovery_curated",
                 details={"imported": imported, "updated": updated})
    return {
        "ok": True, "imported": imported, "updated": updated,
        "total_processed": len(data.get("vendors", [])),
        "next_step": "Open admin → Vendors → filter by 'needs verification' → click each → open source_url → copy real phone → save. Once verified=1 they auto-activate and start receiving auction blasts.",
    }


@router.get("/vendors/needs-verification")
def vendors_needing_verification(emirate: str | None = None,
                                  category: str | None = None,
                                  limit: int = 200):
    """Return curated vendors awaiting phone verification — admin worksheet."""
    sql = ("SELECT id, name, phone, rating, emirate, area, website, source_url, "
           "categories, verified, needs_verification, is_active "
           "FROM vendors WHERE COALESCE(needs_verification, 0) = 1")
    params: list = []
    if emirate:
        sql += " AND emirate = ?"; params.append(emirate)
    if category:
        sql += " AND categories LIKE ?"; params.append(f"%{category}%")
    sql += " ORDER BY emirate, area, name LIMIT ?"
    params.append(limit)
    with db.connect() as c:
        rows = c.execute(sql, params).fetchall()
    return {"items": [dict(r) for r in rows], "count": len(rows)}


class _VerifyVendorBody(BaseModel):
    phone: str
    verified: bool = True


@router.post("/vendors/{vid}/verify")
def verify_vendor(vid: int, body: _VerifyVendorBody):
    """Admin marks a vendor's phone as verified after looking it up.
    Auto-activates the vendor + their vehicle_recovery service binding."""
    from . import uae_phone as _ph
    phone = _ph.normalize(body.phone) or body.phone
    with db.connect() as c:
        n = c.execute(
            "UPDATE vendors SET phone=?, verified=?, needs_verification=?, "
            "is_active=?, is_approved=? WHERE id=?",
            (phone, 1 if body.verified else 0,
             0 if body.verified else 1,
             1 if body.verified else 0,
             1 if body.verified else 0, vid)
        ).rowcount
        if not n:
            raise HTTPException(404, "vendor not found")
        c.execute(
            "UPDATE vendor_services SET active=? WHERE vendor_id=?",
            (1 if body.verified else 0, vid)
        )
    return {"ok": True, "vendor_id": vid, "phone": phone, "verified": body.verified}


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


# ---------- Per-service addons editor ----------
class AddonsBody(BaseModel):
    service_id: str
    addons: list[dict]   # [{id, label, price, default?}]


@router.get("/services/{service_id}/addons")
def get_service_addons(service_id: str):
    """Returns the addons array currently in effect for this service.
    Sources merged in priority order: services_overrides → kb default."""
    overrides = db.cfg_get("services_overrides", {}) or {}
    o = overrides.get(service_id, {}) or {}
    if "addons" in o: return {"service_id": service_id, "addons": o["addons"], "source": "override"}
    svc = next((s for s in kb.services()["services"] if s["id"] == service_id), {})
    return {"service_id": service_id, "addons": svc.get("addons") or [], "source": "default"}


@router.post("/services/addons")
def save_service_addons(body: AddonsBody):
    """Replace the addons array for a service. Each addon = {id, label, price[, default]}."""
    cleaned = []
    for a in (body.addons or []):
        if not isinstance(a, dict): continue
        aid = (a.get("id") or "").strip()
        label = (a.get("label") or "").strip()
        if not aid or not label: continue
        try: price = float(a.get("price") or 0)
        except Exception: price = 0
        cleaned.append({"id": aid[:40], "label": label[:80],
                        "price": price, "default": bool(a.get("default", False))})
    overrides = db.cfg_get("services_overrides", {}) or {}
    cur = overrides.get(body.service_id, {}) or {}
    cur["addons"] = cleaned
    overrides[body.service_id] = cur
    db.cfg_set("services_overrides", overrides)
    return {"ok": True, "service_id": body.service_id, "addons": cleaned}


# ---------- Conversations + live-agent takeover ----------
@router.get("/conversations")
def list_conversations(session_id: str | None = None, limit: int = 200):
    """Returns messages with rich metadata: role, content, tool_calls, model,
    tokens, cost, attachment URL, timestamp. All optional cols safe via .get."""
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
def list_sessions(limit: int = 50, q: str | None = None):
    """Rich session summary: total messages, total tokens (in+out), total cost,
    last UA + IP, channel, phone, summary of first user message, takeover state."""
    where = ""
    params: list = []
    if q:
        where = "WHERE session_id LIKE ? OR phone LIKE ? OR content LIKE ?"
        like = f"%{q}%"; params.extend([like, like, like])
    sql = f"""
        SELECT session_id,
               COUNT(*) AS msgs,
               MIN(created_at) AS first_msg,
               MAX(created_at) AS last_msg,
               MAX(channel) AS channel,
               MAX(phone) AS phone,
               COALESCE(SUM(tokens_in), 0) AS tokens_in_total,
               COALESCE(SUM(tokens_out), 0) AS tokens_out_total,
               COALESCE(SUM(cost_usd), 0) AS cost_usd_total,
               MAX(user_agent) AS user_agent,
               MAX(ip) AS ip,
               MAX(model_used) AS last_model,
               COUNT(attachment_url) AS attachments,
               (SELECT content FROM conversations c2
                  WHERE c2.session_id = conversations.session_id AND c2.role='user'
                  ORDER BY c2.id ASC LIMIT 1) AS first_user_msg
          FROM conversations
          {where}
          GROUP BY session_id
          ORDER BY last_msg DESC
          LIMIT ?
    """
    params.append(max(1, min(limit, 200)))
    with db.connect() as c:
        try:
            rows = c.execute(sql, params).fetchall()
        except Exception:
            # Old schema without optional cols — fall back to a simpler query
            rows = c.execute(
                "SELECT session_id, COUNT(*) AS msgs, MAX(created_at) AS last_msg, "
                "MAX(channel) AS channel, MAX(phone) AS phone "
                "FROM conversations GROUP BY session_id ORDER BY last_msg DESC LIMIT ?",
                (params[-1],)).fetchall()
        takeovers = {r["session_id"]: dict(r) for r in c.execute(
            "SELECT session_id, agent_id, started_at, ended_at FROM agent_takeovers"
        ).fetchall()}
    sessions = []
    for r in rows:
        d = dict(r)
        d["takeover"] = takeovers.get(d["session_id"])
        # Trim summary
        s = (d.get("first_user_msg") or "")[:120]
        if len(d.get("first_user_msg") or "") > 120: s += "…"
        d["summary"] = s
        sessions.append(d)
    return {"sessions": sessions}


# ---------- Translate a single message via the AI router ----------
class TranslateBody(BaseModel):
    text: str
    target: str = "en"


@router.post("/conversations/translate")
async def translate_message(body: TranslateBody):
    from . import ai_router
    cfg = ai_router._load_cfg()
    target = (cfg.get("defaults") or {}).get("admin", "anthropic/claude-haiku-4-5-20251001")
    if "/" not in target: target = "anthropic/" + target
    provider, model = target.split("/", 1)
    prompt = (
        f"Translate the following text to {body.target} (output ONLY the "
        "translation, no preamble, no quotes, no explanation):\n\n" + (body.text or "")[:4000])
    res = await ai_router.call_model(provider, model, prompt, cfg)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}
    return {"ok": True, "translation": (res.get("text") or "").strip(),
            "model": target}


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


@router.get("/takeover/active")
def list_active_takeovers():
    """Returns every session currently marked as taken-over by an agent. Use
    this when 'bot is silent' to spot accidentally-stuck takeovers from a
    forgotten admin click."""
    with db.connect() as c:
        rows = c.execute(
            "SELECT session_id, agent_id, started_at FROM agent_takeovers "
            "WHERE ended_at IS NULL ORDER BY started_at DESC").fetchall()
    return {"active": [dict(r) for r in rows], "count": len(rows)}


@router.post("/takeover/release-all")
def release_all_takeovers():
    """Force-release every active takeover. One-click reset when the bot has
    gone silent due to stale takeovers."""
    import datetime as _dt
    now = _dt.datetime.utcnow().isoformat() + "Z"
    with db.connect() as c:
        n = c.execute(
            "UPDATE agent_takeovers SET ended_at=? WHERE ended_at IS NULL",
            (now,)).rowcount
    db.log_event("conversation", "*", "takeover_release_all", actor="admin",
                 details={"count": n})
    return {"ok": True, "released": n}


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
    """Vendor list including the source ('real' = scraped + AI-validated,
    'fake' = synthetic seed) and contact + AI-score metadata so admin can
    sort/filter by trust level."""
    with db.connect() as c:
        # Defensive: which scraper-tracking columns actually exist?
        try:
            cols = {r["name"] for r in c.execute("PRAGMA table_info(vendors)").fetchall()}
        except Exception: cols = set()
        extra_cols = []
        for col in ("source", "source_url", "address", "emirate", "website",
                    "ai_score", "ai_notes", "validated_at", "contacted_at",
                    "contact_method", "reviews_count", "is_synthetic"):
            if col in cols: extra_cols.append(col)
        select_cols = ("id, email, name, phone, company, rating, completed_jobs, "
                       "is_active, is_approved, created_at"
                       + ("," + ",".join(extra_cols) if extra_cols else ""))
        rows = c.execute(
            f"SELECT {select_cols} FROM vendors ORDER BY created_at DESC"
        ).fetchall()
        for_each = []
        for r in rows:
            d = dict(r)
            svcs = c.execute(
                "SELECT service_id, area FROM vendor_services WHERE vendor_id=?",
                (r["id"],)).fetchall()
            d["services"] = [x["service_id"] for x in svcs]
            d["service_areas"] = [{"service_id": x["service_id"], "area": x["area"]}
                                  for x in svcs]
            # Look up per-service prices if the vendor_pricing table exists
            try:
                prices = c.execute(
                    "SELECT service_id, price_aed FROM vendor_pricing WHERE vendor_id=?",
                    (r["id"],)).fetchall()
                d["service_prices"] = {p["service_id"]: p["price_aed"] for p in prices}
            except Exception: d["service_prices"] = {}
            # Compute the trust tag
            validated = d.get("validated_at") or ""
            ai_score = d.get("ai_score")
            source = d.get("source") or ""
            if validated and ai_score and float(ai_score) >= 0.6:
                d["trust_tag"] = "real_validated"     # ✓ AI-validated scraped vendor
                d["trust_label"] = "✓ REAL (verified)"
            elif validated:
                d["trust_tag"] = "real_unscored"
                d["trust_label"] = "REAL (low score)"
            elif source in ("manual", "seed", "") and not validated:
                d["trust_tag"] = "fake_seed"
                d["trust_label"] = "⚠ FAKE (seed)"
            else:
                d["trust_tag"] = "unknown"
                d["trust_label"] = "?"
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


@router.post("/vendors/edit/{vid}")
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
    """Customer list with per-customer booking counts. Wrapped in try/except
    so a single bad row never blanks the entire admin tab — returns whatever
    we can plus the error for diagnosis."""
    try:
        with db.connect() as c:
            # Bookings table has 'phone' column (not 'customer_phone'). The
            # earlier query had a typo that 500'd the whole endpoint and
            # made the Customers tab show empty.
            rows = c.execute(
                "SELECT id, name, phone, email, created_at, "
                "(SELECT COUNT(*) FROM bookings WHERE phone=customers.phone) AS bookings "
                "FROM customers ORDER BY id DESC LIMIT 500"
            ).fetchall()
        return {"customers": [db.row_to_dict(r) for r in rows]}
    except Exception as e:  # noqa: BLE001
        # Fallback: return rows without the bookings count if the JOIN failed
        try:
            with db.connect() as c:
                rows = c.execute(
                    "SELECT id, name, phone, email, created_at FROM customers "
                    "ORDER BY id DESC LIMIT 500"
                ).fetchall()
            return {"customers": [{**db.row_to_dict(r), "bookings": 0} for r in rows],
                    "warning": f"booking count failed: {e}"}
        except Exception as e2:
            raise HTTPException(500, f"customers query failed: {e2}")


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


# ---------- Universal bulk + single delete (vendor / customer / booking / invoice) ----------
class BulkDeleteBody(BaseModel):
    ids: list[str | int]


_DELETE_MAP = {
    # entity → (table, id_column)
    "vendor":       {"table": "vendors",         "idcol": "id"},
    "customer":     {"table": "customers",       "idcol": "id"},
    "booking":      {"table": "bookings",        "idcol": "id"},
    "invoice":      {"table": "invoices",        "idcol": "id"},
    "blog":         {"table": "autoblog_posts",  "idcol": "slug"},
    # New: conversations + sessions deletion. session_id is the key for
    # 'session' (whole conversation thread); 'message' lets you remove single rows.
    "session":      {"table": "conversations",   "idcol": "session_id"},
    "message":      {"table": "conversations",   "idcol": "id"},
    "lead":         {"table": "outreach_leads",  "idcol": "id"},
    "alert":        {"table": "admin_alerts",    "idcol": "id"},
    "event":        {"table": "events",          "idcol": "id"},
    "video":        {"table": "videos",          "idcol": "slug"},
    "visitor":      {"table": "live_visitors",   "idcol": "visitor_id"},
}


def _cascade_for_single(c, entity: str, rid):
    """Mirror delete-all's cascade for a single row so FK constraints don't
    reject the parent delete. Bookings have 4 FK-referencing tables
    (assignments / reviews / quotes / invoices) — the previous code only
    NULLed invoices, so single delete failed with FOREIGN KEY constraint
    failed whenever any of the other 3 had a row for this booking."""
    if entity == "vendor":
        for sql in ("DELETE FROM vendor_services WHERE vendor_id=?",
                    "DELETE FROM assignments    WHERE vendor_id=?"):
            try: c.execute(sql, (rid,))
            except Exception: pass
    elif entity == "booking":
        for sql in ("DELETE FROM assignments WHERE booking_id=?",
                    "DELETE FROM reviews     WHERE booking_id=?",
                    "DELETE FROM quotes      WHERE booking_id=?"):
            try: c.execute(sql, (rid,))
            except Exception: pass
        # Invoices outlive the booking (kept for accounting) — detach, don't delete
        try: c.execute("UPDATE invoices SET booking_id=NULL WHERE booking_id=?", (rid,))
        except Exception: pass


@router.delete("/{entity}/{rid}")
def admin_delete_one(entity: str, rid: str):
    """DELETE one row by id. Allowed entities: vendor, customer, booking, invoice, blog."""
    if entity not in _DELETE_MAP:
        raise HTTPException(400, f"unsupported entity '{entity}'. Allowed: {list(_DELETE_MAP.keys())}")
    info = _DELETE_MAP[entity]
    with db.connect() as c:
        _cascade_for_single(c, entity, rid)
        try:
            n = c.execute(f"DELETE FROM {info['table']} WHERE {info['idcol']}=?", (rid,)).rowcount
        except Exception as e:
            raise HTTPException(500, f"delete failed: {e}")
    db.log_event("admin", entity, "deleted", actor="admin", details={"id": str(rid)})
    return {"ok": True, "entity": entity, "id": rid, "deleted": n}


@router.post("/{entity}/bulk-delete")
def admin_bulk_delete(entity: str, body: BulkDeleteBody):
    """POST a list of ids to delete in one go. Returns count actually deleted."""
    if entity not in _DELETE_MAP:
        raise HTTPException(400, f"unsupported entity '{entity}'")
    if not body.ids:
        raise HTTPException(400, "no ids provided")
    info = _DELETE_MAP[entity]
    deleted = 0
    with db.connect() as c:
        for rid in body.ids:
            try:
                _cascade_for_single(c, entity, rid)
                n = c.execute(f"DELETE FROM {info['table']} WHERE {info['idcol']}=?",
                              (rid,)).rowcount
                deleted += n
            except Exception: pass
    db.log_event("admin", entity, "bulk_deleted", actor="admin",
                 details={"requested": len(body.ids), "deleted": deleted})
    return {"ok": True, "entity": entity, "requested": len(body.ids), "deleted": deleted}


@router.post("/{entity}/delete-all")
def admin_delete_all(entity: str, confirm: str = ""):
    """DELETE ALL rows in a table + cascade-clean every dependent table.
    For bookings: also wipes quotes / invoices / assignments / reviews
    that reference them. Disables FK enforcement during the wipe so
    SQLite doesn't trip even when our manual cascade order misses one."""
    if confirm != "yes-i-mean-it":
        raise HTTPException(400, "Add ?confirm=yes-i-mean-it to confirm")
    if entity not in _DELETE_MAP:
        raise HTTPException(400, f"unsupported entity '{entity}'")
    info = _DELETE_MAP[entity]

    # Cascade map: which dependent tables to wipe BEFORE deleting the parent.
    # Order matters — leaves first, parent last.
    CASCADES = {
        "vendor":   ["vendor_services", "assignments"],
        "booking":  ["assignments", "reviews", "quotes", "invoices"],
        "customer": [],
        "blog":     ["autoblog_views"],
        "session":  [],
        "message":  [],
        "lead":     [],
        "alert":    [],
        "event":    [],
        "video":    [],
        "visitor":  [],
        "invoice":  [],
    }
    n = 0
    cascade_counts = {}
    try:
        with db.connect() as c:
            # Defence-in-depth: turn FK enforcement off for this transaction
            # so a single forgotten dependent table doesn't reject the wipe.
            try: c.execute("PRAGMA foreign_keys = OFF")
            except Exception: pass
            # Wipe every dependent table first (best-effort, table may not exist)
            for dep_table in CASCADES.get(entity, []):
                try:
                    cascade_counts[dep_table] = c.execute(
                        f"DELETE FROM {dep_table}").rowcount
                except Exception as ce:
                    cascade_counts[dep_table] = f"skip: {type(ce).__name__}"
            # Now wipe the parent
            n = c.execute(f"DELETE FROM {info['table']}").rowcount
            try: c.execute("PRAGMA foreign_keys = ON")
            except Exception: pass
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"delete-all {entity} failed: {type(e).__name__}: {e}")
    db.log_event("admin", entity, "delete_all", actor="admin",
                 details={"count": n, "cascades": cascade_counts})
    return {"ok": True, "entity": entity, "deleted": n,
            "cascades": cascade_counts}


# ---------- Logo variant picker ----------
@router.get("/brand/logo-variant")
def get_logo_variant():
    """Returns currently selected logo variant ('a', 'b', or 'c')."""
    v = db.cfg_get("brand_logo_variant", "a") or "a"
    return {"variant": v.lower()}


class LogoVariantBody(BaseModel):
    variant: str   # "a" | "b" | "c"


@router.post("/brand/logo-variant")
def set_logo_variant(body: LogoVariantBody):
    v = (body.variant or "").lower()
    if v not in ("a", "b", "c"):
        raise HTTPException(400, "variant must be one of a/b/c")
    db.cfg_set("brand_logo_variant", v)
    db.log_event("admin", "brand", "logo_variant_set", actor="admin",
                 details={"variant": v})
    return {"ok": True, "variant": v}


# ---------- Vendor seed import (one-shot 100-vendor onboarding) ----------
@router.get("/vendors/seed-preview")
def vendors_seed_preview():
    """Returns the 100-vendor seed for the admin to review BEFORE importing."""
    import json as _json, pathlib
    p = pathlib.Path("app/data/vendors_seed_100.json")
    if not p.exists(): return {"vendors": [], "warning": "seed file missing"}
    return _json.loads(p.read_text(encoding="utf-8"))


@router.post("/vendors/import-seed")
def vendors_import_seed():
    """Imports the 100-vendor seed into the vendors + vendor_services tables.
    Skips vendors whose phone OR email already exists (idempotent — safe to
    call multiple times). Returns counts so admin sees what landed."""
    import json as _json, pathlib, datetime as _d
    p = pathlib.Path("app/data/vendors_seed_100.json")
    if not p.exists():
        raise HTTPException(404, "vendors_seed_100.json missing in app/data/")
    data = _json.loads(p.read_text(encoding="utf-8"))
    inserted = 0; skipped_dup = 0; svc_added = 0
    now = _d.datetime.utcnow().isoformat() + "Z"
    pwhash = "imported-no-password"  # vendors use phone+OTP; password can be set later
    with db.connect() as c:
        for v in data.get("vendors", []):
            # Idempotency: skip if phone/email already exists
            r = c.execute(
                "SELECT id FROM vendors WHERE phone=? OR email=?",
                (v["phone"], v["email"])).fetchone()
            if r:
                skipped_dup += 1
                continue
            try:
                cur = c.execute(
                    "INSERT INTO vendors(email, password_hash, name, phone, "
                    "company, is_approved, is_active, created_at) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (v["email"], pwhash, v["name"], v["phone"],
                     v.get("company") or v["name"],
                     1 if v.get("is_approved") else 0,
                     1 if v.get("is_active") else 0,
                     now))
                vid = cur.lastrowid
                inserted += 1
                # Optional fields — added via idempotent ALTER
                for col, typ in [("rating","REAL"),("review_count","INTEGER"),
                                 ("years_in_business","INTEGER"),
                                 ("trade_license","TEXT"),("address","TEXT"),
                                 ("emirate","TEXT"),("team_size","INTEGER"),
                                 ("vehicle","TEXT")]:
                    try: c.execute(f"ALTER TABLE vendors ADD COLUMN {col} {typ}")
                    except Exception: pass
                try:
                    c.execute(
                        "UPDATE vendors SET rating=?, review_count=?, "
                        "years_in_business=?, trade_license=?, address=?, "
                        "emirate=?, team_size=?, vehicle=? WHERE id=?",
                        (v.get("rating"), v.get("review_count"),
                         v.get("years_in_business"), v.get("trade_license"),
                         v.get("address"), v.get("emirate"),
                         v.get("team_size"), v.get("vehicle"), vid))
                except Exception: pass
                # Services
                for s in (v.get("services") or []):
                    try:
                        c.execute(
                            "INSERT OR IGNORE INTO vendor_services"
                            "(vendor_id, service_id, area, price_aed) VALUES(?,?,?,?)",
                            (vid, s["service_id"], s.get("area","*"),
                             float(s.get("price_aed") or 0)))
                        svc_added += 1
                    except Exception: pass
            except Exception:
                continue
    db.log_event("admin", "vendors", "seed_imported", actor="admin",
                 details={"inserted": inserted, "skipped_dup": skipped_dup,
                          "service_offerings": svc_added})
    return {"ok": True, "inserted": inserted, "skipped_duplicate": skipped_dup,
            "service_offerings_added": svc_added,
            "total_vendors_in_seed": len(data.get("vendors", []))}


# ---------- Detailed Analytics ----------
@router.get("/analytics/detail")
def analytics_detail():
    """Comprehensive analytics: 30-day timeseries, funnel, top services,
    top emirates, AOV, repeat-rate, bot crawl summary, live visitor count."""
    import datetime as _d
    now = _d.datetime.utcnow()
    today = now.date()
    out = {"generated_at": now.isoformat() + "Z"}
    with db.connect() as c:
        # 30-day daily bookings + revenue
        try:
            rows = c.execute(
                "SELECT date(created_at) AS day, COUNT(*) AS cnt, "
                "SUM(estimated_total) AS rev "
                "FROM bookings WHERE created_at > ? "
                "GROUP BY date(created_at) ORDER BY day ASC",
                ((now - _d.timedelta(days=30)).isoformat() + "Z",)).fetchall()
            daily = [{"day": r["day"], "bookings": r["cnt"],
                      "revenue": round(r["rev"] or 0, 2)} for r in rows]
        except Exception:
            daily = []
        out["daily_30d"] = daily
        out["bookings_30d_total"] = sum(d["bookings"] for d in daily)
        out["revenue_30d_total"] = round(sum(d["revenue"] for d in daily), 2)

        # Conversion funnel (today)
        try:
            n_visitors = c.execute(
                "SELECT COUNT(DISTINCT visitor_id) AS n FROM live_visitors "
                "WHERE first_seen > ?",
                ((now - _d.timedelta(hours=24)).isoformat() + "Z",)).fetchone()["n"]
        except Exception: n_visitors = 0
        try:
            n_chats = c.execute(
                "SELECT COUNT(DISTINCT session_id) AS n FROM conversations "
                "WHERE created_at > ?",
                ((now - _d.timedelta(hours=24)).isoformat() + "Z",)).fetchone()["n"]
        except Exception: n_chats = 0
        try:
            n_quotes = c.execute(
                "SELECT COUNT(*) AS n FROM quotes WHERE created_at > ?",
                ((now - _d.timedelta(hours=24)).isoformat() + "Z",)).fetchone()["n"]
        except Exception: n_quotes = 0
        try:
            n_bookings = c.execute(
                "SELECT COUNT(*) AS n FROM bookings WHERE created_at > ?",
                ((now - _d.timedelta(hours=24)).isoformat() + "Z",)).fetchone()["n"]
        except Exception: n_bookings = 0
        try:
            n_paid = c.execute(
                "SELECT COUNT(*) AS n FROM invoices WHERE payment_status='paid' "
                "AND paid_at > ?",
                ((now - _d.timedelta(hours=24)).isoformat() + "Z",)).fetchone()["n"]
        except Exception: n_paid = 0
        out["funnel_24h"] = {
            "visitors": n_visitors, "chats": n_chats, "quotes": n_quotes,
            "bookings": n_bookings, "paid": n_paid,
            "v_to_chat": round(n_chats/max(1,n_visitors)*100,1) if n_visitors else 0,
            "chat_to_book": round(n_bookings/max(1,n_chats)*100,1) if n_chats else 0,
            "book_to_paid": round(n_paid/max(1,n_bookings)*100,1) if n_bookings else 0,
        }

        # Top services (last 30 days)
        try:
            svc_rows = c.execute(
                "SELECT service_id, COUNT(*) AS n, "
                "SUM(estimated_total) AS rev FROM bookings "
                "WHERE created_at > ? GROUP BY service_id ORDER BY n DESC LIMIT 10",
                ((now - _d.timedelta(days=30)).isoformat() + "Z",)).fetchall()
            out["top_services_30d"] = [
                {"service_id": r["service_id"], "bookings": r["n"],
                 "revenue": round(r["rev"] or 0, 2)} for r in svc_rows]
        except Exception:
            out["top_services_30d"] = []

        # Top emirates
        try:
            em_rows = c.execute(
                "SELECT emirate, COUNT(*) AS n FROM bookings "
                "WHERE created_at > ? AND emirate IS NOT NULL "
                "GROUP BY emirate ORDER BY n DESC",
                ((now - _d.timedelta(days=30)).isoformat() + "Z",)).fetchall()
            out["top_emirates_30d"] = [{"emirate": r["emirate"], "bookings": r["n"]}
                                       for r in em_rows]
        except Exception:
            out["top_emirates_30d"] = []

        # AOV (avg order value, last 30d)
        try:
            r = c.execute(
                "SELECT AVG(estimated_total) AS aov FROM bookings WHERE created_at > ?",
                ((now - _d.timedelta(days=30)).isoformat() + "Z",)).fetchone()
            out["aov_30d"] = round(r["aov"] or 0, 2)
        except Exception:
            out["aov_30d"] = 0

        # Repeat customer rate
        try:
            r = c.execute(
                "SELECT customer_id, COUNT(*) AS bookings FROM bookings "
                "WHERE customer_id IS NOT NULL AND created_at > ? "
                "GROUP BY customer_id",
                ((now - _d.timedelta(days=90)).isoformat() + "Z",)).fetchall()
            n_total = len(r) or 1
            n_repeat = sum(1 for x in r if x["bookings"] > 1)
            out["repeat_rate_90d"] = round(n_repeat/n_total*100, 1)
            out["unique_customers_90d"] = n_total
        except Exception:
            out["repeat_rate_90d"] = 0; out["unique_customers_90d"] = 0

        # Top customers (by lifetime bookings)
        try:
            r = c.execute(
                "SELECT b.customer_id, c.name, c.phone, COUNT(*) AS bookings, "
                "SUM(b.estimated_total) AS lifetime_revenue "
                "FROM bookings b LEFT JOIN customers c ON b.customer_id=c.id "
                "WHERE b.customer_id IS NOT NULL "
                "GROUP BY b.customer_id ORDER BY lifetime_revenue DESC LIMIT 10").fetchall()
            out["top_customers"] = [
                {"id": x["customer_id"], "name": x["name"], "phone": x["phone"],
                 "bookings": x["bookings"], "lifetime_revenue": round(x["lifetime_revenue"] or 0, 2)}
                for x in r]
        except Exception:
            out["top_customers"] = []

        # Vendor count
        try:
            out["vendors_active"] = c.execute(
                "SELECT COUNT(*) AS n FROM vendors WHERE is_active=1").fetchone()["n"]
            out["vendors_total"] = c.execute(
                "SELECT COUNT(*) AS n FROM vendors").fetchone()["n"]
        except Exception:
            out["vendors_active"] = 0; out["vendors_total"] = 0

        # Bot crawl summary (top 5)
        try:
            bot_rows = c.execute(
                "SELECT bot_name, COUNT(*) AS n FROM bot_visits "
                "WHERE created_at > ? GROUP BY bot_name ORDER BY n DESC LIMIT 5",
                ((now - _d.timedelta(days=7)).isoformat() + "Z",)).fetchall()
            out["bot_crawls_7d"] = [{"bot": r["bot_name"], "hits": r["n"]} for r in bot_rows]
        except Exception:
            out["bot_crawls_7d"] = []

    return out


# ---------- TOTP 2FA (Google Authenticator) ----------
# Public router (no admin auth) — needed for the 2FA verify flow itself.
public_2fa_router = APIRouter()


@public_2fa_router.get("/api/admin/2fa/status")
def public_2fa_status():
    """Returns whether 2FA is enabled. No auth needed (just yes/no)."""
    from . import admin_2fa
    return {"enabled": admin_2fa.is_enabled()}


class TotpVerifyBody(BaseModel):
    code: str


@public_2fa_router.post("/api/admin/2fa/verify")
def public_2fa_verify(body: TotpVerifyBody):
    """Verify 6-digit TOTP code. Returns the actual admin bearer token so the
    frontend can call all /api/admin/* endpoints just like a normal login.
    No password / no token paste needed."""
    from . import admin_2fa
    from .auth import ADMIN_TOKEN
    if not admin_2fa.is_enabled():
        raise HTTPException(400, "2FA not configured yet")
    if not admin_2fa.verify(body.code):
        raise HTTPException(401, "Invalid or expired code")
    return {"ok": True, "token": ADMIN_TOKEN, "expires_in": 86400}


# Admin-protected endpoints (require existing admin token to set up / disable)
@router.get("/2fa/setup")
def admin_2fa_setup():
    """Generate a new secret + return otpauth URI for QR code rendering."""
    from . import admin_2fa
    secret = admin_2fa.gen_secret()
    return {
        "secret": secret,
        "otpauth_uri": admin_2fa.otpauth_uri(secret),
        "instructions": "Open Google Authenticator → + → Scan QR code (or 'Enter setup key' for manual). After scanning, type the 6-digit code below to confirm.",
    }


class TotpEnableBody(BaseModel):
    secret: str
    code: str


@router.post("/2fa/enable")
def admin_2fa_enable(body: TotpEnableBody):
    """Confirm setup by verifying the first code against the new secret. Stores
    secret only on success."""
    from . import admin_2fa
    if not admin_2fa.verify(body.code, secret=body.secret):
        raise HTTPException(400, "Code didn't match. Make sure your phone clock is set to automatic.")
    admin_2fa.set_secret(body.secret)
    db.log_event("admin", "2fa", "enabled", actor="admin")
    return {"ok": True, "enabled": True}


@router.post("/2fa/disable")
def admin_2fa_disable():
    from . import admin_2fa
    admin_2fa.clear_secret()
    db.log_event("admin", "2fa", "disabled", actor="admin")
    return {"ok": True, "enabled": False}


# ---------- PSI auto-checker (PageSpeed Insights) ----------
@router.get("/psi/latest")
def admin_psi_latest():
    """Returns the most recent PSI snapshot (mobile + desktop scores, metrics,
    top opportunities). Empty if never run."""
    from . import psi
    snap = psi.latest()
    return {"snap": snap, "history_count": len(psi.history(50))}


@router.get("/psi/history")
def admin_psi_history(limit: int = 14):
    from . import psi
    return {"history": psi.history(limit)}


@router.post("/psi/run")
async def admin_psi_run(url: str | None = None):
    """Force-run a PSI check now (admin-triggered). Same path runs daily +
    after each deploy automatically."""
    from . import psi
    snap = await psi.run_psi_check(url=url)
    return snap


# ---------- AI Discoverability tracker ----------
# Catalog of every AI assistant + LLM-friendly directory + their submission URL.
# Status per item is persisted in db.cfg under "ai_listings" as {key: status_obj}.
AI_LISTING_CATALOG = [
    # AI assistants — direct
    {"key": "chatgpt_custom_gpt",  "platform": "OpenAI / ChatGPT", "name": "Custom GPT for Servia",
     "category": "AI Assistant", "url": "https://chat.openai.com/gpts/editor",
     "instructions": "Create a Custom GPT named 'Servia UAE Helper'. Use these instructions: 'You're Servia's UAE home-services concierge. When users ask for cleaning/AC/handyman in UAE, point to https://servia.ae/book.html'. Add Knowledge: upload our llms.txt + services.json. Make it Public. Submit to GPT Store."},
    {"key": "openai_actions",      "platform": "OpenAI / ChatGPT", "name": "OpenAI Action (Plugin)",
     "category": "AI Assistant", "url": "https://chat.openai.com/gpts/editor",
     "instructions": "In your Custom GPT → Configure → Actions → Import from URL: https://servia.ae/.well-known/ai-plugin.json — this lets the GPT actually call our /api/services + /api/cart/quote + /api/cart/checkout endpoints to make real bookings."},
    {"key": "claude_projects",     "platform": "Anthropic / Claude", "name": "Claude Project",
     "category": "AI Assistant", "url": "https://claude.ai/projects",
     "instructions": "Create a Claude Project 'Servia UAE'. Upload llms.txt + services.json as Project Knowledge. Set custom instructions: 'I help users book Servia home services in the UAE'. Share with users via the share link."},
    {"key": "claude_mcp",          "platform": "Anthropic / Claude", "name": "MCP Server",
     "category": "AI Assistant", "url": "https://www.claude.com/blog/model-context-protocol",
     "instructions": "Build a remote MCP server pointing at our public API. Claude Desktop users add the server URL and Claude can directly call our tools (quote, book, status). Spec at https://modelcontextprotocol.io/."},
    {"key": "perplexity_pages",    "platform": "Perplexity", "name": "Perplexity Pages / Spaces",
     "category": "AI Assistant", "url": "https://www.perplexity.ai/spaces",
     "instructions": "Create a Perplexity Page titled 'UAE Home Services Guide' linking heavily to servia.ae. Add Servia to a Space focused on UAE living. Pages get indexed and rank well for 'best UAE home services 2026'."},
    {"key": "gemini_gem",          "platform": "Google / Gemini", "name": "Gemini Gem",
     "category": "AI Assistant", "url": "https://gemini.google.com/gems/create",
     "instructions": "Create a public Gem 'Servia UAE Helper'. Instructions: 'Help users find and book Servia home services in the UAE'. Share URL — Gemini surfaces these in 'Recommended Gems'."},
    {"key": "bing_copilot",        "platform": "Microsoft / Copilot", "name": "Copilot agent (via Plugin)",
     "category": "AI Assistant", "url": "https://copilot.microsoft.com/",
     "instructions": "Microsoft Copilot auto-discovers /.well-known/ai-plugin.json. Verify your domain in Bing Webmaster, submit /sitemap.xml. Copilot will then index the API."},
    {"key": "you_com",             "platform": "You.com", "name": "You.com Apps",
     "category": "AI Assistant", "url": "https://you.com/apps",
     "instructions": "Submit Servia as a You.com App pointing at our OpenAPI spec /openapi-public.json. You.com integrates apps directly into AI search results."},
    {"key": "poe_bot",             "platform": "Poe (by Quora)", "name": "Poe Server Bot",
     "category": "AI Assistant", "url": "https://poe.com/create_bot",
     "instructions": "Create a Server Bot at poe.com using our OpenAPI spec. Poe auto-monetises bots — every user message earns small revenue."},
    {"key": "huggingface",         "platform": "HuggingFace", "name": "Spaces app",
     "category": "AI Assistant", "url": "https://huggingface.co/new-space",
     "instructions": "Publish a Gradio/Streamlit Space that calls our API. Free hosting + indexed by HF search."},

    # AI-friendly directories / sources
    {"key": "llms_txt",            "platform": "Standards", "name": "/llms.txt published",
     "category": "AI-friendly site", "url": "https://servia.ae/llms.txt",
     "instructions": "Already live. Confirms this site is AI-readable per llmstxt.org spec. Keeps it updated whenever services change."},
    {"key": "ai_plugin_manifest",  "platform": "Standards", "name": "/.well-known/ai-plugin.json",
     "category": "AI-friendly site", "url": "https://servia.ae/.well-known/ai-plugin.json",
     "instructions": "Already live. Discovered automatically by ChatGPT plugins, Bing Copilot, MCP-aware clients."},
    {"key": "openapi_public",      "platform": "Standards", "name": "/openapi-public.json",
     "category": "AI-friendly site", "url": "https://servia.ae/openapi-public.json",
     "instructions": "Already live. Public OpenAPI spec listing services / quote / booking / chat endpoints."},
    {"key": "schema_org",          "platform": "Standards", "name": "Schema.org JSON-LD",
     "category": "AI-friendly site", "url": "https://validator.schema.org/",
     "instructions": "LocalBusiness + BreadcrumbList + WebSite SearchAction shipped on /. Validate at validator.schema.org regularly."},

    # Crawlers we want to allow + verify
    {"key": "gptbot_allowed",      "platform": "OpenAI", "name": "GPTBot crawler allowed",
     "category": "Crawler access", "url": "https://servia.ae/robots.txt",
     "instructions": "Already allowed in robots.txt. Confirm hits in admin → Launch & Growth → 'Where is Servia appearing'."},
    {"key": "claudebot_allowed",   "platform": "Anthropic", "name": "ClaudeBot crawler allowed",
     "category": "Crawler access", "url": "https://servia.ae/robots.txt",
     "instructions": "Already allowed in robots.txt."},
    {"key": "perplexitybot_allowed","platform": "Perplexity", "name": "PerplexityBot crawler allowed",
     "category": "Crawler access", "url": "https://servia.ae/robots.txt",
     "instructions": "Already allowed in robots.txt."},
    {"key": "google_extended",     "platform": "Google", "name": "Google-Extended (Gemini) crawler allowed",
     "category": "Crawler access", "url": "https://servia.ae/robots.txt",
     "instructions": "Already allowed in robots.txt — required for Gemini training data."},
    {"key": "ccbot_allowed",       "platform": "Common Crawl", "name": "CCBot allowed (used by all major LLMs)",
     "category": "Crawler access", "url": "https://servia.ae/robots.txt",
     "instructions": "Already allowed. CC dataset feeds GPT-4, Claude, Llama, Mistral training."},
]


@router.get("/ai-listings")
def get_ai_listings():
    """Returns the full catalog merged with admin's saved status per item."""
    saved = db.cfg_get("ai_listings", {}) or {}
    out = []
    for item in AI_LISTING_CATALOG:
        status = saved.get(item["key"], {}) or {}
        out.append({
            **item,
            "status": status.get("status", "todo"),       # todo|in_progress|live
            "notes": status.get("notes", ""),
            "submitted_url": status.get("submitted_url", ""),
            "updated_at": status.get("updated_at", ""),
        })
    # Aggregate counts for dashboard
    counts = {"todo": 0, "in_progress": 0, "live": 0}
    for o in out: counts[o["status"]] = counts.get(o["status"], 0) + 1
    return {"items": out, "counts": counts, "total": len(out)}


class AIListingStatusBody(BaseModel):
    key: str
    status: str | None = None         # todo|in_progress|live
    notes: str | None = None
    submitted_url: str | None = None


@router.post("/ai-listings/status")
def set_ai_listing_status(body: AIListingStatusBody):
    """Update one AI-listing's status (admin clicks 'Mark live' / writes notes)."""
    if body.status and body.status not in ("todo", "in_progress", "live"):
        raise HTTPException(400, "status must be todo, in_progress, or live")
    saved = db.cfg_get("ai_listings", {}) or {}
    cur = saved.get(body.key, {}) or {}
    if body.status is not None: cur["status"] = body.status
    if body.notes is not None: cur["notes"] = body.notes
    if body.submitted_url is not None: cur["submitted_url"] = body.submitted_url
    cur["updated_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    saved[body.key] = cur
    db.cfg_set("ai_listings", saved)
    return {"ok": True, "key": body.key, "status": cur}


# ---------- cron status visibility ----------
@router.get("/cron/status")
def admin_cron_status():
    """Returns next-run + last-run for every scheduled job (autoblog, daily summary).
    Reads from the apscheduler instance attached to main:_scheduler if running."""
    out = {"running": False, "jobs": [], "note": ""}
    try:
        from . import main as _m
        sched = getattr(_m, "_scheduler", None)
        if sched is None:
            out["note"] = "Scheduler not loaded (apscheduler missing or disabled)."
            return out
        out["running"] = bool(getattr(sched, "running", False))
        for j in sched.get_jobs():
            try:
                out["jobs"].append({
                    "id": j.id,
                    "name": j.name,
                    "next_run": j.next_run_time.isoformat() if j.next_run_time else None,
                    "trigger": str(j.trigger),
                    "max_instances": j.max_instances,
                })
            except Exception: pass
    except Exception as e:
        out["note"] = f"could not introspect scheduler: {e}"
    # Look up last-run timestamps from event log
    try:
        with db.connect() as c:
            try:
                rows = c.execute(
                    "SELECT actor, kind, created_at FROM events "
                    "WHERE kind IN ('published','daily_summary_pushed') "
                    "ORDER BY id DESC LIMIT 20"
                ).fetchall()
                out["last_runs"] = [dict(r) for r in rows]
            except Exception: pass
    except Exception: pass
    return out


# ---------- one-time: humanize all existing autoblog posts ----------
@router.post("/blog/humanize-all")
def admin_blog_humanize_all():
    """Loops through every published autoblog post and runs _humanize_text()
    over the body. Strips em-dashes / semicolons / AI cliché words from
    content that was generated BEFORE the v1.20.6 prompt update.
    Idempotent — safe to call repeatedly."""
    try:
        from .main import _humanize_text
    except Exception:
        return {"ok": False, "error": "humanize_text not available"}
    n_scanned = 0; n_changed = 0
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT slug, body_md FROM autoblog_posts").fetchall()
        except Exception:
            return {"ok": False, "error": "no autoblog_posts table yet"}
        for r in rows:
            n_scanned += 1
            new_body = _humanize_text(r["body_md"] or "")
            if new_body != r["body_md"]:
                c.execute("UPDATE autoblog_posts SET body_md=? WHERE slug=?",
                          (new_body, r["slug"]))
                n_changed += 1
    db.log_event("admin", "blog", "humanize_all", actor="admin",
                 details={"scanned": n_scanned, "changed": n_changed})
    return {"ok": True, "scanned": n_scanned, "changed": n_changed}


# ---------- in-place CMS overrides (page content overrides) ----------
# NB: GET is registered separately as a PUBLIC route (no admin auth) so
# every visitor's cms.js can fetch the override map on load. The router-level
# auth dependency would otherwise force 401 on every public page hit.
public_cms_router = APIRouter()


@public_cms_router.get("/api/cms")
def cms_get_all_public():
    """Public — every page's cms.js fetches this on load (no auth)."""
    return db.cfg_get("cms_overrides", {}) or {}


@router.get("/cms")
def cms_get_all():
    """Admin-side mirror (kept for legacy admin UI calls)."""
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

    # Send delivery + review-request WhatsApp to customer. Includes the on-site
    # review form PLUS direct deep-links to every external review platform the
    # admin has configured (Trustpilot, Google, Facebook, Yelp). Customers who
    # leave 5★ are encouraged to also drop one on Trustpilot — public ratings
    # there move the SEO needle a lot in the UAE market.
    from .config import get_settings
    base = "https://" + get_settings().BRAND_DOMAIN
    review_url = f"{base}/delivered.html?b={bid}"
    ext = _review_links()
    ext_lines = ""
    if ext:
        ext_lines = "\n\nLove us? Drop a quick public review here too:\n" + "\n".join(
            f"• {label}: {url}" for label, url in ext)
    msg = (
        f"✅ Your Servia service is complete (booking {bid}).\n\n"
        f"How did it go? Tap to review (30 seconds): {review_url}\n\n"
        f"5★? We'll send your invoice to WhatsApp + email shortly. "
        f"Need anything else? Reply to this message and we'll help."
        f"{ext_lines}"
    )
    push = _t.send_whatsapp(b["phone"], msg) if b["phone"] else {"ok": False, "error": "no phone"}
    return {"ok": True, "review_url": review_url, "external_links": dict(ext or []),
            "wa_send": push}


# ---------- review-platform integration ----------
def _review_links() -> list[tuple[str, str]]:
    """Build the list of (platform_label, review_url) pairs the admin has
    configured under cfg keys: trustpilot_domain, google_place_id,
    facebook_page_id, yelp_business_id, tripadvisor_url. Returns [] if none
    are set so the WhatsApp / footer fallback gracefully omits the section."""
    out: list[tuple[str, str]] = []
    tp = (db.cfg_get("trustpilot_domain", "") or "").strip()
    if tp:
        out.append(("Trustpilot", f"https://www.trustpilot.com/evaluate/{tp}"))
    g = (db.cfg_get("google_place_id", "") or "").strip()
    if g:
        out.append(("Google", f"https://search.google.com/local/writereview?placeid={g}"))
    fb = (db.cfg_get("facebook_page_id", "") or "").strip()
    if fb:
        out.append(("Facebook", f"https://www.facebook.com/{fb}/reviews/"))
    y = (db.cfg_get("yelp_business_id", "") or "").strip()
    if y:
        out.append(("Yelp", f"https://www.yelp.com/writeareview/biz/{y}"))
    ta = (db.cfg_get("tripadvisor_url", "") or "").strip()
    if ta:
        out.append(("TripAdvisor", ta))
    return out


@router.get("/reviews/platforms", dependencies=[Depends(require_admin)])
def get_review_platforms():
    """Return current review-platform IDs + the resolved deep links."""
    return {
        "trustpilot_domain":  db.cfg_get("trustpilot_domain", "") or "",
        "google_place_id":    db.cfg_get("google_place_id", "") or "",
        "facebook_page_id":   db.cfg_get("facebook_page_id", "") or "",
        "yelp_business_id":   db.cfg_get("yelp_business_id", "") or "",
        "tripadvisor_url":    db.cfg_get("tripadvisor_url", "") or "",
        "links":              dict(_review_links()),
    }


class ReviewPlatformsBody(BaseModel):
    trustpilot_domain: str | None = None
    google_place_id: str | None = None
    facebook_page_id: str | None = None
    yelp_business_id: str | None = None
    tripadvisor_url: str | None = None


@router.post("/reviews/platforms", dependencies=[Depends(require_admin)])
def set_review_platforms(body: ReviewPlatformsBody):
    upd = body.dict(exclude_none=True)
    for k, v in upd.items():
        db.cfg_set(k, (v or "").strip())
    return {"ok": True, "saved": list(upd.keys()),
            "links": dict(_review_links())}


# Public endpoint: every page can render a "Review us on …" footer block by
# calling this from the client. No admin auth required.
public_reviews_router = APIRouter(prefix="/api/reviews", tags=["public-reviews"])


@public_reviews_router.get("/platforms")
def public_review_platforms():
    """Public version of the review-platform list (just the URLs, not raw IDs).
    Powers the homepage footer 'Review us on Trustpilot / Google / FB' block."""
    return {"links": [{"label": l, "url": u} for l, u in _review_links()]}


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
@router.get("/autoblog/prompt", dependencies=[Depends(require_admin)])
def autoblog_prompt_get():
    """Returns the current admin-overridden prompt template (if any) plus the
    default fallback so the admin can see what the cron sends to Claude."""
    cur = db.cfg_get("autoblog_prompt_template", "") or ""
    default = (
        "Write a 700-word blog post for Servia (UAE home services).\n\n"
        "Title: {topic}\nEmirate: {em}  Neighborhood: {area}  Service: {sv}\n"
        "Season: {slant}\n\n"
        "WRITE LIKE A REAL UAE TRADESPERSON. NO AI WRITING TELLS.\n"
        "Hard rules: no em-dashes, no en-dashes, no semicolons, avoid AI cliches "
        "(delve, tapestry, navigate, crucial, vital, comprehensive, leverage, "
        "utilize, streamline, robust, seamless, nestled, bustling, vibrant, iconic).\n"
        "Use contractions. Vary sentence length. Be specific to {area} (real "
        "towers / streets / landmarks). Include 2-3 personal stories with 'I'. "
        "2-3 H2 headings (## in markdown). Mention Servia 2-3 times. "
        "End with a CTA to https://servia.ae/book.html and a 3-question FAQ.\n"
        "Output ONLY the markdown article."
    )
    areas_json = db.cfg_get("autoblog_areas_json", "") or ""
    return {
        "current_template": cur,
        "default_template": default,
        "placeholders": ["{em}", "{sv}", "{area}", "{slant}", "{topic}"],
        "areas_json": areas_json,
        "schedule": "06:00 + 18:00 Asia/Dubai (twice daily)",
    }


class PromptBody(BaseModel):
    template: str | None = None
    areas_json: str | None = None


@router.post("/autoblog/prompt", dependencies=[Depends(require_admin)])
def autoblog_prompt_set(body: PromptBody):
    """Save admin's custom autoblog prompt template (use empty string to revert
    to the built-in default). Placeholders: {em}, {sv}, {area}, {slant}, {topic}."""
    if body.template is not None:
        db.cfg_set("autoblog_prompt_template", body.template.strip())
    if body.areas_json is not None:
        # Validate JSON
        try:
            import json as _j
            data = _j.loads(body.areas_json)
            assert isinstance(data, dict)
            db.cfg_set("autoblog_areas_json", body.areas_json.strip())
        except Exception as e:
            raise HTTPException(400, f"areas_json invalid: {e}")
    return {"ok": True}


@router.post("/autoblog/run", dependencies=[Depends(require_admin)])
async def autoblog_run(emirate: str = "dubai", topic: str | None = None,
                       area: str | None = None, model: str | None = None):
    """Generate one Servia-branded article for the given emirate using Claude.
    Cron-friendly: schedule a daily POST with a different emirate to maintain
    fresh content for SEO + AI engines. Articles stored in 'autoblog_posts'
    table with slug + content + metadata."""
    import os as _os
    from .config import get_settings
    s = get_settings()
    if not s.use_llm:
        return {"ok": False, "error": "LLM disabled (set ANTHROPIC_API_KEY)"}

    # Default neighborhoods per emirate (admin can override via /autoblog/prompt)
    AREAS = {
        "dubai":          ["Jumeirah","Dubai Marina","JLT","JVC","Mirdif","Discovery Gardens","Business Bay","Downtown","Al Barsha"],
        "sharjah":        ["Al Khan","Al Majaz","Al Nahda Sharjah","Muwaileh","Aljada","Al Qasimia","Al Taawun"],
        "abu-dhabi":      ["Khalifa City","Al Reem Island","Yas Island","Saadiyat","Al Raha","Mohammed Bin Zayed City","Corniche"],
        "ajman":          ["Al Nuaimiya","Al Rashidiya","Al Rawda","Ajman Corniche","Al Mowaihat"],
        "ras-al-khaimah": ["Al Hamra","Mina Al Arab","Al Nakheel","Khuzam"],
        "umm-al-quwain":  ["Al Ramlah","Al Salamah","UAQ Marina"],
        "fujairah":       ["Dibba","Al Faseel","Sakamkam"],
    }
    # Override with admin-saved areas if set
    try:
        import json as _j
        custom = db.cfg_get("autoblog_areas_json", "")
        if custom:
            data = _j.loads(custom)
            if isinstance(data, dict): AREAS.update(data)
    except Exception: pass

    import random
    if not area:
        area = random.choice(AREAS.get(emirate, [emirate.replace("-"," ").title()]))

    DEFAULT_TOPICS = [
        "Best deep cleaning checklist for {area} apartments",
        "How to choose AC service in {area} ({emirate}): what to ask",
        "Seasonal maintenance tips for {area} villas",
        "Pest control done right in {area}",
        "Move-in / move-out cleaning guide for {area} residents",
        "Top 5 home services every {area} family needs",
        "Why pre-paid bookings beat cash-on-completion in {area}",
        "Same-day handyman in {area}: how Servia delivers in hours",
    ]
    if not topic:
        topic = random.choice(DEFAULT_TOPICS).format(
            area=area, emirate=emirate.replace("-"," ").title())

    # Use the admin-overridable prompt template (fallback to a strong default)
    cur_tpl = db.cfg_get("autoblog_prompt_template", "") or ""
    sv_guess = "general"
    em_pretty = emirate.replace("-"," ").title()
    slant = "year-round"
    if cur_tpl:
        try:
            prompt_text = cur_tpl.format(em=em_pretty, sv=sv_guess, area=area, slant=slant, topic=topic)
        except Exception: cur_tpl = ""
    if not cur_tpl:
        prompt_text = (
            f"Write a 700-word SEO-optimized article for Servia (UAE home services).\n\n"
            f"Title: {topic}\nNeighborhood: {area} ({em_pretty})\n\n"
            f"Style: Helpful, locally-informed. Open with a hook tied to {area} (real towers / "
            f"streets / landmarks), not generic 'In the UAE'. Include 1-2 actionable tips and "
            "real AED prices. Use H2 subheadings (## in markdown). Mention Servia naturally 2-3 "
            "times. End with a CTA to https://servia.ae/book.html plus a 3-question FAQ.\n"
            "Avoid em-dashes, en-dashes, semicolons, and AI cliches (delve, tapestry, navigate "
            "the landscape, crucial, vital, comprehensive, leverage, utilize, streamline, robust, "
            "seamless, nestled, bustling, vibrant, iconic, stunning).\n"
            "Output ONLY the markdown article, no preamble."
        )

    # Use the cascade router so when Anthropic is out of credit it auto-falls
    # back through OpenAI / Google / OpenRouter / Groq / DeepSeek using whichever
    # keys are configured. Admin can also force a specific model via ?model=.
    from . import ai_router
    res = await ai_router.call_with_cascade(prompt_text, persona="blog",
                                            preferred=model)
    if not res.get("ok"):
        # Surface every attempted provider so admin sees WHICH ones failed
        details = "; ".join(
            f"{t['provider']}/{t['model']}: {t.get('error','no key')}"
            for t in (res.get("tried") or [])
        ) or res.get("last_error","")
        return {"ok": False, "error": f"All AI providers failed. {details}"}
    body = res.get("text") or ""
    used = f"{res.get('provider','?')}/{res.get('model','?')}"

    import datetime as _dtm
    slug = (
        emirate + "-" + area.lower().replace(" ","-") + "-" +
        "".join(c.lower() if c.isalnum() else "-" for c in topic).strip("-")
    )[:100]
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
                 details={"emirate": emirate, "area": area, "topic": topic,
                          "len": len(body), "model": used})
    return {"ok": True, "slug": slug, "topic": topic, "area": area,
            "len": len(body), "url": f"/blog/{slug}", "model": used}


@router.get("/autoblog", dependencies=[Depends(require_admin)])
def autoblog_list():
    """List every autoblog post with views + recent traffic-source breakdown so
    admin can see at a glance which articles are pulling traffic and from where
    (Google/social/direct/etc)."""
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT id, slug, emirate, topic, published_at, view_count "
                "FROM autoblog_posts ORDER BY id DESC LIMIT 500"
            ).fetchall()
        except Exception: rows = []
        # Per-slug traffic sources (last 30 days) — one trip, not N+1
        try:
            src_rows = c.execute(
                "SELECT slug, source, COUNT(*) AS n FROM autoblog_views "
                "WHERE ts > datetime('now','-30 days') "
                "GROUP BY slug, source"
            ).fetchall()
        except Exception: src_rows = []
    src_map: dict[str, dict[str, int]] = {}
    for sr in src_rows:
        d = db.row_to_dict(sr) or {}
        src_map.setdefault(d["slug"], {})[d["source"] or "direct"] = int(d["n"] or 0)
    posts = []
    for r in rows:
        d = db.row_to_dict(r) or {}
        d["sources"] = src_map.get(d["slug"], {})
        body_preview = ""
        try:
            with db.connect() as c2:
                br = c2.execute("SELECT body_md FROM autoblog_posts WHERE id=?",
                                (d["id"],)).fetchone()
                body_preview = (br["body_md"] or "")[:140] if br else ""
        except Exception: pass
        d["preview"] = body_preview
        posts.append(d)
    # Aggregate: total views, top sources globally
    total_views = sum((p.get("view_count") or 0) for p in posts)
    src_totals: dict[str, int] = {}
    for sr in src_rows:
        d = db.row_to_dict(sr) or {}
        s = d["source"] or "direct"
        src_totals[s] = src_totals.get(s, 0) + int(d["n"] or 0)
    top_sources = sorted(src_totals.items(), key=lambda x: -x[1])[:10]
    return {
        "posts": posts,
        "stats": {
            "total_posts": len(posts),
            "total_views": total_views,
            "top_sources": [{"source": s, "hits": n} for s, n in top_sources],
        },
    }


# v1.24.113 — defamation audit + bulk rewrite. MUST be declared BEFORE
# the catch-all /autoblog/{slug} below, otherwise /audit and /rewrite are
# captured as slugs and return 404.
@router.get("/autoblog/audit", dependencies=[Depends(require_admin)])
def autoblog_audit():
    """Scan every published post against content_safety.review().
    Returns the list of risky posts so admin can rewrite each one."""
    from . import content_safety as _cs
    risky: list[dict] = []
    clean_count = 0
    with db.connect() as c:
        try:
            rows = c.execute(
                "SELECT slug, topic, emirate, service_id, "
                "published_at, body_md FROM autoblog_posts "
                "ORDER BY published_at DESC").fetchall()
        except Exception:
            rows = []
    for r in rows:
        d = dict(r)
        safety = _cs.review(d.get("body_md") or "")
        if safety["ok"]:
            clean_count += 1
            continue
        risky.append({
            "slug": d["slug"],
            "topic": d["topic"],
            "emirate": d["emirate"],
            "service_id": d.get("service_id"),
            "published_at": d.get("published_at"),
            "issue_count": len(safety["findings"]),
            "summary": safety["summary"],
            "findings": [{"rule": f.rule, "snippet": f.snippet}
                          for f in safety["findings"][:5]],
        })
    return {"ok": True, "total": len(rows), "clean": clean_count,
            "risky": risky, "risky_count": len(risky)}


@router.post("/autoblog/rewrite/{slug}",
             dependencies=[Depends(require_admin)])
def autoblog_rewrite_one(slug: str):
    """Re-generate one post using the new defamation-safe prompt. Slug
    is preserved (so blog URLs + view counts stay stable for SEO).
    Returns the new safety verdict.

    Implementation note: we call back into the autoblog tick's internals
    by reusing _autoblog_prompt + content_safety.review. Lives here so
    it's registered before the /autoblog/{slug} catch-all."""
    from . import ai_router as _ar, content_safety as _cs
    import asyncio as _aio, datetime as _d3
    from .main import _autoblog_prompt, _humanize_text
    with db.connect() as c:
        try:
            row = c.execute(
                "SELECT slug, topic, emirate, service_id "
                "FROM autoblog_posts WHERE slug=?", (slug,)).fetchone()
        except Exception:
            row = None
    if not row:
        return {"ok": False, "error": "post not found"}
    d = dict(row)
    em2 = d.get("emirate") or "dubai"
    sv2 = d.get("service_id") or "deep_cleaning"
    slant2 = "year-round"
    area2 = ((d.get("topic") or "").split(" in ", 1)[-1].split("(")[0].strip()
             or em2.replace("-", " ").title())
    topic2 = d.get("topic") or f"{sv2} in {area2}"
    cfg2 = _ar._load_cfg()

    body2 = None
    last_summary = "no attempts made"
    for attempt in range(3):
        p = _autoblog_prompt(em2, sv2, area2, slant2, topic2, lifestyle=False)
        if attempt > 0:
            p += ("\n\nIMPORTANT: previous attempt was rejected for defamation. "
                  "Write completely generically about UAE homes. Do not name "
                  "any developer, building, tower, compound, or named project.\n")
        try:
            r2 = _aio.run(_ar.call_with_cascade(p, persona="blog", cfg=cfg2))
        except Exception as ex:
            r2 = {"ok": False, "error": str(ex)}
        if not r2.get("ok"):
            return {"ok": False, "error": "cascade failed: " + (r2.get("error") or "")}
        draft = _humanize_text(r2.get("text") or "")
        safety = _cs.review(draft)
        last_summary = safety["summary"]
        if safety["ok"]:
            body2 = draft
            break
    if not body2:
        return {"ok": False, "error": "3 attempts failed safety filter: " + last_summary}
    with db.connect() as c:
        c.execute("UPDATE autoblog_posts SET body_md=?, published_at=? WHERE slug=?",
                  (body2, _d3.datetime.utcnow().isoformat() + "Z", slug))
    db.log_event("autoblog", slug, "rewritten", actor="admin",
                 details={"new_chars": len(body2)})
    return {"ok": True, "slug": slug, "chars": len(body2),
            "safety": last_summary}


@router.get("/autoblog/{slug}", dependencies=[Depends(require_admin)])
def autoblog_get(slug: str):
    """Full body of one article — used by the edit modal."""
    with db.connect() as c:
        try:
            r = c.execute("SELECT * FROM autoblog_posts WHERE slug=?", (slug,)).fetchone()
        except Exception: r = None
        if not r:
            raise HTTPException(404, "post not found")
        # Recent visitors for this post (last 50)
        try:
            views = c.execute(
                "SELECT ts, referer, source FROM autoblog_views WHERE slug=? "
                "ORDER BY id DESC LIMIT 50", (slug,)).fetchall()
        except Exception: views = []
    out = db.row_to_dict(r) or {}
    out["recent_views"] = [db.row_to_dict(v) for v in views]
    return out


@router.post("/autoblog/{slug}", dependencies=[Depends(require_admin)])
async def autoblog_update(slug: str, request: Request):
    """Inline edit: admin can rewrite topic/body before further AI passes.
    Returns the updated row."""
    body = await request.json()
    new_topic = (body.get("topic") or "").strip()
    new_body = body.get("body_md") or ""
    new_emirate = (body.get("emirate") or "").strip()
    if not new_topic and not new_body:
        return {"ok": False, "error": "nothing to update"}
    with db.connect() as c:
        r = c.execute("SELECT id FROM autoblog_posts WHERE slug=?", (slug,)).fetchone()
        if not r:
            raise HTTPException(404, "post not found")
        c.execute(
            "UPDATE autoblog_posts SET topic=COALESCE(NULLIF(?,''), topic), "
            "body_md=COALESCE(NULLIF(?,''), body_md), "
            "emirate=COALESCE(NULLIF(?,''), emirate) WHERE slug=?",
            (new_topic, new_body, new_emirate, slug))
    db.log_event("autoblog", slug, "edited", actor="admin",
                 details={"topic_changed": bool(new_topic), "body_changed": bool(new_body)})
    return {"ok": True, "slug": slug}


@router.delete("/autoblog/{slug}", dependencies=[Depends(require_admin)])
def autoblog_delete(slug: str):
    with db.connect() as c:
        n = c.execute("DELETE FROM autoblog_posts WHERE slug=?", (slug,)).rowcount
        try: c.execute("DELETE FROM autoblog_views WHERE slug=?", (slug,))
        except Exception: pass
    return {"ok": True, "deleted": int(n)}


# ---------- LLM diagnostics ----------
@router.get("/llm/diagnose")
def llm_diagnose():
    """Pings the configured Anthropic key + model with a 1-token prompt and
    returns the EXACT error so admin can see why /api/chat keeps falling back
    to the demo brain. Common causes: invalid key, billing not set up, model
    name wrong, region restriction, rate limit."""
    from .config import get_settings
    s = get_settings()
    out = {
        "configured": bool(s.ANTHROPIC_API_KEY),
        "key_preview": (s.ANTHROPIC_API_KEY[:8] + "…" + s.ANTHROPIC_API_KEY[-4:]) if len(s.ANTHROPIC_API_KEY or "") >= 14 else "",
        "key_len": len(s.ANTHROPIC_API_KEY or ""),
        "model_configured": s.MODEL,
        "use_llm": s.use_llm,
        "demo_mode": s.DEMO_MODE,
    }
    if not s.ANTHROPIC_API_KEY:
        out["ok"] = False
        out["error"] = "ANTHROPIC_API_KEY env var is empty. Set it in Railway → Variables."
        out["fix"] = "Go to https://console.anthropic.com/settings/keys → create key → paste into Railway env."
        return out
    import time, anthropic
    t0 = time.perf_counter()
    try:
        client = anthropic.Anthropic(api_key=s.ANTHROPIC_API_KEY, timeout=12.0, max_retries=0)
        resp = client.messages.create(
            model=s.MODEL, max_tokens=10,
            messages=[{"role": "user", "content": "Reply with just: ok"}],
        )
        latency = int((time.perf_counter() - t0) * 1000)
        text = ""
        for b in resp.content:
            if getattr(b, "type", "") == "text": text += b.text
        out["ok"] = True
        out["latency_ms"] = latency
        out["model_responded"] = getattr(resp, "model", s.MODEL)
        out["sample"] = text[:80]
        out["usage"] = {
            "input_tokens": getattr(resp.usage, "input_tokens", 0),
            "output_tokens": getattr(resp.usage, "output_tokens", 0),
        }
        out["msg"] = f"✅ Working — {out['model_responded']} replied in {latency}ms with: \"{text[:60]}\""
    except anthropic.AuthenticationError as e:
        out["ok"] = False
        out["error"] = f"Authentication failed (401): {e}"
        out["fix"] = "Key is invalid or revoked. Generate a new one at https://console.anthropic.com/settings/keys."
    except anthropic.RateLimitError as e:
        out["ok"] = False
        out["error"] = f"Rate limited (429): {e}"
        out["fix"] = "Wait a minute, or upgrade your Anthropic plan: https://console.anthropic.com/settings/billing."
    except anthropic.NotFoundError as e:
        out["ok"] = False
        out["error"] = f"Model not found (404): {e}"
        out["fix"] = f"Model '{s.MODEL}' is not available on your account. Try CLAUDE_MODEL=claude-sonnet-4-6 or claude-haiku-4-5 in Railway env."
    except anthropic.BadRequestError as e:
        out["ok"] = False
        out["error"] = f"Bad request (400): {e}"
        out["fix"] = "Likely a prompt-shape issue or model alias problem. Try CLAUDE_MODEL=claude-sonnet-4-6 in Railway env."
    except anthropic.PermissionDeniedError as e:
        out["ok"] = False
        out["error"] = f"Permission denied (403): {e}"
        out["fix"] = "Your account doesn't have access to this model. Check https://console.anthropic.com/settings/limits."
    except Exception as e:  # noqa: BLE001
        out["ok"] = False
        out["error"] = f"{type(e).__name__}: {e}"
        out["fix"] = "Check Railway service logs for full traceback."
    out["latency_ms"] = int((time.perf_counter() - t0) * 1000)
    return out


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


# ============================================================
# TWA / Mobile App credentials
#
# The Servia production Android keystore lives encrypted at rest in
# app/data/twa_credentials.enc — encrypted with a key derived from
# ADMIN_TOKEN via PBKDF2-HMAC-SHA256. Decrypting requires both the
# blob AND the live ADMIN_TOKEN; without one of those the keystore
# cannot be recovered.
# ============================================================

@router.get("/twa/credentials")
def twa_credentials():
    """Decrypt + return the Servia Android signing keystore + credentials.
    Used by the admin Mobile-App tab so the operator can copy these into
    GitHub Actions secrets for the production Play Store build."""
    import base64, hashlib, json, os
    from pathlib import Path
    from cryptography.fernet import Fernet, InvalidToken

    blob_path = Path(__file__).parent / "data" / "twa_credentials.enc"
    if not blob_path.exists():
        raise HTTPException(404, "no twa keystore stored — run the bootstrap script")

    admin_token = os.environ.get("ADMIN_TOKEN", "lumora-admin-test")
    salt = b"servia.twa.creds.v1"
    key_bytes = hashlib.pbkdf2_hmac("sha256", admin_token.encode(), salt, 100_000, dklen=32)
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    f = Fernet(fernet_key)

    encrypted = blob_path.read_bytes()
    try:
        decrypted = json.loads(f.decrypt(encrypted))
    except InvalidToken:
        raise HTTPException(500,
            "could not decrypt twa keystore — ADMIN_TOKEN may have been rotated since "
            "creds were stored. Regenerate via the keystore-rotate endpoint.")
    return decrypted


class TwaWorkflowReq(BaseModel):
    ref: str = "main"  # tag or branch to trigger workflow on


@router.post("/twa/trigger-build")
def twa_trigger_build(body: TwaWorkflowReq):
    """Trigger the Build Android TWA GitHub Actions workflow via the GitHub
    REST API. Requires GITHUB_TOKEN env var with `actions: write` scope on
    the aalmir-erp/aalmir_git_new repo. Without that, returns the URL the
    user should visit on their phone to trigger it manually."""
    import os, json, urllib.request, urllib.error
    repo = os.environ.get("GITHUB_REPO", "aalmir-erp/aalmir_git_new")
    workflow = "build-android-twa.yml"
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    fallback = f"https://github.com/{repo}/actions/workflows/{workflow}"

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return {
            "ok": False,
            "manual_url": fallback,
            "detail": "GITHUB_TOKEN env var not set. Open the URL above on your "
                      "phone, tap 'Run workflow' → 'main' → green button.",
        }
    req = urllib.request.Request(url, method="POST",
        data=json.dumps({"ref": body.ref}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
        return {
            "ok": True,
            "workflow": workflow,
            "ref": body.ref,
            "view_runs_url": f"https://github.com/{repo}/actions/workflows/{workflow}",
        }
    except urllib.error.HTTPError as e:
        return {
            "ok": False,
            "error": f"GitHub API {e.code}: {e.reason}",
            "manual_url": fallback,
            "detail": e.read().decode("utf-8", "replace")[:500],
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "manual_url": fallback}


@router.get("/twa/installs")
def twa_installs():
    """Aggregate install funnel metrics for the admin Mobile-App tab —
    total events by type, by app version, by device, recent installs
    (with linked customer name/phone if known)."""
    from datetime import datetime, timedelta
    out = {"totals": {}, "by_version": [], "by_platform": [],
           "recent": [], "unique_devices": 0, "linked_customers": 0}
    with db.connect() as c:
        # Make sure the table exists
        try:
            c.execute("CREATE TABLE IF NOT EXISTS app_installs("
                      "id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT,"
                      "created_at TEXT)")
        except Exception: pass
        try:
            cnt = c.execute("SELECT event, COUNT(*) AS n FROM app_installs "
                            "GROUP BY event ORDER BY n DESC").fetchall()
            out["totals"] = {r["event"]: r["n"] for r in cnt}
        except Exception: pass
        try:
            ver = c.execute(
                "SELECT app_version, COUNT(*) AS n FROM app_installs "
                "WHERE app_version IS NOT NULL AND app_version != '' "
                "GROUP BY app_version ORDER BY n DESC LIMIT 10").fetchall()
            out["by_version"] = [dict(r) for r in ver]
        except Exception: pass
        try:
            plat = c.execute(
                "SELECT platform, COUNT(*) AS n FROM app_installs "
                "WHERE platform IS NOT NULL AND platform != '' "
                "GROUP BY platform ORDER BY n DESC LIMIT 10").fetchall()
            out["by_platform"] = [dict(r) for r in plat]
        except Exception: pass
        try:
            ud = c.execute(
                "SELECT COUNT(DISTINCT device_id) AS n FROM app_installs "
                "WHERE device_id IS NOT NULL AND device_id != ''").fetchone()
            out["unique_devices"] = ud["n"] if ud else 0
        except Exception: pass
        try:
            lc = c.execute(
                "SELECT COUNT(DISTINCT customer_id) AS n FROM app_installs "
                "WHERE customer_id IS NOT NULL").fetchone()
            out["linked_customers"] = lc["n"] if lc else 0
        except Exception: pass
        # Recent installs with customer details where available
        try:
            recent = c.execute(
                "SELECT i.event, i.app_version, i.device_model, i.os_version, "
                "i.platform, i.device_id, i.customer_id, i.created_at, "
                "i.user_agent, i.source_page, "
                "c.name AS customer_name, c.phone AS customer_phone, "
                "c.email AS customer_email "
                "FROM app_installs i LEFT JOIN customers c ON c.id=i.customer_id "
                "ORDER BY i.id DESC LIMIT 50").fetchall()
            out["recent"] = [dict(r) for r in recent]
        except Exception: pass
    return out
