# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"7ZiYuIgmQZODLFZWo3UVLg"}`

## Build logs
```
[ 1/14] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[internal] load build context
[ 2/14] WORKDIR /app
[ 3/14] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/14] COPY requirements.txt ./
[ 5/14] RUN pip install -r requirements.txt
[ 6/14] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/14] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
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
containerimage.digest: sha256:9cdb9667a6ecbe6b93485b2df11859372cf511908e012860192746f5eff1a329
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OWNkYjk2NjdhNmVjYmU2YjkzNDg1YjJkZjExODU5MzcyY2Y1MTE5MDhlMDEyODYwMTkyNzQ2ZjVlZmYxYTMyOSIsInNpemUiOjM1MzMsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNVQxNjozMjoxNVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:5601519312c669fd06b0f80bf2489de4537016ee48eb6b695fc1a802a7c1a596
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
[wa-bridge] listening on :3001
[wa-bridge] qr_received : len=239
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/067b3422-affc-4828-b954-9b1dc7dd173a/vol_onr647rhdeir9di9
Starting Container
[lp] 17320 Google Ads landing-page routes registered (base=9384, qualifier=7752, near-me=184, 184 service aliases × 51 areas)
[lp-ar] 133 Arabic landing-page routes registered
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[scheduler] started — autoblog 06:00 + 18:00, PSI 03:00, summary 21:00 (Asia/Dubai)
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
[purge] scan complete — 34 posts, 0 flagged
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:49599 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:50964 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=759 HTTP/1.1" 200 OK
INFO:     100.64.0.3:50964 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=759 HTTP/1.1" 200 OK
INFO:     100.64.0.3:50964 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=759 HTTP/1.1" 200 OK
INFO:     100.64.0.3:50964 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=759 HTTP/1.1" 200 OK
INFO:     100.64.0.3:50964 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.4:20784 - "GET /book.html?service=fridge_repair HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.4:20784 - "GET /book.html?service=fridge_repair HTTP/1.1" 200 OK
INFO:     100.64.0.3:46194 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:43102 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=759 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46194 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:43102 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=759 HTTP/1.1" 200 OK
[wa-bridge] qr_received : len=239
[autoblog] catch-up SKIP (last_run @ 2026-05-15T14:00:00.000743Z is fresh AND ok)
[wa-bridge] qr_received : len=239
INFO:     100.64.0.6:41554 - "HEAD /api/videos/play/svc-post-construction-cleaning HTTP/1.1" 404 Not Found
[wa-bridge] qr_received : len=239
```
