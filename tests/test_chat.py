"""Smoke tests covering chat, tools, portal, admin, e-sign."""
import os, sys, tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Use an isolated DB for tests
os.environ["DB_PATH"] = os.path.join(tempfile.gettempdir(), "lumora-test.db")
os.environ["DEMO_MODE"] = "on"
os.environ["ADMIN_TOKEN"] = "test-admin-token"

# Wipe the DB before importing the app
if os.path.exists(os.environ["DB_PATH"]):
    os.remove(os.environ["DB_PATH"])

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app import tools  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["mode"] == "demo"
    assert r.json()["service"] == "Servia"


def test_brand_endpoint():
    r = client.get("/api/brand")
    assert r.status_code == 200
    assert r.json()["name"] == "Servia"


def test_i18n_loads():
    r = client.get("/api/i18n")
    assert r.status_code == 200
    j = r.json()
    assert "en" in j and "ar" in j and "hi" in j and "tl" in j
    assert j["ar"]["dir"] == "rtl"


def test_services_endpoint():
    r = client.get("/api/services")
    assert r.status_code == 200
    j = r.json()
    assert len(j["services"]) >= 15  # expanded catalog
    assert any(s["id"] == "ac_cleaning" for s in j["services"])


def test_chat_quote():
    r = client.post("/api/chat", json={"message": "How much for deep cleaning a 3-bedroom?"})
    assert r.status_code == 200
    body = r.json()
    assert any(t["name"] == "get_quote" for t in body["tool_calls"])


def test_book_and_track():
    b = tools.create_booking(
        service_id="general_cleaning", target_date="2099-01-01", time_slot="10:00",
        customer_name="Test User", phone="+971500000000", address="Demo St", bedrooms=2)
    assert b["ok"]
    bid = b["booking"]["id"]

    # Portal lookup by id
    r = client.get(f"/api/portal/booking/{bid}")
    assert r.status_code == 200
    assert r.json()["booking"]["id"] == bid

    # Portal lookup by phone
    r = client.get("/api/portal/bookings", params={"phone": "+971500000000"})
    assert r.status_code == 200
    assert any(x["id"] == bid for x in r.json()["bookings"])


def test_quote_sign_and_invoice():
    b = tools.create_booking(
        service_id="ac_cleaning", target_date="2099-02-01", time_slot="12:00",
        customer_name="Sign Tester", phone="+971511111111", address="X", units=3)
    bid = b["booking"]["id"]
    full = client.get(f"/api/portal/booking/{bid}").json()
    qid = full["booking"]["quotes"][0]["id"]

    # Sign
    r = client.post("/api/portal/quote/sign",
                    json={"quote_id": qid, "signature_data_url": "data:image/png;base64,iVBOR=="})
    assert r.status_code == 200
    out = r.json()
    assert out["ok"] is True
    assert out.get("invoice"), "signing should mint an invoice"

    # Mark invoice paid via stub
    inv_id = out["invoice"]["id"]
    r = client.post("/api/portal/pay-stub", json={"invoice_id": inv_id})
    assert r.json()["ok"] is True


def test_admin_requires_token():
    assert client.get("/api/admin/stats").status_code == 401
    h = {"Authorization": "Bearer test-admin-token"}
    r = client.get("/api/admin/stats", headers=h)
    assert r.status_code == 200
    assert "bookings_total" in r.json()


def test_admin_pricing_override():
    h = {"Authorization": "Bearer test-admin-token"}
    r = client.post("/api/admin/pricing", headers=h,
                    json={"rules": {"general_cleaning": {"base_per_bedroom": 999}}})
    assert r.status_code == 200
    # Verify the override took effect
    q = tools.get_quote("general_cleaning", bedrooms=2)
    assert q["total"] >= 999 * 2 * 0.95  # ≈ same number


def test_admin_takeover_and_release():
    h = {"Authorization": "Bearer test-admin-token"}
    sid = "test-sw-123"
    # Send a message first to create the conversation row
    client.post("/api/chat", json={"message": "hello", "session_id": sid})
    # Take over
    r = client.post("/api/admin/takeover", headers=h, json={"session_id": sid})
    assert r.status_code == 200
    # Subsequent chat is deferred
    r2 = client.post("/api/chat", json={"message": "are you human?", "session_id": sid})
    assert r2.json()["agent_handled"] is True
    # Agent reply
    r3 = client.post("/api/admin/reply", headers=h,
                     json={"session_id": sid, "text": "Yes, hi! I'm Sarah."})
    assert r3.status_code == 200
    # Release
    r4 = client.post("/api/admin/release", headers=h, json={"session_id": sid})
    assert r4.status_code == 200


def test_static_pages_served():
    for p in ("/", "/services.html", "/book.html", "/account.html",
              "/quote.html", "/admin.html", "/manifest.webmanifest", "/sw.js",
              "/logo.svg", "/avatar.svg"):
        r = client.get(p)
        assert r.status_code == 200, f"{p} → {r.status_code}"
