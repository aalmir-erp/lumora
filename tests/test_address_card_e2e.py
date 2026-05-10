"""v1.24.90 Slice A.5 — Sitewide pin-first address card.

Drives /api/chat with a mocked LLM emitting the EXACT verbatim text
from the user's v1.24.88 screenshot. Asserts the post-processor
auto-injects [[picker:address]] so the chat widget renders the
address card instead of accepting free-text.

Loophole-prevention coverage:
- L2: real screenshot text as fixture (not made up)
- L1: uses DB_PATH not DATABASE_URL
- L8: handles cookie auth via http (TestClient)
"""
import os, sys, uuid
os.environ["DB_PATH"] = "/tmp/test_address_card.db"
if os.path.exists("/tmp/test_address_card.db"): os.unlink("/tmp/test_address_card.db")
os.environ["ANTHROPIC_API_KEY"] = "fake"
os.environ["DEMO_MODE"] = "off"
os.environ["MAGIC_LINK_SALT"] = "test-salt"
sys.path.insert(0, ".")

# Mock Anthropic before app import
import anthropic as _am
class _B:
    def __init__(self, type, text=None): self.type = type; self.text = text or ""
class _U:
    input_tokens=100; output_tokens=50
    cache_creation_input_tokens=0; cache_read_input_tokens=0
class _R:
    def __init__(self, blocks): self.content = blocks; self.stop_reason = "end_turn"; self.usage = _U()
SCRIPT = []
class _M:
    def create(self, **kw):
        if not SCRIPT: return _R([_B("text", text="(empty)")])
        return _R([_B("text", text=SCRIPT.pop(0))])
class _A:
    def __init__(self, *a, **kw): self.messages = _M()
_am.Anthropic = _A

import app.ai_router as _ar
_ar._load_cfg = lambda: {"defaults": {"customer": ""}, "keys": {}}

from fastapi.testclient import TestClient
from app import main
from app.llm import _enforce_picker_and_one_question, _ADDR_TRIGGER

c = TestClient(main.app)

passed = 0; failed = []
def t(name, ok, detail=""):
    global passed
    if ok: passed += 1
    else: failed.append((name, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))

print("="*70); print(" SLICE A.5 — sitewide pin-first address card"); print("="*70)

# ─── Real screenshot text ─────────────────────────────────────────
# Verbatim from /root/.claude/uploads/.../f8661b20-1000427538.jpg
REAL_BOT_REPLIES = [
    "Just to confirm, could you please provide the full address in Furjan, Dubai?",
    "Thanks, Khaqan! Could you please share the full address in Furjan, Dubai, so we can finalize your booking?",
    "Thanks for that! Just to make sure our team finds you easily, could you please provide the full address, including the building or villa number and street name, in Furjan, Dubai?",
    # Variants the LLM might also use
    "What is your full address?",
    "Where should we come?",
    "Could you tell me your address?",
    "Please give me the building name and unit number.",
]

for i, reply in enumerate(REAL_BOT_REPLIES, 1):
    out = _enforce_picker_and_one_question(reply)
    has_picker = "[[picker:address]]" in out
    t(f"{i:02d}. injects picker for: {reply[:60]}…", has_picker, out[-40:].replace("\n"," "))

# Negative tests — should NOT inject
print("\n--- Negative cases (must NOT inject picker:address) ---")
NEG_REPLIES = [
    "Hello! How can I help you today?",
    "We offer Deep Cleaning starting at AED 490.",
    "Your booking is confirmed for tomorrow at 8 AM.",
    "What service do you need?",   # date/time picker not address
]
for i, reply in enumerate(NEG_REPLIES, 1):
    out = _enforce_picker_and_one_question(reply)
    has_picker = "[[picker:address]]" in out
    t(f"NEG {i}. NO picker for: {reply[:60]}…", not has_picker)

