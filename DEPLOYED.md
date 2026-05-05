# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"JsAxjKCDTNCV-T-LozsQ6Q"}`

## Build logs
```
[ 4/11] COPY requirements.txt ./
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
containerimage.digest: sha256:59f0995ba105f77f07b6becd995e77489035e4aac7b14b6f3f32aeb5de96cef1
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NTlmMDk5NWJhMTA1Zjc3ZjA3YjZiZWNkOTk1ZTc3NDg5MDM1ZTRhYWM3YjE0YjZmM2YzMmFlYjVkZTk2Y2VmMSIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNVQxOTowMDoxNloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:0d9e5e35ffd6da1be4823008ad5d48235b0e6b67c55cb202d47e63a02b5e06a4
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
INFO:     100.64.0.5:58394 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.5:49626 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:49622 - "GET /book.html HTTP/1.1" 200 OK
INFO:     100.64.0.5:49640 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:49646 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.5:49662 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:49672 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:49676 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:49646 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.5:49676 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.5:49676 - "GET /book.html HTTP/1.1" 304 Not Modified
INFO:     100.64.0.5:49640 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:49676 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.5:49622 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:49646 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:49672 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:49662 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:49676 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.5:49622 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.5:49640 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.5:60126 - "GET /book.html HTTP/1.1" 304 Not Modified
INFO:     100.64.0.5:60126 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.5:60128 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:60134 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:60148 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:60152 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:60158 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.5:60166 - "GET /api/services HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
