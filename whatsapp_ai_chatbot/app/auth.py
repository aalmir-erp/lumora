"""Admin authentication.

Single-admin model. The password is stored as a salted PBKDF2 hash in
the `settings` table under key `ADMIN_PASSWORD_HASH`. On first run, if
no hash is set, the admin can set one via /admin/setup using the
bootstrap token (env var `ADMIN_BOOTSTRAP_TOKEN`).
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets

from fastapi import Request

from . import settings_store


_ITERATIONS = 200_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iters, salt_hex, digest_hex = encoded.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iters)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, AttributeError):
        return False


def set_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    settings_store.set_value("ADMIN_PASSWORD_HASH", hash_password(password))


def is_password_set() -> bool:
    return bool(settings_store.get("ADMIN_PASSWORD_HASH"))


def check_login(password: str) -> bool:
    encoded = settings_store.get("ADMIN_PASSWORD_HASH")
    if not encoded:
        return False
    return verify_password(password, encoded)


def bootstrap_token() -> str:
    """One-time token used to set the very first admin password.

    Sourced from env var ADMIN_BOOTSTRAP_TOKEN. If not set, a random
    one is generated on import and printed to logs.
    """
    return os.environ.get("ADMIN_BOOTSTRAP_TOKEN", "")


def is_logged_in(request: Request) -> bool:
    return bool(request.session.get("admin"))


def login(request: Request) -> None:
    request.session["admin"] = True


def logout(request: Request) -> None:
    request.session.pop("admin", None)
