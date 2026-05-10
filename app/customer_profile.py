"""v1.24.83 — Customer profile foundation.

Replaces "phone-only access" with a structured customer profile that
the user themselves manages. Auto-created the first time a quote is
generated for a phone number — so the user has a profile to claim
without filling forms.

Schema extensions on `customers`:
  - profile_pic_url      TEXT   (uploaded image)
  - family_json          TEXT   ([{name, role, dob, phone}])
  - locations_json       TEXT   ([{label, address, lat, lng, building, unit, area, city}])
  - bio                  TEXT   (optional self-description)
  - device_tokens_json   TEXT   ([{token, label, last_used_at}])
  - claimed_at           TEXT   (set after the user logs in for the first time)

API:
  POST /api/me/auth/start    — initiate magic-link or device-token auth
  POST /api/me/auth/verify   — verify token → returns session token cookie
  GET  /api/me/profile       — fetch current authed customer's profile
  PUT  /api/me/profile       — update name / email / pic / bio
  POST /api/me/locations     — add a location (label + address + pin lat/lng + building/unit/area/city)
  DELETE /api/me/locations/<id>
  POST /api/me/family        — add/update family members
  POST /api/me/password      — set/change password
  GET  /api/me/quotes        — list all quotes for this phone
  GET  /api/me/bookings      — list all bookings
  POST /api/me/tickets       — open a support ticket
  GET  /api/me/tickets       — list my tickets

Auto-account hook: app/tools.py::create_multi_quote calls
ensure_customer(phone, name) which inserts a row if it doesn't exist.
The customer can later "claim" the account via /api/me/auth/start.
"""
from __future__ import annotations
import datetime as _dt
import hashlib
import hmac
import json as _json
import os
import secrets
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Cookie, Response
from pydantic import BaseModel

from . import db
from .config import get_settings


router = APIRouter(tags=["customer-profile"])


# ─── Schema bootstrap ─────────────────────────────────────────────────
def _ensure_schema() -> None:
    """Idempotent — adds new columns if not already present."""
    with db.connect() as c:
        cols = [
            ("profile_pic_url", "TEXT"),
            ("family_json", "TEXT"),
            ("locations_json", "TEXT"),
            ("bio", "TEXT"),
            ("device_tokens_json", "TEXT"),
            ("claimed_at", "TEXT"),
        ]
        for name, typ in cols:
            try: c.execute(f"ALTER TABLE customers ADD COLUMN {name} {typ}")
            except Exception: pass
        c.execute("""CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            body TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT NOT NULL,
            resolved_at TEXT
        )""")


def _now() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


def ensure_customer(phone: str, name: str | None = None,
                    email: str | None = None) -> int | None:
    """Auto-create a customers row from a chat-time phone if missing.
    Returns customer.id, or None on failure."""
    if not phone: return None
    digits = "".join(c for c in str(phone) if c.isdigit())
    if not digits: return None
    _ensure_schema()
    with db.connect() as c:
        existing = c.execute("SELECT id FROM customers WHERE phone=?",
                             (digits,)).fetchone()
        if existing:
            cid = existing["id"]
            updates, args = [], []
            if name:
                updates.append("name = COALESCE(NULLIF(name,''), ?)")
                args.append(name)
            if email:
                updates.append("email = COALESCE(NULLIF(email,''), ?)")
                args.append(email)
            updates.append("last_seen_at = ?")
            args.append(_now())
            args.append(cid)
            try:
                c.execute(f"UPDATE customers SET {', '.join(updates)} WHERE id=?", args)
            except Exception: pass
            return cid
        # Insert
        try:
            cur = c.execute(
                "INSERT INTO customers(phone, name, email, created_at, last_seen_at) "
                "VALUES(?, ?, ?, ?, ?)",
                (digits, name or "", email or "", _now(), _now()))
            return cur.lastrowid
        except Exception:
            return None


# ─── Auth via WhatsApp magic link OR password ─────────────────────────
class AuthStartReq(BaseModel):
    phone: str | None = None
    email: str | None = None


def _auth_token(phone: str, bucket: int) -> str:
    salt = os.getenv("MAGIC_LINK_SALT", "servia-magic-default")
    return hashlib.sha256(f"{phone}|{salt}|{bucket}".encode()).hexdigest()[:24]


