"""SQLite database — engine, schema, and migrations.

Single-file SQLite is plenty for chatbot scale (orders + settings +
conversations). Mount a Railway volume at the directory containing
the DB to persist across redeploys.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.environ.get("DB_PATH", "data/aalmir_bot.db"))


def init() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                wa_id         TEXT NOT NULL,
                customer_name TEXT,
                company       TEXT,
                phone         TEXT,
                product       TEXT,
                grade         TEXT,
                dimensions    TEXT,
                quantity      TEXT,
                delivery      TEXT,
                notes         TEXT,
                raw_summary   TEXT,
                status        TEXT NOT NULL DEFAULT 'new',
                created_at    REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_orders_wa_id ON orders(wa_id);
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

            CREATE TABLE IF NOT EXISTS conversations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                wa_id       TEXT NOT NULL,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                created_at  REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_conv_wa_id ON conversations(wa_id, id);

            CREATE TABLE IF NOT EXISTS kb_blocks (
                slug       TEXT PRIMARY KEY,
                title      TEXT NOT NULL,
                content    TEXT NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pause_flags (
                wa_id      TEXT PRIMARY KEY,
                until_ts   REAL NOT NULL,
                reason     TEXT
            );
            """
        )


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
    finally:
        conn.close()
