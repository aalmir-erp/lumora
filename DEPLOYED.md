# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"7iH1_rlvTIWN2khyY53eZw"}`

## Build logs
```
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
[ 2/12] WORKDIR /app
[ 2/12] WORKDIR /app
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YjFiOGFjNTI5ZTMxNjhjODgzZWZjMDM1ZDgxYmYyYzg4MDU4ZjBiOGU5YmRjNmFlOWI1ZTQyYzc3NTY2ZmJlMCIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMVQxMjowOTo0NloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:2a667d608f8fb1b76d86ddceb9a982360f0e57fca680a0b17cf6d4600ffff2eb
containerimage.digest: sha256:b1b8ac529e3168c883efc035d81bf2c88058f0b8e9bdc6ae9b5e42c77566fbe0
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
INFO:     100.64.0.3:33878 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.3:38786 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.3:38786 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:38786 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:38786 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.10:59008 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:38786 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.10:59008 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:33878 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.10:59020 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:38786 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.10:59034 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.10:59034 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.6:26772 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.7:22348 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.7:22344 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.7:22352 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.7:22352 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.7:22352 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.7:22352 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.7:22348 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.11:22840 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
Stopping Container
```
