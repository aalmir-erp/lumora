# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"eWuiXKtJTt-M1zFAezItjw"}`

## Build logs
```
[ 1/14] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[ 1/14] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[internal] load build context
[ 2/14] WORKDIR /app
[ 3/14] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/14] COPY requirements.txt ./
[ 5/14] RUN pip install -r requirements.txt
[ 6/14] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/14] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/14] COPY app ./app
[ 8/14] COPY app ./app
[ 9/14] COPY web ./web
[ 9/14] COPY web ./web
[10/14] COPY _e2e-shots ./_e2e-shots
[10/14] COPY _e2e-shots ./_e2e-shots
[11/14] COPY _release/android ./_release/android
[11/14] COPY _release/android ./_release/android
[12/14] COPY twa/android/twa-manifest.json ./twa/android/twa-manifest.json
[12/14] COPY twa/android/twa-manifest.json ./twa/android/twa-manifest.json
[13/14] COPY start.sh /app/start.sh
[13/14] COPY start.sh /app/start.sh
[14/14] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[14/14] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZjJmMGU2NWVmMTFhYzZiZjZhNWI0MThlOGU0ZTkwMjJlZjUyOTgwMDdiOTFmYjBmMjFhZWRhZTVjNzhjZTYyNyIsInNpemUiOjM1MzMsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNFQxNjozMTo1NFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:da6388f64d7c6049aeda5d757618539b9a2216823173cabd91b5dce56113f9af
containerimage.digest: sha256:f2f0e65ef11ac6bf6a5b418e8e4e9022ef5298007b91fb0f21aedae5c78ce627
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
[purge] scan complete — 32 posts, 0 flagged
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/7eb4cb72-e14b-4d75-a959-667159ef2042/vol_onr647rhdeir9di9
Starting Container
INFO:     100.64.0.2:45095 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.7:36106 - "GET /_snippets.js?v=29646273 HTTP/1.1" 200 OK
INFO:     100.64.0.7:36106 - "GET /cart-badge.js?v=29646273 HTTP/1.1" 200 OK
INFO:     100.64.0.9:36770 - "GET /location-bar.js?v=29646273 HTTP/1.1" 200 OK
INFO:     100.64.0.4:16428 - "GET /about-app.js?v=29646273 HTTP/1.1" 200 OK
INFO:     100.64.0.3:51790 - "GET /.well-known/assetlinks.json HTTP/1.1" 200 OK
INFO:     100.64.0.4:16408 - "GET /search.html?source=widget HTTP/1.1" 301 Moved Permanently
[push] converted PEM → raw b64url scalar (43 chars) for pywebpush
[push] sending '👋 New visitor on Servia' to 0 sub(s) (audience=all)
INFO:     100.64.0.3:51790 - "GET /search.html?source=widget HTTP/1.1" 200 OK
INFO:     100.64.0.3:51790 - "GET /api/search/index HTTP/1.1" 200 OK
INFO:     100.64.0.5:48522 - "GET /style.css?v=1.24.205 HTTP/1.1" 200 OK
INFO:     100.64.0.6:62924 - "GET /api/brand/contact HTTP/1.1" 200 OK
INFO:     100.64.0.7:36106 - "GET /widget.js?v=1.24.205 HTTP/1.1" 200 OK
INFO:     100.64.0.8:44704 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:62924 - "GET /api/search/index HTTP/1.1" 200 OK
INFO:     100.64.0.6:62924 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.10:22992 - "GET /services/handyman/business-bay HTTP/1.1" 200 OK
INFO:     100.64.0.11:23950 - "HEAD /api/videos/play/svc-handyman HTTP/1.1" 404 Not Found
INFO:     100.64.0.11:23950 - "GET /services/handyman/business-bay?id=handyman HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-14T14:00:00.000637Z is fresh AND ok)
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
