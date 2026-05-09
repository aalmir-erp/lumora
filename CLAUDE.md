# 🤖 Claude Code — Servia / Lumora project rules

**Read this first, every session.** It captures mistakes made on
2026-05-09 by a previous Claude session that wasted hours of the user's
time. None of these mistakes should ever happen again.

---

## 🚨 Top-3 rules — break any of these and you owe the user an apology

### 🎨 DESIGN-REVIEW gate (added v1.24.77)

ANY new design — page redesign, modal, button, chip, badge, banner,
icon, color change — MUST pass through:

1. **Senior designer review** (visual hierarchy, brand alignment, type
   scale, spacing, accessibility)
2. **UX developer review** (touch targets ≥44px on mobile, hover states,
   loading states, error states, keyboard nav, screen-reader labels)
3. **Screenshot delivered to user** before pushing — render the
   change in a TestClient or local server, save the rendered HTML, and
   describe it in the message ("here's the new quote-card layout: ...
   you can see it at http://localhost:8000/q/Q-XYZ"). DO NOT ship
   visual changes blind.

This rule applies even to a single button. The product has a brand
voice and the user is the brand owner — every visual decision is
theirs to approve, not mine to ship silently.

### 🧪 TESTING LOOPHOLES — categorise + cover (added v1.24.77)

Five recurring test loopholes that have caused me to lie about
"tested ✅":

**Loophole 1 — Unit-test green ≠ feature-works green.**
I tested `_enforce_picker_and_one_question()` directly and it produced
the right output for synthetic inputs. But I never ran a TestClient
chat round-trip to confirm the picker actually reaches the user via
the real `/api/chat` endpoint. Coverage: every chat-flow change must
ship with a TestClient request that drives `/api/chat` and asserts
the final response text contains `[[picker:date]]` (or whatever).

**Loophole 2 — My made-up fixture ≠ real LLM output.**
My parser test used a bulleted-list format I invented. Real bot
output used `✓ Services: A, B, C` (inline). Parser silently returned
[]. Coverage: every text-parser test must include AT LEAST ONE
fixture that is the EXACT text from the user's most recent
screenshot, copy-pasted verbatim.

**Loophole 3 — Local green ≠ deployed green.**
I claimed "v1.24.X is fixed" but Railway hadn't redeployed yet,
service worker hadn't busted cache, or the browser was on
v1.24.X-1. Coverage: when claiming fix-deployed, list:
  a) commit hash pushed
  b) Railway deploy URL  
  c) the version footer the user should see
  d) cache-busting steps if their browser is stuck

**Loophole 4 — Component tested ≠ pipeline tested.**
I tested `create_multi_quote()` returns a row in `multi_quotes`. I
never tested that the conversation phone is correctly indexed so
`/api/me/history?phone=X` returns it. The user reported "no
matches" → my Q-XXXXXX existed but wasn't queryable. Coverage:
every persistence test must include a "find it back" assertion via
the actual lookup endpoint (history, list, search), not just SELECT
from the table.

**Loophole 5 — Happy path tested ≠ rejection path tested.**
I tested that good input creates the quote. I never tested:
  - bad inputs (wrong service id) → 4xx not 500
  - duplicate calls → idempotent or clean error
  - empty / partial fields → tool blocker fires
  - cancellation / abort → DB row marked or removed
Coverage: at least one rejection-path test per public surface.

### 🔒 SCOPE-OF-WORK contract (NEVER violate, even silently)

These are decisions the founder has already made about how the product
must behave. They override default coding instincts — DO NOT add
"normal" implementations that contradict them.

**A) Stealth-launch payment gate (GATE_BOOKINGS=1)**
"Pay with card" must NOT actually charge a card. It routes to
`/gate.html?inv=<id>&amount=<n>` which shows a friendly "your card was
declined by your bank" message and offers a 15% discount voucher in
exchange for WhatsApp contact. Captures real demand without delivering
service. Files: `app/quotes.py::_make_payment_link`,
`app/multi_quote_pages.py::pay_landing`.

