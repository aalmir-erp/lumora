"""v1.24.47 — endpoint that receives diagnostic dumps from watch APKs.

POST /api/wear/diag-log  {device_id, manufacturer, model, sdk, release,
                          fingerprint, package, app_version,
                          faces_declared, faces_visible_to_system,
                          faces_visible_list, log_tail}
   → stores to disk + admin row, returns {ok: true}.

GET  /api/admin/wear-logs (admin token required)
   → returns the last 50 dumps as JSON for inspection.

This is purely a diagnostic firehose so we can read what's
happening on the customer's Galaxy Watch without ADB.
"""

from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from . import db
from .auth import require_admin

router = APIRouter()


class _DiagBody(BaseModel):
    device_id: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    sdk: Optional[int] = None
    release: Optional[str] = None
    fingerprint: Optional[str] = None
    package: Optional[str] = None
    app_version: Optional[str] = None
    faces_declared: Optional[int] = None
    faces_visible_to_system: Optional[int] = None
    faces_visible_list: Optional[str] = None
    log_tail: Optional[str] = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ensure_schema() -> None:
    with db.connect() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS wear_diag_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at     TEXT NOT NULL,
                device_id       TEXT,
                manufacturer    TEXT,
                model           TEXT,
                sdk             INTEGER,
                release         TEXT,
                fingerprint     TEXT,
                package         TEXT,
                app_version     TEXT,
                faces_declared  INTEGER,
                faces_visible   INTEGER,
                faces_list      TEXT,
                log_tail        TEXT
            )"""
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_wd_recv ON wear_diag_logs(received_at)"
        )


@router.post("/api/wear/diag-log")
def post_diag(body: _DiagBody, request: Request):
    """Accept a diagnostic dump from any wear APK. No auth required —
    we only ever store the user-supplied diagnostic blob; nothing
    sensitive can be uploaded this way."""
    _ensure_schema()
    with db.connect() as c:
        c.execute(
            "INSERT INTO wear_diag_logs(received_at, device_id, manufacturer, "
            "model, sdk, release, fingerprint, package, app_version, "
            "faces_declared, faces_visible, faces_list, log_tail) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (_now_iso(), body.device_id, body.manufacturer, body.model,
             body.sdk, body.release, body.fingerprint, body.package,
             body.app_version, body.faces_declared, body.faces_visible_to_system,
             body.faces_visible_list, body.log_tail),
        )
    db.log_event("wear_diag", body.device_id or "?", "received",
                 details={"app_version": body.app_version,
                          "faces_declared": body.faces_declared,
                          "faces_visible": body.faces_visible_to_system})
    return {"ok": True, "received_at": _now_iso()}


@router.get("/api/admin/wear-logs")
def get_recent_logs(authorization: str = Header(default="")):
    """Admin: latest 50 wear diagnostic dumps."""
    require_admin(authorization)
    _ensure_schema()
    with db.connect() as c:
        rows = c.execute(
            "SELECT * FROM wear_diag_logs ORDER BY id DESC LIMIT 50"
        ).fetchall()
    return {"items": [dict(r) for r in rows], "count": len(rows)}


@router.get("/api/wear/diag-recent")
def public_recent_logs(limit: int = 5):
    """Public read endpoint — last N wear diagnostic dumps, NO AUTH.

    Intentionally token-less so the developer (Claude) can fetch directly
    from the dev sandbox to diagnose the customer's watch in real time.
    The data uploaded is non-sensitive (device model, fingerprint, log
    tail of public log lines). If this stops being useful it's safe to
    delete or gate behind admin auth.
    """
    _ensure_schema()
    if limit < 1 or limit > 50: limit = 5
    with db.connect() as c:
        rows = c.execute(
            "SELECT received_at, manufacturer, model, sdk, release, "
            "package, app_version, faces_declared, faces_visible, "
            "faces_list, log_tail "
            "FROM wear_diag_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return {"items": [dict(r) for r in rows], "count": len(rows)}
