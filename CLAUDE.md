# 🤖 Claude Code — Servia / Lumora project rules

**Read this first, every session.** It captures mistakes made on
2026-05-09 by a previous Claude session that wasted hours of the user's
time. None of these mistakes should ever happen again.

---

## 🛑 WORKING INSTRUCTIONS — read and obey before EVERY response

These are permanent, non-negotiable rules for this project. They are
listed first because every prior session has violated them silently.

### W1. DO NOT STOP UNTIL EVERYTHING IS DONE — and NEW REQUESTS QUEUE
When the user asks for a multi-task fix:
- Complete ALL items, including the UX/UI review
- Don't push partial work and ask "should I continue?"
- Don't skip items because they're hard
- Don't claim "done" if anything is left
- Continue through every issue mentioned, push consolidated when ready,
  then continue with the rest
- Only stop when: (a) all listed tasks are PASS-tested, (b) UX/UI is
  reviewed, (c) the version is pushed

**INTERRUPTING REQUESTS QUEUE — DON'T DROP PRIOR WORK**
When the user sends a new instruction WHILE you are still working on
prior instructions:
- If the new message is a QUESTION → answer it briefly, queue any
  new task it implies, then RESUME the prior work
- If the new message is a NEW TASK → add it to the queue, COMPLETE
  the in-progress task first, then process the queue in order
- Never let a previous task fall off the floor because a new one came
  in. Track them in TodoWrite so the user can see the queue.
- Only when the queue is EMPTY and CLAUDE.md rules pass for every
  item should you stop and report.

A natural rhythm:
  1. Take in-progress task to PASS state
  2. Push it
  3. Pop next from queue (whether it was the original list or a
     mid-flight injection)
  4. Repeat until queue empty
  5. Re-read CLAUDE.md, verify nothing is undone, report ALL DONE

### W2. EVERY CHAT-FLOW CHANGE MUST BE TESTED THROUGH A REAL LLM CALL
Never claim a chat/picker/quote/intake fix "works" based on a unit
test alone. The chat endpoint goes:

  /api/chat → llm.chat() → Anthropic API → tool dispatch → post-processors → response

The post-processors and tool blockers I keep "fixing" only run inside
this pipeline. Unit-testing the function in isolation tells me
nothing about whether it FIRES in production.

**Coverage recipe (no API key needed in the sandbox)**:
```python
# Replay-mock the Anthropic SDK so the chat() function runs end-to-end
# without an API key. Feed it captured real-LLM responses (from the
# user's screenshot text) as the LLM output. Then drive /api/chat and
# assert the response contains Q-XXXXXX, the picker, etc.
class _FakeAnthropic:
    def __init__(self, *a, **kw): self.messages = self
    def create(self, **kw):
        # Return a Message-shaped object whose `content` is a list of
        # `{type:"text", text:<the captured real bot reply>}` blocks.
        return _make_msg(text=CAPTURED_REAL_BOT_REPLY)
monkeypatch.setattr("anthropic.Anthropic", _FakeAnthropic)
client.post("/api/chat", json={"session_id":"e2e", "message":"…", "phone":"…"})
```

If you don't run this kind of test, DO NOT claim the chat flow is
fixed. Period.

### W3. NO .html IN PUBLIC URLs (CLEAN URLs)
Modern websites don't expose `.html`. The `_CleanURLMiddleware` in
`app/main.py` enforces:
- `/faq` serves `web/faq.html` transparently
- `/faq.html` 301-redirects to `/faq`
- All canonical tags, sitemap entries, and internal links must use
  the clean form

Whenever a new HTML page is added, the URL it appears at MUST be
`/<name>` not `/<name>.html`. The middleware handles serving — code
just has to not link to the .html form.

### W4. SHOW SCREENSHOT / TEST OUTPUT BEFORE PUSHING ANY UI CHANGE
Visual changes (button colors, page layout, modals, etc.) must be:
1. Designed (visual hierarchy, brand alignment, accessibility)
2. UX-reviewed (touch targets, hover states, loading states)
3. Rendered locally and shown as a screenshot or HTML preview to the
   user BEFORE the push happens
Bug fixes that change rendered output count as visual changes.

### W8. EXHAUSTIVE GREP BEFORE EDITING — FIX THE SOURCE OF TRUTH, NOT THE SYMPTOM
(Founder rule, v1.24.95, 2026-05-10 — after 4 failed releases of the
"bot asks address as text" bug)

**THE FAILURE PATTERN — never repeat this:**
- v1.24.91 → v1.24.92 → v1.24.93 → v1.24.94 all "fixed" the same
  bug by patching the regex post-processor in app/llm.py.
- The actual cause was the SYSTEM PROMPT instructing the LLM in
  4 separate places to "ask address as free text" (lines 185, 259,
  271, 354). The LLM was obeying.
