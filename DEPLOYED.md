# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"CMhFZgnoQ369nUxhGbGh5g"}`

## Build logs
```
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/12] COPY start.sh /app/start.sh
[internal] load build context
[internal] load build context
[internal] load build context
[2/7] WORKDIR /app
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NTdhMzc3Y2E1MTE5MzdjMDc2NGFhMjk1NGRjZGEwNGE3ODZhYTM5OWMyZDBlOTY0ZjZhNmQ0ZDg0OGE1OGYwZCIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QxOTowNzo1MFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:4d6a9d7d8f838cc497e5e67d1574f6bf8c4224bdc3015105c69abfedc9c1c3bd
containerimage.digest: sha256:57a377ca511937c0764aa2954dcda04a786aa399c2d0e964f6a6d4d848a58f0d
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
INFO:     100.64.0.6:35150 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.4:43668 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:43668 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:33174 - "GET /__admin_token__ HTTP/1.1" 403 Forbidden
INFO:     100.64.0.4:43668 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:33164 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.4:43668 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:33174 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.4:33180 - "GET /api/admin/psi/latest HTTP/1.1" 200 OK
INFO:     100.64.0.4:33210 - "GET /api/admin/alerts?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:33210 - "GET /api/admin/bookings?limit=300 HTTP/1.1" 200 OK
INFO:     100.64.0.4:33190 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.4:33208 - "GET /api/admin/bookings?limit=8 HTTP/1.1" 200 OK
INFO:     100.64.0.4:33188 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.4:33190 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:33164 - "GET /api/admin/llm/diagnose HTTP/1.1" 200 OK
INFO:     100.64.0.4:33164 - "POST /api/admin/push/subscribe HTTP/1.1" 200 OK
INFO:     100.64.0.4:33190 - "GET /api/wa/status HTTP/1.1" 200 OK
INFO:     100.64.0.4:33190 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.4:33164 - "GET /api/blog/latest?limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.4:33190 - "GET /api/videos/list?limit=500 HTTP/1.1" 200 OK
INFO:     100.64.0.4:33164 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.4:33164 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:33164 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:33164 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:33164 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:33164 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:33164 - "GET /api/admin/demo-accounts HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
