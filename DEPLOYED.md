# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"YzEya0uRS0WIvz59yCLmYg"}`

## Build logs
```
[ 5/12] RUN pip install -r requirements.txt
[ 4/12] COPY requirements.txt ./
[internal] load build context
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/12] WORKDIR /app
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
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
[ 8/12] COPY app ./app
[ 9/12] COPY web ./web
[10/12] COPY _e2e-shots ./_e2e-shots
[11/12] COPY start.sh /app/start.sh
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MWJmZmEyZWU4ZDEzNDI5ZjVkYWI1ZjYzNzNkMTYzODM4ZjRiNjEwZTMxOWQ2ZWQ4YjYwODNjZmMxNmU2YTdmZiIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMFQyMDo0MDo1NloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:cbc9ef2a2669c2879fc7bbafe78cea3505c30fb9ddc74316aaa35bcacc34f72c
containerimage.digest: sha256:1bffa2ee8d13429f5dab5f6373d163838f4b610e319d6ed8b6083cfc16e6a7ff
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
INFO:     100.64.0.3:51622 - "GET /book.html?nfc=zzzzbogus99 HTTP/1.1" 200 OK
INFO:     100.64.0.6:51058 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.6:51052 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:32970 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.6:32974 - "GET /api/nfc/tag/zzzzbogus99 HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:32970 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:32974 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.6:32970 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.6:32974 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.6:32974 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.6:32974 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:51622 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.13:58840 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.13:58840 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.13:58840 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.13:58840 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.13:58848 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.13:58840 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.13:58840 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.13:58840 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.13:58840 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.8:26648 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.8:26658 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.6:32974 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.7:36114 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.7:36114 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.8:26658 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.8:26648 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.8:26658 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
