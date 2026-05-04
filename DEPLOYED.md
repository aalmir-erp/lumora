# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"QVVjXkl2SL-P7JpTBT7zVQ"}`

## Build logs
```
[ 2/11] WORKDIR /app
[builder 1/5] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[builder 1/5] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[builder 1/5] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[10/11] COPY start.sh /app/start.sh
[ 9/11] COPY web ./web
[internal] load build context
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
containerimage.digest: sha256:67c448425f199209c93ed906c6c72f248e6414bd76a0f2cba70a5f0fbe5e9569
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NjdjNDQ4NDI1ZjE5OTIwOWM5M2VkOTA2YzZjNzJmMjQ4ZTY0MTRiZDc2YTBmMmNiYTcwYTVmMGZiZTVlOTU2OSIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQxOTo1MjoxMFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:f8b9ffb4b312d58bdee5f51d5d4864d701b60bffb8f01286a8635ef70bc4a759
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
    rows = c.execute(
           ^^^^^^^^^^
sqlite3.OperationalError: no such column: customer_phone
INFO:     100.64.0.3:50320 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:50320 - "GET /api/admin/bookings HTTP/1.1" 200 OK
INFO:     100.64.0.3:50320 - "GET /admin.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:50320 - "GET /__admin_token__ HTTP/1.1" 403 Forbidden
INFO:     100.64.0.3:34458 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:50320 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.3:34458 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:34468 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:50320 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.3:34478 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34468 - "GET /api/admin/alerts?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:50320 - "GET /api/admin/bookings?limit=8 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34506 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:34484 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.3:34500 - "GET /api/admin/psi/latest HTTP/1.1" 200 OK
INFO:     100.64.0.3:34458 - "GET /api/admin/llm/diagnose HTTP/1.1" 200 OK
INFO:     100.64.0.3:34458 - "GET /api/admin/bookings?limit=300 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34458 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.3:34500 - "GET /api/wa/status HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:34500 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.3:34500 - "POST /api/admin/push/subscribe HTTP/1.1" 200 OK
INFO:     100.64.0.3:34458 - "GET /api/videos/list?limit=500 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34484 - "GET /api/blog/latest?limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.3:34484 - "GET /sw.js HTTP/1.1" 200 OK
INFO:     100.64.0.3:34484 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:44444 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
```
