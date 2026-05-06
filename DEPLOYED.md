# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"giGZBQwYQDGHSqS4xtoGcA"}`

## Build logs
```
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[ 5/11] RUN pip install -r requirements.txt
[ 4/11] COPY requirements.txt ./
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:e04f7b95e04b90f8e063a416e4af8875a29a196b0eb30c842569a508b94a9c8d
containerimage.digest: sha256:0d2192de7d748a97c42e5c41442809caccc097ffa024a6fd42ddd9b59fb0370c
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MGQyMTkyZGU3ZDc0OGE5N2M0MmU1YzQxNDQyODA5Y2FjY2MwOTdmZmEwMjRhNmZkNDJkZGQ5YjU5ZmIwMzcwYyIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNlQxMTozNTozM1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     100.64.0.4:41812 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:41812 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:41812 - "GET /login.html HTTP/1.1" 304 Not Modified
INFO:     100.64.0.4:41812 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:41830 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:41812 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:41830 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:13862 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:13878 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:13888 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:13862 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:13862 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:13888 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.4:13878 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:13878 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.4:13878 - "GET /api/blog/list?limit=80 HTTP/1.1" 404 Not Found
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.5:26506 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:47290 - "GET /service.html?id=deep_cleaning HTTP/1.1" 200 OK
INFO:     100.64.0.4:47290 - "GET /api/videos/play/svc-deep-cleaning HTTP/1.1" 200 OK
INFO:     100.64.0.4:47290 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:47326 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:47300 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:47292 - "GET /api/reviews/deep_cleaning HTTP/1.1" 200 OK
INFO:     100.64.0.6:17816 - "GET /api/staff/svc-deep-cleaning.svg?service=deep_cleaning HTTP/1.1" 200 OK
INFO:     100.64.0.4:47300 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:47292 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.7:27990 - "GET /wp-json/gravitysmtp/v1/tests/mock-data?page=gravitysmtp-settings HTTP/1.1" 404 Not Found
[push] pywebpush not installed — skipping push send
[wa-bridge] QR received. Open /qr in your browser to scan.
```
