# 🤖 Claude Code — Servia / Lumora project rules

**Read this first, every session.** It captures mistakes made on
2026-05-09 by a previous Claude session that wasted hours of the user's
time. None of these mistakes should ever happen again.

---

## 🚨 Top-3 rules — break any of these and you owe the user an apology

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
