# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"Cj4pBWqPTl2kgRmYxtoGcA"}`

## Build logs
```
[ 9/11] COPY web ./web
[ 8/11] COPY app ./app
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
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
containerimage.config.digest: sha256:579eef169b638f6fcfb337cd04e87b76fb5047eedc8f944ce38d82fc0586329e
containerimage.digest: sha256:60e90695a7afea618f74eded2b5ae21b505d9d76e64a68c4d1be954218d1188f
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NjBlOTA2OTVhN2FmZWE2MThmNzRlZGVkMmI1YWUyMWI1MDVkOWQ3NmU2NGE2OGM0ZDFiZTk1NDIxOGQxMTg4ZiIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNVQyMTo1NDo0M1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/6c2b19a9-9189-4a5d-8bbf-179a340f686a/vol_onr647rhdeir9di9
Starting Container
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
[scheduler] not loaded: BaseScheduler.add_job() got multiple values for argument 'replace_existing'
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:55295 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/twa/installs HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.3:16666 - "POST /api/admin/push/broadcast HTTP/1.1" 200 OK
INFO:     100.64.0.3:16666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:44670 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:15978 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
