# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"QPf_eCaTR5eX1jFUyCLmYg"}`

## Build logs
```
[ 1/14] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[internal] load build context
[ 2/14] WORKDIR /app
[ 3/14] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/14] COPY requirements.txt ./
[ 5/14] RUN pip install -r requirements.txt
[ 6/14] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/14] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 7/14] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/14] COPY app ./app
[ 8/14] COPY app ./app
[ 9/14] COPY web ./web
[ 9/14] COPY web ./web
[10/14] COPY _e2e-shots ./_e2e-shots
[10/14] COPY _e2e-shots ./_e2e-shots
[11/14] COPY _release/android ./_release/android
[11/14] COPY _release/android ./_release/android
[12/14] COPY twa/android/twa-manifest.json ./twa/android/twa-manifest.json
[12/14] COPY twa/android/twa-manifest.json ./twa/android/twa-manifest.json
[13/14] COPY start.sh /app/start.sh
[13/14] COPY start.sh /app/start.sh
[14/14] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[14/14] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MGY4MzYxOGYyYTkzMTdiMjk4YTFmMWI4MTNiMGI1MjA2M2Y0ODM0YTRkY2NkNzkxZDk5ODFlMmQ5ZDIwMWEyYSIsInNpemUiOjM1MzMsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNVQxNzoyNzoxNFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:661146d81f83d407f0d9e5118f9d4ae5ebed96c8943f4c56cd0727e1afdbe217
containerimage.digest: sha256:0f83618f2a9317b298a1f1b813b0b52063f4834a4dccd791d9981e2d9d201a2a
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
INFO:     100.64.0.3:28482 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:28490 - "GET /api/admin/psi/latest HTTP/1.1" 200 OK
INFO:     100.64.0.3:28490 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:28466 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.3:28430 - "GET /__admin_token__ HTTP/1.1" 403 Forbidden
INFO:     100.64.0.3:28482 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:28498 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:28490 - "GET /api/wa/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:28448 - "GET /api/admin/llm/diagnose HTTP/1.1" 200 OK
INFO:     100.64.0.3:28490 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.3:28498 - "GET /api/admin/bookings?limit=8 HTTP/1.1" 200 OK
INFO:     100.64.0.3:28442 - "GET /api/admin/alerts?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:62296 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.6:62292 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:28430 - "GET /api/admin/psi/latest HTTP/1.1" 200 OK
INFO:     100.64.0.3:28442 - "GET /api/admin/bookings?limit=300 HTTP/1.1" 200 OK
INFO:     100.64.0.3:28498 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:28482 - "GET /api/admin/llm/diagnose HTTP/1.1" 200 OK
INFO:     100.64.0.3:28482 - "GET /api/wa/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:28482 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.3:28498 - "GET /api/push/vapid-key HTTP/1.1" 200 OK
INFO:     100.64.0.3:28498 - "GET /api/blog/latest?limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.3:28482 - "GET /api/admin/auto-tests/findings?severity=error&resolved=0&limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.3:28498 - "GET /api/admin/auto-tests/summary HTTP/1.1" 200 OK
INFO:     100.64.0.3:28430 - "GET /api/admin/auto-tests/runs?limit=30 HTTP/1.1" 200 OK
INFO:     100.64.0.3:28430 - "POST /api/admin/push/subscribe HTTP/1.1" 200 OK
INFO:     100.64.0.3:28430 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:28430 - "GET /api/admin/auto-tests/findings?resolved=0&limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.3:28430 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:48800 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
```
