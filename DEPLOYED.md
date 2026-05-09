# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"b-jM4X0UROiLcgcVBT7zVQ"}`

## Build logs
```
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
[ 8/11] COPY app ./app
[ 9/11] COPY web ./web
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.digest: sha256:b29f51bc0fad5e4cf3453eaa4f1321f88fb288e4206faef42387287cefa51808
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YjI5ZjUxYmMwZmFkNWU0Y2YzNDUzZWFhNGYxMzIxZjg4ZmIyODhlNDIwNmZhZWY0MjM4NzI4N2NlZmE1MTgwOCIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQxODo1MjozOVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:7f7e56bc11afa5278bc8e2cd8053944569f6070e85f094aa1175838ca74f4c32
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
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "GET /book.html?service=commercial_cleaning HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:16420 - "GET /api/chat/poll?session_id=sw-GIi-6j6Dx5JLiugs&since_id=489 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:25648 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:25640 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:25640 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:25648 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:16420 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:25640 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:25658 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:25648 - "GET /cart-badge.js?v=29639214 HTTP/1.1" 200 OK
INFO:     100.64.0.12:11024 - "GET /_snippets.js?v=29639214 HTTP/1.1" 200 OK
INFO:     100.64.0.13:24552 - "GET /social-strip.js?v=29639214 HTTP/1.1" 200 OK
INFO:     100.64.0.14:18904 - "GET /location-bar.js?v=29639214 HTTP/1.1" 200 OK
INFO:     100.64.0.15:62908 - "GET /about-app.js?v=29639214 HTTP/1.1" 200 OK
INFO:     100.64.0.16:40744 - "GET /book.html?service=commercial_cleaning HTTP/1.1" 200 OK
```
