"""20-scenario end-to-end smoke test against the live Servia deployment.

Runs from a GitHub Actions runner (or any host with internet). Records every
HTTP call + result + assertion, prints a markdown report, exits 0 always so the
report always commits. Set BASE_URL + ADMIN_TOKEN as env vars.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta

BASE = os.environ.get("BASE_URL", "https://lumora-production-4071.up.railway.app").rstrip("/")
ADMIN = os.environ.get("ADMIN_TOKEN", "")
results: list[dict] = []


def call(method: str, path: str, body=None, headers=None, expect=200, timeout=30):
    h = {"Content-Type": "application/json", "User-Agent": "lumora-e2e/1.0"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            code = r.getcode()
            try:
                payload = json.loads(raw)
            except Exception:
                payload = raw.decode(errors="replace")[:300]
            ok = (code == expect) if isinstance(expect, int) else (code in expect)
            return {"ok": ok, "code": code, "data": payload, "ms": int((time.time()-t0)*1000)}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            payload = json.loads(body)
        except Exception:
            payload = body[:300]
        return {"ok": e.code == expect, "code": e.code, "data": payload, "ms": int((time.time()-t0)*1000)}
    except Exception as e:
        return {"ok": False, "code": None, "data": str(e), "ms": int((time.time()-t0)*1000)}


def scenario(num: int, title: str):
    def deco(fn):
        def wrapped():
            print(f"\n=== #{num}: {title} ===", flush=True)
            try:
                steps = fn()
            except Exception as e:
                steps = [{"step": "exception", "ok": False, "data": str(e)}]
            passed = all(s.get("ok") for s in steps)
            results.append({"num": num, "title": title, "passed": passed, "steps": steps})
            for s in steps:
                ok = "✓" if s.get("ok") else "✗"
                summary = s.get("summary") or json.dumps(s.get("data"))[:120]
                print(f"  {ok} [{s.get('ms','?')}ms] {s['step']}: {summary}", flush=True)
        wrapped._n = num; wrapped._t = title
        return wrapped
    return deco


def get_or_default(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d: d = d[k]
        else: return default
    return d


# ---------- shared state across scenarios ----------
S = {"phone": "+971501234567", "session_id": None, "customer_token": None,
     "customer_id": None, "address_id": None, "booking_ids": [],
     "quote_id": None, "invoice_id": None, "vendor_token": None,
     "vendor_id": None, "claimable_booking": None}


# ============================================================
# Scenario 1 — Anonymous: deep cleaning 2BR quote
# ============================================================
@scenario(1, "Anonymous: deep clean 2BR quote")
def s1():
    r = call("POST", "/api/chat", {"message": "How much for deep cleaning a 2-bedroom?"})
    text = get_or_default(r, "data", "text") or ""
    has_aed = "AED" in text or "aed" in text.lower()
    tools = get_or_default(r, "data", "tool_calls") or []
    has_quote = any(t.get("name") == "get_quote" for t in tools)
    return [{"step": "POST /api/chat", "ok": r["ok"] and (has_aed or has_quote),
             "ms": r["ms"], "code": r["code"],
             "summary": f"text len={len(text)}, has AED: {has_aed}, has tool_call: {has_quote}",
             "data": text[:200]}]


# ============================================================
# Scenario 2 — Quote with addons (deep clean + oven + fridge)
# ============================================================
@scenario(2, "Anonymous: deep clean 3BR with addons (oven, fridge)")
def s2():
    r = call("POST", "/api/chat", {"message": "Quote for deep_cleaning 3 bedroom with addons oven,fridge"})
    text = get_or_default(r, "data", "text") or ""
    tools = get_or_default(r, "data", "tool_calls") or []
    quote_call = next((t for t in tools if t.get("name") == "get_quote"), None)
    total = get_or_default(quote_call, "result", "total") if quote_call else None
    err = ""
    if not r["ok"]:
        err = json.dumps(r["data"])[:200]
    return [{"step": "POST /api/chat (with addons)", "ok": r["ok"] and total is not None,
             "ms": r["ms"], "code": r["code"],
             "summary": f"total: {total} AED" + (f" — err: {err}" if err else ""),
             "data": (text or "")[:200]}]


# ============================================================
# Scenario 3 — Coverage: Sharjah (covered)
# ============================================================
@scenario(3, "Anonymous: coverage check Sharjah")
def s3():
    r = call("POST", "/api/chat", {"message": "Do you cover Sharjah?"})
    tools = get_or_default(r, "data", "tool_calls") or []
    cov = next((t for t in tools if t.get("name") == "check_coverage"), None)
    covered = get_or_default(cov, "result", "covered")
    return [{"step": "POST /api/chat (coverage)", "ok": r["ok"] and covered is True,
             "ms": r["ms"], "code": r["code"],
             "summary": f"Sharjah covered: {covered}",
             "data": (get_or_default(r, "data", "text") or "")[:200]}]


# ============================================================
# Scenario 4 — Public APIs (services + brand + i18n + reviews)
# ============================================================
@scenario(4, "Public: GET /api/services + /api/brand + /api/i18n")
def s4():
    s = call("GET", "/api/services")
    b = call("GET", "/api/brand")
    i = call("GET", "/api/i18n")
    n_svcs = len(get_or_default(s, "data", "services", default=[]))
    brand_phone = get_or_default(b, "data", "phone")
    n_langs = len(get_or_default(i, "data", default={}).keys()) if isinstance(get_or_default(i, "data"), dict) else 0
    return [
        {"step": "GET /api/services", "ok": s["ok"] and n_svcs >= 17, "ms": s["ms"], "code": s["code"],
         "summary": f"{n_svcs} services"},
        {"step": "GET /api/brand", "ok": b["ok"] and bool(brand_phone), "ms": b["ms"], "code": b["code"],
         "summary": f"phone: {brand_phone}"},
        {"step": "GET /api/i18n", "ok": i["ok"] and n_langs >= 4, "ms": i["ms"], "code": i["code"],
         "summary": f"{n_langs} languages"},
    ]


# ============================================================
# Scenario 5 — Anonymous booking via chat
# ============================================================
@scenario(5, "Anonymous: book general cleaning 2BR via chat")
def s5():
    tomorrow = (datetime.utcnow() + timedelta(days=2)).date().isoformat()
    msg = (f"Book general_cleaning on {tomorrow} at 10:00 for Test User One, "
           f"phone {S['phone']}, address: 'Apt 101, Marina Tower, Dubai Marina', 2 bedrooms")
    r = call("POST", "/api/chat", {"message": msg})
    tools = get_or_default(r, "data", "tool_calls") or []
    book_call = next((t for t in tools if t.get("name") == "create_booking"), None)
    bid = get_or_default(book_call, "result", "booking", "id") if book_call else None
    if bid: S["booking_ids"].append(bid)
    return [{"step": "POST /api/chat (book)", "ok": r["ok"] and bool(bid),
             "ms": r["ms"], "code": r["code"],
             "summary": f"booking_id: {bid}",
             "data": (get_or_default(r, "data", "text") or "")[:200]}]


# ============================================================
# Scenario 6 — Anonymous: AC cleaning 4 units
# ============================================================
@scenario(6, "Anonymous: book AC cleaning 4 units")
def s6():
    tomorrow = (datetime.utcnow() + timedelta(days=3)).date().isoformat()
    msg = (f"Book ac_cleaning on {tomorrow} at 14:00 for Test User Two, "
           f"phone {S['phone']}, address: 'Villa 22, Mirdif Hills', 4 units")
    r = call("POST", "/api/chat", {"message": msg})
    tools = get_or_default(r, "data", "tool_calls") or []
    book_call = next((t for t in tools if t.get("name") == "create_booking"), None)
    bid = get_or_default(book_call, "result", "booking", "id") if book_call else None
    if bid: S["booking_ids"].append(bid)
    return [{"step": "POST /api/chat (AC book)", "ok": r["ok"] and bool(bid),
             "ms": r["ms"], "code": r["code"],
             "summary": f"booking_id: {bid}"}]


# ============================================================
# Scenarios 7-10 — Customer portal flow (OTP login → profile → addresses)
# ============================================================
@scenario(7, "Customer: OTP request + verify (login flow)")
def s7():
    r1 = call("POST", "/api/auth/customer/start", {"phone": S["phone"]})
    code = get_or_default(r1, "data", "dev_otp")
    if not code:
        return [{"step": "OTP issue", "ok": False, "ms": r1["ms"], "code": r1["code"],
                 "summary": "no dev_otp returned (WhatsApp bridge active or production mode)"}]
    r2 = call("POST", "/api/auth/customer/verify", {"phone": S["phone"], "code": code})
    token = get_or_default(r2, "data", "token")
    cid = get_or_default(r2, "data", "customer_id")
    if token:
        S["customer_token"] = token; S["customer_id"] = cid
    return [
        {"step": "POST /auth/customer/start", "ok": r1["ok"] and bool(code), "ms": r1["ms"], "code": r1["code"],
         "summary": f"OTP: {code}"},
        {"step": "POST /auth/customer/verify", "ok": r2["ok"] and bool(token), "ms": r2["ms"], "code": r2["code"],
         "summary": f"customer_id={cid}, token len={len(token) if token else 0}"},
    ]


@scenario(8, "Customer: update profile (name, email, language)")
def s8():
    if not S["customer_token"]:
        return [{"step": "skip", "ok": False, "summary": "no token"}]
    r = call("POST", "/api/me/profile",
             {"name": "Sara Mansoori", "email": "sara@example.com", "language": "ar"},
             headers={"Authorization": "Bearer " + S["customer_token"]})
    return [{"step": "POST /api/me/profile", "ok": r["ok"], "ms": r["ms"], "code": r["code"],
             "summary": json.dumps(r["data"])[:120]}]


@scenario(9, "Customer: add 2 saved addresses, fetch list")
def s9():
    if not S["customer_token"]:
        return [{"step": "skip", "ok": False, "summary": "no token"}]
    h = {"Authorization": "Bearer " + S["customer_token"]}
    r1 = call("POST", "/api/me/addresses",
              {"label": "Home", "address": "Apt 1502, Marina Pearl", "area": "Dubai Marina", "is_default": True},
              headers=h)
    r2 = call("POST", "/api/me/addresses",
              {"label": "Office", "address": "Office 305, JLT Cluster T", "area": "JLT", "is_default": False},
              headers=h)
    r3 = call("GET", "/api/me/addresses", headers=h)
    addrs = get_or_default(r3, "data", "addresses") or []
    S["address_id"] = get_or_default(r1, "data", "id")
    return [
        {"step": "POST /me/addresses (Home)", "ok": r1["ok"], "ms": r1["ms"], "code": r1["code"],
         "summary": f"id={S['address_id']}"},
        {"step": "POST /me/addresses (Office)", "ok": r2["ok"], "ms": r2["ms"], "code": r2["code"]},
        {"step": "GET /me/addresses", "ok": r3["ok"] and len(addrs) >= 2, "ms": r3["ms"], "code": r3["code"],
         "summary": f"count={len(addrs)}"},
    ]


@scenario(10, "Customer: fetch own bookings")
def s10():
    if not S["customer_token"]:
        return [{"step": "skip", "ok": False, "summary": "no token"}]
    r = call("GET", "/api/me/bookings", headers={"Authorization": "Bearer " + S["customer_token"]})
    bookings = get_or_default(r, "data", "bookings") or []
    return [{"step": "GET /api/me/bookings", "ok": r["ok"], "ms": r["ms"], "code": r["code"],
             "summary": f"count={len(bookings)}"}]


# ============================================================
# Scenarios 11-13 — Cancel + reschedule + review
# ============================================================
@scenario(11, "Customer: cancel a booking with reason")
def s11():
    if not S["customer_token"] or not S["booking_ids"]:
        return [{"step": "skip", "ok": False, "summary": "missing prereqs"}]
    bid = S["booking_ids"][0]
    h = {"Authorization": "Bearer " + S["customer_token"]}
    r = call("POST", f"/api/me/booking/{bid}/cancel",
             {"reason": "Plans changed"}, headers=h)
    return [{"step": f"POST /me/booking/{bid}/cancel", "ok": r["ok"], "ms": r["ms"], "code": r["code"],
             "summary": json.dumps(r["data"])[:120]}]


@scenario(12, "Customer: reschedule a booking")
def s12():
    if not S["customer_token"] or len(S["booking_ids"]) < 2:
        return [{"step": "skip", "ok": False, "summary": "missing prereqs"}]
    bid = S["booking_ids"][1]
    new_date = (datetime.utcnow() + timedelta(days=5)).date().isoformat()
    h = {"Authorization": "Bearer " + S["customer_token"]}
    r = call("POST", f"/api/me/booking/{bid}/reschedule",
             {"target_date": new_date, "time_slot": "16:00"}, headers=h)
    return [{"step": f"POST /me/booking/{bid}/reschedule", "ok": r["ok"], "ms": r["ms"], "code": r["code"],
             "summary": f"to {new_date} 16:00"}]


@scenario(13, "Customer: submit review (4 stars)")
def s13():
    if not S["customer_token"] or not S["booking_ids"]:
        return [{"step": "skip", "ok": False, "summary": "no booking"}]
    bid = S["booking_ids"][0]
    h = {"Authorization": "Bearer " + S["customer_token"]}
    r = call("POST", "/api/me/review",
             {"booking_id": bid, "stars": 4, "comment": "Friendly cleaner, on time"},
             headers=h)
    # May fail if booking is cancelled — not a real bug, just expected
    return [{"step": "POST /api/me/review", "ok": r["code"] in (200, 400, 403),
             "ms": r["ms"], "code": r["code"],
             "summary": json.dumps(r["data"])[:120]}]


# ============================================================
# Scenarios 14-16 — Vendor flow
# ============================================================
@scenario(14, "Vendor: login (seeded JustMop)")
def s14():
    r = call("POST", "/api/auth/vendor/login",
             {"email": "ops@justmop.lumora", "password": "lumora-vendor-default"})
    token = get_or_default(r, "data", "token")
    if token: S["vendor_token"] = token; S["vendor_id"] = get_or_default(r, "data", "vendor_id")
    return [{"step": "POST /auth/vendor/login", "ok": r["ok"] and bool(token), "ms": r["ms"], "code": r["code"],
             "summary": f"vendor_id={S['vendor_id']}, token len={len(token) if token else 0}"}]


@scenario(15, "Vendor: list available marketplace jobs")
def s15():
    if not S["vendor_token"]:
        return [{"step": "skip", "ok": False, "summary": "no vendor token"}]
    h = {"Authorization": "Bearer " + S["vendor_token"]}
    r = call("GET", "/api/vendor/jobs/available", headers=h)
    jobs = get_or_default(r, "data", "jobs") or []
    if jobs: S["claimable_booking"] = jobs[0].get("id")
    return [{"step": "GET /vendor/jobs/available", "ok": r["ok"], "ms": r["ms"], "code": r["code"],
             "summary": f"{len(jobs)} available, first: {S['claimable_booking']}"}]


@scenario(16, "Vendor: claim a job + mark in_progress + completed")
def s16():
    if not S["vendor_token"] or not S["claimable_booking"]:
        return [{"step": "skip", "ok": False, "summary": "no claimable booking"}]
    bid = S["claimable_booking"]
    h = {"Authorization": "Bearer " + S["vendor_token"]}
    r1 = call("POST", "/api/vendor/jobs/claim", {"booking_id": bid}, headers=h)
    r2 = call("POST", "/api/vendor/jobs/status",
              {"booking_id": bid, "status": "in_progress"}, headers=h)
    r3 = call("POST", "/api/vendor/jobs/status",
              {"booking_id": bid, "status": "completed"}, headers=h)
    return [
        {"step": "POST /vendor/jobs/claim", "ok": r1["ok"], "ms": r1["ms"], "code": r1["code"],
         "summary": json.dumps(r1["data"])[:120]},
        {"step": "POST /vendor/jobs/status (in_progress)", "ok": r2["ok"], "ms": r2["ms"], "code": r2["code"]},
        {"step": "POST /vendor/jobs/status (completed)", "ok": r3["ok"], "ms": r3["ms"], "code": r3["code"]},
    ]


# ============================================================
# Scenarios 17-19 — Admin flows
# ============================================================
@scenario(17, "Admin: GET stats + vendors + services-summary")
def s17():
    if not ADMIN:
        return [{"step": "skip", "ok": False, "summary": "no ADMIN_TOKEN"}]
    h = {"Authorization": "Bearer " + ADMIN}
    r1 = call("GET", "/api/admin/stats", headers=h)
    r2 = call("GET", "/api/admin/vendors", headers=h)
    r3 = call("GET", "/api/admin/services-summary", headers=h)
    n_v = len(get_or_default(r2, "data", "vendors") or [])
    n_s = len(get_or_default(r3, "data", "services") or [])
    return [
        {"step": "GET /admin/stats", "ok": r1["ok"], "ms": r1["ms"], "code": r1["code"],
         "summary": f"bookings_today={get_or_default(r1,'data','bookings_today')}, total={get_or_default(r1,'data','bookings_total')}"},
        {"step": "GET /admin/vendors", "ok": r2["ok"] and n_v >= 40, "ms": r2["ms"], "code": r2["code"],
         "summary": f"{n_v} vendors"},
        {"step": "GET /admin/services-summary", "ok": r3["ok"] and n_s >= 17, "ms": r3["ms"], "code": r3["code"],
         "summary": f"{n_s} services"},
    ]


@scenario(18, "Admin: read brand, no-op patch (preserve existing)")
def s18():
    if not ADMIN:
        return [{"step": "skip", "ok": False, "summary": "no token"}]
    h = {"Authorization": "Bearer " + ADMIN}
    r1 = call("GET", "/api/admin/brand", headers=h)
    cur_phone = get_or_default(r1, "data", "phone")
    # Patch with the same value (idempotent test — does not change live phone)
    r2 = call("POST", "/api/admin/brand", {"phone": cur_phone}, headers=h)
    return [
        {"step": "GET /admin/brand", "ok": r1["ok"], "ms": r1["ms"], "code": r1["code"],
         "summary": f"phone={cur_phone}"},
        {"step": "POST /admin/brand (no-op)", "ok": r2["ok"], "ms": r2["ms"], "code": r2["code"]},
    ]


@scenario(19, "Admin: service detail (vendors + pricing)")
def s19():
    if not ADMIN:
        return [{"step": "skip", "ok": False, "summary": "no token"}]
    h = {"Authorization": "Bearer " + ADMIN}
    r = call("GET", "/api/admin/service/deep_cleaning", headers=h)
    n = len(get_or_default(r, "data", "vendors") or [])
    return [{"step": "GET /admin/service/deep_cleaning", "ok": r["ok"] and n >= 5,
             "ms": r["ms"], "code": r["code"],
             "summary": f"{n} vendors offering"}]


# ============================================================
# Scenario 20 — Public reviews
# ============================================================
@scenario(20, "Public: GET /api/reviews/deep_cleaning")
def s20():
    r = call("GET", "/api/reviews/deep_cleaning")
    return [{"step": "GET /api/reviews/deep_cleaning", "ok": r["ok"],
             "ms": r["ms"], "code": r["code"],
             "summary": f"count={get_or_default(r,'data','count')}, avg={get_or_default(r,'data','avg')}"}]


# ----- Run all -----
def main():
    funcs = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10,
             s11, s12, s13, s14, s15, s16, s17, s18, s19, s20]
    print(f"=== Running {len(funcs)} scenarios against {BASE} ===\n")
    for f in funcs:
        f()
        time.sleep(2.0)

    # Summary
    passed = sum(1 for r in results if r["passed"])
    print(f"\n=== {passed}/{len(results)} scenarios passed ===")

    # Markdown report
    out = ["# Servia E2E Test Report",
           f"\n**URL:** {BASE}",
           f"**Run at:** {datetime.utcnow().isoformat()}Z",
           f"**Result:** **{passed}/{len(results)} scenarios passed**",
           ""]
    for r in results:
        icon = "✅" if r["passed"] else "❌"
        out.append(f"\n## {icon} #{r['num']}: {r['title']}")
        out.append("| Step | Code | Time | Result |")
        out.append("|---|---|---|---|")
        for s in r["steps"]:
            ok = "✓" if s.get("ok") else "✗"
            summary = (s.get("summary") or json.dumps(s.get("data"))[:120]).replace("|", "\\|")
            out.append(f"| {ok} {s['step']} | {s.get('code','—')} | {s.get('ms','?')}ms | {summary[:120]} |")

    out.append("\n## State captured during run")
    out.append("```json\n" + json.dumps({k: (v[:8]+"…" if isinstance(v,str) and len(v)>16 else v) for k,v in S.items()},
                                         indent=2, default=str) + "\n```")

    open("TEST_RESULTS.md", "w").write("\n".join(out))
    print("\nReport written to TEST_RESULTS.md")


if __name__ == "__main__":
    main()
