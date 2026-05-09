# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"3DtEYbyxTw2PdYF5xtoGcA"}`

## Build logs
```
[ 9/11] COPY web ./web
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[2/5] WORKDIR /app
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 8/11] COPY app ./app
[ 4/11] COPY requirements.txt ./
[1/5] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[1/5] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[1/5] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[internal] load build context
[internal] load build context
[2/5] WORKDIR /app
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/11] COPY requirements.txt ./
[ 5/11] RUN pip install -r requirements.txt
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/11] COPY app ./app
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6N2RiZTBhMjc4MGY1ZGE2ODRkZjNkNmY0MWNhOGI2MDliYmM5YmIzMTEyNjkwMmQ4ZDcwYTRiYzFmNmM5NGZjNiIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQyMjoxMToyOFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:ada24c08e1f08ffcfadab87e5fe06196ed80a440bc3c6a70d6a775ff906c788a
containerimage.digest: sha256:7dbe0a2780f5da684df3d6f41ca8b609bbc9bb31126902d8d70a4bc1f6c94fc6
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
INFO:     100.64.0.5:10306 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:49342 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.3:48254 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.5:10306 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:48254 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.7:36456 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.7:36456 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.7:36456 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.7:36456 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.7:36456 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.7:34680 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.7:36456 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.7:36456 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.7:36456 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.5:10306 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.3:48254 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:49342 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:10306 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:49342 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.3:49342 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:10306 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.5:10322 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:10306 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
Stopping Container
```
