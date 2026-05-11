# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"4FvBTPJTTBOnxWKwezItjw"}`

## Build logs
```
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
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
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/12] COPY app ./app
[ 8/12] COPY app ./app
[ 9/12] COPY web ./web
[ 9/12] COPY web ./web
[10/12] COPY _e2e-shots ./_e2e-shots
[10/12] COPY _e2e-shots ./_e2e-shots
[11/12] COPY start.sh /app/start.sh
[11/12] COPY start.sh /app/start.sh
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:93145f6196f3a6cd45f2fcce0370fe876b31459d6dbc80c6020cb6afbbd9223f
containerimage.digest: sha256:70deafc17b9e9ae0a16ef42464c0b6ec4d1062ea907f7c098ffcbcbed3c53064
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NzBkZWFmYzE3YjllOWFlMGExNmVmNDI0NjRjMGI2ZWM0ZDEwNjJlYTkwN2Y3YzA5OGZmY2JjYmVkM2M1MzA2NCIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMVQxODoyODowNloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:62488 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:62488 - "GET /api/admin/autoblog/prompt HTTP/1.1" 200 OK
INFO:     100.64.0.3:62488 - "GET /api/admin/autoblog HTTP/1.1" 200 OK
INFO:     100.64.0.3:62488 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34832 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:62488 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.3:34834 - "GET /api/admin/bookings?limit=8 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34832 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.3:34854 - "GET /api/admin/alerts?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34850 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34868 - "GET /api/admin/psi/latest HTTP/1.1" 200 OK
INFO:     100.64.0.3:34868 - "GET /api/admin/bookings?limit=300 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34868 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:34888 - "GET /api/admin/psi/latest HTTP/1.1" 200 OK
INFO:     100.64.0.3:34850 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.3:62488 - "GET /api/admin/bookings?limit=8 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34868 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.3:34888 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.3:34850 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:34854 - "GET /api/admin/llm/diagnose HTTP/1.1" 200 OK
INFO:     100.64.0.3:34834 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:34888 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:34884 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.3:34868 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34832 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:34894 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.3:34834 - "GET /api/admin/llm/diagnose HTTP/1.1" 200 OK
INFO:     100.64.0.3:34834 - "POST /api/admin/push/subscribe HTTP/1.1" 200 OK
INFO:     100.64.0.3:34894 - "GET /api/admin/autoblog/prompt HTTP/1.1" 200 OK
```
