# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"8Wu6LlM2SESbnlWKg4a9AQ"}`

## Build logs
```
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[internal] load build context
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
containerimage.digest: sha256:3dc1bc89ef8df7b1de5cfb483b66d7283ba4b1ee987b13254db7b1dd99e64a98
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6M2RjMWJjODllZjhkZjdiMWRlNWNmYjQ4M2I2NmQ3MjgzYmE0YjFlZTk4N2IxMzI1NGRiN2IxZGQ5OWU2NGE5OCIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQyMTozODoyMFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:181397dbd9bafeb387052233c551c32225915ca313a4d63fc1295a749f875238
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
INFO:     100.64.0.12:61578 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.12:61598 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.12:61620 - "GET /book.html?nfc=zzzzbogus99 HTTP/1.1" 304 Not Modified
INFO:     100.64.0.12:61630 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.11:51880 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.11:51886 - "GET /cart.html HTTP/1.1" 304 Not Modified
INFO:     100.64.0.11:51868 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.11:51880 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.11:51868 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.11:51886 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.11:51864 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.5:53828 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.11:51864 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.6:61164 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.4:18600 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:18572 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:18610 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:18572 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.4:18610 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:18600 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.4:18592 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.4:18610 - "GET /index.html HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
Stopping Container
```
