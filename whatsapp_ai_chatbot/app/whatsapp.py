"""Meta WhatsApp Cloud API client and webhook signature verification."""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

import httpx

from .config import settings

log = logging.getLogger(__name__)


def verify_signature(app_secret: str, raw_body: bytes, header: str | None) -> bool:
    """Verify Meta's X-Hub-Signature-256 header.

    Meta signs the raw request body with HMAC-SHA256 keyed by the app secret
    and sends it as `sha256=<hex>`. Reject anything that doesn't match.
    """
    if not app_secret or not header:
        return False
    if not header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    received = header.split("=", 1)[1]
    return hmac.compare_digest(expected, received)


def parse_inbound(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten Meta's nested webhook payload into a list of message dicts.

    Returns one entry per text message we care about. Non-text events
    (status callbacks, reactions, media, etc.) are filtered out and the
    caller can decide what to do.
    """
    out: list[dict[str, Any]] = []
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value") or {}
            contacts = {c.get("wa_id"): c for c in value.get("contacts", []) or []}
            for msg in value.get("messages", []) or []:
                if msg.get("type") != "text":
                    continue
                wa_id = msg.get("from")
                contact = contacts.get(wa_id) or {}
                out.append(
                    {
                        "wa_id": wa_id,
                        "name": (contact.get("profile") or {}).get("name"),
                        "text": (msg.get("text") or {}).get("body", ""),
                        "message_id": msg.get("id"),
                        "timestamp": msg.get("timestamp"),
                    }
                )
    return out


async def send_text(to_wa_id: str, text: str) -> dict[str, Any]:
    """Send a plain-text WhatsApp message via the Cloud API."""
    if not settings.meta_access_token or not settings.meta_phone_number_id:
        log.warning("META_ACCESS_TOKEN or META_PHONE_NUMBER_ID missing — skipping send")
        return {"skipped": True}

    url = (
        f"https://graph.facebook.com/{settings.meta_graph_version}"
        f"/{settings.meta_phone_number_id}/messages"
    )
    body = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_wa_id,
        "type": "text",
        "text": {"preview_url": False, "body": text[:4096]},
    }
    headers = {
        "Authorization": f"Bearer {settings.meta_access_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(url, json=body, headers=headers)
        if r.status_code >= 400:
            log.error("WhatsApp send failed %s: %s", r.status_code, r.text)
        r.raise_for_status()
        return r.json()


async def mark_read(message_id: str) -> None:
    """Mark an incoming message as read so the customer sees the blue ticks."""
    if not settings.meta_access_token or not settings.meta_phone_number_id:
        return
    url = (
        f"https://graph.facebook.com/{settings.meta_graph_version}"
        f"/{settings.meta_phone_number_id}/messages"
    )
    body = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    headers = {
        "Authorization": f"Bearer {settings.meta_access_token}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json=body, headers=headers)
    except httpx.HTTPError as e:
        log.debug("mark_read failed (non-fatal): %s", e)
