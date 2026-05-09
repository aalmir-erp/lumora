# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"GC-bwQskSYqyEFmS8u2xcg"}`

## Build logs
```
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[internal] load build context
[ 2/11] WORKDIR /app
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/11] COPY requirements.txt ./
[ 5/11] RUN pip install -r requirements.txt
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/11] COPY app ./app
[ 8/11] COPY app ./app
[ 9/11] COPY web ./web
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:8e31af35897d9d1e2ba5b57544eae472a090ddf9bed727dc17415f68ca417797
containerimage.digest: sha256:4417f32162acaeb98ba781adfdbd29ac3aa131f58e9868a2fe57557adfdcd68a
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NDQxN2YzMjE2MmFjYWViOThiYTc4MWFkZmRiZDI5YWMzYWExMzFmNThlOTg2OGEyZmU1NzU1N2FkZmRjZDY4YSIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQxOTozNDoxM1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     100.64.0.9:17220 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.9:17236 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.11:55638 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.6:62972 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.9:17254 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.5:31034 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.6:62988 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.12:47980 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.12:47992 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.12:47994 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.14:61766 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.18:35766 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.15:57926 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=0 HTTP/1.1" 200 OK
INFO:     100.64.0.9:17270 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.15:57936 - "GET /about-app.js?v=29639254 HTTP/1.1" 200 OK
INFO:     100.64.0.17:17814 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.13:48496 - "GET /location-bar.js?v=29639254 HTTP/1.1" 200 OK
INFO:     100.64.0.12:48004 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.20:62120 - "GET /social-strip.js?v=29639254 HTTP/1.1" 200 OK
INFO:     100.64.0.12:47996 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.12:48010 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.9:17274 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.19:40308 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.16:33630 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.11:55660 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.9:17276 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=507 HTTP/1.1" 200 OK
INFO:     100.64.0.13:48486 - "GET /cart-badge.js?v=29639254 HTTP/1.1" 200 OK
INFO:     100.64.0.19:40310 - "GET /_snippets.js?v=29639254 HTTP/1.1" 200 OK
INFO:     100.64.0.16:33640 - "GET /api/services HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
