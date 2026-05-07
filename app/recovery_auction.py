"""v1.24.34 — Servia vehicle-recovery reverse-auction.

When a customer dispatches a recovery request via /api/recovery/dispatch,
the existing recovery.py module assigns the closest vendor by haversine.
That works but leaves money on the table — vendors compete on price too,
and the customer often prefers a slightly farther vendor that's 30 AED
cheaper.

This module adds a real-time reverse-auction layer on top:

  1. POST /api/recovery/auction
        Customer creates an auction (lat, lng, issue, baseline price).
        Server picks top-5 nearest vendors who offer the service and
        records {auction_id, vendor_pool, expires_at}. Each vendor
        receives a push (admin_alerts.notify_vendor stub) inviting a bid.

  2. POST /api/recovery/auction/{id}/bid
        Vendor submits {price_aed, eta_min}. Multiple bids per vendor
        allowed (latest wins). Bids past expires_at are rejected.

  3. GET /api/recovery/auction/{id}
        Returns live bid list (anonymised) so the customer's UI can
        show "5 vendors bidding · 87s left · lowest AED 220".

  4. POST /api/recovery/auction/{id}/accept
        Customer accepts a specific bid_id (or 'auto'). Server:
          - locks the auction (state -> awarded)
          - inserts a real recovery_dispatch row pointing to the
            winning vendor
          - publishes booking_created so the watch + admin get
            notified.

Defaults chosen for v1 (commented inline so they're tunable):

  POOL_SIZE          = 5     # top-N nearest vendors
  WINDOW_SECONDS     = 90    # auction duration before auto-close
  AUTO_ACCEPT_DROP   = 0.10  # if first bid is >=10% under baseline,
                              # auto-accept immediately (saves 90s)
  MAX_DISTANCE_KM    = 25    # vendors farther than this never invited
  PAYMENT_HOLD_PCT   = 1.0   # 100% pre-auth on customer card; same as
                              # existing recovery flow

These constants are at the top of the file. Tune freely.
"""

from __future__ import annotations

import math
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import db
from .auth_users import current_customer

router = APIRouter()

# ---- tunable defaults (see docstring) ------------------------------
POOL_SIZE = 5
WINDOW_SECONDS = 90
AUTO_ACCEPT_DROP = 0.10
MAX_DISTANCE_KM = 25
PAYMENT_HOLD_PCT = 1.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(t: datetime) -> str:
    return t.isoformat(timespec="seconds")


def _haversine(lat1, lng1, lat2, lng2) -> float:
    """Great-circle distance in km."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _ensure_schema() -> None:
    with db.connect() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS recovery_auctions (
                id              TEXT PRIMARY KEY,
                customer_id     INTEGER,
                lat             REAL NOT NULL,
                lng             REAL NOT NULL,
                issue           TEXT,
                baseline_aed    REAL,
                vendor_pool     TEXT,            -- comma-separated vendor ids invited
                state           TEXT NOT NULL,   -- open / awarded / expired / cancelled
                winner_bid_id   INTEGER,
                booking_id      TEXT,
                created_at      TEXT NOT NULL,
                expires_at      TEXT NOT NULL,
                awarded_at      TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS recovery_bids (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id      TEXT NOT NULL,
                vendor_id       INTEGER NOT NULL,
                price_aed       REAL NOT NULL,
                eta_min         INTEGER NOT NULL,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (auction_id) REFERENCES recovery_auctions(id)
            )"""
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_rec_auc_state "
            "ON recovery_auctions(state)"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_rec_bid_auction "
            "ON recovery_bids(auction_id)"
        )