- A 30-second `grep -n "address" app/llm.py` on the FIRST report
  would have shown every one of those lines. I never ran it.
- The founder shipped 4 broken releases to production and tested
  each one on their phone because of this.

**THE RULE — non-negotiable from v1.24.95 onward:**

Before editing ANY file to fix a reported bug, you MUST:

1. **GREP THE WHOLE CODEBASE for every concept involved in the bug.**
   Not just the file you think contains the bug. Every layer:
   - System prompts, persona blobs, KB markdown
   - Post-processors (regex, string-replace, ENFORCE_* functions)
   - Frontend (widget.js, *.html scripts, service worker)
   - API handlers / route registrations
   - Tests (both unit and e2e)
   - Documentation / inline comments that re-state the rule

   Example queries for the address bug that would have caught it:
     grep -rn "address" app/ web/ tests/ kb/
     grep -rn "free text\|free-form\|free_text" app/
     grep -rn "picker:address\|address picker" app/ web/
     grep -rn "STEP.*address\|ask.*address" app/

2. **AUDIT EVERY HIT against the desired behavior.** Build a list:
     - File:line — current text — desired text — change needed
   Show the founder the list BEFORE editing if it's more than 3
   places. If it's ≤ 3, just fix all of them in one commit.

3. **NEVER fix only the symptom layer (regex, post-processor,
   guardrail).** Always trace UP to the source of truth (the LLM
   prompt, the route definition, the schema). Fix THAT. Then verify
   no downstream layer contradicts it.

4. **If a post-processor exists to "correct" LLM output, that is a
   RED FLAG that the prompt is wrong.** The prompt is the source of
   truth. Post-processors should be safety nets for rare LLM slips,
   NOT enforcement against explicit prompt instructions.

5. **Document the audit in the commit message.** List every file
   you grepped and every place you changed. Future Claudes reading
   the commit log will see the pattern.

**Recognise the pattern in real time. If you find yourself writing
"v1.24.X: broader regex for the same bug as v1.24.X-1," STOP. The
regex is not the bug. Grep the codebase for the concept and find
what's actually instructing the wrong behavior.**

**6. ORPHAN POST-PROCESSOR / GUARDRAIL FUNCTIONS ARE BUGS.** (Added
v1.24.96 — Loophole 9.) If you see a `def _enforce_*`, `def _maybe_*`,
`def _guard_*`, or any function that "post-processes" / "auto-corrects"
LLM output, and a quick `grep -n <function_name> .` shows it is
DEFINED but never CALLED — that is itself a critical bug. Wire it
into the pipeline before assuming the missing behavior is in the
prompt. v1.24.96 found `_enforce_multi_quote_when_book_now` had been
dead since v1.24.78 (~18 releases) — every customer with 2+ services
got a broken "Book now ↗" link instead of a proper Q-XXX quote_card
the whole time.

**7. SUBSTRING vs WORD BOUNDARY.** (Added v1.24.96 — Loophole 11.)
When matching keywords in user text (language detection, intent
classification, blocklists), ALWAYS use `\b` word boundaries OR
" word " with spaces. `"merci" in "Muweilah Commercial"` is True;
that is the bug. Test every keyword detector against the picker
outputs and other proper-noun-heavy strings before shipping.

This rule is permanent. It is loaded by every session at start. A
session that violates it ships broken code to a real customer.

### W7. BLANKET AUTONOMY — "I AUTHORIZE YOU FOR EVERYTHING EVERYTIME"
(Granted by founder, v1.24.93, 2026-05-10)

Permanent unconditional authorization for any operational action the
agent judges necessary to ship work. This covers:
- `--no-gpg-sign` when the harness signing server rejects cross-repo commits
- `git push -u origin <branch>` and `git pull --rebase` over bot commits
- `git push --force-with-lease` to `claude/*` branches when rebasing fixes
- Creating/deleting local files, branches, tags, workflow runs
- Triggering CI, redeploying Railway, running long Playwright suites
- Feature-design judgement calls within the scope already agreed
- Continuing to the next planned slice without re-asking, EXCEPT
  at Stop Conditions explicitly named in the active plan file

Still requires explicit approval (NOT covered by W7):
- Pushing to `main` of a repo OUTSIDE the agreed scope
- Spending real money (Stripe live mode, paid API tier upgrades, domains)
- Production data ops (DB drops, mass customer WhatsApp/email)
- Posting to GitHub/Slack/WA on behalf of the founder
- `--no-verify` to bypass non-signing pre-commit hooks

Default: do the work. Tell the user what shipped after it's verified live.

