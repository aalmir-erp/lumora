# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"lwF9OsYpRm2QQme9lt7tkg"}`

## Build logs
```
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[ 5/11] RUN pip install -r requirements.txt
[ 4/11] COPY requirements.txt ./
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
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
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NGEyYmMwY2Q2NzcyYjVkNmI5MTA0YzFiNTRlMmYxMzA4MTY1NmIxMjMzMmEyMGRjMzkzNDVhNDczOTE2ZmY5ZSIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQxNjoyMzo1MVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:14bd8846dc9c75b08e01885c73df43e7205163b9029a75b7538749019a8cdbb7
containerimage.digest: sha256:4a2bc0cd6772b5d6b9104c1b54e2f13081656b12332a20dc39345a473916ff9e
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
INFO:     100.64.0.7:57600 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.7:57616 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.7:57600 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.7:57616 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.7:57600 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.7:57604 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.7:57604 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.7:57604 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.7:57600 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.7:57616 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.7:57628 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.7:57628 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.7:57616 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.7:57628 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.7:57600 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.12:15948 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=400 HTTP/1.1" 200 OK
INFO:     100.64.0.12:15948 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.12:15948 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=400 HTTP/1.1" 200 OK
INFO:     100.64.0.12:22542 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=400 HTTP/1.1" 200 OK
INFO:     100.64.0.12:15948 - "POST /api/chat HTTP/1.1" 200 OK
INFO:     100.64.0.12:15948 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=401 HTTP/1.1" 200 OK
INFO:     100.64.0.12:40924 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=402 HTTP/1.1" 200 OK
INFO:     100.64.0.12:15948 - "POST /api/chat HTTP/1.1" 200 OK
INFO:     100.64.0.12:15948 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=403 HTTP/1.1" 200 OK
INFO:     100.64.0.12:15948 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=404 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.12:15948 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=404 HTTP/1.1" 200 OK
INFO:     100.64.0.12:15948 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=404 HTTP/1.1" 200 OK
INFO:     100.64.0.12:15948 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=404 HTTP/1.1" 200 OK
```