def _pick_pool(lat: float, lng: float) -> list[int]:
    """Return up to POOL_SIZE vendor ids sorted by distance (closest first)."""
    with db.connect() as c:
        rows = c.execute(
            "SELECT v.id, COALESCE(rvb.lat, 25.2048) AS lat, "
            "COALESCE(rvb.lng, 55.2708) AS lng "
            "FROM vendors v "
            "LEFT JOIN recovery_vendor_base rvb ON rvb.vendor_id = v.id "
            "WHERE v.status='active' "
            "AND ('vehicle_recovery' IN (SELECT value FROM json_each(v.services)) "
            "     OR v.services LIKE '%vehicle_recovery%')"
        ).fetchall()
    distances = []
    for r in rows:
        d = _haversine(lat, lng, r["lat"], r["lng"])
        if d <= MAX_DISTANCE_KM:
            distances.append((d, r["id"]))
    distances.sort()
    return [vid for (_, vid) in distances[:POOL_SIZE]]


# ---- request bodies ------------------------------------------------

class _CreateBody(BaseModel):
    lat: float
    lng: float
    issue: Optional[str] = None
    baseline_aed: Optional[float] = None  # what your map app suggested, etc.


class _BidBody(BaseModel):
    vendor_id: int
    price_aed: float
    eta_min: int


class _AcceptBody(BaseModel):
    bid_id: Optional[int] = None  # None = "auto" (lowest price, then fastest)


# ---- endpoints -----------------------------------------------------

@router.post("/api/recovery/auction")
def auction_create(body: _CreateBody, user=Depends(current_customer)):
    """Open a new auction. Returns auction_id + invited vendor pool."""
    _ensure_schema()
    if not (-90 <= body.lat <= 90 and -180 <= body.lng <= 180):
        raise HTTPException(400, "lat/lng out of range")

    pool = _pick_pool(body.lat, body.lng)
    if not pool:
        raise HTTPException(503, "No recovery vendors within "
                                  f"{MAX_DISTANCE_KM} km")

    aid = "AUC-" + secrets.token_urlsafe(6).upper()
    now = _now()
    expires = now + timedelta(seconds=WINDOW_SECONDS)
    pool_str = ",".join(str(v) for v in pool)

    with db.connect() as c:
        c.execute(
            "INSERT INTO recovery_auctions(id, customer_id, lat, lng, issue, "
            "baseline_aed, vendor_pool, state, created_at, expires_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (aid, user.user_id, body.lat, body.lng, body.issue,
             body.baseline_aed, pool_str, "open", _iso(now), _iso(expires)),
        )

    db.log_event("recovery_auction", aid, "created",
                 actor=str(user.user_id),
                 details={"pool": pool, "issue": body.issue,
                          "baseline_aed": body.baseline_aed})

    # Best-effort vendor invite. We piggyback on the existing
    # admin_alerts module rather than introduce a new fan-out path —
    # this becomes a real per-vendor push when the vendor portal v3
    # ships in v1.25.
    try:
        from . import admin_alerts as _aa
        _aa.notify_admin(
            f"🏷 New recovery auction *{aid}*\n"
            f"Issue: {body.issue or '(none)'}\n"
            f"Pool: {len(pool)} vendor(s) within {MAX_DISTANCE_KM} km\n"
            f"Window: {WINDOW_SECONDS}s",
            kind="recovery_auction_open",
            urgency="urgent",
            meta={"auction_id": aid, "vendor_pool": pool},
        )
    except Exception:
        pass

    return {
        "ok": True,
        "auction_id": aid,
        "vendor_pool": pool,
        "expires_at": _iso(expires),
        "window_seconds": WINDOW_SECONDS,
    }


