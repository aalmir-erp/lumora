"""Knowledge base loader. Supports admin overrides via the `config` table."""
import json
from functools import lru_cache

from . import db
from .config import get_settings


@lru_cache
def _services_file() -> dict:
    return json.loads((get_settings().DATA_DIR / "services.json").read_text())


@lru_cache
def _pricing_file() -> dict:
    return json.loads((get_settings().DATA_DIR / "pricing.json").read_text())


@lru_cache
def faq_text() -> str:
    return (get_settings().DATA_DIR / "faq.md").read_text()


def services() -> dict:
    """File-based services with admin overrides merged in."""
    base = json.loads(json.dumps(_services_file()))  # deep copy
    overrides = db.cfg_get("services_overrides", {}) or {}
    if overrides:
        by_id = {s["id"]: s for s in base["services"]}
        for sid, patch in overrides.items():
            if sid in by_id and isinstance(patch, dict):
                by_id[sid].update(patch)
        base["services"] = list(by_id.values())
    return base


def pricing() -> dict:
    """File-based pricing with admin overrides merged in."""
    base = json.loads(json.dumps(_pricing_file()))
    overrides = db.cfg_get("pricing_overrides", {}) or {}
    if overrides:
        for sid, patch in overrides.get("rules", {}).items():
            if sid in base["rules"]:
                base["rules"][sid].update(patch)
        for k in ("surcharges", "discounts"):
            if k in overrides:
                base[k].update(overrides[k])
    return base


def kb_blob(language: str = "en") -> str:
    """Compact text blob of the full KB — cached as a system-prompt prefix."""
    s = services()
    p = pricing()
    b = get_settings().brand()
    lines = [f"# {b['name'].upper()} KNOWLEDGE BASE", ""]
    lines.append(f"Brand: {b['name']} — {b['tagline']}")
    lines.append(f"Operates as: {b.get('legal_owner', 'Urban Services')}")
    lines.append(f"Phone: {b['phone']}")
    lines.append(f"WhatsApp: {b['whatsapp']}")
    lines.append(f"Email: {b['email']}")
    lines.append(f"Domain: https://{b['domain']}")
    lines.append(f"Languages supported: {', '.join(b['languages'])}")
    lines.append(f"Areas served: {', '.join(s['areas_served'])}")
    lines.append("")
    lines.append("## SERVICES")
    for svc in s["services"]:
        lines.append(f"- {svc['name']} (id: {svc['id']}, category: {svc['category']}, "
                     f"starting from {svc.get('starting_price', '?')} AED)")
        lines.append(f"  {svc['description']}")
        if svc.get("includes"):
            lines.append(f"  Includes: {'; '.join(svc['includes'])}")
        if svc.get("excludes"):
            lines.append(f"  Excludes: {'; '.join(svc['excludes'])}")
        # INTAKE — the ONLY questions to ask the customer for booking this service.
        # Ask in order. Skip anything not in this list.
        if svc.get("intake"):
            lines.append(f"  ASK_FOR_BOOKING (only these — never ask others): "
                         f"{' | '.join(svc['intake'])}")
        # Addon ids LLM can pass to get_quote(addons=[...])
        for a in (svc.get("addons") or []):
            lines.append(f"  Addon[id={a['id']}]: {a['name']} (+{a['price']} AED)")
    lines.append("")
    lines.append("## PRICING (AED, 5% VAT included)")
    for sid, rule in p["rules"].items():
        lines.append(f"- {sid}: {json.dumps(rule)}")
    lines.append(f"Surcharges: {json.dumps(p['surcharges'])}")
    lines.append(f"Discounts: {json.dumps(p['discounts'])}")
    lines.append("")
    lines.append("## FAQ")
    lines.append(faq_text())
    return "\n".join(lines)
