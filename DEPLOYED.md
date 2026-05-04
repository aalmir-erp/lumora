# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** BUILDING
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"WVqa8379RV-EtJ4gwoOzXw"}`

## Build logs
```
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OTJkNDEwOTljOWYxZjMzOTkxM2NlNDYyNTMzYjRjM2JlMzQ3M2E4OTZiN2UyNWYyYWY4Y2JmMTRiZmUzMTUxNSIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQxNDozNDo0MVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:b42a0058dc1a83ef0d1c9a3dcca39913ff6e95759e5693d22bbb0cc553e1464d
containerimage.digest: sha256:92d41099c9f1f339913ce462533b4c3be3473a896b7e25f2af8cbf14bfe31515
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
INFO:     100.64.0.17:39304 - "GET /style.css HTTP/1.1" 200 OK
INFO:     100.64.0.18:30532 - "GET /theme.js HTTP/1.1" 200 OK
INFO:     100.64.0.19:55126 - "GET /lazy-loaders.js HTTP/1.1" 200 OK
INFO:     100.64.0.17:39310 - "GET /banner.js HTTP/1.1" 200 OK
INFO:     100.64.0.20:44514 - "GET /cms.js HTTP/1.1" 200 OK
INFO:     100.64.0.21:50426 - "GET /share.js HTTP/1.1" 200 OK
INFO:     100.64.0.21:50442 - "GET /widget.css HTTP/1.1" 200 OK
INFO:     100.64.0.21:50452 - "GET /app.js HTTP/1.1" 200 OK
INFO:     100.64.0.12:27616 - "GET /sw.js HTTP/1.1" 304 Not Modified
INFO:     100.64.0.21:50452 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.16:52280 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.22:23010 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.23:57908 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.23:57908 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.17:39310 - "GET /widget.js HTTP/1.1" 200 OK
INFO:     100.64.0.18:30532 - "GET /social-strip.js HTTP/1.1" 200 OK
INFO:     100.64.0.21:50452 - "GET /_snippets.js HTTP/1.1" 200 OK
INFO:     100.64.0.24:32766 - "GET /social-proof.js HTTP/1.1" 200 OK
INFO:     100.64.0.16:52280 - "GET /cart-badge.js HTTP/1.1" 200 OK
INFO:     100.64.0.18:30532 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.9:56614 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.25:45282 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.25:45282 - "POST /api/cart/quote HTTP/1.1" 200 OK
INFO:     100.64.0.11:25624 - "GET /sw.js HTTP/1.1" 304 Not Modified
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.11:25624 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.10:58332 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.11:25624 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.10:58340 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:59716 - "GET /book.html?area=dubai&service=sofa_carpet HTTP/1.1" 200 OK
```
