# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"r3Ez7JuPSzWSprAE8u2xcg"}`

## Build logs
```
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
containerimage.digest: sha256:405a6e4375b0965cf8397db7a01cc8ffc9a5136c8f3c4adcedede7ba7e33b580
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NDA1YTZlNDM3NWIwOTY1Y2Y4Mzk3ZGI3YTAxY2M4ZmZjOWE1MTM2YzhmM2M0YWRjZWRlZGU3YmE3ZTMzYjU4MCIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQyMTowMTo1NVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:896b159c759c8c312ca719087887813e12f935573f2610454f980f9cf1c60d73
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
INFO:     100.64.0.3:17948 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:17948 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:17948 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:17948 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:17948 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:37838 - "GET /api/admin/scraper/status HTTP/1.1" 200 OK
INFO:     100.64.0.3:21632 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
