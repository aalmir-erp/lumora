"""v1.24.124 — Ziina hosted-checkout integration for Servia.

Founder pasted the Ziina docs (sections 1-12) on 2026-05-11. This module
implements the client + webhook verifier against THOSE EXACT field
names and endpoints — no guesses.

References (founder paste, verified):
  Base URL          : https://api-v2.ziina.com/api
  Auth              : Authorization: Bearer <key>
  Create intent     : POST /payment_intent
                      body fields: amount, currency_code, message,
                                   success_url, cancel_url, failure_url,
                                   test, expiry
                      response fields: id, redirect_url, status, ...
  Status values     : requires_payment_instrument, requires_user_action,
                      pending, completed, failed, canceled
  Get status        : GET /payment_intent/{id}
  Webhook header    : X-Hmac-Signature
  Algorithm         : HMAC-SHA256 hex over the raw request body
  Webhook events    : payment_intent.status.updated,
                      refund.status.updated
  Refund            : POST /refund
                      body: id (UUID for idempotency),
                            payment_intent_id, amount?, currency_code?
  Amount unit       : integer base units (1000 = 10.00 AED)
  Currency          : AED primary (others may not be supported)
  Test mode         : "test": true in the request body (no separate URL)

Critical guardrails baked in:
  * Amount is always serialised as integer (Ziina rejects 10.00).
  * Webhook signature is verified BEFORE we touch the DB (rejects
    spoofed requests).
  * We NEVER trust the redirect-back query params — `confirm_status()`
    always re-fetches GET /payment_intent/{id} server-side.
  * All requests have a 15-second timeout so a Ziina outage doesn't
    hang the customer's pay page.
"""
from __future__ import annotations

import hmac
import hashlib
import json as _json
import uuid
from typing import Any

import httpx

from . import db


BASE_URL = "https://api-v2.ziina.com/api"
DEFAULT_TIMEOUT = 15.0


# Status values per docs section 6
STATUS_PENDING_INITIAL  = "requires_payment_instrument"
STATUS_PENDING_3DS      = "requires_user_action"
STATUS_PROCESSING       = "pending"
STATUS_COMPLETED        = "completed"
STATUS_FAILED           = "failed"
STATUS_CANCELED         = "canceled"

# Terminal vs pending — drives reconciliation + UI logic
TERMINAL_STATUSES = {STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELED}
SUCCESS_STATUSES  = {STATUS_COMPLETED}


# ────────────────────────────────────────────────────────────────────────
# Configuration loaders (always pulled from db.cfg — admin manages keys)
# ────────────────────────────────────────────────────────────────────────
def _cfg() -> dict:
    return db.cfg_get("payment_providers", {}) or {}


def get_api_key() -> str:
    return (_cfg().get("ziina_api_key") or "").strip()


def get_webhook_secret() -> str:
    return (_cfg().get("ziina_webhook_secret") or "").strip()


def is_test_mode() -> bool:
    """Default True until founder explicitly flips OFF for go-live."""
    v = _cfg().get("ziina_test_mode")
    return bool(v) if v is not None else True


def is_configured() -> bool:
    return bool(get_api_key())


