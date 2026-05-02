"""Rule-based fallback — answers without an Anthropic API key. Persists tool side-effects."""
from __future__ import annotations

import re
from datetime import date, timedelta

from . import kb, tools


_BR_RX = re.compile(r"(\d+)[\s-]*(?:bhk|bedroom|br\b|bed)", re.I)


def _service_id_for(text: str) -> str | None:
    t = text.lower()
    if "deep" in t and "kitchen" not in t: return "deep_cleaning"
    if "kitchen" in t and "deep" in t: return "kitchen_deep"
    if "villa" in t: return "villa_deep"
    if "general" in t and "clean" in t: return "general_cleaning"
    if "maid" in t: return "maid_service"
    if "office" in t: return "office_cleaning"
    if "post" in t and "construction" in t: return "post_construction"
    if "sofa" in t or "carpet" in t: return "sofa_carpet"
    if "ac " in t or "ac duct" in t or "ac clean" in t: return "ac_cleaning"
    if "move" in t and ("in" in t or "out" in t): return "move_in_out"
    if "disinfect" in t or "saniti" in t: return "disinfection"
    if "window" in t: return "window_cleaning"
    if "pest" in t or "cockroach" in t or "bedbug" in t: return "pest_control"
    if "laundry" in t or "ironing" in t: return "laundry"
    if "babysit" in t or "nanny" in t: return "babysitting"
    if "garden" in t or "lawn" in t: return "gardening"
    if "handyman" in t or "plumbing" in t or "electrician" in t: return "handyman"
    return None


def respond(user_message: str, history: list[dict]) -> dict:
    msg = user_message.strip()
    low = msg.lower()
    tool_calls: list[dict] = []

    if any(g in low for g in ("hi", "hello", "hey", "salam", "marhaba")) and len(low) < 30:
        return {"text": "Hi! I'm Lumi from Lumora. I can quote prices, check coverage, "
                        "show open slots, book a cleaner, and connect you with a human. "
                        "What do you need today?",
                "tool_calls": [], "usage": {}, "stop_reason": "end_turn"}

    if any(k in low for k in ("cover", "service in", "available in", "do you go to")):
        m = re.search(r"(dubai|sharjah|ajman|abu dhabi|umm al quwain|fujairah|ras al khaimah)", low)
        if m:
            r = tools.check_coverage(m.group(1))
            tool_calls.append({"name": "check_coverage", "input": {"area": m.group(1)}, "result": r})
            text = (f"Yes — we cover {m.group(1).title()}." if r["covered"]
                    else f"Sorry, we don't currently cover {m.group(1).title()}.")
            if r["surcharge_aed"]:
                text += f" A {r['surcharge_aed']} AED travel surcharge applies."
            return {"text": text, "tool_calls": tool_calls, "usage": {}, "stop_reason": "end_turn"}

    sid = _service_id_for(low)
    if sid and any(k in low for k in ("price", "cost", "how much", "rate", "quote", "aed")):
        bedrooms = None
        m = _BR_RX.search(low)
        if m:
            bedrooms = int(m.group(1))
        first_time = "first" in low or "new customer" in low
        kwargs = {"service_id": sid, "first_time": first_time}
        if bedrooms:
            kwargs["bedrooms"] = bedrooms
        if sid in ("ac_cleaning", "sofa_carpet"):
            n = re.search(r"(\d+)\s+(?:[a-z]+\s+){0,3}?(?:unit|seat|sqm|ac\b)", low)
            if not n:
                n = re.search(r"(\d+)\s*(?:unit|seat|sqm|ac\b)", low)
            if n:
                kwargs["units"] = int(n.group(1))
        if sid in ("maid_service", "office_cleaning", "post_construction", "babysitting", "handyman"):
            n = re.search(r"(\d+)\s*(?:hour|hr)", low)
            if n:
                kwargs["hours"] = int(n.group(1))
        if sid in ("deep_cleaning", "general_cleaning", "move_in_out", "villa_deep") and not bedrooms:
            return {"text": "Sure! How many bedrooms is the place? (Studio counts as 1.)",
                    "tool_calls": [], "usage": {}, "stop_reason": "end_turn"}
        q = tools.get_quote(**kwargs)
        tool_calls.append({"name": "get_quote", "input": kwargs, "result": q})
        if not q.get("ok"):
            return {"text": q.get("error", "Couldn't compute a quote."),
                    "tool_calls": tool_calls, "usage": {}, "stop_reason": "end_turn"}
        lines = [f"Here's an indicative quote for **{sid.replace('_', ' ').title()}**:"]
        for b in q["breakdown"]:
            lines.append(f"  • {b['label']}: {b['amount']} AED")
        if q["discount"]:
            lines.append(f"_Discount applied: -{q['discount']} AED_")
        lines.append(f"**Total: {q['total']} AED** (incl. 5% VAT).")
        lines.append("\nWant me to check available time slots? Just tell me the date.")
        return {"text": "\n".join(lines), "tool_calls": tool_calls, "usage": {}, "stop_reason": "end_turn"}

    if any(k in low for k in ("slot", "available", "tomorrow", "today", "book for")):
        target = None
        if "tomorrow" in low:
            target = (date.today() + timedelta(days=1)).isoformat()
        elif "today" in low:
            target = date.today().isoformat()
        else:
            m = re.search(r"(\d{4}-\d{2}-\d{2})", msg)
            if m:
                target = m.group(1)
        if target:
            r = tools.list_slots(target)
            tool_calls.append({"name": "list_slots", "input": {"target_date": target}, "result": r})
            if r.get("ok"):
                slots = ", ".join(r["slots"]) or "(no slots — try another day)"
                return {"text": f"Open slots on {target}: {slots}.\nWhich one works for you?",
                        "tool_calls": tool_calls, "usage": {}, "stop_reason": "end_turn"}

    if any(k in low for k in ("complain", "manager", "human", "agent", "speak to someone", "refund")):
        r = tools.handoff_to_human(reason="Customer requested human", summary=msg)
        tool_calls.append({"name": "handoff_to_human", "input": {"reason": "demo"}, "result": r})
        return {"text": r["message"], "tool_calls": tool_calls, "usage": {}, "stop_reason": "end_turn"}

    return {"text": ("I can help with:\n"
                     "• **Quotes** — try “How much for deep cleaning a 2-bedroom?”\n"
                     "• **Coverage** — “Do you cover Sharjah?”\n"
                     "• **Slots & booking** — “What's available tomorrow?”\n"
                     "• **Live agent** — say “talk to a human”."),
            "tool_calls": [], "usage": {}, "stop_reason": "end_turn"}
