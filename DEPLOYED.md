# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"Vbb8oGbkQ3Gc9sX-qmzx2A"}`

## Build logs
```
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
[10/12] COPY _e2e-shots ./_e2e-shots
[11/12] COPY start.sh /app/start.sh
[11/12] COPY start.sh /app/start.sh
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.digest: sha256:4dc980fa110f27a758bb9643cca301d46a2df8f29e3058152d87f482e1300b90
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NGRjOTgwZmExMTBmMjdhNzU4YmI5NjQzY2NhMzAxZDQ2YTJkZjhmMjllMzA1ODE1MmQ4N2Y0ODJlMTMwMGI5MCIsInNpemUiOjMxNTEsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMFQxNDo1MTo1MloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:fe7a6d509b5e182bc76ee5f92353b0b66a30065ec18d6a9ab5adc5997ade3d73
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
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.2:33877 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:44348 - "GET /nfc-vs-qr.html HTTP/1.1" 200 OK
INFO:     100.64.0.4:46156 - "GET /style.css?v=1.24.93 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.5:14772 - "GET / HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.6:52972 - "GET //wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //xmlrpc.php?rsd HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.6:52972 - "GET //web/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //blog/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //wordpress/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //website/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //wp/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //news/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //2019/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //wp1/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //test/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //wp2/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //media/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //site/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //cms/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:52972 - "GET //sito/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
```
