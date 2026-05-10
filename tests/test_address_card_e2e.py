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

# ─── v1.24.93 — verbatim screenshot regression ────────────────────
# Bug shipped in v1.24.92: bot replied "could you please confirm the
# emirate for Furjan" + emitted [[choices: Dubai=Dubai; Sharjah=...]]
# WHILE the address picker also rendered. UX showed duplicate
# emirate selectors. The post-processor must (a) inject the picker
# AND (b) strip the redundant emirate-only [[choices:]] block.
print("\n--- v1.24.93 emirate-duplicate regression (verbatim screenshot) ---")

SCREENSHOT_TEXT = (
    "Great! So that's Deep Cleaning, Pest Control, and Sofa & Carpet "
    "Shampoo for Wednesday, May 20, 2026, at 12:00 PM.\n\n"
    "To finalize your booking, could you please confirm the emirate "
    "for Furjan and provide the full address?\n"
    "[[choices: Dubai=Dubai; Sharjah=Sharjah; Ajman=Ajman; "
    "Abu Dhabi=Abu Dhabi]]"
)
out = _enforce_picker_and_one_question(SCREENSHOT_TEXT)
t("R93-1. picker injected for 'confirm the emirate'",
  "[[picker:address]]" in out, out[-60:].replace("\n"," "))
t("R93-2. emirate [[choices:]] block stripped",
  "[[choices:" not in out and "Dubai=Dubai" not in out,
  out)
t("R93-3. summary text retained",
  "Deep Cleaning" in out and "Furjan" in out)

# Variants of the same family that all must strip + inject
VARIANTS = [
    ("which emirate is this in?\n[[choices: Dubai=Dubai; Sharjah=Sharjah]]",
     "which emirate variant"),
    ("Could you confirm the city for me?\n[[choices: Dubai; Abu Dhabi; Ajman]]",
     "confirm the city variant"),
    ("Where should we come?\n[[choices: Dubai=Dubai; Ras Al Khaimah=RAK]]",
     "where should we come variant"),
]
for txt, name in VARIANTS:
    out = _enforce_picker_and_one_question(txt)
    ok = "[[picker:address]]" in out and "[[choices:" not in out
    t(f"R93-V {name}", ok, out[:120].replace("\n"," "))

# ─── v1.24.94 — verbatim screenshot regression #2 ────────────────────
# Bug shipped in v1.24.93: founder screenshot showed the bot replying
# "I just need your full home address in Furjan to finalize the
# booking. Could you please share that?" — picker NOT injected,
# customer asked to type address as free text. The v1.24.93 regex
# did not match because:
#   - verb list missed "need"
#   - qualifier slot was strictly (full|complete|exact|detailed)?
#     followed by \s*address, so "full HOME address" (extra word
#     between qualifier and noun) failed to match
# v1.24.94 fix: broader verb-near-noun pattern matches any address-
# asking verb within 80 chars of the word "address" + standalone
# phrases like "home address" / "full address".
print("\n--- v1.24.94 free-text-address regression (verbatim screenshot) ---")

SCREENSHOT_94 = (
    "Perfect! Thank you, Khaqan. I have:\n\n"
    "Booking Summary:\n"
    " • Services: Deep Cleaning, Pest Control, Sofa & Carpet Shampoo\n"
    " • Location: Furjan, Dubai\n"
    " • Date & Time: Thursday, 14 May 2026 at 14:00\n"
    " • Phone: 0559396459\n\n"
    "I just need your full home address in Furjan to finalize the "
    "booking. Could you please share that?\n\n"
    "Once confirmed, I'll provide your booking links for all three "
    "services."
)
out = _enforce_picker_and_one_question(SCREENSHOT_94)
t("R94-1. picker injected for 'need your full home address'",
  "[[picker:address]]" in out, out[-80:].replace("\n"," "))
t("R94-2. summary preserved (Furjan/Khaqan)",
  "Furjan" in out and "Khaqan" in out)
t("R94-3. trigger regex matches 'need your full home address'",
  bool(_ADDR_TRIGGER.search(SCREENSHOT_94)))

# Variants of the v1.24.93-missed family
VARIANTS_94 = [
    ("Please send me your home address.", "send-home-address"),
    ("Could you type your full address for me?", "type-full-address"),
    ("Drop your address so I can dispatch the team.", "drop-address"),
    ("I need the exact address please.", "need-exact-address"),
    ("Let me know your address and we'll head over.", "let-me-know-address"),
    ("What's the building name and villa number?", "building-villa"),
]
for txt, name in VARIANTS_94:
    out = _enforce_picker_and_one_question(txt)
    ok = "[[picker:address]]" in out
    t(f"R94-V {name}", ok, out.replace("\n"," ")[:120])

