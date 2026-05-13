# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"ZbmA94qGREOYw8maO8poTA"}`

## Build logs
```
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YmI3YmU1MDdiYjFlODc4MjM3NzAyZjc3MzY4ZTQ5MGJmMWFhM2QyMTdjZTUyYzE3YTVhMmYzMmMxYzg0N2Y2MSIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QyMDozNTo0NVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:a0bf9eca92f8984583bf14f192034d74d2b1566d1d5a30f8b5dd14387af0284b
containerimage.digest: sha256:bb7be507bb1e878237702f77368e490bf1aa3d217ce52c17a5a2f32c1c847f61
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
INFO:     100.64.0.7:52994 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.7:53008 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:38092 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.3:38084 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:38092 - "GET /api/me HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.3:38108 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:38100 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:38084 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:38092 - "GET /api/search/index HTTP/1.1" 200 OK
INFO:     100.64.0.3:38092 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.11:27516 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.4:18130 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.5:31280 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:31276 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:31292 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.5:31282 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.5:31330 - "GET /api/admin/bookings?limit=8 HTTP/1.1" 200 OK
INFO:     100.64.0.5:31314 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:31346 - "GET /api/admin/alerts?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:31310 - "GET /api/admin/psi/latest HTTP/1.1" 200 OK
INFO:     100.64.0.5:31310 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.5:31346 - "GET /api/admin/bookings?limit=300 HTTP/1.1" 200 OK
INFO:     100.64.0.5:31346 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.5:31302 - "GET /api/admin/llm/diagnose HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.7:27702 - "GET /api/wa/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:57898 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.4:18130 - "GET /api/blog/latest?limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.4:18132 - "GET /api/videos/list?limit=500 HTTP/1.1" 200 OK
INFO:     100.64.0.5:31302 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
```
