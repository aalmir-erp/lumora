# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"EqUH8cqNQ4WE7Hb-H4GxDA"}`

## Build logs
```
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
uploading snapshot
exporting to docker image format
containerimage.config.digest: sha256:2470b87b1148b7e900a809fba7f8cf3df4af1a445aecac5245446c71d79aa371
containerimage.digest: sha256:c345a741f38ad735953f70905abda2d336c1249100ebff136b2c26b97c9ff7cb
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YzM0NWE3NDFmMzhhZDczNTk1M2Y3MDkwNWFiZGEyZDMzNmMxMjQ5MTAwZWJmZjEzNmIyYzI2Yjk3YzlmZjdjYiIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QxNToxNTozNVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     100.64.0.6:24248 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:24258 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.6:24248 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.6:24278 - "GET /api/admin/bookings?limit=8 HTTP/1.1" 200 OK
INFO:     100.64.0.6:24286 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:24302 - "GET /api/admin/alerts?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:24294 - "GET /api/admin/psi/latest HTTP/1.1" 200 OK
INFO:     100.64.0.6:24294 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.5:58696 - "GET /api/blog/latest?limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.6:24262 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:58696 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.6:24262 - "GET /admin-commerce.html HTTP/1.1" 200 OK
INFO:     100.64.0.5:57354 - "GET /api/admin/sales-orders?limit=1 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.5:58696 - "GET /api/admin/reports/profit?from_date=2026-04-13&to_date=2026-05-13&group_by=month HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.5:57374 - "GET /api/admin/invoices?limit=1 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.5:57362 - "GET /api/admin/quotes?limit=1 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.5:57380 - "GET /api/admin/delivery-notes?limit=1 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.5:57354 - "GET /api/admin/purchase-orders?limit=1 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.5:58696 - "GET /api/admin/payments?limit=1 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.6:24262 - "GET /api/admin/reports/top-customers?limit=8 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.5:58696 - "GET /api/admin/reports/outstanding HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.3:18236 - "POST /api/admin/seed-commerce-demo HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.7:18878 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:47220 - "POST /api/admin/seed-commerce-demo HTTP/1.1" 401 Unauthorized
[autoblog] catch-up SKIP (last_run @ 2026-05-13T14:00:00.000637Z is fresh AND ok)
INFO:     100.64.0.3:47232 - "GET /api/admin/quotes HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.3:25114 - "GET /api/services HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
