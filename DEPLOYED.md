# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"EAHGBqAzRMG4tYm4woOzXw"}`

## Build logs
```
[internal] load build context
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
containerimage.digest: sha256:b34a95fcb97f88d4eb53349fcd90f3ec7fd6e84dd1b3c6aa00984b6ebb0569c4
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YjM0YTk1ZmNiOTdmODhkNGViNTMzNDlmY2Q5MGYzZWM3ZmQ2ZTg0ZGQxYjNjNmFhMDA5ODRiNmViYjA1NjljNCIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNlQwOTo1MTowNFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:65a80fdd7cdebe36d4f8e19534607c0158c9a9ba1bdba9b8681f04f0d916d4d2
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
INFO:     100.64.0.3:21014 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:12458 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:21014 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.3:12458 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:12458 - "GET /me.html HTTP/1.1" 200 OK
INFO:     100.64.0.7:12804 - "GET /impersonation.js HTTP/1.1" 200 OK
INFO:     100.64.0.3:21014 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:12468 - "GET /login.html?next=%2Fme.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:12458 - "GET /api/me HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.6:36874 - "POST /api/auth/logout HTTP/1.1" 200 OK
INFO:     100.64.0.6:36874 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.3:12468 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:12468 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:12468 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:12468 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:36874 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.6:36888 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:12468 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:12468 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:12468 - "POST /api/auth/customer/login HTTP/1.1" 200 OK
INFO:     100.64.0.3:12468 - "POST /api/auth/customer/login HTTP/1.1" 200 OK
INFO:     100.64.0.3:12468 - "POST /api/auth/customer/login HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.3:12468 - "GET /api/wallet/balance HTTP/1.1" 401 Unauthorized
INFO:     Shutting down
INFO:     100.64.0.3:12468 - "POST /api/auth/customer/login HTTP/1.1" 200 OK
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
Stopping Container
```
