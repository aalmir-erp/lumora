"""UAE phone normalisation + validation. Mirrors web/uae-phone.js so client
and server agree on what counts as a valid mobile number.

UAE mobile rules:
  - Country code: +971
  - National prefix when no country code: 0
  - Mobile starts with 5 followed by carrier digit 0/2/4/5/6/8/9
  - 7 trailing digits

Canonical form: +9715XXXXXXXX (13 chars total)
"""
from __future__ import annotations
import re

# Public, friendly error message used by the API + the chat bot
INVALID_MSG = ("Please enter a valid UAE mobile number — it must start with "
               "+971 or 05 (e.g. +971501234567 or 0501234567).")

_E164 = re.compile(r"^\+9715[0245689]\d{7}$")


def normalize(raw: str | None) -> str | None:
    """Returns the canonical +9715XXXXXXXX form or None if invalid."""
    if raw is None: return None
    s = str(raw).strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not s: return None
    # 00971... → +971...
    if s.startswith("00971"): s = "+" + s[2:]
    # 971... (no +) → +971...
    elif s.startswith("971") and not s.startswith("+971"):
        s = "+" + s
    # 05X... → +9715X...
    elif s.startswith("05"):
        s = "+971" + s[1:]
    # 5X... bare local → +9715X...
    elif re.match(r"^5[0245689]\d{7}$", s):
        s = "+971" + s
    return s if _E164.match(s) else None


def is_valid(raw: str | None) -> bool:
    return normalize(raw) is not None


def normalize_or_raise(raw: str | None):
    """For FastAPI handlers — raises HTTPException 400 with the user-friendly
    message if invalid. Returns the canonical phone string when valid."""
    norm = normalize(raw)
    if not norm:
        from fastapi import HTTPException
        raise HTTPException(400, INVALID_MSG)
    return norm
