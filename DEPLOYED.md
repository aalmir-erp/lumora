# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"ok":true,"service":"Lumora","version":"1.16.2","mode":"llm","model":"claude-opus-4-7","wa_bridge":true,"admin_token_hint":null}`

## Build logs
```
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 9/11] COPY web ./web
[ 5/11] RUN pip install -r requirements.txt
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OTgyOWQ4ZmQ5NGU2YWU2Y2JkZmQzZjA3YWM0NDE2ZDNmMjk1OGUzZjkyOGJjZGMwZTY0YTk2NGYwOGU2NDk0MSIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQwMTo0Mjo1NloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:be6b4c12e8e5bbd9441cbf3782925c4b1dd1f6cc368a3c573d9d2fb4c50dfa14
containerimage.digest: sha256:9829d8fd94e6ae6cbdfd3f07ac4416d3f2958e3f928bcdc0e64a964f08e64941
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
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:49265 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:59072 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:59072 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:21488 - "GET /style.css HTTP/1.1" 200 OK
INFO:     100.64.0.5:24250 - "GET /theme.js HTTP/1.1" 200 OK
INFO:     100.64.0.7:62310 - "GET /widget.css HTTP/1.1" 200 OK
INFO:     100.64.0.6:62806 - "GET /_snippets.js HTTP/1.1" 200 OK
INFO:     100.64.0.8:58262 - "GET /banner.js HTTP/1.1" 200 OK
INFO:     100.64.0.6:62818 - "GET /social-strip.js HTTP/1.1" 200 OK
INFO:     100.64.0.7:62324 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:21494 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.8:58264 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.7:62310 - "GET /app.js HTTP/1.1" 200 OK
INFO:     100.64.0.3:59072 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:21494 - "GET /install.js HTTP/1.1" 200 OK
INFO:     100.64.0.9:35668 - "GET /cart-badge.js HTTP/1.1" 200 OK
INFO:     100.64.0.7:62310 - "GET /widget.js HTTP/1.1" 200 OK
INFO:     100.64.0.8:58264 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:59072 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:21494 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:21488 - "POST /api/cart/quote HTTP/1.1" 200 OK
INFO:     100.64.0.8:58264 - "GET /sw.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:21488 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.8:58264 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:34542 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.10:50132 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
```
