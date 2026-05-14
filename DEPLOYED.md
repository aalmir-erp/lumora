# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"tSuml_VzQY67x4k7nPRhug"}`

## Build logs
```
[internal] load build context
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
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
uploading snapshot
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
containerimage.config.digest: sha256:ff7af0e27d78ba7fce088b0d32823dee3bee8b7cfa5439fd7489189b463fdfbe
containerimage.digest: sha256:187c4b7f8766685b8468b2a925cf82ee4a43c77b50e01dec1e2384ad0e492e0b
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MTg3YzRiN2Y4NzY2Njg1Yjg0NjhiMmE5MjVjZjgyZWU0YTQzYzc3YjUwZTAxZGVjMWUyMzg0YWQwZTQ5MmUwYiIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNFQxMToxNzowMloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:58565 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:60476 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.3:60476 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.3:60476 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.4:36720 - "GET / HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-14T02:00:00.000678Z is fresh AND ok)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.5:41398 - "GET /style.css?v=1.24.201 HTTP/1.1" 200 OK
INFO:     100.64.0.6:49144 - "GET /widget.css?v=1.24.201 HTTP/1.1" 200 OK
INFO:     100.64.0.4:21384 - "GET /api/brand/contact HTTP/1.1" 200 OK
INFO:     100.64.0.4:21384 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.4:21384 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:13030 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:13024 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:13024 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.4:13030 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:13010 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.4:21384 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.4:21384 - "GET /api/brand/contact HTTP/1.1" 200 OK
INFO:     100.64.0.4:13024 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:13010 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:13040 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:13040 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.8:14288 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.8:14288 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.8:14288 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
```