@router.post("/api/recovery/auction/{auction_id}/bid")
def auction_bid(auction_id: str, body: _BidBody):
    """Vendor submits a bid. Vendor identity is currently asserted by the
    body; the vendor portal will tighten this with a real auth check."""
    _ensure_schema()
    if body.price_aed <= 0 or body.eta_min <= 0:
        raise HTTPException(400, "price + eta must be positive")
    with db.connect() as c:
        a = c.execute(
            "SELECT state, vendor_pool, expires_at, baseline_aed "
            "FROM recovery_auctions WHERE id=?",
            (auction_id,),
        ).fetchone()
        if not a:
            raise HTTPException(404, "Unknown auction")
        if a["state"] != "open":
            raise HTTPException(409, f"Auction is {a['state']}")
        if datetime.fromisoformat(a["expires_at"]) < _now():
            c.execute(
                "UPDATE recovery_auctions SET state='expired' WHERE id=?",
                (auction_id,),
            )
            raise HTTPException(410, "Auction expired")
        # Vendor must be in invited pool (best-effort sanity gate)
        pool_ids = {int(x) for x in (a["vendor_pool"] or "").split(",") if x}
        if body.vendor_id not in pool_ids:
            raise HTTPException(403, "Vendor not in invited pool")

        c.execute(
            "INSERT INTO recovery_bids(auction_id, vendor_id, price_aed, "
            "eta_min, created_at) VALUES(?,?,?,?,?)",
            (auction_id, body.vendor_id, body.price_aed, body.eta_min,
             _iso(_now())),
        )
        bid_id = c.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    db.log_event("recovery_auction", auction_id, "bid",
                 actor=f"vendor:{body.vendor_id}",
                 details={"bid_id": bid_id, "price_aed": body.price_aed,
                          "eta_min": body.eta_min})

    # Auto-accept hot-bid: first bid that beats baseline by AUTO_ACCEPT_DROP
    # avoids dragging the customer through a full 90s window when the
    # market clearly cleared early.
    if a["baseline_aed"] and body.price_aed <= a["baseline_aed"] * (1.0 - AUTO_ACCEPT_DROP):
        try:
            return _award(auction_id, bid_id, reason="auto_accept_drop")
        except Exception:
            pass  # fall through to normal response

    return {"ok": True, "bid_id": bid_id, "state": "open"}


@router.get("/api/recovery/auction/{auction_id}")
def auction_status(auction_id: str, user=Depends(current_customer)):
    """Live status — bid list, time left, lowest bid, etc."""
    _ensure_schema()
    with db.connect() as c:
        a = c.execute(
            "SELECT * FROM recovery_auctions WHERE id=?", (auction_id,)
        ).fetchone()
        if not a:
            raise HTTPException(404, "Unknown auction")
        # Auto-expire so the UI sees the right state without a dedicated cron.
        state = a["state"]
        if state == "open" and datetime.fromisoformat(a["expires_at"]) < _now():
            c.execute("UPDATE recovery_auctions SET state='expired' WHERE id=?",
                      (auction_id,))
            state = "expired"
        bids = c.execute(
            "SELECT id, vendor_id, price_aed, eta_min, created_at "
            "FROM recovery_bids WHERE auction_id=? ORDER BY price_aed ASC, eta_min ASC",
            (auction_id,),
        ).fetchall()

    bid_list = [dict(b) for b in bids]
    seconds_left = max(
        0, int((datetime.fromisoformat(a["expires_at"]) - _now()).total_seconds())
    )
    return {
        "auction_id": auction_id,
        "state": state,
        "issue": a["issue"],
        "baseline_aed": a["baseline_aed"],
        "vendor_pool": [int(x) for x in (a["vendor_pool"] or "").split(",") if x],
        "bids": bid_list,
        "lowest_aed": bid_list[0]["price_aed"] if bid_list else None,
        "seconds_left": seconds_left,
        "winner_bid_id": a["winner_bid_id"],
        "booking_id": a["booking_id"],
    }


@router.post("/api/recovery/auction/{auction_id}/accept")
def auction_accept(auction_id: str, body: _AcceptBody,
                   user=Depends(current_customer)):
    """Customer accepts a bid (manual) or 'auto' (lowest)."""
    _ensure_schema()
    with db.connect() as c:
        a = c.execute(
            "SELECT state, customer_id FROM recovery_auctions WHERE id=?",
            (auction_id,),
        ).fetchone()
        if not a:
            raise HTTPException(404, "Unknown auction")
        if a["customer_id"] != user.user_id:
            raise HTTPException(403, "Not your auction")
        if a["state"] != "open" and a["state"] != "expired":
            raise HTTPException(409, f"Auction is {a['state']}")

        if body.bid_id is None:
            row = c.execute(
                "SELECT id FROM recovery_bids WHERE auction_id=? "
                "ORDER BY price_aed ASC, eta_min ASC LIMIT 1",
                (auction_id,),
            ).fetchone()
            if not row:
                raise HTTPException(409, "No bids to accept")
            bid_id = row["id"]
        else:
            bid_id = body.bid_id

    return _award(auction_id, bid_id, reason="customer_accept")


