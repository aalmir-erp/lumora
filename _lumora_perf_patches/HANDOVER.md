# 🤝 Servia / Lumora — Handover note for next Claude session

This document is the single source of truth for picking up Servia work
in a new Claude Code session that has access to `aalmir-erp/lumora`.

The previous session (this one) only had access to
`aalmir-erp/aalmir_git_new` so it staged everything as patches in the
folder you're reading this from. **Your job (new session)** is to apply
those patches to the actual `lumora` repo, push, verify, and continue.

---

## ⚙️ Capabilities you have (verified)

The Claude Code sandbox you're running in has all of these pre-installed:

- **Playwright 1.56** + **Chromium 141** at `/opt/pw-browsers/chromium-1194` —
  browse, screenshot, automate any web flow
- **Railway CLI** (`@railway/cli@4.44`) — manage Railway services, env
  vars, logs, deploys (needs `RAILWAY_TOKEN` env, see "Railway access")
- **Node 22**, **Python 3.11**, **fpdf2** for PDF
- Network: outbound HTTPS to most hosts (some restrictions; if a host
  errors with 403 "host_not_allowed", use the `local_proxy` git endpoint
  for repo work)

## ✅ Default operating mode

**Do NOT ask the user about decisions already made in this doc.** The
user is on mobile and explicitly wants you to:

1. Run autonomously
2. Take screenshots (Playwright) of every change you deploy
3. Iterate: if a screenshot shows a bug, fix and re-screenshot before
   reporting
4. Only show the FINAL working screenshots to the user
5. Only ask the user when a decision genuinely requires their input
   (e.g. "what should the Stripe API key be?" — info you can't get
   anywhere else)

## 📍 Where things live

| Repo | Purpose | Branch |
|------|---------|--------|
| `aalmir-erp/lumora` | The deployed Servia website + backend (Railway → servia.ae) | `main` |
| `aalmir-erp/aalmir_git_new` | Frappe ERP customizations + (since this session) staging area for patches that couldn't be pushed to lumora | `claude/plan-urbanservices-chatbot-kMU3s` |

