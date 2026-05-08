"""Layered settings: env > database > default.

Lets the operator paste tokens via the admin UI without redeploying,
while still respecting env vars when set (they take precedence so
production deployments can be locked down).
"""
from __future__ import annotations

import os
import time
from typing import Any

from . import db
from .config import settings as env_settings


# Settings exposed in the admin UI. Order = display order.
EDITABLE_KEYS: list[tuple[str, str, str, bool]] = [
    # (db_key, env_var_name, label, is_secret)
    ("META_ACCESS_TOKEN",    "META_ACCESS_TOKEN",    "Meta Access Token",                True),
    ("META_PHONE_NUMBER_ID", "META_PHONE_NUMBER_ID", "Meta Phone Number ID",             False),
    ("META_APP_SECRET",      "META_APP_SECRET",      "Meta App Secret",                  True),
    ("META_VERIFY_TOKEN",    "META_VERIFY_TOKEN",    "Meta Webhook Verify Token",        False),
    ("META_WABA_ID",         "META_WABA_ID",         "WhatsApp Business Account ID",     False),
    ("AI_PROVIDER",          "AI_PROVIDER",          "AI Provider (anthropic | openai)", False),
    ("ANTHROPIC_API_KEY",    "ANTHROPIC_API_KEY",    "Anthropic API Key",                True),
    ("ANTHROPIC_MODEL",      "ANTHROPIC_MODEL",      "Anthropic Model",                  False),
    ("OPENAI_API_KEY",       "OPENAI_API_KEY",       "OpenAI API Key",                   True),
    ("OPENAI_MODEL",         "OPENAI_MODEL",         "OpenAI Model",                     False),
    ("HANDOFF_WHATSAPP",     "HANDOFF_WHATSAPP",     "Sales handoff WhatsApp number",    False),
    ("HANDOFF_EMAIL",        "HANDOFF_EMAIL",        "Sales handoff email",              False),
    ("BOT_ENABLED",          "BOT_ENABLED",          "Bot enabled? (true / false)",      False),
]


def get(key: str, default: str = "") -> str:
    """Layered get: env > db > default."""
    env_val = os.environ.get(key, "")
    if env_val:
        return env_val
    with db.connect() as c:
        row = c.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row:
            return row["value"]
    return default


def set_value(key: str, value: str) -> None:
    with db.connect() as c:
        c.execute(
            "INSERT INTO settings(key, value, updated_at) VALUES(?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, value, time.time()),
        )


def all_for_admin() -> list[dict[str, Any]]:
    """Return the editable settings list with current values + provenance."""
    out = []
    for key, env_name, label, is_secret in EDITABLE_KEYS:
        env_val = os.environ.get(env_name, "")
        db_val = ""
        with db.connect() as c:
            row = c.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            if row:
                db_val = row["value"]
        if env_val:
            value, source = env_val, "env"
        elif db_val:
            value, source = db_val, "db"
        else:
            value, source = "", "unset"
        out.append(
            {
                "key": key,
                "label": label,
                "is_secret": is_secret,
                "source": source,
                "has_value": bool(value),
                "masked": _mask(value) if is_secret else value,
            }
        )
    return out


def _mask(s: str) -> str:
    if not s:
        return ""
    if len(s) <= 8:
        return "•" * len(s)
    return s[:4] + "•" * (len(s) - 8) + s[-4:]


# Strongly-typed convenience accessors — these wrap get() so callers
# don't sprinkle string keys everywhere.
def meta_access_token() -> str:
    return get("META_ACCESS_TOKEN", env_settings.meta_access_token)


def meta_phone_number_id() -> str:
    return get("META_PHONE_NUMBER_ID", env_settings.meta_phone_number_id)


def meta_app_secret() -> str:
    return get("META_APP_SECRET", env_settings.meta_app_secret)


def meta_verify_token() -> str:
    return get("META_VERIFY_TOKEN", env_settings.meta_verify_token)


def meta_graph_version() -> str:
    return get("META_GRAPH_VERSION", env_settings.meta_graph_version)


def ai_provider() -> str:
    return (get("AI_PROVIDER", env_settings.ai_provider) or "anthropic").lower()


def anthropic_api_key() -> str:
    return get("ANTHROPIC_API_KEY", env_settings.anthropic_api_key)


def anthropic_model() -> str:
    return get("ANTHROPIC_MODEL", env_settings.anthropic_model)


def openai_api_key() -> str:
    return get("OPENAI_API_KEY", env_settings.openai_api_key)


def openai_model() -> str:
    return get("OPENAI_MODEL", env_settings.openai_model)


def handoff_whatsapp() -> str:
    return get("HANDOFF_WHATSAPP", env_settings.handoff_whatsapp)


def handoff_email() -> str:
    return get("HANDOFF_EMAIL", env_settings.handoff_email)


def bot_enabled() -> bool:
    return (get("BOT_ENABLED", "true").lower() != "false")
