"""REAL END-TO-END test of /api/chat with a mocked Anthropic SDK that
replays REAL bot replies captured from the user's screenshots.

This proves the WHOLE pipeline:
  POST /api/chat → llm.chat() → [mocked Anthropic] → tool dispatch →
  post-processors (picker injection, multi-quote auto-conversion) →
  response delivered to widget

If a function only "works in unit test" but never fires here, this
test catches it.
"""
import os, sys, json, types, re, uuid
os.environ["DATABASE_URL"] = "sqlite:////tmp/test_e2e_chat.db"
os.environ["ANTHROPIC_API_KEY"] = "fake-key-for-mock"  # so use_llm=True
os.environ["DEMO_MODE"] = "off"
sys.path.insert(0, "/tmp/lumora-deploy")

# ─── Mock Anthropic SDK BEFORE importing app ────────────────────────
import anthropic as _anthropic_mod

class _Block:
    def __init__(self, type, text=None, name=None, id=None, input=None):
        self.type = type
        if text is not None: self.text = text
        if name is not None: self.name = name
        if id is not None: self.id = id
        if input is not None: self.input = input

class _Usage:
    def __init__(self):
        self.input_tokens = 100
        self.output_tokens = 50
        self.cache_creation_input_tokens = 0
        self.cache_read_input_tokens = 0

class _Resp:
    def __init__(self, blocks, stop_reason="end_turn"):
        self.content = blocks
        self.stop_reason = stop_reason
        self.usage = _Usage()

# ─── Recorded REAL bot outputs from user's actual screenshots ────────
SCRIPT = []  # set per test

class _FakeMessages:
    def create(self, **kw):
        # Pop the next scripted reply
        if not SCRIPT:
            return _Resp([_Block("text", text="(no more scripted replies)")])
        item = SCRIPT.pop(0)
        if isinstance(item, str):
            return _Resp([_Block("text", text=item)])
        elif isinstance(item, dict) and item.get("kind") == "tool":
            blocks = []
            if item.get("text"): blocks.append(_Block("text", text=item["text"]))
            blocks.append(_Block("tool_use",
                                 name=item["tool_name"],
                                 id=f"tu_{uuid.uuid4().hex[:8]}",
                                 input=item.get("tool_input", {})))
            return _Resp(blocks, stop_reason="tool_use")
        return _Resp([_Block("text", text=str(item))])

class _FakeAnthropic:
    def __init__(self, *a, **kw):
        self.messages = _FakeMessages()

_anthropic_mod.Anthropic = _FakeAnthropic

# Force anthropic-primary path: monkey-patch ai_router._load_cfg so
# the chat endpoint doesn't pick admin-router cascade.
import app.ai_router as _ar
_ar._load_cfg = lambda: {"defaults": {"customer": ""}, "keys": {}}

# Now import the app
from app import main as _m
from fastapi.testclient import TestClient
client = TestClient(_m.app)

passed = 0; failed = []
def t(name, ok, detail=""):
    global passed
    if ok: passed += 1
    else: failed.append((name, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))

print("="*78)
print("E2E TEST: /api/chat → mocked LLM → post-processors → DB")
print("="*78)

# ─── SCENARIO A: bot asks date+time as multi-question → server collapses
#                 to single question + datetime picker ────────────────
print("\n--- A) Picker post-processor fires through /api/chat ---")
SCRIPT = [
    "A few quick details to finalize your booking:\n"
    "1. Which emirate is your Furjan property in?\n"
    "2. What date and time work best for you?\n"
    "3. Full address in Furjan?\n"
    "4. Just confirming your phone number?"
]
sid = "e2e-picker-" + uuid.uuid4().hex[:6]
r = client.post("/api/chat", json={
    "session_id": sid, "message": "I need cleaning + pest", "phone": "0559396459"
})
j = r.json()
t("A1 /api/chat status 200", r.status_code == 200, str(r.status_code))
t("A2 reply has [[picker:datetime]]", "[[picker:datetime]]" in j.get("text",""), j.get("text","")[:80])
t("A3 reply has ≤1 question mark (one question per turn)",
  j.get("text","").count("?") <= 1, f"qcount={j.get('text','').count('?')}")
t("A4 multi-question text REPLACED with concise question",
  "When would you like" in j.get("text",""))

# ─── SCENARIO B: bot writes "Book now ↗" with 3 services →
#                 server auto-creates Q-XXXXXX + replaces reply ──────
print("\n--- B) Multi-quote auto-creation fires through /api/chat ---")
SCRIPT = ["""Got it!

✓ Services: Deep Cleaning, Pest Control, Sofa & Carpet Shampoo
✓ Date & Time: Monday, 18 May 2026 at 12:00 PM
✓ Address: JVC 3838
✓ Name: Khaqan
✓ Phone: 0559396459

Total: AED 819 (VAT inclusive)

[Book now ↗]"""]
sid = "e2e-quote-" + uuid.uuid4().hex[:6]
r = client.post("/api/chat", json={
    "session_id": sid, "message": "yes confirm", "phone": "0559396459"
})
j = r.json()
text = j.get("text","")
qid_m = re.search(r"Q-[A-Z0-9]{6}", text)
t("B1 /api/chat → reply has Q-XXXXXX", bool(qid_m), qid_m.group(0) if qid_m else "no Q-")
t("B2 reply NO LONGER contains 'Book now ↗'", "Book now" not in text)
qid_str = qid_m.group(0) if qid_m else None
# v1.24.78 — reply now uses [[quote_card: Q-XXX]] marker. Widget
# renders rich card with all actions IN-CHAT, no inline URLs.
t("B3 reply has [[quote_card: Q-XXX]] marker",
  qid_str and f"[[quote_card: {qid_str}]]" in text)
