# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"6veZ_rrORDOkQnby9o6EoQ"}`

## Build logs
```
[internal] load build context
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YjkyYjc2NzMwNTZkOWZlZGU1MjVlNWM4NzlkMGYzY2ZkNGViM2I2OTg5YWYxNzgzODNlODYyMThiMmZlNTQ1NyIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QwNjozNTo1MFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:78f94c2e814af93f3cda87b3f81fe69e226e4b23c76a38c5059149e404c5fce9
containerimage.digest: sha256:b92b7673056d9fede525e5c879d0f3cfd4eb3b6989af178383e86218b2fe5457
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/9792fb8f-dd37-4ce1-a2c5-1d1bcd0321d1/vol_onr647rhdeir9di9
[start] launching whatsapp_bridge
Starting Container
[wa-bridge] listening on :3001
[wa-bridge] QR received. Open /qr in your browser to scan.
[lp] 17320 Google Ads landing-page routes registered (base=9384, qualifier=7752, near-me=184, 184 service aliases × 51 areas)
[lp-ar] 133 Arabic landing-page routes registered
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[scheduler] started — autoblog 06:00 + 18:00, PSI 03:00, summary 21:00 (Asia/Dubai)
[purge] scan complete — 28 posts, 0 flagged
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:45823 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:16980 - "GET /services/deep-cleaning/al-mowaihat HTTP/1.1" 200 OK
INFO:     100.64.0.4:28524 - "GET /services/gardening/muwaileh HTTP/1.1" 200 OK
INFO:     100.64.0.5:43896 - "GET /services/water-heater-repair/saadiyat HTTP/1.1" 200 OK
INFO:     100.64.0.6:11180 - "GET /services/handyman?id=handyman HTTP/1.1" 200 OK
INFO:     100.64.0.7:12216 - "GET /widget.css?v=1.24.147 HTTP/1.1" 200 OK
INFO:     100.64.0.6:15386 - "GET /style.css?v=1.24.147 HTTP/1.1" 200 OK
INFO:     100.64.0.8:13152 - "GET /sos-fab.js HTTP/1.1" 200 OK
INFO:     100.64.0.9:36122 - "GET /services/deep-cleaning/al-mowaihat?id=deep_cleaning HTTP/1.1" 200 OK
INFO:     100.64.0.3:46044 - "GET /services/gardening/muwaileh?id=gardening HTTP/1.1" 200 OK
INFO:     100.64.0.10:42066 - "GET /widget.js?v=1.24.147 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-13T02:00:00.001964Z is fresh AND ok)
[wa-bridge] QR received. Open /qr in your browser to scan.
```
