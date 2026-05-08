"""Aalmir Plastic Industries — knowledge base.

This is the static fallback KB. The admin panel can override any
section by writing to the `kb_blocks` table; the assemble() function
prefers DB content when present.

Edit either this file (then redeploy) or the admin → KB editor (live).
"""
from __future__ import annotations

from . import db


COMPANY_PROFILE = """
Aalmir Plastic Industries (aalmirplastic.com) is a UAE-based plastic
manufacturer and trader, supplying industrial, commercial, and retail
customers across the GCC and beyond.

- Website: https://aalmirplastic.com
- Headquarters: United Arab Emirates
- Working hours: Sunday–Thursday 08:00–18:00 GST; Saturday 08:00–13:00; Friday closed
- Languages: English, Arabic, Urdu, Hindi
""".strip()


PRODUCTS = """
Aalmir Plastic typically supplies the following categories. The bot
must NOT quote a specific price unless explicitly listed below; instead
it should collect specs and route the request to the sales team.

PLASTIC SHEETS & ROLLS
- HDPE sheets — high stiffness, chemical resistance. Common thicknesses: 1, 2, 3, 5, 10, 15, 20, 25 mm. Sheet sizes 1m × 2m up to 2m × 6m.
- LDPE sheets / rolls — flexible films, liners, protective covering. 30–500 micron typical.
- PP (polypropylene) sheets — food-grade, chemical-resistant. 1–10 mm typical.
- PVC sheets — rigid and flexible grades. 1–20 mm.
- Polycarbonate sheets — clear, impact-resistant. 2–10 mm.
- Acrylic (PMMA) sheets — clear/coloured, used for signage and displays. 2–20 mm.

PLASTIC BAGS & FILMS
- HDPE/LDPE plastic bags — printed and plain
- Garbage bags (rolls and individual)
- Shrink wrap and stretch film
- Bubble wrap and air-bubble film
- Vacuum bags (food and industrial)

INDUSTRIAL PACKAGING
- Plastic drums (50L, 100L, 200L) HDPE
- Jerrycans (5L, 10L, 20L, 25L)
- Plastic pallets (Euro, US sizes)
- Plastic crates (collapsible and rigid)
- IBC tank liners

CUSTOM MOULDED PRODUCTS (Made to order)
- Bespoke designs from customer drawings
- Available in HDPE, PP, PVC, ABS
- MOQ varies — typically 500+ pieces for custom moulds

RECYCLED PLASTIC GRANULES
- HDPE granules (post-industrial / post-consumer)
- LDPE granules
- PP granules
- PET flakes
- Custom blending to specification

RAW MATERIALS (Trading)
- Virgin HDPE, LDPE, PP, PVC resins
- Masterbatches and additives
""".strip()


SERVICES = """
- Bulk supply with delivery across all UAE emirates
- Export across the GCC (KSA, Oman, Kuwait, Bahrain, Qatar) and on request to Africa, Asia, Europe
- Custom sizing, colour matching, and printing for orders above MOQ
- Free sample dispatch for qualified B2B leads (contact details + use case required)
- Recycling buy-back programme for post-industrial plastic waste
- Technical consultation on grade selection and product design
""".strip()


FAQ = """
Q: How do I get a quote?
A: Share product type, grade, dimensions/specs, quantity, and delivery
   address. The bot collects these, summarises, and hands off to the
   sales team.

Q: What is the typical lead time?
A: Stock items: 1–3 working days within UAE. Custom orders: 1–3 weeks
   depending on tooling and quantity. Export orders depend on shipping.
   The bot must defer specific dates to sales.

Q: Do you ship outside the UAE?
A: Yes. GCC by road, other regions Ex-Works or FOB Jebel Ali. Freight
   is quoted separately by the sales team.

Q: Minimum order quantity (MOQ)?
A: Varies by product. The bot collects volume and routes to sales
   rather than guessing. As a rough guide:
   - Stock sheets/rolls: any quantity
   - Custom moulded: 500+ pieces typical
   - Custom-printed bags: 50,000+ pieces typical

Q: Payment terms?
A: New customers — 50% advance, 50% before dispatch. Established
   accounts may have credit terms; sales confirms.

Q: Delivery time inside UAE?
A: Same-day or next-day for stock items in Dubai/Sharjah/Ajman.
   1–3 days for other emirates. Free delivery above a minimum order
   value (sales confirms).

Q: Do you provide samples?
A: Yes, for B2B leads. Customer covers courier on first sample.

Q: What grades / certifications do you have?
A: Food-grade PP and PE available. ISO certifications and material
   data sheets supplied on request via sales.

Q: Can you match a competitor's price?
A: The bot must NOT commit to price matching. It should collect the
   competitor's quote details and route to sales for review.

Q: I have a problem with a previous order — what should I do?
A: The bot should apologise, collect the order reference, brief
   description of the issue, and immediately escalate to sales.

Q: Where are you located?
A: United Arab Emirates. The bot can mention this and offer to share
   the exact address (admin can paste it via the admin panel).
""".strip()


