"""Order extraction and persistence.

When the bot finishes a quote-intake conversation it appends an
<ORDER>...</ORDER> JSON block to its reply. We parse it out, save
the order, and strip the block before sending the reply to the
customer.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass

from . import db


ORDER_OPEN = "<ORDER>"
ORDER_CLOSE = "</ORDER>"
_ORDER_RE = re.compile(r"<ORDER>(.*?)</ORDER>", re.DOTALL | re.IGNORECASE)


@dataclass
class ExtractedOrder:
    customer_name: str = ""
    company: str = ""
    phone: str = ""
    product: str = ""
    grade: str = ""
    dimensions: str = ""
    quantity: str = ""
    delivery: str = ""
    notes: str = ""


def extract_and_strip(reply: str) -> tuple[str, ExtractedOrder | None]:
    """Pull the JSON order block out of a model reply, return clean text + parsed order."""
    m = _ORDER_RE.search(reply)
    if not m:
        return reply, None
    raw = m.group(1).strip()
    cleaned = _ORDER_RE.sub("", reply).strip()
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return cleaned, None

    if not isinstance(data, dict):
        return cleaned, None

    return cleaned, ExtractedOrder(
        customer_name=str(data.get("customer_name") or data.get("name") or "").strip(),
        company=str(data.get("company") or "").strip(),
        phone=str(data.get("phone") or data.get("contact") or "").strip(),
        product=str(data.get("product") or "").strip(),
        grade=str(data.get("grade") or data.get("material") or "").strip(),
        dimensions=str(data.get("dimensions") or data.get("specs") or "").strip(),
        quantity=str(data.get("quantity") or "").strip(),
        delivery=str(data.get("delivery") or data.get("address") or "").strip(),
        notes=str(data.get("notes") or "").strip(),
    )


def save(wa_id: str, order: ExtractedOrder, raw_summary: str) -> int:
    with db.connect() as c:
        cur = c.execute(
            """INSERT INTO orders
               (wa_id, customer_name, company, phone, product, grade, dimensions,
                quantity, delivery, notes, raw_summary, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)""",
            (
                wa_id,
                order.customer_name,
                order.company,
                order.phone,
                order.product,
                order.grade,
                order.dimensions,
                order.quantity,
                order.delivery,
                order.notes,
                raw_summary,
                time.time(),
            ),
        )
        return cur.lastrowid or 0


def list_recent(limit: int = 100, status: str | None = None) -> list[dict]:
    q = "SELECT * FROM orders"
    params: list = []
    if status:
        q += " WHERE status = ?"
        params.append(status)
    q += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with db.connect() as c:
        return [dict(r) for r in c.execute(q, params).fetchall()]


def update_status(order_id: int, status: str) -> None:
    with db.connect() as c:
        c.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))


def get(order_id: int) -> dict | None:
    with db.connect() as c:
        row = c.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        return dict(row) if row else None
