"""v1.24.143 — Centralized brand contact info (phone, email, WhatsApp).

WHY THIS EXISTS
---------------
Founder request: "Every phone/landline/email mentioned anywhere on the
website should pull from ONE field in admin general settings. Replace
strictly wherever you're using everything from one field."

Before v1.24.143:
  - `support@servia.ae` hardcoded in 8+ places
  - `bookings@servia.ae` hardcoded in nfc.py
  - `admin@servia.ae` hardcoded in push_notifications.py
  - WhatsApp number hardcoded in multiple HTML files
  → Changing the contact phone/email means hunting through dozens of
    files and missing some.

THIS MODULE PROVIDES
--------------------
  get_contact_phone()      → main customer-facing phone (config: contact_phone)
  get_contact_whatsapp()   → WhatsApp number (config: contact_whatsapp,
                              falls back to contact_phone if not set)
  get_contact_email()      → support email (config: contact_email)
  get_bookings_email()     → bookings inbox (config: bookings_email,
                              falls back to contact_email)
  get_admin_email()        → admin alerts inbox (config: admin_email,
                              falls back to contact_email)
  get_brand_block()        → dict with all the above + name + address +
                              trn — for templates that need multiple

ALL functions read from the `config` table at runtime, NOT at module
load — so updates from /admin propagate immediately without restart.
Cached for 30 seconds to avoid hitting the DB on every request.

ADMIN UI
--------
/admin-contact.html provides a single form to set all six fields.
POST /api/admin/contact/save persists to config.

WHERE TO USE
------------
- Anywhere in Python: `from app.brand_contact import get_contact_email`
- In HTML/JS: use the JS helper `<script src="/brand-contact.js">` which
  fetches /api/brand/contact (public) and replaces all elements with
  `data-bc-phone` / `data-bc-email` / `data-bc-whatsapp` attributes.
"""
from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from . import db
from .auth import require_admin


router = APIRouter()


# Defaults (used when admin hasn't configured these yet — preserves
# backward compat with pre-v1.24.143 hardcoded values)
DEFAULTS = {
    "contact_phone":     "+971 4 000 0000",        # update via admin
    "contact_whatsapp":  "+971 50 000 0000",
    "contact_email":     "support@servia.ae",
    "bookings_email":    "bookings@servia.ae",
    "admin_email":       "admin@servia.ae",
    "brand_name":        "Servia",
    "company_address":   "Dubai, UAE",
    "vat_trn":           "",
    "company_legal_name": "Servia FZ-LLC",
}


# Read-through cache so we don't hit SQLite on every page load
_cache: dict = {}
_cache_at: float = 0
_CACHE_TTL = 30  # seconds — short enough that admin edits propagate fast


def _load_all() -> dict:
    global _cache, _cache_at
    now = time.time()
    if _cache and (now - _cache_at) < _CACHE_TTL:
        return _cache
    out = dict(DEFAULTS)
    try:
        with db.connect() as c:
            rows = c.execute(
                "SELECT key, value FROM config WHERE key IN ("
                + ",".join(f"'{k}'" for k in DEFAULTS) + ")"
            ).fetchall()
            for r in rows:
                v = (r["value"] or "").strip()
                if v:
                    out[r["key"]] = v
    except Exception:
        pass
    _cache = out
    _cache_at = now
    return out


# v1.24.165 — Detect placeholder / unset numbers so we don't render
# the "000 0000" default in share links / printables. Founder said:
# "you put some random number in WhatsApp by default" — that's this.
_PLACEHOLDER_PATTERNS = ("000 0000", "0000000", "000000",
                          "111 0001", "111 0002", "111 0003", "111 0004", "111 0005",
                          "1110001", "1110002", "1110003", "1110004", "1110005",
                          "1111", "0001")


def _is_placeholder(s: str) -> bool:
    """v1.24.169 — Detect placeholder numbers. Anything matching
    '+971 50 000 0000' / '+971 50 111 0001' / '12345' / 4+ consecutive
    identical digits / <9 digits gets treated as unset so share buttons
    hide instead of advertising a fake number."""
    s = (s or "").strip().lower()
    if not s:
        return True
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) < 9:
        return True
    if any(p in s for p in _PLACEHOLDER_PATTERNS):
        return True
    # Detect runs of 4+ identical digits ("0000", "1111", "9999") which
    # are almost always placeholders in test data.
    for i in range(len(digits) - 3):
        if digits[i] == digits[i+1] == digits[i+2] == digits[i+3]:
            return True
    return False