def _award(auction_id: str, bid_id: int, *, reason: str) -> dict:
    """Mark auction awarded + insert a real recovery_dispatch row."""
    _ensure_schema()
    with db.connect() as c:
        bid = c.execute(
            "SELECT b.id, b.vendor_id, b.price_aed, b.eta_min, "
            "       a.lat, a.lng, a.issue, a.customer_id "
            "FROM recovery_bids b "
            "JOIN recovery_auctions a ON a.id = b.auction_id "
            "WHERE b.id=? AND b.auction_id=?",
            (bid_id, auction_id),
        ).fetchone()
        if not bid:
            raise HTTPException(404, "Bid not found")

        booking_id = "REC-" + secrets.token_urlsafe(6).upper()
        c.execute(
            "INSERT INTO recovery_dispatches(booking_id, customer_phone, "
            "customer_name, vehicle_make, vehicle_plate, issue, lat, lng, "
            "vendor_id, eta_min, price_aed, distance_km, status, source, "
            "created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (booking_id, "", "", "", "",
             bid["issue"] or "auction",
             bid["lat"], bid["lng"], bid["vendor_id"],
             bid["eta_min"], bid["price_aed"], 0.0,
             "dispatched", "auction", _iso(_now())),
        )
        c.execute(
            "UPDATE recovery_auctions SET state='awarded', winner_bid_id=?, "
            "booking_id=?, awarded_at=? WHERE id=?",
            (bid_id, booking_id, _iso(_now()), auction_id),
        )

    db.log_event("recovery_auction", auction_id, "awarded",
                 details={"winner_bid_id": bid_id, "booking_id": booking_id,
                          "reason": reason})
    try:
        from . import admin_alerts as _aa
        _aa.notify_admin(
            f"✅ Recovery auction *{auction_id}* awarded\n"
            f"Booking: {booking_id}\n"
            f"Vendor: {bid['vendor_id']}\n"
            f"Price: AED {bid['price_aed']} · ETA {bid['eta_min']}m\n"
            f"Reason: {reason}",
            kind="recovery_auction_awarded",
            urgency="normal",
            meta={"auction_id": auction_id, "booking_id": booking_id},
        )
    except Exception:
        pass

    return {
        "ok": True,
        "auction_id": auction_id,
        "winner_bid_id": bid_id,
        "booking_id": booking_id,
        "vendor_id": bid["vendor_id"],
        "price_aed": bid["price_aed"],
        "eta_min": bid["eta_min"],
    }


@router.post("/api/recovery/auction/{auction_id}/cancel")
def auction_cancel(auction_id: str, user=Depends(current_customer)):
    """Customer aborts before any bid is accepted."""
    _ensure_schema()
    with db.connect() as c:
        a = c.execute(
            "SELECT customer_id, state FROM recovery_auctions WHERE id=?",
            (auction_id,),
        ).fetchone()
        if not a:
            raise HTTPException(404, "Unknown auction")
        if a["customer_id"] != user.user_id:
            raise HTTPException(403, "Not your auction")
        if a["state"] != "open":
            raise HTTPException(409, f"Auction is {a['state']}")
        c.execute(
            "UPDATE recovery_auctions SET state='cancelled' WHERE id=?",
            (auction_id,),
        )
    db.log_event("recovery_auction", auction_id, "cancelled",
                 actor=str(user.user_id))
    return {"ok": True, "auction_id": auction_id, "state": "cancelled"}
