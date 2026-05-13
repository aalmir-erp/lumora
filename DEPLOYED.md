# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"zmv6Jo0FQ-OEGcTBozsQ6Q"}`

## Build logs
```
[ 5/12] RUN pip install -r requirements.txt
[1/6] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[1/6] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[1/6] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[1/6] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[internal] load build context
[internal] load build context
[2/7] WORKDIR /app
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
containerimage.digest: sha256:82cc08254c91e8b5bebbcb4212a7ca957c75a4684ceb1d1f98fe1b225daa5ac7
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ODJjYzA4MjU0YzkxZThiNWJlYmJjYjQyMTJhN2NhOTU3Yzc1YTQ2ODRjZWIxZDFmOThmZTFiMjI1ZGFhNWFjNyIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QyMDoyNDozNloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:6cd3ea932ca80f84da1397a09e0ff0c8fe2fa05c4bd91ec2cecfb001695d0122
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
INFO:     100.64.0.8:32776 - "GET /services.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.5:37914 - "GET /services.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.11:62264 - "GET /services.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.14:61958 - "GET /services.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.8:32776 - "GET /services.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.5:37914 - "GET /services.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.5:37914 - "GET /llms.txt HTTP/1.1" 200 OK
INFO:     100.64.0.7:23518 - "GET /sitemap.xml HTTP/1.1" 200 OK
INFO:     100.64.0.14:61958 - "GET /robots.txt HTTP/1.1" 200 OK
INFO:     100.64.0.15:31038 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.6:36616 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:36604 - "GET /api/activity/live HTTP/1.1" 200 OK
INFO:     100.64.0.6:36598 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.8:32776 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.16:31594 - "GET /api/videos/list?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.3:11526 - "GET /api/admin/selftest HTTP/1.1" 200 OK
INFO:     100.64.0.3:21410 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21410 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21410 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21410 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:21410 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21410 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21410 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21410 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.17:34320 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.3:21410 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:21410 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:23644 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
```
