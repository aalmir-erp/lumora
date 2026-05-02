# Lumora — Railway deploy guide

This folder is a **completely standalone application**. It has no dependency on
the parent `aalmir_git_new` repo or on `sales.mir.ae`. Deploy it as its own
Railway project.

## Option 1 — Deploy directly from the parent repo (no extraction needed)

1. **Railway → New Project → Deploy from GitHub repo** → pick `aalmir-erp/aalmir_git_new`
2. **In the new service's settings → Root Directory** = `urbanservices_chatbot`
3. **Settings → Watch Paths** = `urbanservices_chatbot/**` (so other repo changes don't trigger redeploys)
4. **Variables** (Service → Variables):
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ADMIN_TOKEN=<long random>
   BRAND_NAME=Lumora
   CLAUDE_MODEL=claude-opus-4-7
   ALLOWED_ORIGINS=https://lumora.app,https://www.lumora.app
   STRIPE_SECRET_KEY=                # optional, blank for stub payments
   WA_BRIDGE_URL=                    # set after deploying the bridge service
   WA_BRIDGE_TOKEN=                  # same secret as the bridge
   ```
5. **Storage → Add Volume** → mount path `/data` (1 GiB is plenty)
6. Deploy. Health check is `/api/health`.

## Option 2 — Extract to its own GitHub repo

Cleaner if you want this to live as `aalmir-erp/lumora` (or any name):

```bash
# Fresh repo, no git history
cp -r urbanservices_chatbot ~/lumora
cd ~/lumora
rm -rf .pytest_cache __pycache__
git init -b main
git add .
git commit -m "Initial commit — Lumora v0.2"
gh repo create aalmir-erp/lumora --private --source=. --push   # or via web UI
```

Then **Railway → New Project → Deploy from GitHub** → pick `aalmir-erp/lumora`.
No Root Directory tweak needed — the Dockerfile sits at the repo root.

## Option 3 — Deploy directly via Railway CLI (no GitHub)

```bash
cd urbanservices_chatbot
railway login
railway init        # creates a new project
railway up          # uploads + builds + deploys
railway domain      # generates a public URL
railway variables set ANTHROPIC_API_KEY=sk-ant-... ADMIN_TOKEN=... BRAND_NAME=Lumora
railway volume create --mount /data
```

## Add a custom domain

In the service → Settings → Networking → "Add custom domain" → e.g. `lumora.app`.
Railway gives you the CNAME. Point your DNS at it.

Update `ALLOWED_ORIGINS` env var to include the new domain, then redeploy.

## Add the WhatsApp QR bridge as a second service

The bridge runs separately and pairs your personal WhatsApp via QR scan.

1. **Railway → same project → New Service → Deploy from same repo (or a separate repo for the bridge)**
2. **Root Directory** = `urbanservices_chatbot/whatsapp_bridge` (or the folder root if extracted)
3. **Volume** mount at `/app/.wwebjs_auth` (so QR session survives restarts)
4. **Variables**:
   ```
   BOT_WEBHOOK=https://<lumora-service>.up.railway.app/api/wa/webhook
   BRIDGE_TOKEN=<same random secret as WA_BRIDGE_TOKEN on the bot>
   PORT=3001
   ```
5. After deploy, hit `https://<bridge>.up.railway.app/qr` (use the bearer token
   in the `Authorization` header) and scan with your phone:
   WhatsApp → Settings → Linked devices → Link a device.
6. Back on the bot service, fill in `WA_BRIDGE_URL` + `WA_BRIDGE_TOKEN` and redeploy.

## After deploy — verify

```bash
curl https://<your-lumora>.up.railway.app/api/health
# {"ok":true,"service":"Lumora","mode":"llm","model":"claude-opus-4-7", ...}
```

Open the public URL in a browser → modern landing page.
Open `/admin.html` → paste your `ADMIN_TOKEN` → dashboard.
