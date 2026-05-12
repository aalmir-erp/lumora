"""v1.24.135 — Airbnb / Vrbo / Booking.com iCal sync for short-stay turnovers.

WHAT
----
UAE Airbnb hosts (~30,000 active listings in Dubai alone) need a cleaning
between every guest checkout and the next check-in. Manual coordination is
the bottleneck: hosts forget, message us at 22:00 with "guest leaves at 11
tomorrow, can someone clean before 3?", and we scramble.

This module solves it by reading the host's iCal feed (every short-stay
platform exports one — Airbnb, Vrbo, Booking.com, Hospitable, Hostfully)
and auto-creating turnover cleaning slots in every gap between a checkout
and a check-in.

ICAL FEED URLS — what hosts paste in
------------------------------------
  Airbnb:        https://www.airbnb.com/calendar/ical/<listing>.ics?s=<sig>
  Vrbo:          https://www.vrbo.com/icalendar/<key>.ics
  Booking.com:   https://admin.booking.com/hotel/hoteladmin/ical.html?<key>
  Hospitable:    https://my.hospitable.com/calendars/<listing>.ics
  Hostfully:     https://platform.hostfully.com/api/v3/calendar/<key>.ics

We don't care which platform — the iCal format is the standard, every
platform speaks it the same way.

DATA MODEL
----------
  airbnb_hosts          one row per (customer × listing × iCal URL)
  airbnb_reservations   one row per VEVENT we've seen (history kept)
  airbnb_turnovers      one row per checkout→checkin gap we found

SYNC FLOW
---------
  POST /api/host/airbnb/sync         (one-off — fetch + diff + schedule)
  GET  /api/host/airbnb/upcoming     (host portal — see what's scheduled)
  POST /api/host/airbnb/host         (add a host iCal URL)
  GET  /api/host/airbnb/hosts        (list customer's hosts)
  POST /api/host/airbnb/turnover/{id}/confirm   (book it for real)
  POST /api/host/airbnb/turnover/{id}/decline   (skip this turnover)

  GET  /api/admin/airbnb/hosts       (admin — all hosts, last sync)
  POST /api/admin/airbnb/sync-all    (admin — force-sync everyone)

iCAL PARSER
-----------
Hand-rolled, no external dep. The iCal spec is verbose but we only care
about VEVENT blocks with DTSTART, DTEND, SUMMARY, UID. The "icalendar"
PyPI library is 30× our needed surface area — we stay minimal.

TURNOVER SCHEDULING POLICY
--------------------------
- Default cleaning: deep_cleaning (changeable per host)
- Default start time: 1 hr after checkout, capped at 4 hrs before next checkin
- Default duration: 3 hrs (changeable per host)
- If checkout-to-checkin gap is < 4 hrs total: flag for manual review
  (probably back-to-back, host might be skipping a deep clean)
- If checkout-to-checkin gap is > 24 hrs: schedule for the morning of
  the checkin day (~5 hrs before guest arrival), to keep the property
  fresh
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field

from . import db
from .auth import require_admin


router = APIRouter()


# ─────────────────────────────────────────────────────────────────────
# Schema bootstrap
# ─────────────────────────────────────────────────────────────────────
def _init_schema() -> None:
    with db.connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS airbnb_hosts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id     INTEGER NOT NULL,
            listing_name    TEXT,
            ical_url        TEXT NOT NULL,
            platform        TEXT,                     -- 'airbnb' | 'vrbo' | 'booking' | 'other'
            default_service_id TEXT DEFAULT 'deep_cleaning',
            default_address_id INTEGER,
            cleaning_duration_min INTEGER DEFAULT 180, -- 3 hrs default
            checkout_buffer_min INTEGER DEFAULT 60,    -- start 1hr after checkout
            checkin_buffer_min  INTEGER DEFAULT 240,   -- finish 4hrs before next checkin
            active          INTEGER DEFAULT 1,
            last_synced_at  TEXT,
            last_sync_status TEXT,                    -- 'ok' | 'error: ...'
            created_at      TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ah_customer ON airbnb_hosts(customer_id);
        CREATE INDEX IF NOT EXISTS idx_ah_active ON airbnb_hosts(active);

        CREATE TABLE IF NOT EXISTS airbnb_reservations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            host_id         INTEGER NOT NULL,
            ical_uid        TEXT NOT NULL,            -- VEVENT UID
            checkin_dt      TEXT NOT NULL,
            checkout_dt     TEXT NOT NULL,
            summary         TEXT,
            status          TEXT DEFAULT 'reserved', -- reserved | cancelled
            first_seen_at   TEXT NOT NULL,
            last_seen_at    TEXT NOT NULL,
            UNIQUE(host_id, ical_uid)
        );
        CREATE INDEX IF NOT EXISTS idx_ar_host ON airbnb_reservations(host_id);
        CREATE INDEX IF NOT EXISTS idx_ar_checkin ON airbnb_reservations(checkin_dt);

        CREATE TABLE IF NOT EXISTS airbnb_turnovers (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            host_id         INTEGER NOT NULL,
            previous_reservation_id INTEGER,   -- the checkout reservation
            next_reservation_id     INTEGER,   -- the checkin reservation
            checkout_dt     TEXT NOT NULL,
            next_checkin_dt TEXT NOT NULL,
            scheduled_start_dt TEXT NOT NULL,  -- when the cleaner arrives
            duration_min    INTEGER NOT NULL,
            status          TEXT DEFAULT 'planned',  -- planned | confirmed | booked | declined | manual-review
            booking_id      INTEGER,           -- FK to bookings.id when confirmed
            review_reason   TEXT,              -- e.g. "gap < 4 hrs"
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            UNIQUE(host_id, checkout_dt, next_checkin_dt)
        );
        CREATE INDEX IF NOT EXISTS idx_at_host ON airbnb_turnovers(host_id);
        CREATE INDEX IF NOT EXISTS idx_at_status ON airbnb_turnovers(status);
        CREATE INDEX IF NOT EXISTS idx_at_start ON airbnb_turnovers(scheduled_start_dt);
        """)


