# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"VVMgB4D2TBe3RNbIPvyhXg"}`

## Build logs
```
[10/11] COPY start.sh /app/start.sh
[ 9/11] COPY web ./web
[ 8/11] COPY app ./app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NjdmOGE0YzRhOWQzMGQyOTMwYTg0NDViMTI5NDI5NDhmZWUzZTIyN2I2MjM5MjM0NzJhNjcyYjg0ZjYxYTJmNCIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQyMjoxNjo1NVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:5114aa473c053f76d09c55e3c68f8252b3d87842cb1cf179a0b099b20b3e5fcd
containerimage.digest: sha256:67f8a4c4a9d30d2930a8445b12942948fee3e227b623923472a672b84f61a2f4
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
INFO:     100.64.0.14:18530 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.14:18572 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.14:18538 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.14:18564 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.13:16852 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.5:32820 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.5:32794 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:32838 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:56906 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:32838 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.5:32794 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.5:56906 - "GET /cart.html HTTP/1.1" 304 Not Modified
INFO:     100.64.0.5:56906 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.5:32838 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.13:16852 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.13:16852 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.13:16856 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.13:16852 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.13:16858 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.13:16856 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.13:16852 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.13:16858 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.13:16852 - "GET /index.html HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
Stopping Container
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
```