t("B4 reply does NOT have inline PDF URL (now via card)",
  "[📥 Download PDF](" not in text)
t("B5 reply has Revise [[choices:]]", "✏️ Revise quote" in text)

# ─── SCENARIO C: persistence — Q-XXXXXX is in DB and findable ───────
print("\n--- C) Persistence + lookup round-trip ---")
if qid_str:
    from app import db as _db
    with _db.connect() as c:
        row = c.execute("SELECT phone, total_aed, customer_name FROM multi_quotes WHERE quote_id=?",
                        (qid_str,)).fetchone()
    t("C1 Q-XXXXXX persisted to multi_quotes table",
      row is not None, str(dict(row)) if row else "NONE")
    t("C2 phone correctly indexed (0559396459)",
      row and row["phone"] == "0559396459")
    # Test the lookup endpoint /q/<id> can find it
    rq = client.get(f"/q/{qid_str}")
    t("C3 GET /q/<id> 200 (signing page renders)", rq.status_code == 200)
    rp = client.get(f"/p/{qid_str}")
    t("C4 GET /p/<id> 200 (pay page renders)", rp.status_code == 200)
    rpdf = client.get(f"/i/{qid_str}.pdf")
    t("C5 GET /i/<id>.pdf returns application/pdf",
      rpdf.status_code == 200 and rpdf.headers.get("content-type","").startswith("application/pdf"),
      f"status={rpdf.status_code} ct={rpdf.headers.get('content-type')}")

# ─── SCENARIO D: rejection — bogus quote_id ─────────────────────────
print("\n--- D) Rejection path ---")
r = client.get("/q/Q-DOESNT-EXIST")
t("D1 /q/<bogus> → 404", r.status_code == 404)

# ─── SCENARIO E: tool blocker fires when LLM tries create_booking
#                 with 2+ services in chat ─────────────────────────
print("\n--- E) Tool blocker fires through /api/chat ---")
SCRIPT = [
    {"kind":"tool","tool_name":"create_booking",
     "tool_input":{"service_id":"deep_cleaning","target_date":"2026-05-18",
                   "time_slot":"10:00","customer_name":"X","phone":"1","address":"y"},
     "text":"booking..."},
    "OK I see I need create_multi_quote instead. Done."
]
sid = "e2e-blocker-" + uuid.uuid4().hex[:6]
r = client.post("/api/chat", json={
    "session_id": sid, "message": "deep cleaning + pest control + sofa", "phone": "0559396459"
})
j = r.json()
# We expect the tool to be BLOCKED (server-side guard)
tool_calls = j.get("tool_calls") or []
blocked = any(
    tc.get("name") == "create_booking" and 
    isinstance(tc.get("result"), dict) and
    "BLOCKED" in str(tc.get("result", {}).get("error", ""))
    for tc in tool_calls
)
t("E1 create_booking BLOCKED when 2+ services in chat",
  blocked, f"tool_calls={[tc['name'] for tc in tool_calls]}")

# ─── SCENARIO F: intake guard fires when bedrooms missing ────────────
print("\n--- F) Intake guard fires through /api/chat ---")
SCRIPT = [
    {"kind":"tool","tool_name":"get_quote",
     "tool_input":{"service_id":"deep_cleaning"},
     "text":"computing price..."},
    "OK I need to ask bedrooms first."
]
sid = "e2e-intake-" + uuid.uuid4().hex[:6]
r = client.post("/api/chat", json={
    "session_id": sid, "message": "i want deep cleaning", "phone": "0559396459"
})
j = r.json()
tool_calls = j.get("tool_calls") or []
intake_blocked = any(
    tc.get("name") == "get_quote" and
    isinstance(tc.get("result"), dict) and
    "intake incomplete" in str(tc.get("result", {}).get("error", "")).lower()
    for tc in tool_calls
)
t("F1 get_quote BLOCKED when bedrooms missing",
  intake_blocked, f"tool_calls={[tc['name'] for tc in tool_calls]}")

# ─── Summary ────────────────────────────────────────────────────────
total = passed + len(failed)
print()
print("=" * 78)
print(f"E2E RESULT: {passed}/{total}")
print("=" * 78)
if failed:
    for n, d in failed:
        print(f"  FAIL: {n}  {d}")
sys.exit(0 if not failed else 1)
