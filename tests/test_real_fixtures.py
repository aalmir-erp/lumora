"""Regression test: every captured user screenshot MUST produce a
Q-XXXXXX (or be unaffected if it's not a quote summary).

This is the LIVE fixture file — every time the user reports a 'no Q-
generated' bug, copy the EXACT bot text from their screenshot here.
"""
import os, re, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/test_real_fixtures.db"
sys.path.insert(0, "/tmp/lumora-deploy")
from app.llm import _enforce_multi_quote_when_book_now as eq, _parse_summary

# ─── Captured real bot outputs (verbatim from screenshots) ────────────
FIXTURES = [
    {
        "name": "v1.24.66 — '4 questions' multi-question (NOT a summary, no Q expected)",
        "text": ("A few quick details to finalize your booking:\n"
                 "1. Which emirate is your Furjan property in?\n"
                 "2. What date and time work best for you?\n"
                 "3. Full address?\n"
                 "4. Phone?"),
        "expect_q": False,
    },
    {
        "name": "v1.24.72 — ✓ inline format with 'Date & Time:'",
        "text": """Got it! JVC Building 3838, Unit 309.

Just to confirm everything before we book:

✓ Services: Deep Cleaning, Pest Control, Sofa & Carpet Shampoo
✓ Location: Furjan, Dubai
✓ Date & Time: Monday, 18 May 2026 at 12:00 PM
✓ Address: JVC Building 3838, Unit 309
✓ Name: Khaqan
✓ Phone: 0559396459

Total: AED 819 (VAT inclusive)

[Book now ↗] and we'll get you confirmed!""",
        "expect_q": True,
    },
    {
        "name": "v1.24.78 — bullet • format with em-dash prices",
        "text": """Perfect, Khaqan! All set. Here's your final booking summary:

Services:
• Deep Cleaning — AED 490
• Pest Control — AED 280
• Sofa & Carpet Shampoo — AED 49

Details:
• Name: Khaqan Shahehe
• Phone: 0559396459
• Location: JVC 8384, 284, Furjan, Dubai
• Date & Time: Tomorrow at 8:00 AM

[Book now ↗](/book.html)

Our team will confirm via SMS shortly.""",
        "expect_q": True,
    },
    {
        "name": "Earlier bulleted format with 'Time:' label",
        "text": """Here's your booking summary:

Services:
- Deep Cleaning (from AED 490)
- Pest Control (from AED 280)

Details:
- Name: Test
- Address: X
- Time: Tomorrow 8 AM
- Phone: 9999

[Book now ↗](/book.html)""",
        "expect_q": True,
    },
    {
        "name": "Hypothetical: numbered list with 'Booking summary:' header",
        "text": """Booking summary:

1. Deep Cleaning · AED 490
2. Pest Control · AED 280
3. Sofa & Carpet Shampoo · AED 49

Name: Khaqan
Address: JVC 8384, Furjan
Date: 2026-05-18
Time: 10:00 AM
Phone: 0559396459

[Book now ↗](/book.html)""",
        "expect_q": True,
    },
    {
        "name": "Edge: prose mention with 'deep cleaning' word — must NOT auto-create",
        "text": "Sure, we offer Deep Cleaning. What date works?",
        "expect_q": False,
    },
    {
        "name": "Edge: 'Book now' but NO summary — must NOT auto-create",
        "text": "Click [Book now ↗](/book.html) to start.",
        "expect_q": False,
    },
    {
        "name": "v1.24.80 — pre-summary asking for fuller address (no 'Book now' yet)",
        "text": """Thanks, Khaqan! Just to confirm before I finalize your bookings:

**Your details:**
• Name: Khaqan Shahehe
• Phone: 0559396459
• Location: Furjan, Dubai
• Time: Tomorrow at 8:00 AM
• Services: Deep Cleaning + Pest Control + Sofa & Carpet Shampoo

Could you provide the **complete address** (building name/number and street)? This ensures our team arrives at the right spot.

Once you give me that, I'll get you booked! 🙌""",
        "expect_q": False,  # bot is correctly asking for complete address — must not auto-quote yet
    },
]

passed = 0; failed = []
def t(name, ok, detail=""):
    global passed
    if ok: passed += 1
    else: failed.append((name, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))

print("="*78)
print(f"REAL-FIXTURE REGRESSION ({len(FIXTURES)} captured bot outputs)")
print("="*78)

for fix in FIXTURES:
    out = eq(fix["text"], session_id="reg-" + fix["name"][:10])
    qid = re.search(r"Q-[A-Z0-9]{6}", out)
    has_q = bool(qid)
    name = fix["name"]
    if fix["expect_q"]:
        ok = has_q and "[[quote_card:" in out and "Book now" not in out
        detail = (qid.group(0) if qid else "no Q-") if ok else (
            f"Q={has_q}, card={'[[quote_card:' in out}, "
            f"book_removed={'Book now' not in out}")
        t(name, ok, detail)
    else:
        ok = not has_q
        t(name, ok, "should NOT have Q-" if not ok else "")

print("\n" + "="*78)
print(f"FIXTURE RESULT: {passed}/{len(FIXTURES)}")
print("="*78)
sys.exit(0 if not failed else 1)
