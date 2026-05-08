"""Static knowledge base for Aalmir Plastic Industries.

Edit this file to keep the bot's product / company facts up to date.
The contents are injected into the system prompt and (with Anthropic)
served from the prompt cache so updates are cheap to roll out.

Keep entries short and factual. The bot is instructed to refuse to
invent facts that aren't here.
"""
from __future__ import annotations

COMPANY_PROFILE = """
Aalmir Plastic Industries (aalmirplastic.com) is a UAE-based plastic
manufacturer and trader. The company supplies plastic products for
industrial, commercial, and retail customers across the GCC.

- Website: https://aalmirplastic.com
- Headquarters: United Arab Emirates
- Business hours (default): Sunday–Thursday, 09:00–18:00 GST
- Languages served: English, Arabic, Urdu, Hindi
""".strip()


PRODUCTS = """
Common product categories Aalmir Plastic deals in (edit to match the
current catalogue):

- Plastic sheets & rolls (HDPE, LDPE, PP, PVC)
- Industrial packaging (drums, jerrycans, pallets, crates)
- Plastic bags & films (printed and plain)
- Custom moulded products (on request)
- Recycled plastic granules

Pricing depends on grade, MOQ, and delivery terms. The bot must NOT
quote a specific price unless the figure is listed below; instead it
should offer to forward the request to the sales team.
""".strip()


SERVICES = """
- Bulk supply with delivery across the UAE and GCC
- Custom sizing, colour, and printing for orders above MOQ
- Sample dispatch for qualified B2B leads
- Recycling buy-back programme for post-industrial plastic waste
""".strip()


FAQ = """
Q: How do I get a quote?
A: Share product type, grade, dimensions/specs, quantity, and delivery
   address. The bot collects these, summarises, and hands off to sales.

Q: What is the typical lead time?
A: Stock items: 1–3 working days within the UAE. Custom orders: 1–3
   weeks depending on tooling and quantity. The bot must confirm with
   sales for any specific commitment.

Q: Do you ship outside the UAE?
A: Yes — across the GCC and on request to other regions (Ex-Works or
   FOB Jebel Ali typical). Freight quoted separately.

Q: Minimum order quantity?
A: Varies by product. The bot should ask for the customer's volume and
   route to sales rather than guessing.

Q: Payment terms?
A: 50% advance, 50% before dispatch is the default for new customers.
   Established accounts may have credit terms — sales confirms.
""".strip()


def assemble() -> str:
    """Return the full KB block to be embedded in the system prompt."""
    return (
        "## Company\n"
        f"{COMPANY_PROFILE}\n\n"
        "## Products\n"
        f"{PRODUCTS}\n\n"
        "## Services\n"
        f"{SERVICES}\n\n"
        "## FAQ\n"
        f"{FAQ}"
    )
