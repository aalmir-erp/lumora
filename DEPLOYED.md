# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"ioa2WfuJQ5izXdpZGbGh5g"}`

## Build logs
```
[ 4/12] COPY requirements.txt ./
[1/8] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[1/8] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[1/8] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZjA5OTViNjJjY2IxYWU4NjliMjcyMmU0ZjE0NzI1NjBhZmEzZWI3MzA5MzJlNmMwNTRlYjM4NGEyMzc3OTU4ZiIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMVQyMDoyNDo0MFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:8cf193f069e613796264b8c9d2f3041bc85954f97d45880161c5e6f94713da5c
containerimage.digest: sha256:f0995b62ccb1ae869b2722e4f1472560afa3eb730932e6c054eb384a2377958f
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
INFO:     100.64.0.4:30766 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.4:30812 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:30814 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.4:30830 - "GET /api/admin/alerts?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:30840 - "GET /api/admin/bookings?limit=8 HTTP/1.1" 200 OK
INFO:     100.64.0.4:30856 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:30860 - "GET /api/admin/psi/latest HTTP/1.1" 200 OK
INFO:     100.64.0.4:30812 - "GET /api/admin/bookings?limit=300 HTTP/1.1" 200 OK
INFO:     100.64.0.4:30812 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.4:30812 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:30812 - "POST /api/admin/push/subscribe HTTP/1.1" 200 OK
INFO:     100.64.0.4:30766 - "GET /api/admin/llm/diagnose HTTP/1.1" 200 OK
INFO:     100.64.0.5:42940 - "GET /api/wa/status HTTP/1.1" 200 OK
INFO:     100.64.0.4:30766 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.5:42940 - "GET /api/videos/list?limit=500 HTTP/1.1" 200 OK
INFO:     100.64.0.5:41744 - "GET /api/blog/latest?limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.4:30766 - "GET /api/admin/autoblog/prompt HTTP/1.1" 200 OK
INFO:     100.64.0.4:30812 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:30812 - "GET /api/admin/ai/catalog HTTP/1.1" 200 OK
INFO:     100.64.0.4:30766 - "GET /api/admin/autoblog HTTP/1.1" 200 OK
INFO:     100.64.0.4:30766 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:41750 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:31196 - "GET /api/admin/autoblog/audit HTTP/1.1" 200 OK
INFO:     100.64.0.5:41750 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:31196 - "GET /api/admin/autoblog/status HTTP/1.1" 404 Not Found
INFO:     100.64.0.5:41750 - "POST /api/admin/autoblog/run-now?slot=manual HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.5:41750 - "GET /api/admin/autoblog/status HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:31196 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:41750 - "GET /api/admin/autoblog/status HTTP/1.1" 404 Not Found
```
