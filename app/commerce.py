"""v1.24.141 — Professional commercial flow: Quote → Sales Order → Delivery
Note → Tax Invoice → Purchase Order → Payment registration → Profit report.

WHY THIS MODULE EXISTS
----------------------
Founder request: "I need professional all quotes invoices with easy tracking,
customization, filters, groups and reportings. Quote auto by AI or manual
from admin → customer confirms → converts to confirmed sales order →
generates performance delivery order for services → select vendors per
service at which rate → end total profit from the quotation."

The existing `quotes` / `invoices` tables (db.py) cover ~15% of what a
proper UAE FTA-compliant commercial flow needs. This module fills the
other 85% without breaking the existing tables.

WHAT WE ADD
-----------
NEW TABLES (created in _init_schema at module load):
  sales_orders         confirmed quote → SO
  delivery_notes       service completed → DN with customer signature
  purchase_orders      vendor assignment → PO with vendor rate
  payment_registrations payments in (customer→us) + out (us→vendor)
  doc_counters         sequential numbering per doc type per year

NEW FIELDS ON EXISTING TABLES (added via ALTER if missing):
  quotes.quote_number, customer_id, line_items_json, vat_amount,
         terms, notes, quote_status
  invoices.invoice_number, customer_id, sales_order_id, line_items_json,
           subtotal, vat_amount, issued_at, due_at, terms, notes

KEY BUSINESS RULES (UAE-specific)
- VAT 5% standard rate (FTA-compliant tax invoice format)
- Sequential numbering: {DOC}-{YYYY}-{0001} — must be gap-free per FTA
- Profit per SO = Customer revenue (excl VAT) − sum(vendor costs) − discounts
- VAT is collected on behalf of FTA, NOT income (recorded as liability)
- Currency: AED default, multi-currency optional

WORKFLOW
--------
  1. QUOTE         created by AI bot or admin     QT-2026-0001
                   line_items: [{svc, qty, unit_price, line_total}, ...]
                   subtotal + 5% VAT = total
  2. ACCEPT        customer signs (signature_data_url)
                   AUTO-CREATES Sales Order        SO-2026-0001
  3. ASSIGN VENDOR admin picks vendor + rate for each line
                   AUTO-CREATES one Purchase Order PO-2026-0001
                   per vendor (could be multiple if split)
  4. SERVICE DONE  vendor marks complete + photo proof
                   AUTO-CREATES Delivery Note      DN-2026-0001
                   customer signs DN to confirm
  5. INVOICE       AUTO-CREATED when SO confirmed   INV-2026-0001
                   sent to customer (WhatsApp + email)
  6. PAYMENT IN    admin registers customer payment via Ziina/bank/cash
                   payment_registrations row: customer_in
                   invoice status → paid
  7. PAYMENT OUT   admin pays vendor against PO
                   payment_registrations row: vendor_out
                   PO status → paid
  8. PROFIT CALC   = INV.subtotal − sum(POs.vendor_rate)
                   (VAT is NOT our money — collected for FTA)

ADMIN UI (web/admin-commerce.html)
- 6 tabs: Quotes / SOs / Invoices / Delivery Notes / POs / Payments
- Reports tab with: revenue/profit by period, by service, by vendor,
  outstanding A/R + A/P
- Each list: filters (date range, status, search), sortable cols,
  CSV export
- Each doc: clean print-CSS template for "Save as PDF" via browser
  print dialog (no server-side PDF lib needed)

ENDPOINTS
---------
Admin auth required for ALL endpoints. Customer-facing quote acceptance
goes through the existing /api/quotes/* surface (extended below).

  Quote
    GET  /api/admin/quotes
    GET  /api/admin/quotes/{id}
    POST /api/admin/quotes/create
    POST /api/admin/quotes/{id}/send
    POST /api/admin/quotes/{id}/accept    → creates SO
    POST /api/admin/quotes/{id}/reject

  Sales Order
    GET  /api/admin/sales-orders
    GET  /api/admin/sales-orders/{id}
    POST /api/admin/sales-orders/{id}/assign-vendor   → creates PO
    POST /api/admin/sales-orders/{id}/mark-completed  → creates DN

  Delivery Note
    GET  /api/admin/delivery-notes
    POST /api/admin/delivery-notes/{id}/sign

  Invoice
    GET  /api/admin/invoices
    GET  /api/admin/invoices/{id}
    POST /api/admin/invoices/{id}/mark-paid

  Purchase Order
    GET  /api/admin/purchase-orders
    GET  /api/admin/purchase-orders/{id}
    POST /api/admin/purchase-orders/create
    POST /api/admin/purchase-orders/{id}/send-to-vendor
    POST /api/admin/purchase-orders/{id}/mark-paid

  Payment
    GET  /api/admin/payments
    POST /api/admin/payments/register

  Reports
    GET  /api/admin/reports/profit?from=YYYY-MM-DD&to=YYYY-MM-DD
    GET  /api/admin/reports/sales-summary?period=month
    GET  /api/admin/reports/outstanding
    GET  /api/admin/reports/top-customers
    GET  /api/admin/reports/top-vendors

  Printable
    GET  /admin/print/quote/{id}        clean HTML for Ctrl+P → PDF
    GET  /admin/print/sales-order/{id}
    GET  /admin/print/invoice/{id}
    GET  /admin/print/delivery-note/{id}
    GET  /admin/print/purchase-order/{id}
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import db
from .auth import require_admin


router = APIRouter()


# UAE FTA standard VAT rate
VAT_RATE = 0.05


# ─────────────────────────────────────────────────────────────────────
# Schema bootstrap
# ─────────────────────────────────────────────────────────────────────
def _init_schema() -> None:
    with db.connect() as conn:
        conn.executescript("""
        -- Document numbering counters
        CREATE TABLE IF NOT EXISTS doc_counters (
            doc_type TEXT NOT NULL,        -- 'quote' | 'so' | 'invoice' | 'po' | 'dn'
            year     INTEGER NOT NULL,
            counter  INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (doc_type, year)
        );

        -- Sales orders (created when a quote is accepted)
        CREATE TABLE IF NOT EXISTS sales_orders (
            id              TEXT PRIMARY KEY,
            so_number       TEXT NOT NULL UNIQUE,    -- "SO-2026-0001"
            quote_id        TEXT,
            booking_id      TEXT,
            customer_id     INTEGER,
            customer_name   TEXT NOT NULL,
            customer_phone  TEXT,
            customer_email  TEXT,
            customer_address TEXT,
            line_items_json TEXT NOT NULL,           -- [{svc_id, name, qty, unit_price, line_total, vendor_id?, vendor_rate?}, ...]
            subtotal        REAL NOT NULL,
            discount        REAL DEFAULT 0,
            vat_amount      REAL NOT NULL,
            total           REAL NOT NULL,
            currency        TEXT DEFAULT 'AED',
            status          TEXT DEFAULT 'confirmed', -- confirmed | in_progress | completed | cancelled
            terms           TEXT,
            notes           TEXT,
            confirmed_at    TEXT,
            completed_at    TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_so_customer ON sales_orders(customer_id);
        CREATE INDEX IF NOT EXISTS idx_so_status   ON sales_orders(status);
        CREATE INDEX IF NOT EXISTS idx_so_created  ON sales_orders(created_at);

        -- Delivery notes
        CREATE TABLE IF NOT EXISTS delivery_notes (
            id              TEXT PRIMARY KEY,
            dn_number       TEXT NOT NULL UNIQUE,    -- "DN-2026-0001"
            sales_order_id  TEXT,
            booking_id      TEXT,
            vendor_id       INTEGER,
            delivered_at    TEXT NOT NULL,
            line_items_json TEXT,                    -- snapshot of what was delivered
            customer_signature TEXT,                 -- base64 data URL
            customer_signed_at TEXT,
            photo_urls_json TEXT,                    -- ["url1", "url2"]
            notes           TEXT,
            created_at      TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_dn_so      ON delivery_notes(sales_order_id);
        CREATE INDEX IF NOT EXISTS idx_dn_vendor  ON delivery_notes(vendor_id);

        -- Purchase orders to vendors
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id              TEXT PRIMARY KEY,
            po_number       TEXT NOT NULL UNIQUE,    -- "PO-2026-0001"
            sales_order_id  TEXT,
            booking_id      TEXT,
            vendor_id       INTEGER NOT NULL,
            vendor_name     TEXT,
            vendor_phone    TEXT,
            service_id      TEXT NOT NULL,
            service_name    TEXT,
            line_items_json TEXT NOT NULL,           -- [{svc_id, qty, vendor_rate, line_total}, ...]
            vendor_total    REAL NOT NULL,           -- total payable to vendor (no VAT — vendor is mostly unregistered)
            currency        TEXT DEFAULT 'AED',
            status          TEXT DEFAULT 'open',     -- open | sent | accepted | completed | paid | cancelled
            sent_at         TEXT,
            accepted_at     TEXT,
            completed_at    TEXT,
            paid_at         TEXT,
            terms           TEXT,
            notes           TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_po_vendor ON purchase_orders(vendor_id);
        CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);
        CREATE INDEX IF NOT EXISTS idx_po_so     ON purchase_orders(sales_order_id);

        -- Payment registrations (in + out)
        CREATE TABLE IF NOT EXISTS payment_registrations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_type    TEXT NOT NULL,           -- 'customer_in' | 'vendor_out'
            reference_type  TEXT NOT NULL,           -- 'invoice' | 'purchase_order'
            reference_id    TEXT NOT NULL,           -- invoice.id or po.id
            counterparty_id INTEGER,                 -- customer_id or vendor_id
            counterparty_name TEXT,
            amount          REAL NOT NULL,
            currency        TEXT DEFAULT 'AED',
            method          TEXT,                    -- card | bank_transfer | cash | wallet | cheque
            reference_number TEXT,                   -- bank ref / txn id / cheque #
            payment_date    TEXT NOT NULL,
            notes           TEXT,
            created_at      TEXT NOT NULL,
            created_by      TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_pr_type    ON payment_registrations(payment_type);
        CREATE INDEX IF NOT EXISTS idx_pr_ref     ON payment_registrations(reference_type, reference_id);
        CREATE INDEX IF NOT EXISTS idx_pr_date    ON payment_registrations(payment_date);
        """)

        # Add columns to existing quotes / invoices tables (idempotent — ignore "already exists")
        def _safe_alter(sql: str):
            try:
                conn.execute(sql)
            except Exception:
                pass

        # Extend quotes
        for col, ddl in [
            ("quote_number",    "ALTER TABLE quotes ADD COLUMN quote_number TEXT"),
            ("customer_id",     "ALTER TABLE quotes ADD COLUMN customer_id INTEGER"),
            ("customer_name",   "ALTER TABLE quotes ADD COLUMN customer_name TEXT"),
            ("customer_phone",  "ALTER TABLE quotes ADD COLUMN customer_phone TEXT"),
            ("customer_email",  "ALTER TABLE quotes ADD COLUMN customer_email TEXT"),
            ("customer_address","ALTER TABLE quotes ADD COLUMN customer_address TEXT"),
            ("line_items_json", "ALTER TABLE quotes ADD COLUMN line_items_json TEXT"),
            ("vat_amount",      "ALTER TABLE quotes ADD COLUMN vat_amount REAL DEFAULT 0"),
            ("terms",           "ALTER TABLE quotes ADD COLUMN terms TEXT"),
            ("notes",           "ALTER TABLE quotes ADD COLUMN notes TEXT"),
        ]:
            _safe_alter(ddl)

        # Extend invoices
        for ddl in [
            "ALTER TABLE invoices ADD COLUMN invoice_number TEXT",
            "ALTER TABLE invoices ADD COLUMN customer_id INTEGER",
            "ALTER TABLE invoices ADD COLUMN customer_name TEXT",
            "ALTER TABLE invoices ADD COLUMN customer_phone TEXT",
            "ALTER TABLE invoices ADD COLUMN customer_email TEXT",
            "ALTER TABLE invoices ADD COLUMN customer_address TEXT",
            "ALTER TABLE invoices ADD COLUMN sales_order_id TEXT",
            "ALTER TABLE invoices ADD COLUMN line_items_json TEXT",
            "ALTER TABLE invoices ADD COLUMN subtotal REAL DEFAULT 0",
            "ALTER TABLE invoices ADD COLUMN discount REAL DEFAULT 0",
            "ALTER TABLE invoices ADD COLUMN vat_amount REAL DEFAULT 0",
            "ALTER TABLE invoices ADD COLUMN issued_at TEXT",
            "ALTER TABLE invoices ADD COLUMN due_at TEXT",
            "ALTER TABLE invoices ADD COLUMN terms TEXT",
            "ALTER TABLE invoices ADD COLUMN notes TEXT",
        ]:
            _safe_alter(ddl)


_init_schema()


# ─────────────────────────────────────────────────────────────────────
# Sequential numbering — FTA-compliant gap-free
# ─────────────────────────────────────────────────────────────────────
def next_doc_number(doc_type: str) -> str:
    """Atomically increment the counter for doc_type/current-year and return
    the formatted number e.g. 'INV-2026-0001'. Thread-safe via SQLite locks.

    doc_type values:
      'quote' → QT
      'so'    → SO
      'invoice' → INV
      'po'    → PO
      'dn'    → DN
    """
    prefix_map = {"quote": "QT", "so": "SO", "invoice": "INV",
                  "po": "PO", "dn": "DN"}
    prefix = prefix_map.get(doc_type, doc_type.upper())
    year = datetime.now(timezone.utc).year
    with db.connect() as c:
        # UPSERT with atomic increment
        c.execute("""
            INSERT INTO doc_counters (doc_type, year, counter) VALUES (?, ?, 1)
            ON CONFLICT(doc_type, year) DO UPDATE SET counter = counter + 1
        """, (doc_type, year))
        row = c.execute(
            "SELECT counter FROM doc_counters WHERE doc_type=? AND year=?",
            (doc_type, year)).fetchone()
        counter = row["counter"]
    return f"{prefix}-{year}-{counter:04d}"


# ─────────────────────────────────────────────────────────────────────
# Helpers — VAT, totals, IDs
# ─────────────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def calc_totals(line_items: list[dict], discount: float = 0) -> dict:
    """Given line_items [{qty, unit_price}, ...], compute subtotal + VAT + total.
    Each line_total is unit_price * qty. Discount is subtracted before VAT.
    UAE FTA standard: VAT 5% applied to (subtotal − discount).
    """
    subtotal = 0.0
    for li in line_items:
        qty = float(li.get("qty", 1) or 1)
        unit_price = float(li.get("unit_price", 0) or 0)
        line_total = qty * unit_price
        li["line_total"] = round(line_total, 2)
        subtotal += line_total
    subtotal = round(subtotal, 2)
    discount = round(float(discount or 0), 2)
    taxable = max(0, subtotal - discount)
    vat_amount = round(taxable * VAT_RATE, 2)
    total = round(taxable + vat_amount, 2)
    return {
        "subtotal": subtotal,
        "discount": discount,
        "vat_amount": vat_amount,
        "total": total,
    }


# ═════════════════════════════════════════════════════════════════════
# QUOTES
# ═════════════════════════════════════════════════════════════════════
class QuoteLineItem(BaseModel):
    svc_id: str
    name: str
    qty: float = 1
    unit_price: float
    vendor_id: Optional[int] = None
    vendor_rate: Optional[float] = None


class QuoteCreateBody(BaseModel):
    customer_id: Optional[int] = None
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    line_items: list[QuoteLineItem]
    discount: float = 0
    currency: str = "AED"
    valid_until: Optional[str] = None
    terms: Optional[str] = None
    notes: Optional[str] = None
    booking_id: Optional[str] = None


@router.post("/api/admin/quotes/create", dependencies=[Depends(require_admin)])
def admin_create_quote(body: QuoteCreateBody):
    """Create a quote manually from the admin panel."""
    line_items = [li.model_dump() for li in body.line_items]
    if not line_items:
        raise HTTPException(status_code=400, detail="at least one line item required")
    totals = calc_totals(line_items, discount=body.discount)
    q_id = _id("Q")
    q_num = next_doc_number("quote")
    now = _now()
    valid_until = body.valid_until or (datetime.now(timezone.utc) + timedelta(days=14)).date().isoformat()

    with db.connect() as c:
        c.execute("""
            INSERT INTO quotes
              (id, quote_number, booking_id, service_id, breakdown_json,
               line_items_json, subtotal, discount, vat_amount, total,
               currency, valid_until, status, customer_id, customer_name,
               customer_phone, customer_email, customer_address, terms,
               notes, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (q_id, q_num, body.booking_id,
              line_items[0]["svc_id"],   # primary service_id for backwards compat
              json.dumps({"items": line_items, "totals": totals}),
              json.dumps(line_items),
              totals["subtotal"], totals["discount"], totals["vat_amount"], totals["total"],
              body.currency, valid_until, "draft",
              body.customer_id, body.customer_name, body.customer_phone,
              body.customer_email, body.customer_address,
              body.terms, body.notes, now))
    return {"ok": True, "id": q_id, "quote_number": q_num, **totals}


@router.get("/api/admin/quotes", dependencies=[Depends(require_admin)])
def admin_list_quotes(status: Optional[str] = None, customer_id: Optional[int] = None,
                       q: Optional[str] = None, from_date: Optional[str] = None,
                       to_date: Optional[str] = None, limit: int = 200):
    """List quotes with filters. ?status=draft|sent|accepted|rejected|expired
    ?q=search-in-name-or-number ?from_date=YYYY-MM-DD ?to_date=YYYY-MM-DD"""
    where = ["1=1"]
    args: list = []
    if status:
        where.append("status = ?"); args.append(status)
    if customer_id:
        where.append("customer_id = ?"); args.append(customer_id)
    if from_date:
        where.append("created_at >= ?"); args.append(from_date)
    if to_date:
        where.append("created_at <= ?"); args.append(to_date + "T23:59:59")
    if q:
        where.append("(quote_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)")
        args.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    where_sql = " AND ".join(where)
    with db.connect() as c:
        rows = c.execute(f"""
            SELECT id, quote_number, customer_name, customer_phone,
                   service_id, subtotal, discount, vat_amount, total,
                   currency, status, valid_until, created_at
            FROM quotes WHERE {where_sql}
            ORDER BY created_at DESC LIMIT ?
        """, (*args, limit)).fetchall()
        items = [dict(r) for r in rows]
    return {"ok": True, "count": len(items), "items": items}


@router.get("/api/admin/quotes/{quote_id}", dependencies=[Depends(require_admin)])
def admin_get_quote(quote_id: str):
    with db.connect() as c:
        row = c.execute("SELECT * FROM quotes WHERE id=?", (quote_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="quote not found")
        return {"ok": True, "quote": dict(row)}


@router.post("/api/admin/quotes/{quote_id}/send", dependencies=[Depends(require_admin)])
def admin_send_quote(quote_id: str):
    """Mark a quote as 'sent' (notifies the customer separately via WhatsApp)."""
    with db.connect() as c:
        c.execute("UPDATE quotes SET status='sent' WHERE id=?", (quote_id,))
    return {"ok": True}


@router.post("/api/admin/quotes/{quote_id}/accept", dependencies=[Depends(require_admin)])
def admin_accept_quote(quote_id: str):
    """Customer accepted (or admin marks accepted on their behalf). This auto-
    creates a Sales Order + an unpaid Customer Invoice. Both share line items
    with the original quote."""
    now = _now()
    with db.connect() as c:
        q = c.execute("SELECT * FROM quotes WHERE id=?", (quote_id,)).fetchone()
        if not q:
            raise HTTPException(status_code=404, detail="quote not found")
        if q["status"] == "accepted":
            raise HTTPException(status_code=409, detail="quote already accepted")
        c.execute("UPDATE quotes SET status='accepted' WHERE id=?", (quote_id,))

    # Create SO
    so = _create_so_from_quote(dict(q))
    # Auto-create invoice
    inv = _create_invoice_from_so(so)
    return {"ok": True, "sales_order": so, "invoice": inv}


@router.post("/api/admin/quotes/{quote_id}/reject", dependencies=[Depends(require_admin)])
def admin_reject_quote(quote_id: str):
    with db.connect() as c:
        c.execute("UPDATE quotes SET status='rejected' WHERE id=?", (quote_id,))
    return {"ok": True}


@router.post("/api/admin/quotes/{quote_id}/cancel", dependencies=[Depends(require_admin)])
def admin_cancel_quote(quote_id: str):
    """v1.24.163 — Cancel a quote (any status). Soft state change."""
    with db.connect() as c:
        q = c.execute("SELECT status FROM quotes WHERE id=?", (quote_id,)).fetchone()
        if not q:
            raise HTTPException(status_code=404, detail="quote not found")
        c.execute("UPDATE quotes SET status='cancelled' WHERE id=?", (quote_id,))
    return {"ok": True}


@router.delete("/api/admin/quotes/{quote_id}", dependencies=[Depends(require_admin)])
def admin_delete_quote(quote_id: str):
    """v1.24.163 — Hard-delete a DRAFT (or cancelled/rejected) quote.
    Accepted/sent quotes cannot be deleted — only cancelled — to keep
    an audit trail of agreed prices."""
    with db.connect() as c:
        q = c.execute("SELECT status FROM quotes WHERE id=?", (quote_id,)).fetchone()
        if not q:
            raise HTTPException(status_code=404, detail="quote not found")
        if q["status"] not in ("draft", "cancelled", "rejected", "superseded"):
            raise HTTPException(
                status_code=409,
                detail=f"cannot delete a {q['status']} quote — cancel it first",
            )
        c.execute("DELETE FROM quotes WHERE id=?", (quote_id,))
    return {"ok": True}


@router.post("/api/admin/quotes/{quote_id}/revise", dependencies=[Depends(require_admin)])
def admin_revise_quote(quote_id: str):
    """v1.24.163 — Create a revision of an existing quote.
    Numbering: QT-2026-0019 → QT-2026-0019-r1 → QT-2026-0019-r2.
    Founder request: 'revision should be the sub number of the main'."""
    now = _now()
    with db.connect() as c:
        orig = c.execute("SELECT * FROM quotes WHERE id=?", (quote_id,)).fetchone()
        if not orig:
            raise HTTPException(status_code=404, detail="quote not found")
        orig = dict(orig)
        base = orig["quote_number"].split("-r")[0]
        existing = c.execute(
            "SELECT quote_number FROM quotes WHERE quote_number LIKE ?",
            (base + "%",),
        ).fetchall()
        rev_n = 1
        for row in existing:
            num = row["quote_number"]
            if "-r" in num:
                try:
                    rev_n = max(rev_n, int(num.split("-r")[-1]) + 1)
                except ValueError:
                    pass
        new_number = f"{base}-r{rev_n}"
        new_id = _id("Q")
        c.execute("""
            INSERT INTO quotes
              (id, quote_number, booking_id, service_id, breakdown_json,
               line_items_json, subtotal, discount, vat_amount, total,
               currency, valid_until, status, customer_id, customer_name,
               customer_phone, customer_email, customer_address, terms,
               notes, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (new_id, new_number, orig.get("booking_id"), orig.get("service_id"),
              orig.get("breakdown_json"), orig.get("line_items_json"),
              orig.get("subtotal") or 0, orig.get("discount") or 0,
              orig.get("vat_amount") or 0, orig.get("total") or 0,
              orig.get("currency") or "AED", orig.get("valid_until"),
              "draft", orig.get("customer_id"), orig.get("customer_name"),
              orig.get("customer_phone"), orig.get("customer_email"),
              orig.get("customer_address"), orig.get("terms"),
              orig.get("notes"), now))
        if orig["status"] not in ("accepted", "cancelled", "rejected", "superseded"):
            c.execute("UPDATE quotes SET status='superseded' WHERE id=?", (quote_id,))
    return {"ok": True, "id": new_id, "quote_number": new_number,
            "revised_from": orig["quote_number"], "rev": rev_n}


class _QuoteFromTextBody(BaseModel):
    """v1.24.167 — Admin types/speaks a free-form request, AI extracts
    structured fields and returns them. UI then auto-fills the
    new-quote modal (admin can review before saving).

    Example inputs (founder's spec):
      'Mariam +971501234567 wants 5 deep cleans next Monday at 2pm in JLT'
      'sara, 050-123 4567, ac cleaning 3 units tomorrow morning, marina'
    """
    text: str


@router.post("/api/admin/quote-from-text", dependencies=[Depends(require_admin)])
def admin_extract_quote_from_text(body: _QuoteFromTextBody):
    """Call Claude with the services catalog + the admin's free-form
    request. Returns a structured object the front-end uses to pre-fill
    the new-quote modal (admin reviews then clicks Save).

    Returns: {"ok": True, "extracted": {customer_name, customer_phone,
              customer_email, customer_address, notes, line_items:[...]}}
    """
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    try:
        from . import kb
        svcs = kb.services().get("services", [])
    except Exception:
        svcs = []
    cat = [{"id": s["id"], "name": s["name"],
            "starting_price": s.get("starting_price", 0)} for s in svcs]
    try:
        import anthropic, json as _json, os as _os
        from .config import get_settings as _gs
        client = anthropic.Anthropic(
            api_key=_gs().ANTHROPIC_API_KEY or _os.getenv("ANTHROPIC_API_KEY", ""),
            timeout=12.0, max_retries=1,
        )
        sys_prompt = (
            "You extract a service booking from the admin's free-form "
            "request. Return STRICT JSON only, no prose. Schema:\n"
            "{\n"
            '  "customer_name": str,\n'
            '  "customer_phone": str (UAE format, +971...),\n'
            '  "customer_email": str | null,\n'
            '  "customer_address": str | null,\n'
            '  "notes": str | null,\n'
            '  "line_items": [{"svc_id": str, "name": str, "qty": number, "unit_price": number}]\n'
            "}\n\n"
            "Rules:\n"
            "- Match services from the catalog to the closest. 'AC cleaning' → 'ac_cleaning'.\n"
            "- Use starting_price as unit_price unless admin overrides.\n"
            "- qty defaults to 1.\n"
            "- Normalise UAE phone: '050-123 4567' / '0501234567' → '+971501234567'.\n"
            f"\nSERVICE CATALOG:\n{_json.dumps(cat, ensure_ascii=False)}\n"
        )
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=700,
            system=sys_prompt,
            messages=[{"role": "user", "content": text}],
        )
        out = ""
        for blk in resp.content:
            if getattr(blk, "type", "") == "text":
                out += getattr(blk, "text", "")
        out = out.strip()
        if out.startswith("```"):
            out = out.strip("`").split("\n", 1)[-1]
            if out.endswith("```"):
                out = out[:-3]
        extracted = _json.loads(out)
    except Exception as e:
        raise HTTPException(502, f"AI extraction failed: {e}")
    return {"ok": True, "extracted": extracted}


@router.get("/api/admin/quotes/{quote_id}/analytics",
             dependencies=[Depends(require_admin)])
def admin_quote_analytics(quote_id: str):
    """v1.24.168 — Full open/view/sign/pay/remark history for a quote.
    Founder demanded: 'admin maintain full analytics — which customer
    opened, browser, location, remarks, when payment made'.

    Returns one row per event (view_open, customer_question,
    customer_reject, customer_change_request, signed, paid) with the
    user-agent + IP (parsed for browser/OS hints) and timestamp.
    """
    with db.connect() as c:
        rows = c.execute(
            "SELECT id, action AS kind, details_json, created_at FROM events "
            "WHERE entity_type='quote' AND entity_id=? "
            "ORDER BY created_at DESC LIMIT 200",
            (quote_id,),
        ).fetchall()
        events = []
        import json as _json2
        for r in rows:
            d = dict(r)
            try:
                d["details"] = _json2.loads(d.get("details_json") or "{}")
            except Exception:
                d["details"] = {}
            ua = d["details"].get("ua", "")
            d["browser"], d["os"] = _parse_ua(ua) if ua else ("", "")
            events.append(d)
        summary = {
            "total_opens": sum(1 for e in events if e["kind"] == "view_open"),
            "first_open_at": next((e["created_at"] for e in events
                                    if e["kind"] == "view_open"), None),
            "signed_at": next((e["created_at"] for e in events
                                if e["kind"] == "signed"), None),
            "paid_at":   next((e["created_at"] for e in events
                                if e["kind"] == "paid"), None),
            "remark_count": sum(1 for e in events
                                 if e["kind"].startswith("customer_")),
        }
        return {"ok": True, "summary": summary, "events": events}


def _parse_ua(ua: str) -> tuple[str, str]:
    """Best-effort browser + OS from User-Agent string."""
    ua = (ua or "").lower()
    browser = "Other"
    if "edg/" in ua: browser = "Edge"
    elif "chrome/" in ua: browser = "Chrome"
    elif "firefox/" in ua: browser = "Firefox"
    elif "safari/" in ua and "chrome/" not in ua: browser = "Safari"
    os_name = "Other"
    if "iphone" in ua or "ipad" in ua: os_name = "iOS"
    elif "android" in ua: os_name = "Android"
    elif "mac os x" in ua or "macintosh" in ua: os_name = "macOS"
    elif "windows" in ua: os_name = "Windows"
    elif "linux" in ua: os_name = "Linux"
    return browser, os_name


@router.get("/api/admin/quotes/{quote_id}/remarks", dependencies=[Depends(require_admin)])
def admin_list_remarks(quote_id: str):
    """v1.24.165 — List customer remarks/change-requests/reject-reasons
    against a quote (multi_quote or admin-quote). Founder demanded:
    'admin side should be getting alerted that there are remarks on this
    quotation by a customer or if there is any change suggested'."""
    with db.connect() as c:
        rows = c.execute(
            "SELECT * FROM quote_remarks WHERE quote_id=? ORDER BY created_at DESC",
            (quote_id,),
        ).fetchall()
        return {"ok": True, "items": [dict(r) for r in rows]}


@router.get("/api/admin/quote-remarks/unread-count",
             dependencies=[Depends(require_admin)])
def admin_count_unread_remarks():
    """v1.24.165 — Total unread remarks across all quotes. UI shows
    this as a 🔔 badge next to the Quotes tab title."""
    try:
        with db.connect() as c:
            row = c.execute(
                "SELECT COUNT(*) AS n FROM quote_remarks WHERE admin_seen_at IS NULL"
            ).fetchone()
            return {"ok": True, "unread": int(row["n"]) if row else 0}
    except Exception:
        return {"ok": True, "unread": 0}


@router.post("/api/admin/quote-remarks/{remark_id}/seen",
              dependencies=[Depends(require_admin)])
def admin_mark_remark_seen(remark_id: int):
    """Mark a single remark as seen by admin (clears the 🔔 badge)."""
    with db.connect() as c:
        c.execute("UPDATE quote_remarks SET admin_seen_at=? WHERE id=?",
                  (_now(), remark_id))
    return {"ok": True}


class _RemarkReplyBody(BaseModel):
    reply: str


@router.post("/api/admin/quote-remarks/{remark_id}/reply",
              dependencies=[Depends(require_admin)])
def admin_reply_remark(remark_id: int, body: _RemarkReplyBody):
    """Admin replies to a customer remark. Stored on the remark row.
    (Reply delivery to customer — via WhatsApp/email — is on the founder
    to send; UI offers a one-click WA/email link using customer_phone.)"""
    with db.connect() as c:
        c.execute(
            "UPDATE quote_remarks SET admin_reply=?, admin_seen_at=? WHERE id=?",
            (body.reply, _now(), remark_id),
        )
    return {"ok": True}


@router.get("/api/admin/quotes/{quote_id}/links", dependencies=[Depends(require_admin)])
def admin_quote_links(quote_id: str):
    """v1.24.163 — Full doc chain for breadcrumb UI:
    Quote → revisions → SO → Invoice + DNs + POs."""
    with db.connect() as c:
        q = c.execute(
            "SELECT id, quote_number, status FROM quotes WHERE id=?", (quote_id,)
        ).fetchone()
        if not q:
            raise HTTPException(status_code=404, detail="quote not found")
        base = q["quote_number"].split("-r")[0]
        revs = c.execute(
            "SELECT id, quote_number, status FROM quotes WHERE quote_number LIKE ? "
            "ORDER BY quote_number",
            (base + "%",),
        ).fetchall()
        sos = c.execute(
            "SELECT id, so_number, status FROM sales_orders WHERE quote_id=?",
            (quote_id,),
        ).fetchall()
        invs, dns, pos = [], [], []
        for so in sos:
            sid = so["id"]
            invs += [dict(r) for r in c.execute(
                "SELECT id, invoice_number, status FROM invoices WHERE sales_order_id=?",
                (sid,)).fetchall()]
            dns += [dict(r) for r in c.execute(
                "SELECT id, dn_number, delivered_at FROM delivery_notes WHERE sales_order_id=?",
                (sid,)).fetchall()]
            pos += [dict(r) for r in c.execute(
                "SELECT id, po_number, status, vendor_name FROM purchase_orders WHERE sales_order_id=?",
                (sid,)).fetchall()]
    return {
        "ok": True,
        "quote": dict(q),
        "revisions": [dict(r) for r in revs],
        "sales_orders": [dict(s) for s in sos],
        "invoices": invs, "delivery_notes": dns, "purchase_orders": pos,
    }


# ═════════════════════════════════════════════════════════════════════
# SALES ORDERS
# ═════════════════════════════════════════════════════════════════════
def _create_so_from_quote(quote: dict) -> dict:
    """Internal: turn an accepted quote into a Sales Order."""
    so_id = _id("SO")
    so_num = next_doc_number("so")
    now = _now()
    line_items = json.loads(quote["line_items_json"] or "[]")
    with db.connect() as c:
        c.execute("""
            INSERT INTO sales_orders
              (id, so_number, quote_id, booking_id, customer_id,
               customer_name, customer_phone, customer_email, customer_address,
               line_items_json, subtotal, discount, vat_amount, total,
               currency, status, confirmed_at, terms, notes, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (so_id, so_num, quote["id"], quote.get("booking_id"),
              quote.get("customer_id"), quote.get("customer_name"),
              quote.get("customer_phone"), quote.get("customer_email"),
              quote.get("customer_address"),
              quote["line_items_json"],
              quote.get("subtotal") or 0, quote.get("discount") or 0,
              quote.get("vat_amount") or 0, quote.get("total") or 0,
              quote.get("currency", "AED"), "confirmed", now,
              quote.get("terms"), quote.get("notes"), now, now))
    return {"id": so_id, "so_number": so_num, "line_items": line_items,
            "total": quote.get("total")}


@router.get("/api/admin/sales-orders", dependencies=[Depends(require_admin)])
def admin_list_sos(status: Optional[str] = None, customer_id: Optional[int] = None,
                    q: Optional[str] = None, from_date: Optional[str] = None,
                    to_date: Optional[str] = None, limit: int = 200):
    where = ["1=1"]; args: list = []
    if status: where.append("status=?"); args.append(status)
    if customer_id: where.append("customer_id=?"); args.append(customer_id)
    if from_date: where.append("created_at >= ?"); args.append(from_date)
    if to_date: where.append("created_at <= ?"); args.append(to_date + "T23:59:59")
    if q:
        where.append("(so_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)")
        args.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    with db.connect() as c:
        rows = c.execute(f"""
            SELECT id, so_number, customer_name, customer_phone, subtotal,
                   vat_amount, total, currency, status, confirmed_at,
                   completed_at, created_at
            FROM sales_orders WHERE {' AND '.join(where)}
            ORDER BY created_at DESC LIMIT ?
        """, (*args, limit)).fetchall()
        return {"ok": True, "count": len(rows), "items": [dict(r) for r in rows]}


@router.get("/api/admin/sales-orders/{so_id}", dependencies=[Depends(require_admin)])
def admin_get_so(so_id: str):
    with db.connect() as c:
        so = c.execute("SELECT * FROM sales_orders WHERE id=?", (so_id,)).fetchone()
        if not so:
            raise HTTPException(status_code=404, detail="not found")
        # Get linked POs + DN + invoice
        pos = c.execute("SELECT * FROM purchase_orders WHERE sales_order_id=?", (so_id,)).fetchall()
        dns = c.execute("SELECT * FROM delivery_notes WHERE sales_order_id=?", (so_id,)).fetchall()
        invs = c.execute("SELECT * FROM invoices WHERE sales_order_id=?", (so_id,)).fetchall()
        return {"ok": True, "sales_order": dict(so),
                "purchase_orders": [dict(p) for p in pos],
                "delivery_notes": [dict(d) for d in dns],
                "invoices": [dict(i) for i in invs]}


class AssignVendorBody(BaseModel):
    vendor_id: int
    vendor_rate: float                    # AED to pay vendor (per line if applicable)
    service_id: str                       # which service line(s) this PO covers
    qty: float = 1
    notes: Optional[str] = None


@router.get("/api/admin/vendors/{vendor_id}/rate-for-service",
             dependencies=[Depends(require_admin)])
def admin_vendor_rate_for_service(vendor_id: int, service_id: str):
    """v1.24.169 — Auto-fill vendor rate when admin picks a service.
    Founder feedback: 'selected vendor rates neither in quotation neither
    in inventory or generating it should be automatically coming by
    default'. Look up the agreed price for this vendor × service from
    the vendor_services table.

    Returns:
      {"ok": True, "vendor_rate": float | null,
        "price_unit": str | null, "sla_hours": int | null}
    """
    try:
        with db.connect() as c:
            r = c.execute(
                "SELECT price_aed, price_unit, sla_hours FROM vendor_services "
                "WHERE vendor_id=? AND service_id=? AND active=1 LIMIT 1",
                (vendor_id, service_id),
            ).fetchone()
            if not r:
                return {"ok": True, "vendor_rate": None}
            return {
                "ok": True,
                "vendor_rate": r["price_aed"],
                "price_unit": r["price_unit"],
                "sla_hours": r["sla_hours"],
            }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/api/admin/sales-orders/{so_id}/assign-vendor",
             dependencies=[Depends(require_admin)])
def admin_assign_vendor(so_id: str, body: AssignVendorBody):
    """Pick a vendor + rate for a service in this SO. Creates a Purchase Order."""
    with db.connect() as c:
        so = c.execute("SELECT * FROM sales_orders WHERE id=?", (so_id,)).fetchone()
        if not so:
            raise HTTPException(status_code=404, detail="SO not found")
        vendor = c.execute("SELECT id, name, phone FROM vendors WHERE id=?",
                           (body.vendor_id,)).fetchone()
        if not vendor:
            raise HTTPException(status_code=404, detail="vendor not found")

    po_id = _id("PO")
    po_num = next_doc_number("po")
    now = _now()
    vendor_total = round(body.qty * body.vendor_rate, 2)
    line_items = [{
        "svc_id": body.service_id,
        "qty": body.qty,
        "vendor_rate": body.vendor_rate,
        "line_total": vendor_total,
    }]
    with db.connect() as c:
        c.execute("""
            INSERT INTO purchase_orders
              (id, po_number, sales_order_id, booking_id, vendor_id,
               vendor_name, vendor_phone, service_id, line_items_json,
               vendor_total, currency, status, terms, notes, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (po_id, po_num, so_id, so["booking_id"], body.vendor_id,
              vendor["name"], vendor["phone"], body.service_id,
              json.dumps(line_items), vendor_total,
              so["currency"], "open",
              "Net 7 days from completion", body.notes, now, now))

    # Move SO to in_progress on first vendor assignment
    with db.connect() as c:
        c.execute("UPDATE sales_orders SET status='in_progress', updated_at=? WHERE id=? AND status='confirmed'",
                  (now, so_id))

    return {"ok": True, "po_id": po_id, "po_number": po_num, "vendor_total": vendor_total}


class MarkCompletedBody(BaseModel):
    notes: Optional[str] = None
    photo_urls: Optional[list[str]] = None
    customer_signature: Optional[str] = None


@router.post("/api/admin/sales-orders/{so_id}/mark-completed",
             dependencies=[Depends(require_admin)])
def admin_mark_so_completed(so_id: str, body: MarkCompletedBody):
    """Mark SO completed → auto-create a Delivery Note."""
    now = _now()
    with db.connect() as c:
        so = c.execute("SELECT * FROM sales_orders WHERE id=?", (so_id,)).fetchone()
        if not so:
            raise HTTPException(status_code=404, detail="not found")
        c.execute("""
            UPDATE sales_orders SET status='completed', completed_at=?, updated_at=?
            WHERE id=?
        """, (now, now, so_id))

    dn_id = _id("DN")
    dn_num = next_doc_number("dn")
    with db.connect() as c:
        c.execute("""
            INSERT INTO delivery_notes
              (id, dn_number, sales_order_id, booking_id, delivered_at,
               line_items_json, customer_signature, customer_signed_at,
               photo_urls_json, notes, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (dn_id, dn_num, so_id, so["booking_id"], now,
              so["line_items_json"], body.customer_signature,
              (now if body.customer_signature else None),
              json.dumps(body.photo_urls or []), body.notes, now))
    return {"ok": True, "dn_id": dn_id, "dn_number": dn_num}


# ═════════════════════════════════════════════════════════════════════
# DELIVERY NOTES
# ═════════════════════════════════════════════════════════════════════
@router.get("/api/admin/delivery-notes", dependencies=[Depends(require_admin)])
def admin_list_dns(from_date: Optional[str] = None, to_date: Optional[str] = None,
                    limit: int = 200):
    where = ["1=1"]; args: list = []
    if from_date: where.append("delivered_at >= ?"); args.append(from_date)
    if to_date: where.append("delivered_at <= ?"); args.append(to_date + "T23:59:59")
    with db.connect() as c:
        rows = c.execute(f"""
            SELECT d.*, s.customer_name, s.customer_phone, s.total AS so_total
            FROM delivery_notes d
            LEFT JOIN sales_orders s ON s.id = d.sales_order_id
            WHERE {' AND '.join(where)}
            ORDER BY d.delivered_at DESC LIMIT ?
        """, (*args, limit)).fetchall()
        return {"ok": True, "count": len(rows), "items": [dict(r) for r in rows]}


class DnSignBody(BaseModel):
    customer_signature: str               # base64 data URL


@router.post("/api/admin/delivery-notes/{dn_id}/sign",
             dependencies=[Depends(require_admin)])
def admin_sign_dn(dn_id: str, body: DnSignBody):
    now = _now()
    with db.connect() as c:
        c.execute("""
            UPDATE delivery_notes SET customer_signature=?, customer_signed_at=?
            WHERE id=?
        """, (body.customer_signature, now, dn_id))
    return {"ok": True}


# ═════════════════════════════════════════════════════════════════════
# INVOICES
# ═════════════════════════════════════════════════════════════════════
def _create_invoice_from_so(so: dict) -> dict:
    """Auto-create a customer invoice when SO is confirmed."""
    inv_id = _id("INV")
    inv_num = next_doc_number("invoice")
    now = _now()
    due = (datetime.now(timezone.utc) + timedelta(days=14)).date().isoformat()
    # Fetch full SO row for line_items
    with db.connect() as c:
        so_row = c.execute("SELECT * FROM sales_orders WHERE id=?", (so["id"],)).fetchone()
        if not so_row:
            return None
        so_d = dict(so_row)
        c.execute("""
            INSERT INTO invoices
              (id, invoice_number, booking_id, quote_id, sales_order_id,
               customer_id, customer_name, customer_phone, customer_email,
               customer_address, line_items_json,
               subtotal, discount, vat_amount, amount, currency,
               payment_status, issued_at, due_at, terms, notes, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (inv_id, inv_num, so_d.get("booking_id"), so_d.get("quote_id"), so_d["id"],
              so_d.get("customer_id"), so_d.get("customer_name"),
              so_d.get("customer_phone"), so_d.get("customer_email"),
              so_d.get("customer_address"), so_d["line_items_json"],
              so_d["subtotal"], so_d["discount"], so_d["vat_amount"], so_d["total"],
              so_d["currency"], "unpaid", now, due,
              "Payment due within 14 days. UAE VAT 5% included.",
              so_d.get("notes"), now))
    return {"id": inv_id, "invoice_number": inv_num, "amount": so_d["total"]}


@router.get("/api/admin/invoices", dependencies=[Depends(require_admin)])
def admin_list_invoices(status: Optional[str] = None, customer_id: Optional[int] = None,
                         q: Optional[str] = None, from_date: Optional[str] = None,
                         to_date: Optional[str] = None, limit: int = 200):
    """status = unpaid | paid | overdue | cancelled"""
    where = ["1=1"]; args: list = []
    if status:
        if status == "overdue":
            where.append("payment_status='unpaid' AND due_at < ?")
            args.append(_now()[:10])
        else:
            where.append("payment_status=?"); args.append(status)
    if customer_id: where.append("customer_id=?"); args.append(customer_id)
    if from_date: where.append("created_at >= ?"); args.append(from_date)
    if to_date: where.append("created_at <= ?"); args.append(to_date + "T23:59:59")
    if q:
        where.append("(invoice_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)")
        args.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    with db.connect() as c:
        rows = c.execute(f"""
            SELECT id, invoice_number, customer_name, customer_phone,
                   subtotal, vat_amount, amount, currency, payment_status,
                   issued_at, due_at, paid_at, created_at
            FROM invoices WHERE {' AND '.join(where)}
            ORDER BY created_at DESC LIMIT ?
        """, (*args, limit)).fetchall()
        return {"ok": True, "count": len(rows), "items": [dict(r) for r in rows]}


@router.get("/api/admin/invoices/{inv_id}", dependencies=[Depends(require_admin)])
def admin_get_invoice(inv_id: str):
    with db.connect() as c:
        inv = c.execute("SELECT * FROM invoices WHERE id=?", (inv_id,)).fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="not found")
        return {"ok": True, "invoice": dict(inv)}


class MarkPaidBody(BaseModel):
    amount: Optional[float] = None        # null = full
    method: str = "bank_transfer"          # card | bank_transfer | cash | wallet | cheque
    reference_number: Optional[str] = None
    payment_date: Optional[str] = None
    notes: Optional[str] = None


@router.post("/api/admin/invoices/{inv_id}/mark-paid",
             dependencies=[Depends(require_admin)])
def admin_mark_invoice_paid(inv_id: str, body: MarkPaidBody):
    now = _now()
    with db.connect() as c:
        inv = c.execute("SELECT * FROM invoices WHERE id=?", (inv_id,)).fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="not found")
        amount = body.amount or inv["amount"]
        c.execute("""
            UPDATE invoices SET payment_status='paid', paid_at=? WHERE id=?
        """, (now, inv_id))
        # Register the payment
        c.execute("""
            INSERT INTO payment_registrations
              (payment_type, reference_type, reference_id,
               counterparty_id, counterparty_name, amount, currency,
               method, reference_number, payment_date, notes, created_at)
            VALUES ('customer_in', 'invoice', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (inv_id, inv["customer_id"], inv["customer_name"], amount,
              inv["currency"], body.method, body.reference_number,
              body.payment_date or now, body.notes, now))
    return {"ok": True}


# ═════════════════════════════════════════════════════════════════════
# PURCHASE ORDERS
# ═════════════════════════════════════════════════════════════════════
@router.get("/api/admin/purchase-orders", dependencies=[Depends(require_admin)])
def admin_list_pos(status: Optional[str] = None, vendor_id: Optional[int] = None,
                    q: Optional[str] = None, from_date: Optional[str] = None,
                    to_date: Optional[str] = None, limit: int = 200):
    """status = open | sent | accepted | completed | paid | cancelled"""
    where = ["1=1"]; args: list = []
    if status: where.append("status=?"); args.append(status)
    if vendor_id: where.append("vendor_id=?"); args.append(vendor_id)
    if from_date: where.append("created_at >= ?"); args.append(from_date)
    if to_date: where.append("created_at <= ?"); args.append(to_date + "T23:59:59")
    if q:
        where.append("(po_number LIKE ? OR vendor_name LIKE ?)")
        args.extend([f"%{q}%", f"%{q}%"])
    with db.connect() as c:
        rows = c.execute(f"""
            SELECT id, po_number, vendor_name, vendor_phone, service_id,
                   vendor_total, currency, status, sent_at, completed_at,
                   paid_at, created_at
            FROM purchase_orders WHERE {' AND '.join(where)}
            ORDER BY created_at DESC LIMIT ?
        """, (*args, limit)).fetchall()
        return {"ok": True, "count": len(rows), "items": [dict(r) for r in rows]}


@router.get("/api/admin/purchase-orders/{po_id}", dependencies=[Depends(require_admin)])
def admin_get_po(po_id: str):
    with db.connect() as c:
        po = c.execute("SELECT * FROM purchase_orders WHERE id=?", (po_id,)).fetchone()
        if not po:
            raise HTTPException(status_code=404, detail="not found")
        return {"ok": True, "purchase_order": dict(po)}


@router.post("/api/admin/purchase-orders/{po_id}/send-to-vendor",
             dependencies=[Depends(require_admin)])
def admin_send_po(po_id: str):
    now = _now()
    with db.connect() as c:
        c.execute("UPDATE purchase_orders SET status='sent', sent_at=?, updated_at=? WHERE id=?",
                  (now, now, po_id))
    return {"ok": True}


@router.post("/api/admin/purchase-orders/{po_id}/mark-paid",
             dependencies=[Depends(require_admin)])
def admin_mark_po_paid(po_id: str, body: MarkPaidBody):
    now = _now()
    with db.connect() as c:
        po = c.execute("SELECT * FROM purchase_orders WHERE id=?", (po_id,)).fetchone()
        if not po:
            raise HTTPException(status_code=404, detail="not found")
        amount = body.amount or po["vendor_total"]
        c.execute("""
            UPDATE purchase_orders SET status='paid', paid_at=?, updated_at=? WHERE id=?
        """, (now, now, po_id))
        c.execute("""
            INSERT INTO payment_registrations
              (payment_type, reference_type, reference_id,
               counterparty_id, counterparty_name, amount, currency,
               method, reference_number, payment_date, notes, created_at)
            VALUES ('vendor_out', 'purchase_order', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (po_id, po["vendor_id"], po["vendor_name"], amount,
              po["currency"], body.method, body.reference_number,
              body.payment_date or now, body.notes, now))
    return {"ok": True}


# ═════════════════════════════════════════════════════════════════════
# PAYMENTS
# ═════════════════════════════════════════════════════════════════════
@router.get("/api/admin/payments", dependencies=[Depends(require_admin)])
def admin_list_payments(payment_type: Optional[str] = None,
                         from_date: Optional[str] = None,
                         to_date: Optional[str] = None,
                         reference_id: Optional[str] = None,
                         limit: int = 200):
    """payment_type = customer_in | vendor_out;
    reference_id optional — pass invoice.id or po.id to list payments
    against a specific document (v1.24.163)."""
    where = ["1=1"]; args: list = []
    if payment_type: where.append("payment_type=?"); args.append(payment_type)
    if reference_id: where.append("reference_id=?"); args.append(reference_id)
    if from_date: where.append("payment_date >= ?"); args.append(from_date)
    if to_date: where.append("payment_date <= ?"); args.append(to_date + "T23:59:59")
    with db.connect() as c:
        rows = c.execute(f"""
            SELECT * FROM payment_registrations WHERE {' AND '.join(where)}
            ORDER BY payment_date DESC LIMIT ?
        """, (*args, limit)).fetchall()
        return {"ok": True, "count": len(rows), "items": [dict(r) for r in rows]}


class PaymentRegisterBody(BaseModel):
    """v1.24.163 — Register a manual payment in or out.

    Founder feedback: 'no option to register a payment in quotations or
    invoice, no method to register a manual vendor or customer payment,
    no option to link payments to existing code or invoices.' This
    closes that gap.
    """
    payment_type:   str                 # 'customer_in' | 'vendor_out'
    reference_type: str                 # 'invoice' | 'purchase_order'
    reference_id:   str                 # invoice.id or po.id
    amount:         float
    method:         str                 # card | bank_transfer | cash | wallet | cheque | stripe | ziina
    payment_date:   Optional[str] = None
    reference_number: Optional[str] = None   # bank txn / cheque #
    receipt_url:    Optional[str] = None     # screenshot/PDF of receipt
    notes:          Optional[str] = None


@router.post("/api/admin/payments/register", dependencies=[Depends(require_admin)])
def admin_register_payment(body: PaymentRegisterBody):
    """Register an inbound or outbound payment and auto-link it to an
    invoice or purchase order. The invoice/PO status is updated to
    'paid' if the cumulative payments now equal or exceed the doc total.

    Method values typical for UAE:
      card · bank_transfer · cash · wallet · cheque · stripe · ziina
    """
    if body.payment_type not in ("customer_in", "vendor_out"):
        raise HTTPException(400, "payment_type must be customer_in or vendor_out")
    if body.reference_type not in ("invoice", "purchase_order"):
        raise HTTPException(400, "reference_type must be invoice or purchase_order")
    if body.amount <= 0:
        raise HTTPException(400, "amount must be > 0")
    pay_date = body.payment_date or _now()
    # Stash receipt_url in notes JSON if provided — keeps schema additive.
    notes_blob = body.notes or ""
    if body.receipt_url:
        notes_blob = (notes_blob + " " if notes_blob else "") + f"[receipt:{body.receipt_url}]"
    with db.connect() as c:
        # Resolve counterparty + doc total for paid-status update.
        cp_id, cp_name, doc_total, status_col, status_tbl = None, None, 0.0, "payment_status", "invoices"
        if body.reference_type == "invoice":
            row = c.execute(
                "SELECT id, customer_id, customer_name, amount FROM invoices WHERE id=?",
                (body.reference_id,)).fetchone()
            if not row:
                raise HTTPException(404, "invoice not found")
            cp_id, cp_name, doc_total = row["customer_id"], row["customer_name"], row["amount"] or 0
            status_col, status_tbl = "payment_status", "invoices"
        else:
            row = c.execute(
                "SELECT id, vendor_id, vendor_name, vendor_total FROM purchase_orders WHERE id=?",
                (body.reference_id,)).fetchone()
            if not row:
                raise HTTPException(404, "purchase_order not found")
            cp_id, cp_name, doc_total = row["vendor_id"], row["vendor_name"], row["vendor_total"] or 0
            status_col, status_tbl = "status", "purchase_orders"
        c.execute("""
            INSERT INTO payment_registrations
              (payment_type, reference_type, reference_id, counterparty_id,
               counterparty_name, amount, currency, method, reference_number,
               payment_date, notes, created_at, created_by)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (body.payment_type, body.reference_type, body.reference_id,
              cp_id, cp_name, body.amount, "AED", body.method,
              body.reference_number, pay_date, notes_blob, _now(), "admin"))
        new_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        # Cumulative paid so far against this doc
        total_paid = c.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM payment_registrations
            WHERE reference_type=? AND reference_id=?
        """, (body.reference_type, body.reference_id)).fetchone()[0]
        new_status = None
        if total_paid >= doc_total - 0.01 and doc_total > 0:
            new_status = "paid"
        elif total_paid > 0:
            new_status = "partially_paid"
        if new_status:
            c.execute(f"UPDATE {status_tbl} SET {status_col}=? WHERE id=?",
                      (new_status, body.reference_id))
    return {
        "ok": True, "payment_id": new_id,
        "total_paid": round(total_paid, 2),
        "doc_total": round(doc_total, 2),
        "remaining": round(max(0, doc_total - total_paid), 2),
        "new_status": new_status,
    }


# ═════════════════════════════════════════════════════════════════════
# REPORTS
# ═════════════════════════════════════════════════════════════════════
# Credit-card processing fee (typical UAE rates: 2.5% Visa/MC, 2.9% Amex).
# Configurable via admin → config table key 'cc_fee_pct'. Applied to payment
# registrations where method='card' to compute net-after-fee revenue.
def _cc_fee_pct() -> float:
    try:
        with db.connect() as c:
            row = c.execute("SELECT value FROM config WHERE key='cc_fee_pct'").fetchone()
            if row:
                return float(row["value"])
    except Exception:
        pass
    return 2.5  # default UAE rate


@router.get("/api/admin/reports/profit", dependencies=[Depends(require_admin)])
def report_profit(from_date: Optional[str] = None, to_date: Optional[str] = None,
                   group_by: str = "month"):
    """Profit = customer revenue (subtotal, excl VAT) − vendor cost (PO total)
    − card-processing fees (where customer paid by card)
    grouped by day | week | month | quarter | year"""
    df = from_date or (datetime.now(timezone.utc) - timedelta(days=90)).date().isoformat()
    dt = to_date or _now()[:10]
    period_expr = {
        "day":     "date(s.created_at)",
        "week":    "strftime('%Y-W%W', s.created_at)",
        "month":   "strftime('%Y-%m', s.created_at)",
        "quarter": "(strftime('%Y', s.created_at) || '-Q' || ((cast(strftime('%m', s.created_at) as integer) - 1) / 3 + 1))",
        "year":    "strftime('%Y', s.created_at)",
    }.get(group_by, "strftime('%Y-%m', s.created_at)")

    cc_pct = _cc_fee_pct()
    with db.connect() as c:
        rows = c.execute(f"""
            SELECT
                {period_expr} AS period,
                SUM(s.subtotal) AS revenue_excl_vat,
                SUM(s.vat_amount) AS vat_collected,
                SUM(s.total) AS revenue_total,
                COALESCE(SUM((SELECT SUM(p.vendor_total) FROM purchase_orders p
                              WHERE p.sales_order_id=s.id)), 0) AS vendor_cost,
                COALESCE(SUM((SELECT SUM(pr.amount) FROM payment_registrations pr
                              WHERE pr.reference_type='invoice'
                                AND pr.reference_id IN (
                                    SELECT i.id FROM invoices i WHERE i.sales_order_id=s.id
                                )
                                AND pr.method='card')), 0) AS card_payments,
                COUNT(*) AS so_count
            FROM sales_orders s
            WHERE s.created_at >= ? AND s.created_at <= ?
              AND s.status != 'cancelled'
            GROUP BY period ORDER BY period DESC
        """, (df, dt + "T23:59:59")).fetchall()
        out = []
        total_revenue = 0; total_cost = 0; total_vat = 0; total_cc = 0; total_cc_fee = 0
        for r in rows:
            d = dict(r)
            d["revenue_excl_vat"] = round(d["revenue_excl_vat"] or 0, 2)
            d["vendor_cost"]      = round(d["vendor_cost"] or 0, 2)
            d["vat_collected"]    = round(d["vat_collected"] or 0, 2)
            d["card_payments"]    = round(d["card_payments"] or 0, 2)
            d["card_fees"]        = round(d["card_payments"] * cc_pct / 100, 2)
            d["profit"]           = round(d["revenue_excl_vat"] - d["vendor_cost"] - d["card_fees"], 2)
            d["margin_pct"]       = round((d["profit"] / d["revenue_excl_vat"] * 100), 1) if d["revenue_excl_vat"] else 0
            out.append(d)
            total_revenue += d["revenue_excl_vat"]
            total_cost += d["vendor_cost"]
            total_vat += d["vat_collected"]
            total_cc += d["card_payments"]
            total_cc_fee += d["card_fees"]
        totals = {
            "revenue_excl_vat": round(total_revenue, 2),
            "vendor_cost": round(total_cost, 2),
            "card_payments": round(total_cc, 2),
            "card_fees_deducted": round(total_cc_fee, 2),
            "cc_fee_pct_applied": cc_pct,
            "vat_collected_for_fta": round(total_vat, 2),
            "profit": round(total_revenue - total_cost - total_cc_fee, 2),
            "margin_pct": round((total_revenue - total_cost - total_cc_fee) / total_revenue * 100, 1) if total_revenue else 0,
        }
        return {"ok": True, "from": df, "to": dt, "group_by": group_by,
                "periods": out, "totals": totals}


@router.get("/api/admin/reports/outstanding",
             dependencies=[Depends(require_admin)])
def report_outstanding():
    """Outstanding A/R (unpaid customer invoices) + A/P (unpaid vendor POs)."""
    today = _now()[:10]
    with db.connect() as c:
        ar = c.execute(f"""
            SELECT id, invoice_number, customer_name, amount, currency,
                   due_at, created_at,
                   CASE WHEN due_at < ? THEN 1 ELSE 0 END AS is_overdue
            FROM invoices WHERE payment_status='unpaid'
            ORDER BY due_at ASC LIMIT 500
        """, (today,)).fetchall()
        ap = c.execute("""
            SELECT id, po_number, vendor_name, vendor_total AS amount,
                   currency, created_at, status
            FROM purchase_orders
            WHERE status IN ('open', 'sent', 'accepted', 'completed')
            ORDER BY created_at ASC LIMIT 500
        """).fetchall()
        ar_total = sum((r["amount"] or 0) for r in ar)
        ap_total = sum((r["amount"] or 0) for r in ap)
        return {
            "ok": True,
            "accounts_receivable": {"items": [dict(r) for r in ar],
                                    "total": round(ar_total, 2),
                                    "overdue_count": sum(1 for r in ar if r["is_overdue"])},
            "accounts_payable":    {"items": [dict(r) for r in ap],
                                    "total": round(ap_total, 2)},
            "net_working_capital": round(ar_total - ap_total, 2),
        }


@router.get("/api/admin/reports/top-customers",
             dependencies=[Depends(require_admin)])
def report_top_customers(from_date: Optional[str] = None, limit: int = 20):
    df = from_date or (datetime.now(timezone.utc) - timedelta(days=365)).date().isoformat()
    with db.connect() as c:
        rows = c.execute("""
            SELECT customer_id, customer_name, customer_phone,
                   COUNT(*) AS orders, SUM(total) AS revenue
            FROM sales_orders
            WHERE created_at >= ? AND status != 'cancelled'
            GROUP BY customer_id, customer_phone
            ORDER BY revenue DESC LIMIT ?
        """, (df, limit)).fetchall()
        return {"ok": True, "items": [dict(r) for r in rows]}


# v1.24.157 — Customer + vendor lookup/create for the admin commerce UI.
# Customer autocomplete pulls from the existing `customers` table; vendor
# picker pulls from `vendors`. One-click create-new keeps the founder out
# of the admin → customers tab when they're in the middle of a quote.

@router.get("/api/admin/customers/search", dependencies=[Depends(require_admin)])
def admin_customers_search(q: str = "", limit: int = 12):
    """Type-ahead search of existing customers by phone or name.
    Returns up to `limit` matches ordered by most-recent activity."""
    if not q or len(q.strip()) < 2:
        # Default: return the 10 most-recent customers
        with db.connect() as c:
            rows = c.execute("""
                SELECT id, name, phone, email, language, last_seen_at, created_at
                FROM customers
                ORDER BY COALESCE(last_seen_at, created_at) DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return {"ok": True, "items": [dict(r) for r in rows]}
    pattern = f"%{q.strip()}%"
    with db.connect() as c:
        rows = c.execute("""
            SELECT id, name, phone, email, language, last_seen_at, created_at
            FROM customers
            WHERE phone LIKE ? OR name LIKE ? OR email LIKE ?
            ORDER BY COALESCE(last_seen_at, created_at) DESC
            LIMIT ?
        """, (pattern, pattern, pattern, limit)).fetchall()
        return {"ok": True, "items": [dict(r) for r in rows]}


class CustomerCreateBody(BaseModel):
    name:    str
    phone:   str
    email:   Optional[str] = None
    language: Optional[str] = "en"


@router.post("/api/admin/customers/create", dependencies=[Depends(require_admin)])
def admin_customer_create(body: CustomerCreateBody):
    """1-click new-customer creation from the quote form."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    with db.connect() as c:
        # Idempotent — return existing if phone matches
        existing = c.execute("SELECT id, name, phone FROM customers WHERE phone=?",
                              (body.phone.strip(),)).fetchone()
        if existing:
            return {"ok": True, "existed": True, "id": existing["id"],
                    "name": existing["name"], "phone": existing["phone"]}
        try:
            cur = c.execute("""
                INSERT INTO customers (phone, name, email, language, created_at)
                VALUES (?,?,?,?,?)
            """, (body.phone.strip(), body.name.strip(),
                  (body.email or "").strip() or None,
                  body.language or "en", now))
            return {"ok": True, "existed": False, "id": cur.lastrowid,
                    "name": body.name.strip(), "phone": body.phone.strip()}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/admin/vendors/search", dependencies=[Depends(require_admin)])
def admin_vendors_search(q: str = "", service_id: Optional[str] = None, limit: int = 12):
    """Pick a vendor for a PO. Optional filter by service_id so the
    dropdown only shows vendors that offer the relevant service."""
    args: list = []
    where = ["v.is_active=1"]
    if q and len(q.strip()) >= 2:
        pattern = f"%{q.strip()}%"
        where.append("(v.name LIKE ? OR v.email LIKE ? OR v.phone LIKE ? OR v.company LIKE ?)")
        args.extend([pattern, pattern, pattern, pattern])
    if service_id:
        where.append("EXISTS (SELECT 1 FROM vendor_services vs WHERE vs.vendor_id=v.id AND vs.service_id=?)")
        args.append(service_id)
    with db.connect() as c:
        rows = c.execute(f"""
            SELECT v.id, v.name, v.email, v.phone, v.company, v.rating, v.completed_jobs,
                   (SELECT GROUP_CONCAT(service_id) FROM vendor_services WHERE vendor_id=v.id) AS services
            FROM vendors v
            WHERE {' AND '.join(where)}
            ORDER BY v.rating DESC, v.completed_jobs DESC
            LIMIT ?
        """, (*args, limit)).fetchall()
        return {"ok": True, "items": [dict(r) for r in rows]}


class VendorCreateBody(BaseModel):
    name:    str
    phone:   str
    email:   Optional[str] = None
    company: Optional[str] = None
    service_ids: Optional[list[str]] = None


@router.post("/api/admin/vendors/create", dependencies=[Depends(require_admin)])
def admin_vendor_create(body: VendorCreateBody):
    """1-click new-vendor creation from the assign-vendor flow."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    email = (body.email or f"vendor-{int(time.time())}@servia.ae").strip()
    with db.connect() as c:
        existing = c.execute("SELECT id, name FROM vendors WHERE email=? OR phone=?",
                              (email, body.phone.strip())).fetchone()
        if existing:
            return {"ok": True, "existed": True, "id": existing["id"], "name": existing["name"]}
        try:
            from .auth_users import hash_password
            tmp_pwd = hash_password("temp-pass-" + str(int(time.time())))
            cur = c.execute("""
                INSERT INTO vendors (email, password_hash, name, phone, company,
                                     rating, completed_jobs, is_active, is_approved, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (email, tmp_pwd, body.name.strip(), body.phone.strip(),
                  (body.company or body.name).strip(), 5.0, 0, 1, 1, now))
            vid = cur.lastrowid
            for svc in (body.service_ids or []):
                try:
                    c.execute("INSERT INTO vendor_services (vendor_id, service_id, area) VALUES (?,?,?)",
                              (vid, svc, "*"))
                except Exception: pass
            return {"ok": True, "existed": False, "id": vid, "name": body.name.strip()}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/admin/seed-commerce-demo", dependencies=[Depends(require_admin)])
def admin_seed_commerce_demo():
    """v1.24.156 — Insert demo customers/vendors/quotes/SOs/DNs/invoices/POs/
    payments so the admin commerce tabs show real-looking data. Idempotent —
    re-running won't duplicate. Call POST /api/admin/seed-commerce-demo with
    admin auth to trigger. Use /clear-commerce-demo to remove."""
    from . import seed_commerce_demo
    return seed_commerce_demo.seed()


@router.post("/api/admin/clear-commerce-demo", dependencies=[Depends(require_admin)])
def admin_clear_commerce_demo():
    """Remove all demo-seeded commerce rows."""
    from . import seed_commerce_demo
    return seed_commerce_demo.clear()


@router.get("/api/admin/reports/top-vendors",
             dependencies=[Depends(require_admin)])
def report_top_vendors(from_date: Optional[str] = None, limit: int = 20):
    df = from_date or (datetime.now(timezone.utc) - timedelta(days=365)).date().isoformat()
    with db.connect() as c:
        rows = c.execute("""
            SELECT vendor_id, vendor_name,
                   COUNT(*) AS po_count, SUM(vendor_total) AS payouts
            FROM purchase_orders
            WHERE created_at >= ? AND status != 'cancelled'
            GROUP BY vendor_id
            ORDER BY payouts DESC LIMIT ?
        """, (df, limit)).fetchall()
        return {"ok": True, "items": [dict(r) for r in rows]}


# ═════════════════════════════════════════════════════════════════════
# PRINTABLE TEMPLATES (one-click view / Ctrl+P → PDF / share)
# ═════════════════════════════════════════════════════════════════════
def _brand_block() -> dict:
    """Read brand info from config table — name, phone, email, address.
    These centralize all phone/email references for the printed documents.
    Phase 1 of the v1.24.142 centralization push."""
    out = {"name": "Servia", "phone": "", "email": "", "address": "", "trn": "", "logo_url": "/mascot.svg"}
    try:
        with db.connect() as c:
            rows = c.execute("SELECT key, value FROM config WHERE key IN ("
                             "'brand_name','contact_phone','contact_email',"
                             "'company_address','vat_trn','brand_logo_url')").fetchall()
            for r in rows:
                k = r["key"]; v = r["value"]
                if k == "brand_name":     out["name"] = v
                elif k == "contact_phone": out["phone"] = v
                elif k == "contact_email": out["email"] = v
                elif k == "company_address": out["address"] = v
                elif k == "vat_trn":      out["trn"] = v
                elif k == "brand_logo_url": out["logo_url"] = v
    except Exception:
        pass
    return out


def _print_css() -> str:
    """v1.24.165 — Redesign per founder feedback: 'design is bad, no logo,
    no linking — add mascot watermark + interactive feel'."""
    return """<style>
        *,*::before,*::after{box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:0;background:linear-gradient(180deg,#ECFDF5 0%,#F1F5F9 100%);color:#0F172A;line-height:1.5;-webkit-print-color-adjust:exact;print-color-adjust:exact}
        .doc{background:#fff;max-width:880px;margin:24px auto;padding:48px;box-shadow:0 16px 48px rgba(15,118,110,.12);border-radius:14px;position:relative;overflow:hidden}
        /* v1.24.165 — Servia mascot watermark, very faint */
        .doc::before{
            content:"";position:absolute;top:50%;right:-80px;width:480px;height:480px;
            background:url("/brand/servia-avatar-512x512.png") center/contain no-repeat;
            opacity:.05;pointer-events:none;transform:translateY(-50%) rotate(-8deg);
            z-index:0;
        }
        .doc>*{position:relative;z-index:1}
        .hd{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:3px solid #0F766E;padding-bottom:20px;margin-bottom:18px;gap:24px}
        .hd .left{flex:1}
        .hd .right{text-align:right}
        .hd .logo{display:flex;align-items:center;gap:10px;margin-bottom:10px}
        .hd .logo img{height:38px;width:auto;background:transparent}
        .hd .logo .wm{font-size:18px;font-weight:900;color:#0F766E;letter-spacing:-.02em}
        .hd h1{font-size:30px;margin:6px 0 4px;letter-spacing:-.02em;color:#0F766E;font-weight:800}
        .hd .docnum{font-size:14px;color:#64748B;font-weight:700;font-family:Menlo,monospace;background:#F0FDFA;padding:4px 10px;border-radius:6px;display:inline-block;margin-top:6px;border:1px solid #99F6E4}
        .hd .brand{font-size:18px;font-weight:800;color:#0F172A;margin-bottom:4px}
        .hd .meta{font-size:12px;color:#64748B;line-height:1.7}
        .hd .meta b{color:#334155}
        /* v1.24.165 — Cross-doc linking breadcrumb strip */
        .links-strip{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px;padding:10px 14px;background:linear-gradient(90deg,#F0FDF4 0%,#ECFDF5 100%);border:1px solid #BBF7D0;border-radius:10px;font-size:11.5px}
        .links-strip .lab{font-weight:800;color:#166534;text-transform:uppercase;letter-spacing:.06em;margin-right:6px;display:flex;align-items:center}
        .links-strip a{background:#fff;border:1px solid #86EFAC;padding:4px 10px;border-radius:99px;color:#0F766E;font-weight:700;text-decoration:none;display:inline-flex;align-items:center;gap:4px}
        .links-strip a:hover{background:#F0FDFA;border-color:#0F766E}
        .links-strip a.this{background:#0F766E;color:#fff;border-color:#0F766E}
        .grid2{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px}
        .card{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:14px 16px}
        .card .lab{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:#64748B;font-weight:800;margin-bottom:4px}
        .card .val{font-size:14px;font-weight:600;color:#0F172A;line-height:1.5}
        table.lines{width:100%;border-collapse:collapse;margin:18px 0;font-size:13px}
        table.lines th{background:#0F172A;color:#fff;padding:10px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;font-weight:700}
        table.lines th:last-child,table.lines td:last-child{text-align:right}
        table.lines td{padding:10px 12px;border-bottom:1px solid #E2E8F0}
        table.lines tbody tr:nth-child(even){background:#FAFBFC}
        .totals{margin-top:12px;display:flex;justify-content:flex-end}
        .totals table{font-size:13px;min-width:280px}
        .totals td{padding:6px 12px}
        .totals tr.grand td{font-size:18px;font-weight:800;color:#0F766E;border-top:2px solid #0F766E;padding-top:10px}
        .status-row{margin:18px 0;padding:12px 16px;background:#F0FDFA;border-left:4px solid #0F766E;border-radius:6px;font-size:13px;font-weight:600;color:#134E4A}
        .status-row.unpaid{background:#FEF3C7;border-left-color:#F59E0B;color:#7C2D12}
        .status-row.paid{background:#D1FAE5;border-left-color:#10B981;color:#065F46}
        .notes{margin-top:24px;font-size:12px;color:#64748B;line-height:1.7;border-top:1px dashed #CBD5E1;padding-top:14px}
        .notes b{color:#334155;display:block;margin-bottom:4px}
        .footer{margin-top:28px;text-align:center;font-size:11px;color:#94A3B8;border-top:1px solid #E2E8F0;padding-top:14px}
        .signature{margin-top:32px;display:grid;grid-template-columns:1fr 1fr;gap:32px}
        .sigbox{border-top:1px solid #CBD5E1;padding-top:8px;font-size:11px;color:#64748B}
        .sigbox img{max-width:200px;max-height:80px;display:block;margin-bottom:4px;background:#fff;border:1px solid #E2E8F0;padding:4px;border-radius:4px}
        .actions{position:fixed;top:14px;right:14px;display:flex;gap:8px;z-index:1000}
        .actions button,.actions a{background:#0F766E;color:#fff;border:0;padding:9px 14px;border-radius:8px;font-size:12.5px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:5px;box-shadow:0 4px 12px rgba(15,118,110,.3)}
        .actions a.share-wa{background:#25D366}
        .actions a.share-em{background:#3B82F6}
        .actions button:hover,.actions a:hover{filter:brightness(1.1)}
        @media print{
            .actions{display:none}
            body{background:#fff}
            .doc{box-shadow:none;margin:0;border-radius:0;max-width:none;padding:24px}
        }
    </style>"""


def _share_buttons(doc_type: str, doc_id: str, doc_num: str, recipient_phone: str | None,
                    recipient_email: str | None, recipient_name: str | None) -> str:
    """Generate one-click share + print buttons for a printable document."""
    domain = "servia.ae"   # could read from brand config
    public_url = f"https://{domain}/admin/print/{doc_type}/{doc_id}"
    wa_text = f"Hi {recipient_name or ''}, your {doc_type} {doc_num} from Servia: {public_url}".strip()
    wa_link = f"https://wa.me/{(recipient_phone or '').lstrip('+').replace(' ','')}?text={_url_encode(wa_text)}"
    email_subject = f"Servia · {doc_type.replace('-',' ').title()} {doc_num}"
    email_body = f"Dear {recipient_name or 'customer'},\n\nPlease find your {doc_type} {doc_num} below or at:\n{public_url}\n\nServia"
    em_link = f"mailto:{recipient_email or ''}?subject={_url_encode(email_subject)}&body={_url_encode(email_body)}"
    parts = [
        f'<button onclick="window.print()">🖨 Print / Save PDF</button>',
    ]
    if recipient_phone:
        parts.append(f'<a class="share-wa" href="{wa_link}" target="_blank">💬 WhatsApp</a>')
    if recipient_email:
        parts.append(f'<a class="share-em" href="{em_link}">📧 Email</a>')
    return f'<div class="actions">{"".join(parts)}</div>'


def _url_encode(s: str) -> str:
    from urllib.parse import quote
    return quote(s or "")


def _render_line_items(items: list[dict], for_doc: str = "invoice") -> str:
    """Render line_items as a table. for_doc = 'invoice' or 'po' (vendor view)."""
    if not items:
        return '<p style="color:#94A3B8;font-style:italic">No line items.</p>'
    if for_doc == "po":
        # PO uses vendor_rate (what we pay vendor)
        rows = ""
        for it in items:
            qty = it.get("qty", 1)
            rate = it.get("vendor_rate", it.get("unit_price", 0))
            total = it.get("line_total", qty * rate)
            rows += f"""<tr>
                <td>{_html_escape(it.get("svc_id") or it.get("name") or "Service")}</td>
                <td>{qty}</td>
                <td>AED {rate:,.2f}</td>
                <td>AED {total:,.2f}</td>
            </tr>"""
        return f"""<table class="lines">
            <thead><tr><th>Service</th><th>Qty</th><th>Vendor rate</th><th>Total</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>"""
    else:
        rows = ""
        for it in items:
            qty = it.get("qty", 1)
            rate = it.get("unit_price", 0)
            total = it.get("line_total", qty * rate)
            rows += f"""<tr>
                <td>{_html_escape(it.get("name") or it.get("svc_id") or "Service")}</td>
                <td>{qty}</td>
                <td>AED {rate:,.2f}</td>
                <td>AED {total:,.2f}</td>
            </tr>"""
        return f"""<table class="lines">
            <thead><tr><th>Description</th><th>Qty</th><th>Unit price</th><th>Total</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>"""


def _html_escape(s: str) -> str:
    import html as _h
    return _h.escape(str(s or ""))


def _format_dt(iso: str) -> str:
    if not iso: return "—"
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d %b %Y · %H:%M")
    except Exception:
        return iso[:16]


def _format_d(iso: str) -> str:
    if not iso: return "—"
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d %b %Y")
    except Exception:
        return iso[:10]


def _print_doc_chain(doc_type: str, row: dict) -> str:
    """v1.24.166 — Cross-document link strip on every printable.
    Founder said: 'there is no linking showing between quote to invoice
    to PO or delivery or sale order'. Now every printable shows the
    chain at the top with clickable links to other docs."""
    cur_num = (row.get("quote_number") or row.get("so_number") or
               row.get("invoice_number") or row.get("dn_number") or
               row.get("po_number") or row.get("id") or "—")
    links: list[tuple[str, str, str]] = []   # (label, num, url) with this-doc highlighted
    with db.connect() as c:
        # Walk OUTWARD from the current doc in both directions.
        # Find the central SO + the source Quote first.
        so_id = row.get("sales_order_id") if doc_type != "sales-order" else row.get("id")
        quote_id = (row.get("quote_id") if doc_type != "quote" else row.get("id"))
        if doc_type == "sales-order":
            quote_id = row.get("quote_id")
        # Quote
        if quote_id:
            q = c.execute(
                "SELECT id, quote_number FROM quotes WHERE id=?", (quote_id,)
            ).fetchone()
            if q:
                links.append(("📝 Quote", q["quote_number"],
                              f"/admin/print/quote/{q['id']}"))
        elif doc_type == "quote":
            links.append(("📝 Quote", row.get("quote_number") or "—",
                          f"/admin/print/quote/{row.get('id')}"))
        # Sales Order
        if so_id and doc_type != "sales-order":
            so = c.execute(
                "SELECT id, so_number FROM sales_orders WHERE id=?", (so_id,)
            ).fetchone()
            if so:
                links.append(("📋 Sales Order", so["so_number"],
                              f"/admin/print/sales-order/{so['id']}"))
        elif doc_type == "sales-order":
            links.append(("📋 Sales Order", row.get("so_number") or "—",
                          f"/admin/print/sales-order/{row.get('id')}"))
        # Invoices linked to the SO
        if so_id:
            for inv in c.execute(
                "SELECT id, invoice_number FROM invoices WHERE sales_order_id=?",
                (so_id,)).fetchall():
                links.append(("📄 Invoice", inv["invoice_number"],
                              f"/admin/print/invoice/{inv['id']}"))
        elif doc_type == "invoice":
            links.append(("📄 Invoice", row.get("invoice_number") or "—",
                          f"/admin/print/invoice/{row.get('id')}"))
        # Service Notes (DNs)
        if so_id:
            for dn in c.execute(
                "SELECT id, dn_number FROM delivery_notes WHERE sales_order_id=?",
                (so_id,)).fetchall():
                links.append(("✅ Service Note", dn["dn_number"],
                              f"/admin/print/delivery-note/{dn['id']}"))
        elif doc_type == "delivery-note":
            links.append(("✅ Service Note", row.get("dn_number") or "—",
                          f"/admin/print/delivery-note/{row.get('id')}"))
        # POs
        if so_id:
            for po in c.execute(
                "SELECT id, po_number FROM purchase_orders WHERE sales_order_id=?",
                (so_id,)).fetchall():
                links.append(("🛒 Purchase Order", po["po_number"],
                              f"/admin/print/purchase-order/{po['id']}"))
        elif doc_type == "purchase-order":
            links.append(("🛒 Purchase Order", row.get("po_number") or "—",
                          f"/admin/print/purchase-order/{row.get('id')}"))
    if not links:
        return ""
    # Deduplicate (by num) preserving order
    seen, out = set(), []
    for lbl, num, url in links:
        if num in seen: continue
        seen.add(num); out.append((lbl, num, url))
    chips = []
    for lbl, num, url in out:
        is_this = num == cur_num
        cls = "this" if is_this else ""
        chips.append(f'<a class="{cls}" href="{url}" target="_blank">{lbl} {_html_escape(num)}</a>')
    return (
        '<div class="links-strip">'
        '<span class="lab">🔗 Linked:</span>'
        + "".join(chips) +
        '</div>'
    )


def _render_quote_or_invoice_print(doc_type: str, row: dict) -> str:
    """Render a printable quote, invoice, or sales-order. They share enough
    structure to use the same template with a doc-type-specific header."""
    brand = _brand_block()
    line_items = []
    try:
        line_items = json.loads(row.get("line_items_json") or "[]")
    except Exception:
        pass
    doc_label = {
        "quote":         ("QUOTATION", "quote_number"),
        "sales-order":   ("SALES ORDER", "so_number"),
        "invoice":       ("TAX INVOICE", "invoice_number"),
    }.get(doc_type, ("DOCUMENT", "id"))
    doc_num = row.get(doc_label[1]) or row.get("id") or "—"
    paid_status = ""
    if doc_type == "invoice":
        st = row.get("payment_status", "unpaid")
        paid_status = f'<div class="status-row {st}">Status: <b>{st.upper()}</b>'
        if row.get("paid_at"):
            paid_status += f' · paid on {_format_d(row["paid_at"])}'
        elif row.get("due_at"):
            paid_status += f' · due {_format_d(row["due_at"])}'
        paid_status += "</div>"

    share = _share_buttons(doc_type, row["id"], doc_num,
                           row.get("customer_phone"), row.get("customer_email"),
                           row.get("customer_name"))

    chain_strip = _print_doc_chain(doc_type, row)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow">
<title>{doc_label[0]} {doc_num} · {brand['name']}</title>
{_print_css()}
</head><body>
{share}
<div class="doc">
  <div class="hd">
    <div class="left">
      <div class="logo">
        <img src="/brand/servia-logo-full.svg" alt="Servia" onerror="this.style.display='none'">
      </div>
      <h1>{doc_label[0]}</h1>
      <span class="docnum">{doc_num}</span>
    </div>
    <div class="right">
      <div class="brand">{_html_escape(brand['name'])}</div>
      <div class="meta">
        {_html_escape(brand['address']) or '&nbsp;'}<br>
        {('☎ ' + _html_escape(brand['phone'])) if brand['phone'] else ''}<br>
        {('✉ ' + _html_escape(brand['email'])) if brand['email'] else ''}<br>
        {('<b>TRN:</b> ' + _html_escape(brand['trn'])) if brand['trn'] else ''}
      </div>
    </div>
  </div>
  {chain_strip}

  <div class="grid2">
    <div class="card">
      <div class="lab">Bill To</div>
      <div class="val">
        <b>{_html_escape(row.get('customer_name') or '—')}</b><br>
        {('☎ ' + _html_escape(row.get('customer_phone') or ''))}<br>
        {('✉ ' + _html_escape(row.get('customer_email') or ''))}<br>
        {_html_escape(row.get('customer_address') or '')}
      </div>
    </div>
    <div class="card">
      <div class="lab">Document details</div>
      <div class="val">
        <b>Issue date:</b> {_format_d(row.get('issued_at') or row.get('confirmed_at') or row.get('created_at'))}<br>
        {('<b>Due date:</b> ' + _format_d(row['due_at']) + '<br>') if row.get('due_at') else ''}
        {('<b>Valid until:</b> ' + _format_d(row['valid_until']) + '<br>') if row.get('valid_until') else ''}
        <b>Currency:</b> {row.get('currency','AED')}
      </div>
    </div>
  </div>

  {paid_status}
  {_render_line_items(line_items, for_doc='invoice')}

  <div class="totals">
    <table>
      <tr><td>Subtotal</td><td><b>AED {row.get('subtotal',0):,.2f}</b></td></tr>
      {('<tr><td>Discount</td><td>−AED ' + f"{row['discount']:,.2f}" + '</td></tr>') if row.get('discount') else ''}
      <tr><td>VAT (5%)</td><td>AED {row.get('vat_amount',0):,.2f}</td></tr>
      <tr class="grand"><td>TOTAL</td><td>AED {(row.get('amount') or row.get('total') or 0):,.2f}</td></tr>
    </table>
  </div>

  {('<div class="notes"><b>Terms</b>' + _html_escape(row.get('terms') or '')) if row.get('terms') else ''}
  {('</div><div class="notes"><b>Notes</b>' + _html_escape(row.get('notes') or '') + '</div>') if row.get('notes') else ('</div>' if row.get('terms') else '')}

  <div class="footer">{_html_escape(brand['name'])} · Computer-generated document · This document is valid without signature.</div>
</div>
</body></html>"""


def _render_dn_print(row: dict) -> str:
    brand = _brand_block()
    line_items = []
    try:
        line_items = json.loads(row.get("line_items_json") or "[]")
    except Exception:
        pass
    sig_html = ""
    if row.get("customer_signature"):
        sig_html = f'<div class="sigbox"><img src="{row["customer_signature"]}" alt="signature"><b>Customer signature</b><br>{_format_dt(row.get("customer_signed_at"))}</div>'
    else:
        sig_html = '<div class="sigbox" style="min-height:80px"><br><b>Customer signature</b><br>(pending)</div>'

    photo_html = ""
    try:
        photos = json.loads(row.get("photo_urls_json") or "[]")
        if photos:
            photo_html = '<div class="notes"><b>Proof photos</b><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">'
            for u in photos:
                photo_html += f'<img src="{_html_escape(u)}" style="width:120px;height:90px;object-fit:cover;border-radius:6px;border:1px solid #E2E8F0">'
            photo_html += '</div></div>'
    except Exception:
        pass

    customer_phone = None
    customer_email = None
    customer_name = None
    so_id = row.get("sales_order_id")
    if so_id:
        try:
            with db.connect() as c:
                so = c.execute("SELECT customer_name, customer_phone, customer_email FROM sales_orders WHERE id=?", (so_id,)).fetchone()
                if so:
                    customer_name = so["customer_name"]; customer_phone = so["customer_phone"]; customer_email = so["customer_email"]
        except Exception:
            pass

    share = _share_buttons("delivery-note", row["id"], row.get("dn_number") or row["id"],
                           customer_phone, customer_email, customer_name)

    chain_strip = _print_doc_chain("delivery-note", row)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow">
<title>Service Note {row.get('dn_number')} · {brand['name']}</title>
{_print_css()}
</head><body>
{share}
<div class="doc">
  <div class="hd">
    <div class="left">
      <div class="logo">
        <img src="/brand/servia-logo-full.svg" alt="Servia" onerror="this.style.display='none'">
      </div>
      <h1>SERVICE COMPLETION NOTE</h1>
      <span class="docnum">{_html_escape(row.get('dn_number') or '—')}</span>
    </div>
    <div class="right">
      <div class="brand">{_html_escape(brand['name'])}</div>
      <div class="meta">
        {_html_escape(brand['address'])}<br>
        {('☎ ' + _html_escape(brand['phone'])) if brand['phone'] else ''}<br>
        {('✉ ' + _html_escape(brand['email'])) if brand['email'] else ''}
      </div>
    </div>
  </div>
  {chain_strip}

  <div class="card" style="margin-bottom:24px">
    <div class="lab">Delivered on</div>
    <div class="val"><b>{_format_dt(row.get('delivered_at'))}</b>
      {('· linked to SO ' + _html_escape(row['sales_order_id'])) if row.get('sales_order_id') else ''}
    </div>
  </div>

  <div class="status-row paid">✓ This document confirms the service was delivered. Customer signature below acknowledges receipt.</div>

  {_render_line_items(line_items, for_doc='invoice')}
  {photo_html}
  {('<div class="notes"><b>Notes</b>' + _html_escape(row.get('notes') or '') + '</div>') if row.get('notes') else ''}

  <div class="signature">
    {sig_html}
    <div class="sigbox" style="min-height:80px"><br><b>Servia representative</b><br>{_html_escape(brand['name'])}</div>
  </div>

  <div class="footer">{_html_escape(brand['name'])} · DN-{_html_escape(row.get('dn_number',''))} · Computer-generated.</div>
</div>
</body></html>"""


def _render_po_print(row: dict) -> str:
    brand = _brand_block()
    line_items = []
    try:
        line_items = json.loads(row.get("line_items_json") or "[]")
    except Exception:
        pass
    share = _share_buttons("purchase-order", row["id"], row.get("po_number") or row["id"],
                           row.get("vendor_phone"), None, row.get("vendor_name"))
    status_class = "paid" if row.get("status") == "paid" else ("unpaid" if row.get("status") in ("sent", "open", "accepted") else "paid")
    chain_strip = _print_doc_chain("purchase-order", row)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow">
<title>Purchase Order {row.get('po_number')} · {brand['name']}</title>
{_print_css()}
</head><body>
{share}
<div class="doc">
  <div class="hd">
    <div class="left">
      <div class="logo">
        <img src="/brand/servia-logo-full.svg" alt="Servia" onerror="this.style.display='none'">
      </div>
      <h1>PURCHASE ORDER</h1>
      <span class="docnum">{_html_escape(row.get('po_number') or '—')}</span>
    </div>
    <div class="right">
      <div class="brand">{_html_escape(brand['name'])}</div>
      <div class="meta">
        {_html_escape(brand['address'])}<br>
        {('☎ ' + _html_escape(brand['phone'])) if brand['phone'] else ''}<br>
        {('✉ ' + _html_escape(brand['email'])) if brand['email'] else ''}<br>
        {('<b>TRN:</b> ' + _html_escape(brand['trn'])) if brand['trn'] else ''}
      </div>
    </div>
  </div>
  {chain_strip}

  <div class="grid2">
    <div class="card">
      <div class="lab">Vendor</div>
      <div class="val">
        <b>{_html_escape(row.get('vendor_name') or '—')}</b><br>
        {('☎ ' + _html_escape(row.get('vendor_phone') or ''))}<br>
        ID: #{row.get('vendor_id')}
      </div>
    </div>
    <div class="card">
      <div class="lab">PO details</div>
      <div class="val">
        <b>Issued:</b> {_format_d(row.get('created_at'))}<br>
        <b>Status:</b> {_html_escape((row.get('status') or '').upper())}<br>
        {('<b>Linked SO:</b> ' + _html_escape(row['sales_order_id']) + '<br>') if row.get('sales_order_id') else ''}
        <b>Currency:</b> {row.get('currency','AED')}
      </div>
    </div>
  </div>

  <div class="status-row {status_class}">Pay this vendor: <b>AED {row.get('vendor_total',0):,.2f}</b>
    {(' · paid on ' + _format_d(row['paid_at'])) if row.get('paid_at') else ' · pending'}</div>

  {_render_line_items(line_items, for_doc='po')}

  <div class="totals">
    <table>
      <tr class="grand"><td>VENDOR TOTAL</td><td>AED {row.get('vendor_total',0):,.2f}</td></tr>
    </table>
  </div>

  {('<div class="notes"><b>Terms</b>' + _html_escape(row.get('terms') or '') + '</div>') if row.get('terms') else ''}
  {('<div class="notes"><b>Notes</b>' + _html_escape(row.get('notes') or '') + '</div>') if row.get('notes') else ''}

  <div class="footer">{_html_escape(brand['name'])} · {_html_escape(row.get('po_number',''))} · This PO is binding upon vendor acceptance.</div>
</div>
</body></html>"""


@router.get("/admin/print/quote/{doc_id}", response_class=HTMLResponse,
             dependencies=[Depends(require_admin)])
def print_quote(doc_id: str):
    with db.connect() as c:
        row = c.execute("SELECT * FROM quotes WHERE id=?", (doc_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
    return HTMLResponse(_render_quote_or_invoice_print("quote", dict(row)))


@router.get("/admin/print/sales-order/{doc_id}", response_class=HTMLResponse,
             dependencies=[Depends(require_admin)])
def print_so(doc_id: str):
    with db.connect() as c:
        row = c.execute("SELECT * FROM sales_orders WHERE id=?", (doc_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
    return HTMLResponse(_render_quote_or_invoice_print("sales-order", dict(row)))


@router.get("/admin/print/invoice/{doc_id}", response_class=HTMLResponse,
             dependencies=[Depends(require_admin)])
def print_invoice(doc_id: str):
    with db.connect() as c:
        row = c.execute("SELECT * FROM invoices WHERE id=?", (doc_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
    return HTMLResponse(_render_quote_or_invoice_print("invoice", dict(row)))


@router.get("/admin/print/delivery-note/{doc_id}", response_class=HTMLResponse,
             dependencies=[Depends(require_admin)])
def print_dn(doc_id: str):
    with db.connect() as c:
        row = c.execute("SELECT * FROM delivery_notes WHERE id=?", (doc_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
    return HTMLResponse(_render_dn_print(dict(row)))


@router.get("/admin/print/purchase-order/{doc_id}", response_class=HTMLResponse,
             dependencies=[Depends(require_admin)])
def print_po(doc_id: str):
    with db.connect() as c:
        row = c.execute("SELECT * FROM purchase_orders WHERE id=?", (doc_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
    return HTMLResponse(_render_po_print(dict(row)))
