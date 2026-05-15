# WhatsApp bridge — deploy as a separate Railway service (permanent sign-out fix)

## The problem in one line

Servia's WhatsApp bridge keeps signing out. The sales.mir.ae bridge
never does. The only architectural difference is that sales.mir.ae's
bridge runs in **its own Railway service** with dedicated memory; Servia's
shares ~512 MB with FastAPI + Chromium + the inspector bot + image
generation + APScheduler crons. When memory spikes, Chromium gets
OOM-killed → WA Web session in browser memory dies → restore from
`/data/.wwebjs_auth` sometimes fails because the session file was
mid-write during the kill → bridge stays signed out until manual re-pair.

All the in-container mitigations (LocalAuth, graceful SIGTERM, exponential
reconnect, 30s heartbeat, Chromium memory caps) reduce frequency but don't
eliminate the issue.

## The permanent fix: separate Railway service

Same git repo, same code, **two Railway services**. The bridge runs by
itself in service B with its own memory.

```
┌───────── Railway project: lumora-production ─────────┐
│                                                       │
│  Service A: servia (FastAPI + everything else)        │
│    PROCFILE: web: ./start.sh                          │
│    Container: 1 GB RAM                                │
│    Env: WA_BRIDGE_URL = http://wa-bridge.railway.internal:3001 │
│                                                       │
│  Service B: wa-bridge (Node bridge ONLY)              │
│    PROCFILE: web: cd whatsapp_bridge && node index.js │
│    Container: 1 GB RAM                                │
│    Volume mount: /data → persistent for session state │
│    Env: BRIDGE_TOKEN = (auto-set by start.sh of A)    │
│                                                       │
└───────────────────────────────────────────────────────┘
```

## Setup steps (one-time, ~10 min)

### 1. Add a new service in Railway

1. Open your Railway project → tap **+ New** → **GitHub Repo**
2. Pick the same repo (`aalmir-erp/lumora`)
3. Name the new service `wa-bridge`
4. In the service's **Settings** tab:
   - **Root directory**: leave blank (whole repo)
   - **Custom start command**: `cd whatsapp_bridge && npm install --omit=dev && node --max-old-space-size=512 index.js`
   - **Watch paths**: `whatsapp_bridge/**`  (so deploys only retrigger when the bridge code changes)

### 2. Mount a persistent volume on the new service

Railway → wa-bridge service → **Settings** → **Volumes**

- Mount point: `/data`
- Size: 1 GB (plenty for session files)

This stores `.wwebjs_auth/` so the QR doesn't have to be re-scanned on every deploy.

### 3. Set env vars on wa-bridge (do NOT put these in Railway — admin UI per W0 rule)

Actually you don't need any Railway env vars. The new service inherits the
`BRIDGE_TOKEN` from a shared volume / network. If absolutely needed:

- `BRIDGE_TOKEN`: a long random string (32+ chars). Generate locally,
  copy into BOTH services' env. Used to authenticate Servia → bridge calls.
- `BOT_WEBHOOK`: `https://lumora-production-4071.up.railway.app/api/wa/webhook`
  (Servia's public URL — the bridge POSTs inbound WhatsApp messages here)

### 4. Point Servia at the new bridge

In Servia's admin → 📲 WhatsApp tab → **Bridge URL** field:

```
http://wa-bridge.railway.internal:3001
```

(Railway-internal hostname — no public exposure, no SSL handshake overhead.)

Save. The bridge starts auto-loading the existing paired session from
its own `/data` volume.

### 5. Remove the bridge launch from start.sh of service A

Edit `/start.sh`:

```diff
- (
-   cd /app/whatsapp_bridge
-   while true; do
-     echo "[start] launching whatsapp_bridge"
-     PORT=3001 node --max-old-space-size=256 index.js \
-       || echo "[start] bridge exited; restarting in 5s..."
-     sleep 5
-   done
- ) &
```

Commit + push. Service A now ONLY runs FastAPI, freeing 200-500 MB.

## Verification

After both services are deployed:

- Service A logs: `[uvicorn] running on http://0.0.0.0:8000`  (NO `[wa-bridge]` lines anymore)
- Service B logs: `[wa-bridge] listening on :3001` then `[wa-bridge] ready: paired=971XXXXXXXXX`
- Servia admin → 📲 WhatsApp → **🔍 Diagnose** → all 7 checks green
- Send a test message → arrives instantly, no cooldown errors
- Wait a few hours → bridge stays connected (the proof point)

## Cost

Railway charges per service. Adding one more service is ~$5/month at the
free hobby plan, or whatever the project's current plan covers. The
tradeoff against perpetual sign-outs is overwhelmingly worth it.

## Why I keep saying "shared container is the issue"

Run this on your phone any time:
```
https://servia.ae/admin#auto-tests   →   Run FULL scan
```

While the scan runs (Inspector bot launches headless Chromium for 130+
pages), refresh the WhatsApp tab. You'll see "waiting for scan" come back
within 30 seconds — the second Chromium instance pushed the first one
into OOM territory. With a separate service, this can't happen.