# ────────────────────────────────────────────────────────────────────────
# Client — create / get / refund
# ────────────────────────────────────────────────────────────────────────
async def create_payment_intent(
    *,
    amount_minor: int,
    currency_code: str = "AED",
    success_url: str | None = None,
    cancel_url: str | None = None,
    failure_url: str | None = None,
    message: str | None = None,
    expiry_ms: int | None = None,
) -> dict:
    """POST /payment_intent. Returns {ok, id, redirect_url, status, ...}
    or {ok:False, error, http_status, retryable}.

    `retryable=True` means transient (5xx, network) — caller should
    fall back to Stripe. `retryable=False` means a 4xx — caller should
    NOT fall back (likely a config bug). NEVER catches uppercase
    rare ConnectionError silently; surfaces every failure mode.
    """
    api_key = get_api_key()
    if not api_key:
        return {"ok": False, "error": "ZIINA_API_KEY not configured in admin",
                "retryable": False, "http_status": 0}
    if not isinstance(amount_minor, int):
        return {"ok": False,
                "error": f"amount_minor must be int (got {type(amount_minor).__name__})",
                "retryable": False, "http_status": 0}
    if amount_minor <= 0:
        return {"ok": False, "error": f"amount_minor must be > 0 (got {amount_minor})",
                "retryable": False, "http_status": 0}

    payload: dict[str, Any] = {
        "amount": amount_minor,        # MUST be int per docs gotcha
        "currency_code": currency_code,
        "test": is_test_mode(),
    }
    if success_url: payload["success_url"] = success_url
    if cancel_url:  payload["cancel_url"]  = cancel_url
    if failure_url: payload["failure_url"] = failure_url
    if message:     payload["message"]     = message[:200]
    if expiry_ms:   payload["expiry"]      = int(expiry_ms)

    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as c:
            r = await c.post(BASE_URL + "/payment_intent",
                              headers=headers, json=payload)
    except httpx.TimeoutException as e:
        return {"ok": False, "error": f"timeout: {e}",
                "retryable": True, "http_status": 0}
    except httpx.HTTPError as e:
        return {"ok": False, "error": f"network: {type(e).__name__}: {e}",
                "retryable": True, "http_status": 0}

    if r.status_code >= 500:
        return {"ok": False, "error": f"ziina 5xx: {r.text[:200]}",
                "retryable": True, "http_status": r.status_code}
    if r.status_code >= 400:
        return {"ok": False, "error": f"ziina {r.status_code}: {r.text[:200]}",
                "retryable": False, "http_status": r.status_code}

    try:
        d = r.json()
    except Exception as e:
        return {"ok": False, "error": f"invalid json: {e}",
                "retryable": False, "http_status": r.status_code}

    intent_id   = d.get("id") or ""
    redirect_url = d.get("redirect_url") or ""
    status       = d.get("status") or ""
    if not intent_id or not redirect_url:
        return {"ok": False,
                "error": f"missing id/redirect_url in ziina response: {d}",
                "retryable": False, "http_status": r.status_code}

    return {
        "ok": True,
        "id": intent_id,
        "redirect_url": redirect_url,
        "status": status,
        "amount": d.get("amount"),
        "currency_code": d.get("currency_code"),
        "raw": d,
    }


