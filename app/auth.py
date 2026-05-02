"""Simple admin auth — single shared bearer token from env. Good enough for v1.

For multi-user: replace with users table + bcrypt + JWT.
"""
import os
import secrets
from fastapi import Header, HTTPException

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN") or "lumora-admin-" + secrets.token_urlsafe(8)


def require_admin(authorization: str = Header(default="")) -> str:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(None, 1)[1].strip()
    if not secrets.compare_digest(token, ADMIN_TOKEN):
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return token
