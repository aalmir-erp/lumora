# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"L0yTc4TnSvGNwBHaGbGh5g"}`

## Build logs
```
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
[ 8/11] COPY app ./app
[ 9/11] COPY web ./web
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:8a5d4c15b348d3730083fcdab20186460ab4419668e1991c062bb39233eaa5d4
containerimage.digest: sha256:7165d01117af2b2229c783a42deadc91ca0d7739c3ff2dbc90e773322d72e059
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NzE2NWQwMTExN2FmMmIyMjI5Yzc4M2E0MmRlYWRjOTFjYTBkNzczOWMzZmYyZGJjOTBlNzczMzIyZDcyZTA1OSIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNlQwOTowMToyNloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     100.64.0.3:32922 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:32936 - "GET /api/nfc/tag/zzzzbogus99 HTTP/1.1" 404 Not Found
INFO:     100.64.0.3:43312 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:32936 - "GET /book.html?nfc=zzzzbogus99 HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:32906 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:32936 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:32906 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:32922 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:43312 - "GET /api/nfc/tag/zzzzbogus99 HTTP/1.1" 404 Not Found
INFO:     100.64.0.3:32978 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.9:52830 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:32936 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:43312 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:32978 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:32922 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:32922 - "GET /cart.html HTTP/1.1" 304 Not Modified
INFO:     100.64.0.11:55510 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.11:55514 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.10:17514 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.10:17514 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.10:23836 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.10:17514 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.9:52830 - "GET / HTTP/1.1" 304 Not Modified
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
Stopping Container
```