If you're writing a new payment-related code path, it MUST honour
`GATE_BOOKINGS` first — never bypass it with a Stripe / direct gateway
link. Switch is `app/config.py :: GATE_BOOKINGS`.

**B) Clean URLs (no .html in production paths)**
The site is served via FastAPI middleware that:
- `/faq` → serves `web/faq.html` transparently
- `/faq.html` → 301 redirect to `/faq`
- `/services/<slug>` and `/services/<slug>.html` both work
Internal links, sitemap, canonical tags must use the clean form.
Files: `app/main.py :: _CleanURLMiddleware`, `service_slug_page`.

**C) "Get the Servia app" FAB hidden on transactional pages**
Never show the install FAB or the install banner on `/book`, `/q/`,
`/p/`, `/i/`, `/pay/`, `/cart`, `/checkout` — they distract from the
checkout task. Files: `web/install.js :: injectFAB`.

**D) Multi-service flow uses Q-XXXXXX, not "Book now ↗"**
When the customer is buying 2+ services, the bot output (or the
server-side post-processor) MUST produce a structured cart with
Q-XXXXXX, sign URL, pay URL, manual-pay fallback. The legacy
single-service `Book now ↗ /book.html?service=X` link is BANNED for
multi-service. Server-side guards live at:
- `app/llm.py :: _enforce_multi_quote_when_book_now` (output post-processor)
- `app/llm.py :: chat()` tool dispatch (rejects create_booking when 2+ services)

**E) Service-specific intake uses ASK_FOR_BOOKING from KB**
The bot must only ask the fields listed in each service's
ASK_FOR_BOOKING (e.g. `bedrooms` for cleaning, `ac_units_count` for
ac_cleaning, `pool_size_sqm` for swimming_pool). Never invent fields
the KB doesn't list. Never skip required fields the KB lists.

**F) UI uniformity — never fork the canonical template**
Every service detail page is rendered from the SINGLE canonical
template `web/service.html` via `app/main.py :: service_slug_page`.
Do NOT create per-service custom HTML files — it produces visually
inconsistent pages. New service = add to `services.json` + `pricing.json`,
the slug page renders automatically.

If you ever feel like duplicating page structure, DON'T. Use the
canonical template.

### 0. NEVER say "fixed" / "okay" / "done" without showing test output

**Hard rule (added v1.24.72, refined v1.24.75)**: when the user reports a
bug, you must:
1. Write a real test that reproduces it (Python + TestClient + Node for
   widget regex if needed)
2. **Use the EXACT bot output from the user's screenshot as your test
   fixture** — not a contrived format you made up. Different LLM versions
   produce different reply formats (bulleted vs ✓-prefixed inline vs
   "Date & Time:" vs "Time:") and a parser that works on Format A will
   silently return [] on Format B.
3. Run it and capture PASS/FAIL output
4. Show the test output to the user BEFORE claiming the fix works
5. If PASS → push; if FAIL → keep fixing, don't push

