# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"OQLk16BzQBGg0_bxwoOzXw"}`

## Build logs
```
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
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
containerimage.config.digest: sha256:8ebf469d8a86308b52e91513eee57fbd2894356c58f58fc1ea7136cc0a910790
containerimage.digest: sha256:30d5e290a404755a74dbe093356506e311dbb3ef8242a3589cf1636275798e11
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MzBkNWUyOTBhNDA0NzU1YTc0ZGJlMDkzMzU2NTA2ZTMxMWRiYjNlZjgyNDJhMzU4OWNmMTYzNjI3NTc5OGUxMSIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMVQwNjoyODo1MloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     100.64.0.4:62436 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:60668 - "GET /book.html?nfc=zzzzbogus99 HTTP/1.1" 200 OK
INFO:     100.64.0.13:18008 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.13:18020 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.13:18038 - "GET /api/nfc/tag/zzzzbogus99 HTTP/1.1" 404 Not Found
INFO:     100.64.0.13:18046 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.13:18056 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.13:18008 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.13:18038 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.13:18090 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.10:57866 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.9:31688 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.9:37716 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.9:37708 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.9:37718 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.9:31688 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.9:37728 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.9:37708 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.6:60668 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.6:60668 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:37758 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.6:60668 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.6:37772 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.6:37780 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:60668 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.6:37772 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.6:60668 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.14:11126 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
