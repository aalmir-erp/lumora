"""v1.24.124 — Ziina integration tests. All 15 scenarios from the
pre-build plan. Uses httpx.MockTransport for the Ziina API surface so
NO real network calls happen, and no real key is needed.

Per CLAUDE.md W2: these MUST be 15/15 green before pushing the
integration to production. Payment bugs cost real money.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import pytest
import httpx

os.environ.setdefault("ADMIN_TOKEN", "lumora-admin-test")

from app import db, ziina  # noqa: E402


TEST_API_KEY = "ziina_TEST_FAKE_KEY_for_tests"
TEST_WEBHOOK_SECRET = "whsec_test_fake_secret_xyz"


def _seed_cfg(test_mode: bool = True):
    db.cfg_set("payment_providers", {
        "ziina_api_key": TEST_API_KEY,
        "ziina_webhook_secret": TEST_WEBHOOK_SECRET,
        "ziina_test_mode": test_mode,
    })


def _make_transport(handler):
    """Wrap a request-handler closure as an httpx MockTransport."""
    return httpx.MockTransport(handler)


def _patch_httpx_async(monkeypatch, handler):
    """Patch httpx.AsyncClient to use a MockTransport that runs the handler."""
    real_AsyncClient = httpx.AsyncClient
    def _patched(*args, **kw):
        kw["transport"] = _make_transport(handler)
        return real_AsyncClient(*args, **kw)
    monkeypatch.setattr(httpx, "AsyncClient", _patched)


# ════════════════════════════════════════════════════════════════════════
# 1. HAPPY PATH — create returns 200 with redirect_url + id
# ════════════════════════════════════════════════════════════════════════
def test_01_create_payment_intent_happy_path(monkeypatch):
    _seed_cfg()
    captured = {}
    def handler(req: httpx.Request) -> httpx.Response:
        captured["path"]    = req.url.path
        captured["method"]  = req.method
        captured["headers"] = dict(req.headers)
        captured["body"]    = json.loads(req.content.decode())
        return httpx.Response(200, json={
            "id": "pi_FAKE123",
            "amount": 2500,
            "currency_code": "AED",
            "status": "requires_payment_instrument",
            "redirect_url": "https://checkout.ziina.com/p/abc",
            "success_url": "https://servia.ae/booked",
            "cancel_url":  "https://servia.ae/pay/inv_1",
        })
    _patch_httpx_async(monkeypatch, handler)

    r = asyncio.run(ziina.create_payment_intent(
        amount_minor=2500, currency_code="AED",
        success_url="https://servia.ae/booked",
        cancel_url="https://servia.ae/pay/inv_1",
        message="Servia booking inv_1",
    ))
    assert r["ok"] is True
    assert r["id"] == "pi_FAKE123"
    assert r["redirect_url"] == "https://checkout.ziina.com/p/abc"
    assert captured["method"] == "POST"
    assert captured["path"]   == "/api/payment_intent"
    assert captured["headers"]["authorization"] == "Bearer " + TEST_API_KEY
    assert captured["body"]["amount"] == 2500
    assert isinstance(captured["body"]["amount"], int)        # docs gotcha
    assert captured["body"]["currency_code"] == "AED"
    assert captured["body"]["test"] is True
    assert captured["body"]["success_url"] == "https://servia.ae/booked"


# ════════════════════════════════════════════════════════════════════════
# 2. AMOUNT MUST BE INTEGER — docs explicitly forbid 10.00
# ════════════════════════════════════════════════════════════════════════
def test_02_amount_must_be_integer(monkeypatch):
    _seed_cfg()
    r = asyncio.run(ziina.create_payment_intent(amount_minor=25.00))
    assert r["ok"] is False
    assert "must be int" in r["error"]
    assert r["retryable"] is False


# ════════════════════════════════════════════════════════════════════════
# 3. NO API KEY → caller can fall back, but ok=False
# ════════════════════════════════════════════════════════════════════════
def test_03_no_api_key_configured(monkeypatch):
    db.cfg_set("payment_providers", {})
    r = asyncio.run(ziina.create_payment_intent(amount_minor=2500))
    assert r["ok"] is False
    assert "not configured" in r["error"]
    assert r["retryable"] is False


# ════════════════════════════════════════════════════════════════════════
# 4. ZIINA 5XX → retryable=True (caller falls back to Stripe)
# ════════════════════════════════════════════════════════════════════════
def test_04_ziina_5xx_is_retryable(monkeypatch):
    _seed_cfg()
    _patch_httpx_async(monkeypatch,
        lambda req: httpx.Response(503, text="upstream timeout"))
    r = asyncio.run(ziina.create_payment_intent(amount_minor=2500))
    assert r["ok"] is False
    assert r["retryable"] is True
    assert r["http_status"] == 503


# ════════════════════════════════════════════════════════════════════════
# 5. ZIINA 4XX → retryable=False (config bug, do NOT fall back silently)
# ════════════════════════════════════════════════════════════════════════
def test_05_ziina_4xx_is_not_retryable(monkeypatch):
    _seed_cfg()
    _patch_httpx_async(monkeypatch,
        lambda req: httpx.Response(401, json={"error": "Invalid key"}))
    r = asyncio.run(ziina.create_payment_intent(amount_minor=2500))
    assert r["ok"] is False
    assert r["retryable"] is False
    assert r["http_status"] == 401


# ════════════════════════════════════════════════════════════════════════
# 6. NETWORK TIMEOUT → retryable=True
# ════════════════════════════════════════════════════════════════════════
def test_06_network_timeout_is_retryable(monkeypatch):
    _seed_cfg()
    def handler(req):
        raise httpx.TimeoutException("simulated")
    _patch_httpx_async(monkeypatch, handler)
    r = asyncio.run(ziina.create_payment_intent(amount_minor=2500))
    assert r["ok"] is False
    assert r["retryable"] is True
    assert "timeout" in r["error"].lower()


# ════════════════════════════════════════════════════════════════════════
# 7. MISSING redirect_url IN RESPONSE → reject (don't silently succeed)
# ════════════════════════════════════════════════════════════════════════
def test_07_missing_redirect_url_in_response(monkeypatch):
    _seed_cfg()
    _patch_httpx_async(monkeypatch,
        lambda req: httpx.Response(200, json={"id": "pi_X"}))
    r = asyncio.run(ziina.create_payment_intent(amount_minor=2500))
    assert r["ok"] is False
    assert "missing" in r["error"]


# ════════════════════════════════════════════════════════════════════════
# 8. GET PAYMENT INTENT STATUS (for reconciliation + redirect verify)
# ════════════════════════════════════════════════════════════════════════
def test_08_get_payment_intent_status(monkeypatch):
    _seed_cfg()
    def handler(req):
        assert req.method == "GET"
        assert req.url.path == "/api/payment_intent/pi_ABC"
        return httpx.Response(200, json={
            "id": "pi_ABC", "status": "completed",
            "amount": 2500, "currency_code": "AED",
        })
    _patch_httpx_async(monkeypatch, handler)
    r = asyncio.run(ziina.get_payment_intent("pi_ABC"))
    assert r["ok"] is True
    assert r["status"] == "completed"
    assert r["amount"] == 2500


# ════════════════════════════════════════════════════════════════════════
# 9. WEBHOOK SIGNATURE VERIFICATION — happy path
# ════════════════════════════════════════════════════════════════════════
def test_09_webhook_signature_valid():
    _seed_cfg()
    body = b'{"event":"payment_intent.status.updated","data":{"id":"pi_X","status":"completed","amount":2500,"currency_code":"AED"}}'
    sig = hmac.new(TEST_WEBHOOK_SECRET.encode(), body,
                    hashlib.sha256).hexdigest()
    assert ziina.verify_webhook_signature(body, sig) is True
    # Also accept the optional "sha256=" prefix
    assert ziina.verify_webhook_signature(body, "sha256=" + sig) is True


# ════════════════════════════════════════════════════════════════════════
# 10. WEBHOOK SIGNATURE VERIFICATION — wrong signature → reject
# ════════════════════════════════════════════════════════════════════════
def test_10_webhook_signature_invalid():
    _seed_cfg()
    body = b'{"event":"payment_intent.status.updated","data":{}}'
    # Wrong signature (signed with different secret)
    bad = hmac.new(b"different_secret", body, hashlib.sha256).hexdigest()
    assert ziina.verify_webhook_signature(body, bad) is False
    # Missing signature header
    assert ziina.verify_webhook_signature(body, "") is False
    # Tampered body but valid-looking sig
    correct = hmac.new(TEST_WEBHOOK_SECRET.encode(), body,
                        hashlib.sha256).hexdigest()
    tampered = b'{"event":"payment_intent.status.updated","data":{"amount":999999}}'
    assert ziina.verify_webhook_signature(tampered, correct) is False


# ════════════════════════════════════════════════════════════════════════
# 11. WEBHOOK SECRET NOT CONFIGURED → reject (don't silently allow)
# ════════════════════════════════════════════════════════════════════════
def test_11_webhook_no_secret_configured():
    db.cfg_set("payment_providers", {"ziina_api_key": TEST_API_KEY})
    body = b'{"event":"x","data":{}}'
    sig = hmac.new(b"anything", body, hashlib.sha256).hexdigest()
    assert ziina.verify_webhook_signature(body, sig) is False


# ════════════════════════════════════════════════════════════════════════
# 12. PARSE WEBHOOK BODY → returns event + data
# ════════════════════════════════════════════════════════════════════════
def test_12_parse_webhook():
    body = b'{"event":"payment_intent.status.updated","data":{"id":"pi_X","status":"completed","amount":2500,"currency_code":"AED"}}'
    p = ziina.parse_webhook(body)
    assert p["event"] == "payment_intent.status.updated"
    assert p["data"]["id"] == "pi_X"
    assert p["data"]["status"] == "completed"
    assert p["data"]["amount"] == 2500


# ════════════════════════════════════════════════════════════════════════
# 13. AMOUNT-MATCH VALIDATION (defence against webhook tampering)
# ════════════════════════════════════════════════════════════════════════
def test_13_amount_match():
    # 25.00 AED → 2500 fils. Webhook says 2500 → match.
    assert ziina.validate_amount_match(25.00, 2500) is True
    # 1-fil rounding tolerance
    assert ziina.validate_amount_match(25.00, 2501) is True
    assert ziina.validate_amount_match(25.00, 2499) is True
    # Outside tolerance → reject
    assert ziina.validate_amount_match(25.00, 2400) is False
    # Attacker tries to refund 100 AED for a 25 AED invoice
    assert ziina.validate_amount_match(25.00, 10000) is False
    # 350.50 AED → 35050 fils (decimal)
    assert ziina.validate_amount_match(350.50, 35050) is True


# ════════════════════════════════════════════════════════════════════════
# 14. REFUND — idempotency via UUID
# ════════════════════════════════════════════════════════════════════════
def test_14_refund_with_idempotency_uuid(monkeypatch):
    _seed_cfg()
    captured = {}
    def handler(req):
        captured["body"] = json.loads(req.content.decode())
        return httpx.Response(200, json={"id": captured["body"]["id"],
                                          "status": "completed",
                                          "amount": captured["body"].get("amount")})
    _patch_httpx_async(monkeypatch, handler)
    # Caller-supplied refund_id → reused for idempotency
    r = asyncio.run(ziina.refund(
        payment_intent_id="pi_ABC",
        amount_minor=1500,
        refund_id="ref-fixed-uuid-1234",
    ))
    assert r["ok"] is True
    assert r["refund_id"] == "ref-fixed-uuid-1234"
    assert captured["body"]["id"] == "ref-fixed-uuid-1234"
    assert captured["body"]["payment_intent_id"] == "pi_ABC"
    assert captured["body"]["amount"] == 1500

    # No refund_id → mint a fresh UUID
    captured.clear()
    r2 = asyncio.run(ziina.refund(payment_intent_id="pi_ABC"))
    assert r2["ok"] is True
    assert r2["refund_id"]  # auto-minted UUID present
    assert "amount" not in captured["body"]   # full refund


# ════════════════════════════════════════════════════════════════════════
# 15. AMOUNT CONVERSION HELPERS — AED ↔ fils
# ════════════════════════════════════════════════════════════════════════
def test_15_amount_conversion():
    assert ziina.amount_to_minor(25.00) == 2500
    assert ziina.amount_to_minor(350.50) == 35050
    assert ziina.amount_to_minor(0.01) == 1
    assert ziina.amount_to_minor("25.50") == 2550
    assert ziina.minor_to_aed(2500) == 25.00
    assert ziina.minor_to_aed(35050) == 350.50
