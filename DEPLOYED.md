# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"8qZXnbx7QGWx8I0uU79b0g"}`

## Build logs
```
[ 2/12] WORKDIR /app
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/12] COPY start.sh /app/start.sh
[10/12] COPY _e2e-shots ./_e2e-shots
[ 9/12] COPY web ./web
[ 8/12] COPY app ./app
[internal] load build context
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NjE5NGFhYmUwODVhNTNhMDUwZmQ2OGRlNDkwYTNmNmI0YzE0Zjc4MzVkMTczZDJiNjEzOTgwNTViYjQ3NTYxZiIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMFQyMDowMzo0OVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:0ba8f7245cda2df24a6b2f3f5ed6bba153f0b1000584bb76e5b2b56c5ca50ef6
containerimage.digest: sha256:6194aabe085a53a050fd68de490a3f6b4c14f7835d173d2b61398055bb47561f
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
INFO:     100.64.0.5:33492 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:33508 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:33484 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:33484 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.5:33484 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:33508 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.5:33508 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.9:50972 - "HEAD /api/videos/play/svc-pest-control HTTP/1.1" 404 Not Found
INFO:     100.64.0.9:50972 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.9:50988 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.9:50982 - "GET /api/reviews/pest_control HTTP/1.1" 200 OK
INFO:     100.64.0.9:51002 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.10:36508 - "GET /api/staff/svc-pest-control.svg?service=pest_control HTTP/1.1" 200 OK
INFO:     100.64.0.9:51002 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.9:50982 - "GET /social-strip.js?v=29640725 HTTP/1.1" 200 OK
INFO:     100.64.0.9:51014 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.9:50988 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.9:50972 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.11:59348 - "GET /cart-badge.js?v=29640725 HTTP/1.1" 200 OK
INFO:     100.64.0.13:16216 - "GET /mascots/pest.svg HTTP/1.1" 200 OK
INFO:     100.64.0.14:44396 - "GET /about-app.js?v=29640725 HTTP/1.1" 200 OK
INFO:     100.64.0.9:50972 - "GET /api/site/social HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
Stopping Container
```
