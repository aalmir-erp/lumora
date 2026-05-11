import json
import os
from functools import lru_cache
from pathlib import Path


class Settings:
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    WEB_DIR = BASE_DIR.parent / "web"

    # Brand (env can override)
    BRAND_NAME = os.getenv("BRAND_NAME", "Servia")
    BRAND_TAGLINE = os.getenv("BRAND_TAGLINE", "UAE's smart home services platform")
    BRAND_DOMAIN = os.getenv("BRAND_DOMAIN", "servia.ae")

    APP_VERSION = "1.24.104"

    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-7")
    MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "1500"))

    DEMO_MODE = os.getenv("DEMO_MODE", "auto").lower()  # auto | on | off

    # Stealth-launch: when GATE_BOOKINGS=1 we accept bookings up to the payment
    # screen, then show a friendly "payment gateway temporarily unavailable"
    # error + offer 15% off coupon when fixed + capture intent (price-acceptance
    # + voice/text feedback). Customers feel respected (no time wasted, real-
    # sounding error, future discount) while we get real-demand data without
    # delivering services. Set GATE_BOOKINGS=0 to deactivate when going live.
    GATE_BOOKINGS = os.getenv("GATE_BOOKINGS", "0") == "1"
    GATE_DISCOUNT_PCT = int(os.getenv("GATE_DISCOUNT_PCT", "15"))

    ALLOWED_ORIGINS = [
        o.strip() for o in os.getenv(
            "ALLOWED_ORIGINS",
            "https://servia.ae,https://www.servia.ae,"
            "https://urbanservices.ae,https://www.urbanservices.ae,"
            "http://localhost:8000,http://127.0.0.1:8000,http://127.0.0.1:8788"
        ).split(",") if o.strip()
    ]

    HANDOFF_WHATSAPP = os.getenv("HANDOFF_WHATSAPP", "")  # internal-only
    HANDOFF_EMAIL = os.getenv("HANDOFF_EMAIL", "support@servia.ae")

    # WhatsApp bridge endpoint (Node service URL where the QR-paired bridge lives).
    WA_BRIDGE_URL = os.getenv("WA_BRIDGE_URL", "")
    WA_BRIDGE_TOKEN = os.getenv("WA_BRIDGE_TOKEN", "")  # shared secret

    @property
    def use_llm(self) -> bool:
        if self.DEMO_MODE == "on":
            return False
        if self.DEMO_MODE == "off":
            return True
        return bool(self.ANTHROPIC_API_KEY)

    def brand(self) -> dict:
        """File defaults → env overrides → DB overrides (admin-set, runtime editable)."""
        from . import db
        with open(self.DATA_DIR / "brand.json", encoding="utf-8") as f:
            base = json.load(f)
        base["name"] = self.BRAND_NAME
        base["tagline"] = self.BRAND_TAGLINE
        base["domain"] = self.BRAND_DOMAIN
        try:
            ov = db.cfg_get("brand_overrides", {}) or {}
            for k, v in ov.items():
                if v not in (None, ""):
                    base[k] = v
        except Exception:  # noqa: BLE001
            pass
        return base


@lru_cache
def get_settings() -> Settings:
    return Settings()
