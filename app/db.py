"""SQLite persistence. Single file, mounted on Railway as a volume.

Tables:
  bookings       — customer bookings + status
  quotes         — quote line items (1:N with bookings is via booking_id)
  invoices       — invoices, payment status, signature
  conversations  — flat message log (one row per turn) for admin review
  events         — audit log (status changes, agent takeovers, payments)
  config         — runtime-editable key/value (admin overrides for pricing, etc.)
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", "/tmp/lumora.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()


SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings (
    id TEXT PRIMARY KEY,
    service_id TEXT NOT NULL,
    target_date TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    bedrooms INTEGER,
    hours INTEGER,
    units INTEGER,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    estimated_total REAL,
    currency TEXT DEFAULT 'AED',
    language TEXT DEFAULT 'en',
    source TEXT DEFAULT 'web',
    session_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bookings_phone ON bookings(phone);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);

CREATE TABLE IF NOT EXISTS quotes (
    id TEXT PRIMARY KEY,
    booking_id TEXT,
    service_id TEXT NOT NULL,
    breakdown_json TEXT NOT NULL,
    subtotal REAL NOT NULL,
    discount REAL DEFAULT 0,
    total REAL NOT NULL,
    currency TEXT DEFAULT 'AED',
    valid_until TEXT,
    status TEXT DEFAULT 'sent',
    signature_data_url TEXT,
    signed_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(id)
);
CREATE INDEX IF NOT EXISTS idx_quotes_booking ON quotes(booking_id);

CREATE TABLE IF NOT EXISTS invoices (
    id TEXT PRIMARY KEY,
    booking_id TEXT,
    quote_id TEXT,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'AED',
    payment_status TEXT DEFAULT 'unpaid',
    payment_url TEXT,
    paid_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(id),
    FOREIGN KEY (quote_id) REFERENCES quotes(id)
);
CREATE INDEX IF NOT EXISTS idx_invoices_booking ON invoices(booking_id);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tool_calls_json TEXT,
    channel TEXT DEFAULT 'web',
    phone TEXT,
    agent_handled INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conv_phone ON conversations(phone);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor TEXT,
    details_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_takeovers (
    session_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT
);

-- ---------- accounts + auth ----------

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT UNIQUE NOT NULL,
    name TEXT,
    email TEXT,
    language TEXT DEFAULT 'en',
    created_at TEXT NOT NULL,
    last_seen_at TEXT
);

CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    company TEXT,
    rating REAL DEFAULT 5.0,
    completed_jobs INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    is_approved INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_vendors_email ON vendors(email);

CREATE TABLE IF NOT EXISTS vendor_services (
    vendor_id INTEGER NOT NULL,
    service_id TEXT NOT NULL,
    area TEXT DEFAULT '*',
    PRIMARY KEY (vendor_id, service_id, area),
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id TEXT NOT NULL,
    vendor_id INTEGER NOT NULL,
    status TEXT DEFAULT 'assigned',
    payout_amount REAL,
    notes TEXT,
    claimed_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (booking_id) REFERENCES bookings(id),
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);
CREATE INDEX IF NOT EXISTS idx_assn_vendor ON assignments(vendor_id);
CREATE INDEX IF NOT EXISTS idx_assn_booking ON assignments(booking_id);

CREATE TABLE IF NOT EXISTS otps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_otps_phone ON otps(phone);

CREATE TABLE IF NOT EXISTS auth_sessions (
    token TEXT PRIMARY KEY,
    user_type TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_auth_user ON auth_sessions(user_type, user_id);

CREATE TABLE IF NOT EXISTS saved_addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    label TEXT,
    address TEXT NOT NULL,
    area TEXT,
    is_default INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_addr_customer ON saved_addresses(customer_id);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id TEXT NOT NULL,
    customer_id INTEGER,
    vendor_id INTEGER,
    service_id TEXT NOT NULL,
    stars INTEGER NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);
CREATE INDEX IF NOT EXISTS idx_reviews_service ON reviews(service_id);
CREATE INDEX IF NOT EXISTS idx_reviews_vendor ON reviews(vendor_id);

"""


def init_db() -> None:
    with connect() as c:
        c.executescript(SCHEMA)
        # Idempotent column additions for vendor_services price config
        for stmt in (
            "ALTER TABLE vendor_services ADD COLUMN price_aed REAL",
            "ALTER TABLE vendor_services ADD COLUMN price_unit TEXT DEFAULT 'fixed'",
            "ALTER TABLE vendor_services ADD COLUMN sla_hours INTEGER DEFAULT 24",
            "ALTER TABLE vendor_services ADD COLUMN active INTEGER DEFAULT 1",
            "ALTER TABLE vendor_services ADD COLUMN notes TEXT",
            "ALTER TABLE bookings ADD COLUMN recurring TEXT",
            "ALTER TABLE bookings ADD COLUMN photos_json TEXT",
            "ALTER TABLE bookings ADD COLUMN cancelled_at TEXT",
            "ALTER TABLE bookings ADD COLUMN cancellation_reason TEXT",
        ):
            try:
                c.execute(stmt)
            except Exception:  # noqa: BLE001
                pass  # column exists


@contextmanager
def connect():
    with _lock:
        conn = sqlite3.connect(DB_PATH, isolation_level=None, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        try:
            yield conn
        finally:
            conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    for k, v in list(d.items()):
        if k.endswith("_json") and v:
            try:
                d[k[:-5]] = json.loads(v)
            except Exception:  # noqa: BLE001
                pass
    return d


def rows_to_dicts(rows) -> list[dict]:
    return [row_to_dict(r) for r in rows]


# ---------- Config helpers ----------
def cfg_get(key: str, default=None):
    with connect() as c:
        r = c.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
    if not r:
        return default
    try:
        return json.loads(r["value"])
    except Exception:  # noqa: BLE001
        return r["value"]


def cfg_set(key: str, value) -> None:
    import datetime as _dt
    val = json.dumps(value) if not isinstance(value, str) else value
    with connect() as c:
        c.execute(
            "INSERT INTO config(key,value,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, val, _dt.datetime.utcnow().isoformat() + "Z"),
        )


def cfg_all() -> dict:
    with connect() as c:
        rows = c.execute("SELECT key, value FROM config").fetchall()
    out = {}
    for r in rows:
        try:
            out[r["key"]] = json.loads(r["value"])
        except Exception:  # noqa: BLE001
            out[r["key"]] = r["value"]
    return out


# ---------- Event log ----------
def log_event(entity_type: str, entity_id: str, action: str,
              actor: str | None = None, details: dict | None = None) -> None:
    import datetime as _dt
    with connect() as c:
        c.execute(
            "INSERT INTO events(entity_type, entity_id, action, actor, details_json, created_at) "
            "VALUES(?,?,?,?,?,?)",
            (entity_type, entity_id, action, actor,
             json.dumps(details) if details else None,
             _dt.datetime.utcnow().isoformat() + "Z"),
        )


# Initialize on import.
init_db()