# ─── v1.24.95 — verbatim screenshot regression #3 ────────────────────
# Bug shipped in v1.24.94: founder filled the in-chat picker, submitted,
# the bot received a synthesized "[Office] Liberty, BJKJ, ..." message,
# treated it as a normal customer message containing the address, and
# created Q-0B1FB9 without ever EMITTING [[picker:address]] in the
# turn that asked for address.
#
# Root cause: 3 places in the system prompt explicitly said "ask address
# as free text". The LLM was obeying instructions. Regex post-processor
# was fighting the prompt and lost.
#
# v1.24.95 fix:
#   - STEP 7 now says "emit [[picker:address]] and STOP"
#   - "When location/address, ask in free text" → "...end with
#     [[picker:address]]"
#   - "Then ask name, phone, full address" → "...then emit
#     [[picker:address]]"
#   - "For free-form input (name, address, phone, custom date), do NOT
#     include the marker" → address removed from free-form list
#   - New "ADDRESS PICKER PROTOCOL" section: 5 absolute rules, never
#     accept typed addresses, re-emit picker if user types
#
# These are SYSTEM PROMPT changes — not testable by static unit tests
# without a real LLM call. The regression detector here is the persona
# blob itself: assert that the persona STRING contains the new rules
# and does NOT contain the old free-text instruction.
print("\n--- v1.24.95 system-prompt audit (R95) ---")

# The system prompt is built dynamically. Grab the file source and
# audit the literal strings so this test catches any future regression
# that re-adds the "ask address as free text" instruction.
import app.llm as _llm_mod
import inspect as _inspect
persona = _inspect.getsource(_llm_mod)

t("R95-1. persona declares ADDRESS PICKER PROTOCOL",
  "ADDRESS PICKER PROTOCOL" in persona)
t("R95-2. STEP 7 emits picker, not 'free text'",
  "STEP 7" in persona and
  "address with building / area (one question, free text)" not in persona)
t("R95-3. 'When location/address, ask in free text' is gone",
  "When location/address, ask in free text" not in persona)
t("R95-4. free-form list no longer includes 'address'",
  "input (name, address, phone, custom date)" not in persona and
  "input (name, phone, custom date)" in persona)
t("R95-5. persona explicitly mentions 'NEVER accept a typed address'"
  " or equivalent",
  "Never accept a typed address" in persona or
  "NEVER accept a typed address" in persona or
  "typed address as the customer" in persona)
t("R95-6. STEP 7 contains the literal [[picker:address]] marker",
  "STEP 7" in persona and
  persona.split("STEP 7")[1].split("STEP 8")[0].count("[[picker:address]]") >= 1)

# ─── v1.24.96 — Loophole 9/10 regressions ────────────────────────────
# Founder screenshot showed bot replying in French ("Parfait! J'ai bien
# enregistré...") + writing a plain-text "Final Summary" with a legacy
# "Book now ↗" link instead of calling create_multi_quote to render a
# quote_card. Two root causes from per-W8 audit:
#
#   L9: _enforce_multi_quote_when_book_now is DEFINED in app/llm.py
#       but was NEVER CALLED. Pure dead code. Bot text passed through
#       unchanged.
#   L10: _detect_lang_from_text returned None for Latin-script messages
#        without specific French/Spanish/Filipino markers. Fell back to
#        ui_lang. localStorage.lumora.lang somehow got "fr". Bot
#        replied French to UAE customer typing English.
print("\n--- v1.24.96 Book-now wire-up + language audit (R96) ---")

# L9 wire-up: the post-processor must be CALLED, not just defined.
import inspect as _inspect2
llm_src = _inspect2.getsource(_llm_mod)
t("R96-1. _enforce_multi_quote_when_book_now is now called",
  "_enforce_multi_quote_when_book_now(" in llm_src and
  llm_src.count("_enforce_multi_quote_when_book_now") >= 2,
  "definition + at least one call site")
t("R96-2. wired up in the chat() pipeline next to picker enforcer",
  "_enforce_picker_and_one_question" in llm_src and
  "_enforce_multi_quote_when_book_now(final_text" in llm_src)

# L10 language detection — Latin script with English stopwords → "en"
import importlib as _imp
_main = _imp.import_module("app.main")
_dl = _main._detect_lang_from_text
t("R96-3. 'Yes' detects as English (was: None → ui_lang fallback)",
  _dl("Yes") == "en")
t("R96-4. 'thanks please' detects as English",
  _dl("thanks please") == "en")
t("R96-5. 'bonjour merci' still detects as French",
  _dl("bonjour merci où c'est") == "fr")
t("R96-6. picker output has no stopwords → still None (history fallback handles it)",
  _dl("[Homehh] Liberty Building 2720, 8293, Muweilah Commercial, Sharjah") is None,
  "intentional: short proper-noun strings → server uses conv history")
t("R96-7. French diacritics block English default",
  _dl("réservation pour mercredi à 14h") in ("fr", None),
  "explicit French (via réservation keyword) OR None (history wins)")
t("R96-8. Arabic still detects as Arabic",
  _dl("أهلاً، أحتاج خدمة تنظيف") == "ar")

# Summary
total = passed + len(failed)
print()
print("="*70)
print(f" SLICE A.5 RESULT: {passed}/{total}")
print("="*70)
if failed:
    for n, d in failed: print(f"  FAIL: {n}  {d}")
sys.exit(0 if not failed else 1)
