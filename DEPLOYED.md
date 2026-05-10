# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"8O8ph7vkRZeovMuNO8poTA"}`

## Build logs
```
[ 5/12] RUN pip install -r requirements.txt
[ 4/12] COPY requirements.txt ./
[internal] load build context
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/12] WORKDIR /app
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
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
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YTZiZjAyMTIxZDhmZDBlM2JkODJiZWFlNzc5ZmJiODhlMWZiMzkwNTVlODc4OWE1NmNmMmNlMzk0NTc5MmY3YiIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMFQxOTo0NTo0NloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:838873fe54f2153ac91ca7ff4615d3037215dd09ede0bf7bb5dcf01a2c57d420
containerimage.digest: sha256:a6bf02121d8fd0e3bd82beae779fbb88e1fb39055e8789a56cf2ce3945792f7b
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
INFO:     100.64.0.13:52774 - "GET /api/reviews/villa_deep HTTP/1.1" 200 OK
INFO:     100.64.0.13:52798 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.13:52810 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.13:52770 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.15:23570 - "GET /style.css?v=1.24.97 HTTP/1.1" 200 OK
INFO:     100.64.0.16:54594 - "GET /widget.js?v=1.24.97 HTTP/1.1" 200 OK
INFO:     100.64.0.12:22062 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.17:28104 - "GET /api/staff/svc-villa-deep.svg?service=villa_deep HTTP/1.1" 200 OK
INFO:     100.64.0.18:20418 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=0 HTTP/1.1" 200 OK
INFO:     100.64.0.18:20418 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.16:54594 - "GET /about-app.js?v=29640707 HTTP/1.1" 200 OK
INFO:     100.64.0.19:11936 - "GET /location-bar.js?v=29640707 HTTP/1.1" 200 OK
INFO:     100.64.0.20:29248 - "GET /social-strip.js?v=29640707 HTTP/1.1" 200 OK
INFO:     100.64.0.19:11938 - "GET /cart-badge.js?v=29640707 HTTP/1.1" 200 OK
INFO:     100.64.0.21:30012 - "GET /_snippets.js?v=29640707 HTTP/1.1" 200 OK
INFO:     100.64.0.18:20418 - "GET /api/me/profile HTTP/1.1" 200 OK
INFO:     100.64.0.18:20418 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.22:42332 - "GET /address-picker.js?v=1.24.97 HTTP/1.1" 200 OK
INFO:     100.64.0.13:52828 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=609 HTTP/1.1" 200 OK
INFO:     100.64.0.18:20418 - "GET /api/me/profile HTTP/1.1" 200 OK
INFO:     100.64.0.13:52828 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=609 HTTP/1.1" 200 OK
INFO:     100.64.0.13:52828 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=609 HTTP/1.1" 200 OK
INFO:     100.64.0.13:52828 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=609 HTTP/1.1" 200 OK
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
[wa-bridge] QR received. Open /qr in your browser to scan.
Stopping Container
Stopping Container
```
