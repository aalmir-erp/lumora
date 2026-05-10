# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"UELEBZQ5QrWYdW1BCx5-qw"}`

## Build logs
```
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
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
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:f6843962028e44b94947a880c77880d84bd10f52d4cc0e89273e0b08cfc633f6
containerimage.digest: sha256:602f3fa93cc89277c43a01cb8f7129b8ad65b71ea505ccfd781d5744245b0e07
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NjAyZjNmYTkzY2M4OTI3N2M0M2EwMWNiOGY3MTI5YjhhZDY1YjcxZWE1MDVjY2ZkNzgxZDU3NDQyNDViMGUwNyIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMFQwOTo1OToxNFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     100.64.0.4:56158 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:56162 - "GET /api/nfc/tag/zzzzbogus99 HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:56166 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:56168 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.4:23990 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.4:56166 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:56170 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:29380 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.7:37962 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.7:37978 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.7:37954 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.13:35028 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.7:37936 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.7:37944 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.7:37954 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.7:37958 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:29380 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:29390 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:29396 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:29380 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.3:29390 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:29396 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:29412 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:29396 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
Stopping Container
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Finished server process [1]
Stopping Container
```
