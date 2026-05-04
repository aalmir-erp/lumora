# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"BbOXpEY1QJKCb6iJ8u2xcg"}`

## Build logs
```
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
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
containerimage.config.digest: sha256:a2b40b8bf2c91f08ee15e0e6031c37ca1b5386b48c9d82d587adb833e6791012
containerimage.digest: sha256:83544c259ca62dffd2b985387d86ac91e3006561e0ace2951e18d7ce238e9c97
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ODM1NDRjMjU5Y2E2MmRmZmQyYjk4NTM4N2Q4NmFjOTFlMzAwNjU2MWUwYWNlMjk1MWUxOGQ3Y2UyMzhlOWM5NyIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQxMToyMToyMloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
[scheduler] not loaded: BaseScheduler.add_job() got multiple values for argument 'replace_existing'
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     100.64.0.2:38015 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:51334 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:21816 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:11304 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:23052 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:17360 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:19164 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41054 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.7:32252 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.8:14286 - "GET /robots.txt HTTP/1.1" 200 OK
INFO:     100.64.0.9:44068 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.10:10720 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:22008 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.4:22008 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:38898 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:60996 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.7:19194 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:32474 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.6:32474 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.7:24766 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.10:37146 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
