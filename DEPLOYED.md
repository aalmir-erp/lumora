# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"08UvwZjxTfGvv4kY2prcFg"}`

## Build logs
```
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
containerimage.config.digest: sha256:b1fd7486da97d1ab6f3a5f9cd033ff7845bcadd5e8ad38b8392d96d1b13a561f
containerimage.digest: sha256:2735c7bf9c2e8a3fa804cbc22dd55a354dada880f6bdef601c8a8512721512d9
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MjczNWM3YmY5YzJlOGEzZmE4MDRjYmMyMmRkNTVhMzU0ZGFkYTg4MGY2YmRlZjYwMWM4YTg1MTI3MjE1MTJkOSIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNVQxMzoyMjo1MFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.4:54524 - "GET / HTTP/1.1" 301 Moved Permanently
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.5:38678 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.6:56934 - "GET /robots.txt HTTP/1.1" 301 Moved Permanently
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.7:32468 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.5:38678 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.8:20892 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:38678 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.7:32468 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.8:20892 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.8:20892 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.9:13150 - "GET /services.html HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.10:58932 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.11:54926 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.10:58928 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.12:35608 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.11:54926 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.11:54932 - "GET /services.html HTTP/1.1" 304 Not Modified
INFO:     100.64.0.10:58932 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.10:58928 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.10:58932 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.10:58934 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.10:58928 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.10:58938 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.10:58950 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.10:58934 - "POST /api/app-install HTTP/1.1" 200 OK
```
