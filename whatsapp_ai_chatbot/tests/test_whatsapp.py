import hashlib
import hmac

from app.whatsapp import parse_inbound, verify_signature


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_verify_signature_accepts_valid():
    body = b'{"hello":"world"}'
    secret = "topsecret"
    assert verify_signature(secret, body, _sign(secret, body)) is True


def test_verify_signature_rejects_tampered():
    body = b'{"hello":"world"}'
    sig = _sign("topsecret", body)
    assert verify_signature("topsecret", body + b"x", sig) is False


def test_verify_signature_rejects_wrong_prefix():
    assert verify_signature("s", b"x", "md5=deadbeef") is False


def test_verify_signature_rejects_empty():
    assert verify_signature("s", b"x", None) is False
    assert verify_signature("", b"x", "sha256=abc") is False


def test_parse_inbound_extracts_text_message():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "contacts": [
                                {"wa_id": "971501234567", "profile": {"name": "Ali"}}
                            ],
                            "messages": [
                                {
                                    "from": "971501234567",
                                    "id": "wamid.ABC",
                                    "timestamp": "1700000000",
                                    "type": "text",
                                    "text": {"body": "Hi, do you have HDPE sheets?"},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }
    out = parse_inbound(payload)
    assert len(out) == 1
    assert out[0]["wa_id"] == "971501234567"
    assert out[0]["name"] == "Ali"
    assert "HDPE" in out[0]["text"]


def test_parse_inbound_skips_non_text():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {"from": "1", "type": "image", "id": "x"}
                            ]
                        }
                    }
                ]
            }
        ]
    }
    assert parse_inbound(payload) == []
