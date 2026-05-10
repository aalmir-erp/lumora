# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"aI0Zez6GTEmpUFGhWUN5dQ"}`

## Build logs
```
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 5/12] RUN pip install -r requirements.txt
[ 4/12] COPY requirements.txt ./
[internal] load build context
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/12] WORKDIR /app
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
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
containerimage.digest: sha256:7631560aac9d6e9a362c5b7cf5fa68c3652998806e86f8c40121a1eae3f14452
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NzYzMTU2MGFhYzlkNmU5YTM2MmM1YjdjZjVmYTY4YzM2NTI5OTg4MDZlODZmOGM0MDEyMWExZWFlM2YxNDQ1MiIsInNpemUiOjMxNTEsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMFQxMDoyNTozMloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:250a361e99b4822604c64d3db2069425b845681c814ff8430573e53537c937e1
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
INFO:     100.64.0.2:60615 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:23696 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:39222 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.4:39214 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:23696 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:39234 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:23702 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:39240 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.5:62070 - "GET /_e2e-shots/45-25613268017/T01.png HTTP/1.1" 200 OK
INFO:     100.64.0.3:23698 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:23722 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.3:23696 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.3:23696 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.4:39214 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.4:39214 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:39222 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:39214 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:39234 - "GET /index.html HTTP/1.1" 301 Moved Permanently
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
Stopping Container
```