**v1.24.75 retrospective**: I claimed "24/24 PASS" for v1.24.73, but
the parser only handled the bulleted format. Real production output
used `✓ Services: A, B, C` (inline comma-separated, ✓ prefix, "Date &
Time:" label). My parser returned `services: []` → post-processor
exited → no Q-XXXXXX. The user paid for 3 more wasted iterations.

**v1.24.77 retrospective (THE END-TO-END LIE)**: Test passed for
`_enforce_multi_quote_when_book_now()` directly — I fed it sample
text, it produced Q-XXXXXX. Shipped, called it done. User reported
the History tab still says "No matches for this phone." I had NEVER
verified the chat endpoint → real LLM → post-processor → DB save →
phone-indexed history → search round-trip end-to-end. **Unit-test
green ≠ feature-works green.** Going forward, every chat-flow change
MUST also include:

```python
# E2E pseudo-test recipe — REQUIRED for any chat/quote/booking change
client = TestClient(app)
sid = "e2e-" + uuid4().hex
# Drive a real chat sequence
for msg in ["hi", "deep cleaning + pest", "2 br", "tomorrow", ...]:
    client.post("/api/chat", json={"session_id": sid, "message": msg, "phone": "0559396459"})
# Then verify
assert phone_appears_in_DB(table="multi_quotes", phone="0559396459")
assert client.get("/api/me/history?phone=0559396459").json()["count"] >= 1
```

Without an actual ANTHROPIC_API_KEY in the sandbox the LLM won't drive
the chat — but you can still test the post-processor + DB persistence
+ history endpoint round-trip with a mocked-LLM fixture. That mock
must use a REAL bot reply (from the user's screenshot), not made up.

**The fix discipline**: every parser/regex must be tested against:
  a) The fixture I made up (synthetic test)
  b) **The exact text from the user's screenshot** (real-world test)
  c) An edge case it should NOT match (prose / casual mention)

Without (b) and (c), the test is theatre, not verification.

If you don't have an API key to drive the LLM in the sandbox, mock the
LLM output (capture its prior reply from the screenshot, paste it into
the test as input) and run the post-processor / widget extractor against
it. The user has paid for hours of broken iterations because I claimed
fixes without running them. Never again.

Concrete recipes that should always be runnable:
- **Picker e2e**: `python3 /tmp/test_picker_e2e.py` — drives 7 LLM-style
  replies through `_enforce_picker_and_one_question`, then through the
  widget regex via Node. Asserts each scenario's picker kind matches and
  no >1 questions remain.
- **Multi-quote auto-creation**: feed a "Book now ↗" + 3-service summary
  to `_enforce_multi_quote_when_book_now`, assert output contains
  `Q-XXXXXX`, sign URL, pay URL, no "Book now".
- **Slug routes**: `TestClient(app).get("/services/<slug>.html")` →
  assert 200 + `mascot.svg` present + correct canonical URL.
- **Tool blocker**: assert `create_booking` rejected when 2+ services
  are in conversation history.

### 1. Verify code BEFORE saying "deployed"
After every code change, before claiming success, run:
```bash
python3 -c "import sys; sys.path.insert(0,'.'); from app import main; print('routes=', len([r for r in main.app.routes if hasattr(r,'path')]))"
```
If it errors → fix immediately, don't push, don't claim done.

Why: A previous session claimed "11 patches deployed" but the server
crashed on startup because `app.include_router(_mqp.admin_router)`
referenced an attribute that didn't exist on the module. The user had
to tell me "site not deployed" before I checked.

### 2. Apply ALL cache-bust dimensions when shipping front-end changes
Front-end deploys hit FOUR caches on the user side:
1. CDN edge (Cloudflare) — handled automatically by deploy
2. Service worker file cache (`/sw.js` constant `CACHE`)
3. Browser HTTP cache for JS/CSS
4. **Anthropic LLM prompt cache** (`cache_control=ephemeral`, ~5 min)

Every time you change widget.js, widget.css, or sw.js you MUST:
- Bump `CACHE = "servia-vX.Y.Z"` in `web/sw.js`
- Bump `APP_VERSION` in `app/config.py`
- Bump the `?v=X.Y.Z` query string in EVERY `<script src="/widget.js">`
  and `<link href="/widget.css">` reference across all `web/*.html`
  (use a one-liner: `python3 -c "..."` to mass-replace)
- Ensure `[BUILD={app_version}]` is the first line of the system prompt
  in `app/llm.py` so Anthropic's prompt cache invalidates with each deploy

Why: Sessions wasted 4+ hours debugging "why isn't my new widget
showing" — answer was always one of these caches.