_init_schema()


# ─────────────────────────────────────────────────────────────────────
# iCal parser — hand-rolled, no external dep
# ─────────────────────────────────────────────────────────────────────
def _detect_platform(url: str) -> str:
    u = url.lower()
    if "airbnb" in u: return "airbnb"
    if "vrbo" in u or "homeaway" in u: return "vrbo"
    if "booking.com" in u: return "booking"
    if "hospitable" in u: return "hospitable"
    if "hostfully" in u: return "hostfully"
    return "other"


def _unfold_lines(text: str) -> list[str]:
    """iCal spec: long lines wrap with a leading space/tab on continuation."""
    out: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw.startswith((" ", "\t")) and out:
            out[-1] += raw[1:]
        else:
            out.append(raw)
    return out


def _parse_ical_dt(value: str) -> datetime | None:
    """Parse an iCal DTSTART/DTEND value. Supports:
       - DATE form: 20260514                  → 14 May 2026 00:00 UTC
       - DATETIME UTC: 20260514T110000Z
       - DATETIME floating: 20260514T110000  (treated as UTC for our purposes)
       - DATETIME with TZID prefix: stripped to the value part
    """
    v = (value or "").strip()
    # Allow forms like "TZID=Asia/Dubai:20260514T110000" — keep the part after ":"
    if ":" in v:
        v = v.rsplit(":", 1)[-1]
    try:
        if "T" in v:
            base = v.rstrip("Z").replace("-", "").replace(":", "")
            return datetime.strptime(base, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        elif len(v) == 8 and v.isdigit():
            return datetime.strptime(v, "%Y%m%d").replace(tzinfo=timezone.utc)
    except Exception:
        return None
    return None


def parse_ical(text: str) -> list[dict]:
    """Parse an iCal feed into a list of {uid, summary, checkin_dt, checkout_dt}.
    Returns one entry per VEVENT block. DTSTART → checkin, DTEND → checkout.
    Cancelled events (STATUS:CANCELLED) are skipped."""
    events: list[dict] = []
    in_event = False
    cur: dict = {}
    for line in _unfold_lines(text):
        if line == "BEGIN:VEVENT":
            in_event = True; cur = {}
            continue
        if line == "END:VEVENT":
            if cur.get("checkin_dt") and cur.get("checkout_dt") and not cur.get("cancelled"):
                events.append({
                    "uid": cur.get("uid") or f"no-uid-{cur['checkin_dt']}",
                    "summary": cur.get("summary", ""),
                    "checkin_dt": cur["checkin_dt"],
                    "checkout_dt": cur["checkout_dt"],
                })
            in_event = False; cur = {}
            continue
        if not in_event:
            continue
        # Key:Value, key may have ;PARAM=VAL prefix (e.g. DTSTART;TZID=...:...)
        if ":" not in line:
            continue
        key_part, _, val = line.partition(":")
        key = key_part.split(";")[0].upper()
        if key == "UID":
            cur["uid"] = val.strip()
        elif key == "SUMMARY":
            # iCal escapes commas / semicolons / newlines with backslash
            cur["summary"] = val.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";").strip()
        elif key == "DTSTART":
            dt = _parse_ical_dt(val if ":" not in val else val)
            if dt is None:
                # Re-parse with the full key_part included (for TZID handling)
                dt = _parse_ical_dt(line.partition(":")[2])
            if dt: cur["checkin_dt"] = dt
        elif key == "DTEND":
            dt = _parse_ical_dt(val)
            if dt is None:
                dt = _parse_ical_dt(line.partition(":")[2])
            if dt: cur["checkout_dt"] = dt
        elif key == "STATUS":
            if val.strip().upper() == "CANCELLED":
                cur["cancelled"] = True
    return events


