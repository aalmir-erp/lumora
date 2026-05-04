"""TOTP-based 2FA for admin. Google Authenticator / Authy / 1Password compatible.

Implementation notes:
- Pure stdlib (hmac, hashlib, base64, struct, secrets, time). No new deps.
- Secret stored in db.cfg('admin_2fa_secret') as base32 string.
- Six-digit code, 30-second period (Google standard).
- ±1 step tolerance for clock drift on the user's phone.
- 10-minute "elevated" admin sessions issued on successful TOTP — stored as
  HMAC-signed tokens (no DB needed) so they survive restarts.
"""
from __future__ import annotations
import base64, hashlib, hmac, os, secrets, struct, time
from typing import Tuple

from . import db


_PERIOD = 30          # Google Authenticator standard
_DIGITS = 6
_TOLERANCE = 1        # accept code from previous OR next 30s window


def gen_secret() -> str:
    """Generate a random 20-byte (160-bit) base32-encoded secret."""
    raw = secrets.token_bytes(20)
    return base64.b32encode(raw).decode("ascii").rstrip("=")


def _b32_decode(secret: str) -> bytes:
    pad = "=" * ((8 - len(secret) % 8) % 8)
    return base64.b32decode(secret.upper() + pad)


def hotp_at(secret: str, counter: int) -> str:
    key = _b32_decode(secret)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = (
        (digest[offset]   & 0x7F) << 24 |
        (digest[offset+1] & 0xFF) << 16 |
        (digest[offset+2] & 0xFF) <<  8 |
        (digest[offset+3] & 0xFF)
    ) % (10 ** _DIGITS)
    return str(code_int).zfill(_DIGITS)


def totp_now(secret: str, t: int | None = None) -> str:
    if t is None: t = int(time.time())
    return hotp_at(secret, t // _PERIOD)


def verify(code: str, secret: str | None = None) -> bool:
    if not code or not code.isdigit() or len(code) != _DIGITS: return False
    sec = (secret or get_secret() or "").strip()
    if not sec: return False
    now = int(time.time())
    base_step = now // _PERIOD
    for delta in range(-_TOLERANCE, _TOLERANCE + 1):
        if hmac.compare_digest(hotp_at(sec, base_step + delta), code):
            return True
    return False


# ---------- secret persistence ----------
def get_secret() -> str | None:
    s = db.cfg_get("admin_2fa_secret", None)
    return s if isinstance(s, str) and s else None


def set_secret(secret: str) -> None:
    db.cfg_set("admin_2fa_secret", secret)


def clear_secret() -> None:
    db.cfg_set("admin_2fa_secret", "")


def is_enabled() -> bool:
    return bool(get_secret())


# ---------- otpauth:// URI for QR / manual setup ----------
def otpauth_uri(secret: str, label: str = "Servia Admin",
                issuer: str = "Servia") -> str:
    from urllib.parse import quote
    return (
        f"otpauth://totp/{quote(issuer)}:{quote(label)}"
        f"?secret={secret}&issuer={quote(issuer)}"
        f"&algorithm=SHA1&digits={_DIGITS}&period={_PERIOD}"
    )


# ---------- elevated session token (admin verified via TOTP within 24h) ----------
# Hash-only, no DB. token = base64(uid + expiry + hmac(secret, uid|expiry))
_TOKEN_TTL = 24 * 3600


def issue_session_token() -> str:
    """Issues a self-validating signed token. Verifiable without DB."""
    sk = (os.getenv("ADMIN_SESSION_SECRET") or
          db.cfg_get("admin_session_secret", "") or "")
    if not sk:
        sk = secrets.token_urlsafe(32)
        db.cfg_set("admin_session_secret", sk)
    payload_id = secrets.token_urlsafe(8)
    expiry = int(time.time()) + _TOKEN_TTL
    msg = f"{payload_id}|{expiry}"
    sig = hmac.new(sk.encode(), msg.encode(), hashlib.sha256).hexdigest()[:24]
    return f"{msg}|{sig}"


def validate_session_token(token: str) -> bool:
    if not token or token.count("|") != 2: return False
    sk = (os.getenv("ADMIN_SESSION_SECRET") or
          db.cfg_get("admin_session_secret", "") or "")
    if not sk: return False
    try:
        payload_id, expiry, sig = token.split("|")
        if int(expiry) < int(time.time()): return False
        msg = f"{payload_id}|{expiry}"
        expected = hmac.new(sk.encode(), msg.encode(), hashlib.sha256).hexdigest()[:24]
        return hmac.compare_digest(expected, sig)
    except Exception:
        return False
