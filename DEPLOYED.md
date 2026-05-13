# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"jRQkN-L4QUmFMmNH6WHkDg"}`

## Build logs
```
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[internal] load build context
[ 2/12] WORKDIR /app
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/12] COPY requirements.txt ./
[ 5/12] RUN pip install -r requirements.txt
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/12] COPY app ./app
[ 8/12] COPY app ./app
[ 9/12] COPY web ./web
[ 9/12] COPY web ./web
[10/12] COPY _e2e-shots ./_e2e-shots
[10/12] COPY _e2e-shots ./_e2e-shots
[11/12] COPY start.sh /app/start.sh
[11/12] COPY start.sh /app/start.sh
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:0cb47531101a1d5ec8e1d2646879c0008c0f94470ee6da18879fd4399038465b
containerimage.digest: sha256:7121f76a4df49a3b0e742c6d1cabe05275010ee074fc1e83776819cfb520d55f
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NzEyMWY3NmE0ZGY0OWEzYjBlNzQyYzZkMWNhYmUwNTI3NTAxMGVlMDc0ZmMxZTgzNzc2ODE5Y2ZiNTIwZDU1ZiIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QxNzo0Njo0NFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
image push
image push

[35m====================
Starting Healthcheck
====================
[0m
[37mPath: /api/health[0m
[37mRetry window: 1m0s[0m

[92m[1/1] Healthcheck succeeded![0m
```

## Runtime logs
```
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/7ff2bf27-f605-4c8a-a817-c2b60e9fe736/vol_onr647rhdeir9di9
Starting Container
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
[wa-bridge] QR received. Open /qr in your browser to scan.
[lp] 17320 Google Ads landing-page routes registered (base=9384, qualifier=7752, near-me=184, 184 service aliases × 51 areas)
[lp-ar] 133 Arabic landing-page routes registered
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[scheduler] started — autoblog 06:00 + 18:00, PSI 03:00, summary 21:00 (Asia/Dubai)
[purge] scan complete — 29 posts, 0 flagged
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:43495 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:42940 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.4:42446 - "GET /q/Q-1778690765082 HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.4:17028 - "POST /api/q/Q-1778690765082/verify HTTP/1.1" 200 OK
INFO:     100.64.0.5:43680 - "GET /api/q/Q-1778690765082 HTTP/1.1" 200 OK
INFO:     100.64.0.6:35778 - "GET /robots.txt HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-13T14:00:00.000637Z is fresh AND ok)
INFO:     100.64.0.7:55640 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