### 3. Sandbox blocks ALL external hosts except github.com + pypi.org
This sandbox CANNOT reach:
- servia.ae / *.up.railway.app / lumora-production-*
- railway.app / backboard.railway.app / api.railway.app (even with token)
- google.com / dl.google.com / Maven / google-fonts
- ANY other host the user runs

You CANNOT verify anything via Playwright, curl, or HTTP from the
sandbox. Don't promise screenshots. Don't promise live tests. The user
verifies on their phone; you patch based on their report.

The sandbox CAN:
- ✅ Push to GitHub (via `local_proxy` git endpoint)
- ✅ Read/write local files
- ✅ Run Python/Node locally
- ✅ Bypass commit signing with `git -c commit.gpgsign=false` (user
  already authorized for this project)

---

## 🛑 Specific anti-patterns — avoid

### Don't `git apply --reject` patches and ignore the .rej files
Hunks that fail to apply produce `.rej` files that are silently
discarded. A previous session lost ~70 files of code this way.

If a patch fails to apply cleanly, EITHER:
- Edit the file directly with `Edit` tool (preferred)
- OR apply with `--3way` and resolve conflicts explicitly
- OR re-generate the patch against current HEAD

### Don't `git reset --soft HEAD~1` then re-commit
This sequence can lose working-tree changes if anything else manipulates
the index in between. A previous session lost the entire app/multi_quote_pages.py
this way.

If you need to amend a commit message: `git -c commit.gpgsign=false commit --amend -m "..."`

### Don't trust "branch pushed = deploy live"
Railway only deploys from `main`. Pushing to `claude/perf-patches-xyz`
does NOTHING for the running site. ALWAYS push to main directly:

```bash
git -c commit.gpgsign=false -c pull.rebase=false pull origin main --no-edit
git push origin HEAD:main
```

### Don't reference module attributes you haven't verified exist
Before writing `app.include_router(_some_module.some_router)`, grep:
```bash
grep "router\s*=\|@router" app/some_module.py
```
A previous session referenced `_mqp.admin_router` that didn't exist →
server crashed on startup.

### Don't hardcode the admin phone number anywhere
The user's personal mobile (`971564020087` historically) must NEVER
appear in source code. Use env var `ADMIN_WA_NUMBER` and admin panel.

If you find it hardcoded, scrub. If you find it in an admin DB
override (`brand_overrides.phone`), tell the user to clear it via
`/admin.html` Brand → Phone field. The `kb_blob()` function in `kb.py`
exposes brand fields to the LLM — leaks happen there.

### Don't mass-edit pricing without authorization
`app/data/pricing.json` is the canonical price source. The user bumped
40% on 2026-05-08 and may bump again. Don't change values without an
explicit ask. Admin override via DB exists but is admin-controlled.

