# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"fPWxw8GQQVKom-cGLPU1MQ"}`

## Build logs
```
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[internal] load build context
[ 2/11] WORKDIR /app
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/11] COPY requirements.txt ./
[ 5/11] RUN pip install -r requirements.txt
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/11] COPY app ./app
[ 8/11] COPY app ./app
[ 9/11] COPY web ./web
[ 2/11] WORKDIR /app
[ 2/11] WORKDIR /app
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6N2UwMjg2ODk3Nzc0ZjQzZjM5NTY3MTZjYzk2ZGI5YWE3NzFhZTM4ODYxYmE0YWNiMGU4ZGI0MzIzNzBmY2IzYyIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQyMTowNToyNFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:22c70a7ba76d3909b6a429dc4a05bb514ed56c0676ce34e9afcc9783be17083a
containerimage.digest: sha256:7e0286897774f43f3956716cc96db9aa771ae38861ba4acb0e8db432370fcb3c
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
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.2:43763 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:25960 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.4:46056 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.4:46062 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.5:32590 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.7:45706 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.8:40574 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.10:58342 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.6:12412 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.12:10412 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.9:47100 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.9:47102 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.11:16366 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.13:25800 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.9:47116 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.9:47126 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.12:10412 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.14:61210 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.12:10412 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.3:25960 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.6:12412 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.8:28894 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=543 HTTP/1.1" 200 OK
INFO:     100.64.0.5:43394 - "POST /api/q/Q-0B1FB9/sign HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
```
