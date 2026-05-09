"""v1.24.83 — Phase 1 customer auth + profile + auto-create tests.

Drives /api/me/auth/* + /api/me/profile + /api/me/locations + /api/me/family
+ /api/me/tickets through TestClient. Asserts the round-trip works.
"""
import os, sys, hashlib
os.environ["DATABASE_URL"] = "sqlite:////tmp/test_customer_profile.db"
if os.path.exists("/tmp/test_customer_profile.db"): os.unlink("/tmp/test_customer_profile.db")
sys.path.insert(0, ".")
os.environ["MAGIC_LINK_SALT"] = "test-salt"

from fastapi.testclient import TestClient
from app import main
from app.tools import create_multi_quote
from app.customer_profile import _auth_token

c = TestClient(main.app)

passed = 0; failed = []
def t(name, ok, detail=""):
    global passed
    if ok: passed += 1
    else: failed.append((name, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))

print("="*70); print(" PHASE 1 — customer auth + profile + auto-create"); print("="*70)

PHONE = "0501234567"

# 1. Auto-create customer when create_multi_quote runs
q = create_multi_quote(
    services=[{"service_id":"deep_cleaning","bedrooms":2},
              {"service_id":"pest_control"}],
    customer_name="Test User", phone=PHONE,
    address="A", target_date="2026-05-25", time_slot="10:00",
    session_id="cp-1")
t("1. multi_quote auto-creates customer", q.get("ok") is True)

# Verify customer exists in DB
from app import db as _db
with _db.connect() as conn:
    row = conn.execute("SELECT id, phone, name FROM customers WHERE phone=?",
                       ("".join(d for d in PHONE if d.isdigit()),)).fetchone()
t("2. customers row exists", row is not None,
  f"row={dict(row) if row else 'NONE'}")
t("3. customer name auto-filled", row and row["name"] == "Test User")

# 2. Unauthenticated GET /api/me/profile → 401-ish
r = c.get("/api/me/profile")
t("4. /api/me/profile without cookie → not authenticated",
  r.json().get("ok") is False)

# 3. Start auth flow
r = c.post("/api/me/auth/start", json={"phone": PHONE})
j = r.json()
t("5. /api/me/auth/start returns ok=True", j.get("ok") is True)

# 4. Verify with valid token
import datetime as _dt
bucket = int(_dt.datetime.utcnow().timestamp() // 1800)
token = _auth_token("".join(d for d in PHONE if d.isdigit()), bucket)
r = c.post("/api/me/auth/verify", json={"phone": PHONE, "token": token})
t("6. /api/me/auth/verify with valid token → ok",
  r.json().get("ok") is True, str(r.json()))
t("7. session cookie set", "servia_auth" in r.cookies)

# 5. Verify with bad token → reject
r2 = c.post("/api/me/auth/verify", json={"phone": PHONE, "token": "bogus"})
t("8. invalid token → rejected", r2.json().get("ok") is False)

# 6. Authed GET /api/me/profile
r = c.get("/api/me/profile")
j = r.json()
t("9. profile fetch ok", j.get("ok") is True, str(j))
t("10. profile.phone matches", j.get("phone","").endswith("0501234567"))
t("11. profile has empty family + locations",
  isinstance(j.get("family"), list) and isinstance(j.get("locations"), list))

# 7. Update profile
r = c.put("/api/me/profile", json={"name": "Khaqan", "email": "k@example.com",
                                    "language": "en", "bio": "Servia regular"})
t("12. profile update ok", r.json().get("ok") is True)
r = c.get("/api/me/profile")
j = r.json()
t("13. profile name updated", j.get("name") == "Khaqan")
t("14. profile email updated", j.get("email") == "k@example.com")

# 8. Add location
r = c.post("/api/me/locations", json={
    "label": "Home",
    "address": "JVC Building 3838, Unit 309, Dubai",
    "building": "Building 3838", "unit": "309", "area": "JVC", "city": "Dubai",
    "lat": 25.05, "lng": 55.18,
})
t("15. add location ok", r.json().get("ok") is True)
r = c.get("/api/me/profile")
locs = r.json().get("locations", [])
t("16. location appears in profile", len(locs) == 1 and locs[0].get("label") == "Home")
loc_id = locs[0].get("id")
t("17. location has id", bool(loc_id))

# 9. Add second location + family member
r = c.post("/api/me/locations", json={"label": "Office",
    "address": "Marina, Dubai", "city": "Dubai"})
t("18. add second location ok", r.json().get("ok") is True)
r = c.post("/api/me/family", json={"name": "Sara", "role": "spouse",
                                    "phone": "0509999999"})
t("19. add family ok", r.json().get("ok") is True)
r = c.get("/api/me/profile")
j = r.json()
t("20. profile has 2 locations + 1 family",
  len(j.get("locations",[])) == 2 and len(j.get("family",[])) == 1)

# 10. Delete a location
r = c.delete(f"/api/me/locations/{loc_id}")
t("21. delete location ok", r.json().get("ok") is True)
r = c.get("/api/me/profile")
t("22. one location left after delete",
  len(r.json().get("locations",[])) == 1)

# 11. Set password
r = c.post("/api/me/password", json={"new_password": "supersecure123"})
t("23. password set ok", r.json().get("ok") is True)
# Wrong password rejection
r = c.post("/api/me/password", json={"old_password": "wrongpw",
                                      "new_password": "newpw123"})
t("24. password change w/ wrong old → rejected",
  r.json().get("ok") is False)

# 12. List my quotes
r = c.get("/api/me/quotes")
j = r.json()
t("25. /api/me/quotes returns ok", j.get("ok") is True)
t("26. /api/me/quotes returns the auto-created quote",
  any(q.get("quote_id","").startswith("Q-") for q in j.get("quotes", [])))

# 13. Open ticket
r = c.post("/api/me/tickets", json={"subject": "Crew was late",
                                     "body": "Team arrived 30 min late on Q-XYZ"})
t("27. open ticket ok", r.json().get("ok") is True)
r = c.get("/api/me/tickets")
j = r.json()
t("28. /api/me/tickets lists my ticket",
  j.get("ok") is True and len(j.get("tickets",[])) >= 1)
t("29. ticket subject preserved",
  j["tickets"][0].get("subject") == "Crew was late")

# 14. Logout
r = c.post("/api/me/logout")
t("30. logout ok", r.json().get("ok") is True)
# Profile fetch after logout → unauthenticated
r = c.get("/api/me/profile")
t("31. profile unauthenticated after logout",
  r.json().get("ok") is False)

# Summary
total = passed + len(failed)
print()
print("="*70)
print(f" PROFILE & AUTH RESULT: {passed}/{total}")
print("="*70)
if failed:
    for n, d in failed: print(f"  FAIL: {n}  {d}")
sys.exit(0 if not failed else 1)
