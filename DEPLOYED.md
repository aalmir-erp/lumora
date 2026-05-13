# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"kEnt3YL_TSS_YOcAljLL4A"}`

## Build logs
```
[ 4/12] COPY requirements.txt ./
[ 1/10] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[ 1/10] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[ 2/10] WORKDIR /app
[ 2/10] WORKDIR /app
[internal] load build context
[internal] load build context
[internal] load build context
[internal] load build context
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/12] COPY requirements.txt ./
[ 5/12] RUN pip install -r requirements.txt
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MThjMWFhZWZmYjQ3MzM5NDliZWIyYTc4MDgyOGIyMGM1ZDExYTMyY2RiYmZhYTQ1MmQwMGI2MDg1OTRlOTgyNCIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QyMDozMDoyN1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:b2b26cdc80677466666b41c4c73eaa923372918d1c8a64a9695207fffd653367
containerimage.digest: sha256:18c1aaeffb4733949beb2a780828b20c5d11a32cdbbfaa452d00b608594e9824
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
INFO:     100.64.0.4:45842 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:26084 - "GET /__admin_token__ HTTP/1.1" 403 Forbidden
INFO:     100.64.0.3:26076 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:26094 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.8:13666 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:50256 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.5:50254 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.8:13666 - "GET /api/admin/psi/latest HTTP/1.1" 200 OK
INFO:     100.64.0.5:54386 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.8:13666 - "GET /api/admin/bookings?limit=300 HTTP/1.1" 200 OK
INFO:     100.64.0.8:13672 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.8:13678 - "GET /api/admin/bookings?limit=8 HTTP/1.1" 200 OK
INFO:     100.64.0.5:54386 - "GET /api/admin/alerts?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:50254 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.8:13666 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.8:13658 - "GET /api/admin/llm/diagnose HTTP/1.1" 200 OK
INFO:     100.64.0.7:44050 - "GET /api/wa/status HTTP/1.1" 200 OK
INFO:     100.64.0.6:52820 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.8:13658 - "GET /api/blog/latest?limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.8:13666 - "GET /api/videos/list?limit=500 HTTP/1.1" 200 OK
INFO:     100.64.0.10:31928 - "GET /api/admin/payments/status HTTP/1.1" 200 OK
INFO:     100.64.0.10:31938 - "GET /api/admin/payment-providers HTTP/1.1" 200 OK
INFO:     100.64.0.9:28548 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:18268 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:15556 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-13T14:00:00.000637Z is fresh AND ok)
INFO:     100.64.0.13:59224 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
