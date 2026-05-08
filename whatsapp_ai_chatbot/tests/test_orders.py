from app import orders


def test_extract_full_order_block():
    reply = """Thank you Ahmed — passing this to sales.

<ORDER>
{
  "customer_name": "Ahmed",
  "company": "ABC Trading",
  "phone": "+971501234567",
  "product": "HDPE sheet",
  "grade": "HDPE",
  "dimensions": "2mm x 1m x 2m",
  "quantity": "100 sheets",
  "delivery": "Dubai Industrial Area",
  "notes": "food-grade required"
}
</ORDER>

<ESCALATE>"""
    cleaned, ext = orders.extract_and_strip(reply)
    assert "<ORDER>" not in cleaned
    assert ext is not None
    assert ext.customer_name == "Ahmed"
    assert ext.product == "HDPE sheet"
    assert ext.quantity == "100 sheets"
    assert ext.notes == "food-grade required"


def test_extract_no_order_block():
    cleaned, ext = orders.extract_and_strip("plain reply")
    assert cleaned == "plain reply"
    assert ext is None


def test_extract_malformed_json_returns_none():
    reply = "ok\n<ORDER>{not valid json}</ORDER>"
    cleaned, ext = orders.extract_and_strip(reply)
    assert "<ORDER>" not in cleaned
    assert ext is None


def test_save_and_list_roundtrip():
    o = orders.ExtractedOrder(
        customer_name="Test",
        product="HDPE",
        quantity="1",
    )
    oid = orders.save("971500000000", o, raw_summary="summary")
    assert oid > 0
    rows = orders.list_recent(limit=10)
    assert len(rows) == 1
    assert rows[0]["customer_name"] == "Test"
    assert rows[0]["status"] == "new"


def test_update_status():
    o = orders.ExtractedOrder(customer_name="X", product="Y")
    oid = orders.save("971500000001", o, raw_summary="")
    orders.update_status(oid, "contacted")
    row = orders.get(oid)
    assert row is not None and row["status"] == "contacted"
