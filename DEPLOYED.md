# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"vcCaU8J3SiGykYNCnPRhug"}`

## Build logs
```
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[ 5/11] RUN pip install -r requirements.txt
[ 4/11] COPY requirements.txt ./
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
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
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:dab80e76d56a50fd091c3b7078c21450150cf28d071d93a2f35b2ef1860c3774
containerimage.digest: sha256:e4c752be59a5c1e779c863f9c9aac68fd07ce44a5597fbb9095ef3d66d9968d6
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZTRjNzUyYmU1OWE1YzFlNzc5Yzg2M2Y5YzlhYWM2OGZkMDdjZTQ0YTU1OTdmYmI5MDk1ZWYzZDY2ZDk5NjhkNiIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQyMTo0NDo0OVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     100.64.0.14:26962 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.16:26132 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.14:26966 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:41464 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.16:26160 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.16:26132 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.16:26142 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.16:26156 - "GET /api/nfc/tag/zzzzbogus99 HTTP/1.1" 404 Not Found
INFO:     100.64.0.14:26968 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.14:26966 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.10:32212 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.10:32226 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.10:32230 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.10:32230 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.17:52574 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.17:52594 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.17:52594 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.17:52574 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.17:52594 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.17:52602 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.17:52594 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.17:52574 - "GET / HTTP/1.1" 304 Not Modified
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
Stopping Container
```
