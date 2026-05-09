# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"nBSW2ZuET3iU-0r7Aax-fw"}`

## Build logs
```
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[internal] load build context
[internal] load build context
[ 2/11] WORKDIR /app
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/11] COPY requirements.txt ./
[ 5/11] RUN pip install -r requirements.txt
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
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
containerimage.config.digest: sha256:77eb62b33b56a89eea786abc3e7d642b188605dcfcd14401c6dbab5528f3996a
containerimage.digest: sha256:f183c84a782fcee1f7a80d4ca7d9b520d6fdcc5c1a4141d61ecb700e0858eeac
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZjE4M2M4NGE3ODJmY2VlMWY3YTgwZDRjYTdkOWI1MjBkNmZkY2M1YzFhNDE0MWQ2MWVjYjcwMGUwODU4ZWVhYyIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQxNjoyODowNloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     100.64.0.4:33210 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:33214 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:57672 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:57672 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:57686 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:33214 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:18450 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.4:27050 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.3:18450 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:18450 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:18456 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:18472 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.3:18480 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:18456 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:27050 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:27060 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:27652 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:27646 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.4:22016 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.10:58724 - "GET /admin-live.html HTTP/1.1" 200 OK
INFO:     100.64.0.9:34496 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.11:50518 - "GET /admin-live.js HTTP/1.1" 200 OK
INFO:     100.64.0.3:27392 - "GET /admin-live.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.12:59754 - "GET /admin-live.html HTTP/1.1" 200 OK
INFO:     100.64.0.13:50958 - "GET /admin-live.html HTTP/1.1" 200 OK
INFO:     100.64.0.14:30038 - "GET /admin-live.html HTTP/1.1" 200 OK
INFO:     100.64.0.15:34738 - "GET /admin-live.js HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.9:59352 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
```
