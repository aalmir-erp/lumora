# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"QS6qDtoYQC-vzzElPvyhXg"}`

## Build logs
```
[ 4/11] COPY requirements.txt ./
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
containerimage.digest: sha256:6a8ae662fc789e2109240391adfabbf323cc58756e3016a6af6dfe038ac5245d
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NmE4YWU2NjJmYzc4OWUyMTA5MjQwMzkxYWRmYWJiZjMyM2NjNTg3NTZlMzAxNmE2YWY2ZGZlMDM4YWM1MjQ1ZCIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNVQxNDo1MzozNVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:f005fddfa0773880906e5ad32ac1a4fdf5e12872f3965ea69ebb40b3b7e23063
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
INFO:     100.64.0.4:43718 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:43734 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:43740 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.8:32026 - "GET /search-widget.js HTTP/1.1" 200 OK
INFO:     100.64.0.5:32262 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.5:32264 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.7:18352 - "GET /api/reviews/window_cleaning HTTP/1.1" 200 OK
INFO:     100.64.0.9:54104 - "GET /mascots/cleaning.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:38802 - "GET /sear HTTP/1.1" 404 Not Found
INFO:     100.64.0.10:55350 - "GET /api/staff/svc-window-cleaning.svg?service=window_cleaning HTTP/1.1" 200 OK
INFO:     100.64.0.9:54114 - "GET /api/videos/play/svc-window-cleaning HTTP/1.1" 200 OK
INFO:     100.64.0.5:41638 - "GET /contact.html HTTP/1.1" 200 OK
INFO:     100.64.0.4:21724 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:21730 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.11:10252 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:55330 - "GET /search.html?q=sofa+do+you+have HTTP/1.1" 200 OK
INFO:     100.64.0.4:46800 - "GET /api/blog/list?limit=200 HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:46814 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:46822 - "GET /api/videos/list?limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.5:55332 - "GET /service.html?id=sofa_carpet HTTP/1.1" 200 OK
INFO:     100.64.0.5:55332 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:46854 - "GET /api/videos/play/svc-sofa-carpet HTTP/1.1" 200 OK
INFO:     100.64.0.12:44280 - "GET /intake.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:46830 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.13:26212 - "GET /api/staff/svc-sofa-carpet.svg?service=sofa_carpet HTTP/1.1" 200 OK
INFO:     100.64.0.4:46826 - "GET /api/reviews/sofa_carpet HTTP/1.1" 200 OK
INFO:     100.64.0.4:46838 - "GET /api/i18n HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
