"""v1.24.84 — pin-location reverse geocode + city cross-check.

Tests use the in-memory Nominatim cache (no real network call).
"""
import os, sys
os.environ["DB_PATH"] = "/tmp/test_address.db"
if os.path.exists("/tmp/test_address.db"): os.unlink("/tmp/test_address.db")
sys.path.insert(0, ".")

from app.address_picker import (_which_emirate, _GEO_CACHE, reverse_geocode,
                                 EMIRATE_BOXES)
from fastapi.testclient import TestClient
from app import main
import time

c = TestClient(main.app)
passed = 0; failed = []
def t(name, ok, detail=""):
    global passed
    if ok: passed += 1
    else: failed.append((name, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))

print("="*70); print(" v1.24.84 — pin-location address picker"); print("="*70)

# 1. Bounding-box check — Dubai Marina coords
t("1. Dubai Marina coords resolve to dubai",
  _which_emirate(25.078, 55.140) == "dubai")
t("2. Abu Dhabi corniche resolves to abu_dhabi",
  _which_emirate(24.471, 54.370) == "abu_dhabi")
t("3. Sharjah Buhairah resolves to sharjah",
  _which_emirate(25.328, 55.382) == "sharjah")
t("4. Pure ocean (negative test) returns None",
  _which_emirate(0, 0) is None)
t("5. London (negative test) returns None",
  _which_emirate(51.5, -0.12) is None)

# 6. /api/geocode/check-city — pin in dubai, claimed dubai → matches
r = c.post("/api/geocode/check-city",
           json={"lat": 25.078, "lng": 55.140, "claimed_city": "Dubai"})
j = r.json()
t("6. check-city: pin Dubai + claim Dubai → matches",
  j.get("ok") is True and j.get("matches") is True)

# 7. pin Sharjah but claim Dubai → mismatch + suggestion
r = c.post("/api/geocode/check-city",
           json={"lat": 25.328, "lng": 55.382, "claimed_city": "Dubai"})
j = r.json()
t("7. check-city: pin Sharjah + claim Dubai → mismatch",
  j.get("ok") is True and j.get("matches") is False)
t("8. mismatch returns suggestion + correct emirate",
  j.get("actual_emirate") == "sharjah" and "Sharjah" in (j.get("suggestion") or ""))

# 9. case-insensitive city
r = c.post("/api/geocode/check-city",
           json={"lat": 25.078, "lng": 55.140, "claimed_city": "dubai"})
t("9. check-city: lowercase 'dubai' matches",
  r.json().get("matches") is True)

# 10. underscore form
r = c.post("/api/geocode/check-city",
           json={"lat": 25.55, "lng": 55.55, "claimed_city": "Umm Al Quwain"})
t("10. check-city: 'Umm Al Quwain' string handled",
  r.json().get("matches") is True)

# 11. /api/geocode/reverse — out of range coord
r = c.post("/api/geocode/reverse", json={"lat": 999, "lng": 999})
t("11. reverse: invalid lat/lng → ok=false",
  r.json().get("ok") is False)

# 12. cache mechanic — populate cache directly
_GEO_CACHE["25.0780,55.1400"] = (time.time(), {
    "ok": True, "lat": 25.078, "lng": 55.140,
    "city": "Dubai", "area": "Dubai Marina",
    "road": "Marina Walk", "country": "United Arab Emirates",
    "emirate": "dubai",
})
result = reverse_geocode(25.078, 55.140)
t("12. cached reverse-geocode returns city",
  result.get("city") == "Dubai")
t("13. cached reverse-geocode returns area",
  result.get("area") == "Dubai Marina")
t("14. cached reverse-geocode includes emirate",
  result.get("emirate") == "dubai")

# 15. /api/geocode/reverse with cached data → returns same
r = c.post("/api/geocode/reverse", json={"lat": 25.078, "lng": 55.140})
j = r.json()
t("15. /api/geocode/reverse uses cache",
  j.get("city") == "Dubai" and j.get("emirate") == "dubai")

# 16. JS widget file exists with leaflet integration
import os.path
js_exists = os.path.isfile("web/address-picker.js")
t("16. /address-picker.js exists in /web",
  js_exists)
if js_exists:
    js = open("web/address-picker.js").read()
    t("17. widget loads Leaflet + English-label tiles",
      "leaflet" in js.lower() and ("openstreetmap.org" in js or "cartocdn.com" in js))
    t("18. widget posts to /api/geocode/reverse",
      "/api/geocode/reverse" in js)
    t("19. widget v1.24.91 — auto-fills area+city from reverse-geocode (cross-check removed per UX feedback)",
      "areaIn.value = j.area" in js and "cityIn.value = j.city" in js)
    t("20. widget exposes window.serviaAddressPicker.mount",
      "window.serviaAddressPicker" in js and "mount" in js)

# Summary
total = passed + len(failed)
print()
print("="*70)
print(f" ADDRESS PICKER RESULT: {passed}/{total}")
print("="*70)
if failed:
    for n, d in failed: print(f"  FAIL: {n}  {d}")
sys.exit(0 if not failed else 1)
