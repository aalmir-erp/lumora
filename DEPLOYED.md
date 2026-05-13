# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"pcfPnzScQJutYCWGc9o55Q"}`

## Build logs
```
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
[internal] load build context
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
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
containerimage.digest: sha256:a85cc7ffa2ea5bae233901d222c5bbf7498173d91b4339b05ab0498455c08feb
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YTg1Y2M3ZmZhMmVhNWJhZTIzMzkwMWQyMjJjNWJiZjc0OTgxNzNkOTFiNDMzOWIwNWFiMDQ5ODQ1NWMwOGZlYiIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QxNzowMTo0MloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:8c704ff6bfdf2680b90447dbe6a83834f534e52aa42d4ec4add9803f4c8b2c10
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
INFO:     100.64.0.2:57921 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:57634 - "GET /widget.js?v=1.24.163 HTTP/1.1" 200 OK
INFO:     100.64.0.7:53756 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.8:59054 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.3:10868 - "GET /services/water-heater-repair/al-nuaimiya?id=water_heater_repair HTTP/1.1" 200 OK
INFO:     100.64.0.4:26724 - "GET /style.css?v=1.24.163 HTTP/1.1" 200 OK
INFO:     100.64.0.5:15942 - "GET /widget.css?v=1.24.163 HTTP/1.1" 200 OK
INFO:     100.64.0.9:46022 - "GET /admin/print/quote/Q-1778690765101 HTTP/1.1" 401 Unauthorized
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-13T14:00:00.000637Z is fresh AND ok)
INFO:     100.64.0.10:17058 - "GET /admin/print/quote/Q-1778690765101 HTTP/1.1" 401 Unauthorized
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.10:17058 - "GET /admin/print/quote/Q-1778690765101 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.10:22520 - "GET /api/admin/quotes HTTP/1.1" 200 OK
INFO:     100.64.0.10:22492 - "GET /api/admin/delivery-notes?limit=1 HTTP/1.1" 200 OK
INFO:     100.64.0.10:22474 - "GET /api/admin/sales-orders?limit=1 HTTP/1.1" 200 OK
INFO:     100.64.0.10:22490 - "GET /api/admin/quotes?limit=1 HTTP/1.1" 200 OK
INFO:     100.64.0.10:22456 - "GET /api/admin/quotes HTTP/1.1" 200 OK
INFO:     100.64.0.10:22464 - "GET /api/admin/purchase-orders?limit=1 HTTP/1.1" 200 OK
INFO:     100.64.0.10:22474 - "GET /api/admin/payments?limit=1 HTTP/1.1" 200 OK
INFO:     100.64.0.10:22490 - "GET /api/admin/quotes?limit=1 HTTP/1.1" 200 OK
INFO:     100.64.0.10:22464 - "GET /api/admin/payments?limit=1 HTTP/1.1" 200 OK
INFO:     100.64.0.10:22514 - "GET /api/admin/invoices?limit=1 HTTP/1.1" 200 OK
INFO:     100.64.0.10:22456 - "GET /api/admin/quotes/Q-1778690827048 HTTP/1.1" 200 OK
INFO:     100.64.0.10:22456 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.10:22456 - "GET /api/admin/customers/search?q=A HTTP/1.1" 200 OK
INFO:     100.64.0.10:22456 - "GET /api/admin/customers/search?q=Ai HTTP/1.1" 200 OK
```
