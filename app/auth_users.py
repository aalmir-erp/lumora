"""Authentication: customer phone+OTP and vendor email+password.

Sessions are opaque tokens stored in `auth_sessions`. 30-day expiry.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel, Field

from . import db


SESSION_TTL_DAYS = 30
OTP_TTL_MIN = 10
SCRYPT_PARAMS = dict(n=2**14, r=8, p=1, dklen=64)


def _now() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


# ---------- password hashing (stdlib scrypt; no extra deps) ----------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT_PARAMS)
    return f"scrypt${salt.hex()}${h.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, salt_hex, hash_hex = stored.split("$", 2)
        if algo != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        h = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT_PARAMS)
        return hmac.compare_digest(h, expected)
    except Exception:
        return False


# ---------- OTP ----------
def _hash_otp(code: str, phone: str) -> str:
    secret = os.getenv("OTP_PEPPER", "lumora-default-pepper")
    return hashlib.sha256(f"{secret}|{phone}|{code}".encode()).hexdigest()


def issue_otp(phone: str) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = (_dt.datetime.utcnow() + _dt.timedelta(minutes=OTP_TTL_MIN)).isoformat() + "Z"
    with db.connect() as c:
        c.execute(
            "INSERT INTO otps(phone, code_hash, expires_at, created_at) VALUES(?,?,?,?)",
            (phone, _hash_otp(code, phone), expires_at, _now()),
        )
    db.log_event("otp", phone, "issued")
    return code


def verify_otp(phone: str, code: str) -> bool:
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, code_hash, expires_at, used_at FROM otps WHERE phone=? "
            "ORDER BY id DESC LIMIT 5",
            (phone,),
        ).fetchall()
    target = _hash_otp(code, phone)
    now = _dt.datetime.utcnow().isoformat() + "Z"
    for r in rows:
        if r["used_at"]:
            continue
        if r["expires_at"] < now:
            continue
        if hmac.compare_digest(r["code_hash"], target):
            with db.connect() as c:
                c.execute("UPDATE otps SET used_at=? WHERE id=?", (_now(), r["id"]))
            return True
    return False


# ---------- session tokens ----------
def create_session(user_type: str, user_id: int) -> str:
    token = "lt_" + secrets.token_urlsafe(32)
    expires = (_dt.datetime.utcnow() + _dt.timedelta(days=SESSION_TTL_DAYS)).isoformat() + "Z"
    with db.connect() as c:
        c.execute(
            "INSERT INTO auth_sessions(token, user_type, user_id, expires_at, created_at) "
            "VALUES(?,?,?,?,?)",
            (token, user_type, user_id, expires, _now()),
        )
    return token


def revoke_session(token: str) -> None:
    with db.connect() as c:
        c.execute("DELETE FROM auth_sessions WHERE token=?", (token,))


@dataclass
class AuthedUser:
    user_type: str          # 'customer' or 'vendor'
    user_id: int
    record: dict


def _resolve_user(user_type: str, user_id: int) -> dict | None:
    table = "customers" if user_type == "customer" else "vendors"
    with db.connect() as c:
        r = c.execute(f"SELECT * FROM {table} WHERE id=?", (user_id,)).fetchone()
    return db.row_to_dict(r) if r else None


def lookup_session(token: str) -> AuthedUser | None:
    if not token:
        return None
    now = _dt.datetime.utcnow().isoformat() + "Z"
    with db.connect() as c:
        r = c.execute(
            "SELECT user_type, user_id FROM auth_sessions WHERE token=? AND expires_at>?",
            (token, now),
        ).fetchone()
    if not r:
        return None
    rec = _resolve_user(r["user_type"], r["user_id"])
    if not rec:
        return None
    return AuthedUser(user_type=r["user_type"], user_id=r["user_id"], record=rec)


# ---------- FastAPI dependencies ----------
def _bearer(authorization: str = Header(default="")) -> str:
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return ""


def current_user(authorization: str = Header(default="")) -> AuthedUser:
    user = lookup_session(_bearer(authorization))
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")
    return user


def current_customer(user: AuthedUser = Depends(current_user)) -> AuthedUser:
    if user.user_type != "customer":
        raise HTTPException(status_code=403, detail="customer login required")
    return user


def current_vendor(user: AuthedUser = Depends(current_user)) -> AuthedUser:
    if user.user_type != "vendor":
        raise HTTPException(status_code=403, detail="vendor login required")
    if not user.record.get("is_approved", 1):
        raise HTTPException(status_code=403, detail="vendor account pending approval")
    return user


# ---------- public API request models ----------
class OtpStartReq(BaseModel):
    phone: str = Field(..., min_length=4, max_length=20)
    name: str | None = None
    language: str | None = "en"


class OtpVerifyReq(BaseModel):
    phone: str
    code: str = Field(..., min_length=4, max_length=8)


class VendorLoginReq(BaseModel):
    email: str
    password: str


class VendorRegisterReq(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    name: str
    phone: str | None = None
    company: str | None = None
    services: list[str] = []