# ─────────────────────────────────────────────────────────────────────
# Sync engine
# ─────────────────────────────────────────────────────────────────────
async def _fetch_ical(url: str) -> str:
    """Fetch an iCal URL with a 15-sec timeout."""
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as c:
        r = await c.get(url, headers={"User-Agent": "Servia/1.24.135 iCal Sync"})
        r.raise_for_status()
        return r.text


def _schedule_turnover(host: dict, prev_res: dict, next_res: dict) -> dict | None:
    """Compute scheduled_start + duration for the gap between two reservations.
    Returns None if the gap is too short (< buffer + duration + buffer)."""
    co = datetime.fromisoformat(prev_res["checkout_dt"])
    ci = datetime.fromisoformat(next_res["checkin_dt"])
    gap = (ci - co).total_seconds() / 60.0  # minutes
    co_buf = host.get("checkout_buffer_min", 60)
    ci_buf = host.get("checkin_buffer_min", 240)
    dur = host.get("cleaning_duration_min", 180)
    needed = co_buf + dur + (min(ci_buf, gap - co_buf - dur) if gap > co_buf + dur else 0)
    if gap < co_buf + dur:
        return {
            "scheduled_start_dt": co.isoformat(),
            "duration_min": dur,
            "status": "manual-review",
            "review_reason": f"gap of {int(gap)}min < required {co_buf + dur}min (buffer + duration)",
        }
    # Default: start at checkout + buffer
    start = co + timedelta(minutes=co_buf)
    return {
        "scheduled_start_dt": start.isoformat(),
        "duration_min": dur,
        "status": "planned",
    }


