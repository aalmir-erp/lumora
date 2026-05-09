"""v1.24.82 — quote versioning + 3-state change policy regression."""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/test_versioning.db"
sys.path.insert(0, ".")
import os; os.unlink("/tmp/test_versioning.db") if os.path.exists("/tmp/test_versioning.db") else None
from app.tools import create_multi_quote
from app import db as _db

passed = 0; failed = []
def t(name, ok, detail=""):
    global passed
    if ok: passed += 1
    else: failed.append((name, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))

q1 = create_multi_quote(
    services=[{"service_id":"deep_cleaning"},{"service_id":"pest_control"}],
    customer_name="Test", phone="999", address="X",
    target_date="2026-05-25", time_slot="10:00", session_id="vt-1")
t("Initial quote created", q1.get("ok") and q1.get("quote_id","").startswith("Q-"))
qid_base = q1["quote_id"]

q2 = create_multi_quote(
    services=[{"service_id":"deep_cleaning"},{"service_id":"pest_control"},
              {"service_id":"sofa_carpet"}],
    customer_name="Test", phone="999", address="X",
    target_date="2026-05-25", time_slot="10:00", session_id="vt-1",
    revise_of=qid_base)
t("Pre-sign edit → SAME quote_id (modify in place)",
  q2.get("ok") and q2.get("quote_id") == qid_base)

with _db.connect() as c:
    c.execute("UPDATE multi_quotes SET signed_at=? WHERE quote_id=?",
              ("2026-05-09T10:00:00Z", qid_base))

q3 = create_multi_quote(
    services=[{"service_id":"deep_cleaning"}],
    customer_name="Test", phone="999", address="X",
    target_date="2026-05-25", time_slot="10:00", session_id="vt-1",
    revise_of=qid_base)
t("Post-sign revise → Q-XXX-1 (versioned)",
  q3.get("ok") and q3.get("quote_id") == f"{qid_base}-1")

q4 = create_multi_quote(
    services=[{"service_id":"deep_cleaning"},{"service_id":"ac_cleaning"}],
    customer_name="Test", phone="999", address="X",
    target_date="2026-05-26", time_slot="10:00", session_id="vt-1",
    revise_of=qid_base)
t("Second post-sign revise → Q-XXX-2",
  q4.get("ok") and q4.get("quote_id") == f"{qid_base}-2")

with _db.connect() as c:
    c.execute("UPDATE multi_quotes SET paid_at=? WHERE quote_id=?",
              ("2026-05-09T11:00:00Z", qid_base))

q5 = create_multi_quote(
    services=[{"service_id":"deep_cleaning"}],
    customer_name="Test", phone="999", address="X",
    target_date="2026-05-27", time_slot="10:00", session_id="vt-1",
    revise_of=qid_base)
t("Post-pay revise → REJECTED", q5.get("ok") is False)
t("Post-pay reject suggests handoff_to_human",
  q5.get("action") == "handoff_to_human")

q6 = create_multi_quote(
    services=[{"service_id":"deep_cleaning"}],
    customer_name="Test", phone="999", address="X",
    target_date="2026-05-27", time_slot="10:00",
    revise_of="Q-NOPE99")
t("Bogus revise_of → REJECTED", q6.get("ok") is False)

q7 = create_multi_quote(
    services=[{"service_id":"deep_cleaning",
               "special_instructions":"no chemicals on marble"}],
    customer_name="Test", phone="999", address="X",
    target_date="2026-05-28", time_slot="10:00", session_id="vt-2")
t("special_instructions per service flows through",
  q7.get("ok") and q7["items"][0].get("special_instructions") == "no chemicals on marble")

print()
print(f"VERSIONING & POLICY: {passed}/{passed + len(failed)}")
sys.exit(0 if not failed else 1)
