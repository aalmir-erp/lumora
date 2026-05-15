# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"DFwuBDHRRQyq7B8-ljLL4A"}`

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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MjhlZmU5NzNlYzA0NmQzOTAzMjI4MWJlMTY4YjRiY2U0NTQzMTRlZDBmMjFmMjEwYTUxNjU1OGY1NmE3MTZhMiIsInNpemUiOjM1MzMsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNVQxNDo1NTozMVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:da38abceb51f0933cd728dfdb41328cd8ef23ad4eb6450489ad06e708faf7609
containerimage.digest: sha256:28efe973ec046d39032281be168b4bce454314ed0f21f210a516558f56a716a2
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
INFO:     100.64.0.5:62008 - "GET /admin.html HTTP/1.1" 200 OK
INFO:     100.64.0.5:62008 - "GET /__admin_token__ HTTP/1.1" 403 Forbidden
INFO:     100.64.0.5:20622 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:62008 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.5:20646 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.5:62008 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:20638 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:20646 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.5:20646 - "GET /api/push/vapid-key HTTP/1.1" 200 OK
INFO:     100.64.0.5:20646 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.5:20638 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/admin/whatsapp/qr-page HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.5:20622 - "POST /api/admin/push/subscribe HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.5:20622 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:61758 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.5:61758 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:61758 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:61758 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.5:61758 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
```
