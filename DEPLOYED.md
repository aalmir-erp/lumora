# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"7m8FuWcEQ6aaM8Iklt7tkg"}`

## Build logs
```
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
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
uploading snapshot
[ 8/11] COPY app ./app
[ 9/11] COPY web ./web
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZGM5YjczYTdhM2NmNzU5ODAzOTljODBmODA3ODM5ZDVjM2NjMWQ3OGQwYzRiY2U3YmRkMzU2Mjg4NjIxODE0ZiIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQyMDo0MDo1MloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:fd3a2c89dc19f40fe4c965dfc6788c778060b3cfa87b7dbc54b3499978cb2f25
containerimage.digest: sha256:dc9b73a7a3cf75980399c80f807839d5c3cc1d78d0c4bce7bdd356288621814f
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
INFO:     100.64.0.5:60040 - "GET /social-strip.js?v=29639321 HTTP/1.1" 200 OK
INFO:     100.64.0.8:10954 - "GET /location-bar.js?v=29639321 HTTP/1.1" 200 OK
INFO:     100.64.0.9:21812 - "GET /about-app.js?v=29639321 HTTP/1.1" 200 OK
INFO:     100.64.0.11:50722 - "GET /cart-badge.js?v=29639321 HTTP/1.1" 200 OK
INFO:     100.64.0.4:48042 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:48042 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.4:48042 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.4:48042 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.12:24368 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:48042 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.12:24376 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.3:42354 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.3:42354 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.3:42354 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.3:42354 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.3:42354 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:42354 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.8:22060 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.8:22060 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.8:22070 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.8:22070 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.8:22070 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.8:22070 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.8:22070 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.8:22070 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
INFO:     100.64.0.8:22070 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.13:37252 - "GET /api/chat/poll?session_id=sw-y66iMTK_1CIeoQP2&since_id=511 HTTP/1.1" 200 OK
```
