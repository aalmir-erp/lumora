# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"PtDCExdBQLWh828iLPU1MQ"}`

## Build logs
```
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YzA4ZDc2YWM2YWJkMjc4M2E0ZTI1ZTIyNWFhZDRlNzY2ZDdlNzVjYjNjMjhlNzBmZGJiNTI1MDFjMDI3NDY4NiIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMlQxMzo1NToxNVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:b812492e22500c9182f631c6b7abfa87105218bf47564a5d90b42bf8a293c7db
containerimage.digest: sha256:c08d76ac6abd2783a4e25e225aad4e766d7e75cb3c28e70fdbb52501c0274686
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
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:34587 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:11170 - "GET /api/blog/hero/al-barsha-restaurant-pest-control-dm-compliance.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:34734 - "GET /api/blog/hero/ras-al-khaimah-mina-al-arab-gym-deep-cleaning-in-mina-al-arab--ras-al-khaimah---pre-summer-prep-guid.svg HTTP/1.1" 200 OK
INFO:     100.64.0.5:14648 - "GET /api/blog/hero/sharjah-silverfish-bathrooms-humidity-fix-2026.svg HTTP/1.1" 200 OK
INFO:     100.64.0.6:56584 - "GET /api/blog/hero/ajman-al-jurf-sofa-carpet-in-al-jurf--ajman---pre-summer-prep-guide-for-may-2026.svg HTTP/1.1" 200 OK
INFO:     100.64.0.7:34956 - "GET /api/blog/hero/ras-al-khaimah-mina-al-arab-living-through-dewa-sewa-peak-season-in-ras-al-khaimah--cutting-your-bil.svg HTTP/1.1" 200 OK
INFO:     100.64.0.8:62308 - "GET /api/blog/hero/dubai-arabian-ranches-living-through-dewa-sewa-peak-season-in-dubai--cutting-your-bill--may-2026.svg HTTP/1.1" 200 OK
INFO:     100.64.0.3:55738 - "GET /faq.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:55738 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:55742 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:55752 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:55738 - "GET /api/search/index HTTP/1.1" 200 OK
INFO:     100.64.0.3:55742 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:55738 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:55562 - "GET /_snippets.js?v=29643236 HTTP/1.1" 200 OK
INFO:     100.64.0.9:34156 - "GET /cart-badge.js?v=29643236 HTTP/1.1" 200 OK
INFO:     100.64.0.10:49278 - "GET /social-strip.js?v=29643236 HTTP/1.1" 200 OK
INFO:     100.64.0.11:56370 - "GET /location-bar.js?v=29643236 HTTP/1.1" 200 OK
INFO:     100.64.0.3:55738 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:55738 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.11:56370 - "GET /api/blog/hero/damac-hills-mosquito-balconies-2026-dengue-alert.svg HTTP/1.1" 200 OK
INFO:     100.64.0.8:15368 - "GET /about-app.js?v=29643236 HTTP/1.1" 200 OK
INFO:     100.64.0.3:54822 - "POST /api/app-install HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-12T02:00:00.000558Z is fresh AND ok)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.12:53024 - "GET / HTTP/1.1" 200 OK
```
