# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"O2RR7Z54QD66_0Oo8u2xcg"}`

## Build logs
```
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZTE5MGE1MmMwZjBkOTVhMjMyNGQxNTU5ZmM1NTljZDU1MjJlNDA3YmNlMjZjNTVmYTk4ZjQ3YWYwMmU2MDUwMCIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNlQyMDo1MjoyN1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:30fb8ebb91034a4af20c3fb8b68633d6e0177f94a4ce4d9aa973b13713362f29
containerimage.digest: sha256:e190a52c0f0d95a2324d1559fc559cd5522e407bce26c55fa98f47af02e60500
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
INFO:     100.64.0.3:46402 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:11784 - "GET /?source=twa HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:11784 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:11798 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:11804 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:11806 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:11806 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:11804 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:11806 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.3:11798 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:11798 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.3:11798 - "GET /?source=twa HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:11798 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:60382 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:60368 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:60382 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:60368 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:60382 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.3:11798 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:11798 - "GET /?source=twa HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:11798 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:60382 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:60368 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:11798 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:60368 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:11798 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.3:60382 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:60382 - "GET /sos.html HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