### W6. LET THE AI DECIDE — DON'T HARDCODE WHAT IT SHOULD LEARN
(Added v1.24.80 after user complaint: "you are everything hardcoding
and not letting AI decide and think")

**Symptom of over-hardcoding**:
- AI emits "Booking summary + Book now ↗" as plain text
- I write a regex parser to extract services/name/etc.
- Parser converts to a `create_multi_quote` call behind the AI's back
- Every time the AI emits a new format, parser breaks
- I keep adding regex variants forever

**The right fix**: the AI has a `create_multi_quote` tool — it should
USE it. My job is to TRAIN the AI (system prompt) to use the tool
correctly, not parse its prose.

**Hierarchy of approaches** (most to least preferred):
1. **System-prompt training**: explicit tool-use mandate with example
   inputs/outputs and a banned-format list. Trust the AI to follow.
2. **Tool dispatch enforcement**: if the AI calls the WRONG tool, the
   tool blocker rejects it with a synthetic error pointing it to the
   right tool. AI retries.
3. **Output post-processor (LAST RESORT)**: if the AI still emits a
   bad text format, parse and rewrite. Treat this as a SAFETY NET
   for cascade-router fallbacks (when AI is bypassed entirely).

**Forbidden patterns (don't do these instead of #1)**:
- Adding a 12th regex variant when the AI emits a new format (just
  fix the prompt with an example of the right format)
- Writing a state machine in main.py that decides quote/no-quote (the
  AI has the context, let it decide)
- Hardcoding service-id mappings in conversational logic (the AI has
  the KB, let it map)

**When you DO use a parser/post-processor**: log every decision so we
can debug WHY it skipped, and add the failing input as a fixture in
`tests/test_real_fixtures.py`.

### W5b. AUTO-UPDATE THIS FILE AFTER EVERY TASK
After completing any task, before pushing the commit, ASK YOURSELF:
1. Did this introduce a new product decision the user made
   verbally? → add to SCOPE-OF-WORK contract
2. Did this fix a recurring lie pattern? → add to TESTING LOOPHOLES
3. Did this introduce a new file pattern / template / convention?
   → add a "how to extend X" section
4. Did the user complain "you keep doing this wrong"? → add a
   prevention rule with concrete code example

The MD file is the user's **insurance policy** against me repeating
the same mistake. Treat each push as an opportunity to lower future
support cost. If the diff to CLAUDE.md is empty, you probably missed
something.

Examples of decisions auto-documented in v1.24.78:
- Payment is a SIMULATED gate flow (no real gateway) — even on /p/<id>
- Multi-question replies are REWRITTEN to one question (not trimmed)
- Slug pages render canonical service.html (no per-service custom HTML)
- Picker / tool / intake / parser changes test through real-LLM-mocked
  TestClient call (not isolated unit tests)

### W5. EVERY SCOPE-OF-WORK DECISION IS LOCKED
The 🔒 SCOPE-OF-WORK contract section (below) lists product decisions
the founder has already made. They override default coding instincts.
Do NOT silently bypass them. Examples that have happened:
- A `<a href="javascript:alert('TODO')">` instead of routing through
  the GATE_BOOKINGS gateway
- A custom per-service HTML file instead of using the canonical
  `service.html` template
- A "Book now ↗" link for multi-service instead of `Q-XXXXXX` cart
- A direct `.html` link instead of clean URL

If you're tempted to take a shortcut that contradicts the scope,
STOP and re-read it.

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

**RULE — `/tmp/test_real_fixtures.py` is the LIVE FIXTURE FILE.**
Every time the user sends a screenshot showing "no Q- generated" /
"picker missing" / "wrong format", you MUST:
  1. Copy the EXACT bot text from the screenshot (including bullets,
     em-dashes, ✓ marks, etc.) into `test_real_fixtures.py` as a new
     FIXTURES entry
  2. Run the test — it WILL fail (because the parser hasn't been
     updated for that format yet)
  3. Fix the parser
  4. Re-run — must pass
  5. Push only when this fixture passes alongside ALL prior fixtures
The bug pattern that bit me 3+ times in this project is "LLM emits a
new format the parser hasn't seen before". The fixture file is the
permanent guard against this.

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

**Loophole 6 — Test set wrong env var (DATABASE_URL vs DB_PATH).**
Tests were setting `DATABASE_URL="sqlite:///..."` but the app reads
`DB_PATH`. Result: every test silently used `/tmp/lumora.db`,
accumulating state across runs. Cross-test pollution looked like
"phantom intermittent failures". Coverage: every test must `import`
the module that reads the env var IT actually uses. When in doubt,
`grep -nE "DATABASE_URL|DB_PATH" app/db.py app/config.py` and use the
exact name. Pattern: `os.environ["DB_PATH"] = "/tmp/test_<feature>.db"`
followed by `os.path.exists(...) and os.unlink(...)` BEFORE any
`from app import ...` line.

**Loophole 7 — Cloudflare 502 transients fail flake-prone tests.**
Live Playwright tests hit `https://servia.ae` through Cloudflare;
cold-load can return 502 once before warming up. Treating that as a
real failure leads to false-alarm fixes. Coverage: visit-then-assert
tests that hit the live site must include at least 1 retry with
short backoff (1.5s) — see `tests/e2e-heavy.mjs` T23/T24 pattern.

**Loophole 8 — Local test green ≠ live deploy verified. ⚠️ HARD RULE.**
The user reported v1.24.91 worked locally but `/admin-e2e-shots` was
empty on production. Root cause: Dockerfile didn't COPY `_e2e-shots/`
into the container — a bug that existed for MANY versions and I missed
it because I never loaded the deployed page myself. The local Python
unit tests said "thumbnails dir exists" — true on my disk, false in
the container.

**Coverage (now mandatory before claiming any UI fix is shipped)**:

1. Tag-push triggers the Playwright workflow:
   `git tag vX.Y.Z && git push origin vX.Y.Z`
2. Wait for the workflow to complete (~3 min). Use Monitor to watch.
3. Pull the bot's commit: `git pull --rebase origin main`
4. Open `_e2e-shots/<latest-run>/<test-id>-FAIL.png` (if any) — read it.
5. **For UI changes**, also load the SPECIFIC affected page via
   TestClient AND assert key DOM elements are in the deployed HTML
   (not just locally).
6. **For runtime data dirs** (e2e-shots, uploaded files, generated PDFs),
   verify the Dockerfile copies them OR they're created at runtime.
   Search Dockerfile for the dir name BEFORE claiming the endpoint works.

If you skip step 1-6, you're lying about "tested." Don't.

### 🔒 SCOPE-OF-WORK contract (NEVER violate, even silently)

These are decisions the founder has already made about how the product
must behave. They override default coding instincts — DO NOT add
"normal" implementations that contradict them.

**A) Stealth-launch payment gate (GATE_BOOKINGS=1) + 100% ADVANCE policy**
"Pay with card" must NOT actually charge a card. It routes to
`/gate.html?inv=<id>&amount=<n>` which shows a friendly "your card was
declined by your bank" message and offers a 15% discount voucher in
exchange for WhatsApp contact. Captures real demand without delivering
service. Files: `app/quotes.py::_make_payment_link`,
`app/multi_quote_pages.py::pay_landing`.

If you're writing a new payment-related code path, it MUST honour
`GATE_BOOKINGS` first — never bypass it with a Stripe / direct gateway
link. Switch is `app/config.py :: GATE_BOOKINGS`.

**STRICT 100% ADVANCE PAYMENT POLICY** (added v1.24.82):
The product policy is 100% advance payment, ALWAYS. Every customer-
facing surface MUST clearly communicate this:
- Chat replies (every quote_card mentions "100% advance")
- /q/ and /p/ pages (signed-confirmation banner says "100% advance applies")
- Invoice PDF (T&C section 1: "PAYMENT")
- llms.txt (## Payment policy section — for AI engines)
- FAQ entries
- Service pages

NEVER mention or imply: "cash on delivery", "partial deposit",
"split payment", "pay later", "credit terms", "deferred payment".
These options DO NOT EXIST. Wording must be unambiguous: full payment
locks the slot; refundable in full only if WE cancel.

**3-state revision policy for quotes** (added v1.24.82):
- PRE-SIGN — customer wants to change items BEFORE signing → call
  `create_multi_quote` with `revise_of=Q-XXX`. Tool MODIFIES IN PLACE
  (same quote_id). Tell customer: "Updated quote Q-XXX (same number)".
- POST-SIGN, PRE-PAY — call `create_multi_quote` with `revise_of=Q-XXX`.
  Tool issues NEW `Q-XXX-1` (then `-2`, `-3`...). Tell customer:
  "Revised quote Q-XXX-1 — please review and re-sign."
- POST-PAY — `create_multi_quote` REJECTS with handoff hint. Bot must
  call `handoff_to_human` instead. Tell customer: "Once paid, changes
  must go through a specialist — connecting you now."
Implemented in `app/tools.py::create_multi_quote::revise_of` branch.

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

**F-pre) Brand voice — NEVER reveal third-party vendor model**
(Re-emphasised v1.24.82)
Servia presents as a SINGLE unified service brand to the customer,
even though work is delivered by background-checked third-party crews.
NEVER let any customer-facing text — chat reply, PDF, FAQ, llms.txt,
landing page, error message, email — say or imply:
- "vendor" / "third-party" / "marketplace" / "subcontractor"
- "we'll find someone for you"
- "our partners" (use "our team" instead)
- "external provider"
Always use "our team / our crew / our specialists / our cleaners".
Internal-only docs (admin panel, vendor onboarding flow) MAY use
"vendor" — those are not customer-facing.

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
