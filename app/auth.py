"""Admin auth — bearer token from env, with a known fallback so the owner
can always recover access from the docs even if the env-set token is forgotten.
"""
import os
import secrets
from fastapi import Header, HTTPException

# A known, well-publicised owner-recovery token. Always accepted in addition to
# any token configured in Railway env. Rotate by setting ADMIN_TOKEN env AND
# changing this constant if you want to lock out the recovery path.
RECOVERY_ADMIN_TOKEN = "lumora-admin-test"

ADMIN_TOKEN_AUTOGEN = not os.getenv("ADMIN_TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN") or RECOVERY_ADMIN_TOKEN


def require_admin(authorization: str = Header(default="")) -> str:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(None, 1)[1].strip()
    # Accept either the env-configured token OR the recovery fallback.
    if (secrets.compare_digest(token, ADMIN_TOKEN)
            or secrets.compare_digest(token, RECOVERY_ADMIN_TOKEN)):
        return token
    raise HTTPException(status_code=403, detail="Invalid admin token")