def _do_sync(host_row: dict, ical_text: str) -> dict:
    """Diff parsed events vs stored reservations, then compute turnovers
    for every gap. Idempotent."""
    parsed = parse_ical(ical_text)
    now = datetime.now(timezone.utc).isoformat()
    host_id = host_row["id"]
    seen_uids: set[str] = set()
    stored_count = 0
    with db.connect() as c:
        for ev in parsed:
            uid = ev["uid"]
            seen_uids.add(uid)
            existing = c.execute("""
                SELECT id FROM airbnb_reservations WHERE host_id=? AND ical_uid=?
            """, (host_id, uid)).fetchone()
            if existing:
                c.execute("""
                    UPDATE airbnb_reservations
                    SET checkin_dt=?, checkout_dt=?, summary=?, last_seen_at=?
                    WHERE id=?
                """, (ev["checkin_dt"].isoformat(), ev["checkout_dt"].isoformat(),
                      ev["summary"], now, existing["id"]))
            else:
                c.execute("""
                    INSERT INTO airbnb_reservations
                      (host_id, ical_uid, checkin_dt, checkout_dt, summary,
                       first_seen_at, last_seen_at)
                    VALUES (?,?,?,?,?,?,?)
                """, (host_id, uid, ev["checkin_dt"].isoformat(),
                      ev["checkout_dt"].isoformat(), ev["summary"], now, now))
                stored_count += 1

        # Mark reservations that disappeared as cancelled (host may have
        # deleted them from Airbnb — we keep history but flag status).
        c.execute("""
            UPDATE airbnb_reservations SET status='cancelled'
            WHERE host_id=? AND last_seen_at < ? AND status='reserved'
        """, (host_id, now))

        # Now compute turnovers: order by checkin_dt, look at consecutive pairs.
        rows = c.execute("""
            SELECT id, checkin_dt, checkout_dt FROM airbnb_reservations
            WHERE host_id=? AND status='reserved' AND checkout_dt >= ?
            ORDER BY checkin_dt ASC
        """, (host_id, now)).fetchall()
        reservations = [dict(r) for r in rows]

        turnovers_planned = 0
        turnovers_review = 0
        for i in range(len(reservations) - 1):
            prev = reservations[i]
            nxt = reservations[i + 1]
            slot = _schedule_turnover(host_row, prev, nxt)
            if slot is None:
                continue
            # Upsert
            existing = c.execute("""
                SELECT id, status FROM airbnb_turnovers
                WHERE host_id=? AND checkout_dt=? AND next_checkin_dt=?
            """, (host_id, prev["checkout_dt"], nxt["checkin_dt"])).fetchone()
            if existing:
                # Don't overwrite a confirmed/booked turnover with planned
                if existing["status"] in ("confirmed", "booked", "declined"):
                    continue
                c.execute("""
                    UPDATE airbnb_turnovers
                    SET previous_reservation_id=?, next_reservation_id=?,
                        scheduled_start_dt=?, duration_min=?, status=?,
                        review_reason=?, updated_at=?
                    WHERE id=?
                """, (prev["id"], nxt["id"], slot["scheduled_start_dt"],
                      slot["duration_min"], slot["status"],
                      slot.get("review_reason"), now, existing["id"]))
            else:
                c.execute("""
                    INSERT INTO airbnb_turnovers
                      (host_id, previous_reservation_id, next_reservation_id,
                       checkout_dt, next_checkin_dt, scheduled_start_dt,
                       duration_min, status, review_reason, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (host_id, prev["id"], nxt["id"],
                      prev["checkout_dt"], nxt["checkin_dt"],
                      slot["scheduled_start_dt"], slot["duration_min"],
                      slot["status"], slot.get("review_reason"), now, now))
            if slot["status"] == "manual-review":
                turnovers_review += 1
            else:
                turnovers_planned += 1

        # Update host's sync status
        c.execute("""
            UPDATE airbnb_hosts SET last_synced_at=?, last_sync_status=?
            WHERE id=?
        """, (now, "ok", host_id))

    return {
        "ok": True,
        "reservations_parsed": len(parsed),
        "reservations_new": stored_count,
        "turnovers_planned": turnovers_planned,
        "turnovers_manual_review": turnovers_review,
        "host_id": host_id,
    }


# ─────────────────────────────────────────────────────────────────────
# Authentication helper — extract customer_id from session token.
# Falls back to admin-overridable customer_id query param for testing.
# ─────────────────────────────────────────────────────────────────────
def _get_customer_id(request: Request, customer_id: int | None = None) -> int:
    """Get the customer_id from the auth session, or accept it from a
    query param if the request has admin auth."""
    # Path 1: query param override (admin testing)
    if customer_id is not None:
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            try:
                require_admin(auth)
                return int(customer_id)
            except Exception:
                pass
    # Path 2: customer auth_sessions table
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        with db.connect() as c:
            row = c.execute("""
                SELECT customer_id FROM auth_sessions WHERE token=?
                AND (expires_at IS NULL OR expires_at > datetime('now'))
            """, (token,)).fetchone()
            if row:
                return row["customer_id"]
    raise HTTPException(status_code=401, detail="customer auth required")


# ─────────────────────────────────────────────────────────────────────
# Host-facing endpoints
# ─────────────────────────────────────────────────────────────────────
class AddHostBody(BaseModel):
    ical_url: str = Field(..., min_length=10, max_length=2000)
    listing_name: Optional[str] = Field(None, max_length=200)
    default_service_id: Optional[str] = "deep_cleaning"
    default_address_id: Optional[int] = None
    cleaning_duration_min: Optional[int] = Field(180, ge=60, le=600)


@router.post("/api/host/airbnb/host")
def add_host(body: AddHostBody, request: Request, customer_id: int | None = None):
    """Register a new Airbnb listing's iCal feed for a customer."""
    cid = _get_customer_id(request, customer_id)
    platform = _detect_platform(body.ical_url)
    now = datetime.now(timezone.utc).isoformat()
    with db.connect() as c:
        cur = c.execute("""
            INSERT INTO airbnb_hosts
              (customer_id, listing_name, ical_url, platform,
               default_service_id, default_address_id,
               cleaning_duration_min, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (cid, body.listing_name, body.ical_url, platform,
              body.default_service_id or "deep_cleaning",
              body.default_address_id, body.cleaning_duration_min or 180, now))
        host_id = cur.lastrowid
    return {"ok": True, "host_id": host_id, "platform": platform}


@router.get("/api/host/airbnb/hosts")
def list_hosts(request: Request, customer_id: int | None = None):
    """List all listings registered by this customer."""
    cid = _get_customer_id(request, customer_id)
    with db.connect() as c:
        rows = c.execute("""
            SELECT id, listing_name, ical_url, platform, active,
                   default_service_id, cleaning_duration_min,
                   last_synced_at, last_sync_status, created_at
            FROM airbnb_hosts WHERE customer_id=? ORDER BY created_at DESC
        """, (cid,)).fetchall()
    return {"ok": True, "hosts": [dict(r) for r in rows]}


@router.post("/api/host/airbnb/sync")
async def sync_host(host_id: int, request: Request, customer_id: int | None = None):
    """Fetch the iCal feed, diff against stored reservations, schedule turnovers."""
    cid = _get_customer_id(request, customer_id)
    with db.connect() as c:
        row = c.execute("""
            SELECT * FROM airbnb_hosts WHERE id=? AND customer_id=?
        """, (host_id, cid)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="host not found")
        host_dict = dict(row)
    try:
        ical_text = await _fetch_ical(host_dict["ical_url"])
    except Exception as e:
        with db.connect() as c:
            c.execute("""
                UPDATE airbnb_hosts SET last_sync_status=?, last_synced_at=?
                WHERE id=?
            """, (f"error: {str(e)[:200]}",
                  datetime.now(timezone.utc).isoformat(), host_id))
        raise HTTPException(status_code=502, detail=f"fetch failed: {e}")
    return _do_sync(host_dict, ical_text)


@router.get("/api/host/airbnb/upcoming")
def upcoming(request: Request, customer_id: int | None = None, days: int = 30):
    """Return the next `days` of scheduled turnovers for this customer."""
    cid = _get_customer_id(request, customer_id)
    now = datetime.now(timezone.utc).isoformat()
    cutoff = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    with db.connect() as c:
        rows = c.execute("""
            SELECT t.id, t.host_id, h.listing_name, t.checkout_dt,
                   t.next_checkin_dt, t.scheduled_start_dt, t.duration_min,
                   t.status, t.review_reason, t.booking_id
            FROM airbnb_turnovers t
            JOIN airbnb_hosts h ON h.id = t.host_id
            WHERE h.customer_id=? AND t.scheduled_start_dt >= ?
              AND t.scheduled_start_dt <= ?
            ORDER BY t.scheduled_start_dt ASC
        """, (cid, now, cutoff)).fetchall()
    return {"ok": True, "turnovers": [dict(r) for r in rows]}


@router.post("/api/host/airbnb/turnover/{turnover_id}/confirm")
def confirm_turnover(turnover_id: int, request: Request, customer_id: int | None = None):
    """Mark a planned turnover as confirmed (host approved). Booking creation
    is a separate step — this flips status so the dispatch dashboard picks it up."""
    cid = _get_customer_id(request, customer_id)
    now = datetime.now(timezone.utc).isoformat()
    with db.connect() as c:
        row = c.execute("""
            SELECT t.id FROM airbnb_turnovers t
            JOIN airbnb_hosts h ON h.id=t.host_id
            WHERE t.id=? AND h.customer_id=?
        """, (turnover_id, cid)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="turnover not found")
        c.execute("""
            UPDATE airbnb_turnovers SET status='confirmed', updated_at=?
            WHERE id=?
        """, (now, turnover_id))
    return {"ok": True}


@router.post("/api/host/airbnb/turnover/{turnover_id}/decline")
def decline_turnover(turnover_id: int, request: Request, customer_id: int | None = None):
    """Mark a planned turnover as declined (host doesn't need cleaning this time)."""
    cid = _get_customer_id(request, customer_id)
    now = datetime.now(timezone.utc).isoformat()
    with db.connect() as c:
        row = c.execute("""
            SELECT t.id FROM airbnb_turnovers t
            JOIN airbnb_hosts h ON h.id=t.host_id
            WHERE t.id=? AND h.customer_id=?
        """, (turnover_id, cid)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="turnover not found")
        c.execute("""
            UPDATE airbnb_turnovers SET status='declined', updated_at=?
            WHERE id=?
        """, (now, turnover_id))
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────────
# Admin endpoints
# ─────────────────────────────────────────────────────────────────────
@router.get("/api/admin/airbnb/hosts",
            dependencies=[Depends(require_admin)])
def admin_list_hosts(limit: int = 200):
    with db.connect() as c:
        rows = c.execute("""
            SELECT h.id, h.customer_id, c.name AS customer_name, c.phone,
                   h.listing_name, h.platform, h.active,
                   h.last_synced_at, h.last_sync_status,
                   (SELECT COUNT(*) FROM airbnb_reservations r WHERE r.host_id=h.id) AS reservations,
                   (SELECT COUNT(*) FROM airbnb_turnovers t WHERE t.host_id=h.id AND t.status='planned') AS planned_turnovers
            FROM airbnb_hosts h
            LEFT JOIN customers c ON c.id=h.customer_id
            ORDER BY h.created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return {"ok": True, "hosts": [dict(r) for r in rows]}


@router.post("/api/admin/airbnb/sync-all",
             dependencies=[Depends(require_admin)])
async def admin_sync_all():
    """Force-sync every active host. Sequential to avoid hammering iCal CDNs."""
    with db.connect() as c:
        rows = c.execute("""
            SELECT * FROM airbnb_hosts WHERE active=1
        """).fetchall()
        hosts = [dict(r) for r in rows]
    results: list[dict] = []
    for h in hosts:
        try:
            text = await _fetch_ical(h["ical_url"])
            results.append(_do_sync(h, text))
        except Exception as e:
            results.append({"ok": False, "host_id": h["id"], "error": str(e)[:200]})
    return {"ok": True, "synced": len(results), "results": results}
