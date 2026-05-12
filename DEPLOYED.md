# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"m8jFh3n3RIuxutKPHn5Ytg"}`

## Build logs
```
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[internal] load build context
[internal] load build context
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 2/12] WORKDIR /app
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/12] COPY requirements.txt ./
[ 5/12] RUN pip install -r requirements.txt
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/12] COPY app ./app
uploading snapshot
[ 8/12] COPY app ./app
[ 9/12] COPY web ./web
[ 9/12] COPY web ./web
[10/12] COPY _e2e-shots ./_e2e-shots
[10/12] COPY _e2e-shots ./_e2e-shots
[11/12] COPY start.sh /app/start.sh
[11/12] COPY start.sh /app/start.sh
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
[ 2/12] WORKDIR /app
[ 2/12] WORKDIR /app
exporting to docker image format
containerimage.digest: sha256:c292303d1db856669ff6aba0aee10243bfda0be4c3eb7d53a7ca4eb9fc8ef834
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YzI5MjMwM2QxZGI4NTY2NjlmZjZhYmEwYWVlMTAyNDNiZmRhMGJlNGMzZWI3ZDUzYTdjYTRlYjlmYzhlZjgzNCIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMlQyMDozMDowOVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:8e1c713a8404cf50d86a8577479f958c7255535f0d52ccbe5a16136f2639800e
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
INFO:     100.64.0.3:54962 - "HEAD /api/videos/play/svc-maid-service HTTP/1.1" 404 Not Found
INFO:     100.64.0.3:54962 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:54994 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:54968 - "GET /api/reviews/maid_service HTTP/1.1" 200 OK
INFO:     100.64.0.3:55008 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:55024 - "GET /api/search/index HTTP/1.1" 200 OK
INFO:     100.64.0.3:55034 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:55036 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:54962 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:54962 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:15232 - "GET /ar-preview HTTP/1.1" 200 OK
INFO:     100.64.0.9:29502 - "HEAD /api/videos/play/svc-sofa-carpet HTTP/1.1" 404 Not Found
INFO:     100.64.0.9:29502 - "GET /api/reviews/sofa_carpet HTTP/1.1" 200 OK
INFO:     100.64.0.9:29518 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.9:29520 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.8:29778 - "GET /api/staff/svc-sofa-carpet.svg?service=sofa_carpet HTTP/1.1" 200 OK
INFO:     100.64.0.9:29528 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.9:29540 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.9:29548 - "GET /api/search/index HTTP/1.1" 200 OK
INFO:     100.64.0.9:29556 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.9:29562 - "GET /about-app.js?v=29643632 HTTP/1.1" 200 OK
INFO:     100.64.0.8:29784 - "GET /location-bar.js?v=29643632 HTTP/1.1" 200 OK
INFO:     100.64.0.9:29520 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:51726 - "GET /_snippets.js?v=29643632 HTTP/1.1" 200 OK
INFO:     100.64.0.9:29520 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.11:18216 - "GET /%D8%AA%D9%86%D8%B8%D9%8A%D9%81-%D8%B3%D8%AC%D8%A7%D8%AF-%D8%A7%D9%84%D8%B4%D8%A7%D8%B1%D9%82%D8%A9?id=sofa_carpet&lang=ar HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.9:29520 - "POST /api/app-install HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
