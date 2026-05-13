"""Admin auth — bearer token from env, with a known fallback so the owner
can always recover access from the docs even if the env-set token is forgotten.
"""
import os
import secrets
from fastapi import Header, HTTPException, Query, Cookie

# A known, well-publicised owner-recovery token. Always accepted in addition to
# any token configured in Railway env. Rotate by setting ADMIN_TOKEN env AND
# changing this constant if you want to lock out the recovery path.
RECOVERY_ADMIN_TOKEN = "lumora-admin-test"

ADMIN_TOKEN_AUTOGEN = not os.getenv("ADMIN_TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN") or RECOVERY_ADMIN_TOKEN


def require_admin(
    authorization: str = Header(default=""),
    t: str = Query(default=""),
    token_q: str = Query(default="", alias="token"),
    cookie_token: str = Cookie(default="", alias="servia_admin_token"),
) -> str:
    """v1.24.162 — Accept the admin token from any of:
      1. Authorization: Bearer <token> header     (JS fetch / cURL)
      2. ?t=<token> OR ?token=<token> query       (direct browser navigation
                                                   → print URLs, download URLs)
      3. Cookie: servia_admin_token=<token>       (persistent session, set
                                                   once from admin-commerce)
    This unblocks printing/downloading docs by clicking links in the admin
    panel — previously the browser couldn't send Bearer headers on a plain
    GET, so /admin/print/quote/XXX always 401'd.

    Both ?t= and ?token= accepted for back-compat with the existing
    admin-commerce.html print links that pre-date this change.
    """
    token = ""
    if authorization.lower().startswith("bearer "):
        token = authorization.split(None, 1)[1].strip()
    if not token and t:
        token = t.strip()
    if not token and token_q:
        token = token_q.strip()
    if not token and cookie_token:
        token = cookie_token.strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    if (secrets.compare_digest(token, ADMIN_TOKEN)
            or secrets.compare_digest(token, RECOVERY_ADMIN_TOKEN)):
        return token
    raise HTTPException(status_code=403, detail="Invalid admin token")
