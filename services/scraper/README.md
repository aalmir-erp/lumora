# Lumora Scraper Agent

A switchable AI scraping/automation agent. Pick the **AI backend**
(Gemini 2.5 Pro / Flash / Computer Use, or Claude Sonnet 4.6 Computer Use)
and the **runtime** (Railway-hosted Chromium, your local PC, or
hybrid auto-fallback). Browser **and** desktop (Excel/any app) tasks
are supported through the same UI.

```
            ┌─────────────────────┐
            │  Web UI (Railway)   │  pick backend + runtime + goal
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │  FastAPI server     │
            │  - /api/tasks       │
            │  - /api/.../events  │  SSE
            │  - /ws/agent        │  WebSocket
            └─────┬──────────┬────┘
                  │          │
       Railway Chromium   Local Agent (your PC)
       headless,          your Chrome profile + desktop
       datacenter IP      (cookies, your IP, real keyboard)
```

## When does Railway run Chrome vs your PC?

| Runtime | Chrome runs on | IP seen by site | Cookies/session | When to use |
|---|---|---|---|---|
| `railway` | Railway container | Railway datacenter | Manual cookie injection | Public scraping, low anti-bot |
| `local` | Your PC | Your home/office IP | Your real Chrome profile | Logged-in sites, WhatsApp |
| `hybrid` (default) | Tries Railway, falls back to local on block | Both | Both | Best general choice |

**Hosts in `FORCE_LOCAL_HOSTS` always go local from the start.** Default list
includes `web.whatsapp.com` because WhatsApp Web is QR-bound to your phone —
it can never run on Railway.

**Desktop mode is always local** (Excel, any GUI app). Railway has no display.

## Deploy on Railway

The scraper is a **separate Railway service** from the main `lumora` service
(it uses a Playwright base image, ~1.5 GB).

### One-time setup (5 min on Railway dashboard)

1. **Project → New Service → Deploy from GitHub repo → `aalmir-erp/lumora`**
2. **Settings → Source**:
    - Watch path: `services/scraper`
    - Branch: `main` (or `claude/gemini-web-scraping-B7GWh` for testing)
3. **Settings → Build**: leave Dockerfile detection on. It picks up
   `services/scraper/Dockerfile` automatically (the path is set in
   `services/scraper/railway.toml`).
4. **Variables** — add these:
   ```
   GOOGLE_API_KEY        (https://aistudio.google.com/apikey)
   ANTHROPIC_API_KEY     (https://console.anthropic.com/settings/keys)
   LOCAL_AGENT_TOKEN     # generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
   DEFAULT_BACKEND=gemini-pro
   DEFAULT_RUNTIME=hybrid
   FORCE_LOCAL_HOSTS=web.whatsapp.com,*.whatsapp.com
   STATUS_WEBHOOK_URL=   # optional — POSTed on every task done/fail
   ```
5. **Settings → Networking → Generate Domain** — Railway gives you a public URL.
6. Push commits — Railway auto-deploys.

### Quick test (no API keys needed)
After deploy, visit `https://<your-domain>/healthz` → should return
`{"ok": true, "agents": []}`.

## Run the local agent on your PC

The local agent connects out to your Railway server and waits for tasks.
You only need it for `local` runtime / `desktop` mode / WhatsApp tasks.

### Install (one-time)

```bash
git clone https://github.com/aalmir-erp/lumora.git
cd lumora/services/scraper
pip install -r local_agent/requirements.txt
playwright install chrome
```

### Configure

Create `services/scraper/.env`:
```
SCRAPER_SERVER_URL=wss://<your-railway-domain>
LOCAL_AGENT_TOKEN=<same value as on Railway>
AGENT_ID=my-laptop          # optional, defaults to hostname
# AGENT_DRY_RUN=1           # uncomment for desktop dry-run mode
# CHROME_USER_DATA_DIR=...  # uncomment to override Chrome profile path
```

### Run

```bash
cd services/scraper
python -m local_agent.agent
```

You'll see `[agent] connected, waiting for tasks...`. Leave it running.
The web UI's "agents" pill will show your `AGENT_ID`.

## How desktop / Excel tasks work

When you pick **mode = desktop**, the agent uses `pyautogui` for mouse/keyboard
on your real screen. There are three failsafes (all on by default):

