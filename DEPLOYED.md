# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"BXuAf6n4T3uPKm4NnPRhug"}`

## Build logs
```
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[internal] load build context
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[internal] load build context
[ 2/12] WORKDIR /app
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
containerimage.digest: sha256:82b67254bdef9f033a0ea2d8d5e7c767e594856f3e8fd866842e2c4191686362
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ODJiNjcyNTRiZGVmOWYwMzNhMGVhMmQ4ZDVlN2M3NjdlNTk0ODU2ZjNlOGZkODY2ODQyZTJjNDE5MTY4NjM2MiIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QxNToyODoyMFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:eff5eeb85f867882576e5d2cca8087d60e5e09636f0c884d436e89a9954e78fa
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
INFO:     100.64.0.8:17992 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.13:14200 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.12:14548 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.9:26542 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.5:28792 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.6:25118 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.6:25136 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.10:60966 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.10:60960 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.15:51570 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.15:51560 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.14:14054 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.8:18016 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.6:25146 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.6:25132 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.8:18024 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.16:35330 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.15:51560 - "GET /api/admin/reports/profit?from_date=2026-04-13&to_date=2026-05-13&group_by=month HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.15:51570 - "GET /api/admin/quotes?limit=1 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.15:51578 - "GET /api/admin/delivery-notes?limit=1 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.15:51590 - "GET /api/admin/sales-orders?limit=1 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.15:51602 - "GET /api/admin/payments?limit=1 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.15:51594 - "GET /api/admin/purchase-orders?limit=1 HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.15:51548 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.15:51570 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.15:51548 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.5:28806 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
INFO:     100.64.0.5:28806 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.6:24390 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=673 HTTP/1.1" 200 OK
```
