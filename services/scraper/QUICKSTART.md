# Scraper — One-screen quick start

You only need 3 things: a Railway service for the scraper, API keys, and
(optionally) the local agent running on your PC.

## 1. Create the Railway service (one-time, ~3 min on dashboard)

1. Railway dashboard → your `lumora` project → **+ New** → **GitHub Repo** → `aalmir-erp/lumora`.
2. Pick `Empty Service` if prompted, then **Settings**:
   - **Source → Watch path**: `services/scraper`
   - **Source → Branch**: `main` (after merge) or `claude/gemini-web-scraping-B7GWh` for testing
   - **Build → Dockerfile path**: `services/scraper/Dockerfile`
3. **Variables tab** — paste:

   | Key | Value |
   |---|---|
   | `GOOGLE_API_KEY` | get free at https://aistudio.google.com/apikey |
   | `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys (skip if not using Claude) |
   | `LOCAL_AGENT_TOKEN` | run on your PC: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
   | `DEFAULT_BACKEND` | `gemini-pro` |
   | `DEFAULT_RUNTIME` | `hybrid` |
   | `FORCE_LOCAL_HOSTS` | `web.whatsapp.com,*.whatsapp.com` |

4. **Settings → Networking → Generate Domain** — note the URL.
5. Wait for the build (~3 min). Hit `https://<domain>/healthz` — should return `{"ok":true,"agents":[]}`.

## 2. Start the local agent on your PC

### Windows (one-click)
```cmd
cd lumora\services\scraper\local_agent
install_windows.bat
```
The installer asks for `SCRAPER_SERVER_URL`, generates a token, writes
`.env`, and installs Playwright. Then double-click `run_windows.bat`
whenever you want the agent online.

### macOS / Linux / manual
```bash
cd lumora/services/scraper
pip install -r local_agent/requirements.txt
playwright install chrome
```

Create `services/scraper/.env` on your PC:
```
SCRAPER_SERVER_URL=wss://<your-railway-domain>
LOCAL_AGENT_TOKEN=<same value you set on Railway>
AGENT_ID=my-laptop
```

Run:
```bash
python -m local_agent.agent
```

Leave it running. The web UI's "agents" pill will show your laptop.

## 3. Test it

**Without any keys**: pick backend = `demo`, runtime = `railway`, hit Run with
goal `Visit https://example.com and read the homepage`. Lets you verify the
whole stack works before pasting paid API keys.

**With keys**: pick `gemini-pro` / `gemini-flash` / `gemini-cu` / `claude-cu`.

**Diagnose anything missing**: GET `https://<domain>/api/diag` — tells you
exactly which env vars and agents are wired up.

Open `https://<domain>/`, type a goal, pick backend/runtime/mode, hit Run.

Or via API:
```bash
curl -X POST https://<domain>/api/tasks \
  -H "content-type: application/json" \
  -d '{"goal":"Visit sale.mir.ae/demo and screenshot it","backend":"gemini-flash","runtime":"hybrid"}'
```

## Test the prepared scenarios

```bash
SCRAPER_URL=https://<domain> python -m tests.scenarios.mir_demo smoke_demo
SCRAPER_URL=https://<domain> python -m tests.scenarios.mir_demo whatsapp_otp
SCRAPER_URL=https://<domain> python -m tests.scenarios.mir_demo demo_with_otp
SCRAPER_URL=https://<domain> python -m tests.scenarios.mir_demo excel_round_trip
```

Screenshots are saved to `out/<scenario>/`.

## When something breaks

- **`agents: 0` in UI**: local agent not connected. Check the agent terminal for
  errors, verify `SCRAPER_SERVER_URL` uses `wss://` and `LOCAL_AGENT_TOKEN` matches.
- **WhatsApp says "NOT_LOGGED_IN"**: open Chrome on your PC, scan QR on
  web.whatsapp.com once. Local agent reuses your profile, so the session sticks.
- **Railway runs slow / blocks**: it's the datacenter IP. Switch runtime
  dropdown to `local`.
- **Desktop tasks misclick**: set `AGENT_DRY_RUN=1` in your local `.env`,
  re-run, confirm each action with ENTER.
- **Kill switch**: slam mouse to corner OR press `Ctrl+Alt+Q`.
