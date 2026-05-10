# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"DleUWbgnRaKyjB1zPvyhXg"}`

## Build logs
```
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[stage-2 2/9] WORKDIR /app
[ 9/12] COPY web ./web
[10/12] COPY _e2e-shots ./_e2e-shots
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 4/12] COPY requirements.txt ./
[py-builder 1/9] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[py-builder 1/9] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[py-builder 1/9] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/12] COPY start.sh /app/start.sh
[internal] load build context
[internal] load build context
[internal] load build context
[stage-2 2/9] WORKDIR /app
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MGE0NjY1ZTVjN2M0OGM0ZmU5YTRiZGRkNzE3YTdjMmU3NDE5YjMwNTU3Yjg2MTgzODI3NDRiZGNlY2FhYjAzOCIsInNpemUiOjMxNTEsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMFQxMDoyMDozNVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:16b0c6500ccdf2b75e8e5b712d4d85058c13a495a37cc92763bc9544cde5ae31
containerimage.digest: sha256:0a4665e5c7c48c4fe9a4bddd717a7c2e7419b30557b8618382744bdcecaab038
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
INFO:     100.64.0.5:27420 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.12:57646 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.5:27458 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.5:27408 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.5:27414 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.12:57666 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.12:57668 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.12:57650 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.12:57692 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.12:57682 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.12:57646 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.7:27234 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.3:15684 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:15694 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:15698 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:15684 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.3:15698 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:15694 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:15716 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:15684 - "GET /index.html HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.5:47288 - "GET /services.html?service=laundry&area=abu-dhabi HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.13:54038 - "GET /?lang=ar HTTP/1.1" 200 OK
INFO:     100.64.0.10:26384 - "GET /services.html HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
```
