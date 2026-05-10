# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"sIkJWCQkQyWZZbOUnpoFkQ"}`

## Build logs
```
[internal] load metadata for docker.io/library/python:3.12-slim
[internal] load .dockerignore
[internal] load .dockerignore
[internal] load .dockerignore
[internal] load .dockerignore
[ 8/12] COPY app ./app
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
[ 5/12] RUN pip install -r requirements.txt
[10/12] COPY _e2e-shots ./_e2e-shots
[internal] load build context
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/12] WORKDIR /app
[11/12] COPY start.sh /app/start.sh
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 9/12] COPY web ./web
[ 4/12] COPY requirements.txt ./
[1/6] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[1/6] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[1/6] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[internal] load build context
[internal] load build context
[internal] load build context
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OWZkYmMwNTMwMjE1ZTg4ZTFhYmUzZjIxMWVkNjRhZWZkMzdkNDZhNjc5MTE0MzRiZDEwYWE4NzI3NTI1MmJjNCIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMFQxODoxNzo0NVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:3de99ae28f18fdf63a9deb3a2ebcb47e485f17134eb2668c1cd800e2dfa4c476
containerimage.digest: sha256:9fdbc0530215e88e1abe3f211ed64aefd37d46a67911434bd10aa87275252bc4
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
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.2:51563 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:36530 - "GET /style.css?v=1.24.95 HTTP/1.1" 200 OK
INFO:     100.64.0.4:39372 - "GET /widget.css?v=1.24.95 HTTP/1.1" 200 OK
INFO:     100.64.0.5:48708 - "HEAD /api/videos/play/svc-%24%7Bs.id%7D HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:54150 - "GET /api/reviews/%24%7Bs.id%7D HTTP/1.1" 200 OK
INFO:     100.64.0.7:37068 - "GET /widget.js?v=1.24.95 HTTP/1.1" 200 OK
INFO:     100.64.0.14:32028 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.13:27230 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.15:54878 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.19:20732 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.13:27208 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.13:27218 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.16:30886 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.8:48982 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.17:51950 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.12:42112 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.18:22758 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.11:61496 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.9:29454 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.10:19710 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.20:23710 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.21:17178 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.21:17182 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.19:20750 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
INFO:     100.64.0.20:23702 - "GET /api/chat/poll?session_id=sw-i0Vg0PcNTxsinDqm&since_id=607 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
