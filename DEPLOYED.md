# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"PsAx9QljR06MdchFGbGh5g"}`

## Build logs
```
[ 2/12] WORKDIR /app
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/12] COPY start.sh /app/start.sh
[10/12] COPY _e2e-shots ./_e2e-shots
[internal] load build context
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
[10/12] COPY _e2e-shots ./_e2e-shots
[11/12] COPY start.sh /app/start.sh
[11/12] COPY start.sh /app/start.sh
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:ecb9f0ab3cfddcdccbbc5d222f4c5bbf55d90afd9127ba349b422a751ccaae2c
containerimage.digest: sha256:8daa899cee4c669ae65581e66f339c5f7569c6146fd2777df0ba80e47a0560e7
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OGRhYTg5OWNlZTRjNjY5YWU2NTU4MWU2NmYzMzljNWY3NTY5YzYxNDZmZDI3NzdkZjBiYTgwZTQ3YTA1NjBlNyIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMFQxOTo1NjoyMloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
Starting Container
[scheduler] not loaded: BaseScheduler.add_job() got multiple values for argument 'replace_existing'
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.2:38831 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:34142 - "GET /api/staff/svc-sofa-carpet.svg?service=sofa_carpet HTTP/1.1" 200 OK
INFO:     100.64.0.7:54016 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.6:52644 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.9:36486 - "GET /widget.js?v=1.24.98 HTTP/1.1" 200 OK
INFO:     100.64.0.3:31428 - "GET /services/sofa-carpet/al-reem-island HTTP/1.1" 200 OK
INFO:     100.64.0.4:48568 - "GET /style.css?v=1.24.98 HTTP/1.1" 200 OK
INFO:     100.64.0.5:42286 - "GET /widget.css?v=1.24.98 HTTP/1.1" 200 OK
INFO:     100.64.0.6:34114 - "HEAD /api/videos/play/svc-sofa-carpet HTTP/1.1" 404 Not Found
INFO:     100.64.0.7:54004 - "GET /api/reviews/sofa_carpet HTTP/1.1" 200 OK
INFO:     100.64.0.6:34138 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:34128 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.8:20994 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.7:54016 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.6:52644 - "GET /social-strip.js?v=29640717 HTTP/1.1" 200 OK
INFO:     100.64.0.10:23424 - "GET /_snippets.js?v=29640717 HTTP/1.1" 200 OK
INFO:     100.64.0.12:32136 - "GET /location-bar.js?v=29640717 HTTP/1.1" 200 OK
INFO:     100.64.0.11:33656 - "GET /cart-badge.js?v=29640717 HTTP/1.1" 200 OK
INFO:     100.64.0.13:56746 - "GET /about-app.js?v=29640717 HTTP/1.1" 200 OK
INFO:     100.64.0.6:52644 - "GET /api/site/social HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
