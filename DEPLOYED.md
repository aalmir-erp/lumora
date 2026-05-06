# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"42h-sJTpSPSNV2wMn6XIxQ"}`

## Build logs
```
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
uploading snapshot
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OTllNWNhMTAwNzU2MjNiMzczZDg4OGY1ZjFjNWNkMmEzMDE2NzdlOTcxYWFjZjEwOWJiM2VlNjYxODVlYmIxNiIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNlQxMDoyOToyM1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:63e327b283db22714aac62a8c7144659dbffc947aaf203f62b683521b24c0d5b
containerimage.digest: sha256:99e5ca10075623b373d888f5f1c5cd2a301677e971aacf109bb3ee66185ebb16
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
INFO:     100.64.0.14:12190 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.14:12210 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.14:12210 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.15:34740 - "GET /book.html?nfc=zzzzbogus99 HTTP/1.1" 200 OK
INFO:     100.64.0.21:52432 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.21:52454 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.21:52442 - "GET /api/nfc/tag/zzzzbogus99 HTTP/1.1" 404 Not Found
INFO:     100.64.0.21:52478 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.21:52468 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.21:52432 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.21:59730 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.11:11944 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.20:17644 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.11:11960 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.11:11962 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.11:11964 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.11:11968 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.14:12210 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.14:12202 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.22:58676 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.22:58690 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.22:58676 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.22:58690 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.22:58690 - "GET / HTTP/1.1" 304 Not Modified
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
Stopping Container
```