def get_contact_phone() -> str:
    v = _load_all().get("contact_phone")
    if v and not _is_placeholder(v):
        return v
    return ""   # blank → callers fall back to "see /contact"


def get_contact_whatsapp() -> str:
    d = _load_all()
    for key in ("contact_whatsapp", "contact_phone"):
        v = d.get(key)
        if v and not _is_placeholder(v):
            return v
    return ""


def get_contact_email() -> str:
    v = _load_all().get("contact_email") or DEFAULTS.get("contact_email") or ""
    if "example" in v.lower() or "@example" in v.lower():
        return ""
    return v


def get_bookings_email() -> str:
    d = _load_all()
    return d.get("bookings_email") or d.get("contact_email") or DEFAULTS["bookings_email"]


def get_admin_email() -> str:
    d = _load_all()
    return d.get("admin_email") or d.get("contact_email") or DEFAULTS["admin_email"]


def get_brand_name() -> str:
    return _load_all().get("brand_name") or DEFAULTS["brand_name"]


def get_brand_block() -> dict:
    """Single call that returns everything — for templates."""
    return dict(_load_all())


# ─────────────────────────────────────────────────────────────────────
# Public endpoint — HTML pages fetch this to render contact info
# ─────────────────────────────────────────────────────────────────────
@router.get("/api/brand/contact")
def public_brand_contact():
    """Public, no-auth endpoint. Returns the customer-facing contact info
    so HTML pages can populate footer / contact buttons / etc. Internal-
    only fields (admin_email) are NOT exposed here."""
    d = _load_all()
    return {
        "ok": True,
        "brand_name":       d.get("brand_name"),
        "contact_phone":    d.get("contact_phone"),
        "contact_whatsapp": d.get("contact_whatsapp") or d.get("contact_phone"),
        "contact_email":    d.get("contact_email"),
        "bookings_email":   d.get("bookings_email") or d.get("contact_email"),
        "company_address":  d.get("company_address"),
        "company_legal":    d.get("company_legal_name"),
        # Pre-built convenience values for embedding
        "whatsapp_url":     "https://wa.me/" + (
            (d.get("contact_whatsapp") or d.get("contact_phone") or "")
            .lstrip("+").replace(" ", "").replace("-", "")
        ),
        "tel_url":          "tel:" + (d.get("contact_phone") or "").replace(" ", ""),
        "mailto_url":       "mailto:" + (d.get("contact_email") or ""),
    }


# ─────────────────────────────────────────────────────────────────────
# Admin endpoints — set + retrieve all contact fields
# ─────────────────────────────────────────────────────────────────────
class ContactSaveBody(BaseModel):
    contact_phone:     Optional[str] = None
    contact_whatsapp:  Optional[str] = None
    contact_email:     Optional[str] = None
    bookings_email:    Optional[str] = None
    admin_email:       Optional[str] = None
    brand_name:        Optional[str] = None
    company_address:   Optional[str] = None
    company_legal_name: Optional[str] = None
    vat_trn:           Optional[str] = None


@router.get("/api/admin/contact", dependencies=[Depends(require_admin)])
def admin_get_contact():
    """Admin: return ALL contact fields (including admin_email)."""
    return {"ok": True, **_load_all()}


@router.post("/api/admin/contact/save", dependencies=[Depends(require_admin)])
def admin_save_contact(body: ContactSaveBody):
    """Admin: save updated contact fields. Cache invalidated immediately."""
    global _cache_at
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    saved: list[str] = []
    with db.connect() as c:
        for field in ContactSaveBody.model_fields:
            val = getattr(body, field)
            if val is not None:
                c.execute("""
                    INSERT INTO config (key, value, updated_at) VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value,
                                                    updated_at=excluded.updated_at
                """, (field, val.strip(), now))
                saved.append(field)
    _cache_at = 0  # bust cache
    return {"ok": True, "saved_fields": saved}