**Important — pricing lives in TWO files**:
- `app/data/pricing.json` → used by `get_quote()` for actual computed prices
- `app/data/services.json` → used by `kb_blob()` (the LLM's KB) for "starting_price"
  hints the bot quotes when it doesn't call get_quote

If you bump `pricing.json` you MUST also bump `services.json` `starting_price` fields
by the same multiplier. Otherwise the bot quotes the OLD starting price even though
get_quote returns the NEW computed price → inconsistent prices in the same chat.

Use this snippet to bump both consistently:
```python
import json
for fname in ('app/data/pricing.json', 'app/data/services.json'):
    with open(fname) as f: d = json.load(f)
    PRICE_KEYS = {'base_per_bedroom','min_charge','hourly_rate','starting_price','base_flat',
                  'per_sqft','per_visit','flat_rate','call_out_fee','base_price','supplies_addon'}
    def bump(o, mult=1.40):
        if isinstance(o, dict):
            return {k: (round(v*mult,2) if k in PRICE_KEYS and isinstance(v,(int,float)) and not isinstance(v,bool)
                       else bump(v, mult)) for k,v in o.items()}
        if isinstance(o, list): return [bump(x, mult) for x in o]
        return o
    with open(fname,'w') as f: json.dump(bump(d), f, indent=2, ensure_ascii=False)
```

---

## 📦 Project structure (avoid hunting)

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI entrypoint, all router includes |
| `app/llm.py` | LLM persona prompts (customer + admin + vendor) |
| `app/tools.py` | Bot tool schemas + dispatch table |
| `app/multi_quote_pages.py` | `/q/{id}` `/p/{id}` `/i/{id}` `/i/{id}.pdf` |
| `app/me_history.py` | `/api/me/history` for chat widget History tab |
| `app/admin_live.py` | `/api/admin/live/*` for admin-live PWA |
| `app/admin_alerts.py` | WhatsApp bridge + push-fanout |
| `app/live_visitors.py` | Visitor tracking + click-trail |
| `app/kb.py` | KB blob fed to LLM (CAREFUL: leaks brand fields) |
| `app/config.py` | `APP_VERSION` lives here |
| `web/widget.js` | Customer chat widget (1000+ lines) |
| `web/widget.css` | Widget styles |
| `web/admin-live.html/.js/-sw.js/.webmanifest` | Admin PWA |
| `web/sw.js` | Service worker — has the CACHE constant |

## 🔐 Important env vars on Railway

| Var | Purpose | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | Default chat LLM | Bypassed if admin AI Arena sets non-Claude default |
| `CLAUDE_MODEL` | Anthropic model id | Default `claude-opus-4-7` |
| `ADMIN_TOKEN` | Admin panel auth | Default `lumora-admin-test` — should rotate |
| `ADMIN_WA_NUMBER` | Where to push admin alerts | E.164 digits: `971564020087` |
| `WA_BRIDGE_URL` | WhatsApp bridge service URL | Bridge container in same Railway project |
| `WA_BRIDGE_TOKEN` | Shared secret with bridge | |
| `STRIPE_SECRET_KEY` | Live card payments | Optional; widget gracefully degrades to WhatsApp |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook verification | |

## 🚦 Standard deploy workflow

```bash
# 1. Make changes
# 2. Local sanity check
python3 -c "import sys; sys.path.insert(0,'.'); from app import main; print('routes=', len([r for r in main.app.routes if hasattr(r,'path')]))"

# 3. Bump version (only if shipping front-end changes the user will see)
sed -i 's/APP_VERSION = "X.Y.Z"/APP_VERSION = "X.Y.Z+1"/' app/config.py
sed -i 's/servia-vX.Y.Z/servia-vX.Y.Z+1/' web/sw.js

# 4. Cache-bust front-end if widget.js / widget.css changed
python3 -c "import re,glob
for f in glob.glob('web/*.html'):
    s=open(f).read()
    n=re.sub(r'\\?v=\\d+\\.\\d+\\.\\d+','?v=X.Y.Z+1', s)
    if n!=s: open(f,'w').write(n)"

# 5. Stage + commit + push to main
git add -A
git -c commit.gpgsign=false commit -m "vX.Y.Z+1: <one-line description>"
git -c commit.gpgsign=false -c pull.rebase=false pull origin main --no-edit
git push origin HEAD:main

# 6. Wait ~2 min for Railway redeploy. Look for the next "deploy: SUCCESS"
#    commit on origin/main (the deploy bot pushes it). If "deploy: FAILED"
#    instead, investigate.
```

## 🔁 Apply discipline — no claim of "done" without:

1. ✅ Local import check passes
2. ✅ Git push succeeds (network not blocked)
3. ✅ Railway deploy bot has confirmed by pushing a "deploy: SUCCESS"
   commit (visible in `git log origin/main --oneline`)
4. ✅ User has confirmed visible change (you cannot verify yourself)

If any of those aren't done, say "deployed but not yet confirmed" — not "done".

### 🚨 RUN A REAL END-TO-END TEST BEFORE PUSHING (added v1.24.71)

Recurring failure mode: I claimed a fix worked, pushed it, user found
it didn't. Cost: hours of back-and-forth iteration on the same bug.

**Rule**: before pushing ANY chat / bot / quote / picker / multi-step
flow change, write a Python test that exercises the actual code path
and prints the result. Show the user the test output ("CONTAINS Q-:
True, sign URL: True") BEFORE saying "fixed". If you don't have an API
key in the sandbox, mock the LLM output and run the post-processor
against it.

Examples of what should always be tested locally before push:
- Picker injection — feed bot text "What date works?", assert output
  contains `[[picker:date]]`
- Multi-quote auto-creation — feed a "Book now ↗" multi-service
  summary, assert output contains `Q-XXXXXX` + sign URL + pay URL
- Service slug routes — TestClient.get(`/services/<slug>.html`),
  assert 200 + canonical nav present
- Tool blocker — assert `create_booking` is rejected when 2+ services
  are in the conversation

Common gotchas that bit me in v1.24.65 → v1.24.70:
1. Bot produces a hyperlink in TEXT, not a tool call → tool-level
   blocker can't help. Need OUTPUT post-processor.
2. Post-processor only ran inside `llm.chat()` (Anthropic-primary
   path). Cascade router / demo-brain bypassed it. Move enforcement
   to `main.py` where ALL paths converge.
3. `create_multi_quote` returned 0 AED when sizing fields missing.
   Fall back to `services.json :: starting_price`.
4. SVG hero "image" wired only as `og:image` → never rendered on the
   page. Test the actual page render, not just the file existence.
5. New service pages used custom CSS instead of `service.html`
   template → looked like a different brand. Don't fork the
   template — render the canonical one server-side with SEO meta
   injected.
6. Regex `Address|Location` without `(?:...)` group has wrong
   precedence: matches "Address" alone, group(1) is None, AttributeError
   on `.strip()`. Always wrap alternations in non-capturing groups.

## 📚 Patches folder

`/_lumora_perf_patches/` exists for HISTORICAL patches that the previous
session was unable to push directly (it had a session-scope JWT that
didn't include lumora). Those patches have been applied to main as of
2026-05-09. Don't re-apply them.

You can use that folder as a reference for what each feature does
(every patch has a `*-README.md` next to it).

## ❌ Don't promise the user

- "I can verify with Playwright" — sandbox blocks the deployed URL
- "I have Railway access" — sandbox blocks Railway hosts even with token
- "It will deploy in seconds" — Railway redeploy is ~2 min minimum
- "Cache will refresh on next visit" — service workers + LLM prompt
  cache need explicit busting; see Top-3 rule #2
- "Going to a branch = deploys" — only `main` deploys

## 🤝 What to ask the user (only ask once these things)

- **Railway logs** if WhatsApp bridge or any service crashes — they
  paste; you diagnose
- **Screenshots** of any visible bug — they screenshot; you read
- **Stripe key** if user wants real card checkout
- **A new Claude session pointed at lumora** if your current session's
  JWT scope doesn't include `aalmir-erp/lumora` — check first:
  ```bash
  TOKEN=$(cat /home/claude/.claude/remote/.session_ingress_token)
  echo "$TOKEN" | sed 's/^sk-ant-si-//' | cut -d. -f2 | base64 -d 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('sources'))"
  ```

## 🎯 If you're starting fresh (new session)

Run these in order:
```bash
# 1. Confirm scope
git remote -v
# Should show aalmir-erp/lumora

# 2. Check current state
git log origin/main --oneline -5
grep APP_VERSION app/config.py

# 3. Read the recent commits for context (especially last 30 days)
git log origin/main --oneline -30

# 4. NOW you can work
```

---

_Last updated 2026-05-09. Update this file with NEW lessons whenever
you make a non-trivial mistake. The goal is each generation of Claude
sessions makes fewer mistakes than the last._