async def get_payment_intent(intent_id: str) -> dict:
    """GET /payment_intent/{id}. Returns the current authoritative status.
    Called by the reconciliation cron + the /api/pay/status/{id} endpoint
    after a customer redirects back."""
    api_key = get_api_key()
    if not api_key:
        return {"ok": False, "error": "ZIINA_API_KEY not configured",
                "retryable": False}
    if not intent_id:
        return {"ok": False, "error": "intent_id is required",
                "retryable": False}

    headers = {
        "Authorization": "Bearer " + api_key,
        "Accept":        "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as c:
            r = await c.get(BASE_URL + "/payment_intent/" + intent_id,
                             headers=headers)
    except httpx.TimeoutException as e:
        return {"ok": False, "error": f"timeout: {e}", "retryable": True}
    except httpx.HTTPError as e:
        return {"ok": False, "error": f"network: {e}", "retryable": True}

    if r.status_code == 404:
        return {"ok": False, "error": "payment intent not found at ziina",
                "retryable": False, "http_status": 404}
    if r.status_code >= 500:
        return {"ok": False, "error": f"ziina 5xx: {r.text[:200]}",
                "retryable": True, "http_status": r.status_code}
    if r.status_code >= 400:
        return {"ok": False, "error": f"ziina {r.status_code}: {r.text[:200]}",
                "retryable": False, "http_status": r.status_code}

    try:
        d = r.json()
    except Exception as e:
        return {"ok": False, "error": f"invalid json: {e}",
                "retryable": False}

    return {
        "ok": True,
        "id": d.get("id"),
        "status": d.get("status"),
        "amount": d.get("amount"),
        "currency_code": d.get("currency_code"),
        "raw": d,
    }


async def refund(
    *,
    payment_intent_id: str,
    amount_minor: int | None = None,
    currency_code: str | None = None,
    refund_id: str | None = None,
) -> dict:
    """POST /refund. Idempotency via `id` (UUID) — same id ⇒ same refund.
    Caller can pass `refund_id` to retry a previously-attempted refund;
    if omitted, a new UUID is minted."""
    api_key = get_api_key()
    if not api_key:
        return {"ok": False, "error": "ZIINA_API_KEY not configured"}
    if not payment_intent_id:
        return {"ok": False, "error": "payment_intent_id required"}

    payload: dict[str, Any] = {
        "id": refund_id or str(uuid.uuid4()),
        "payment_intent_id": payment_intent_id,
    }
    if amount_minor is not None:
        if not isinstance(amount_minor, int) or amount_minor <= 0:
            return {"ok": False,
                    "error": f"amount_minor must be positive int (got {amount_minor!r})"}
        payload["amount"] = amount_minor
    if currency_code:
        payload["currency_code"] = currency_code

    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as c:
            r = await c.post(BASE_URL + "/refund",
                              headers=headers, json=payload)
    except httpx.HTTPError as e:
        return {"ok": False, "error": f"network: {e}"}

    if r.status_code >= 400:
        return {"ok": False, "error": f"ziina {r.status_code}: {r.text[:200]}",
                "http_status": r.status_code, "refund_id": payload["id"]}

    try:
        d = r.json()
    except Exception:
        d = {"raw": r.text}
    return {"ok": True, "refund_id": payload["id"], "raw": d}


# ────────────────────────────────────────────────────────────────────────
# Webhook signature verification (HMAC-SHA256 over raw body, hex)
# ────────────────────────────────────────────────────────────────────────
def verify_webhook_signature(raw_body: bytes, signature_header: str,
                              secret: str | None = None) -> bool:
    """Verify the X-Hmac-Signature header against HMAC-SHA256(raw_body, secret).

    Constant-time compare via hmac.compare_digest so we don't leak
    timing information. Returns True only if the signature header is
    present, the secret is configured, AND the hash matches.

    Per docs: "Hash the raw JSON request body using your secret with
    HMAC-SHA256. Compare the resulting hex string to the X-Hmac-Signature
    header value."
    """
    secret = (secret if secret is not None else get_webhook_secret()).encode()
    if not secret:
        # Mis-configured → reject (don't silently allow)
        return False
    if not signature_header:
        return False
    expected = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    sig = signature_header.strip().lower()
    # Some senders prefix "sha256=" — accept either form
    if sig.startswith("sha256="):
        sig = sig.split("=", 1)[1]
    try:
        return hmac.compare_digest(expected, sig)
    except Exception:
        return False


def parse_webhook(raw_body: bytes) -> dict:
    """Decode a webhook body. Returns {"event": ..., "data": {...}} or
    raises ValueError. Use AFTER verify_webhook_signature() returns True."""
    try:
        d = _json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"invalid json: {e}") from e
    return {
        "event": d.get("event") or "",
        "data":  d.get("data") or {},
    }


# ────────────────────────────────────────────────────────────────────────
# Helpers for invoice ↔ intent matching with safety checks
# ────────────────────────────────────────────────────────────────────────
def amount_to_minor(aed_decimal: float | int | str) -> int:
    """Convert an AED decimal (e.g. 25.00, "350.50") to integer minor
    units (fils) that Ziina requires. 25.00 → 2500."""
    return int(round(float(aed_decimal) * 100))


def minor_to_aed(amount_minor: int) -> float:
    return round(amount_minor / 100.0, 2)


def validate_amount_match(invoice_amount_aed: float, webhook_amount_minor: int,
                           tolerance_fils: int = 1) -> bool:
    """Defence against amount-tampering webhooks. We accept a 1-fil
    rounding tolerance because float math + rounding can drift."""
    expected = amount_to_minor(invoice_amount_aed)
    return abs(int(webhook_amount_minor) - expected) <= tolerance_fils
