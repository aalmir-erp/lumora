# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** BUILDING
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"Bh5O6xBRTJ2k60XBg4a9AQ"}`

## Build logs
```
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OGYzM2FkZDZmMmNhYTIxN2VlMDk5MDE1NWRmYTA0YzU1MzA0OThiMTU5NmY1ZGU4NmIyOGJiZjUyMmUwYWJiMCIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQxOToxMDo1NFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:c9940b349fd8749bdde8a7a5a4ef386a569acb3b9090846b7fe70f33240bf4ea
containerimage.digest: sha256:8f33add6f2caa217ee0990155dfa04c5530498b1596f5de86b28bbf522e0abb0
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
INFO:     100.64.0.3:40060 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:40076 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:40042 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:40056 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:40058 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:40060 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:40058 - "GET /sw.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:10778 - "GET /coverage.html HTTP/1.1" 200 OK
INFO:     100.64.0.4:10778 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:10792 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:10778 - "GET /api/activity/live HTTP/1.1" 200 OK
INFO:     100.64.0.4:10778 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:10792 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:40058 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:23266 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.3:40058 - "GET /book.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:23274 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:10792 - "GET /sw.js HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:23274 - "GET /intake.js HTTP/1.1" 200 OK
INFO:     100.64.0.3:23282 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:23282 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:23274 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:40058 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:23274 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:23266 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:23266 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:23274 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:23266 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:23266 - "GET /sw.js HTTP/1.1" 304 Not Modified
[wa-bridge] QR received. Open /qr in your browser to scan.
```