ORDER_INTAKE = """
When a customer expresses buying intent, the bot collects ALL of the
following before issuing <ESCALATE> and the <ORDER> JSON block:

1. Product type and grade (e.g. "HDPE sheet, 2mm")
2. Dimensions / specs (size in mm, weight, colour, printing details)
3. Quantity (and unit — pieces, kg, rolls, sheets, drums)
4. Delivery emirate / country and approximate address
5. Buyer name and company
6. Best contact phone number (confirm if it differs from WhatsApp)
7. Any deadline / urgency
8. Any special notes (e.g. food-grade, food contact, certification needs)

The bot summarises the collected info back to the customer in a
numbered list and asks them to confirm. Only after the customer
confirms does it emit <ESCALATE> and the <ORDER> block.
""".strip()


CONTACT = """
- WhatsApp (this number) — handled by the AI assistant + sales agents
- Email: info@aalmirplastic.com (admin can override)
- Website: https://aalmirplastic.com
- Sales hotline: shared by the sales team during handoff
""".strip()


_SECTIONS: list[tuple[str, str, str]] = [
    ("company",  "Company",       COMPANY_PROFILE),
    ("products", "Products",      PRODUCTS),
    ("services", "Services",      SERVICES),
    ("faq",      "FAQ",           FAQ),
    ("order",    "Order intake",  ORDER_INTAKE),
    ("contact",  "Contact",       CONTACT),
]


def assemble() -> str:
    """Assemble the full KB. DB-stored blocks override file defaults."""
    overrides: dict[str, tuple[str, str]] = {}
    try:
        with db.connect() as c:
            for row in c.execute("SELECT slug, title, content FROM kb_blocks").fetchall():
                overrides[row["slug"]] = (row["title"], row["content"])
    except Exception:
        pass

    parts: list[str] = []
    for slug, title, default_content in _SECTIONS:
        t, content = overrides.get(slug, (title, default_content))
        parts.append(f"## {t}\n{content}")

    # Any extra DB-only blocks the admin added (not in defaults)
    for slug, (title, content) in overrides.items():
        if slug not in {s for s, _, _ in _SECTIONS}:
            parts.append(f"## {title}\n{content}")

    return "\n\n".join(parts)


def list_blocks() -> list[dict]:
    """Return all blocks for the admin editor — DB values overlaid on defaults."""
    overrides: dict[str, tuple[str, str]] = {}
    with db.connect() as c:
        for row in c.execute("SELECT slug, title, content FROM kb_blocks").fetchall():
            overrides[row["slug"]] = (row["title"], row["content"])

    out = []
    for slug, title, default_content in _SECTIONS:
        t, content = overrides.get(slug, (title, default_content))
        out.append(
            {
                "slug": slug,
                "title": t,
                "content": content,
                "overridden": slug in overrides,
            }
        )
    return out


def save_block(slug: str, title: str, content: str) -> None:
    import time as _t

    with db.connect() as c:
        c.execute(
            "INSERT INTO kb_blocks(slug, title, content, updated_at) VALUES(?, ?, ?, ?) "
            "ON CONFLICT(slug) DO UPDATE SET title=excluded.title, content=excluded.content, updated_at=excluded.updated_at",
            (slug, title, content, _t.time()),
        )


def reset_block(slug: str) -> None:
    with db.connect() as c:
        c.execute("DELETE FROM kb_blocks WHERE slug = ?", (slug,))