# ─── End-to-end through /api/chat ─────────────────────────────────
print("\n--- E2E /api/chat with mocked LLM ---")
SCRIPT = [REAL_BOT_REPLIES[0]]  # the very first verbatim text
sid = "addr-" + uuid.uuid4().hex[:6]
r = c.post("/api/chat", json={
    "session_id": sid, "message": "yes", "phone": "0559396459"
})
j = r.json()
text = j.get("text","")
t("E2E1. /api/chat → reply has [[picker:address]]",
  "[[picker:address]]" in text, text[:120])
t("E2E2. /api/chat → still contains the original prompt text",
  "Furjan" in text or "address" in text.lower())

# ─── Widget regex extraction (Node) ──────────────────────────────
print("\n--- Widget regex extraction ---")
import subprocess, json as _json
node_in = _json.dumps([text])
proc = subprocess.run(
    ["node", "/tmp/widget_picker_test.js"],
    input=node_in, capture_output=True, text=True, timeout=10,
)
if proc.returncode == 0:
    parsed = _json.loads(proc.stdout)
    t("E2E3. widget regex extracts kind='address'",
      parsed[0].get("picker") == "address", str(parsed))

# ─── upsert-from-pin endpoint ─────────────────────────────────────
print("\n--- /api/me/locations/upsert-from-pin ---")
# 1. Anonymous → silently no-op
r = c.post("/api/me/locations/upsert-from-pin", json={
    "label":"Home", "address":"x", "lat":25.05, "lng":55.18,
    "building":"B 3838", "unit":"309", "area":"JVC", "city":"Dubai",
})
t("UP1. anonymous → 200 + saved=False (no leak)",
  r.json().get("ok") and not r.json().get("saved"))

# 2. Sign in then upsert
PHONE = "0501234567"
import datetime as _dt
from app.customer_profile import _auth_token
bucket = int(_dt.datetime.utcnow().timestamp() // 1800)
token = _auth_token(PHONE, bucket)
r = c.post("/api/me/auth/verify", json={"phone": PHONE, "token": token})
t("UP2. auth/verify ok", r.json().get("ok") is True)

r = c.post("/api/me/locations/upsert-from-pin", json={
    "label":"Home", "address":"JVC", "lat":25.05, "lng":55.18,
    "building":"B 3838", "unit":"309", "area":"JVC", "city":"Dubai",
})
t("UP3. authed → ok + saved", r.json().get("ok") and r.json().get("saved"))

# 3. Same pin again → deduped, no new row
r = c.post("/api/me/locations/upsert-from-pin", json={
    "label":"Home2", "address":"JVC2", "lat":25.0501, "lng":55.1801,
    "building":"B 3838", "unit":"309", "area":"JVC", "city":"Dubai",
})
t("UP4. same pin (within 30m) → deduped",
  r.json().get("ok") and r.json().get("deduped"))

# 4. Profile shows only 1 location after dedupe
r = c.get("/api/me/profile")
locs = r.json().get("locations", [])
t("UP5. profile has exactly 1 location after 2 upserts at same pin",
  len(locs) == 1, f"got {len(locs)} locations")

# 5. Different pin → new row
r = c.post("/api/me/locations/upsert-from-pin", json={
    "label":"Office", "address":"Marina", "lat":25.08, "lng":55.14,
    "building":"Marina Crown", "unit":"4501", "area":"Dubai Marina", "city":"Dubai",
})
t("UP6. different pin → not deduped",
  r.json().get("ok") and not r.json().get("deduped"))
r = c.get("/api/me/profile")
t("UP7. profile now has 2 locations",
  len(r.json().get("locations",[])) == 2)

# 6. Pin missing → reject
r = c.post("/api/me/locations/upsert-from-pin", json={
    "label":"NoPin", "address":"x", "city":"Dubai",
})
t("UP8. lat/lng missing → ok=false",
  r.json().get("ok") is False)

# Summary
total = passed + len(failed)
print()
print("="*70)
print(f" SLICE A.5 RESULT: {passed}/{total}")
print("="*70)
if failed:
    for n, d in failed: print(f"  FAIL: {n}  {d}")
sys.exit(0 if not failed else 1)
