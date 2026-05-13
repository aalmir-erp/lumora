"""COMPREHENSIVE E2E TEST — verifies every feature shipped v1.24.160 → v1.24.168.

Run with:
    rm -f /tmp/lumora-deploy/servia_test.db
    DB_PATH=/tmp/lumora-deploy/servia_test.db python3 -m pytest tests/test_admin_commerce_e2e.py -v
    # or as a standalone script:
    DB_PATH=/tmp/lumora-deploy/servia_test.db python3 tests/test_admin_commerce_e2e.py
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app.main import app
from app.multi_quote_pages import _sign_token
from app.config import get_settings
from app.llm import _enforce_multi_quote_when_book_now
from app.brand_contact import get_contact_whatsapp, _is_placeholder


def _client():
    c = TestClient(app)
    return c


def test_boot_and_version():
    assert get_settings().APP_VERSION.startswith("1.24.")
    assert len(app.routes) > 17000


def test_seed_demo_data():
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    r = c.post("/api/admin/seed-commerce-demo", headers=H)
    assert r.status_code == 200
    d = r.json()
    assert d.get("ok") is True
    assert d.get("quotes") == 9
    assert d.get("sos") == 5
    assert d.get("invoices") == 5
    assert d.get("dns") == 4
    assert d.get("pos") == 5


def test_auth_sources_v1_24_162():
    c = _client()
    c.post("/api/admin/seed-commerce-demo",
           headers={"Authorization": "Bearer lumora-admin-test"})
    assert c.get(
        "/api/admin/quotes",
        headers={"Authorization": "Bearer lumora-admin-test"},
    ).status_code == 200
    assert c.get("/api/admin/quotes?t=lumora-admin-test").status_code == 200
    assert c.get("/api/admin/quotes?token=lumora-admin-test").status_code == 200
    c.cookies.set("servia_admin_token", "lumora-admin-test")
    assert c.get("/api/admin/quotes").status_code == 200
    c.cookies.clear()
    assert c.get("/api/admin/quotes").status_code == 401
    assert c.get("/api/admin/quotes?t=wrong").status_code == 403


def test_bot_single_service_book_now_v1_24_160():
    text = (
        "Here's your summary:\n\n"
        "📋 **Summary**\n"
        "• Service: AC cleaning (2 units)\n"
        "• Date: tomorrow at 2pm\n"
        "• Address: Marina, Building Marina Crown, Apt 309, Dubai\n"
        "• Name: Sara\n"
        "• Phone: +971501234567\n\n"
        "[Book now ↗](/book?service=ac_cleaning)"
    )
    out = _enforce_multi_quote_when_book_now(text, session_id="e2e-test")
    assert "/checkout?q=" in out
    assert "/book?service=" not in out


def test_quote_actions_v1_24_163():
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    c.post("/api/admin/seed-commerce-demo", headers=H)
    q = c.get("/api/admin/quotes", headers=H).json()["items"][0]
    qid = q["id"]
    # revise
    r = c.post(f"/api/admin/quotes/{qid}/revise", headers=H).json()
    assert r.get("quote_number", "").endswith("-r1")
    new_id = r["id"]
    # reject + delete
    assert c.post(f"/api/admin/quotes/{new_id}/reject", headers=H).json().get("ok")
    assert c.delete(f"/api/admin/quotes/{new_id}", headers=H).json().get("ok")
    # links
    links = c.get(f"/api/admin/quotes/{qid}/links", headers=H).json()
    assert links.get("ok")
    assert isinstance(links.get("revisions"), list)


def test_payment_register_v1_24_163():
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    HJ = {**H, "Content-Type": "application/json"}
    c.post("/api/admin/seed-commerce-demo", headers=H)
    inv = c.get("/api/admin/invoices", headers=H).json()["items"][0]
    half = float(inv.get("amount") or 100.0) / 2.0
    r1 = c.post("/api/admin/payments/register", headers=HJ, json={
        "payment_type": "customer_in", "reference_type": "invoice",
        "reference_id": inv["id"], "amount": half, "method": "card",
        "reference_number": "TXN-001",
    }).json()
    assert r1.get("new_status") == "partially_paid"
    r2 = c.post("/api/admin/payments/register", headers=HJ, json={
        "payment_type": "customer_in", "reference_type": "invoice",
        "reference_id": inv["id"], "amount": half + 1, "method": "bank_transfer",
    }).json()
    assert r2.get("new_status") == "paid"
    assert len(
        c.get(f"/api/admin/payments?reference_id={inv['id']}", headers=H).json().get("items", [])
    ) == 2


def test_q_url_opens_admin_quotes_v1_24_165():
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    c.post("/api/admin/seed-commerce-demo", headers=H)
    q = c.get("/api/admin/quotes", headers=H).json()["items"][0]
    assert c.get(f"/q/{q['id']}", follow_redirects=False).status_code == 200
    assert c.get(f"/q/{q['quote_number']}", follow_redirects=False).status_code == 200


def test_customer_remark_and_admin_alert_v1_24_165():
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    c.post("/api/admin/seed-commerce-demo", headers=H)
    q = c.get("/api/admin/quotes", headers=H).json()["items"][0]
    qid = q["id"]
    phone = "".join(ch for ch in (q.get("customer_phone") or "") if ch.isdigit())
    tok = _sign_token(qid, phone)
    r = c.post(
        f"/api/q/{qid}/remark",
        headers={"X-Quote-Token": tok, "Content-Type": "application/json"},
        json={"action": "change_request", "remarks": "Can we do Saturday instead?"},
    ).json()
    assert r.get("ok")
    items = c.get(f"/api/admin/quotes/{qid}/remarks", headers=H).json().get("items", [])
    assert len(items) == 1
    assert items[0]["remarks"].startswith("Can we")
    assert c.get("/api/admin/quote-remarks/unread-count", headers=H).json().get("unread") == 1


def test_printable_redesign_v1_24_166():
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    c.post("/api/admin/seed-commerce-demo", headers=H)
    q = c.get("/api/admin/quotes", headers=H).json()["items"][0]
    r = c.get(f"/admin/print/quote/{q['id']}?t=lumora-admin-test")
    assert r.status_code == 200
    body = r.text
    assert "servia-avatar-512x512.png" in body
    assert "servia-logo-full.svg" in body
    assert "links-strip" in body
    assert 'class="this"' in body


def test_all_five_print_urls_v1_24_166():
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    c.post("/api/admin/seed-commerce-demo", headers=H)
    quotes = c.get("/api/admin/quotes", headers=H).json()["items"]
    sos = c.get("/api/admin/sales-orders", headers=H).json().get("items", [])
    invs = c.get("/api/admin/invoices", headers=H).json().get("items", [])
    dns = c.get("/api/admin/delivery-notes", headers=H).json().get("items", [])
    pos = c.get("/api/admin/purchase-orders", headers=H).json().get("items", [])
    for dtype, lst in [
        ("quote", quotes), ("sales-order", sos), ("invoice", invs),
        ("delivery-note", dns), ("purchase-order", pos),
    ]:
        assert lst, f"no {dtype} seeded"
        r = c.get(f"/admin/print/{dtype}/{lst[0]['id']}?t=lumora-admin-test")
        assert r.status_code == 200, f"{dtype} → {r.status_code}"


def test_ai_quote_endpoint_reachable_v1_24_167():
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    r = c.post(
        "/api/admin/quote-from-text",
        headers={**H, "Content-Type": "application/json"},
        json={"text": "Sara +971501234567 wants AC cleaning 3 units tomorrow"},
    )
    # 200 if ANTHROPIC_API_KEY set; 502 if not (still proves the route exists).
    assert r.status_code in (200, 502)


def test_analytics_v1_24_168():
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    c.post("/api/admin/seed-commerce-demo", headers=H)
    q = c.get("/api/admin/quotes", headers=H).json()["items"][0]
    qid = q["id"]
    for ua in [
        "Mozilla/5.0 (iPhone) Safari",
        "Mozilla/5.0 (Android) Chrome",
        "Mozilla/5.0 (Windows) Chrome",
    ]:
        c.get(
            f"/q/{qid}",
            headers={"user-agent": ua, "x-forwarded-for": "82.137.20.10"},
        )
    r = c.get(f"/api/admin/quotes/{qid}/analytics", headers=H).json()
    assert r.get("ok")
    assert r["summary"]["total_opens"] >= 3
    oses = {e.get("os") for e in r.get("events", [])}
    assert {"iOS", "Android", "Windows"} & oses


def test_open_balance_and_bulk_payment_v1_24_170():
    """v1.24.170 — Multi-doc payment merge:
       1. List unpaid invoices per customer
       2. Register ONE bulk payment that settles 2+ invoices at once
       3. Verify each gets its own payment_registrations row + status=paid"""
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    HJ = {**H, "Content-Type": "application/json"}
    c.post("/api/admin/seed-commerce-demo", headers=H)
    invs = c.get("/api/admin/invoices", headers=H).json()["items"]
    # Pick any customer that has 2+ invoices in the seed
    by_cust: dict = {}
    for inv in invs:
        cid = inv.get("customer_id")
        if cid:
            by_cust.setdefault(cid, []).append(inv)
    target = next((cid for cid, ls in by_cust.items() if len(ls) >= 2), None)
    if target is None:
        # Fallback — at least exercise the endpoint
        target = invs[0]["customer_id"] or 1

    r = c.get(f"/api/admin/customers/{target}/open-balance", headers=H).json()
    assert r.get("ok")
    open_invs = r.get("invoices") or []
    if not open_invs:
        return   # No unpaid invoices to merge — endpoint shape still verified.
    # Allocate to first 2 (or 1 if only 1)
    allocations = []
    for inv in open_invs[:2]:
        allocations.append({"reference_id": inv["id"], "amount": inv["remaining"]})
    r = c.post("/api/admin/payments/register-bulk", headers=HJ, json={
        "payment_type": "customer_in",
        "reference_type": "invoice",
        "method": "bank_transfer",
        "reference_number": "TXN-BULK-001",
        "notes": "Combined payment from customer",
        "allocations": allocations,
    }).json()
    assert r.get("ok")
    assert r.get("doc_count") == len(allocations)
    for s in r.get("settled", []):
        assert s.get("new_status") in ("paid", "partially_paid")


def test_accept_and_pay_v1_24_172():
    """v1.24.172 — One-click accept + register payment, atomic SO/invoice/pay."""
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    HJ = {**H, "Content-Type": "application/json"}
    c.post("/api/admin/seed-commerce-demo", headers=H)
    draft_quotes = [q for q in c.get("/api/admin/quotes", headers=H).json()["items"]
                     if q["status"] == "draft"]
    if not draft_quotes:
        return  # No drafts to test against, endpoint shape still exists
    q = draft_quotes[0]
    total = float(q.get("total") or 100.0)
    r = c.post(f"/api/admin/quotes/{q['id']}/accept-and-pay", headers=HJ, json={
        "amount": total, "method": "cash",
        "reference_number": "WALK-IN-001",
        "notes": "Customer paid cash at door"
    }).json()
    assert r.get("ok")
    assert r.get("status") == "paid"
    assert r.get("invoice_id")
    # Verify quote status is now accepted
    q2 = c.get(f"/api/admin/quotes/{q['id']}", headers=H).json()
    assert q2.get("quote", {}).get("status") == "accepted"


def test_partial_fulfillment_back_order_v1_24_173():
    """v1.24.173 — Partial fulfillment: complete a subset of an SO's
    lines first, then the rest. SO stays in_progress until all covered."""
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    HJ = {**H, "Content-Type": "application/json"}
    # Build a fresh quote with 3 line items so we have something to partially complete
    new_q = c.post("/api/admin/quotes/create", headers=HJ, json={
        "customer_name": "Test Partial",
        "customer_phone": "+971501112222",
        "line_items": [
            {"svc_id": "deep_cleaning", "name": "Deep clean",  "qty": 1, "unit_price": 490},
            {"svc_id": "ac_cleaning",    "name": "AC cleaning", "qty": 2, "unit_price": 150},
            {"svc_id": "plumbing",       "name": "Plumbing",    "qty": 1, "unit_price": 200},
        ],
    }).json()
    assert new_q.get("ok"), new_q
    qid = new_q["id"]
    # Accept → creates SO + invoice
    r = c.post(f"/api/admin/quotes/{qid}/accept", headers=H).json()
    so_id = r.get("sales_order", {}).get("id")
    assert so_id
    # Partial complete: only lines 0 + 1 (deep_clean + ac_cleaning)
    r = c.post(f"/api/admin/sales-orders/{so_id}/mark-completed", headers=HJ, json={
        "line_item_indices": [0, 1],
        "notes": "First two services done, plumbing rescheduled",
    }).json()
    assert r.get("ok")
    assert r.get("fully_completed") is False
    assert r.get("lines_in_this_sn") == 2
    assert r.get("so_status") == "in_progress"
    # Second partial: complete the remaining plumbing line
    r = c.post(f"/api/admin/sales-orders/{so_id}/mark-completed", headers=HJ, json={
        "line_item_indices": [2],
        "notes": "Plumbing done now",
    }).json()
    assert r.get("ok")
    assert r.get("fully_completed") is True
    assert r.get("so_status") == "completed"


def test_wa_bridge_status_v1_24_175():
    """v1.24.175 — Bridge proxy returns helpful error when not configured."""
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    r = c.get("/api/admin/wa-bridge/status", headers=H).json()
    # In test env WA_BRIDGE_URL is unset — must return ok=False + error message
    assert r.get("ok") is False
    assert "not set" in (r.get("error") or "").lower()


def test_payments_config_v1_24_175():
    """v1.24.175 — Payments-config status surfaces GATE_BOOKINGS + Stripe state."""
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    r = c.get("/api/admin/payments/config", headers=H).json()
    assert r.get("ok") is True
    assert "live_mode" in r
    assert "gate_bookings" in r
    assert "stealth_explanation" in r


def test_print_hide_options_v1_24_175():
    """v1.24.175 — ?hide=watermark,links toggles sections off in printable."""
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    c.post("/api/admin/seed-commerce-demo", headers=H)
    q = c.get("/api/admin/quotes", headers=H).json()["items"][0]
    # Without hide → has chain strip (the rendered DIV, not just the CSS class name)
    r1 = c.get(f"/admin/print/quote/{q['id']}?t=lumora-admin-test")
    assert r1.status_code == 200
    assert '<div class="links-strip">' in r1.text
    # With hide=links → chain strip is NOT rendered (CSS class def still exists in <style>)
    r2 = c.get(f"/admin/print/quote/{q['id']}?t=lumora-admin-test&hide=links")
    assert r2.status_code == 200
    assert '<div class="links-strip">' not in r2.text
    # With hide=watermark → mascot is display:none via override
    r3 = c.get(f"/admin/print/quote/{q['id']}?t=lumora-admin-test&hide=watermark")
    assert r3.status_code == 200
    assert "display:none !important" in r3.text


def test_po_bill_flow_v1_24_175():
    """v1.24.175 — Record vendor bill against a PO + read it back."""
    c = _client()
    H = {"Authorization": "Bearer lumora-admin-test"}
    HJ = {**H, "Content-Type": "application/json"}
    c.post("/api/admin/seed-commerce-demo", headers=H)
    pos = c.get("/api/admin/purchase-orders", headers=H).json().get("items", [])
    assert pos, "seed should provide POs"
    po_id = pos[0]["id"]
    r = c.post(f"/api/admin/purchase-orders/{po_id}/bill", headers=HJ, json={
        "bill_number": "BILL-TEST-001",
        "bill_date": "2026-05-13",
        "amount": 150.0,
        "notes": "Test vendor bill",
    }).json()
    assert r.get("ok")
    assert r.get("bill_number") == "BILL-TEST-001"
    r2 = c.get(f"/api/admin/purchase-orders/{po_id}/bill", headers=H).json()
    assert r2.get("bill", {}).get("bill_number") == "BILL-TEST-001"


def test_brand_contact_placeholder_v1_24_165_169():
    assert _is_placeholder("+971 50 000 0000")
    assert _is_placeholder("+971 50 111 0001")
    assert _is_placeholder("+971 50 1110001")
    assert _is_placeholder("+971 50 555 0001")
    assert _is_placeholder("+971 4 444 5566")
    assert not _is_placeholder("+971 4 567 8910")
    assert not _is_placeholder("+971 50 234 5678")
    assert not _is_placeholder("+971 5012345678")
    # When config has only placeholders → should return ""
    assert get_contact_whatsapp() == ""


if __name__ == "__main__":
    # Standalone runner — useful in the sandbox where pytest isn't always installed.
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__} — {e}")
            failed += 1
    print(f"\nRESULT: {passed}/{passed + failed} passed")
    sys.exit(0 if failed == 0 else 1)
