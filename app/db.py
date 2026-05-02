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
"""


def init_db() -> None:
    with connect() as c:
        c.executescript(SCHEMA)


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
