# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"-_pQGK6SS3W8O_RYCx5-qw"}`

## Build logs
```
[internal] load .dockerignore
[internal] load .dockerignore
[11/12] COPY start.sh /app/start.sh
[10/12] COPY _e2e-shots ./_e2e-shots
[ 9/12] COPY web ./web
[ 8/12] COPY app ./app
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[ 5/12] RUN pip install -r requirements.txt
[ 4/12] COPY requirements.txt ./
[internal] load build context
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/12] WORKDIR /app
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
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
[ 9/12] COPY web ./web
[10/12] COPY _e2e-shots ./_e2e-shots
[11/12] COPY start.sh /app/start.sh
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:b2863aac131df263705761b6ed907850b79669d1575d6b21c32dae39fe78320f
containerimage.digest: sha256:0eeac481db2328700a45d179c6d4e92432ee3d175a6d0638cf85888ae17d01e5
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MGVlYWM0ODFkYjIzMjg3MDBhNDVkMTc5YzZkNGU5MjQzMmVlM2QxNzVhNmQwNjM4Y2Y4NTg4OGFlMTdkMDFlNSIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNFQxMzowMDoxMloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
image push
```

## Runtime logs
```
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
[wa-bridge] QR received. Open /qr in your browser to scan.
[lp-ar] 133 Arabic landing-page routes registered
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[lp] 17320 Google Ads landing-page routes registered (base=9384, qualifier=7752, near-me=184, 184 service aliases × 51 areas)
[scheduler] started — autoblog 06:00 + 18:00, PSI 03:00, summary 21:00 (Asia/Dubai)
[purge] scan complete — 31 posts, 0 flagged
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:37315 - "GET /api/health HTTP/1.1" 200 OK
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/91b3bf91-c74f-4104-a047-4d969182821d/vol_onr647rhdeir9di9
Starting Container
INFO:     100.64.0.3:10464 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.3:10464 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.3:10464 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-14T02:00:00.000678Z is fresh AND ok)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.4:52232 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.4:52232 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.4:52232 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:54700 - "GET /admin.html HTTP/1.1" 200 OK
INFO:     100.64.0.5:54700 - "GET /__admin_token__ HTTP/1.1" 403 Forbidden
INFO:     100.64.0.5:54700 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:54706 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:54706 - "GET /api/brand HTTP/1.1" 200 OK
```