1. **Mouse-to-corner**: slam your mouse to a screen corner → instant abort.
2. **Ctrl+Alt+Q**: global hotkey kills the agent process.
3. **Dry-run** (`AGENT_DRY_RUN=1`): every action prints first, waits for ENTER.

For Excel data tasks the AI is encouraged to use the structured path
(`excel_read` / `excel_write` via `openpyxl`) which reads/writes `.xlsx`
files directly — much more reliable than clicking around the UI. AI clicking
is reserved for tasks that genuinely need the live UI (filtered views, pivots).

## Run a task

### Via web UI
Open `https://<domain>/`, fill the goal, pick backend + runtime + mode, click Run.
Live screenshots and event log stream in.

### Via API
```bash
curl -X POST https://<domain>/api/tasks \
  -H "content-type: application/json" \
  -d '{"goal":"Visit sale.mir.ae/demo and screenshot the homepage",
       "backend":"gemini-flash","runtime":"hybrid","mode":"browser"}'
# → {"id": "abc123...", "status": "pending"}

curl https://<domain>/api/tasks/abc123
```

### Test scenarios
```bash
SCRAPER_URL=https://<domain> python -m tests.scenarios.mir_demo smoke_demo
SCRAPER_URL=https://<domain> python -m tests.scenarios.mir_demo whatsapp_otp     # needs local agent
SCRAPER_URL=https://<domain> python -m tests.scenarios.mir_demo demo_with_otp    # needs local agent
SCRAPER_URL=https://<domain> python -m tests.scenarios.mir_demo excel_round_trip # desktop, local only
```

Screenshots save to `services/scraper/out/<scenario>/`.

## Backend cheat sheet

| Backend | Model | Best for | Cost |
|---|---|---|---|
| `gemini-pro` | gemini-2.5-pro | Complex multi-step, login flows | $$ |
| `gemini-flash` | gemini-2.5-flash | High-volume similar pages | $ |
| `gemini-cu` | gemini-2.5-computer-use | Native click/type actions | $$ |
| `claude-cu` | claude-sonnet-4-6 | Toughest UIs / fallback | $$$ |

Switch from the dropdown — no redeploy needed.

## Status webhook

If `STATUS_WEBHOOK_URL` is set, the server POSTs JSON on every task start/finish:
```json
{"event":"done","task_id":"abc123","status":"done","answer":"...","error":null}
```
Use this to ping a Claude session, Slack, or anything else.

## File map

```
services/scraper/
├── Dockerfile              # Railway build (Playwright base image)
├── railway.toml            # Railway service config
├── requirements.txt        # Server deps (lean, no pyautogui)
├── server/
│   ├── main.py             # FastAPI app
│   ├── config.py           # env vars
│   ├── tasks.py            # task store + orchestrator loop
│   ├── runtime/
│   │   ├── base.py         # BrowserRuntime ABC
│   │   ├── railway.py      # headless Playwright on Railway
│   │   ├── local.py        # WebSocket bridge to local agent
│   │   ├── hybrid.py       # auto-fallback router
│   │   └── agent_registry.py
│   ├── ai/
│   │   ├── base.py         # AIBackend ABC
│   │   ├── gemini.py       # Pro + Flash
│   │   ├── gemini_cu.py    # Computer Use preview
│   │   └── claude_cu.py    # Claude computer_20250124
│   └── web/index.html      # UI
├── local_agent/
│   ├── agent.py            # entry point — WebSocket client
│   ├── browser.py          # local Chrome via persistent profile
│   ├── desktop.py          # pyautogui + Excel + screenshots
│   ├── safety.py           # failsafes
│   └── requirements.txt    # heavier deps for the user's PC
├── tests/
│   ├── test_smoke.py       # factory/import sanity
│   └── scenarios/
│       └── mir_demo.py     # end-to-end test scenarios
└── .env.example
```

## Honest limitations

- **WhatsApp Web** must run on your local agent — it's QR-locked to your phone.
  Hybrid router enforces this automatically.
- **Anti-bot**: even with stealth flags, sophisticated targets (Cloudflare
  Turnstile, PerimeterX) will still flag a Railway datacenter IP. Use `local`
  runtime or add a residential proxy.
- **Captchas**: model can READ visible captchas but cannot reliably solve
  reCAPTCHA v3. Wire a paid solver (2Captcha, CapSolver) if you need this.
- **Desktop drift**: pyautogui clicks pixel coordinates. If the AI is
  misaligned with your screen DPI, set `AGENT_DRY_RUN=1` first and tune.