@router.post("/api/me/auth/start")
def auth_start(req: AuthStartReq):
    """Start an auth flow. Returns 200 either way (do not reveal whether
    the phone is registered)."""
    _ensure_schema()
    phone = "".join(c for c in (req.phone or "") if c.isdigit())
    if not phone:
        return {"ok": False, "error": "phone required"}
    bucket = int(_dt.datetime.utcnow().timestamp() // 1800)  # 30-min window
    token = _auth_token(phone, bucket)
    domain = get_settings().brand().get("domain", "servia.ae")
    link = f"https://{domain}/me?phone={phone}&t={token}"
    # Try WhatsApp bridge first
    delivered = False
    try:
        s = get_settings()
        if s.WA_BRIDGE_URL and s.WA_BRIDGE_TOKEN:
            import httpx
            r = httpx.post(
                s.WA_BRIDGE_URL.rstrip("/") + "/send",
                headers={"Authorization": f"Bearer {s.WA_BRIDGE_TOKEN}"},
                json={"phone": phone, "message":
                      f"🔐 Sign in to Servia\n{link}\n\n"
                      f"This link expires in 30 minutes."},
                timeout=8.0,
            )
            delivered = r.status_code < 400
    except Exception: pass
    # Always fall back to admin alert
    try:
        from . import admin_alerts
        admin_alerts.notify_admin(
            f"🔐 Customer auth-link {'sent via WA' if delivered else 'requested'}\n"
            f"Phone: +{phone}\nLink: {link}",
            kind="magic_link", urgency="normal")
    except Exception: pass
    return {"ok": True, "delivered": delivered, "channel": "whatsapp" if delivered else "admin",
            "expires_in_min": 30}


class AuthVerifyReq(BaseModel):
    phone: str
    token: str


@router.post("/api/me/auth/verify")
def auth_verify(req: AuthVerifyReq, response: Response, request: Request):
    _ensure_schema()
    phone = "".join(c for c in (req.phone or "") if c.isdigit())
    if not phone or not req.token:
        return {"ok": False, "error": "phone + token required"}
    now_bucket = int(_dt.datetime.utcnow().timestamp() // 1800)
    if not any(hmac.compare_digest(req.token, _auth_token(phone, b))
               for b in (now_bucket, now_bucket - 1)):
        return {"ok": False, "error": "invalid or expired token"}
    cid = ensure_customer(phone)
    if not cid:
        return {"ok": False, "error": "customer record creation failed"}
    with db.connect() as c:
        c.execute("UPDATE customers SET claimed_at = COALESCE(claimed_at, ?) WHERE id=?",
                  (_now(), cid))
    # Set a long-lived auth cookie. `secure` only when the request actually
    # arrived over HTTPS — otherwise the cookie won't ride back on dev /
    # TestClient HTTP (was breaking the e2e test).
    sess = secrets.token_urlsafe(32)
    is_https = request.url.scheme == "https" or \
               request.headers.get("x-forwarded-proto", "").startswith("https")
    response.set_cookie(
        key="servia_auth", value=f"{cid}:{sess}",
        httponly=True, secure=is_https, samesite="lax", max_age=60*60*24*30,
        path="/")
    return {"ok": True, "customer_id": cid, "phone": phone}


def _authed_customer(servia_auth: str | None) -> dict | None:
    """Resolve the authed customer from cookie. Returns row dict or None."""
    if not servia_auth or ":" not in servia_auth:
        return None
    try:
        cid_str, _ = servia_auth.split(":", 1)
        cid = int(cid_str)
    except Exception:
        return None
    with db.connect() as c:
        r = c.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()
    return dict(r) if r else None


# ─── Profile read/write ──────────────────────────────────────────────
@router.get("/api/me/profile")
def get_profile(servia_auth: str | None = Cookie(None)):
    cust = _authed_customer(servia_auth)
    if not cust:
        return {"ok": False, "error": "not authenticated"}
    return {
        "ok": True,
        "id": cust["id"],
        "phone": cust["phone"],
        "name": cust.get("name") or "",
        "email": cust.get("email") or "",
        "language": cust.get("language") or "en",
        "profile_pic_url": cust.get("profile_pic_url") or "",
        "bio": cust.get("bio") or "",
        "family": _json.loads(cust.get("family_json") or "[]"),
        "locations": _json.loads(cust.get("locations_json") or "[]"),
        "claimed_at": cust.get("claimed_at"),
        "created_at": cust.get("created_at"),
    }


class ProfileUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    language: str | None = None
    bio: str | None = None
    profile_pic_url: str | None = None


@router.put("/api/me/profile")
def update_profile(body: ProfileUpdate, servia_auth: str | None = Cookie(None)):
    cust = _authed_customer(servia_auth)
    if not cust:
        return {"ok": False, "error": "not authenticated"}
    fields = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not fields: return {"ok": True, "updated": 0}
    sets = ", ".join(f"{k}=?" for k in fields)
    args = list(fields.values()) + [cust["id"]]
    with db.connect() as c:
        c.execute(f"UPDATE customers SET {sets} WHERE id=?", args)
    return {"ok": True, "updated": len(fields)}


# ─── Multiple locations + pin ─────────────────────────────────────────
class LocationItem(BaseModel):
    label: str          # "Home", "Office", "Mom's place"
    address: str        # full string
    building: str | None = None
    unit: str | None = None
    area: str | None = None
    city: str | None = None
    lat: float | None = None
    lng: float | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    notes: str | None = None


@router.post("/api/me/locations")
def add_location(body: LocationItem, servia_auth: str | None = Cookie(None)):
    cust = _authed_customer(servia_auth)
    if not cust:
        return {"ok": False, "error": "not authenticated"}
    item = body.model_dump()
    item["id"] = secrets.token_urlsafe(8)
    item["created_at"] = _now()
    with db.connect() as c:
        existing = _json.loads(cust.get("locations_json") or "[]")
        existing.append(item)
        c.execute("UPDATE customers SET locations_json=? WHERE id=?",
                  (_json.dumps(existing), cust["id"]))
    return {"ok": True, "location": item}


# v1.24.90 Slice A.5 — auto-save from chat / book / cart pin-pickers
# Dedupes by lat/lng within ~30m so the customer's profile doesn't get
# spammed when they pin the same place repeatedly across surfaces.
@router.post("/api/me/locations/upsert-from-pin")
def upsert_location_from_pin(body: LocationItem, servia_auth: str | None = Cookie(None)):
    cust = _authed_customer(servia_auth)
    if not cust:
        # Anonymous-friendly: silently no-op (the picker still works,
        # we just don't save). When the customer later authenticates,
        # backfill is the responsibility of the auth flow.
        return {"ok": True, "saved": False, "reason": "not authenticated"}
    item = body.model_dump()
    if not (item.get("lat") and item.get("lng")):
        return {"ok": False, "error": "lat/lng required for pin-based upsert"}
    existing = _json.loads(cust.get("locations_json") or "[]")
    # ~30m at UAE latitude ≈ 0.00027° (1° lat ≈ 111km, 30m ≈ 0.00027)
    THRESH = 0.00030
    duped = None
    for loc in existing:
        if loc.get("lat") and loc.get("lng"):
            if (abs(loc["lat"] - item["lat"]) < THRESH and
                abs(loc["lng"] - item["lng"]) < THRESH):
                duped = loc; break
    if duped:
        # Update label / building / unit if newly provided
        for k in ("label","building","unit","area","city",
                  "contact_name","contact_phone","notes"):
            if item.get(k) and not duped.get(k):
                duped[k] = item[k]
    else:
        item["id"] = secrets.token_urlsafe(8)
        item["created_at"] = _now()
        existing.append(item)
    with db.connect() as c:
        c.execute("UPDATE customers SET locations_json=? WHERE id=?",
                  (_json.dumps(existing), cust["id"]))
    return {"ok": True, "saved": True, "deduped": bool(duped),
            "location": duped or item}


@router.delete("/api/me/locations/{loc_id}")
def del_location(loc_id: str, servia_auth: str | None = Cookie(None)):
    cust = _authed_customer(servia_auth)
    if not cust:
        return {"ok": False, "error": "not authenticated"}
    existing = _json.loads(cust.get("locations_json") or "[]")
    new_list = [l for l in existing if l.get("id") != loc_id]
    with db.connect() as c:
        c.execute("UPDATE customers SET locations_json=? WHERE id=?",
                  (_json.dumps(new_list), cust["id"]))
    return {"ok": True, "removed": len(existing) - len(new_list)}


# ─── Family members ───────────────────────────────────────────────────
class FamilyItem(BaseModel):
    name: str
    role: str | None = None       # spouse, child, parent, helper
    phone: str | None = None
    dob: str | None = None
    notes: str | None = None


@router.post("/api/me/family")
def add_family(body: FamilyItem, servia_auth: str | None = Cookie(None)):
    cust = _authed_customer(servia_auth)
    if not cust:
        return {"ok": False, "error": "not authenticated"}
    item = body.model_dump()
    item["id"] = secrets.token_urlsafe(8)
    with db.connect() as c:
        existing = _json.loads(cust.get("family_json") or "[]")
        existing.append(item)
        c.execute("UPDATE customers SET family_json=? WHERE id=?",
                  (_json.dumps(existing), cust["id"]))
    return {"ok": True, "member": item}


# ─── Password (optional, for return visits) ──────────────────────────
class PasswordReq(BaseModel):
    new_password: str
    old_password: str | None = None


@router.post("/api/me/password")
def set_password(body: PasswordReq, servia_auth: str | None = Cookie(None)):
    cust = _authed_customer(servia_auth)
    if not cust:
        return {"ok": False, "error": "not authenticated"}
    if cust.get("password_hash") and body.old_password is not None:
        existing = cust["password_hash"]
        check = hashlib.sha256(
            (body.old_password + str(cust["id"])).encode()).hexdigest()
        if not hmac.compare_digest(existing, check):
            return {"ok": False, "error": "old password incorrect"}
    if not body.new_password or len(body.new_password) < 6:
        return {"ok": False, "error": "password must be ≥6 chars"}
    new_hash = hashlib.sha256(
        (body.new_password + str(cust["id"])).encode()).hexdigest()
    with db.connect() as c:
        c.execute("UPDATE customers SET password_hash=? WHERE id=?",
                  (new_hash, cust["id"]))
    return {"ok": True}


# ─── Quote / booking history (filtered by phone) ──────────────────────
@router.get("/api/me/quotes")
def list_my_quotes(servia_auth: str | None = Cookie(None)):
    cust = _authed_customer(servia_auth)
    if not cust:
        return {"ok": False, "error": "not authenticated"}
    with db.connect() as c:
        rows = c.execute(
            "SELECT quote_id, total_aed, target_date, time_slot, "
            "       signed_at, paid_at, created_at "
            "FROM multi_quotes WHERE phone=? "
            "ORDER BY created_at DESC LIMIT 200",
            (cust["phone"],)).fetchall()
    return {"ok": True, "quotes": [dict(r) for r in rows]}


# ─── Tickets ──────────────────────────────────────────────────────────
class TicketReq(BaseModel):
    subject: str
    body: str | None = ""


@router.post("/api/me/tickets")
def open_ticket(body: TicketReq, servia_auth: str | None = Cookie(None)):
    cust = _authed_customer(servia_auth)
    if not cust:
        return {"ok": False, "error": "not authenticated"}
    _ensure_schema()
    with db.connect() as c:
        cur = c.execute(
            "INSERT INTO support_tickets(customer_id, subject, body, created_at) "
            "VALUES(?, ?, ?, ?)",
            (cust["id"], body.subject, body.body or "", _now()))
        tid = cur.lastrowid
    return {"ok": True, "ticket_id": tid}


@router.get("/api/me/tickets")
def list_my_tickets(servia_auth: str | None = Cookie(None)):
    cust = _authed_customer(servia_auth)
    if not cust:
        return {"ok": False, "error": "not authenticated"}
    _ensure_schema()
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, subject, body, status, created_at, resolved_at "
            "FROM support_tickets WHERE customer_id=? "
            "ORDER BY created_at DESC LIMIT 200", (cust["id"],)).fetchall()
    return {"ok": True, "tickets": [dict(r) for r in rows]}


@router.post("/api/me/logout")
def logout(response: Response):
    response.delete_cookie("servia_auth", path="/")
    return {"ok": True}