The folder `_lumora_perf_patches/` in `aalmir_git_new` contains 11
patches each with a `*.patch` (apply with `git apply`) and a
`*-README.md` (explains what's in it + test plan + caveats).

## 📂 Patches in apply-order

Apply in this exact order. Patch 06 contains main.py changes from 04
and 05 too, so use `--include` flags as shown.

```bash
cd <local lumora clone>

git apply _lumora_perf_patches/01-defer-health-and-logo-dims.patch
git apply _lumora_perf_patches/02-scrub-admin-number.patch
git apply _lumora_perf_patches/03-kb-redact-admin-number.patch
git apply --include='app/live_visitors.py' _lumora_perf_patches/04-traffic-source-parsing.patch
git apply --include='app/admin_live.py' --include='web/admin-live*' _lumora_perf_patches/05-admin-live-pwa.patch
git apply _lumora_perf_patches/06-admin-ai-arena-wins.patch
git apply _lumora_perf_patches/07-quote-cart-and-admin-bot.patch
git apply _lumora_perf_patches/08-quote-complete-experience.patch
git apply _lumora_perf_patches/09-chat-widget-controls.patch
git apply _lumora_perf_patches/10-pdf-history-gsc.patch
git apply _lumora_perf_patches/11-trail-tools-quotes-bridge.patch

git add -A
git commit -m "feat: 11-patch batch — quotes/photos/PDF/history/admin-PWA/perf/security"
git push origin main
```

What each patch contains is in the corresponding `*-README.md` in the
same folder. Read those if needed.

## ⚙️ After deploy

1. Wait ~2 min for Railway to redeploy.
2. **Set Railway env var** `ADMIN_WA_NUMBER=971564020087` (or whatever
   number admin WhatsApp alerts should go to — the patches removed the
   hardcoded fallback for security).
3. **Optional**: set `STRIPE_SECRET_KEY` for real card checkout. Without
   it, "Pay with card" button is disabled with a hint, customers see
   the WhatsApp manual fallback only.
4. **Optional**: `CLAUDE_MODEL` env var. Patch 06 makes Admin AI Arena
   the source of truth for chat model selection. If set anywhere, just
   delete it.
5. **In admin panel** (`https://servia.ae/admin.html`):
   - Brand → **clear the Phone field** if it contains the personal
     number 971564020087 (it may have been saved there causing the bot
     to leak it). Patch 03 redacts it defensively but clearing the DB
     field is the real fix.
   - AI Arena → confirm Gemini key is saved + Customer dropdown is set
     to `google/gemini-2.5-flash` (FREE tier).

## 🚧 What's NOT done — needs YOUR session's attention

These were genuinely blocked on inputs from the user and/or external
review queues:

### 1. WhatsApp bridge container is in 503 state
The user's `/qr` page returns: `WhatsApp not paired yet — open /qr`.
Bridge container is up but Chromium/Puppeteer hasn't produced a QR.
Likely root cause: `wwebjs_auth` volume not mounted on Railway, so
session resets every redeploy.

**Action**: Pull the `whatsapp_bridge` Railway service logs. Look for
Puppeteer errors. Confirm volume mount at `/app/.wwebjs_auth`. If
missing, ask the user to add it via Railway dashboard → Service →
Settings → Volumes.

### 2. Watch faces not visible in Galaxy Watch picker
Plan A (Watch Face Push API) was definitively shown not to work on
Samsung Galaxy Watch L310 (Wear OS 6) — Samsung doesn't ship the
runtime. Three options remain, none quick:

- **Galaxy Store internal testing** with Watch Faces category permission.
  User has been gated by Samsung's Watch Faces category permission
  requirement. They emailed `seller@samsungapps.com`. Wait for approval.
- **Play Console internal testing**. Account is in identity-verification
  hold (1-7 days). Wait.
- **Watch Face Push API on a different Wear OS device** (Pixel Watch).

For now: this is a known dead-end on the L310. Don't keep iterating on
sideload approaches.

### 3. Existing CI builds you can use right now
- Phone TWA AAB: `https://github.com/aalmir-erp/lumora/actions` →
  most recent successful run → artifact `servia-android-twa` →
  `servia-twa-v1.24.NN.aab`
- Wear face APKs: same actions page → `servia-faces-standalone` artifact
- `aalmir-erp/aalmir_git_new` actions for the Plan A watch face pusher
  build (proven not to work on Samsung).

## 🧠 Architecture decisions made this session

| Decision | Reasoning |
|---|---|
| Multi-service quote cart (`Q-XXXXXX`) NOT one booking per service | One total + one signing link is much better UX |
| Customer signing page is phone-gated | Customer enters phone → HMAC token → can view + sign |
| Photos stored as base64 inside SQLite | Tiny scale (~12 MB cap per photo after client-side compression). Move to S3 when scale demands |
| PDF generated via fpdf2 (pure Python) | No system deps, ~500 KB install. Falls back to HTML print on missing lib |
| Web Push for admin alerts (not custom Wear OS APK) | Wear OS auto-mirrors phone push notifications. Same path WhatsApp uses. Removes the need for the Watch Face Push API path that died on L310 |
| Admin AI Arena dropdown is the SINGLE source of truth for chat model | Stops the user juggling Railway env vars |
| Hardcoded admin number `971564020087` REMOVED from source | Set it on Railway env `ADMIN_WA_NUMBER` instead |
| Customer history matches by last 9 phone digits | UAE format-tolerant: +971..., 971..., 0... all match |

## 🚫 Don't change

- `app/data/pricing.json` was bumped 40% in patch 07. If user wants to
  re-bump or set per-service, just edit pricing.json — admin override
  via DB is supported but file is the canonical default
- Patches 02 + 03 — leave the empty-string fallbacks. Setting the env
  var is the correct path; never hardcode the number again
- `multi_quotes` table schema — additive columns only. Existing data
  must be preserved through any future migration
- Chat widget sessionStorage usage was removed in patch 09 — don't add
  it back; localStorage everywhere is correct

## 🔑 Important files for context

| File | What |
|---|---|
| `app/main.py` | FastAPI entrypoint, all router includes |
| `app/llm.py` | LLM persona prompts (customer + admin) |
| `app/tools.py` | Bot tool schemas + dispatch table |
| `app/multi_quote_pages.py` | The new quote/invoice/PDF system (patch 07/08/10) |
| `app/me_history.py` | Customer history endpoint (patch 10) |
| `app/admin_live.py` | Admin Live PWA backend (patch 05/11) |
| `app/admin_alerts.py` | WhatsApp bridge alerts + Web Push fanout |
| `app/live_visitors.py` | Visitor tracking + click-trail (patch 04/11) |
| `web/admin-live.html`, `.js`, `.webmanifest`, `admin-live-sw.js` | Admin Live PWA (patch 05/11) |
| `web/widget.js`, `widget.css` | Customer chat widget (patch 09/10) |

## 🧪 After deploy — test plan

After applying the 11 patches and pushing to lumora main:

1. Wait Railway redeploy (~2 min).
2. Open https://servia.ae in a fresh incognito tab. Chat: ask for
   "deep clean + pest control + sofa cleaning for tomorrow morning".
3. Bot should reply with an itemised cart `Q-XXXXXX` + 3 links (sign /
   pay / WhatsApp).
4. Tap signing link → enter phone → see the cart → approve a few lines,
   reject one, add comments → sign → submit.
5. Open `/i/Q-XXXXXX.pdf` → should download a clean PDF invoice.
6. Open `/admin-live.html` → enter ADMIN_TOKEN → check Visitors tab
   shows live entries with traffic source chips, Chats tab shows
   recent sessions, Quotes tab shows the new quote.
7. Tap the quote → status update to "dispatched" → customer's `/q/...`
   page shows the new status within 4s.
8. In the chat widget, tap "📜 History" tab → enter the same phone →
   see the past quote/booking/chat.
9. Run https://pagespeed.web.dev/?url=https%3A%2F%2Fservia.ae —
   compare against the baseline (61 mobile, 73 desktop). Should now be
   80+ mobile, 90+ desktop after CF Email Obfuscation toggle + perf
   patches.

## 📸 Auto-verify with screenshots (REQUIRED)

A ready-made verifier lives at `_lumora_perf_patches/verify.js`.
After every deploy, run it:

```bash
cd <local lumora clone>
node _lumora_perf_patches/verify.js \
     --base https://servia.ae \
     --token $SERVIA_ADMIN_TOKEN  # optional, enables admin-live tests
```

It does:

1. Visits 6 critical pages on mobile (390×844) + desktop (1366×900)
2. Opens chat widget, sends a test message, verifies bot replies
3. Tests history tab (with `--phone <number>`)
4. Tests `/q/{id}` signing flow (with `--quote Q-XXX --phone NNN`)
5. Tests `/i/{id}.pdf` returns valid PDF
6. Logs into admin-live PWA (with `--token`)
7. Measures FCP / LCP / CLS

Output:
- `_verify/{timestamp}/mobile-*.png` and `desktop-*.png` screenshots
- `_verify/{timestamp}/summary.json` with pass/fail per check
- Exits 1 if anything failed

**After every patch deploy:** run verify.js, look at the screenshots,
fix any visual or functional regression you spot, commit the fix,
re-deploy, re-run verify.js. Only when the run is fully green do you
share the final screenshots back to the user.

## 🚂 Railway access

To manage Railway env vars / logs / deploys without the user touching
anything, you need `RAILWAY_TOKEN`:

1. **Try this first** — the user's previous session may have stored it:
   ```bash
   echo $RAILWAY_TOKEN
   railway whoami 2>&1
   ```
   If `whoami` returns a username, you're already authed; skip step 2.

2. **If not authed**, you have to ask the user — but only ONCE — to
   create a project token at https://railway.app/account/tokens →
   "Create Token" → copy → paste into the chat. Save it as a permanent
   project file (do NOT commit it):
   ```bash
   mkdir -p ~/.railway
   echo "TOKEN_VALUE_HERE" > ~/.railway/token
   chmod 600 ~/.railway/token
   echo 'export RAILWAY_TOKEN="$(cat ~/.railway/token)"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. Once authed, you have full access:
   ```bash
   railway variables                            # list env
   railway variables --set ADMIN_WA_NUMBER=971564020087
   railway logs --service whatsapp_bridge       # diagnose bridge issue
   railway redeploy                             # force redeploy
   ```

## 🤖 Continuation work this new session can take on autonomously

If you finish the patch apply + verify cleanly, here's the next backlog
sorted by impact:

1. WhatsApp bridge container fix (read Railway logs, propose volume mount)
2. Vendor cost catalog seed (currently only 100 vehicle-recovery vendors)
3. Email/SMS sending of quote/invoice link (currently bot just replies in chat)
4. Live visitor abandoned-cart detection using the new click-trail
5. Push-vs-poll: switch admin-live PWA from 4-sec poll to SSE for sub-second live UX
6. Photo gallery on `/q/{id}` — currently shows thumbnails but no gallery view

---

Generated by previous Claude session that had `aalmir-erp/aalmir_git_new`
auth only. Last commit before handover: see git log of this branch.
