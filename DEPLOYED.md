# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"rUq00AjLSSGuNVAN9I3ezw"}`

## Build logs
```
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[internal] load build context
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[internal] load build context
[ 2/12] WORKDIR /app
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/12] COPY requirements.txt ./
[ 5/12] RUN pip install -r requirements.txt
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/12] COPY app ./app
uploading snapshot
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
containerimage.config.digest: sha256:c1053873deccc436efb96008a93101848da9ca8a7b972eb083fa65460af122c2
containerimage.digest: sha256:691e75c569478e4ce05be1655bd6a200a4b926614b4254c42ee86cec7f5875c7
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NjkxZTc1YzU2OTQ3OGU0Y2UwNWJlMTY1NWJkNmEyMDBhNGI5MjY2MTRiNDI1NGM0MmVlODZjZWM3ZjU4NzVjNyIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QxODoxNjozMVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/c0e7ae15-0762-460f-8e67-9600192db655/vol_onr647rhdeir9di9
Starting Container
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
INFO:     100.64.0.2:47037 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:34328 - "GET /api/q/Q-1778690765082 HTTP/1.1" 200 OK
[autoblog] catch-up SKIP (last_run @ 2026-05-13T14:00:00.000637Z is fresh AND ok)
INFO:     100.64.0.3:34328 - "GET /api/q/Q-1778690765082 HTTP/1.1" 200 OK
INFO:     100.64.0.4:32474 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41726 - "GET /pay/Q-1778690765082 HTTP/1.1" 302 Found
INFO:     100.64.0.3:41726 - "GET /api/q/Q-1778690765082 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41726 - "GET /pay/Q-1778690765082 HTTP/1.1" 302 Found
INFO:     100.64.0.3:41726 - "GET /api/q/Q-1778690765082 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:52986 - "GET /pay/Q-1778690765082 HTTP/1.1" 302 Found
INFO:     100.64.0.3:52986 - "GET /api/q/Q-1778690765082 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
